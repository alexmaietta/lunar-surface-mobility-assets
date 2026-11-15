import math

from demo_robot_rover import Example as RoverExample
from demo_robot_rover import InteractiveDriver, ScriptedDriver, Sequencer, smoothstep

CORNERS = ("fl", "fr", "rl", "rr")
COVERS = ("nav_cam_left_cover", "nav_cam_right_cover")
BELLY_Z = 0.25
ARM = 0.26
AUGER_RPM = 100.0
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
    (0.5, "seq", "covers_close"), (2.5, "seq", "covers_open"), (1.0, "seq", "look_ahead"), (2.0, "drive", (0.72, 0.0)),
    (8.0, "mode", "crab"), (8.0, "drive", (0.72, math.radians(30))), (13.0, "mode", "spin"), (13.0, "drive", (0.5, 0.0)),
    (18.0, "mode", "ackermann"), (18.0, "drive", (0.0, 0.0)), (18.5, "walk", 1), (39.0, "seq", "survey_pano"),
    (51.0, "seq", "drill"), (51.0, "auger", True),
]


class Example(RoverExample):
    def __init__(self, args):
        self.auger = False
        self.track = args.track
        self.earth = (math.radians(args.earth_az), math.radians(args.earth_el))
        self.walk = None
        self.walk_progress = 0.0
        self.max_feed = 0.0
        self.auger_turns = 0.0
        self.covers_closed_seen = False
        super().__init__(args)
        self.seq = Sequencer(self.robot.joints)
        self.lift = {c: f"{c}_lower_arm" for c in CORNERS if f"{c}_lower_arm" in self.robot.joints}
        missing = [n for n in ("trident_deploy", "trident_feed", "trident_auger", "nav_mast_pan", "nav_mast_tilt", "hga_azimuth",
                               "hga_elevation", *COVERS, *self.lift.values()) if n not in self.robot.joints]
        if missing:
            raise SystemExit(f"viper URDF is missing joints {missing}; rebuild it with ./pipeline.sh viper")
        print(f"viper: sequences {', '.join(SEQUENCES)}")
        if isinstance(self.driver, InteractiveDriver):
            print("viper keys: 1 covers, 2 survey pano, 3 drill, 4 wheel walk, 5 auger, e track Earth, h covers toggle")

    def configure_rover(self):
        for n in ("nav_mast_pan", "nav_mast_tilt"):
            self.robot.joints[n].rate = 1.2
        for n in ("trident_deploy", "trident_feed"):
            self.robot.joints[n].rate = 0.3

    def demo_script(self):
        return list(DEMO)

    def joint_q(self, name):
        return self.robot.joints[name].position()

    def run_sequence(self, name):
        self.seq.add(SEQUENCES[name])

    def start_walk(self, cycles):
        self.walk = {"cycles": cycles, "phase": 0, "t": 0.0, "x0": self.pos()}

    def walk_step(self):
        order = ("fl", "rr", "fr", "rl")
        phases = (("lift", 1.5), ("push", 2.0), ("plant", 1.5))
        corner = order[self.walk["phase"] // len(phases)]
        action, dur = phases[self.walk["phase"] % len(phases)]
        f = smoothstep(self.walk["t"] / dur)
        lift = self.args.walk_lift / ARM
        for c in CORNERS:
            self.driver.SetLifting(0.0, c)
        self.driver.SetLifting(lift * {"lift": f, "push": 1.0, "plant": 1 - f}[action], corner)
        omega = 0.10 / 0.25 if action == "push" else 0.0
        self.wheel_override = {c: (0.0 if c == corner else omega) for c in CORNERS}
        self.walk["t"] += self.step_size
        if self.walk["t"] >= dur:
            self.walk["t"] = 0.0
            self.walk["phase"] = (self.walk["phase"] + 1) % (len(phases) * len(order))
            if self.walk["phase"] == 0:
                self.walk["cycles"] -= 1
                if self.walk["cycles"] <= 0:
                    p = self.pos()
                    self.walk_progress = math.hypot(p.x - self.walk["x0"].x, p.y - self.walk["x0"].y)
                    print(f"wheel walking moved {self.walk_progress:.2f} m")
                    self.walk, self.wheel_override = None, {}
                    for c in CORNERS:
                        self.driver.SetLifting(0.0, c)

    def handle_keys(self, keys):
        super().handle_keys(keys)
        if "1" in keys:
            self.run_sequence("covers_open" if self.robot.joints[COVERS[0]].target > 1.0 else "covers_close")
        if "2" in keys:
            self.run_sequence("survey_pano")
        if "3" in keys:
            self.run_sequence("drill")
            self.auger = True
        if "4" in keys and self.walk is None:
            self.start_walk(2)
        if "5" in keys:
            self.auger = not self.auger
        if "e" in keys:
            self.track = not self.track

    def update(self):
        if isinstance(self.driver, ScriptedDriver):
            for kind, arg in self.driver.events:
                if kind == "seq":
                    self.run_sequence(arg)
                elif kind == "walk":
                    self.start_walk(arg)
                elif kind == "auger":
                    self.auger = arg
            self.driver.events.clear()
        if self.walk is not None:
            self.walk_step()
        self.seq.step(self.step_size)
        if self.track:
            az = (self.earth[0] - self.yaw() + math.pi) % (2 * math.pi) - math.pi
            j = self.robot.joints["hga_azimuth"]
            j.target += (az - j.target) * 0.003
            j = self.robot.joints["hga_elevation"]
            j.target += (self.earth[1] - math.atan2(0.3, 1.0) - j.target) * 0.003
        self.robot.joints["trident_auger"].set(AUGER_RPM * 2 * math.pi / 60 if self.auger else 0.0)
        self.max_feed = max(self.max_feed, self.joint_q("trident_feed"))
        self.auger_turns = max(self.auger_turns, abs(self.robot.joints["trident_auger"].link.GetMotorAngle()) / (2 * math.pi))
        self.covers_closed_seen |= self.joint_q(COVERS[0]) > 3.0

    def clearance(self):
        return self.pos().z + BELLY_Z

    def status(self):
        return (f"{super().status()}  belly {self.clearance() * 100:4.1f} cm  drill {self.joint_q('trident_deploy') + self.joint_q('trident_feed'):4.2f} m"
                + (f"  seq {self.seq.pending()}" if self.seq.pending() else "")
                + ("  walking" if self.walk else ""))

    def test_final(self):
        super().test_final()
        if self.args.driver != "demo":
            return
        p = self.pos()
        moved = math.hypot(p.x - self.start.x, p.y - self.start.y)
        checks = {
            "drove more than 1 m": moved > 1.0,
            "wheel walking made progress": self.walk_progress > 0.05,
            "drill fed past 0.9 m": self.max_feed > 0.9,
            "auger turned": self.auger_turns > 5.0,
            "lens covers closed then reopened": self.covers_closed_seen and all(self.joint_q(c) < 0.2 for c in COVERS),
            "mast panned back to centre": abs(self.joint_q("nav_mast_pan")) < 0.1,
            "belly clear of the ground": self.clearance() > 0.05,
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "viper showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="viper", max_speed=0.72)
        parser.add_argument("--track", action="store_true", help="HGA tracks Earth.")
        parser.add_argument("--walk-lift", type=float, default=0.06, help="Wheel lift during wheel walking [m].")
        parser.add_argument("--earth-az", type=float, default=35.0, help="Earth azimuth for HGA tracking [deg, world frame].")
        parser.add_argument("--earth-el", type=float, default=6.0, help="Earth elevation for HGA tracking [deg]; low at the pole.")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
