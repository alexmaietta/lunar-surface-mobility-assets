import math

from mathutils import Vector

import geo as G

TAU = 2 * math.pi


def polar(r, az_deg, z):
    a = math.radians(az_deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def radial_frame(az_deg):
    a = math.radians(az_deg)
    return Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))


def densify(profile, k):
    out = []
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        for i in range(k):
            t = i / k
            out.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
    out.append(profile[-1])
    return out


def bell(name, link, exit_c, exit_r, throat_r, length, mat_ext, mat_int, axis=(0, 0, -1), wall=0.008, segments=48,
         throat_frac=0.78, power=1.9):
    exit_c, d = Vector(exit_c), Vector(axis).normalized()
    throat = exit_c - d * length * throat_frac
    prof = []
    for i in range(25):
        t = i / 24
        prof.append((throat_r + (exit_r - throat_r) * (1 - (1 - t) ** power), length * throat_frac * (1 - t)))
    prof = prof[::-1]
    frame = _lathe_frame(-d)
    outer = [(r + wall, z) for r, z in prof]
    G.add_mesh_uv(f"{name}_nozzle", G.lathe_geo(outer, segments, exit_c, frame), mat_ext, link)
    G.add_mesh_uv(f"{name}_nozzle_inner", G.lathe_geo(prof, segments, exit_c, frame, flip=True), mat_int, link)
    G.add_mesh_uv(f"{name}_nozzle_lip", G.lathe_geo([(exit_r, 0), (exit_r + wall, 0)], segments, exit_c, frame), mat_ext, link)
    return throat


def _lathe_frame(up):
    f = _axis_frame(up)
    return None if f is None else [list(r) for r in zip(*f)]


def _axis_frame(up):
    up = Vector(up).normalized()
    if abs(up.z) > 0.999:
        return None if up.z > 0 else [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    x = Vector((0, 0, 1)).cross(up).normalized()
    y = up.cross(x)
    return [list(x), list(y), list(up)]


def footpad(name, link, centre, r, h, mat, segments=32, dish=0.35):
    c = Vector(centre)
    prof = [(1e-3, -0.005), (r * 0.85, 0.0), (r, h * dish), (r, h * 0.55), (r * 0.55, h * 0.8), (r * 0.12, h)]
    G.add_mesh_uv(name, G.lathe_geo(prof, segments, center=(c.x, c.y, c.z)), mat, link)


def leg(i, body, hard_point, foot, secondaries, mats, *, stroke, knee_frac=0.55, r_outer=0.05, r_piston=0.035,
        r_secondary=0.025, pad_r=0.2, pad_h=0.1, piston_mass=4.0, stiffness=2.0e4, damping=3.0e3, max_force=6.0e4):
    hp, ft = Vector(hard_point), Vector(foot)
    axis = (ft - hp).normalized()
    knee = hp + (ft - hp) * knee_frac
    ankle = Vector((ft.x, ft.y, ft.z + pad_h * 0.8))
    G.add_mesh_uv(f"leg_{i}_primary", G.tube_uv(hp, knee, r_outer, 20), mats["primary"], body)
    G.add_mesh_uv(f"leg_{i}_collar", G.tube_uv(knee - axis * r_outer * 2, knee, r_outer * 1.2, 20), mats["collar"], body)
    for s, root in enumerate(secondaries):
        G.add_mesh_uv(f"leg_{i}_secondary_{s}", G.tube_uv(Vector(root), knee - axis * r_outer, r_secondary, 12),
                      mats["secondary"], body)
    piston = G.link(f"leg_{i}_piston", tuple(knee), body, mass=piston_mass,
                    joint={"type": "prismatic", "axis": tuple(-axis), "limit": (0.0, stroke), "role": "landing_gear",
                           "drive": {"kind": "spring", "stiffness": stiffness, "damping": damping, "max_force": max_force}})
    G.add_mesh_uv(f"leg_{i}_piston_rod", G.tube_uv(knee - axis * stroke * 0.6, ankle, r_piston, 16), mats["piston"], piston)
    footpad(f"leg_{i}_footpad", piston, (ft.x, ft.y, ft.z), pad_r, pad_h, mats["footpad"])
    G.site(f"leg_{i}_foot_contact", piston, (ft.x, ft.y, ft.z), (0, 0, -1), kind="contact",
           description="Footpad contact point (touchdown sensing)")
    return piston, knee, axis


def thruster_cone(name, link, base, flow, spec, mat, cluster=None, notes_extra=""):
    base, flow = Vector(base), Vector(flow).normalized()
    exit_p = base + flow * spec["nozzle_len"]
    G.add_mesh_uv(name, G.tube_uv(base, exit_p, spec["exit_r"] * 0.45, 16, r1=spec["exit_r"], caps=False), mat, link)
    G.thruster(name, link, tuple(exit_p), tuple(flow), kind=spec.get("kind", "rcs"), thrust_n=spec["thrust_n"],
               isp_s=spec["isp_s"], exit_radius=spec["exit_r"], propellant=spec["propellant"], cluster=cluster,
               notes=spec["notes"] + notes_extra, confidence=spec["confidence"])
    return exit_p


def rcs_cluster(prefix, link, centre, az_deg, dirs, spec, mat_pod, mat_nozzle, pod=(0.12, 0.14, 0.12), offset=None):
    radial, tang = radial_frame(az_deg)
    c = Vector(centre)
    G.add_mesh_uv(f"{prefix}_pod", G.box_uv(tuple(c), pod), mat_pod, link, smooth=False)
    off = offset if offset is not None else max(pod) * 0.5
    for n, d in enumerate(dirs):
        flow = (radial * d[0] + tang * d[1] + Vector((0, 0, d[2]))).normalized()
        thruster_cone(f"{prefix}_{n}", link, c + flow * off, flow, spec, mat_nozzle, cluster=prefix)


def panel(name, link, centre, u, v, w, h, t, mat_front, mat_back, normal=None):
    c, u, v = Vector(centre), Vector(u).normalized(), Vector(v).normalized()
    n = Vector(normal).normalized() if normal is not None else u.cross(v).normalized()
    corners = [c + u * sx * w / 2 + v * sy * h / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    V = [p + n * t / 2 for p in corners] + [p - n * t / 2 for p in corners]
    uv = [(0, 0), (w, 0), (w, h), (0, h)]
    G.add_mesh(f"{name}_front", V[:4], [(0, 1, 2, 3)], mat_front, link, uvs=uv)
    G.add_mesh(f"{name}_back", V[4:] + V[:4], [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
               mat_back, link, uvs=uv + uv)
    return n


def sphere_geo(c, r, rings=16, segments=32):
    prof = [(max(r * math.sin(math.pi * k / rings), 1e-3), -r * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    return G.lathe_geo(prof, segments, center=tuple(c))


def dish(name, link, centre, boresight, r, mat_front, mat_back, depth=0.35, segments=40):
    c, b = Vector(centre), Vector(boresight).normalized()
    f = r / (4 * depth) if depth else r
    prof = [(max(r * k / 12, 1e-3), (r * k / 12) ** 2 / (4 * f)) for k in range(13)]
    frame = _lathe_frame(b)
    G.add_mesh_uv(f"{name}_front", G.lathe_geo(prof, segments, c, frame), mat_front, link)
    G.add_mesh_uv(f"{name}_back", G.lathe_geo([(rr, z - 0.008) for rr, z in prof], segments, c, frame, flip=True), mat_back, link)
    return c + b * f


def chamfer_square(half, chamfer, phase_deg=0.0):
    pts = []
    for k in range(4):
        a = math.radians(phase_deg + 90 * k)
        u, v = Vector((math.cos(a), math.sin(a))), Vector((-math.sin(a), math.cos(a)))
        pts += [u * half - v * (half - chamfer), u * half + v * (half - chamfer)]
    return [(p.x, p.y) for p in pts]


def loft_geo(poly0, z0, poly1, z1, top=True, bottom=True):
    n = len(poly0)
    V, F, U = [], [], []
    u = 0.0
    for k in range(n):
        a0, a1 = Vector((*poly0[k], z0)), Vector((*poly0[(k + 1) % n], z0))
        b0, b1 = Vector((*poly1[k], z1)), Vector((*poly1[(k + 1) % n], z1))
        w = (a1 - a0).length
        h = ((a0 + a1) / 2 - (b0 + b1) / 2).length
        o = len(V)
        V += [a0, a1, b1, b0]
        du = ((b1 - b0).length - w) / 2
        U += [(u, 0), (u + w, 0), (u + w + du, h), (u - du, h)]
        F.append((o, o + 1, o + 2, o + 3))
        u += w
    for poly, z, on, rev in ((poly1, z1, top, False), (poly0, z0, bottom, True)):
        if not on:
            continue
        o = len(V)
        V += [Vector((x, y, z)) for x, y in poly]
        U += list(poly)
        f = tuple(range(o, o + n))
        F.append(f[::-1] if rev else f)
    return [tuple(v) for v in V], F, U


def ring_loft_geo(rings, cap_first=True, cap_last=True):
    rings = [[Vector(p) for p in r] for r in rings]
    n = len(rings[0])
    V, F, U = [], [], []
    for a, b in zip(rings, rings[1:]):
        u = 0.0
        h = ((sum(a, Vector()) / n) - (sum(b, Vector()) / n)).length
        for k in range(n):
            a0, a1, b0, b1 = a[k], a[(k + 1) % n], b[k], b[(k + 1) % n]
            w = (a1 - a0).length
            o = len(V)
            V += [a0, a1, b1, b0]
            U += [(u, 0), (u + w, 0), (u + w, h), (u, h)]
            F.append((o, o + 1, o + 2, o + 3))
            u += w
    for ring, on, rev in ((rings[0], cap_first, True), (rings[-1], cap_last, False)):
        if not on:
            continue
        c = sum(ring, Vector()) / n
        e1 = (ring[0] - c).normalized()
        e2 = (ring[1] - ring[0]).cross(ring[2] - ring[1]).normalized().cross(e1)
        o = len(V)
        V += ring
        U += [((p - c).dot(e1), (p - c).dot(e2)) for p in ring]
        f = tuple(range(o, o + n))
        F.append(f[::-1] if rev else f)
    return [tuple(v) for v in V], F, U
