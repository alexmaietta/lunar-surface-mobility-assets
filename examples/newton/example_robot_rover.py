import glob
import math
import os

import numpy as np
import warp as wp

import newton
import newton.examples

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
G_MOON = 1.625
MODES = ("ackermann", "crab", "spin")
TOGGLES = {"h": "hatch", "t": "stair", "g": "latch"}


def find_usd(asset):
    hits = glob.glob(os.path.join(REPO, "assets", "*", "*", "*", "usd", f"{asset}.usda"))
    hits += glob.glob(os.path.join(REPO, "build", asset, "usd", asset, f"{asset}.usda"))
    if not hits:
        raise SystemExit(f"no USD for '{asset}': build it with ./pipeline.sh {asset} or pass --usd")
    return hits[0]


def usd_roles(stage):
    from pxr import UsdPhysics

    out = {}
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.Joint) and prim.HasAttribute("joint:role"):
            out[prim.GetName()] = prim.GetAttribute("joint:role").Get()
    return out


class Example:
    def __init__(self, viewer, args):
        self.fps = 60
        self.frame_dt = 1.0 / self.fps
        self.sim_substeps = args.substeps
        self.sim_dt = self.frame_dt / self.sim_substeps
        self.sim_time = 0.0
        self.viewer = viewer
        self.world_count = args.world_count
        self.max_speed = args.max_speed
        self.speed = float(args.speed)
        self.steer = math.radians(args.steer)
        self.mode = 0
        self.ride = 0.0
        self.keys_prev = {}
        self.record = {"body_q": [], "t": [], "lights": []} if args.record else None

        from pxr import Usd

        usd = args.usd or find_usd(args.asset)
        stage = Usd.Stage.Open(usd)
        root = stage.GetDefaultPrim()
        for kv in [x for x in (args.variants or "").split(",") if x]:
            k, v = kv.split("=")
            root.GetVariantSet(k).SetVariantSelection(v)
        if root.GetVariantSets().HasVariantSet("Physics"):
            root.GetVariantSet("Physics").SetVariantSelection(args.physics)
        roles = usd_roles(stage)

        newton.use_coord_layout_targets = True
        g = 9.81 if args.earth else G_MOON
        rover = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=(0.0, 0.0, -g))
        newton.solvers.SolverMuJoCo.register_custom_attributes(rover)
        rover.default_shape_cfg.mu = 0.8
        rover.default_shape_cfg.ke = 2.0e5
        rover.default_shape_cfg.kd = 5.0e3
        rover.add_usd(stage, xform=wp.transform(wp.vec3(0.0, 0.0, args.drop), wp.quat_identity()),
                      collapse_fixed_joints=False, enable_self_collisions=False, hide_collision_shapes=True)
        self.labels = [s.rsplit("/", 1)[-1] for s in rover.joint_label]
        blabels = [s.rsplit("/", 1)[-1] for s in rover.body_label]
        self.coord = {n: rover.joint_q_start[i] for i, n in enumerate(self.labels)}
        self.dof = {n: rover.joint_qd_start[i] for i, n in enumerate(self.labels)}
        self.role = {n: roles.get(n, "") for n in self.labels}

        q0 = np.array(rover.body_q)
        self.wheels = {}
        for n in self.labels:
            if n.endswith("_wheel") and self.role[n] == "drive":
                p = q0[blabels.index(n)][:3]
                corner = n[: -len("_wheel")]
                steer = f"{corner}_steer" if f"{corner}_steer" in self.coord else None
                self.wheels[corner] = {"x": float(p[0]), "y": float(p[1]), "r": float(p[2] - args.drop), "steer": steer}
        self.steer_names = [w["steer"] for w in self.wheels.values() if w["steer"]]
        self.lim = {n: (rover.joint_limit_lower[self.dof[n]], rover.joint_limit_upper[self.dof[n]]) for n in self.labels
                    if self.role[n] not in ("", "drive")}
        fixed_x = [w["x"] for w in self.wheels.values() if not w["steer"]]
        self.turn_x = float(np.mean(fixed_x)) if fixed_x else 0.0
        self.all_steer = bool(self.wheels) and all(w["steer"] for w in self.wheels.values())
        self.servo = [n for n in self.labels if self.role[n] in ("arm", "camera", "antenna", "solar", "hatch", "latch", "stair", "railing")]
        self.active = [n for n in self.labels if self.role[n] == "active_suspension"]
        self.poses = {n: 0.0 for n in self.servo}
        self.args, self.stage, self.blabels = args, stage, blabels
        start = self.initial_pose()
        for n, v in start.items():
            rover.joint_q[self.coord[n]] = v
        self.coords_per_world = rover.joint_coord_count
        self.dofs_per_world = rover.joint_dof_count

        builder = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=(0.0, 0.0, -g))
        builder.replicate(rover, self.world_count)
        builder.add_ground_plane(color=(0.42, 0.41, 0.39))
        self.model = builder.finalize()
        self.solver = newton.solvers.SolverMuJoCo(self.model, iterations=100, ls_iterations=50, cone="elliptic", impratio=10,
                                                  njmax=1200, nconmax=256)
        self.state_0, self.state_1 = self.model.state(), self.model.state()
        self.control = self.model.control()
        newton.eval_fk(self.model, self.model.joint_q, self.model.joint_qd, self.state_0)
        self.pipe = newton.CollisionPipeline(self.model)
        self.contacts = self.pipe.contacts()
        self._tq = self.control.joint_target_q.numpy()
        self._tqd = self.control.joint_target_qd.numpy()
        self.home = {n: float(self._tq[self.coord[n]]) for n in self.active + self.servo}
        for n in self.servo:
            self.poses[n] = start.get(n, self.home[n])
        self._write_targets()
        self.viewer.set_model(self.model)
        self.viewer.set_world_offsets((10.0, 10.0, 0.0))
        kind = "all-wheel steer" if self.all_steer else ("steered" if self.steer_names else "skid steer")
        print(f"{args.asset or os.path.basename(usd)}: {len(self.wheels)} driven wheels, {kind}, "
              f"{len(self.active)} active suspension joints, servos: {', '.join(self.servo) or 'none'}")
        print("keys: i/k throttle, j/l steer, space stop, m steer mode, u/o ride height, h hatch, t stair, g latch")
        self.capture()

    def _corner_commands(self):
        r_mean = np.mean([w["r"] for w in self.wheels.values()]) if self.wheels else 0.3
        v = self.speed / 3.6
        out = {}
        mode = MODES[self.mode] if self.steer_names else "skid"
        if mode == "skid":
            half = max(abs(w["y"]) for w in self.wheels.values())
            yaw = v * math.tan(self.steer) / max(half, 1e-3) * 1.5
            for c, w in self.wheels.items():
                out[c] = (0.0, (v - yaw * w["y"]) / w["r"])
            return out
        if mode == "crab":
            for c, w in self.wheels.items():
                out[c] = (self.steer if w["steer"] else 0.0, v / w["r"])
            return out
        if mode == "spin" and self.all_steer:
            for c, w in self.wheels.items():
                ang = math.atan2(w["x"], -w["y"])
                sgn = 1.0
                if ang > math.pi / 2:
                    ang, sgn = ang - math.pi, -1.0
                elif ang < -math.pi / 2:
                    ang, sgn = ang + math.pi, -1.0
                out[c] = (ang, sgn * v * math.hypot(w["x"], w["y"]) / w["r"] / max(r_mean, 1e-3))
            return out
        if abs(self.steer) < 1e-4:
            return {c: (0.0, v / w["r"]) for c, w in self.wheels.items()}
        span = max(abs(w["x"] - self.turn_x) for w in self.wheels.values())
        radius = span / math.tan(self.steer)
        for c, w in self.wheels.items():
            dx, dy = w["x"] - self.turn_x, radius - w["y"]
            ang = math.atan2(dx, dy) if radius > 0 else -math.atan2(dx, -dy)
            out[c] = (ang if w["steer"] else 0.0, v * math.hypot(dx, dy) / abs(radius) / w["r"])
        return out

    def _write_targets(self):
        cmd = self._corner_commands()
        for world in range(self.world_count):
            qo, do = world * self.coords_per_world, world * self.dofs_per_world
            for c, (ang, omega) in cmd.items():
                w = self.wheels[c]
                if w["steer"]:
                    lo, hi = self.lim[w["steer"]]
                    self._tq[qo + self.coord[w["steer"]]] = float(np.clip(ang, lo, hi))
                self._tqd[do + self.dof[f"{c}_wheel"]] = omega
            for n in self.active:
                lo, hi = self.lim[n]
                self._tq[qo + self.coord[n]] = float(np.clip(self.home[n] - self.ride, lo, hi))
            for n in self.servo:
                self._tq[qo + self.coord[n]] = self.poses[n]
        self.control.joint_target_q.assign(self._tq)
        self.control.joint_target_qd.assign(self._tqd)

    def _pressed(self, key):
        down = self.viewer.is_key_down(key)
        edge = down and not self.keys_prev.get(key, False)
        self.keys_prev[key] = down
        return edge

    def _poll_keyboard(self):
        v = self.viewer
        if v.is_key_down("i"):
            self.speed = min(self.max_speed, self.speed + self.max_speed * 0.4 * self.frame_dt)
        if v.is_key_down("k"):
            self.speed = max(-self.max_speed, self.speed - self.max_speed * 0.4 * self.frame_dt)
        if v.is_key_down("space"):
            self.speed = 0.0
        if v.is_key_down("j"):
            self.steer = min(math.radians(45.0), self.steer + 0.8 * self.frame_dt)
        if v.is_key_down("l"):
            self.steer = max(-math.radians(45.0), self.steer - 0.8 * self.frame_dt)
        if v.is_key_down("u"):
            self.ride = min(0.6, self.ride + 0.3 * self.frame_dt)
        if v.is_key_down("o"):
            self.ride = max(-0.6, self.ride - 0.3 * self.frame_dt)
        if self._pressed("m"):
            self.mode = (self.mode + 1) % len(MODES)
            print("steer mode:", MODES[self.mode])
        for key, role in TOGGLES.items():
            if self._pressed(key):
                for n in [n for n in self.servo if self.role[n] == role]:
                    lo, hi = self.lim[n]
                    far = hi if abs(hi) >= abs(lo) else lo
                    self.poses[n] = self.home[n] if abs(self.poses[n] - self.home[n]) > 1e-3 else far

    def capture(self):
        self.graph = None
        if wp.get_device().is_cuda:
            with wp.ScopedCapture() as capture:
                self.simulate()
            self.graph = capture.graph

    def simulate(self):
        self.pipe.collide(self.state_0, self.contacts)
        for _ in range(self.sim_substeps):
            self.state_0.clear_forces()
            self.viewer.apply_forces(self.state_0)
            self.solver.step(self.state_0, self.state_1, self.control, self.contacts, self.sim_dt)
            self.state_0, self.state_1 = self.state_1, self.state_0

    def initial_pose(self):
        return {}

    def update(self):
        pass

    def render_extra(self):
        pass

    def step(self):
        self._poll_keyboard()
        self.update()
        self._write_targets()
        if self.graph:
            wp.capture_launch(self.graph)
        else:
            self.simulate()
        self.sim_time += self.frame_dt
        if self.record is not None and round(self.sim_time / self.frame_dt) % self.args.record_every == 0:
            self.record["body_q"].append(self.state_0.body_q.numpy()[: len(self.blabels)].copy())
            self.record["t"].append(self.sim_time)
            self.record["lights"].append(bool(getattr(self, "lights_on", False)))

    def save_record(self):
        if self.record is not None and self.record["t"]:
            np.savez_compressed(self.args.record, body_q=np.array(self.record["body_q"]), t=np.array(self.record["t"]),
                                lights=np.array(self.record["lights"]), bodies=np.array(self.blabels),
                                **{k: np.array(v) for k, v in getattr(self, "record_meta", {}).items()})
            print(f"recorded {len(self.record['t'])} frames -> {self.args.record}")

    def render(self):
        self.viewer.begin_frame(self.sim_time)
        self.viewer.log_state(self.state_0)
        self.viewer.log_contacts(self.contacts, self.state_0)
        self.render_extra()
        self.viewer.end_frame()

    def gui(self, ui):
        ui.text("Speed (km/h)")
        changed, value = ui.slider_float("##speed", self.speed, -self.max_speed, self.max_speed)
        if changed:
            self.speed = value
        ui.text("Steer (deg)")
        changed, deg = ui.slider_float("##steer", float(np.degrees(self.steer)), -45.0, 45.0)
        if changed:
            self.steer = math.radians(deg)
        if self.steer_names:
            ui.text(f"Steer mode: {MODES[self.mode]}")
            for i, name in enumerate(MODES):
                if ui.button(name):
                    self.mode = i
        if self.active:
            ui.text("Ride height offset (rad)")
            changed, value = ui.slider_float("##ride", self.ride, -0.6, 0.6)
            if changed:
                self.ride = value
        for n in self.servo:
            lo, hi = self.lim[n]
            ui.text(f"{n} ({self.role[n]})")
            changed, value = ui.slider_float(f"##{n}", float(self.poses[n]), float(max(lo, -math.pi)), float(min(hi, math.pi)))
            if changed:
                self.poses[n] = value

    def test_final(self):
        self.save_record()
        newton.examples.test_body_state(self.model, self.state_0, "all bodies are above the ground", lambda q, qd: q[2] > -0.05)
        print(f"final chassis position {np.round(self.state_0.body_q.numpy()[0][:3], 3)}, t = {self.sim_time:.1f} s")

    @staticmethod
    def create_parser():
        parser = newton.examples.create_parser()
        newton.examples.add_world_count_arg(parser)
        parser.add_argument("--asset", default="ltv_concept", help="Asset id (configs/<id>.py); finds assets/ or build/ USD.")
        parser.add_argument("--usd", default=None, help="Explicit path to a rover USD.")
        parser.add_argument("--variants", default="", help="Variant selections, e.g. Crew=cargo,Payload=crewed")
        parser.add_argument("--physics", default="physics", choices=["physics", "physx", "mujoco"], help="USD Physics variant.")
        parser.add_argument("--speed", type=float, default=0.0, help="Initial speed [km/h].")
        parser.add_argument("--steer", type=float, default=0.0, help="Initial steer angle [deg].")
        parser.add_argument("--max-speed", type=float, default=10.0, help="Throttle limit [km/h].")
        parser.add_argument("--drop", type=float, default=0.05, help="Initial height above the ground [m].")
        parser.add_argument("--substeps", type=int, default=10, help="Physics substeps per 60 Hz frame.")
        parser.add_argument("--earth", action="store_true", help="Earth gravity.")
        parser.add_argument("--record", default=None, help="Save body poses to this .npz (written at the end of a --test run).")
        parser.add_argument("--record-every", type=int, default=2, help="Record every N frames (2 = 30 fps).")
        parser.set_defaults(world_count=1)
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
