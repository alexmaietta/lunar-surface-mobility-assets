import math

import numpy as np
import warp as wp

import newton
import newton.examples
from example_robot_rover import Example as RoverExample

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
    (1.0, "drive", (6.0, 0.0)), (5.0, "drive", (6.0, math.radians(15))), (9.0, "drive", (6.0, math.radians(-10))),
    (12.0, "drive", (0.0, 0.0)), (13.0, "seq", "wings_deploy"), (13.0, "track", True), (20.0, "lights", True),
    (21.0, "seq", "stair_deploy"), (29.0, "seq", "airlock_open"), (36.0, "seq", "arm_reach"),
]
HGA_BORESIGHT_EL = math.atan2(0.6, 1.0)


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Example(RoverExample):
    def __init__(self, viewer, args):
        self.queue, self.active_step, self.t_local = [], None, 0.0
        self.track = False
        self.lights_on = args.lights
        self.earth = (math.radians(args.earth_az), math.radians(args.earth_el))
        self.demo = list(DEMO) if args.demo else []
        self.start_xy = None
        self.sun = [None if args.sun_az is None else math.radians(args.sun_az), math.radians(args.sun_el)]
        self.record_meta = {}
        super().__init__(viewer, args)
        self.light_sites = self._find_light_sites()
        self.strut = [n for n in self.labels if n.endswith("_strut_rod")]
        self.start_xy = self.state_0.body_q.numpy()[0][:2].copy()
        print(f"lunar cruiser: {len(self.light_sites)} lights, sequences: {', '.join(SEQUENCES)}")
        print("keys: 1 airlock, 2 stair, 3 wings, 4 arm, f lights, e track Earth, plus the rover keys")

    def initial_pose(self):
        return {n: v for n, v in STOWED.items() if n in self.coord}

    def _find_light_sites(self):
        from pxr import Usd, UsdGeom

        cache = UsdGeom.XformCache(Usd.TimeCode.Default())
        out = []
        for prim in Usd.PrimRange(self.stage.GetDefaultPrim()):
            if not prim.HasAttribute("site:kind") or prim.GetAttribute("site:kind").Get() != "light":
                continue
            body = prim.GetParent()
            while body and body.GetName() not in self.blabels:
                body = body.GetParent()
            if not body:
                continue
            local = cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(body).GetInverse()
            t = local.ExtractTranslation()
            z = local.TransformDir((0, 0, 1))
            r = prim.GetAttribute("site:radius_m").Get() if prim.HasAttribute("site:radius_m") else 0.05
            out.append({"body": self.blabels.index(body.GetName()), "p": np.array(t), "d": np.array(z) / max(np.linalg.norm(z), 1e-9),
                        "r": float(r or 0.05), "name": prim.GetName()})
        return out

    def yaw(self):
        x, y, z, w = self.state_0.body_q.numpy()[0][3:7]
        return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))

    def sun_facing_wings(self):
        yaw = self.yaw()
        if self.sun[0] is None:
            self.sun[0] = yaw + math.radians(15)
        self.record_meta.update(sun_az=self.sun[0], sun_el=self.sun[1])
        phi = (self.sun[0] - yaw + math.pi) % (2 * math.pi) - math.pi
        lim = math.radians(120)
        return {"solar_wing_l": min(lim, max(0.0, math.pi / 2 - phi)), "solar_wing_r": min(lim, max(0.0, math.pi / 2 + phi))}

    def run_sequence(self, name):
        if name == "wings_deploy":
            self.queue.append(dict(self.sun_facing_wings(), _dur=6.0))
            return
        self.queue += [dict(step, _dur=dur) for step, dur in [({k: v for k, v in s.items() if k in self.poses}, d) for s, d in SEQUENCES[name]]]

    def toggle(self, a, b, probe, value):
        self.run_sequence(a if abs(self.poses.get(probe, 0.0) - value) > 1e-3 else b)

    def update(self):
        if self._pressed("1"):
            self.toggle("airlock_open", "airlock_close", "airlock_hatch", math.radians(100))
        if self._pressed("2"):
            self.toggle("stair_deploy", "stair_stow", "rear_stair", 0.0)
        if self._pressed("3"):
            self.toggle("wings_deploy", "wings_stow", "solar_wing_l", self.sun_facing_wings()["solar_wing_l"])
        if self._pressed("4"):
            self.toggle("arm_reach", "arm_stow", "arm_shoulder", 0.9)
        if self._pressed("f"):
            self.lights_on = not self.lights_on
        if self._pressed("e"):
            self.track = not self.track
        while self.demo and self.sim_time >= self.demo[0][0]:
            _, kind, arg = self.demo.pop(0)
            if kind == "drive":
                self.speed, self.steer = arg
            elif kind == "seq":
                self.run_sequence(arg)
            elif kind == "track":
                self.track = arg
            elif kind == "lights":
                self.lights_on = arg
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
        if self.track and "hga_azimuth" in self.poses:
            q = self.state_0.body_q.numpy()[0]
            yaw = self.yaw()
            az = (self.earth[0] - yaw + math.pi) % (2 * math.pi) - math.pi
            self.poses["hga_azimuth"] += (az - self.poses["hga_azimuth"]) * 0.05
            self.poses["hga_elevation"] += (self.earth[1] - HGA_BORESIGHT_EL - self.poses["hga_elevation"]) * 0.05

    def render_extra(self):
        if not self.light_sites or not self.lights_on:
            self.viewer.log_points("lights", None)
            self.viewer.log_lines("light_beams", None, None, None)
            return
        bq = self.state_0.body_q.numpy()
        pts, ends, radii = [], [], []
        for s in self.light_sites:
            q = bq[s["body"]]
            tf = wp.transform(wp.vec3(*q[:3]), wp.quat(*q[3:7]))
            p = np.array(wp.transform_point(tf, wp.vec3(*s["p"])))
            d = np.array(wp.transform_vector(tf, wp.vec3(*s["d"])))
            pts.append(p)
            ends.append(p + d * (0.6 if s["r"] < 0.05 else 3.0))
            radii.append(max(0.04, s["r"] * 1.4))
        self.viewer.log_points("lights", wp.array(pts, dtype=wp.vec3), wp.array(radii, dtype=wp.float32), (1.0, 0.92, 0.65))
        self.viewer.log_lines("light_beams", wp.array(pts, dtype=wp.vec3), wp.array(ends, dtype=wp.vec3), (1.0, 0.85, 0.5), width=0.02)

    def gui(self, ui):
        super().gui(ui)
        ui.separator()
        ui.text("Lunar Cruiser sequences")
        for name in SEQUENCES:
            if ui.button(name):
                self.run_sequence(name)
        _, self.lights_on = ui.checkbox("Lights (USD DiskLights; drawn as beams here)", self.lights_on)
        _, self.track = ui.checkbox("HGA tracks Earth", self.track)
        if self.queue or self.active_step:
            ui.text(f"sequence: {len(self.queue) + (1 if self.active_step else 0)} step(s) left")
        qd = self.state_0.body_qd.numpy()[0]
        ui.text(f"ground speed {np.linalg.norm(qd[:2]) * 3.6:5.1f} km/h")
        q = self.state_0.joint_q.numpy()
        for n in self.strut:
            ui.text(f"{n[:-10]:>4} strut {q[self.coord[n]] * 1000:+6.1f} mm")

    def test_final(self):
        super().test_final()
        q = self.state_0.joint_q.numpy()
        moved = float(np.linalg.norm(self.state_0.body_q.numpy()[0][:2] - self.start_xy))
        checks = {
            "drove more than 8 m": moved > 8.0,
            "airlock hatch open": q[self.coord["airlock_hatch"]] > math.radians(90),
            "stair deployed": abs(q[self.coord["rear_stair"]]) < 0.05 and abs(q[self.coord["rear_stair_lower"]]) < 0.05,
            "railings up": all(abs(q[self.coord[r]]) < 0.05 for r in RAILS),
            "solar wings out and sun-facing": all(q[self.coord[w]] > math.radians(45) for w in WINGS),
        }
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "lunar cruiser showcase checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="lunar_cruiser", max_speed=15.0, substeps=10)
        parser.add_argument("--demo", action="store_true", help="Run the scripted showcase (drive, wings, airlock, stair, arm, lights).")
        parser.add_argument("--lights", action="store_true", help="Start with the lights on.")
        parser.add_argument("--sun-az", type=float, default=None, help="Sun azimuth [deg, world]; default: 15 deg left of the heading at deploy.")
        parser.add_argument("--sun-el", type=float, default=6.0, help="Sun elevation [deg]; polar sun is low.")
        parser.add_argument("--earth-az", type=float, default=35.0, help="Earth azimuth for HGA tracking [deg, world frame].")
        parser.add_argument("--earth-el", type=float, default=25.0, help="Earth elevation for HGA tracking [deg].")
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
