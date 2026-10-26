import glob
import json
import math
import os
import re

import numpy as np
import warp as wp

import newton
import newton.examples
from example_robot_rover import REPO, find_usd

G_MOON = 1.625
STAGE = re.compile(r"_(stage\d+|inner|compression|tension\d+|outer|piston)$")
PHYSICS = ("physics", "physx", "mujoco")
SKIP_SETS = {"Physics", "Fidelity"}


def gear_joints(stage):
    from pxr import UsdPhysics

    out = {}
    for prim in stage.Traverse():
        if not prim.IsA(UsdPhysics.PrismaticJoint):
            continue
        get = lambda n, d=None: prim.GetAttribute(n).Get() if prim.HasAttribute(n) else d
        if get("physics:excludeFromArticulation", False) or get("joint:role") != "landing_gear":
            continue
        out[prim.GetName()] = {"limit": (get("physics:lowerLimit"), get("physics:upperLimit")), "load": get("joint:crushLoad")}
    return out


def landers():
    import sys

    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import assetcfg

    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "configs", "*.py"))):
        a = os.path.splitext(os.path.basename(p))[0]
        if assetcfg.load(a).ASSET_PATH.endswith("/lander"):
            out.append(a)
    return out


def quat_rotate(q, v):
    u, w = q[:3], q[3]
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def parse_variants(text):
    return dict(kv.split("=") for kv in (text or "").split(",") if "=" in kv)


class Example:
    def __init__(self, viewer, args):
        self.fps = 60
        self.frame_dt = 1.0 / self.fps
        self.viewer = viewer
        self.args = args
        self.keys_prev = {}
        self.assets = landers()
        self.variants = parse_variants(args.variants)
        self.crush_scale = 1.0
        self.rebuild_requested = False
        self.since_drop = 0.0
        self.build()

    def build(self):
        from pxr import Usd

        a = self.args
        self.world_count = a.world_count
        self.sim_substeps = a.substeps
        self.sim_dt = self.frame_dt / self.sim_substeps
        usd = a.usd or find_usd(a.asset)
        stage = Usd.Stage.Open(usd)
        root = stage.GetDefaultPrim()
        sets = root.GetVariantSets()
        self.variant_sets = {}
        for name in sets.GetNames():
            vs = sets.GetVariantSet(name)
            if name in self.variants and self.variants[name] in vs.GetVariantNames():
                vs.SetVariantSelection(self.variants[name])
            if name not in SKIP_SETS:
                self.variant_sets[name] = (list(vs.GetVariantNames()), vs.GetVariantSelection())
        if sets.HasVariantSet("Physics"):
            sets.GetVariantSet("Physics").SetVariantSelection(a.physics)
        self.gear = gear_joints(stage)
        if not self.gear:
            raise SystemExit(f"{a.asset}: no prismatic landing_gear joints")
        tj = os.path.join(os.path.dirname(usd), "thrusters.json")
        thrusters = json.load(open(tj))["thrusters"] if os.path.exists(tj) else []

        lander = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=self.gravity())
        newton.solvers.SolverMuJoCo.register_custom_attributes(lander)
        lander.default_shape_cfg.mu = a.mu
        lander.add_usd(stage, collapse_fixed_joints=False, enable_self_collisions=False, hide_collision_shapes=True)
        labels = [s.rsplit("/", 1)[-1] for s in lander.joint_label]
        self.blabels = [s.rsplit("/", 1)[-1] for s in lander.body_label]
        q_start, qd_start = lander.joint_q_start, lander.joint_qd_start
        free = next(i for i, t in enumerate(lander.joint_type) if t == newton.JointType.FREE)
        self.free_q, self.free_qd = q_start[free], qd_start[free]
        self.root = lander.joint_child[free]
        self.coord = {n: q_start[i] for i, n in enumerate(labels)}
        dof = {n: qd_start[i] for i, n in enumerate(labels)}
        self.groups = {}
        for n in self.gear:
            if n in self.coord:
                self.groups.setdefault(STAGE.sub("", n), []).append(n)
        self.coords_per_world = lander.joint_coord_count
        self.dofs_per_world = lander.joint_dof_count
        self.bodies_per_world = lander.body_count
        self.mass = float(sum(lander.body_mass))
        self.exits = [(self.blabels.index(th["link"]), np.array(th["exit_center_m"])) for th in thrusters if th["kind"] == "main"]

        builder = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=self.gravity())
        builder.replicate(lander, self.world_count)
        builder.add_ground_plane(color=(0.42, 0.41, 0.39))
        self.model = builder.finalize()
        self.solver = newton.solvers.SolverMuJoCo(self.model, iterations=100, ls_iterations=50, cone="elliptic",
                                                  njmax=1200 * self.world_count, nconmax=256 * self.world_count)
        self.state_0, self.state_1 = self.model.state(), self.model.state()
        self.control = self.model.control()
        self.pipe = newton.CollisionPipeline(self.model)
        self.contacts = self.pipe.contacts()
        self.friction0 = self.model.joint_friction.numpy().copy()
        self.gear_dofs = np.array([w * self.dofs_per_world + dof[n] for w in range(self.world_count) for n in self.gear if n in dof])
        self.crushable = bool(np.any(self.friction0[self.gear_dofs] > 0)) if len(self.gear_dofs) else False
        self.drop()
        if hasattr(self.viewer, "clear_model"):
            self.viewer.clear_model()
        self.viewer.set_model(self.model)
        self.viewer.set_world_offsets((a.spacing, 0.0, 0.0))
        self.apply_crush_scale()
        loads = sorted({round(g["load"] / 1000, 1) for g in self.gear.values() if g["load"]})
        chosen = ", ".join(f"{k}={v[1]}" for k, v in self.variant_sets.items())
        print(f"{a.asset} ({chosen}): {self.mass:.0f} kg, {len(self.groups)} struts ({len(self.gear)} gear joints"
              + (f", crush stages {'/'.join(map(str, loads))} kN" if loads else ", springs") + f"), slope {a.slope:.1f} deg")
        print("sink rates m/s: " + " ".join(f"{v:.2f}" for v in self.sink) + f", drift {a.vh:.2f} m/s at {a.heading:.0f} deg")
        print("keys: r re-drop")
        self.capture()

    def gravity(self):
        sl = math.radians(self.args.slope)
        return (-G_MOON * math.sin(sl), 0.0, -G_MOON * math.cos(sl))

    def apply_slope(self):
        self.model.set_gravity(self.gravity())
        self.solver.notify_model_changed(newton.ModelFlags.MODEL_PROPERTIES)
        self.capture()

    def apply_mu(self):
        mu = self.model.shape_material_mu.numpy()
        mu[:] = self.args.mu
        self.model.shape_material_mu.assign(mu)
        self.solver.notify_model_changed(newton.ModelFlags.SHAPE_PROPERTIES)
        self.capture()

    def apply_crush_scale(self):
        if not self.crushable:
            return
        f = self.friction0.copy()
        f[self.gear_dofs] *= self.crush_scale
        self.model.joint_friction.assign(f)
        self.solver.notify_model_changed(newton.ModelFlags.JOINT_DOF_PROPERTIES)

    def drop(self):
        m, a = self.model, self.args
        n = self.world_count
        self.sink = [a.vz + (a.vz_max - a.vz) * i / max(n - 1, 1) if a.vz_max else a.vz for i in range(n)]
        q, qd = m.joint_q.numpy().copy(), np.zeros(m.joint_dof_count, np.float32)
        h = math.radians(a.heading)
        for w in range(n):
            qo, do = w * self.coords_per_world + self.free_q, w * self.dofs_per_world + self.free_qd
            base = q[qo:qo + 3].copy()
            q[qo:qo + 3] = (base[0], base[1], a.height)
            q[qo + 3:qo + 7] = (0.0, 0.0, 0.0, 1.0)
            qd[do:do + 3] = (a.vh * math.cos(h), a.vh * math.sin(h), -self.sink[w])
            for names in self.groups.values():
                for j in names:
                    q[w * self.coords_per_world + self.coord[j]] = 0.0
        self.state_0.joint_q.assign(q)
        self.state_0.joint_qd.assign(qd)
        newton.eval_fk(m, self.state_0.joint_q, self.state_0.joint_qd, self.state_0)
        self.sim_time = 0.0
        self.since_drop = 0.0
        bq = self.state_0.body_q.numpy()
        self.exit_local = [[(li, local + (0, 0, a.height) - bq[w * self.bodies_per_world + li][:3]) for li, local in self.exits]
                           for w in range(n)]
        self.peak = np.zeros((n, len(self.groups)))
        self.peak_tilt = np.zeros(n)
        self.clear = np.full(n, np.inf)

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

    def travel(self):
        q = self.state_0.joint_q.numpy().reshape(self.world_count, self.coords_per_world)
        return np.array([[sum(q[w, self.coord[n]] for n in names) for names in self.groups.values()]
                         for w in range(self.world_count)])

    def tilt(self):
        bq = self.state_0.body_q.numpy()
        out = []
        for w in range(self.world_count):
            qx, qy = bq[w * self.bodies_per_world + self.root][3:5]
            out.append(math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * (qx * qx + qy * qy))))))
        return np.array(out)

    def track(self):
        t = self.travel()
        self.peak = np.where(np.abs(t) > np.abs(self.peak), t, self.peak)
        self.peak_tilt = np.maximum(self.peak_tilt, self.tilt())
        bq = self.state_0.body_q.numpy()
        for w in range(self.world_count):
            for li, local in self.exit_local[w]:
                b = bq[w * self.bodies_per_world + li]
                self.clear[w] = min(self.clear[w], float((b[:3] + quat_rotate(b[3:], local))[2]))

    def _pressed(self, key):
        down = self.viewer.is_key_down(key)
        edge = down and not self.keys_prev.get(key, False)
        self.keys_prev[key] = down
        return edge

    def step(self):
        if self.rebuild_requested:
            self.rebuild_requested = False
            self.build()
        if self._pressed("r") or (self.args.loop and self.since_drop >= self.args.loop):
            self.drop()
        if self.graph:
            wp.capture_launch(self.graph)
        else:
            self.simulate()
        self.sim_time += self.frame_dt
        self.since_drop += self.frame_dt
        self.track()

    def render(self):
        self.viewer.begin_frame(self.sim_time)
        self.viewer.log_state(self.state_0)
        self.viewer.log_contacts(self.contacts, self.state_0)
        self.viewer.end_frame()

    def _slider(self, ui, label, attr, lo, hi, fmt="%.2f"):
        ui.text(label)
        changed, value = ui.slider_float(f"##{attr}", float(getattr(self.args, attr)), lo, hi, fmt)
        if changed:
            setattr(self.args, attr, value)
        return changed

    def gui(self, ui):
        a = self.args
        ui.text("Lander")
        idx = self.assets.index(a.asset) if a.asset in self.assets else 0
        changed, idx = ui.combo("##asset", idx, self.assets)
        if changed:
            a.asset, a.usd = self.assets[idx], None
            self.variants = {}
            self.rebuild_requested = True
        for name, (options, current) in self.variant_sets.items():
            changed, k = ui.combo(name, options.index(current) if current in options else 0, options)
            if changed:
                self.variants[name] = options[k]
                self.rebuild_requested = True
        changed, k = ui.combo("Physics", PHYSICS.index(a.physics), list(PHYSICS))
        if changed:
            a.physics = PHYSICS[k]
            self.rebuild_requested = True
        ui.text("Worlds")
        changed, n = ui.slider_int("##worlds", self.args.world_count, 1, 9)
        if changed:
            a.world_count = n
        ui.text("Substeps per frame")
        changed, s = ui.slider_int("##substeps", self.args.substeps, 2, 40)
        if changed:
            a.substeps = s
        if (a.world_count != self.world_count or a.substeps != self.sim_substeps) and ui.button("Rebuild"):
            self.rebuild_requested = True
        ui.separator()

        ui.text("Touchdown (applied on re-drop)")
        self._slider(ui, "Sink rate, first world (m/s)", "vz", 0.0, 4.0)
        if self.world_count > 1:
            self._slider(ui, "Sink rate, last world (m/s, 0 = same)", "vz_max", 0.0, 4.0)
        self._slider(ui, "Horizontal drift (m/s)", "vh", 0.0, 2.0)
        self._slider(ui, "Drift heading (deg from +X)", "heading", -180.0, 180.0, "%.0f")
        self._slider(ui, "Release height (m)", "height", 0.0, 3.0)
        changed, loop = ui.checkbox("Loop", bool(a.loop))
        if changed:
            a.loop = 6.0 if loop else 0.0
        if a.loop:
            ui.same_line()
            _, a.loop = ui.slider_float("##loop", float(a.loop), 2.0, 20.0, "every %.0f s")
        if ui.button("Re-drop (r)"):
            self.drop()
        ui.separator()

        ui.text("Surface (live)")
        if self._slider(ui, "Slope (deg, downhill +X)", "slope", 0.0, 30.0, "%.1f"):
            self.apply_slope()
        if self._slider(ui, "Friction", "mu", 0.05, 1.5):
            self.apply_mu()
        if self._slider(ui, "World spacing (m)", "spacing", 2.0, 30.0, "%.1f"):
            self.viewer.set_world_offsets((a.spacing, 0.0, 0.0))
        if self.crushable:
            ui.text("Crush load scale")
            changed, s = ui.slider_float("##crush", self.crush_scale, 0.1, 3.0, "x %.2f")
            if changed:
                self.crush_scale = s
                self.apply_crush_scale()
        ui.separator()

        tilt = self.tilt()
        names = list(self.groups)
        ui.text(f"{a.asset}: {self.mass:.0f} kg, t = {self.since_drop:.1f} s since drop")
        for w in range(self.world_count):
            i = int(np.argmax(np.abs(self.peak[w]))) if names else 0
            clear = f", nozzle {self.clear[w]:.2f} m" if self.exits and np.isfinite(self.clear[w]) else ""
            ui.text(f"world {w}: sink {self.sink[w]:.2f} m/s, tilt {tilt[w]:.1f} deg (peak {self.peak_tilt[w]:.1f}){clear}")
            if names:
                ui.text(f"  max stroke {names[i]} {self.peak[w, i] * 1000:+.0f} mm")

    def report(self):
        names = list(self.groups)
        final = self.travel()
        tilt = self.tilt()
        for w in range(self.world_count):
            print(f"world {w}: sink {self.sink[w]:.2f} m/s, peak tilt {self.peak_tilt[w]:.1f} deg, final tilt {tilt[w]:.2f} deg"
                  + (f", min nozzle clearance {self.clear[w]:.3f} m" if self.exits else ""))
            for i, g in enumerate(names):
                print(f"  {g:24s} peak {self.peak[w, i] * 1000:+7.1f} mm  final {final[w, i] * 1000:+7.1f} mm")

    def test_final(self):
        self.report()
        bq = self.state_0.body_q.numpy()
        z = np.array([bq[w * self.bodies_per_world + self.root][2] for w in range(self.world_count)])
        assert np.all(z > -0.5), f"lander sank through the surface: origin z {np.round(z, 3)} m"
        tilt = self.tilt()
        assert np.all(tilt < 10.0), f"lander tipped: final tilt {np.round(tilt, 1)} deg"

    @staticmethod
    def create_parser():
        parser = newton.examples.create_parser()
        newton.examples.add_world_count_arg(parser)
        parser.add_argument("--asset", default="apollo_lm", help="Lander asset id; finds assets/ or build/ USD.")
        parser.add_argument("--usd", default=None, help="Explicit path to a lander USD.")
        parser.add_argument("--variants", default="LandingGear=crush", help="Variant selections, e.g. LandingGear=spring,Propellant=dry")
        parser.add_argument("--physics", default="physics", choices=PHYSICS, help="USD Physics variant.")
        parser.add_argument("--vz", type=float, default=1.0, help="Sink rate at touchdown [m/s] (first world).")
        parser.add_argument("--vz-max", type=float, default=0.0, help="Sink rate of the last world; worlds sweep vz..vz-max.")
        parser.add_argument("--vh", type=float, default=0.3, help="Horizontal drift [m/s].")
        parser.add_argument("--heading", type=float, default=0.0, help="Drift direction [deg from +X].")
        parser.add_argument("--slope", type=float, default=0.0, help="Surface slope [deg], downhill along +X.")
        parser.add_argument("--height", type=float, default=0.02, help="Footpad height above the surface at release [m].")
        parser.add_argument("--mu", type=float, default=0.8, help="Footpad-surface friction.")
        parser.add_argument("--spacing", type=float, default=12.0, help="Distance between worlds [m].")
        parser.add_argument("--substeps", type=int, default=10, help="Physics substeps per 60 Hz frame.")
        parser.add_argument("--loop", type=float, default=0.0, help="Re-drop automatically every N seconds (0 = off).")
        parser.set_defaults(world_count=1, num_frames=360)
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
