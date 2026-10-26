import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P
import rover_kit as K

WHEEL_FRAME = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]


def axis_frame(d):
    f = P._axis_frame(d)
    return None if f is None else [list(r) for r in zip(*f)]


def dish(name, link, centre, boresight, r, mat_front, mat_back, depth=0.35, segments=40):
    c, b = Vector(centre), Vector(boresight).normalized()
    f = r / (4 * depth) if depth else r
    prof = [(max(r * k / 12, 1e-3), (r * k / 12) ** 2 / (4 * f)) for k in range(13)]
    frame = axis_frame(b)
    G.add_mesh_uv(f"{name}_front", G.lathe_geo(prof, segments, c, frame), mat_front, link)
    G.add_mesh_uv(f"{name}_back", G.lathe_geo([(rr, z - 0.008) for rr, z in prof], segments, c, frame, flip=True), mat_back, link)
    return c + b * f
LINKS = {}


def build(cfg):
    LINKS.clear()
    R = cfg.ROVER
    m = M.get
    total = cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"]
    chassis = G.link("chassis", (0, 0, 0), mass=total)
    LINKS["chassis"] = chassis
    for c in R.get("carriers", []):
        _carrier(c, R, total, m)
    for L in R.get("links", []):
        joint = {"type": L.get("type", "revolute"), "axis": tuple(L.get("axis", (0, 0, 1))), "role": L.get("role", "actuated")}
        if "limit" in L:
            joint["limit"] = tuple(L["limit"])
        if L.get("drive"):
            joint["drive"] = dict(L["drive"])
        LINKS[L["name"]] = G.link(L["name"], L["pos"], LINKS[L.get("parent", "chassis")], joint, mass=L.get("mass", 5.0))
    for lp in R.get("loops", []):
        G.loop_joint(lp["name"], lp["parent"], lp["child"], tuple(lp["anchor"]), tuple(lp["axis"]), jtype=lp.get("type", "revolute"))
    for w in R["wheels"]:
        _wheel_module(w, R, total, m)
    for p in R.get("parts", []):
        _part(p, m)
    if R.get("crew"):
        _crew(R["crew"], chassis, m)
    for i, mast in enumerate(R.get("masts", [])):
        _mast(i, mast, chassis, m)
    if R.get("hga"):
        _hga(R["hga"], m)
    for i, s in enumerate(R.get("solar", [])):
        _solar(i, s, m)
    if R.get("arm"):
        _arm(R["arm"], m)
    for i, lt in enumerate(R.get("lights", [])):
        _light(lt[3] if len(lt) > 3 else f"light_{i}", LINKS[lt[4]] if len(lt) > 4 else chassis, lt[0], lt[1], m,
               lt[2] if len(lt) > 2 else 0.05)
    for n, link, pos, z_axis, kind, desc, *extra in R.get("sites", []):
        G.site(n, LINKS[link], pos, z_axis, kind=kind, description=desc, **(extra[0] if extra else {}))
    G.site("vehicle_origin", chassis, (0, 0, 0), kind="reference", description="Ground point under the chassis centre at nominal ride height")
    G.site("imu", chassis, R.get("imu", (0, 0, R["wheel"]["r"] * 1.5)), kind="sensor", description="IMU / navigation reference (estimated)")
    return chassis


def _v(p):
    return Vector(p)


def obox_geo(c, ax, ay, size):
    c, ax, ay = Vector(c), Vector(ax).normalized(), Vector(ay).normalized()
    az = ax.cross(ay).normalized()
    ay = az.cross(ax).normalized()
    hx, hy, hz = (s / 2 for s in size)
    V, F, U = [], [], []
    for n, u, v, hn, hu, hv in ((ax, ay, az, hx, hy, hz), (-ax, az, ay, hx, hz, hy), (ay, az, ax, hy, hz, hx),
                                (-ay, ax, az, hy, hx, hz), (az, ax, ay, hz, hx, hy), (-az, ay, ax, hz, hy, hx)):
        o = len(V)
        fc = c + n * hn
        V += [fc - u * hu - v * hv, fc + u * hu - v * hv, fc + u * hu + v * hv, fc - u * hu + v * hv]
        U += [(0, 0), (2 * hu, 0), (2 * hu, 2 * hv), (0, 2 * hv)]
        F.append((o, o + 1, o + 2, o + 3))
    return [tuple(p) for p in V], F, U


def rrect(hw, hh, rc, n=4):
    rc = min(rc, hw * 0.999, hh * 0.999)
    pts = []
    for cx, cy, a0 in ((hw - rc, hh - rc, 0), (-hw + rc, hh - rc, 90), (-hw + rc, -hh + rc, 180), (hw - rc, -hh + rc, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return pts


def loft_x_geo(stations, n=4, caps=(True, True)):
    rings = []
    for x, hw, zc, hh, rc in stations:
        rings.append([Vector((x, y, zc + z)) for y, z in rrect(hw, hh, rc, n)])
    k = len(rings[0])
    V, F, U = [], [], []
    vlen = 0.0
    for i in range(len(rings)):
        if i:
            vlen += (rings[i][0] - rings[i - 1][0]).length
        ulen = 0.0
        for j in range(k + 1):
            p = rings[i][j % k]
            if j:
                ulen += (p - rings[i][(j - 1) % k]).length
            V.append(tuple(p))
            U.append((ulen, vlen))
    for i in range(len(rings) - 1):
        for j in range(k):
            a, b = i * (k + 1) + j, (i + 1) * (k + 1) + j
            F.append((a, b, b + 1, a + 1))
    for ring, on, rev in ((rings[0], caps[0], False), (rings[-1], caps[1], True)):
        if not on:
            continue
        o = len(V)
        V += [tuple(p) for p in ring]
        U += [(p.y, p.z) for p in ring]
        f = tuple(range(o, o + k))
        F.append(f[::-1] if rev else f)
    return V, F, U


def arc_shell_geo(c, r, w, a0, a1, t=0.006, seg=16):
    V, F, U = [], [], []
    for side in (0, 1):
        rr = r + side * t
        for s in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * s / seg)
            for y in (-w / 2, w / 2):
                V.append((c.x + rr * math.sin(a), c.y + y, c.z + rr * math.cos(a)))
                U.append((rr * math.radians(a1 - a0) * s / seg, y))
    n = (seg + 1) * 2
    for s in range(seg):
        a, b = s * 2, (s + 1) * 2
        F.append((a, a + 1, b + 1, b))
        F.append((n + a, n + b, n + b + 1, n + a + 1))
    for s in (0, seg):
        a = s * 2
        F.append((a, n + a, n + a + 1, a + 1) if s == 0 else (a, a + 1, n + a + 1, n + a))
    for s in range(seg):
        for y in (0, 1):
            a, b = s * 2 + y, (s + 1) * 2 + y
            F.append((a, b, n + b, n + a) if y == 0 else (a, n + a, n + b, b))
    return V, F, U


def _drive(kind, **kw):
    return {"kind": kind, **kw}


def _wheel_mass(R, total):
    n = len(R["wheels"])
    W = R["wheel"]
    return W.get("mass", max(0.05, 0.035 * total * 4 / n))


def _module_masses(R, total):
    n = len(R["wheels"])
    base = total * 4 / n
    mm = {"steer": 0.012, "upright": 0.006, "lower_arm": 0.006, "upper_arm": 0.004, "strut": 0.0015, "arm": 0.01}
    mm = {k: max(0.02, v * base) for k, v in mm.items()}
    mm.update(R.get("module_masses", {}))
    return mm


def _carrier(c, R, total, m):
    parent = LINKS[c.get("parent", "chassis")]
    jt = c.get("type", "revolute")
    k, target = c.get("stiffness", 0.0), c.get("target", 0.0)
    if c.get("auto_spring"):
        a = c["auto_spring"]
        f = total * K.G_MOON * a["wheels"] / len(R["wheels"])
        lever = a.get("lever", 1.0)
        k = f * lever / a["static"]
        target = -a["static"]
        if not c.get("damping"):
            c["damping"] = 2 * a.get("zeta", 0.5) * math.sqrt(k / (lever * lever) * total * a["wheels"] / len(R["wheels"])) * lever * lever
    joint = {"type": jt, "axis": c.get("axis", (0, 1, 0)), "limit": c.get("limit", (-0.5, 0.5)),
             "role": c.get("role", "suspension"),
             "drive": _drive(c.get("drive", "spring"), stiffness=k * c.get("gain", 1.0), damping=c.get("damping", 0.0),
                             max_force=c.get("max_force", 1.0e6), target=target / c.get("gain", 1.0))}
    if jt == "fixed":
        joint = {"type": "fixed"}
    link = G.link(c["name"], c["pos"], parent, joint, mass=c.get("mass", 0.01 * total))
    LINKS[c["name"]] = link
    pos = _v(c["pos"])
    mat = m(c.get("mat", "anodised_grey"))
    b = c.get("beam", 0.08)
    if jt == "revolute" and c.get("pivot", True):
        ax = Vector(c.get("axis", (0, 1, 0)))
        G.add_mesh_uv(f"{c['name']}_pivot", G.tube_uv(pos - ax * 0.6 * b, pos + ax * 0.6 * b, b * 0.7, 16), m("titanium"), link)
    for q in c.get("beams_to", []):
        v, f = G.box_beam_geo(pos, _v(q), b, b * 1.3)
        G.add_mesh(f"{c['name']}_beam", v, f, mat, link)
    if c.get("column"):
        col = c["column"]
        G.add_mesh_uv(f"{c['name']}_column", G.tube_uv(pos + Vector(col.get("from", (0, 0, 0))), pos + Vector(col.get("to", (0, 0, 0.5))),
                                                       col.get("r", 0.08), 24), m(col.get("mat", "anodised_grey")), link)
    if c.get("sleeve"):
        sl = c["sleeve"]
        G.add_mesh_uv(f"{c['name']}_sleeve", G.tube_uv(pos + Vector(sl.get("from", (0, 0, 0))), pos + Vector(sl.get("to", (0, 0, 0.5))),
                                                       sl.get("r", 0.1), 24), m(sl.get("mat", "anodised_grey")), parent)


def _wheel_module(w, R, total, m):
    W, S = R["wheel"], dict(R.get("suspension", {}))
    S.update(w.get("suspension", {}))
    n = w["name"]
    side = 1 if w["y"] > 0 else -1
    r, width = W["r"], W["w"]
    wc = Vector((w["x"], w["y"], w.get("z", r)))
    ko = S.get("kingpin_off", width / 2 + 0.25 * r)
    ky = wc.y - side * ko
    mm = _module_masses(R, total)
    nw = len(R["wheels"])
    up_dz, lo_dz = S.get("upper_dz", 0.42 * r), S.get("lower_dz", -0.30 * r)
    kind = S.get("type", "carrier")
    if kind == "double_wishbone":
        carrier = _wishbone(n, w, S, R, wc, ky, side, up_dz, lo_dz, mm, total, nw, m)
    elif kind == "trailing_arm":
        carrier = _trailing(n, w, S, wc, ky, side, up_dz, mm, total, nw, m)
    else:
        carrier = LINKS[w.get("carrier", "chassis")]
        top = Vector((wc.x, ky, wc.z + up_dz))
        if w.get("mount_to"):
            v, f = G.box_beam_geo(_v(w["mount_to"]), top + Vector((0, 0, 0.04 * r)), S.get("beam", 0.07 * r + 0.02),
                                  S.get("beam", 0.07 * r + 0.02))
            G.add_mesh(f"{n}_mount_beam", v, f, m(S.get("arm_mat", "anodised_grey")), carrier)
    steer_lim = w.get("steer")
    parent = carrier
    if steer_lim:
        parent = G.link(f"{n}_steer", (wc.x, ky, wc.z), carrier, mass=mm["steer"],
                        joint={"type": "revolute", "axis": (0, 0, 1), "limit": tuple(steer_lim), "role": "steer",
                               "drive": _drive("position", stiffness=S.get("steer_k", 40.0 * total / nw),
                                               damping=S.get("steer_c", 4.0 * total / nw),
                                               max_force=S.get("steer_tau", 3.0 * total / nw))})
        LINKS[f"{n}_steer"] = parent
    _knuckle(n, parent, wc, ky, side, r, width, up_dz, S, m, steer=bool(steer_lim))
    if R.get("fenders"):
        F = R["fenders"]
        G.add_mesh_uv(f"{n}_fender", arc_shell_geo(Vector((wc.x, wc.y, wc.z)), r + F.get("gap", 0.05), width + 2 * F.get("overhang", 0.03),
                                                   F.get("arc", (-60, 70))[0], F.get("arc", (-60, 70))[1]),
                      m(F.get("mat", "white_panel")), parent, smooth=True)
    wheel = G.link(f"{n}_wheel", tuple(wc), parent, mass=_wheel_mass(R, total),
                   joint={"type": "revolute", "axis": (0, 1, 0), "role": "drive",
                          "drive": _drive("velocity", stiffness=0.0, damping=W.get("drive_c", 6.0 * total / nw),
                                          max_force=W.get("drive_tau", total * K.G_MOON / nw * r * 1.2))}
                   if w.get("drive", True) else
                   {"type": "revolute", "axis": (0, 1, 0), "role": "linkage", "drive": _drive("none", stiffness=0.0, damping=0.2)})
    LINKS[f"{n}_wheel"] = wheel
    _wheel_geo(n, wheel, wc, W, side, m)
    G.site(f"{n}_contact", wheel, (wc.x, wc.y, wc.z - r), (0, 0, -1), kind="contact", description="Nominal tyre contact point")
    G.site(f"{n}_hub", wheel, tuple(wc), (0, side, 0), kind="reference", description="Wheel centre; +Z = outboard axle")


def _wishbone(n, w, S, R, wc, ky, side, up_dz, lo_dz, mm, total, nw, m):
    chassis = LINKS["chassis"]
    arm = S["arm"]
    arm_u = arm * S.get("upper_ratio", 0.85)
    spread = S.get("spread", 0.55 * arm)
    rr = S.get("tube_r", 0.012 + 0.012 * R["wheel"]["r"])
    lb, ub = Vector((wc.x, ky, wc.z + lo_dz)), Vector((wc.x, ky, wc.z + up_dz))
    li, ui = Vector((wc.x, ky - side * arm, lb.z)), Vector((wc.x, ky - side * arm_u, ub.z))
    k, c, target = K.suspension_tuning(total, nw, arm, S.get("static_rad", 0.12), S.get("zeta", 0.45))
    reb, jnc = S.get("travel", (0.12, 0.15))
    lim = (-math.asin(min(0.95, reb / arm)), math.asin(min(0.95, jnc / arm)))
    if S.get("active"):
        drive = {"type": "revolute", "axis": (side, 0, 0), "limit": (lim[0] - 0.35, lim[1]), "role": "active_suspension",
                 "drive": _drive("position", stiffness=k * 15, damping=c * 4, max_force=k * 2, target=target / 15)}
    else:
        drive = {"type": "revolute", "axis": (side, 0, 0), "limit": lim, "role": "suspension",
                 "drive": _drive("spring", stiffness=k, damping=c, max_force=1.0e6, target=target)}
    lower = G.link(f"{n}_lower_arm", tuple(li), chassis, drive, mass=mm["lower_arm"])
    upright = G.link(f"{n}_upright", tuple(lb), lower, mass=mm["upright"],
                     joint={"type": "revolute", "axis": (side, 0, 0), "limit": (-1.2, 1.2), "role": "linkage",
                            "drive": _drive("none", stiffness=0.0, damping=0.0)})
    upper = G.link(f"{n}_upper_arm", tuple(ui), chassis, mass=mm["upper_arm"],
                   joint={"type": "revolute", "axis": (side, 0, 0), "limit": (-1.2, 1.2), "role": "linkage",
                          "drive": _drive("none", stiffness=0.0, damping=0.0)})
    G.loop_joint(f"{n}_upper_ball", f"{n}_upper_arm", f"{n}_upright", tuple(ub), (side, 0, 0))
    arm_mat, joint_mat = m(S.get("arm_mat", "anodised_grey")), m("titanium")
    for link, inner, outer, tag in ((lower, li, lb, "lower"), (upper, ui, ub, "upper")):
        segs = [(inner + Vector((s * spread / 2, 0, 0)), outer) for s in (-1, 1)]
        for j, (p0, p1) in enumerate(segs):
            G.add_mesh_uv(f"{n}_{tag}_arm_{j}", G.tube_uv(p0, p1, rr, 12), arm_mat, link)
            G.add_mesh_uv(f"{n}_{tag}_bush_{j}", G.tube_uv(p0 - Vector((0.03, 0, 0)), p0 + Vector((0.03, 0, 0)), rr * 1.6, 12),
                          joint_mat, link)
        G.add_mesh_uv(f"{n}_{tag}_ball", P.sphere_geo(outer, rr * 1.7, 8, 12), joint_mat, link)
        G.add_mesh_uv(f"{n}_{tag}_bracket", G.box_uv(tuple(inner), (spread + 0.08, 0.05 + rr, 0.05 + 2 * rr)), arm_mat, chassis,
                      smooth=False)
    v, f = G.box_beam_geo(lb, ub, 2.4 * rr, 2.4 * rr)
    G.add_mesh(f"{n}_upright_post", v, f, arm_mat, upright)
    if S.get("strut", True):
        lm = li + (lb - li) * S.get("strut_at", 0.6)
        top = Vector((lm.x, ui.y - side * S.get("strut_in", 0.12 * arm), ub.z + S.get("strut_up", 0.35 * (up_dz - lo_dz))))
        axis = (lm - top).normalized()
        body = G.link(f"{n}_strut", tuple(top), chassis, mass=mm["strut"],
                      joint={"type": "revolute", "axis": (side, 0, 0), "limit": (-1.0, 1.0), "role": "linkage",
                             "drive": _drive("none", stiffness=0.0, damping=0.0)})
        L = (lm - top).length
        rod = G.link(f"{n}_strut_rod", tuple(top), body, mass=mm["strut"],
                     joint={"type": "prismatic", "axis": tuple(axis), "limit": (-0.6 * L, 0.6 * L), "role": "linkage",
                            "drive": _drive("none", stiffness=0.0, damping=0.0)})
        G.loop_joint(f"{n}_strut_eye", f"{n}_strut_rod", f"{n}_lower_arm", tuple(lm), (side, 0, 0), jtype="spherical")
        G.add_mesh_uv(f"{n}_strut_body", G.tube_uv(top, top + axis * L * 0.55, rr * 1.9, 14), m("anodised_dark"), body)
        coil = []
        turns, cr = 7, rr * 2.8
        a_, b_ = G._frame(axis)
        for i in range(turns * 12 + 1):
            t = i / (turns * 12)
            ang = 2 * math.pi * turns * t
            coil.append(top + axis * (0.15 + 0.7 * t) * L + (a_ * math.cos(ang) + b_ * math.sin(ang)) * cr)
        G.pipe(f"{n}_spring", coil, rr * 0.45, m(S.get("spring_mat", "accent")), rod, sides=6)
        G.add_mesh_uv(f"{n}_strut_shaft", G.tube_uv(top + axis * L * 0.45, lm, rr * 0.9, 12), m("titanium"), rod)
        G.add_mesh_uv(f"{n}_strut_mount", G.box_uv(tuple(top), (0.07, 0.05, 0.05)), arm_mat, chassis, smooth=False)
    return upright


def _trailing(n, w, S, wc, ky, side, up_dz, mm, total, nw, m):
    chassis = LINKS["chassis"]
    dx = S.get("arm_dx", 0.6) * (1 if w["x"] > 0 else -1) * (-1 if S.get("leading", False) else 1)
    pivot = Vector((wc.x - dx, ky - side * S.get("arm_dy", 0.0), wc.z + S.get("pivot_dz", up_dz)))
    arm = abs(dx)
    k, c, target = K.suspension_tuning(total, nw, arm, S.get("static_rad", 0.12), S.get("zeta", 0.45))
    sgn = -1 if dx > 0 else 1
    reb, jnc = S.get("travel", (0.12, 0.15))
    lim = (-math.asin(min(0.95, reb / arm)), math.asin(min(0.95, jnc / arm)))
    if S.get("active"):
        joint = {"type": "revolute", "axis": (0, sgn, 0), "limit": (lim[0] - 0.5, lim[1]), "role": "active_suspension",
                 "drive": _drive("position", stiffness=k * 15, damping=c * 4, max_force=k * 2, target=target / 15)}
    else:
        joint = {"type": "revolute", "axis": (0, sgn, 0), "limit": lim, "role": "suspension",
                 "drive": _drive("spring", stiffness=k, damping=c, max_force=1.0e6, target=target)}
    link = G.link(f"{n}_arm", tuple(pivot), chassis, joint, mass=mm["arm"])
    LINKS[f"{n}_arm"] = link
    b = S.get("beam", 0.05 + 0.05 * w.get("scale", 1.0))
    top = Vector((wc.x, ky, wc.z + up_dz))
    v, f = G.box_beam_geo(pivot, top, b, b * 1.3)
    G.add_mesh(f"{n}_arm_beam", v, f, m(S.get("arm_mat", "anodised_grey")), link)
    G.add_mesh_uv(f"{n}_arm_pivot", G.tube_uv(pivot - Vector((0, b, 0)), pivot + Vector((0, b, 0)), b * 0.8, 16), m("titanium"), link)
    G.add_mesh_uv(f"{n}_arm_actuator", G.tube_uv(pivot - Vector((0, side * b * 1.6, 0)), pivot - Vector((0, side * b * 0.9, 0)),
                                                 b * 1.1, 16), m("anodised_dark"), chassis)
    return link


def _knuckle(n, link, wc, ky, side, r, width, up_dz, S, m, steer):
    mat = m(S.get("knuckle_mat", "anodised_grey"))
    t = S.get("knuckle_t", 0.05 + 0.06 * r)
    top = Vector((wc.x, ky, wc.z + up_dz))
    low = Vector((wc.x, ky, wc.z - 0.15 * r))
    v, f = G.box_beam_geo(top, low, t, t * 1.3)
    G.add_mesh(f"{n}_knuckle", v, f, mat, link)
    if steer:
        G.add_mesh_uv(f"{n}_steer_motor", G.tube_uv(top, top + Vector((0, 0, 0.12 * r + 0.04)), t * 1.0, 20), m("anodised_dark"), link)
        G.add_mesh_uv(f"{n}_steer_cap", G.tube_uv(top + Vector((0, 0, 0.12 * r + 0.04)), top + Vector((0, 0, 0.12 * r + 0.06)),
                                                   t * 1.05, 20), m("aluminium"), link)
    hub_in = Vector((wc.x, ky, wc.z))
    hub_out = Vector((wc.x, wc.y - side * width * 0.25, wc.z))
    G.add_mesh_uv(f"{n}_axle", G.tube_uv(hub_in, hub_out, t * 0.45, 16), m("titanium"), link)


def _wheel_geo(n, link, wc, W, side, m):
    r, w = W["r"], W["w"]
    style = W.get("style", "spring")
    seg = W.get("segments", 48)
    ri = r * W.get("rim_frac", 0.82)
    rh = r * W.get("hub_frac", 0.28)
    c0 = Vector((wc.x, wc.y, wc.z))

    def lathe(profile, mat, name, flip=False):
        G.add_mesh_uv(f"{n}_{name}", G.lathe_geo(profile, seg, c0, WHEEL_FRAME, flip=flip), m(mat), link)

    gh = W.get("grouser_h", 0.03 * r + 0.004)
    band = [(ri, -w / 2), (r - gh, -w / 2), (r - gh, w / 2), (ri, w / 2), (ri, -w / 2)]
    if style in ("spring", "airless", "solid"):
        lathe(band, W.get("tread_mat", "tread"), "tread")
    elif style == "mesh":
        lathe([(r - gh, -w / 2), (r - gh, w / 2)], "tyre_mesh", "mesh")
        lathe([(r - gh - 0.004, w / 2), (r - gh - 0.004, -w / 2)], "tyre_mesh", "mesh_in")
        for s in (-1, 1):
            rb = r - gh + 0.004
            lathe([(ri, s * w / 2), (rb, s * w / 2), (rb, s * (w / 2 - 0.02)), (ri, s * (w / 2 - 0.02))], "titanium", f"bead_{s + 1}")
    else:
        lathe([(r - gh - 0.006, -w / 2), (r - gh, -w / 2), (r - gh, w / 2), (r - gh - 0.006, w / 2), (r - gh - 0.006, -w / 2)],
              W.get("drum_mat", "aluminium"), "drum")
    ng = W.get("grousers", 24)
    gmat = W.get("grouser_mat", "tread" if style in ("spring", "airless", "solid") else "titanium")
    geos = []
    for k in range(ng):
        a = 2 * math.pi * k / ng
        d = Vector((math.cos(a), 0, -math.sin(a)))
        tdir = Vector((-math.sin(a), 0, -math.cos(a)))
        cc = c0 + d * (r - gh / 2)
        if W.get("chevron", style in ("spring", "airless", "mesh")):
            for s in (-1, 1):
                ang = math.radians(28)
                ax = (tdir * math.sin(ang) + Vector((0, s, 0)) * math.cos(ang)).normalized()
                geos.append(obox_geo(cc + Vector((0, s * w / 4, 0)) + tdir * 0.0, ax, d, (w / 2 / math.cos(ang) * 0.95, gh, 0.018 + 0.02 * r)))
        else:
            geos.append(obox_geo(cc, Vector((0, 1, 0)), d, (w * 0.98, gh, 0.012 + 0.012 * r)))
    if geos:
        G.add_mesh_uv(f"{n}_grousers", G.merge_geo(*geos), m(gmat), link, smooth=False)
    if W.get("disc"):
        for s_ in (-1, 1):
            lathe([(rh, s_ * w * 0.3), (ri, s_ * w * 0.3)][::s_], W.get("disc_mat", W.get("rim_mat", "aluminium")), f"disc_{s_ + 1}")
    ns = W.get("spokes", 10)
    spoke_mat = m(W.get("spoke_mat", "composite" if style in ("spring", "airless") else "titanium"))
    sr = W.get("spoke_r", 0.008 + 0.012 * r)
    sp = []
    for k in range(ns):
        a = 2 * math.pi * (k + 0.5) / ns
        for y in ((-w * 0.25, w * 0.25) if style in ("spring", "airless") else (0.0,)):
            pts = []
            for i in range(7):
                t = i / 6
                rad = rh + (ri - rh) * t
                aa = a + W.get("spoke_curve", 0.35) * math.sin(math.pi * t)
                pts.append(c0 + Vector((rad * math.cos(aa), y, -rad * math.sin(aa))))
            for p0, p1 in zip(pts, pts[1:]):
                sp.append(G.tube_uv(p0, p1, sr, 6))
    if sp:
        G.add_mesh_uv(f"{n}_spokes", G.merge_geo(*sp), spoke_mat, link)
    rr = ri - 0.006
    lathe([(rr - 0.01, -w * 0.42), (rr, -w * 0.45), (rr, w * 0.45), (rr - 0.01, w * 0.42)], W.get("rim_mat", "aluminium"), "rim")
    lathe([(1e-3, side * w * 0.36), (rh * 0.6, side * w * 0.36), (rh, side * w * 0.28), (rh, -side * w * 0.3),
           (rh * 0.8, -side * w * 0.38), (1e-3, -side * w * 0.38)], W.get("hub_mat", "anodised_dark"), "hub_motor", flip=side < 0)
    lathe([(1e-3, side * (w * 0.36 + 0.012)), (rh * 0.45, side * (w * 0.36 + 0.008)), (rh * 0.5, side * w * 0.36)],
          W.get("hub_cap_mat", "aluminium"), "hub_cap", flip=side < 0)


def _part(p, m):
    kind, link = p["kind"], LINKS[p.get("link", "chassis")]
    name, mat = p["name"], m(p["mat"])
    if kind == "box":
        ob = G.add_mesh_uv(name, G.box_uv(p["c"], p["size"]), mat, link, smooth=False)
    elif kind == "cbox":
        x0, x1 = p["c"][0] - p["size"][0] / 2, p["c"][0] + p["size"][0] / 2
        hw, hh = p["size"][1] / 2, p["size"][2] / 2
        ob = G.add_mesh_uv(name, loft_x_geo([(x0, hw, p["c"][2], hh, p.get("r", 0.05)), (x1, hw, p["c"][2], hh, p.get("r", 0.05))],
                                            p.get("n", 3)), mat, link, smooth=False)
        if p["c"][1]:
            for i, v in enumerate(ob.data.vertices):
                v.co.y += p["c"][1]
    elif kind == "extrude":
        poly = [tuple(q) for q in p["profile"]]
        y0, y1 = p["y"]
        v, f, u = P.loft_geo(poly, y0, poly, y1)
        v = [(a, cc, b) for a, b, cc in v]
        f = [tuple(reversed(q)) for q in f]
        ob = G.add_mesh_uv(name, (v, f, u), mat, link, smooth=False)
    elif kind == "obox":
        ob = G.add_mesh_uv(name, obox_geo(p["c"], p["ax"], p["ay"], p["size"]), mat, link, smooth=False)
    elif kind == "loft":
        ob = G.add_mesh_uv(name, loft_x_geo(p["stations"], p.get("n", 4), p.get("caps", (True, True))), mat, link,
                           smooth=p.get("smooth", True))
    elif kind == "tube":
        ob = G.add_mesh_uv(name, G.tube_uv(p["p0"], p["p1"], p["r"], p.get("sides", 16), r1=p.get("r1")), mat, link)
    elif kind == "rail":
        ob = G.pipe(name, [Vector(q) for q in p["points"]], p["r"], mat, link, closed=p.get("closed", False), sides=8)
    elif kind == "beam":
        v, f = G.box_beam_geo(p["p0"], p["p1"], p["w"], p["h"])
        ob = G.add_mesh(name, v, f, mat, link)
    elif kind == "panel":
        P.panel(name, link, p["c"], p["u"], p["v"], p["w"], p["h"], p.get("t", 0.02), mat, m(p.get("back", "white_panel")),
                normal=p.get("normal"))
        ob = None
    elif kind == "disc":
        c, d = Vector(p["c"]), Vector(p["n"]).normalized()
        ob = G.add_mesh_uv(name, G.tube_uv(c, c + d * p.get("t", 0.02), p["r"], p.get("sides", 32)), mat, link)
    elif kind == "ring":
        c, d = Vector(p["c"]), Vector(p["n"]).normalized()
        frame = axis_frame(d)
        prof = [(p["r"], 0.0), (p["r"] + p["w"], 0.0), (p["r"] + p["w"], p["t"]), (p["r"], p["t"]), (p["r"], 0.0)]
        ob = G.add_mesh_uv(name, G.lathe_geo(prof, p.get("sides", 40), c, frame), mat, link)
    elif kind == "sphere":
        ob = G.add_mesh_uv(name, P.sphere_geo(p["c"], p["r"]), mat, link)
    elif kind == "lathe":
        c, d = Vector(p["c"]), Vector(p.get("n", (0, 0, 1))).normalized()
        ob = G.add_mesh_uv(name, G.lathe_geo(p["profile"], p.get("sides", 32), c, axis_frame(d)), mat, link)
    else:
        raise ValueError(kind)
    if p.get("variant") and ob is not None:
        G.tag_variant(ob, p["variant"])
    if p.get("variant") and ob is None:
        for o in [o for o in link.children if o.name.startswith(name)]:
            G.tag_variant(o, p["variant"])


def _crew(C, chassis, m):
    var = C.get("variant")
    obs = []
    z = C["floor_z"]
    for i, y in enumerate(C["seats_y"]):
        x = C["x"]
        if C.get("style", "seat") == "seat":
            sh = C.get("seat_h", 0.45)
            obs.append(G.add_mesh_uv(f"seat_{i}_pan", G.box_uv((x, y, z + sh), (0.50, 0.52, 0.05)), m("seat_cloth"), chassis, smooth=False))
            obs.append(G.add_mesh_uv(f"seat_{i}_back", obox_geo((x - 0.30, y, z + sh + 0.30), (0.25, 0, 1), (0, 1, 0), (0.62, 0.52, 0.04)),
                                     m("seat_cloth"), chassis, smooth=False))
            fr = []
            for s in (-1, 1):
                yy = y + s * 0.27
                fr += [((x + 0.25, yy, z), (x + 0.25, yy, z + sh)), ((x - 0.25, yy, z), (x - 0.25, yy, z + sh)),
                       ((x + 0.25, yy, z + sh), (x - 0.25, yy, z + sh)), ((x - 0.25, yy, z + sh), (x - 0.40, yy, z + sh + 0.62))]
            obs.append(G.add_mesh_uv(f"seat_{i}_frame", G.merge_geo(*[G.tube_uv(a, b, 0.014, 8) for a, b in fr]), m("aluminium"), chassis))
            obs.append(G.add_mesh_uv(f"seat_{i}_footrest", obox_geo((x + 0.62, y, z + 0.10), (0.6, 0, 0.8), (0, 1, 0), (0.30, 0.44, 0.02)),
                                     m("grey_panel"), chassis, smooth=False))
            G.site(f"crew_{i}_seat", chassis, (x, y, z + sh + 0.03), (0, 0, 1), kind="crew", description="Crew seat reference point (H-point)")
        else:
            obs.append(G.add_mesh_uv(f"stand_{i}_plate", G.box_uv((x, y, z + 0.015), (0.55, 0.55, 0.03)), m("grey_panel"), chassis, smooth=False))
            for s in (-1, 1):
                pts = [(x - 0.20, y + s * 0.32, z), (x - 0.20, y + s * 0.32, z + 1.05), (x + 0.30, y + s * 0.32, z + 1.05),
                       (x + 0.30, y + s * 0.32, z + 0.85)]
                obs.append(G.pipe(f"stand_{i}_rail_{s + 1}", [Vector(q) for q in pts], 0.018, m("aluminium"), chassis))
            obs.append(G.add_mesh_uv(f"stand_{i}_toe_bar", G.tube_uv((x + 0.25, y - 0.25, z + 0.10), (x + 0.25, y + 0.25, z + 0.10), 0.015, 8),
                                     m("aluminium"), chassis))
            G.site(f"crew_{i}_station", chassis, (x, y, z + 0.03), (0, 0, 1), kind="crew", description="Standing crew station foot plate")
    if C.get("console"):
        cx, cy, cz = C["console"]
        obs.append(G.add_mesh_uv("console", obox_geo((cx, cy, cz), (0.85, 0, -0.5), (0, 1, 0), (0.36, 0.40, 0.18)), m("grey_panel"),
                                 chassis, smooth=False))
        obs.append(G.add_mesh_uv("console_post", G.tube_uv((cx, cy, z), (cx, cy, cz - 0.08), 0.03, 12), m("aluminium"), chassis))
        obs.append(G.add_mesh_uv("console_display", obox_geo((cx - 0.05, cy, cz + 0.095), (0.85, 0, -0.5), (0, 1, 0), (0.24, 0.30, 0.01)),
                                 m("glass"), chassis, smooth=False))
        jx = cx - 0.32
        obs.append(G.add_mesh_uv("hand_controller_base", G.box_uv((jx, cy, cz - 0.10), (0.12, 0.12, 0.08)), m("anodised_dark"), chassis, smooth=False))
        obs.append(G.add_mesh_uv("hand_controller", G.tube_uv((jx, cy, cz - 0.06), (jx, cy, cz + 0.10), 0.015, 10), m("anodised_dark"), chassis))
        obs.append(G.add_mesh_uv("hand_controller_grip", G.tube_uv((jx, cy - 0.06, cz + 0.12), (jx, cy + 0.06, cz + 0.12), 0.018, 10),
                                 m("anodised_dark"), chassis))
        G.site("hand_controller", chassis, (jx, cy, cz + 0.12), (0, 0, 1), kind="crew", description="Hand controller grip (drive/steer)")
    for i, pts in enumerate(C.get("handholds", [])):
        obs.append(G.pipe(f"handhold_{i}", [Vector(q) for q in pts], 0.016, m(C.get("rail_mat", "accent")), chassis))
    if var:
        for o in obs:
            G.tag_variant(o, var)


def _mast(i, S, chassis, m):
    base = Vector(S["base"])
    top = base + Vector((0, 0, S["h"]))
    pre = S.get("name", f"mast_{i}")
    if S["h"] > 0.01:
        G.add_mesh_uv(f"{pre}_post", G.tube_uv(base, top, S.get("r", 0.03), 16), m(S.get("mat", "aluminium")), chassis)
    if S.get("foot", (0.12, 0.12, 0.04)):
        f = S.get("foot", (0.12, 0.12, 0.04))
        G.add_mesh_uv(f"{pre}_foot", G.box_uv(tuple(base + Vector((0, 0, f[2] / 2))), f), m("anodised_grey"), chassis, smooth=False)
    head_parent = chassis
    hz = top
    if S.get("pan_tilt", True):
        pan = G.link(f"{pre}_pan", tuple(top), chassis, mass=S.get("mass", 1.5) * 0.4,
                     joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "camera",
                            "drive": _drive("position", stiffness=30.0, damping=3.0, max_force=20.0)})
        G.add_mesh_uv(f"{pre}_pan_housing", G.tube_uv(top, top + Vector((0, 0, 0.06)), S.get("r", 0.03) * 1.6, 16), m("anodised_dark"), pan)
        hz = top + Vector((0, 0, 0.06 + S.get("head", (0.10, 0.30, 0.08))[2] / 2 + 0.01))
        tilt = G.link(f"{pre}_tilt", tuple(hz), pan, mass=S.get("mass", 1.5) * 0.6,
                      joint={"type": "revolute", "axis": (0, -1, 0), "limit": (math.radians(-60), math.radians(60)), "role": "camera",
                             "drive": _drive("position", stiffness=30.0, damping=3.0, max_force=20.0)})
        head_parent = tilt
        LINKS[f"{pre}_tilt"] = tilt
    hx, hy, hzz = S.get("head", (0.10, 0.30, 0.08))
    G.add_mesh_uv(f"{pre}_head", G.box_uv(tuple(hz), (hx, hy, hzz)), m(S.get("head_mat", "white_panel")), head_parent, smooth=False)
    fwd = Vector(S.get("forward", (1, 0, 0))).normalized()
    left = Vector((0, 0, 1)).cross(fwd).normalized()
    for j, off in enumerate(S.get("cams", (-0.10, 0.10))):
        p = hz + fwd * hx / 2 + left * off
        G.add_mesh_uv(f"{pre}_cam_{j}_lens", G.tube_uv(p, p + fwd * 0.03, 0.022, 14), m("lens"), head_parent)
        G.sensor_camera(f"{pre}_cam_{j}", head_parent, tuple(p + fwd * 0.03), tuple(fwd), (0, 0, 1),
                        {"focal_mm": S.get("focal_mm", 8.0), "aperture_mm": (7.2, 5.4), "fstop": 4.0, "clip_m": (0.05, 500.0),
                         "resolution": (2048, 1536), "source": S.get("source", "Navigation stereo camera (optics estimated)")})
    if S.get("lamp"):
        p = hz + fwd * hx / 2 - Vector((0, 0, hzz * 0.25))
        G.add_mesh_uv(f"{pre}_lamp", G.box_uv(tuple(p + fwd * 0.01), (0.02, hy * 0.25, 0.03)), m("lamp"), head_parent, smooth=False)


def _hga(H, m):
    parent = LINKS[H.get("link", "chassis")]
    base = Vector(H["base"])
    top = base + Vector((0, 0, H.get("h", 0.3)))
    G.add_mesh_uv("hga_mast", G.tube_uv(base, top, H.get("mast_r", 0.03), 16), m("aluminium"), parent)
    az = G.link("hga_azimuth", tuple(top), parent, mass=H.get("mass", 3.0) * 0.4,
                joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "antenna",
                       "drive": _drive("position", stiffness=40.0, damping=4.0, max_force=30.0)})
    G.add_mesh_uv("hga_az_housing", G.tube_uv(top, top + Vector((0, 0, 0.08)), H.get("mast_r", 0.03) * 1.8, 16), m("anodised_dark"), az)
    piv = top + Vector((0, 0, 0.08 + H["r"] * 0.35))
    el = G.link("hga_elevation", tuple(piv), az, mass=H.get("mass", 3.0) * 0.6,
                joint={"type": "revolute", "axis": (0, -1, 0), "limit": (math.radians(-20), math.radians(90)), "role": "antenna",
                       "drive": _drive("position", stiffness=40.0, damping=4.0, max_force=30.0)})
    G.add_mesh_uv("hga_yoke", G.box_uv(tuple(top + Vector((0, 0, 0.04 + H["r"] * 0.17))), (0.04, 0.05, 0.08 + H["r"] * 0.35)),
                  m("aluminium"), az, smooth=False)
    b = Vector(H.get("boresight", (1, 0, 0.3))).normalized()
    c = piv + b * 0.05
    focus = dish("hga_dish", el, c, b, H["r"], m(H.get("front", "radome")), m(H.get("back", "white_panel")), depth=H.get("depth", 0.3))
    G.add_mesh_uv("hga_feed", G.tube_uv(c, focus, 0.008, 8), m("aluminium"), el)
    G.site("hga_boresight", el, tuple(focus), tuple(b), kind="antenna", band=H.get("band", "X"),
           description="High-gain antenna boresight (+Z), 2-axis gimbal")


def _solar(i, S, m):
    parent = LINKS[S.get("link", "chassis")]
    name = S.get("name", f"solar_{i}")
    c = Vector(S["c"])
    u, v = Vector(S["u"]).normalized(), Vector(S["v"]).normalized()
    n = Vector(S.get("normal", tuple(u.cross(v)))).normalized()
    link = parent
    if S.get("hinge"):
        h = S["hinge"]
        link = G.link(name, h["pos"], parent, mass=S.get("mass", 2.0),
                      joint={"type": "revolute", "axis": h["axis"], "limit": h["limit"], "role": "solar",
                             "drive": _drive("position", stiffness=h.get("k", 200.0), damping=h.get("c", 20.0), max_force=h.get("tau", 200.0),
                                             target=h.get("target", 0.0))})
        LINKS[name] = link
        G.add_mesh_uv(f"{name}_hinge", G.tube_uv(Vector(h["pos"]) - Vector(h["axis"]) * 0.05, Vector(h["pos"]) + Vector(h["axis"]) * 0.05,
                                                 0.02, 12), m("titanium"), link)
    P.panel(name, link, c, u, v, S["w"], S["h"], S.get("t", 0.03), m(S.get("front", "solar_cells")), m(S.get("back", "white_panel")),
            normal=n)
    G.site(f"{name}_normal", link, tuple(c + n * 0.02), tuple(n), kind="power", area_m2=S["w"] * S["h"],
           description="Solar array centre; +Z = cell normal")


def _arm(A, m):
    parent = LINKS[A.get("link", "chassis")]
    base = Vector(A["base"])
    l1, l2, l3 = A["lengths"]
    r = A.get("r", 0.05)
    fwd = Vector(A.get("stow_dir", (-1, 0, 0))).normalized()
    left = Vector((0, 0, 1)).cross(fwd)
    left = left.normalized() if left.length > 1e-6 else Vector(A.get("side", (0, 1, 0)))
    mass = A.get("mass", 40.0)
    tau = A.get("tau", 400.0)

    def jt(axis, lim, scale):
        return {"type": "revolute", "axis": tuple(axis), "limit": lim, "role": "arm",
                "drive": _drive("position", stiffness=tau * 15 * scale, damping=tau * 1.5 * scale, max_force=tau * scale)}

    G.add_mesh_uv("arm_base", G.tube_uv(base - Vector(A.get("up", (0, 0, 1))) * 0.06, base, r * 1.6, 20), m("anodised_grey"), parent)
    yaw = G.link("arm_yaw", tuple(base), parent, jt(A.get("up", (0, 0, 1)), (-math.pi, math.pi), 1.0), mass=mass * 0.15)
    sh = base + Vector(A.get("up", (0, 0, 1))) * r * 2.2
    G.add_mesh_uv("arm_turret", G.tube_uv(base, sh, r * 1.4, 20), m(A.get("mat", "white_panel")), yaw)
    shoulder = G.link("arm_shoulder", tuple(sh), yaw, jt(left, (math.radians(-10), math.radians(150)), 1.0), mass=mass * 0.3)
    el = sh + fwd * l1
    G.add_mesh_uv("arm_upper", G.tube_uv(sh, el, r, 20), m(A.get("mat", "white_panel")), shoulder)
    G.add_mesh_uv("arm_shoulder_joint", G.tube_uv(sh - left * r * 1.3, sh + left * r * 1.3, r * 1.3, 20), m("anodised_dark"), shoulder)
    elbow = G.link("arm_elbow", tuple(el), shoulder, jt(left, (math.radians(-170), math.radians(5)), 0.6), mass=mass * 0.25)
    wr = el - fwd * l2 + Vector(A.get("fold_off", (0, 0, 1))) * r * 2.4
    G.add_mesh_uv("arm_elbow_joint", G.tube_uv(el - left * r * 1.2, el + left * r * 1.2, r * 1.2, 20), m("anodised_dark"), elbow)
    G.add_mesh_uv("arm_fore", G.tube_uv(el + Vector((0, 0, r * 0.2)), wr, r * 0.85, 20), m(A.get("mat", "white_panel")), elbow)
    wrist = G.link("arm_wrist_pitch", tuple(wr), elbow, jt(left, (-math.pi / 2, math.pi / 2), 0.3), mass=mass * 0.15)
    G.add_mesh_uv("arm_wrist_joint", G.tube_uv(wr - left * r, wr + left * r, r, 16), m("anodised_dark"), wrist)
    d = (-fwd)
    roll = G.link("arm_wrist_roll", tuple(wr + d * r * 1.2), wrist, jt(d, (-math.pi, math.pi), 0.2), mass=mass * 0.15)
    tip = wr + d * l3
    G.add_mesh_uv("arm_tool", G.tube_uv(wr + d * r * 1.2, tip, r * 0.7, 16), m("anodised_grey"), roll)
    for s in (-1, 1):
        G.add_mesh_uv(f"arm_finger_{s + 1}", G.box_uv(tuple(tip + d * 0.05 + left * s * r * 0.6), (0.10, 0.02, 0.04)), m("aluminium"), roll,
                      smooth=False)
    G.site("arm_tool_point", roll, tuple(tip + d * 0.1), tuple(d), kind="tool", description="End-effector tool centre point (+Z = approach)")
    LINKS["arm_wrist_roll"] = roll


def _light(name, link, pos, d, m, r=0.05):
    p, d = Vector(pos), Vector(d).normalized()
    G.add_mesh_uv(f"{name}_housing", G.tube_uv(p - d * r * 1.2, p, r, 20), m("anodised_dark"), link)
    G.add_mesh_uv(f"{name}_bezel", G.lathe_geo([(r * 0.84, 0.0), (r * 1.02, 0.0), (r * 1.02, r * 0.12), (r * 0.84, r * 0.12)], 24, p,
                                               axis_frame(d)), m("aluminium"), link)
    G.add_mesh_uv(f"{name}_lens", G.tube_uv(p, p + d * r * 0.16, r * 0.84, 20), m("lamp"), link)
    G.site(name, link, tuple(p + d * 0.01), tuple(d), kind="light", description="Floodlight (+Z = beam axis)", radius_m=r * 0.84,
           intensity=200000.0, colour_k=5600.0)
