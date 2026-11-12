import math

import numpy as np
import warp as wp

import newton
import newton.examples
from example_robot_rover import Example as RoverExample

G_MOON = 1.625
BLADE, BUCKET, DRUM, RAKE, RIPPER, BOX, COMPACTOR = range(7)
KINDS = {"blade": BLADE, "bucket": BUCKET, "drum": DRUM, "rake": RAKE, "ripper": RIPPER, "box_blade": BOX, "compactor": COMPACTOR}
STORES = (BUCKET, DRUM, BOX)
BANDS = {BLADE: (0.12, 0.03, 0.35), RAKE: (0.10, 0.03, 0.12), BUCKET: (0.25, 0.03, 0.30), DRUM: (0.18, 0.18, 0.30),
         BOX: (0.12, 0.03, 0.25), RIPPER: (0.10, 0.05, 0.0), COMPACTOR: (0.12, 0.12, 0.0)}
RHO_LOOSE, RHO_DENSE, LIFT_T = 1300.0, 1900.0, 0.20
NG, NC, MU_PILE = 6.0, 6.0, 0.6
RIP_K = 1.2e4
TOOL_ROLES = ("tool", "excavate")


@wp.kernel
def soil_tools(h: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), delta: wp.array2d(dtype=float), x0: float, y0: float,
               dx: float, ntool: int, E: wp.array(dtype=wp.vec3), F: wp.array(dtype=wp.vec3), slope: wp.array(dtype=float),
               width: wp.array(dtype=float), kind: wp.array(dtype=int), active: wp.array(dtype=int), store: wp.array(dtype=int),
               fill: wp.array(dtype=int), back: wp.array(dtype=float), front: wp.array(dtype=float), push: wp.array(dtype=float),
               adv: wp.array(dtype=float), acc: wp.array(dtype=float)):
    r, c = wp.tid()
    x = x0 + float(c) * dx
    y = y0 + float(r) * dx
    hv = h[r, c]
    cv = comp[r, c]
    cell = dx * dx
    for t in range(ntool):
        if active[t] == 0:
            continue
        e = E[t]
        f = F[t]
        px = x - e[0]
        py = y - e[1]
        u = px * f[0] + py * f[1]
        v = -px * f[1] + py * f[0]
        if wp.abs(v) > width[t] * 0.5:
            continue
        ze = e[2] + slope[t] * v
        k = kind[t]
        if k == 6:
            if wp.abs(u) < front[t] and hv > ze - 0.03:
                inc = 0.35 * (1.0 - cv) * adv[t] / (2.0 * front[t])
                rho0 = 1300.0 + 600.0 * cv
                cv = wp.min(cv + inc, 1.0)
                hv = hv - 0.20 * (1.0 - rho0 / (1300.0 + 600.0 * cv))
            continue
        if k == 4:
            if u > -back[t] and u < front[t] and hv > ze and cv > 0.15:
                hv = hv + 0.06 * (hv - ze) * (cv - 0.15)
                cv = 0.15
            continue
        if u > -back[t] and u < front[t]:
            if hv > ze:
                dh = hv - ze
                hv = ze
                wp.atomic_add(acc, t, dh * cell)
                if store[t] == 0:
                    cc = int(wp.round((x + f[0] * push[t] - x0) / dx))
                    rr = int(wp.round((y + f[1] * push[t] - y0) / dx))
                    if rr >= 0 and rr < h.shape[0] and cc >= 0 and cc < h.shape[1]:
                        wp.atomic_add(delta, rr, cc, dh)
            elif fill[t] == 1:
                wp.atomic_add(acc, 2 * ntool + t, (ze - hv) * cell)
                hv = ze
        if u > 0.0 and u < 0.7 and hv > ze:
            wp.atomic_add(acc, ntool + t, (hv - ze) * cell)
    h[r, c] = hv
    comp[r, c] = cv


@wp.kernel
def apply_delta(h: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), delta: wp.array2d(dtype=float)):
    r, c = wp.tid()
    d = delta[r, c]
    if d != 0.0:
        h[r, c] = h[r, c] + d
        if d > 0.0:
            comp[r, c] = comp[r, c] * wp.max(0.0, 1.0 - d / 0.2)
        delta[r, c] = 0.0


@wp.func
def _flow(h: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), delta: wp.array2d(dtype=float), r: int, c: int, rn: int, cn: int,
          dist: float, tan_lo: float, tan_hi: float, rate: float):
    if rn < 0 or rn >= h.shape[0] or cn < 0 or cn >= h.shape[1]:
        return
    dh = h[r, c] - h[rn, cn]
    lim = (tan_lo + (tan_hi - tan_lo) * 0.5 * (comp[r, c] + comp[rn, cn])) * dist
    if dh > lim:
        q = rate * (dh - lim) * 0.5
        wp.atomic_add(delta, r, c, -q)
        wp.atomic_add(delta, rn, cn, q)
    elif dh < -lim:
        q = rate * (-dh - lim) * 0.5
        wp.atomic_add(delta, r, c, q)
        wp.atomic_add(delta, rn, cn, -q)


@wp.kernel
def relax(h: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), delta: wp.array2d(dtype=float), dx: float, tan_lo: float,
          tan_hi: float, rate: float):
    r, c = wp.tid()
    _flow(h, comp, delta, r, c, r, c + 1, dx, tan_lo, tan_hi, rate)
    _flow(h, comp, delta, r, c, r + 1, c, dx, tan_lo, tan_hi, rate)
    _flow(h, comp, delta, r, c, r + 1, c + 1, dx * 1.41421, tan_lo, tan_hi, rate * 0.5)
    _flow(h, comp, delta, r, c, r + 1, c - 1, dx * 1.41421, tan_lo, tan_hi, rate * 0.5)


@wp.kernel
def deposit_disc(h: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), x0: float, y0: float, dx: float, cx: float, cy: float,
                 radius: float, dz: float):
    r, c = wp.tid()
    px = x0 + float(c) * dx - cx
    py = y0 + float(r) * dx - cy
    if px * px + py * py < radius * radius:
        h[r, c] = h[r, c] + dz
        comp[r, c] = comp[r, c] * wp.max(0.0, 1.0 - dz / 0.2)


@wp.kernel
def to_heightfield(h: wp.array2d(dtype=float), elev: wp.array(dtype=float), zmin: float, zspan: float):
    r, c = wp.tid()
    elev[r * h.shape[1] + c] = wp.clamp((h[r, c] - zmin) / zspan, 0.0, 1.0)


@wp.kernel
def to_mesh(h: wp.array2d(dtype=float), x0: float, y0: float, dx: float, pts: wp.array(dtype=wp.vec3), nrm: wp.array(dtype=wp.vec3)):
    r, c = wp.tid()
    nr = h.shape[0]
    nc = h.shape[1]
    i = r * nc + c
    pts[i] = wp.vec3(x0 + float(c) * dx, y0 + float(r) * dx, h[r, c])
    gx = h[r, wp.min(c + 1, nc - 1)] - h[r, wp.max(c - 1, 0)]
    gy = h[wp.min(r + 1, nr - 1), c] - h[wp.max(r - 1, 0), c]
    nrm[i] = wp.normalize(wp.vec3(-gx, -gy, 2.0 * dx))


@wp.kernel
def sample(h: wp.array2d(dtype=float), x0: float, y0: float, dx: float, q: wp.array(dtype=wp.vec2), out: wp.array(dtype=float),
           offset: int):
    i = wp.tid()
    fx = wp.clamp((q[i][0] - x0) / dx, 0.0, float(h.shape[1] - 2))
    fy = wp.clamp((q[i][1] - y0) / dx, 0.0, float(h.shape[0] - 2))
    c = int(fx)
    r = int(fy)
    tx = fx - float(c)
    ty = fy - float(r)
    out[offset + i] = (h[r, c] * (1.0 - tx) + h[r, c + 1] * tx) * (1.0 - ty) + (h[r + 1, c] * (1.0 - tx) + h[r + 1, c + 1] * tx) * ty


@wp.kernel
def region_stats(h: wp.array2d(dtype=float), h0: wp.array2d(dtype=float), comp: wp.array2d(dtype=float), x0: float, y0: float,
                 dx: float, lo: wp.vec2, hi: wp.vec2, grade: float, out: wp.array(dtype=float)):
    r, c = wp.tid()
    x = x0 + float(c) * dx
    y = y0 + float(r) * dx
    if x < lo[0] or x > hi[0] or y < lo[1] or y > hi[1]:
        return
    d = h[r, c] - h0[r, c]
    cell = dx * dx
    wp.atomic_add(out, 0, wp.max(d, 0.0) * cell)
    wp.atomic_add(out, 1, wp.min(d, 0.0) * cell)
    g = h[r, c] - grade
    wp.atomic_add(out, 2, g * g)
    wp.atomic_add(out, 3, comp[r, c])
    wp.atomic_add(out, 4, 1.0)
    wp.atomic_max(out, 5, d)
    wp.atomic_add(out, 6, h[r, c])


@wp.kernel
def add_wrench(src: wp.array(dtype=wp.spatial_vector), dst: wp.array(dtype=wp.spatial_vector)):
    i = wp.tid()
    dst[i] = dst[i] + src[i]


def qrot(q, v):
    x, y, z, w = q
    u = np.array([x, y, z])
    v = np.asarray(v, dtype=float)
    return v + 2.0 * np.cross(u, np.cross(u, v) + w * v)


def make_terrain(nrow, ncol, dx, x0, y0, seed, craters, clear):
    rng = np.random.default_rng(seed)
    X, Y = np.meshgrid(x0 + dx * np.arange(ncol), y0 + dx * np.arange(nrow))
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
    return (h - h[nrow // 2, ncol // 2]) * (w * w * (3 - 2 * w))


def tool_sites(stage, blabels):
    from pxr import Usd, UsdGeom

    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    out = []
    for prim in Usd.PrimRange(stage.GetDefaultPrim()):
        if not prim.HasAttribute("site:kind") or prim.GetAttribute("site:kind").Get() not in ("tool_edge", "payload", "reference"):
            continue
        body = prim.GetParent()
        while body and body.GetName() not in blabels:
            body = body.GetParent()
        if not body:
            continue
        local = cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(body).GetInverse()
        attr = lambda k, d=None: prim.GetAttribute(f"site:{k}").Get() if prim.HasAttribute(f"site:{k}") else d
        out.append({"name": prim.GetName(), "kind": attr("kind"), "body": blabels.index(body.GetName()), "body_name": body.GetName(),
                    "p": np.array(local.ExtractTranslation()), "d": np.array(local.TransformDir((0, 0, 1))), "tool": attr("tool"),
                    "width": float(attr("width_m") or attr("loosen_width_m") or 0.1), "loosen": attr("loosen_width_m"),
                    "capacity": float(attr("capacity_m3") or attr("volume_m3") or 0.0), "radius": float(attr("radius_m") or 0.0),
                    "length": float(attr("length_m") or 0.0), "bed_width": float(attr("width_m") or 0.0)})
    return out


class Example(RoverExample):
    def __init__(self, viewer, args):
        self.ready = False
        self.grid = None
        super().__init__(viewer, args)
        wp.launch(to_heightfield, (self.nrow, self.ncol), inputs=[self.h, self.model.heightfield_elevations, self.zmin, self.zmax - self.zmin])
        self._setup_tools()
        self.wrench = wp.zeros(self.model.body_count, dtype=wp.spatial_vector)
        self.ready = True
        self.capture()
        self.task = args.task
        self.pass_i, self.phase, self.phase_t, self.stall_t = 0, "goto", 0.0, 0.0
        self.work = 0.0
        self.moved = 0.0
        self.last_report = 0.0
        self._setup_task()
        print(f"earthmoving: {self.nrow} x {self.ncol} soil grid at {self.dx * 100:.0f} cm, tools "
              f"{', '.join(f'{t['tool']}@{t['body_name']}' for t in self.tools) or 'none'}, task {self.task}")
        print("keys: 1/2 front lift up/down, 3/4 front angle or curl, 5/6 rear lift up/down, 7 drum dig, 8 drum dump, "
              "9 tip bed, 0 autopilot on/off, plus the rover keys")

    def solver_options(self):
        return {"use_mujoco_contacts": False, "njmax": 3000, "nconmax": 1500}

    def configure_rover(self, rover, blabels):
        tool_bodies = {n for n in self.labels if self.role.get(n) in TOOL_ROLES}
        for b, name in enumerate(blabels):
            if name in tool_bodies:
                for s in rover.body_shapes[b]:
                    rover.shape_flags[s] = rover.shape_flags[s] & ~newton.ShapeFlags.COLLIDE_SHAPES

    def add_terrain(self, builder):
        a = self.args
        self.dx = a.cell
        self.ncol = int(round(a.terrain_length / self.dx)) + 1
        self.nrow = int(round(a.terrain_width / self.dx)) + 1
        self.x0, self.y0 = a.terrain_start, -a.terrain_width / 2
        h = make_terrain(self.nrow, self.ncol, self.dx, self.x0, self.y0, a.seed, a.craters, 4.0)
        self.zmin, self.zmax = -2.0, 3.5
        hx, hy = (self.ncol - 1) * self.dx / 2, (self.nrow - 1) * self.dx / 2
        hf = newton.Heightfield(data=h, nrow=self.nrow, ncol=self.ncol, hx=hx, hy=hy, min_z=self.zmin, max_z=self.zmax)
        cfg = newton.ModelBuilder.ShapeConfig(mu=0.8, ke=2.0e5, kd=5.0e3, is_visible=False)
        builder.add_shape_heightfield(xform=wp.transform(wp.vec3(self.x0 + hx, self.y0 + hy, 0.0), wp.quat_identity()), heightfield=hf,
                                      cfg=cfg)
        self.h = wp.array(h.astype(np.float32), dtype=float)
        self.h0 = wp.array(h.astype(np.float32), dtype=float)
        self.comp = wp.full((self.nrow, self.ncol), a.initial_density, dtype=float)
        self.delta = wp.zeros((self.nrow, self.ncol), dtype=float)
        self.pts = wp.zeros(self.nrow * self.ncol, dtype=wp.vec3)
        self.nrm = wp.zeros(self.nrow * self.ncol, dtype=wp.vec3)
        r, c = np.meshgrid(np.arange(self.nrow - 1), np.arange(self.ncol - 1), indexing="ij")
        i = (r * self.ncol + c).ravel()
        self.idx = wp.array(np.stack([i, i + 1, i + self.ncol, i + 1, i + self.ncol + 1, i + self.ncol], 1).ravel().astype(np.int32),
                            dtype=wp.int32)

    def _setup_tools(self):
        sites = tool_sites(self.stage, self.blabels)
        self.tools = [s for s in sites if s["kind"] == "tool_edge" and s["tool"] in KINDS]
        self.payloads = {s["body_name"]: s for s in sites if s["kind"] == "payload"}
        self.bed = next((s for s in sites if s["name"] == "bed_volume"), None)
        self.lip = next((s for s in sites if s["name"] == "dump_lip"), None)
        for t in self.tools:
            t["k"] = KINDS[t["tool"]]
            t["a"] = np.array([0.0, 1.0, 0.0]) if t["k"] == COMPACTOR else np.cross((0, 0, 1), t["d"])
            t["a"] = t["a"] / max(np.linalg.norm(t["a"]), 1e-6)
            t["prev"] = None
            t["load"] = 0.0
            t["store_body"] = t["body_name"] if t["k"] in STORES else None
            if t["k"] == DRUM:
                t["store_body"] = "drums"
        self.trailer_load = 0.0
        bq0 = self.state_0.body_q.numpy()
        cx = bq0[0][0]
        for t in self.tools:
            t["x0"] = float(self._world(bq0, t)[0][0] - cx)
        working = [t for t in self.tools if t["k"] != COMPACTOR]
        self.front_tool = max(working, key=lambda t: t["x0"]) if working and max(t["x0"] for t in working) > 0 else None
        rear = [t for t in working if t["x0"] < 0]
        self.rear_tool = min(rear, key=lambda t: abs(t["E"][1]) if "E" in t else abs(t["p"][1])) if rear else None
        front = [n for n in ("blade_lift", "loader_lift", "drum_arm", "rake_lift") if n in self.coord]
        rear = [n for n in ("ripper_lift", "box_lift") if n in self.coord]
        second = [n for n in ("blade_angle", "bucket", "wing_l") if n in self.coord]
        self.front_lift = front[0] if front else None
        self.rear_lift = rear[0] if rear else None
        self.second = second[0] if second else None
        self.drum_dir = 0
        self.autopilot = self.args.task != "drive"
        n = max(len(self.tools), 1)
        self.t_arr = {k: wp.zeros(n, dtype=d) for k, d in (("E", wp.vec3), ("F", wp.vec3), ("slope", float), ("width", float),
                                                            ("kind", int), ("active", int), ("store", int), ("fill", int), ("back", float),
                                                            ("front", float), ("push", float), ("adv", float))}
        self.acc = wp.zeros(5 * n, dtype=float)
        self.tool_pts = wp.zeros(2 * n, dtype=wp.vec2)
        self.stats = wp.zeros(8, dtype=float)
        self.com = self.model.body_com.numpy()
        self.bq = self.state_0.body_q.numpy()
        self.v_body = 0.0
        self.zone_z = 0.0

    def capture(self):
        if self.ready:
            super().capture()
        else:
            self.graph = None

    def simulate(self):
        self.pipe.collide(self.state_0, self.contacts)
        for _ in range(self.sim_substeps):
            self.state_0.clear_forces()
            self.viewer.apply_forces(self.state_0)
            wp.launch(add_wrench, self.model.body_count, inputs=[self.wrench, self.state_0.body_f])
            self.solver.step(self.state_0, self.state_1, self.control, self.contacts, self.sim_dt)
            self.state_0, self.state_1 = self.state_1, self.state_0

    def _world(self, bq, s, p=None):
        q = bq[s["body"]]
        return q[:3] + qrot(q[3:7], s["p"] if p is None else p), q[3:7]

    def update_soil(self):
        if not self.tools:
            self._finish_soil()
            return
        bq = self.bq = self.state_0.body_q.numpy()
        self.v_body = float(np.linalg.norm(self.state_0.body_qd.numpy()[0][:3]))
        qd = self.state_0.joint_qd.numpy() if ("drums" in self.dof or "bed" in self.coord) else None
        self.joint_q_bed = float(self.state_0.joint_q.numpy()[self.coord["bed"]]) if "bed" in self.coord else 0.0
        rows = []
        for t in self.tools:
            E, q = self._world(bq, t)
            Fw = qrot(q, (1, 0, 0) if t["k"] == COMPACTOR else t["d"])
            fh = np.array([Fw[0], Fw[1], 0.0])
            fh = fh / max(np.linalg.norm(fh), 1e-6)
            A = qrot(q, t["a"])
            L2 = np.array([-fh[1], fh[0]])
            den = A[0] * L2[0] + A[1] * L2[1]
            slope = A[2] / den if abs(den) > 0.3 else 0.0
            adv = 0.0 if t["prev"] is None else float(np.dot(E[:2] - t["prev"][:2], fh[:2]))
            t["prev"], t["E"], t["fh"], t["Fw"], t["adv"] = E, E, fh, Fw, adv
            back, front, push = BANDS[t["k"]]
            active, store, fill = 1, 0, 0
            cap = t["capacity"]
            if t["k"] == DRUM:
                spin = qd[self.dof["drums"]]
                active = 1 if spin * self.args.drum_dig_sign > 1.0 else 0
                store = 1
            elif t["k"] == BUCKET:
                active = 1 if Fw[2] > -0.5 else 0
                store = 1 if t["load"] < cap else 0
            elif t["k"] == BOX:
                store = 1 if t["load"] < cap else 0
                fill = 1 if t["load"] > 0.002 else 0
                store = 1 if t["load"] < cap else 0
            width = t["loosen"] if t["k"] == RIPPER and t["loosen"] else t["width"]
            rows.append((E, fh, slope, width, t["k"], active, store, fill, back, front, push * (1 if adv >= -1e-4 else -1), abs(adv)))
        A = self.t_arr
        A["E"].assign(np.array([r[0] for r in rows], dtype=np.float32))
        A["F"].assign(np.array([r[1] for r in rows], dtype=np.float32))
        for i, key in enumerate(("slope", "width", "kind", "active", "store", "fill", "back", "front", "push", "adv")):
            A[key].assign(np.array([r[i + 2] for r in rows], dtype=np.int32 if key in ("kind", "active", "store", "fill") else np.float32))
        n = len(self.tools)
        self.acc.zero_()
        self.tool_pts.assign(np.array([t["E"][:2] for t in self.tools] + [t["E"][:2] + t["fh"][:2] * 0.3 for t in self.tools],
                                      dtype=np.float32))
        wp.launch(sample, 2 * n, inputs=[self.h, self.x0, self.y0, self.dx, self.tool_pts, self.acc, 3 * n])
        wp.launch(soil_tools, (self.nrow, self.ncol), inputs=[self.h, self.comp, self.delta, self.x0, self.y0, self.dx, n,
                                                             *[A[k] for k in ("E", "F", "slope", "width", "kind", "active", "store", "fill",
                                                                              "back", "front", "push", "adv")], self.acc])
        acc = self.acc.numpy()
        cut, pile, filled, depth, ahead = acc[:n], acc[n:2 * n], acc[2 * n:3 * n], acc[3 * n:4 * n], acc[4 * n:]
        for t, z0, z1 in zip(self.tools, depth, ahead):
            t["surf"], t["surf_ahead"] = float(z0), float(z1)
        wrench = np.zeros((self.model.body_count, 6), dtype=np.float32)
        com = self.com
        g = 9.81 if self.args.earth else G_MOON
        rho, coh = self.args.density, self.args.cohesion
        for i, t in enumerate(self.tools):
            self.moved += float(cut[i])
            if t["k"] in STORES and rows[i][6]:
                t["load"] = min(t["capacity"], t["load"] + float(cut[i]))
            if t["k"] == BOX:
                t["load"] -= float(filled[i])
            w = max(rows[i][3], 0.05)
            adv = abs(t["adv"])
            moving = min(1.0, adv / 0.003)
            if t["k"] == RIPPER:
                d = max(0.0, float(depth[i]) - t["E"][2])
                f = RIP_K * d * d
            elif t["k"] == COMPACTOR:
                f = 0.0
            else:
                d = min(float(cut[i]) / (w * adv), 0.3) if adv > 1e-3 else 0.0
                f = w * (rho * g * d * d * NG + coh * d * NC) + MU_PILE * rho * g * float(pile[i])
                if t["k"] == DRUM:
                    f *= 0.3
            f = min(f, self.args.max_soil_force) * moving
            sgn = 1.0 if t["adv"] >= 0 else -1.0
            fv = -t["fh"] * f * sgn
            self.work += f * abs(t["adv"])
            self._add_force(wrench, bq, com, t["body"], t["E"], fv)
            if t["k"] in STORES and t["load"] > 0:
                ps = self.payloads.get(t["store_body"])
                body = self.blabels.index(t["store_body"]) if t["store_body"] in self.blabels else t["body"]
                p = self._world(bq, ps)[0] if ps else t["E"]
                self._add_force(wrench, bq, com, body, p, np.array([0, 0, -t["load"] * rho * g]))
        self._dumps(bq, qd, wrench, com, g, rho)
        self.wrench.assign(wrench)
        self._finish_soil()

    def _add_force(self, wrench, bq, com, b, p, f):
        q = bq[b]
        c = q[:3] + qrot(q[3:7], com[b])
        wrench[b, :3] += f
        wrench[b, 3:] += np.cross(p - c, f)

    def _deposit(self, x, y, vol, radius):
        if vol <= 0:
            return
        wp.launch(deposit_disc, (self.nrow, self.ncol), inputs=[self.h, self.comp, self.x0, self.y0, self.dx, float(x), float(y), radius,
                                                               float(vol / (math.pi * radius * radius))])

    def _in_bed(self, bq, p):
        if not self.bed:
            return False
        c, q = self._world(bq, self.bed)
        d = p - c
        ax = qrot(q, (1, 0, 0))
        ay = qrot(q, (0, 1, 0))
        return abs(np.dot(d, ax)) < self.bed["length"] / 2 and abs(np.dot(d, ay)) < self.bed["bed_width"] / 2 and -0.3 < d[2] < 1.5

    def _dumps(self, bq, qd, wrench, com, g, rho):
        dt = self.frame_dt
        for t in self.tools:
            if t["k"] not in (BUCKET, DRUM) or t["load"] <= 0:
                continue
            dumping = t["Fw"][2] < -0.55 if t["k"] == BUCKET else qd[self.dof["drums"]] * self.args.drum_dig_sign < -1.0
            if not dumping:
                continue
            v = min(t["load"], t["capacity"] * dt / 1.2)
            t["load"] -= v
            p = t["E"] + t["fh"] * 0.1
            if self._in_bed(bq, p):
                self.trailer_load += v
            else:
                self._deposit(p[0], p[1], v, 0.35)
        if self.bed and "bed" in self.coord:
            if self.joint_q_bed > 0.6 and self.trailer_load > 0:
                v = min(self.trailer_load, 0.8 * dt / 1.5)
                self.trailer_load -= v
                p = self._world(bq, self.lip)[0] if self.lip else self._world(bq, self.bed)[0]
                self._deposit(p[0] - 0.2, p[1], v, 0.5)
            if self.trailer_load > 0:
                self._add_force(wrench, bq, com, self.bed["body"], self._world(bq, self.bed)[0],
                                np.array([0, 0, -self.trailer_load * rho * g]))

    def _finish_soil(self):
        wp.launch(apply_delta, (self.nrow, self.ncol), inputs=[self.h, self.comp, self.delta])
        lo, hi = math.tan(math.radians(self.args.repose_loose)), math.tan(math.radians(self.args.repose_dense))
        for _ in range(self.args.relax_iters):
            wp.launch(relax, (self.nrow, self.ncol), inputs=[self.h, self.comp, self.delta, self.dx, lo, hi, 0.4])
            wp.launch(apply_delta, (self.nrow, self.ncol), inputs=[self.h, self.comp, self.delta])
        wp.launch(to_heightfield, (self.nrow, self.ncol), inputs=[self.h, self.model.heightfield_elevations, self.zmin, self.zmax - self.zmin])

    def region(self, lo, hi, grade=0.0):
        self.stats.zero_()
        wp.launch(region_stats, (self.nrow, self.ncol), inputs=[self.h, self.h0, self.comp, self.x0, self.y0, self.dx, wp.vec2(*lo),
                                                               wp.vec2(*hi), float(grade), self.stats])
        s = self.stats.numpy()
        n = max(s[4], 1.0)
        return {"fill_m3": s[0], "cut_m3": -s[1], "rms_m": math.sqrt(s[2] / n), "rel_density": s[3] / n, "max_rise_m": s[5],
                "mean_z": s[6] / n}

    def _setup_task(self):
        a = self.args
        self.lanes = [float(v) for v in a.lanes.split(",")]
        self.berm_lo, self.berm_hi = (a.berm_x - 0.6, -a.berm_length / 2), (a.berm_x + 2.5, a.berm_length / 2)
        self.pad_lo, self.pad_hi = (a.pad_start, -a.pad_width / 2), (a.pad_start + a.pad_length, a.pad_width / 2)
        self.grade = self.region(self.pad_lo, self.pad_hi)["mean_z"]
        self.pad0 = self.region(self.pad_lo, self.pad_hi, self.grade)
        lo, hi = (self.berm_lo, self.berm_hi) if self.task != "pad" else (self.pad_lo, self.pad_hi)
        self.zone_z = 0.02 + max(0.0, self.region(lo, hi)["mean_z"])

    def _pose_toward(self, joint, value, rate):
        lo, hi = self.lim[joint]
        cur = self.poses[joint]
        self.poses[joint] = float(np.clip(cur + np.clip(value - cur, -rate * self.frame_dt, rate * self.frame_dt), lo, hi))

    def _edge_to(self, joint, tool, z_target, gain=2.5):
        t = tool
        if joint is None or t is None or "E" not in t:
            return
        err = z_target - t["E"][2]
        lo, hi = self.lim[joint]
        self.poses[joint] = float(np.clip(self.poses[joint] + gain * err * self.frame_dt, lo, hi))

    def _steer_lane(self, y_target, forward, crab_max=0.45):
        q = self.bq[0]
        yaw = math.atan2(2 * (q[6] * q[5] + q[3] * q[4]), 1 - 2 * (q[4] ** 2 + q[5] ** 2))
        sgn = 1.0 if forward else -1.0
        if abs(yaw) > math.radians(3):
            self.mode = 0
            self.steer = float(np.clip(-1.5 * yaw * sgn, -0.4, 0.4))
        else:
            self.mode = 1
            self.steer = float(np.clip(0.8 * (y_target - q[1]) * sgn, -crab_max, crab_max))
        return q

    def autopilot_step(self):
        a = self.args
        if not self.autopilot or self.task == "drive" or self.pass_i >= len(self.lanes) * a.layers:
            if self.autopilot and self.task != "drive" and self.phase != "done":
                self.phase, self.speed = "done", 0.0
                print(f"{self.task} finished at t = {self.sim_time:.0f} s")
            return
        lane = self.lanes[self.pass_i % len(self.lanes)]
        layer = self.pass_i // len(self.lanes)
        tool = self.front_tool if self.front_tool and "E" in self.front_tool else None
        q = self.bq[0]
        ex = tool["E"][0] if tool else q[0]
        compacting = self.task == "pad" and layer >= a.layers - a.compact_layers
        self.phase_t += self.frame_dt
        v_act = self.v_body
        if self.task == "berm":
            start, stop = a.borrow_start, a.berm_x
        else:
            start, stop = a.pad_start - 2.5, a.pad_start + a.pad_length
        if self.phase == "goto":
            start -= a.approach
            self._steer_lane(lane, forward=q[0] < start, crab_max=0.65)
            self.speed = a.cruise if q[0] < start - 0.2 else (-a.cruise if q[0] > start + 0.2 else 0.0)
            if self.front_lift:
                self._pose_toward(self.front_lift, self.lim[self.front_lift][1] * 0.6, 0.5)
            if self.rear_lift:
                self._pose_toward(self.rear_lift, self.lim[self.rear_lift][1] * 0.8, 0.5)
            if abs(q[0] - start) < 0.3:
                self.phase, self.phase_t, self.speed = "work", 0.0, 0.0
        elif self.phase == "work":
            self._steer_lane(lane, forward=True)
            self.speed = a.work_speed
            if tool:
                surf = tool["surf_ahead"]
                if self.task == "berm":
                    z = surf - a.cut_depth * (0.4 if ex > stop - 1.2 else 1.0)
                else:
                    z = surf + 0.25 if compacting else self.grade
                self._edge_to(self.front_lift, tool, z)
            rt = self.rear_tool
            if self.rear_lift and rt and "E" in rt:
                surf_r = rt["surf"]
                if rt["k"] == RIPPER:
                    zr = surf_r - a.rip_depth if (self.task == "berm" or layer == 0) else surf_r + 0.3
                else:
                    zr = surf_r + 0.3 if (compacting or self.task == "berm") else self.grade
                self._edge_to(self.rear_lift, rt, zr)
            self.stall_t = self.stall_t + self.frame_dt if (v_act < 0.03 and self.phase_t > 3.0) else 0.0
            if ex > stop or self.stall_t > 2.5 or self.phase_t > 120.0:
                self.phase, self.phase_t, self.speed = "lift", 0.0, 0.0
        elif self.phase == "lift":
            self.speed = 0.0
            if self.front_lift:
                self._pose_toward(self.front_lift, self.lim[self.front_lift][1] * 0.6, 0.6)
            if self.rear_lift:
                self._pose_toward(self.rear_lift, self.lim[self.rear_lift][1] * 0.8, 0.6)
            if self.phase_t > 1.5:
                self.pass_i += 1
                self.phase, self.phase_t = "goto", 0.0

    def step(self):
        if not hasattr(self, "wall0"):
            import time
            self.wall0, self.clock = time.perf_counter(), time.perf_counter
        if self.args.task != "drive" and self.autopilot:
            self.autopilot_step()
        self._tool_keys()
        super().step()
        self.update_soil()
        if self.sim_time - self.last_report >= self.args.report_every:
            self.last_report = self.sim_time
            self.report()

    def _tool_keys(self):
        v = self.viewer
        dt = self.frame_dt
        nudge = lambda j, s: j and self._pose_toward(j, self.poses[j] + s, abs(s) / dt)
        if v.is_key_down("1"):
            nudge(self.front_lift, 0.6 * dt)
        if v.is_key_down("2"):
            nudge(self.front_lift, -0.6 * dt)
        if v.is_key_down("3"):
            nudge(self.second, 0.6 * dt)
            if self.second == "wing_l":
                nudge("wing_r", 0.6 * dt)
        if v.is_key_down("4"):
            nudge(self.second, -0.6 * dt)
            if self.second == "wing_l":
                nudge("wing_r", -0.6 * dt)
        if v.is_key_down("5"):
            nudge(self.rear_lift, 0.6 * dt)
        if v.is_key_down("6"):
            nudge(self.rear_lift, -0.6 * dt)
        if self._pressed("7"):
            self.drum_dir = 0 if self.drum_dir == 1 else 1
        if self._pressed("8"):
            self.drum_dir = 0 if self.drum_dir == -1 else -1
        if self._pressed("9") and "bed" in self.coord:
            self.poses["bed"] = 0.0 if self.poses["bed"] > 0.3 else self.lim["bed"][1]
        if self._pressed("0"):
            self.autopilot = not self.autopilot
            self.speed = 0.0
            print("autopilot", "on" if self.autopilot else "off")
        if "drums" in self.dof:
            omega = self.drum_dir * self.args.drum_dig_sign * self.args.drum_speed
            for world in range(self.world_count):
                self._tqd[world * self.dofs_per_world + self.dof["drums"]] = omega

    def report(self):
        r = self.region(self.berm_lo, self.berm_hi) if self.task != "pad" else self.region(self.pad_lo, self.pad_hi, self.grade)
        q = self.state_0.body_q.numpy()[0]
        loads = ", ".join(f"{t['tool']} {t['load'] * self.args.density:.0f} kg" for t in self.tools if t["k"] in STORES)
        if self.bed:
            loads += (", " if loads else "") + f"trailer {self.trailer_load * self.args.density:.0f} kg"
        rate = self.sim_time / max(self.clock() - self.wall0, 1e-6) if hasattr(self, "wall0") else 0.0
        head = f"[{rate:4.2f}x real time] t {self.sim_time:6.1f} s  pass {self.pass_i + 1} {self.phase:5s}  rover ({q[0]:5.2f}, {q[1]:5.2f})  moved {self.moved:6.2f} m3"
        if self.task == "pad":
            print(f"{head}  pad rms {r['rms_m'] * 100:5.1f} cm (start {self.pad0['rms_m'] * 100:.1f})  rel density {r['rel_density']:.2f}"
                  f"  soil work {self.work / 1e3:6.1f} kJ  {loads}")
        else:
            print(f"{head}  berm fill {r['fill_m3']:5.2f} m3  crest +{r['max_rise_m']:.2f} m  soil work {self.work / 1e3:6.1f} kJ  {loads}")

    def render_extra(self):
        wp.launch(to_mesh, (self.nrow, self.ncol), inputs=[self.h, self.x0, self.y0, self.dx, self.pts, self.nrm])
        self.viewer.log_mesh("regolith", self.pts, self.idx, self.nrm, color=(0.45, 0.44, 0.42), roughness=0.95, metallic=0.0)
        if self.tools and all("E" in t for t in self.tools):
            self.viewer.log_points("tool_edges", wp.array([t["E"] for t in self.tools], dtype=wp.vec3),
                                   wp.full(len(self.tools), 0.05, dtype=float), (1.0, 0.55, 0.1))
        lo, hi = (self.berm_lo, self.berm_hi) if self.task != "pad" else (self.pad_lo, self.pad_hi)
        z = self.zone_z
        c = [(lo[0], lo[1], z), (hi[0], lo[1], z), (hi[0], hi[1], z), (lo[0], hi[1], z)]
        self.viewer.log_lines("target_zone", wp.array(c, dtype=wp.vec3), wp.array(c[1:] + c[:1], dtype=wp.vec3), (0.2, 0.8, 0.4), width=0.03)

    def test_final(self):
        self.report()
        dh = float(np.sum(self.h.numpy() - self.h0.numpy())) * self.dx * self.dx
        held = sum(t["load"] for t in self.tools) + self.trailer_load
        print(f"soil volume change {dh:+.3f} m3 (compaction settles it), tools holding {held:.3f} m3, moved {self.moved:.2f} m3")
        print(f"final chassis position {np.round(self.state_0.body_q.numpy()[0][:3], 3)}, t = {self.sim_time:.1f} s")

    def gui(self, ui):
        super().gui(ui)
        ui.text(f"Autopilot ({self.task}): {'on' if self.autopilot else 'off'}  phase {self.phase}")
        ui.text(f"Moved {self.moved:.2f} m3, soil work {self.work / 1e3:.1f} kJ")

    @staticmethod
    def create_parser():
        parser = RoverExample.create_parser()
        parser.set_defaults(asset="pegasus", variants="FrontTool=dozer_blade", max_speed=5.0)
        parser.add_argument("--task", default="berm", choices=["drive", "berm", "pad"], help="Scripted task, or drive by keyboard.")
        parser.add_argument("--cell", type=float, default=0.1, help="Soil grid spacing [m] (0.05 is finer and about 4x slower).")
        parser.add_argument("--terrain-length", type=float, default=24.0, help="Soil field length along x [m].")
        parser.add_argument("--terrain-width", type=float, default=16.0, help="Soil field width along y [m].")
        parser.add_argument("--terrain-start", type=float, default=-6.0, help="Soil field start x [m].")
        parser.add_argument("--seed", type=int, default=7, help="Terrain seed.")
        parser.add_argument("--craters", type=int, default=25, help="Small craters in the field.")
        parser.add_argument("--density", type=float, default=1500.0, help="Loose regolith bulk density [kg/m3].")
        parser.add_argument("--cohesion", type=float, default=500.0, help="Regolith cohesion [Pa] (0.1-1 kPa measured).")
        parser.add_argument("--initial-density", type=float, default=0.35, help="Initial relative density of the top layer [0-1].")
        parser.add_argument("--repose-loose", type=float, default=36.0, help="Angle of repose of loose regolith [deg].")
        parser.add_argument("--repose-dense", type=float, default=55.0, help="Steepest stable slope of fully compacted regolith [deg].")
        parser.add_argument("--relax-iters", type=int, default=6, help="Slope relaxation iterations per frame.")
        parser.add_argument("--max-soil-force", type=float, default=6000.0, help="Clamp on the soil resistance per tool [N].")
        parser.add_argument("--drum-speed", type=float, default=3.0, help="Drum speed [rad/s].")
        parser.add_argument("--drum-dig-sign", type=float, default=-1.0, help="Drum spin sign that digs (scoops lead at the bottom).")
        parser.add_argument("--lanes", default="-2.4,-1.2,0.0,1.2,2.4", help="Lateral lane offsets for scripted passes [m].")
        parser.add_argument("--layers", type=int, default=3, help="Number of times to repeat the lane set.")
        parser.add_argument("--compact-layers", type=int, default=1, help="Pad task: final layers that only compact (blade up).")
        parser.add_argument("--cut-depth", type=float, default=0.06, help="Berm task: cut depth per pass [m].")
        parser.add_argument("--rip-depth", type=float, default=0.12, help="Ripper working depth below the surface [m].")
        parser.add_argument("--berm-x", type=float, default=11.0, help="Berm task: berm line position [m].")
        parser.add_argument("--berm-length", type=float, default=7.0, help="Berm task: berm length [m].")
        parser.add_argument("--borrow-start", type=float, default=1.0, help="Berm task: pass start x for the rover [m].")
        parser.add_argument("--approach", type=float, default=2.5, help="Distance behind the start line to reverse to while lining up [m].")
        parser.add_argument("--pad-start", type=float, default=4.0, help="Pad task: pad start x [m].")
        parser.add_argument("--pad-length", type=float, default=6.0, help="Pad task: pad length [m].")
        parser.add_argument("--pad-width", type=float, default=6.0, help="Pad task: pad width [m].")
        parser.add_argument("--cruise", type=float, default=3.0, help="Repositioning speed [km/h].")
        parser.add_argument("--work-speed", type=float, default=1.5, help="Working speed [km/h].")
        parser.add_argument("--report-every", type=float, default=5.0, help="Seconds between metric reports.")
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    newton.examples.run(Example(viewer, args), args)
