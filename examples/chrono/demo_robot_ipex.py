import math

from demo_robot_rover import Example as RoverExample
from demo_robot_rover import InteractiveDriver, ScriptedDriver, Sequencer

ARMS = ("front_arm", "rear_arm")
DRUMS = ("front_drums", "rear_drums")
SHOULDER_Z, ARM_LEN, ARM_POSE, DRUM_R = 0.185, 0.36, math.radians(40.0), 0.150
DRUM_SPEED = 2000.0 / 160.0 * 2 * math.pi / 60.0
BELLY_Z = 0.124


def arm_angle(drum_bottom_z):
    return math.asin(max(-1.0, min(1.0, (drum_bottom_z + DRUM_R - SHOULDER_Z) / ARM_LEN))) - ARM_POSE


DIG_Q = arm_angle(-0.012)
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
KEYS = {"1": "dig_both", "2": "dig_front", "3": "dump_front", "4": "iron_cross", "5": "tilt", "6": "dock"}
DEMO = [(0.5, "drive", (1.08, 0.0)), (4.5, "drive", (1.08, math.radians(30))), (8.5, "drive", (0.0, 0.0)),
        (9.0, "seq", "dig_both"), (19.0, "seq", "dig_front"), (28.0, "seq", "dump_front"), (36.0, "seq", "iron_cross"),
        (45.0, "seq", "tilt"), (53.0, "seq", "dock")]


class Example(RoverExample):
    def __init__(self, args):
        self.drum_cmd = [0.0, 0.0]
        self.creep = 0.0
        self.metrics = {"dig_both_drift": None, "drum_turns": 0.0, "lift": 0.0, "tilt": 0.0, "cover": 0.0}
        self.watch = None
        super().__init__(args)
        missing = [n for n in (*ARMS, *DRUMS, "radiator_cover") if n not in self.robot.joints]
        if missing:
            raise SystemExit(f"ipex URDF is missing joints {missing}; rebuild it with ./pipeline.sh ipex")
        self.seq = Sequencer(self.robot.joints)
        self.z0 = self.pos().z
        print(f"ipex: sequences {', '.join(SEQUENCES)}")
        if isinstance(self.driver, InteractiveDriver):
            print("ipex keys: 1 dig both, 2 dig front, 3 dump front, 4 iron cross, 5 tilt, 6 dock, x drums dig/stop, z drums reverse")

    def configure_rover(self):
        for n in ARMS:
            self.robot.joints[n].rate = 2.0
        self.robot.joints["radiator_cover"].rate = 2.0

    def demo_script(self):
        return list(DEMO)

    def run_sequence(self, name):
        self.seq.add(SEQUENCES[name], _name=name)

    def write_targets(self):
        self.wheel_override = {c: self.creep / w["r"] for c, w in self.wheels.items()} if self.creep else {}
        super().write_targets()
        for d, w in zip(DRUMS, self.drum_cmd):
            self.robot.joints[d].set(w * DRUM_SPEED)

    def on_step(self, step):
        self.drum_cmd = list(step.get("_drums", self.drum_cmd))
        self.creep = step.get("_creep", 0.0)
        if step["_name"] == "dig_both" and step.get("_drums") == (1, 1) and "front_arm" not in step:
            self.watch = self.pos()

    def on_step_end(self, step):
        p = self.pos()
        name, arms_moving = step["_name"], any(k in step for k in ARMS)
        if name == "dig_both" and self.watch is not None and not arms_moving:
            self.metrics["dig_both_drift"] = math.hypot(p.x - self.watch.x, p.y - self.watch.y)
            print(f"counter-rotating dig: chassis drifted {self.metrics['dig_both_drift'] * 100:.1f} cm in {step['_dur']:.0f} s")
            self.watch = None
        if name == "iron_cross" and not arms_moving:
            self.metrics["lift"] = p.z - self.z0
            print(f"iron cross: chassis raised {self.metrics['lift'] * 100:.1f} cm, belly {self.clearance() * 100:.1f} cm off the ground")
        if name == "tilt" and not arms_moving:
            self.metrics["tilt"] = self.pitch()
            print(f"tilt: chassis pitched {math.degrees(self.metrics['tilt']):.1f} deg")
        if name == "dock" and "radiator_cover" not in step:
            self.metrics["cover"] = self.robot.joints["radiator_cover"].position()

    def pitch(self):
        x = self.chassis.GetRot().GetAxisX()
        return math.asin(max(-1.0, min(1.0, -x.z)))

    def clearance(self):
        return self.pos().z + BELLY_Z

    def handle_keys(self, keys):
        super().handle_keys(keys)
        for key, name in KEYS.items():
            if key in keys:
                self.run_sequence(name)
        if "x" in keys:
            self.drum_cmd = [0.0, 0.0] if any(self.drum_cmd) else [1.0, 1.0]
        if "z" in keys:
            self.drum_cmd = [-1.0, -1.0]

    def update(self):
        if isinstance(self.driver, ScriptedDriver):
            for kind, arg in self.driver.events:
                if kind == "seq":
                    self.run_sequence(arg)
            self.driver.events.clear()
        started, finished = self.seq.step(self.step_size)
        if started is not None:
            self.on_step(started)
        if finished is not None:
            self.on_step_end(finished)
        turns = sum(abs(self.robot.joints[d].position()) for d in DRUMS) / (2 * math.pi)
        self.metrics["drum_turns"] = max(self.metrics["drum_turns"], turns)

    def status(self):
        return (f"{super().status()}  belly {self.clearance() * 100:4.1f} cm  pitch {math.degrees(self.pitch()):+5.1f} deg  "
                f"drums {self.drum_cmd[0] * DRUM_SPEED:+4.2f}/{self.drum_cmd[1] * DRUM_SPEED:+4.2f} rad/s"
                + (f"  seq {self.seq.pending()}" if self.seq.pending() else ""))

    def test_final(self):
        super().test_final()
        if self.args.driver != "demo":
            return
        p = self.pos()
        moved = math.hypot(p.x - self.start.x, p.y - self.start.y)
        drift = self.metrics["dig_both_drift"]
        checks = {
            "drove more than 1 m": moved > 1.0,
            "counter-rotating drums held the chassis within 5 cm": drift is not None and drift < 0.05,
            "drums turned more than 2 revolutions": self.metrics["drum_turns"] > 2.0,
            "iron cross lifted the chassis more than 4 cm": self.metrics["lift"] > 0.04,
            "single-arm lift pitched the chassis more than 4 deg": abs(self.metrics["tilt"]) > math.radians(4),
            "radiator cover opened past 80 deg": self.metrics["cover"] > math.radians(80),
            "arms back at the driving pose": all(abs(self.robot.joints[a].position()) < 0.05 for a in ARMS),
            "belly clear of the ground": self.clearance() > 0.08,
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "ipex showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="ipex", max_speed=1.44)
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
