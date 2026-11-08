import math

import numpy as np

import newton
import newton.examples
from example_robot_rover import Example as RoverExample
from example_robot_rover import draw_light_beams, find_light_sites

CORNERS = ("fl", "fr", "rl", "rr")
COVERS = ("nav_cam_left_cover", "nav_cam_right_cover")
BELLY_Z = 0.25
ARM = 0.26
AUGER_RPM = 100.0
LIGHT_COLOURS = {"nav": (0.25, 0.45, 1.0), "haz": (0.35, 0.55, 1.0), "nirvss": (0.9, 0.5, 1.0), "": (1.0, 0.92, 0.65)}
SEQUENCES = {
    "covers_open": [({c: 0.0 for c in COVERS}, 1.5)],
    "covers_close": [({c: math.pi for c in COVERS}, 1.5)],
    "survey_pano": [({"nav_mast_tilt": math.radians(-20), "nav_mast_pan": math.radians(-150)}, 3.0),
                    *[({"nav_mast_pan": math.radians(a)}, 1.5) for a in (-90, -30, 30, 90, 150)],
                    ({"nav_mast_pan": 0.0, "nav_mast_tilt": math.radians(-30)}, 3.0)],
    "drill": [({"trident_deploy": 0.38}, 4.0), *[({"trident_feed": d}, 3.0) for d in (0.2, 0.4, 0.6, 0.8, 1.0)],
              ({"trident_feed": 0.0}, 6.0), ({"trident_deploy": 0.0}, 4.0)],
    "look_down": [({"nav_mast_tilt": math.radians(-60.95)}, 2.0)],
    "look_ahead": [({"nav_mast_tilt": math.radians(-30), "nav_mast_pan": 0.0}, 2.0)],
}
DEMO = [
    (0.5, "seq", "covers_open"), (0.5, "lights", "nav"), (1.0, "seq", "look_ahead"), (2.0, "drive", (0.72, 0.0)),
    (8.0, "mode", "crab"), (8.0, "drive", (0.72, math.radians(30))), (13.0, "mode", "spin"), (13.0, "drive", (0.5, 0.0)),
    (18.0, "mode", "ackermann"), (18.0, "drive", (0.0, 0.0)), (18.5, "walk", 1), (39.0, "lights", "haz"),
    (39.0, "seq", "survey_pano"), (51.0, "lights", "nirvss"), (51.0, "seq", "drill"), (51.0, "auger", True),
]


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Example(RoverExample):
    def __init__(self, viewer, args):
        self.queue, self.active_step, self.t_local = [], None, 0.0
        self.demo = list(DEMO) if args.demo else []
        self.light_group = args.lights
        self.auger = False
        self.track = args.track
        self.earth = (math.radians(args.earth_az), math.radians(args.earth_el))
        self.walk = None
        self.corner_ride = {c: 0.0 for c in CORNERS}
        self.walk_override = {}
        self.record_meta = {}
        self.max_feed = 0.0
        self.auger_turns = 0.0
        self.walk_progress = 0.0
        super().__init__(viewer, args)
        self.light_sites = find_light_sites(self.stage, self.blabels)
        self.groups = sorted({s["group"] for s in self.light_sites if s["group"]})
        self.start_xy = self.state_0.body_q.numpy()[0][:2].copy()
        self.lift = {c: f"{c}_lower_arm" for c in CORNERS if f"{c}_lower_arm" in self.coord}
        missing = [n for n in ("trident_deploy", "trident_feed", "trident_auger", "nav_mast_pan", "nav_mast_tilt", "hga_azimuth",
                               "hga_elevation", *COVERS, *self.lift.values()) if n not in self.coord]
        if missing:
            raise SystemExit(f"viper USD is missing joints {missing}; rebuild it with ./pipeline.sh viper")
        print(f"viper: {len(self.light_sites)} lights in groups {self.groups}, sequences: {', '.join(SEQUENCES)}")
        print("keys: 1 covers, 2 survey pano, 3 drill, 4 wheel walk, 5 auger, f cycle lights, e track Earth, plus the rover keys")

    def initial_pose(self):
        return {c: math.pi for c in COVERS if c in self.coord}

    def yaw(self):
        x, y, z, w = self.state_0.body_q.numpy()[0][3:7]
        return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))

    def run_sequence(self, name):
        self.queue += [dict({k: v for k, v in step.items() if k in self.poses}, _dur=dur) for step, dur in SEQUENCES[name]]

    def start_walk(self, cycles):
        self.walk = {"cycles": cycles, "phase": 0, "t": 0.0, "x0": self.state_0.body_q.numpy()[0][:2].copy()}

    def _walk_step(self):
        order = ("fl", "rr", "fr", "rl")
        phases = (("lift", 1.5), ("push", 2.0), ("plant", 1.5))
        corner = order[self.walk["phase"] // len(phases)]
        action, dur = phases[self.walk["phase"] % len(phases)]
        f = smoothstep(self.walk["t"] / dur)
        lift = self.args.walk_lift / ARM
        self.corner_ride = {c: 0.0 for c in CORNERS}
        self.corner_ride[corner] = lift * {"lift": f, "push": 1.0, "plant": 1 - f}[action]
        omega = 0.10 / 0.25 if action == "push" else 0.0
        self.walk_override = {c: (0.0 if c == corner else omega) for c in CORNERS}
        self.walk["t"] += self.frame_dt
        if self.walk["t"] >= dur:
            self.walk["t"] = 0.0
            self.walk["phase"] = (self.walk["phase"] + 1) % (len(phases) * len(order))
            if self.walk["phase"] == 0:
                self.walk["cycles"] -= 1
                if self.walk["cycles"] <= 0:
                    xy = self.state_0.body_q.numpy()[0][:2]
                    self.walk_progress = float(np.linalg.norm(xy - self.walk["x0"]))
                    print(f"wheel walking moved {self.walk_progress:.2f} m")
                    self.walk, self.walk_override = None, {}
                    self.corner_ride = {c: 0.0 for c in CORNERS}

    def _write_targets(self):
        super()._write_targets()
        if not getattr(self, "lift", None):
            return
        for world in range(self.world_count):
            qo, do = world * self.coords_per_world, world * self.dofs_per_world
            for c, n in self.lift.items():
                lo, hi = self.lim[n]
                self._tq[qo + self.coord[n]] = float(np.clip(self.home[n] - self.ride + self.corner_ride[c], lo, hi))
            for c, omega in self.walk_override.items():
                self._tqd[do + self.dof[f"{c}_wheel"]] = omega
            self._tqd[do + self.dof["trident_auger"]] = AUGER_RPM * 2 * math.pi / 60 if self.auger else 0.0
        self.control.joint_target_q.assign(self._tq)
        self.control.joint_target_qd.assign(self._tqd)

    def _cycle_lights(self):
        order = ["", *self.groups, "all"]
        i = order.index(self.light_group) if self.light_group in order else 0
        self.light_group = order[(i + 1) % len(order)]
        print("lights:", self.light_group or "off")

    def update(self):
        if self._pressed("1"):
            self.run_sequence("covers_open" if self.poses[COVERS[0]] > 1.0 else "covers_close")
        if self._pressed("2"):
            self.run_sequence("survey_pano")
        if self._pressed("3"):
            self.run_sequence("drill")
            self.auger = True
        if self._pressed("4") and self.walk is None:
            self.start_walk(2)
        if self._pressed("5"):
            self.auger = not self.auger
        if self._pressed("f"):
            self._cycle_lights()
        if self._pressed("e"):
            self.track = not self.track
        while self.demo and self.sim_time >= self.demo[0][0]:
            _, kind, arg = self.demo.pop(0)
            if kind == "drive":
                self.speed, self.steer = arg
            elif kind == "mode":
                self.mode = ("ackermann", "crab", "spin").index(arg)
            elif kind == "seq":
                self.run_sequence(arg)
            elif kind == "lights":
                self.light_group = arg
            elif kind == "walk":
                self.start_walk(arg)
            elif kind == "auger":
                self.auger = arg
        if self.walk is not None:
            self._walk_step()
        if self.active_step is None and self.queue:
            step = self.queue.pop(0)
            self.active_step = (step, {k: self.poses[k] for k in step if k != "_dur"})
            self.t_local = 0.0
        if self.active_step is not None:
            step, start = self.active_step
            self.t_local += self.frame_dt
            f = smoothstep(self.t_local / step["_dur"])
            for k, a in start.items():
                self.poses[k] = a + (step[k] - a) * f
            if f >= 1.0:
                self.active_step = None
        if self.track:
            az = (self.earth[0] - self.yaw() + math.pi) % (2 * math.pi) - math.pi
            self.poses["hga_azimuth"] += (az - self.poses["hga_azimuth"]) * 0.05
            self.poses["hga_elevation"] += (self.earth[1] - math.atan2(0.3, 1.0) - self.poses["hga_elevation"]) * 0.05
        q = self.state_0.joint_q.numpy()
        self.max_feed = max(self.max_feed, float(q[self.coord["trident_feed"]]))
        self.auger_turns = max(self.auger_turns, abs(float(q[self.coord["trident_auger"]])) / (2 * math.pi))

    def lit_sites(self):
        if not self.light_group:
            return []
        return [s for s in self.light_sites if self.light_group == "all" or s["group"] == self.light_group]

    def render_extra(self):
        lit = self.lit_sites()
        for g in [*self.groups, ""]:
            draw_light_beams(self.viewer, self.state_0, [s for s in lit if s["group"] == g], LIGHT_COLOURS.get(g, LIGHT_COLOURS[""]),
                             name=f"lights_{g or 'other'}")

    def clearance(self):
        q = self.state_0.body_q.numpy()[0]
        return float(q[2] + BELLY_Z)

    def gui(self, ui):
        super().gui(ui)
        ui.separator()
        ui.text("VIPER")
        for name in SEQUENCES:
            if ui.button(name):
                self.run_sequence(name)
        if ui.button("wheel walk (2 cycles)") and self.walk is None:
            self.start_walk(2)
        _, self.auger = ui.checkbox(f"TRIDENT auger ({AUGER_RPM:.0f} rpm)", self.auger)
        _, self.track = ui.checkbox("HGA tracks Earth", self.track)
        ui.text(f"lights: {self.light_group or 'off'} (f cycles {', '.join(self.groups)}, all)")
        if self.queue or self.active_step:
            ui.text(f"sequence: {len(self.queue) + (1 if self.active_step else 0)} step(s) left")
        qd = self.state_0.body_qd.numpy()[0]
        ui.text(f"ground speed {np.linalg.norm(qd[:2]) * 100:5.1f} cm/s (VIPER max 20)")
        ui.text(f"belly clearance {self.clearance() * 100:5.1f} cm (VIPER 7-43)")
        q = self.state_0.joint_q.numpy()
        ui.text(f"drill depth below stow {q[self.coord['trident_deploy']] + q[self.coord['trident_feed']]:5.2f} m")

    def test_final(self):
        super().test_final()
        q = self.state_0.joint_q.numpy()
        moved = float(np.linalg.norm(self.state_0.body_q.numpy()[0][:2] - self.start_xy))
        checks = {
            "drove more than 1 m": moved > 1.0,
            "wheel walking made progress": self.walk_progress > 0.05,
            "drill fed past 0.9 m": self.max_feed > 0.9,
            "auger turned": self.auger_turns > 5.0,
            "lens covers open": all(q[self.coord[c]] < 0.2 for c in COVERS),
            "mast panned back to centre": abs(q[self.coord["nav_mast_pan"]]) < 0.1,
            "belly clear of the ground": self.clearance() > 0.05,
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "viper showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="viper", max_speed=0.72, substeps=10)
        parser.add_argument("--demo", action="store_true", help="Scripted showcase: drive, crab, spin, wheel walk, survey, drill.")
        parser.add_argument("--lights", default="", help="Initial light group: nav, haz, nirvss, all or empty for off.")
        parser.add_argument("--track", action="store_true", help="HGA tracks Earth.")
        parser.add_argument("--walk-lift", type=float, default=0.06, help="Wheel lift during wheel walking [m].")
        parser.add_argument("--earth-az", type=float, default=35.0, help="Earth azimuth for HGA tracking [deg, world frame].")
        parser.add_argument("--earth-el", type=float, default=6.0, help="Earth elevation for HGA tracking [deg]; low at the pole.")
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
