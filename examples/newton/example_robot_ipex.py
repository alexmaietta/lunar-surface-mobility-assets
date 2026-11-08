import math

import numpy as np

import newton
import newton.examples
from example_robot_rover import Example as RoverExample

ARMS = ("front_arm", "rear_arm")
DRUMS = ("front_drums", "rear_drums")
SHOULDER_Z, ARM_LEN, ARM_POSE, DRUM_R = 0.185, 0.36, math.radians(40.0), 0.150
DRUM_SPEED = 2000.0 / 160.0 * 2 * math.pi / 60.0
BELLY_Z = 0.124


def arm_q(drum_bottom_z):
    return math.asin(max(-1.0, min(1.0, (drum_bottom_z + DRUM_R - SHOULDER_Z) / ARM_LEN))) - ARM_POSE


DIG_Q = arm_q(-0.012)
CARRY_Q = math.radians(15.0)
DUMP_Q = math.radians(50.0)
LIFT_Q = -1.05
SEQUENCES = {
    "dig_both": [({"front_arm": DIG_Q, "rear_arm": DIG_Q, "_drums": (1, 1)}, 2.0), ({"_drums": (1, 1)}, 5.0),
                 ({"front_arm": 0.0, "rear_arm": 0.0, "_drums": (0, 0)}, 2.0)],
    "dig_front": [({"front_arm": DIG_Q, "_drums": (1, 0)}, 2.0), ({"_drums": (1, 0), "_creep": 0.10}, 4.0),
                  ({"front_arm": CARRY_Q, "_drums": (0, 0)}, 2.0)],
    "dump_front": [({"front_arm": DUMP_Q}, 2.0), ({"_drums": (-1, 0)}, 3.0), ({"front_arm": 0.0, "_drums": (0, 0)}, 2.0)],
    "iron_cross": [({"front_arm": LIFT_Q, "rear_arm": LIFT_Q}, 3.0), ({}, 2.0), ({"front_arm": 0.0, "rear_arm": 0.0}, 3.0)],
    "tilt": [({"front_arm": LIFT_Q}, 3.0), ({}, 1.5), ({"front_arm": 0.0}, 3.0)],
    "dock": [({"radiator_cover": math.pi / 2}, 3.0), ({}, 2.0), ({"radiator_cover": 0.0}, 3.0)],
}
DEMO = [(0.5, "drive", (1.08, 0.0)), (4.5, "drive", (1.08, math.radians(30))), (8.5, "drive", (0.0, 0.0)),
        (9.0, "seq", "dig_both"), (19.0, "seq", "dig_front"), (28.0, "seq", "dump_front"), (36.0, "seq", "iron_cross"),
        (45.0, "seq", "tilt"), (53.0, "seq", "dock")]


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Example(RoverExample):
    def __init__(self, viewer, args):
        self.queue, self.active_step, self.t_local = [], None, 0.0
        self.demo = list(DEMO) if args.demo else []
        self.drum_cmd = [0.0, 0.0]
        self.creep = 0.0
        self.metrics = {"dig_both_drift": None, "drum_turns": 0.0, "lift": 0.0, "tilt": 0.0, "cover": 0.0}
        self.watch = None
        super().__init__(viewer, args)
        missing = [n for n in (*ARMS, *DRUMS, "radiator_cover") if n not in self.coord]
        if missing:
            raise SystemExit(f"ipex USD is missing joints {missing}; rebuild it with ./pipeline.sh ipex")
        self.start_xy = self.state_0.body_q.numpy()[0][:2].copy()
        self.z0 = float(self.state_0.body_q.numpy()[0][2])
        self.drum_q0 = [float(self.state_0.joint_q.numpy()[self.coord[d]]) for d in DRUMS]
        print(f"ipex: sequences {', '.join(SEQUENCES)}")
        print("keys: 1 dig both, 2 dig front, 3 dump front, 4 iron cross, 5 tilt, 6 dock, x drums dig/stop, z drums reverse, plus the rover keys")

    def run_sequence(self, name):
        for step, dur in SEQUENCES[name]:
            self.queue.append(dict(step, _dur=dur, _name=name))

    def _write_targets(self):
        speed = self.speed
        if self.creep:
            self.speed = self.creep * 3.6
        super()._write_targets()
        self.speed = speed
        for world in range(self.world_count):
            do = world * self.dofs_per_world
            for d, w in zip(DRUMS, self.drum_cmd):
                self._tqd[do + self.dof[d]] = w * DRUM_SPEED
        self.control.joint_target_qd.assign(self._tqd)

    def _sequence_step(self):
        if self.active_step is None and self.queue:
            step = self.queue.pop(0)
            self.active_step = (step, {k: self.poses[k] for k in step if k in self.poses})
            self.t_local = 0.0
            self.drum_cmd = list(step.get("_drums", self.drum_cmd))
            self.creep = step.get("_creep", 0.0)
            self._on_step(step)
        if self.active_step is None:
            return
        step, start = self.active_step
        self.t_local += self.frame_dt
        f = smoothstep(self.t_local / step["_dur"])
        for k, a in start.items():
            self.poses[k] = a + (step[k] - a) * f
        if f >= 1.0:
            self.active_step = None
            self._on_step_end(step)

    def _on_step(self, step):
        if step["_name"] == "dig_both" and step.get("_drums") == (1, 1) and "front_arm" not in step:
            self.watch = self.state_0.body_q.numpy()[0][:2].copy()

    def _on_step_end(self, step):
        bq = self.state_0.body_q.numpy()[0]
        if step["_name"] == "dig_both" and self.watch is not None and "front_arm" not in step:
            self.metrics["dig_both_drift"] = float(np.linalg.norm(bq[:2] - self.watch))
            print(f"counter-rotating dig: chassis drifted {self.metrics['dig_both_drift'] * 100:.1f} cm in {step['_dur']:.0f} s")
            self.watch = None
        if step["_name"] == "iron_cross" and not any(k in step for k in ARMS):
            self.metrics["lift"] = float(bq[2] - self.z0)
            print(f"iron cross: chassis raised {self.metrics['lift'] * 100:.1f} cm, belly {self.clearance() * 100:.1f} cm off the ground")
        if step["_name"] == "tilt" and not any(k in step for k in ARMS):
            self.metrics["tilt"] = self.pitch()
            print(f"tilt: chassis pitched {math.degrees(self.metrics['tilt']):.1f} deg")
        if step["_name"] == "dock" and "radiator_cover" not in step:
            self.metrics["cover"] = float(self.state_0.joint_q.numpy()[self.coord["radiator_cover"]])

    def pitch(self):
        x, y, z, w = self.state_0.body_q.numpy()[0][3:7]
        return math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))

    def clearance(self):
        return float(self.state_0.body_q.numpy()[0][2] + BELLY_Z)

    def update(self):
        for key, name in (("1", "dig_both"), ("2", "dig_front"), ("3", "dump_front"), ("4", "iron_cross"), ("5", "tilt"), ("6", "dock")):
            if self._pressed(key):
                self.run_sequence(name)
        if self._pressed("x"):
            self.drum_cmd = [0.0, 0.0] if any(self.drum_cmd) else [1.0, 1.0]
        if self._pressed("z"):
            self.drum_cmd = [-1.0, -1.0]
        while self.demo and self.sim_time >= self.demo[0][0]:
            _, kind, arg = self.demo.pop(0)
            if kind == "drive":
                self.speed, self.steer = arg
            elif kind == "seq":
                self.run_sequence(arg)
        self._sequence_step()
        q = self.state_0.joint_q.numpy()
        turns = sum(abs(float(q[self.coord[d]]) - q0) for d, q0 in zip(DRUMS, self.drum_q0)) / (2 * math.pi)
        self.metrics["drum_turns"] = max(self.metrics["drum_turns"], turns)

    def gui(self, ui):
        super().gui(ui)
        ui.separator()
        ui.text("IPEx")
        for name in SEQUENCES:
            if ui.button(name):
                self.run_sequence(name)
        for i, d in enumerate(DRUMS):
            ui.text(f"{d} (rad/s, dig > 0)")
            changed, value = ui.slider_float(f"##{d}", float(self.drum_cmd[i] * DRUM_SPEED), -DRUM_SPEED, DRUM_SPEED)
            if changed:
                self.drum_cmd[i] = value / DRUM_SPEED
        if self.queue or self.active_step:
            ui.text(f"sequence: {len(self.queue) + (1 if self.active_step else 0)} step(s) left")
        qd = self.state_0.body_qd.numpy()[0]
        ui.text(f"ground speed {np.linalg.norm(qd[:2]) * 100:5.1f} cm/s (IPEx nominal 30, max 40)")
        ui.text(f"belly clearance {self.clearance() * 100:5.1f} cm, pitch {math.degrees(self.pitch()):+5.1f} deg")

    def test_final(self):
        super().test_final()
        q = self.state_0.joint_q.numpy()
        moved = float(np.linalg.norm(self.state_0.body_q.numpy()[0][:2] - self.start_xy))
        drift = self.metrics["dig_both_drift"]
        checks = {
            "drove more than 1 m": moved > 1.0,
            "counter-rotating drums held the chassis within 5 cm": drift is not None and drift < 0.05,
            "drums turned more than 2 revolutions": self.metrics["drum_turns"] > 2.0,
            "iron cross lifted the chassis more than 4 cm": self.metrics["lift"] > 0.04,
            "single-arm lift pitched the chassis more than 4 deg": abs(self.metrics["tilt"]) > math.radians(4),
            "radiator cover opened past 80 deg": self.metrics["cover"] > math.radians(80),
            "arms back at the driving pose": all(abs(q[self.coord[a]]) < 0.05 for a in ARMS),
            "belly clear of the ground": self.clearance() > 0.08,
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "ipex showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="ipex", max_speed=1.44, substeps=10, drop=0.02)
        parser.add_argument("--demo", action="store_true", help="Scripted showcase: drive, counter-rotating dig, single-drum dig, dump, "
                                                                "iron cross, tilt, dock.")
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
