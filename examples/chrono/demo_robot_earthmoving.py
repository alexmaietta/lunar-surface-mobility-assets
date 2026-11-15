import math
import os
import sys

import numpy as np
import pychrono as chrono

from demo_robot_rover import Example as RoverExample
from demo_robot_rover import G_MOON, HULL, REPO, InteractiveDriver, RoverDriver, UrdfRobot, find_urdf, vec

sys.path.insert(0, os.path.join(REPO, "scripts"))
import assetcfg

FRONT_TOOLS = ("dozer_blade", "v_blade", "loader_bucket", "drum_excavator", "rock_rake")
REAR_TOOLS = ("ripper", "box_blade", "roller_compactor", "dump_trailer")
FRONT_LIFTS = ("blade_lift", "loader_lift", "drum_arm", "rake_lift")
REAR_LIFTS = ("ripper_lift", "box_lift")
SECOND = ("blade_angle", "bucket", "wing_l")
BLADE, BUCKET, DRUM, RAKE, RIPPER, BOX, COMPACTOR = range(7)
KINDS = {"blade": BLADE, "bucket": BUCKET, "drum": DRUM, "rake": RAKE, "ripper": RIPPER, "box_blade": BOX, "compactor": COMPACTOR}
STORES = (BUCKET, DRUM, BOX)
BANDS = {BLADE: (0.12, 0.03, 0.35), RAKE: (0.10, 0.03, 0.12), BUCKET: (0.25, 0.03, 0.30), DRUM: (0.18, 0.18, 0.30),
         BOX: (0.12, 0.03, 0.25), RIPPER: (0.10, 0.05, 0.0), COMPACTOR: (0.12, 0.12, 0.0)}
NG, NC, MU_PILE, RIP_K = 6.0, 6.0, 0.6, 1.2e4


def make_terrain(X, Y, seed, craters, clear):
    rng = np.random.default_rng(seed)
    h = np.zeros_like(X)
    for k in range(6):
        kx, ky = rng.normal(0.0, 0.35, 2)
        h += 0.08 / (k + 1) * np.sin(kx * X + ky * Y + rng.uniform(0, 2 * np.pi))
    for _ in range(craters):
        cx, cy = rng.uniform(X.min(), X.max()), rng.uniform(Y.min(), Y.max())
        R = rng.uniform(0.3, 1.4)
        r = np.hypot(X - cx, Y - cy) / R
        h += np.where(r < 1.0, -0.18 * R * (1 - r * r), np.where(r < 1.5, 0.05 * R * (1 - (r - 1) / 0.5), 0.0))
    h += rng.normal(0.0, 0.003, h.shape)
    w = np.clip(np.hypot(X, Y) / clear - 0.6, 0.0, 1.0)
    i0, j0 = np.unravel_index(np.argmin(np.hypot(X, Y)), X.shape)
    return (h - h[i0, j0]) * (w * w * (3 - 2 * w))


class Soil:
    def __init__(self, terrain, cx, length, width, dx, args):
        import pychrono.vehicle as veh

        self.veh, self.terrain, self.cx, self.dx, self.args = veh, terrain, cx, dx, args
        self.ni, self.nj = int(round(length / 2 / dx)), int(round(width / 2 / dx))
        i = np.arange(-self.ni, self.ni + 1)
        j = np.arange(-self.nj, self.nj + 1)
        self.X, self.Y = np.meshgrid(cx + i * dx, j * dx)
        self.h = make_terrain(self.X, self.Y, args.seed, args.craters, 4.0)
        self.h0 = self.h.copy()
        self.comp = np.full(self.h.shape, args.initial_density)
        self.pushed = self.h.copy()
        self.write(np.ones(self.h.shape, bool))

    def write(self, mask):
        nodes = self.veh.ChSCMTerrainNodeLevelList()
        for r, c in zip(*np.nonzero(mask)):
            nodes.append(self.veh.ChSCMTerrainNodeLevel(chrono.ChVector2i(int(c) - self.ni, int(r) - self.nj), float(self.h[r, c])))
        if len(nodes):
            self.terrain.SetModifiedNodes(nodes)
        self.pushed[mask] = self.h[mask]

    def pull(self):
        for ij, level in self.terrain.GetModifiedNodes(False):
            c, r = ij.x + self.ni, ij.y + self.nj
            if 0 <= r < self.h.shape[0] and 0 <= c < self.h.shape[1]:
                self.h[r, c] = self.pushed[r, c] = level

    def sample(self, x, y):
        fc, fr = (x - self.X[0, 0]) / self.dx, (y - self.Y[0, 0]) / self.dx
        c, r = int(np.clip(np.floor(fc), 0, self.h.shape[1] - 2)), int(np.clip(np.floor(fr), 0, self.h.shape[0] - 2))
        u, v = min(max(fc - c, 0.0), 1.0), min(max(fr - r, 0.0), 1.0)
        h = self.h
        return float((h[r, c] * (1 - u) + h[r, c + 1] * u) * (1 - v) + (h[r + 1, c] * (1 - u) + h[r + 1, c + 1] * u) * v)

    def tools(self, rows):
        cell = self.dx * self.dx
        delta = np.zeros_like(self.h)
        out = []
        for e, f, slope, width, k, active, store, fill, back, front, push, adv in rows:
            acc = {"cut": 0.0, "pile": 0.0, "fill": 0.0}
            out.append(acc)
            if not active:
                continue
            reach = max(back, front, 0.7, push) + width
            c0, c1 = [int(np.clip(round((e[0] + s * reach - self.X[0, 0]) / self.dx), 0, self.h.shape[1] - 1)) for s in (-1, 1)]
            r0, r1 = [int(np.clip(round((e[1] + s * reach - self.Y[0, 0]) / self.dx), 0, self.h.shape[0] - 1)) for s in (-1, 1)]
            win = (slice(r0, r1 + 1), slice(c0, c1 + 1))
            px, py = self.X[win] - e[0], self.Y[win] - e[1]
            u, v = px * f[0] + py * f[1], -px * f[1] + py * f[0]
            band = np.abs(v) <= width * 0.5
            ze = e[2] + slope * v
            hv, cv = self.h[win], self.comp[win]
            if k == COMPACTOR:
                m = band & (np.abs(u) < front) & (hv > ze - 0.03)
                rho0 = 1300.0 + 600.0 * cv[m]
                cv[m] = np.minimum(cv[m] + 0.35 * (1.0 - cv[m]) * adv / (2.0 * front), 1.0)
                hv[m] -= 0.20 * (1.0 - rho0 / (1300.0 + 600.0 * cv[m]))
                continue
            if k == RIPPER:
                m = band & (u > -back) & (u < front) & (hv > ze) & (cv > 0.15)
                hv[m] += 0.06 * (hv[m] - ze[m]) * (cv[m] - 0.15)
                cv[m] = 0.15
                continue
            m = band & (u > -back) & (u < front)
            cut = m & (hv > ze)
            dh = np.where(cut, hv - ze, 0.0)
            acc["cut"] = float(dh.sum() * cell)
            if not store:
                rr = np.round((self.Y[win] + f[1] * push - self.Y[0, 0]) / self.dx).astype(int)
                cc = np.round((self.X[win] + f[0] * push - self.X[0, 0]) / self.dx).astype(int)
                ok = cut & (rr >= 0) & (rr < self.h.shape[0]) & (cc >= 0) & (cc < self.h.shape[1])
                np.add.at(delta, (rr[ok], cc[ok]), dh[ok])
            hv[cut] = ze[cut]
            if fill:
                fm = m & ~cut & (hv < ze)
                acc["fill"] = float((ze[fm] - hv[fm]).sum() * cell)
                hv[fm] = ze[fm]
            pile = band & (u > 0.0) & (u < 0.7) & (hv > ze)
            acc["pile"] = float((hv[pile] - ze[pile]).sum() * cell)
        self.apply(delta)
        return out

    def apply(self, delta):
        nz = delta != 0
        self.h[nz] += delta[nz]
        up = delta > 0
        self.comp[up] *= np.maximum(0.0, 1.0 - delta[up] / 0.2)

    def deposit(self, x, y, vol, radius):
        m = (self.X - x) ** 2 + (self.Y - y) ** 2 < radius * radius
        if vol > 0 and m.any():
            dz = vol / (m.sum() * self.dx * self.dx)
            self.h[m] += dz
            self.comp[m] *= max(0.0, 1.0 - dz / 0.2)

    def relax(self, iters, tan_lo, tan_hi, rate=0.4):
        h, comp, dx = self.h, self.comp, self.dx
        for _ in range(iters):
            delta = np.zeros_like(h)
            for (dr, dc), dist, w in (((0, 1), dx, rate), ((1, 0), dx, rate), ((1, 1), dx * 1.41421, rate * 0.5), ((1, -1), dx * 1.41421, rate * 0.5)):
                a = (slice(0, h.shape[0] - dr), slice(max(0, -dc), h.shape[1] - max(0, dc)))
                b = (slice(dr, h.shape[0]), slice(max(0, dc), h.shape[1] - max(0, -dc)))
                diff = h[a] - h[b]
                lim = (tan_lo + (tan_hi - tan_lo) * 0.5 * (comp[a] + comp[b])) * dist
                q = np.where(diff > lim, w * (diff - lim) * 0.5, np.where(diff < -lim, -w * (-diff - lim) * 0.5, 0.0))
                delta[a] -= q
                delta[b] += q
            self.apply(delta)

    def flush(self):
        self.write(np.abs(self.h - self.pushed) > 1e-5)

    def region(self, lo, hi):
        m = (self.X >= lo[0]) & (self.X <= hi[0]) & (self.Y >= lo[1]) & (self.Y <= hi[1])
        d = (self.h - self.h0)[m]
        cell = self.dx * self.dx
        return {"fill": float(d[d > 0].sum() * cell), "cut": float(-d[d < 0].sum() * cell), "crest": float(d.max(initial=0.0)),
                "density": float(self.comp[m].mean()) if m.any() else 0.0}


class Tool:
    def __init__(self, ex, name, mount):
        self.name = name
        cfg = assetcfg.load(name)
        ref = ex.chassis.GetFrameRefToAbs()
        self.pose = chrono.ChFramed(ref.TransformPointLocalToParent(vec(mount)), ref.GetRot())
        urdf = find_urdf(name)
        hulls = {n: HULL for n in getattr(cfg, "COLLIDERS", {})}
        self.robot = UrdfRobot(ex.system, urdf, self.pose, material=ex.mat, collision_types=hulls)
        weld = chrono.ChLinkLockLock()
        weld.Initialize(self.robot.chassis, ex.chassis, self.pose)
        weld.SetName(f"{name}_mount")
        ex.system.AddLink(weld)
        for name in self.robot.xlinks:
            b = self.robot.body(name)
            if b is not None:
                b.EnableCollision(False)
        self.edges = []
        for site in cfg.TOOL["sites"]:
            if site[4] != "tool_edge" or site[6].get("tool") not in KINDS:
                continue
            body = self.robot.body(site[1])
            frame = body.GetFrameRefToAbs()
            props = site[6]
            k = KINDS[props["tool"]]
            d = frame.TransformDirectionParentToLocal(self.pose.TransformDirectionLocalToParent(vec(site[3])))
            a = chrono.ChVector3d(0, 1, 0) if k == COMPACTOR else chrono.ChVector3d(0, 0, 1).Cross(d)
            a = a * (1.0 / max(a.Length(), 1e-6))
            self.edges.append({"name": site[0], "body": body, "p": frame.TransformPointParentToLocal(self.pose.TransformPointLocalToParent(vec(site[2]))),
                               "d": d, "a": a, "k": k, "width": float(props.get("width_m") or props.get("loosen_width_m") or 0.1),
                               "loosen": props.get("loosen_width_m"), "capacity": float(props.get("capacity_m3") or props.get("volume_m3") or 0.0),
                               "load": 0.0, "prev": None, "acc": body.AddAccumulator()})

    def edge(self, i=0):
        t = self.edges[i]
        return t["body"].GetFrameRefToAbs().TransformPointLocalToParent(t["p"])


class Example(RoverExample):
    def __init__(self, args):
        self.tools = {}
        super().__init__(args)
        self.front = self.tools.get("front")
        self.rear = self.tools.get("rear")
        j = self.robot.joints
        self.front_lift = next((n for n in FRONT_LIFTS if n in j), None)
        self.rear_lift = next((n for n in REAR_LIFTS if n in j), None)
        self.second = next((n for n in SECOND if n in j), None)
        self.drum = next((n for n, jj in j.items() if jj.role == "excavate"), None)
        self.raise_sign = {n: self.lift_gain(n, t) for n, t in ((self.front_lift, self.front), (self.rear_lift, self.rear)) if n and t}
        self.drum_dir = 0
        self.autopilot = args.task != "drive"
        self.lanes = [float(v) for v in args.lanes.split(",")]
        self.pass_i, self.phase, self.phase_t, self.stall_t = 0, "goto", 0.0, 0.0
        self.last_report = 0.0
        self.berm_lo, self.berm_hi = (args.berm_x - 0.6, -args.berm_length / 2), (args.berm_x + 2.5, args.berm_length / 2)
        self.borrow_lo, self.borrow_hi = (args.borrow_start, -args.berm_length / 2), (args.berm_x - 0.6, args.berm_length / 2)
        print(f"earthmoving: tools {', '.join(f'{k} {t.name}' for k, t in self.tools.items()) or 'none'}, "
              f"lifts {self.front_lift or '-'} / {self.rear_lift or '-'}, task {args.task}")
        if isinstance(self.driver, InteractiveDriver):
            print("tool keys: 1/2 front lift up/down, 3/4 blade angle or bucket curl, 5/6 rear lift up/down, 7 drum dig, 8 drum dump, "
                  "0 autopilot on/off")

    def configure_rover(self):
        a = self.args
        cfg = assetcfg.load(a.asset)
        mounts = {"front": getattr(cfg, "TOOL_FRONT", None), "rear": getattr(cfg, "TOOL_REAR", None)}
        for side, name in (("front", a.front_tool), ("rear", a.rear_tool)):
            if name == "none":
                continue
            if mounts[side] is None:
                raise SystemExit(f"{a.asset} has no {side} tool mount (TOOL_{side.upper()} in configs/{a.asset}.py)")
            tool = self.tools[side] = Tool(self, name, mounts[side])
            for jn, joint in tool.robot.joints.items():
                joint.rate = 0.6
                self.robot.joints[jn] = joint

    def create_driver(self):
        if self.args.task == "drive":
            return super().create_driver()
        return RoverDriver(max_speed=self.args.max_speed)

    def lift_gain(self, joint, tool):
        xj = next(t.robot.xjoints[joint] for t in self.tools.values() if joint in t.robot.xjoints)
        robot = next(t.robot for t in self.tools.values() if joint in t.robot.xjoints)
        child = robot.body(xj.find("child").get("link")).GetFrameRefToAbs()
        axis = child.TransformDirectionLocalToParent(vec(robot.axis(joint)))
        return 1.0 if axis.Cross(tool.edge() - child.GetPos()).z >= 0 else -1.0

    def add_terrain(self):
        import pychrono.vehicle as veh

        a = self.args
        self.scm_domain = False
        self.terrain = veh.SCMTerrain(self.system)
        cx = a.terrain_start + a.terrain_length / 2
        self.terrain.SetReferenceFrame(chrono.ChCoordsysd(chrono.ChVector3d(cx, 0, 0), chrono.QUNIT))
        self.terrain.SetSoilParameters(a.scm_kphi, a.scm_kc, a.scm_n, a.scm_cohesion, a.scm_phi, a.scm_janosi, 4e7, 3e4)
        if a.scm_bulldozing:
            self.terrain.EnableBulldozing(True)
            self.terrain.SetBulldozingParameters(a.repose_loose, 1.0, 3, 10)
        self.terrain.Initialize(a.terrain_length, a.terrain_width, a.scm_delta)
        self.terrain.SetPlotType(veh.SCMTerrain.PLOT_LEVEL, -0.3, 0.3)
        self.terrain.SetColor(chrono.ChColor(0.55, 0.53, 0.5))
        self.terrain.SetMeshWireframe(False)
        self.soil = Soil(self.terrain, cx, a.terrain_length, a.terrain_width, a.scm_delta, a)
        self.work = self.moved = 0.0
        self.soil_dt = 1.0 / 60.0
        self.next_soil = 0.0
        print(f"SCM soil field {a.terrain_length:.0f} x {a.terrain_width:.0f} m from x = {a.terrain_start:+.1f}, grid {a.scm_delta * 100:.0f} cm, "
              f"{a.craters} craters; wheels on SCM, tools on the cut/push/relax soil model")

    def add_scm_domain(self):
        xs = [w["x"] for w in self.wheels.values()]
        ys = [w["y"] for w in self.wheels.values()]
        r = max(w["r"] for w in self.wheels.values())
        size = chrono.ChVector3d(max(xs) - min(xs) + 2 * r + 0.6, max(ys) - min(ys) + 2 * r + 0.6, 4.0)
        centre = chrono.ChVector3d((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0.0)
        self.terrain.AddActiveDomain(self.chassis, centre, size)
        self.scm_domain = True
        print(f"SCM active domain {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m around the wheels")

    def update_soil(self):
        a, dt = self.args, self.soil_dt
        g = 9.81 if a.earth else G_MOON
        rho, coh = a.density, a.cohesion
        rows, edges = [], [t for tool in self.tools.values() for t in tool.edges]
        for t in edges:
            frame = t["body"].GetFrameRefToAbs()
            E = frame.TransformPointLocalToParent(t["p"])
            Fw = frame.TransformDirectionLocalToParent(chrono.ChVector3d(1, 0, 0) if t["k"] == COMPACTOR else t["d"])
            fh = np.array([Fw.x, Fw.y])
            fh = fh / max(np.linalg.norm(fh), 1e-6)
            A = frame.TransformDirectionLocalToParent(t["a"])
            den = A.x * -fh[1] + A.y * fh[0]
            slope = A.z / den if abs(den) > 0.3 else 0.0
            e = np.array([E.x, E.y, E.z])
            adv = 0.0 if t["prev"] is None else float(np.dot(e[:2] - t["prev"][:2], fh))
            t.update(prev=e, E=e, fh=fh, Fw=Fw, adv=adv)
            back, front, push = BANDS[t["k"]]
            active, store, fill = 1, 0, 0
            if t["k"] == DRUM:
                active = 1 if self.drum and self.robot.joints[self.drum].velocity() * a.drum_dig_sign > 1.0 else 0
                store = 1
            elif t["k"] == BUCKET:
                active = 1 if Fw.z > -0.5 else 0
                store = 1 if t["load"] < t["capacity"] else 0
            elif t["k"] == BOX:
                fill = 1 if t["load"] > 0.002 else 0
                store = 1 if t["load"] < t["capacity"] else 0
            width = t["loosen"] if t["k"] == RIPPER and t["loosen"] else t["width"]
            t["band_width"] = width
            rows.append((e, fh, slope, width, t["k"], active, store, fill, back, front, push * (1 if adv >= -1e-4 else -1), abs(adv)))
        for t in edges:
            t["surf"], t["surf_ahead"] = self.soil.sample(*t["E"][:2]), self.soil.sample(*(t["E"][:2] + t["fh"] * 0.3))
        accs = self.soil.tools(rows)
        for t, acc, row in zip(edges, accs, rows):
            body = t["body"]
            body.EmptyAccumulator(t["acc"])
            self.moved += acc["cut"]
            if t["k"] in STORES and row[6]:
                t["load"] = min(t["capacity"], t["load"] + acc["cut"])
            if t["k"] == BOX:
                t["load"] -= acc["fill"]
            w, adv = max(row[3], 0.05), abs(t["adv"])
            moving = min(1.0, adv / 0.003)
            if t["k"] == RIPPER:
                d = max(0.0, t["surf"] - t["E"][2])
                f = RIP_K * d * d
            elif t["k"] == COMPACTOR:
                f = 0.0
            else:
                d = min(acc["cut"] / (w * adv), 0.3) if adv > 1e-3 else 0.0
                f = w * (rho * g * d * d * NG + coh * d * NC) + MU_PILE * rho * g * acc["pile"]
                if t["k"] == DRUM:
                    f *= 0.3
            f = min(f, a.max_soil_force) * moving
            sgn = 1.0 if t["adv"] >= 0 else -1.0
            point = chrono.ChVector3d(*t["E"])
            body.AccumulateForce(t["acc"], chrono.ChVector3d(-t["fh"][0] * f * sgn, -t["fh"][1] * f * sgn, 0.0), point, False)
            self.work += f * adv
            if t["k"] in STORES and t["load"] > 0:
                body.AccumulateForce(t["acc"], chrono.ChVector3d(0, 0, -t["load"] * rho * g), point, False)
            if t["k"] in (BUCKET, DRUM) and t["load"] > 0:
                dumping = t["Fw"].z < -0.55 if t["k"] == BUCKET else (self.drum and self.robot.joints[self.drum].velocity() * a.drum_dig_sign < -1.0)
                if dumping:
                    v = min(t["load"], t["capacity"] * dt / 1.2)
                    t["load"] -= v
                    p = t["E"][:2] + t["fh"] * 0.1
                    self.soil.deposit(p[0], p[1], v, 0.35)
        self.soil.relax(a.relax_iters, math.tan(math.radians(a.repose_loose)), math.tan(math.radians(a.repose_dense)))
        self.soil.flush()

    def surface(self, x, y):
        return self.soil.sample(x, y)

    def pose_toward(self, joint, value, rate):
        j = self.robot.joints[joint]
        j.target = min(max(j.target + max(-rate * self.step_size, min(rate * self.step_size, value - j.target)), j.lower), j.upper)

    def raised(self, joint, frac):
        j = self.robot.joints[joint]
        return (j.upper if self.raise_sign[joint] > 0 else j.lower) * frac

    def edge_to(self, joint, tool, z_target, gain=2.5):
        if joint is None or tool is None:
            return
        j = self.robot.joints[joint]
        err = z_target - tool.edge().z
        j.target = min(max(j.target + self.raise_sign[joint] * gain * err * self.step_size, j.lower), j.upper)

    def steer_lane(self, y_target, forward, crab_max=0.45):
        d, yaw, sgn = self.driver, self.yaw(), 1.0 if forward else -1.0
        if abs(yaw) > math.radians(3):
            d.SetMode("ackermann")
            d.SetSteering(max(-0.4, min(0.4, -1.5 * yaw * sgn)))
        else:
            d.SetMode("crab")
            d.SetSteering(max(-crab_max, min(crab_max, 0.8 * (y_target - self.pos().y) * sgn)))

    def autopilot_step(self):
        a, d = self.args, self.driver
        if self.pass_i >= len(self.lanes) * a.layers:
            if self.phase != "done":
                self.phase = "done"
                d.SetSpeed(0.0)
                d.SetMode("ackermann")
                d.SetSteering(0.0)
                print(f"{a.task} finished at t = {self.sim_time:.0f} s")
            return
        lane = self.lanes[self.pass_i % len(self.lanes)]
        p = self.pos()
        ex = self.front.edge().x if self.front else p.x
        self.phase_t += self.step_size
        start, stop = a.borrow_start, a.berm_x
        if self.phase == "goto":
            target = start - a.approach
            self.steer_lane(lane, forward=p.x < target, crab_max=0.65)
            d.SetSpeed(a.cruise if p.x < target - 0.2 else (-a.cruise if p.x > target + 0.2 else 0.0))
            for lift in (self.front_lift, self.rear_lift):
                if lift:
                    self.pose_toward(lift, self.raised(lift, 0.6), 0.5)
            if abs(p.x - target) < 0.3:
                self.phase, self.phase_t = "work", 0.0
                d.SetSpeed(0.0)
        elif self.phase == "work":
            self.steer_lane(lane, forward=True)
            d.SetSpeed(a.work_speed)
            if self.front:
                surf = self.front.edges[0].get("surf_ahead", 0.0)
                self.edge_to(self.front_lift, self.front, surf - a.cut_depth * (0.4 if ex > stop - 1.2 else 1.0))
            if self.rear and self.rear_lift:
                e = self.rear.edge()
                depth = a.rip_depth if self.rear.name in ("ripper", "box_blade") else -0.3
                self.edge_to(self.rear_lift, self.rear, self.surface(e.x, e.y) - depth)
            if self.drum:
                self.drum_dir = 1
            self.stall_t = self.stall_t + self.step_size if (self.ground_speed() < 0.03 and self.phase_t > 3.0) else 0.0
            if ex > stop or self.stall_t > 2.5 or self.phase_t > 120.0:
                self.phase, self.phase_t = "lift", 0.0
                d.SetSpeed(0.0)
        elif self.phase == "lift":
            self.drum_dir = 0
            for lift in (self.front_lift, self.rear_lift):
                if lift:
                    self.pose_toward(lift, self.raised(lift, 0.6), 0.6)
            if self.phase_t > 1.5:
                self.pass_i += 1
                self.phase, self.phase_t = "goto", 0.0
                print(f"[{self.sim_time:6.1f} s] pass {self.pass_i}/{len(self.lanes) * a.layers} done")

    def handle_keys(self, keys):
        super().handle_keys(keys)
        for up, down, joint in (("1", "2", self.front_lift), ("3", "4", self.second), ("5", "6", self.rear_lift)):
            if joint is None:
                continue
            s = self.raise_sign.get(joint, 1.0)
            if up in keys:
                self.robot.joints[joint].target += 0.08 * s
            if down in keys:
                self.robot.joints[joint].target -= 0.08 * s
        if "7" in keys:
            self.drum_dir = 0 if self.drum_dir == 1 else 1
        if "8" in keys:
            self.drum_dir = 0 if self.drum_dir == -1 else -1
        if "0" in keys:
            self.autopilot = not self.autopilot
            if not self.autopilot:
                self.driver.SetSpeed(0.0)

    def step(self):
        super().step()
        self.soil.pull()

    def update(self):
        if self.sim_time >= self.next_soil:
            self.next_soil += self.soil_dt
            self.update_soil()
        if self.autopilot and self.args.task != "drive":
            self.autopilot_step()
        if self.drum:
            self.robot.joints[self.drum].set(self.args.drum_dig_sign * self.drum_dir * self.args.drum_speed)
        if self.sim_time - self.last_report >= self.args.report_every:
            self.last_report = self.sim_time
            self.report()

    def report(self):
        r = self.soil.region(self.berm_lo, self.berm_hi)
        b = self.soil.region(self.borrow_lo, self.borrow_hi)
        self.metrics = {"berm": r["fill"], "crest": r["crest"], "cut": b["cut"]}
        loads = ", ".join(f"{t['name']} {t['load'] * self.args.density:.0f} kg" for tool in self.tools.values() for t in tool.edges
                          if t["k"] in STORES)
        edge = f", front edge z {self.front.edge().z:+.3f} m" if self.front else ""
        print(f"[{self.sim_time:6.1f} s] {self.phase:5s} pass {min(self.pass_i + 1, len(self.lanes) * self.args.layers)}: moved {self.moved:5.2f} m3, berm fill {r['fill']:5.2f} m3 "
              f"crest +{r['crest']:.2f} m, borrow cut {b['cut']:5.2f} m3, soil work {self.work / 1e3:6.1f} kJ{edge}"
              + (f", {loads}" if loads else ""))

    def status(self):
        return f"{super().status()}  {self.phase}"

    def test_final(self):
        super().test_final()
        if self.args.task == "drive":
            return
        self.report()
        checks = {"soil cut from the borrow area": self.metrics["cut"] > 0.1, "soil pushed into the berm": self.metrics["berm"] > 0.05,
                  "tools moved soil": self.moved > 0.2}
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "earthmoving checks failed"

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="pegasus", max_speed=5.0, terrain="scm", scm_delta=0.1, driver="speed")
        parser.add_argument("--front-tool", default="dozer_blade", choices=["none", *FRONT_TOOLS], help="Tool URDF on the front mount.")
        parser.add_argument("--rear-tool", default="none", choices=["none", *REAR_TOOLS], help="Tool URDF on the rear mount.")
        parser.add_argument("--task", default="berm", choices=["drive", "berm"], help="Scripted berm building, or drive with --driver.")
        parser.add_argument("--terrain-length", type=float, default=24.0, help="Soil field length along x [m].")
        parser.add_argument("--terrain-width", type=float, default=16.0, help="Soil field width along y [m].")
        parser.add_argument("--terrain-start", type=float, default=-6.0, help="Soil field start x [m].")
        parser.add_argument("--seed", type=int, default=7, help="Terrain seed.")
        parser.add_argument("--craters", type=int, default=25, help="Small craters in the field.")
        parser.add_argument("--scm-bulldozing", action="store_true", help="Also let SCM bulldoze soil aside from the wheel ruts.")
        parser.add_argument("--density", type=float, default=1500.0, help="Loose regolith bulk density [kg/m3].")
        parser.add_argument("--cohesion", type=float, default=500.0, help="Regolith cohesion for the tool force model [Pa].")
        parser.add_argument("--initial-density", type=float, default=0.35, help="Initial relative density of the top layer [0-1].")
        parser.add_argument("--repose-loose", type=float, default=36.0, help="Angle of repose of loose regolith [deg].")
        parser.add_argument("--repose-dense", type=float, default=55.0, help="Steepest stable slope of fully compacted regolith [deg].")
        parser.add_argument("--relax-iters", type=int, default=6, help="Slope relaxation iterations per soil update.")
        parser.add_argument("--max-soil-force", type=float, default=6000.0, help="Clamp on the soil resistance per tool [N].")
        parser.add_argument("--drum-speed", type=float, default=3.0, help="Drum excavator speed [rad/s].")
        parser.add_argument("--drum-dig-sign", type=float, default=-1.0, help="Drum spin sign that digs.")
        parser.add_argument("--lanes", default="-2.4,-1.2,0.0,1.2,2.4", help="Lateral lane offsets for scripted passes [m].")
        parser.add_argument("--layers", type=int, default=3, help="Number of times to repeat the lane set.")
        parser.add_argument("--cut-depth", type=float, default=0.06, help="Cut depth per pass [m].")
        parser.add_argument("--rip-depth", type=float, default=0.12, help="Ripper working depth below the surface [m].")
        parser.add_argument("--berm-x", type=float, default=11.0, help="Berm line position [m].")
        parser.add_argument("--berm-length", type=float, default=7.0, help="Berm length [m].")
        parser.add_argument("--borrow-start", type=float, default=1.0, help="Pass start x for the rover [m].")
        parser.add_argument("--approach", type=float, default=2.5, help="Distance behind the start line to reverse to while lining up [m].")
        parser.add_argument("--cruise", type=float, default=3.0, help="Repositioning speed [km/h].")
        parser.add_argument("--work-speed", type=float, default=1.5, help="Working speed [km/h].")
        parser.add_argument("--report-every", type=float, default=5.0, help="Seconds between soil metric reports.")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
