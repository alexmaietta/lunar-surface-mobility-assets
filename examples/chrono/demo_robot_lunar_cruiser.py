import math

from demo_robot_rover import Example as RoverExample
from demo_robot_rover import InteractiveDriver, ScriptedDriver, Sequencer

RAILS = [f"rear_stair{f}_rail_{s}" for f in ("", "_lower") for s in ("l", "r")]
WINGS = ("solar_wing_l", "solar_wing_r")
BOLTS = ("latch_bolt_upper", "latch_bolt_lower", "latch_bolt_top", "latch_bolt_bottom")
ARM = ("arm_yaw", "arm_shoulder", "arm_elbow", "arm_wrist_pitch", "arm_wrist_roll")
STOWED = {**{r: math.pi / 2 for r in RAILS}, "rear_stair_lower": 3.0, "rear_stair": 2.35}
SEQUENCES = {
    "airlock_open": [({"airlock_handwheel": 4 * math.pi, **{b: 0.10 for b in BOLTS}}, 3.0), ({"airlock_hatch": math.radians(100)}, 3.5)],
    "airlock_close": [({"airlock_hatch": 0.0}, 3.5), ({"airlock_handwheel": 0.0, **{b: 0.0 for b in BOLTS}}, 3.0)],
    "stair_deploy": [({"rear_stair": 0.7}, 2.0), ({"rear_stair_lower": 0.0}, 2.5), ({"rear_stair": 0.0}, 1.5),
                     ({r: 0.0 for r in RAILS}, 1.5)],
    "stair_stow": [({r: math.pi / 2 for r in RAILS}, 1.5), ({"rear_stair": 0.7}, 1.5), ({"rear_stair_lower": 3.0}, 2.5),
                   ({"rear_stair": 2.35}, 2.0)],
    "wings_deploy": [({w: math.pi / 2 for w in WINGS}, 6.0)],
    "wings_stow": [({w: 0.0 for w in WINGS}, 6.0)],
    "arm_reach": [({"arm_yaw": 0.0, "arm_shoulder": 0.9}, 2.0), ({"arm_elbow": -1.2, "arm_wrist_pitch": 0.5}, 2.0),
                  ({"arm_yaw": 0.6, "arm_wrist_roll": 1.2}, 2.0)],
    "arm_stow": [({"arm_yaw": 0.0, "arm_wrist_roll": 0.0, "arm_wrist_pitch": 0.0}, 2.0), ({"arm_elbow": 0.0, "arm_shoulder": 0.0}, 2.5)],
}
DEMO = [
    (4.0, "drive", (6.0, 0.0)), (8.0, "drive", (6.0, math.radians(15))), (12.0, "drive", (6.0, math.radians(-10))),
    (15.0, "drive", (0.0, 0.0)), (16.0, "seq", "wings_deploy"), (16.0, "track", True), (24.0, "seq", "stair_deploy"),
    (32.0, "seq", "airlock_open"), (39.0, "seq", "arm_reach"),
]
HGA_BORESIGHT_EL = math.atan2(0.6, 1.0)


class Example(RoverExample):
    def __init__(self, args):
        self.track = args.track
        self.earth = (math.radians(args.earth_az), math.radians(args.earth_el))
        self.sun_az = math.radians(args.sun_az)
        super().__init__(args)
        self.seq = Sequencer(self.robot.joints)
        missing = [n for n in (*WINGS, *ARM, *RAILS, "rear_stair", "rear_stair_lower", "airlock_hatch", "airlock_handwheel")
                   if n not in self.robot.joints]
        if missing:
            raise SystemExit(f"lunar cruiser URDF is missing joints {missing}; rebuild it with ./pipeline.sh lunar_cruiser")
        print(f"lunar cruiser: sequences {', '.join(SEQUENCES)}")
        if isinstance(self.driver, InteractiveDriver):
            print("cruiser keys: 1 airlock, 2 stair, 3 wings, 4 arm, e track Earth")

    def initial_pose(self):
        return dict(STOWED)

    def configure_rover(self):
        for j in self.robot.joints.values():
            if j.role in ("stair", "railing", "latch", "hatch", "arm", "solar"):
                j.rate = 3.0
        self.robot.joints["airlock_handwheel"].rate = 12.0

    def demo_script(self):
        return list(DEMO)

    def q(self, name):
        return self.robot.joints[name].position()

    def sun_facing_wings(self):
        yaw = self.yaw()
        phi = (self.sun_az - yaw + math.pi) % (2 * math.pi) - math.pi
        lim = math.radians(120)
        return {"solar_wing_l": min(lim, max(0.0, math.pi / 2 - phi)), "solar_wing_r": min(lim, max(0.0, math.pi / 2 + phi))}

    def run_sequence(self, name):
        if name == "wings_deploy":
            self.seq.add([(self.sun_facing_wings(), 6.0)])
        else:
            self.seq.add(SEQUENCES[name])

    def toggle(self, a, b, probe, value):
        self.run_sequence(a if abs(self.robot.joints[probe].target - value) > 1e-3 else b)

    def handle_keys(self, keys):
        super().handle_keys(keys)
        if "1" in keys:
            self.toggle("airlock_open", "airlock_close", "airlock_hatch", math.radians(100))
        if "2" in keys:
            self.toggle("stair_deploy", "stair_stow", "rear_stair", 0.0)
        if "3" in keys:
            self.toggle("wings_deploy", "wings_stow", "solar_wing_l", self.sun_facing_wings()["solar_wing_l"])
        if "4" in keys:
            self.toggle("arm_reach", "arm_stow", "arm_shoulder", 0.9)
        if "e" in keys:
            self.track = not self.track

    def update(self):
        if isinstance(self.driver, ScriptedDriver):
            for kind, arg in self.driver.events:
                if kind == "seq":
                    self.run_sequence(arg)
                elif kind == "track":
                    self.track = arg
            self.driver.events.clear()
        self.seq.step(self.step_size)
        if self.track and "hga_azimuth" in self.robot.joints:
            az = (self.earth[0] - self.yaw() + math.pi) % (2 * math.pi) - math.pi
            j = self.robot.joints["hga_azimuth"]
            j.target += (az - j.target) * 0.003
            j = self.robot.joints["hga_elevation"]
            j.target += (self.earth[1] - HGA_BORESIGHT_EL - j.target) * 0.003

    def status(self):
        return (f"{super().status()}  wings {math.degrees(self.q('solar_wing_l')):3.0f}/{math.degrees(self.q('solar_wing_r')):3.0f} deg  "
                f"stair {math.degrees(self.q('rear_stair')):4.0f} deg  hatch {math.degrees(self.q('airlock_hatch')):3.0f} deg"
                + (f"  seq {self.seq.pending()}" if self.seq.pending() else ""))

    def test_final(self):
        super().test_final()
        if self.args.driver != "demo":
            return
        p = self.pos()
        moved = math.hypot(p.x - self.start.x, p.y - self.start.y)
        checks = {
            "drove more than 8 m": moved > 8.0,
            "airlock hatch open": self.q("airlock_hatch") > math.radians(90),
            "stair deployed": abs(self.q("rear_stair")) < 0.05 and abs(self.q("rear_stair_lower")) < 0.05,
            "railings up": all(abs(self.q(r)) < 0.05 for r in RAILS),
            "solar wings out and sun-facing": all(self.q(w) > math.radians(45) for w in WINGS),
            "arm reached out": self.q("arm_shoulder") > 0.8,
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "lunar cruiser showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="lunar_cruiser", max_speed=15.0, sun_az=30.0, sun_el=6.0)
        parser.add_argument("--track", action="store_true", help="HGA tracks Earth from the start.")
        parser.add_argument("--earth-az", type=float, default=35.0, help="Earth azimuth for HGA tracking [deg, world frame].")
        parser.add_argument("--earth-el", type=float, default=25.0, help="Earth elevation for HGA tracking [deg].")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
