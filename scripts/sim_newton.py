import argparse
import json
import math
import os
import re
import sys

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMuJoCo
from pxr import Usd, UsdPhysics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

G_MOON = 1.625
PASSIVE = {"landing_gear", "suspension", "linkage"}
RELATIVE = {"active_suspension"}
LOCKED = {"deploy"}
CHECKS = ("settle", "servo", "drive", "thrust", "touchdown")
STAGE = re.compile(r"_(stage\d+|inner|compression|tension\d+|outer|piston)$")


def usd_joints(stage):
    out = {}
    for prim in stage.Traverse():
        if not (prim.IsA(UsdPhysics.RevoluteJoint) or prim.IsA(UsdPhysics.PrismaticJoint)):
            continue
        get = lambda n, d=None: prim.GetAttribute(n).Get() if prim.HasAttribute(n) else d
        if get("physics:excludeFromArticulation", False):
            continue
        revolute = prim.IsA(UsdPhysics.RevoluteJoint)
        sc = math.radians(1) if revolute else 1.0
        lo, hi = get("physics:lowerLimit"), get("physics:upperLimit")
        out[prim.GetName()] = {"revolute": revolute, "role": get("joint:role", "actuated"),
                               "drive": get("joint:driveKind", "none"), "load": get("joint:crushLoad"),
                               "limit": (lo * sc, hi * sc) if lo is not None and hi is not None else None}
    return out


def servo_target(spec):
    lo, hi = spec["limit"] or (-1.0, 1.0)
    t = 0.5 * (hi if abs(hi) >= abs(lo) else lo)
    return max(-math.pi / 2, min(math.pi / 2, t)) if spec["revolute"] else t


class Sim:
    def __init__(self, a):
        asset_dir = os.path.join(assetcfg.ROOT, "build", a.asset, "usd", a.asset)
        usd = os.path.join(asset_dir, f"{a.asset}.usda")
        tj = os.path.join(asset_dir, "thrusters.json")
        self.thrusters = json.load(open(tj))["thrusters"] if os.path.exists(tj) else []
        stage = Usd.Stage.Open(usd)
        for kv in [x for x in a.variants.split(",") if x]:
            k, v = kv.split("=")
            stage.GetPrimAtPath(f"/{a.asset}").GetVariantSet(k).SetVariantSelection(v)
        self.specs = usd_joints(stage)

        sl = math.radians(a.slope)
        b = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=(-G_MOON * math.sin(sl), 0.0, -G_MOON * math.cos(sl)))
        SolverMuJoCo.register_custom_attributes(b)
        b.default_shape_cfg.mu = a.mu
        b.default_shape_cfg.ke = 2.0e5
        b.default_shape_cfg.kd = 5.0e3
        b.add_usd(stage, collapse_fixed_joints=False, enable_self_collisions=False, hide_collision_shapes=True)
        b.joint_q[2] += a.drop
        b.add_ground_plane()
        m = self.model = b.finalize()
        self.labels = [s.rsplit("/", 1)[-1] for s in b.joint_label]
        self.blabels = [s.rsplit("/", 1)[-1] for s in m.body_label]
        q_start = m.joint_q_start.numpy()
        qd_start = m.joint_qd_start.numpy()
        self.coord = {n: int(q_start[i]) for i, n in enumerate(self.labels)}
        self.dof = {n: int(qd_start[i]) for i, n in enumerate(self.labels)}
        free = int(newton.JointType.FREE)
        jtype, jchild = m.joint_type.numpy(), m.joint_child.numpy()
        jfree = next((i for i in range(m.joint_count) if jtype[i] == free), None)
        self.root = int(jchild[jfree]) if jfree is not None else 0
        self.free_q = int(q_start[jfree]) if jfree is not None else None
        self.free_qd = int(qd_start[jfree]) if jfree is not None else None
        self.mass = m.body_mass.numpy()
        print(f"loaded {a.asset}: {m.body_count} bodies, {m.joint_count} joints, {m.shape_count} shapes, "
              f"total mass {self.mass.sum():.0f} kg, root '{self.blabels[self.root]}'")

        self.solver = SolverMuJoCo(m, iterations=100, ls_iterations=50, cone="elliptic", nconmax=256, njmax=1200)
        self.s0, self.s1 = m.state(), m.state()
        self.ctrl = m.control()
        newton.eval_fk(m, m.joint_q, m.joint_qd, self.s0)
        self.pipe = newton.CollisionPipeline(m)
        self.contacts = self.pipe.contacts()
        self.viewer = newton.viewer.ViewerGL() if a.viewer == "gl" else None
        if self.viewer:
            self.viewer.set_model(m)
        self.fps, self.sub, self.t = 60, 10, 0.0
        self.tq = self.ctrl.joint_target_q.numpy()
        self.tv = self.ctrl.joint_target_qd.numpy()
        self.failures = []

    def run(self, seconds, force=None, on_frame=None):
        dt = 1.0 / self.fps / self.sub
        for _ in range(int(seconds * self.fps)):
            if on_frame:
                on_frame()
            self.pipe.collide(self.s0, self.contacts)
            for _ in range(self.sub):
                self.s0.clear_forces()
                if force is not None:
                    self.s0.body_f.assign(force)
                self.solver.step(self.s0, self.s1, self.ctrl, self.contacts, dt)
                self.s0, self.s1 = self.s1, self.s0
            self.t += 1.0 / self.fps
            if self.viewer:
                self.viewer.begin_frame(self.t)
                self.viewer.log_state(self.s0)
                self.viewer.end_frame()

    def pose(self):
        bq = self.s0.body_q.numpy()[self.root]
        qx, qy = bq[3], bq[4]
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * (qx * qx + qy * qy)))))
        v = np.linalg.norm(self.s0.body_qd.numpy()[self.root][:3])
        return bq[:3], tilt, v

    def q(self, name):
        return float(self.s0.joint_q.numpy()[self.coord[name]])

    def check(self, tag, ok, msg):
        print(f"[{tag}] {'ok  ' if ok else 'FAIL'} {msg}")
        if not ok:
            self.failures.append(f"{tag}: {msg}")

    def contact_summary(self):
        c = self.contacts
        n = int(c.rigid_contact_count.numpy()[0])
        sb = self.model.shape_body.numpy()
        s0, s1 = c.rigid_contact_shape0.numpy()[:n], c.rigid_contact_shape1.numpy()[:n]
        per = {}
        for a, b in zip(s0, s1):
            for s in (a, b):
                if s >= 0 and sb[s] >= 0:
                    per[self.blabels[sb[s]]] = per.get(self.blabels[sb[s]], 0) + 1
        cap = c.rigid_contact_max if isinstance(c.rigid_contact_max, int) else "?"
        return f"{n}/{cap} " + " ".join(f"{k}={v}" for k, v in sorted(per.items()))

    def joints(self, pred):
        return [n for n, s in self.specs.items() if n in self.coord and pred(s)]

    def struts(self):
        out = {}
        for n in self.joints(lambda s: s["role"] in PASSIVE and not s["revolute"]):
            out.setdefault(STAGE.sub("", n), []).append(n)
        return out

    def strut_travel(self, groups):
        q = self.s0.joint_q.numpy()
        return {g: sum(float(q[self.coord[n]]) for n in names) for g, names in groups.items()}

    def settle(self, seconds=5.0):
        for k in range(int(seconds)):
            self.run(1.0)
            p, tilt, v = self.pose()
            print(f"[settle] t={self.t:5.2f} z={p[2]:6.3f} tilt={tilt:5.2f} deg |v|={v:.3f} m/s")
        travel = self.strut_travel(self.struts())
        if travel:
            print("[settle] strut travel mm: " + " ".join(f"{g}={v * 1000:+.1f}" for g, v in travel.items()))
        rev = self.joints(lambda s: s["role"] in PASSIVE and s["revolute"])
        if rev:
            print("[settle] passive joints deg: " + " ".join(f"{n}={math.degrees(self.q(n)):+.1f}" for n in rev))
        print("[settle] ground contacts: " + self.contact_summary())
        p, tilt, v = self.pose()
        self.check("settle", tilt < 2.0 and v < 0.05, f"tilt {tilt:.2f} deg, |v| {v:.3f} m/s after {seconds:.0f} s")

    def servo(self, hold=2.0):
        names = self.joints(lambda s: s["drive"] == "position" and s["role"] not in PASSIVE | LOCKED)
        for n in names:
            spec = self.specs[n]
            i = self.coord[n]
            home = self.tq[i]
            target = home + 0.5 * ((spec["limit"] or (0, 0.2))[0] - home) if spec["role"] in RELATIVE else servo_target(spec)
            self.tq[i] = target
            self.ctrl.joint_target_q.assign(self.tq)
            self.run(hold * (3 if not spec["revolute"] and abs(target) > 1 else 1))
            sc, unit = (180 / math.pi, "deg") if spec["revolute"] else (1.0, "m")
            err = abs(self.q(n) - target) * sc
            tol = 1.0 if spec["revolute"] else 0.05
            self.check("servo", err < tol, f"{n} ({spec['role']}) target {target * sc:+.2f} {unit} -> {self.q(n) * sc:+.2f} {unit}")
            self.tq[i] = home
            self.ctrl.joint_target_q.assign(self.tq)
            self.run(hold)

    def drive(self, speed, seconds=5.0):
        names = self.joints(lambda s: s["drive"] == "velocity")
        if not names:
            return
        p0, _, _ = self.pose()
        for n in names:
            self.tv[self.dof[n]] = speed
        self.ctrl.joint_target_qd.assign(self.tv)
        self.run(seconds)
        p1, tilt, _ = self.pose()
        qd = self.s0.joint_qd.numpy()
        mean = np.mean([qd[self.dof[n]] for n in names])
        dist = float(np.linalg.norm((p1 - p0)[:2]))
        self.check("drive", dist > 0.1 and tilt < 15, f"{len(names)} velocity joints at {speed:+.2f} -> mean {mean:+.2f}, "
                                                       f"travelled {dist:.2f} m, tilt {tilt:.1f} deg in {seconds:.0f} s")
        for n in names:
            self.tv[self.dof[n]] = 0.0
        self.ctrl.joint_target_qd.assign(self.tv)
        self.run(1.0)

    def thrust(self):
        mains = [th for th in self.thrusters if th["kind"] == "main"]
        if not mains:
            return
        w = self.mass.sum() * G_MOON
        vac = sum(th["thrustVac"] for th in mains)
        tmin = sum(th.get("thrustMin", th["thrustVac"]) for th in mains)
        print(f"[thrust] weight {w / 1000:.2f} kN, {len(mains)} main engine(s) {vac / 1000:.2f} kN vac -> hover throttle "
              f"{w / vac * 100:.1f}% (min {tmin / vac * 100:.0f}%)")
        self.check("thrust", w < vac, f"thrust-to-weight {vac / w:.2f} in lunar gravity")

        def force(level):
            f = np.zeros((self.model.body_count, 6), np.float32)
            for th in mains:
                f[self.blabels.index(th["link"]), :3] += -np.array(th["flow_dir"]) * w * level * th["thrustVac"] / vac
            return wp.array(f, dtype=wp.spatial_vector)

        self.run(1.0, force(1.0))
        self.run(1.0, force(1.05))
        v0 = self.s0.body_qd.numpy()[self.root][2]
        self.run(1.0, force(1.05))
        acc = self.s0.body_qd.numpy()[self.root][2] - v0
        self.check("thrust", abs(acc - 0.05 * G_MOON) < 0.03, f"1.05 x weight: vertical accel {acc:+.4f} m/s^2 "
                                                               f"(expected {0.05 * G_MOON:+.4f}, open loop)")

    def touchdown(self, vz, vh, height, seconds=6.0):
        groups = self.struts()
        if not groups or self.free_q is None:
            return
        m = self.model
        q, qd = m.joint_q.numpy().copy(), m.joint_qd.numpy().copy()
        q[self.free_q:self.free_q + 3] = (0.0, 0.0, height)
        q[self.free_q + 3:self.free_q + 7] = (0.0, 0.0, 0.0, 1.0)
        qd[:] = 0.0
        qd[self.free_qd:self.free_qd + 3] = (vh, 0.0, -vz)
        self.s0, self.s1 = m.state(), m.state()
        self.s0.joint_q.assign(q)
        self.s0.joint_qd.assign(qd)
        newton.eval_fk(m, self.s0.joint_q, self.s0.joint_qd, self.s0)
        v0 = self.s0.body_qd.numpy()[self.root][:3]
        bq0 = self.s0.body_q.numpy()
        exits = []
        for th in self.thrusters:
            if th["kind"] == "main":
                li = self.blabels.index(th["link"])
                exits.append((li, np.array(th["exit_center_m"]) + (0, 0, height) - bq0[li][:3]))
        peak = {g: 0.0 for g in groups}
        stats = {"tilt": 0.0, "clear": float("inf")}

        def rot(qv, v):
            x, y, z, w = qv
            u = np.array((x, y, z))
            return v + 2 * np.cross(u, np.cross(u, v) + w * v)

        def sample():
            for g, v in self.strut_travel(groups).items():
                peak[g] = v if abs(v) > abs(peak[g]) else peak[g]
            stats["tilt"] = max(stats["tilt"], self.pose()[1])
            bq = self.s0.body_q.numpy()
            for li, local in exits:
                stats["clear"] = min(stats["clear"], float((bq[li][:3] + rot(bq[li][3:], local))[2]))

        print(f"[touchdown] reset at {height:.2f} m, body velocity ({v0[0]:+.2f}, {v0[1]:+.2f}, {v0[2]:+.2f}) m/s")
        self.run(seconds, on_frame=sample)
        final = self.strut_travel(groups)
        for g in groups:
            loads = [self.specs[n]["load"] for n in groups[g] if self.specs[n]["load"]]
            note = f" stages {'/'.join(f'{l / 1000:.1f}' for l in loads)} kN" if loads else ""
            print(f"[touchdown] {g:24s} peak {peak[g] * 1000:+7.1f} mm  final {final[g] * 1000:+7.1f} mm{note}")
        q = self.s0.joint_q.numpy()
        bottomed = [n for ns in groups.values() for n in ns
                    if self.specs[n]["limit"] and self.specs[n]["limit"][1] - self.specs[n]["limit"][0] > 1e-4
                    and min(abs(q[self.coord[n]] - lim) for lim in self.specs[n]["limit"] if abs(lim) > 1e-4) < 0.002]
        p, tilt, v = self.pose()
        if exits:
            print(f"[touchdown] min main-engine exit clearance {stats['clear']:.3f} m")
        self.check("touchdown", tilt < 10.0 and v < 0.05 and not bottomed,
                   f"vz {vz:.2f} m/s vh {vh:.2f} m/s: peak tilt {stats['tilt']:.1f} deg, final tilt {tilt:.2f} deg, "
                   f"|v| {v:.3f} m/s" + (f", bottomed out: {', '.join(bottomed)}" if bottomed else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", default="mk1")
    ap.add_argument("--drop", type=float, default=0.5)
    ap.add_argument("--mu", type=float, default=0.8, help="contact friction coefficient")
    ap.add_argument("--viewer", default="null")
    ap.add_argument("--variants", default="", help="variant selections, e.g. Offloader=crane,Propellant=dry")
    ap.add_argument("--checks", default=",".join(CHECKS), help="comma list of " + ", ".join(CHECKS))
    ap.add_argument("--drive-speed", type=float, default=2.0, help="velocity-drive target (rad/s or m/s)")
    ap.add_argument("--slope", type=float, default=0.0, help="surface slope in degrees (tilts gravity about +Y)")
    ap.add_argument("--td-vz", type=float, default=1.0, help="touchdown sink rate, m/s")
    ap.add_argument("--td-vh", type=float, default=0.3, help="touchdown horizontal speed along +X, m/s")
    ap.add_argument("--td-height", type=float, default=0.02, help="footpad height above the surface at reset, m")
    a = ap.parse_args()
    sim = Sim(a)
    checks = a.checks.split(",")
    sim.settle()
    if "servo" in checks:
        sim.servo()
    if "drive" in checks:
        sim.drive(a.drive_speed)
    if "thrust" in checks:
        sim.thrust()
    if "touchdown" in checks:
        sim.touchdown(a.td_vz, a.td_vh, a.td_height)
    p, tilt, v = sim.pose()
    print(f"[end] t={sim.t:5.2f} z={p[2]:6.3f} tilt={tilt:5.2f} deg |v|={v:.3f} m/s")
    if sim.failures:
        raise SystemExit(f"{len(sim.failures)} check(s) failed")


if __name__ == "__main__":
    main()
