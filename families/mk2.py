import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P

TAU = 2 * math.pi
D = {
    "height": 15.30,
    "facets": 16,
    "cabin_r": 2.95, "cabin_bot": 1.70, "cabin_top": 4.60, "skirt_bot": 1.00, "skirt_r": 2.80,
    "truss_r": 3.05, "truss_bot": 4.60, "truss_mid": 6.50, "truss_top": 8.80, "truss_bays": 8, "truss_tube": 0.055,
    "tank_r": 2.85, "tank_hh": 0.92, "tank_z": (5.55, 7.70),
    "lh2_r": 2.70, "lh2_bot": 8.90, "lh2_top": 13.60,
    "panel_az": (45, 135, 225, 315), "panel_arc": 52.0, "panel_arc_bot": 80.0, "panel_r": 2.82, "panel_flare_deg": 8.0, "panel_top": 13.50,
    "panel_bot": 9.00,
    "dome_band_z": 13.75, "dome_top": 15.30,
    "dish_r": 0.45, "dish_az": (90, 270), "dish_rad": 2.20, "dish_z": 15.05,
    "be7_n": 3, "be7_radius": 1.00, "be7_exit_z": 1.42, "be7_exit_r": 0.34, "be7_throat_r": 0.036, "be7_len": 1.45,
    "be7_gimbal_deg": 6.0, "be7_az0": 90.0,
    "leg_az": (0, 90, 180, 270), "hard_point_r": 3.12, "hard_point_z": 6.40, "foot_r": 5.20, "pad_r": 0.42, "pad_h": 0.15,
    "knee_frac": 0.62, "stroke": 0.40,
    "door_az": 135.0, "door_w": 1.00, "door_h": 1.85, "door_sill": 2.50,
    "port_az": 322.0, "port_r": 0.55, "port_z": 3.30,
    "window_az": 0.0, "window_z": 3.50,
    "rcs_az": (0, 90, 180, 270), "rcs_z": 4.95,
}


def polar(r, az_deg, z):
    a = math.radians(az_deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def frame(az_deg):
    a = math.radians(az_deg)
    return Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))


def flat_r(r):
    return r * math.cos(math.pi / D["facets"])


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    m = M.get
    body = G.link("body", (0, 0, 0), mass=cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"])
    _cabin(body, m)
    _truss(body, m)
    _tanks(body, m)
    _lh2(body, m)
    for i in range(D["be7_n"]):
        _engine(i, D["be7_az0"] + 360.0 * i / D["be7_n"], body, m)
    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, m)
    for i, az in enumerate(D["rcs_az"]):
        _rcs(i, az, body, m, cfg)
    _crew_door(body, m)
    _docking_port(body, m)
    _windows(body, m)
    _flag(body, m)
    for i, az in enumerate(D["dish_az"]):
        _dish(i, az, body, m)
    for name, link, pos, d, r, *rest in _light_specs():
        light(name, body, pos, d, m, r, *rest)
    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("imu", body, (0, 0, 6.0), kind="sensor", description="IMU / navigation reference (estimated)")
    G.site("top_deck", body, (0, 0, D["dome_top"]), kind="payload_interface", description="Dome top / lifting interface")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, polar(D["truss_r"], az, D["truss_top"]), kind="handling", description="GSE lift point (truss top ring)")
    return body


def _cabin(body, m):
    n, ph = D["facets"], math.pi / D["facets"]
    fr = flat_r(D["cabin_r"])
    G.add_mesh_uv("cabin_shell", G.prism_geo(n, fr, D["cabin_bot"], D["cabin_top"] - 0.08, phase=ph, top=False, bottom=False),
                  m("white_panel"), body, smooth=False)
    G.add_mesh_uv("cabin_roof_ring", G.prism_geo(n, fr + 0.03, D["cabin_top"] - 0.08, D["cabin_top"], phase=ph), m("grey_panel"), body,
                  smooth=False)
    G.add_mesh_uv("cabin_floor", G.prism_geo(n, fr - 0.02, D["cabin_bot"] - 0.04, D["cabin_bot"], phase=ph, top=False), m("grey_panel"),
                  body, smooth=False)
    skirt = G.prism_geo(n, flat_r(D["skirt_r"]), D["skirt_bot"], D["cabin_bot"] - 0.04, phase=ph, top=False)
    G.add_mesh_uv("engine_skirt", G.puff(skirt, 0.015, 0.25, seed=3), m("mli_gold"), body, smooth=False)
    G.add_mesh_uv("engine_bay_floor", G.lathe_geo([(D["be7_radius"] + 0.55, D["skirt_bot"]), (flat_r(D["skirt_r"]) - 0.02, D["skirt_bot"])],
                                                  64), m("mli_gold"), body)
    for k in range(n):
        a = TAU * (k + 0.5) / n
        p0 = Vector((math.cos(a), math.sin(a), 0)) * (D["cabin_r"] + 0.005)
        G.add_mesh_uv(f"cabin_seam_{k}", G.box_uv((p0.x, p0.y, (D["cabin_bot"] + D["cabin_top"]) / 2), (0.014, 0.014, D["cabin_top"] - D["cabin_bot"] - 0.1)),
                      m("grey_panel"), body, smooth=False)


def _truss(body, m):
    n, R, t = D["truss_bays"], D["truss_r"], D["truss_tube"]
    zs = (D["truss_bot"], D["truss_mid"], D["truss_top"])
    segs = []
    for k in range(n):
        a0, a1 = 360.0 * k / n + 22.5, 360.0 * (k + 1) / n + 22.5
        for lvl in range(2):
            z0, z1 = zs[lvl], zs[lvl + 1]
            segs.append((polar(R, a0, z0), polar(R, a0, z1)))
            mid = (a0 + a1) / 2
            if (k + lvl) % 2 == 0:
                segs += [(polar(R, a0, z0), polar(R, mid, z1)), (polar(R, mid, z1), polar(R, a1, z0))]
            else:
                segs += [(polar(R, a0, z1), polar(R, mid, z0)), (polar(R, mid, z0), polar(R, a1, z1))]
    G.add_mesh_uv("truss_struts", G.merge_geo(*[G.tube_uv(a, b, t, 8) for a, b in segs]), m("strut"), body)
    for z in zs:
        ring = [polar(R, 360.0 * k / 48, z) for k in range(49)]
        G.add_mesh_uv(f"truss_ring_{int(z * 100)}", G.merge_geo(*[G.tube_uv(a, b, t * 1.6, 8) for a, b in zip(ring, ring[1:])]),
                      m("frame"), body)
    G.add_mesh_uv("truss_mid_band", G.lathe_geo([(R + 0.04, D["truss_mid"] - 0.10), (R + 0.04, D["truss_mid"] + 0.10)], 64), m("white_panel"),
                  body)


def _ellipsoid(c, r, hh, rings=18):
    prof = [(max(r * math.sin(math.pi * k / rings), 1e-3), c - hh * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    return G.lathe_geo(prof, 64)


def _tanks(body, m):
    for i, zc in enumerate(D["tank_z"]):
        G.add_mesh_uv(f"lox_tank_{i}", G.puff(_ellipsoid(zc, D["tank_r"], D["tank_hh"]), 0.02, 0.4, seed=11 + i), m("mli_white"), body)
        G.add_mesh_uv(f"lox_tank_{i}_girth", G.lathe_geo([(D["tank_r"] + 0.02, zc - 0.06), (D["tank_r"] + 0.02, zc + 0.06)], 64), m("frame"),
                      body)
    G.add_mesh_uv("feed_column", G.tube_uv((0, 0, D["cabin_top"]), (0, 0, D["lh2_bot"]), 0.22, 24), m("frame"), body)


def _lh2(body, m):
    r = D["lh2_r"]
    G.add_mesh_uv("lh2_tank", G.puff(G.lathe_geo([(r * 0.6, D["lh2_bot"] - 0.25), (r, D["lh2_bot"] + 0.15), (r, D["lh2_top"])], 64),
                                     0.02, 0.5, seed=21), m("mli_silver"), body)
    band = D["dome_band_z"]
    G.add_mesh_uv("dome", G.lathe_geo([(r + 0.06, D["lh2_top"] - 0.05), (r + 0.06, band - 0.05), (r + 0.02, band + 0.25),
                                       (r - 0.20, band + 0.70), (r - 0.75, D["dome_top"] - 0.12), (1.40, D["dome_top"]), (1e-3, D["dome_top"])], 64),
                  m("white_panel"), body)
    G.add_mesh_uv("dome_band", G.lathe_geo([(r + 0.075, band - 0.05), (r + 0.075, band + 0.05)], 64), m("blue_paint"), body)
    G.add_mesh_uv("dome_ring", G.lathe_geo([(r + 0.09, D["lh2_top"] - 0.08), (r + 0.09, D["lh2_top"] + 0.04)], 64), m("frame"), body)
    for k, az in enumerate(D["panel_az"]):
        _sunshield(k, az, body, m)


def _sunshield(k, az, body, m):
    rt, half, half_b = D["panel_r"], math.radians(D["panel_arc"] / 2), math.radians(D["panel_arc_bot"] / 2)
    zt, zb = D["panel_top"], D["panel_bot"]
    flare = math.radians(D["panel_flare_deg"])
    radial, tang = frame(az)
    hinge = polar(rt, az, zt)
    link = G.link(f"sunshield_{k}", tuple(hinge), body, mass=60.0,
                  joint={"type": "revolute", "axis": tuple(-tang), "limit": (math.radians(-6), math.radians(30)), "role": "radiator",
                         "drive": {"kind": "position", "stiffness": 6.0e4, "damping": 6.0e3, "max_force": 2.0e4}})
    nu, nv = 16, 8
    V, F, U = [], [], []
    for side, dr in ((0, 0.0), (1, -0.025)):
        for j in range(nv + 1):
            z = zt - (zt - zb) * j / nv
            rr = rt + dr + (zt - z) * math.tan(flare)
            hz = half + (half_b - half) * j / nv
            for i in range(nu + 1):
                a = math.radians(az) - hz + 2 * hz * i / nu
                V.append((rr * math.cos(a), rr * math.sin(a), z))
                U.append((rr * (a - math.radians(az)), z))
    w = nu + 1
    off = (nv + 1) * w
    for j in range(nv):
        for i in range(nu):
            a, b = j * w + i, j * w + i + 1
            F.append((a, a + w, b + w, b))
            F.append((off + a, off + b, off + b + w, off + a + w))
    for i in range(nu):
        F.append((i, i + 1, off + i + 1, off + i))
        a, b = nv * w + i, nv * w + i + 1
        F.append((a, off + a, off + b, b))
    for j in range(nv):
        for i in (0, nu):
            a, c = j * w + i, (j + 1) * w + i
            F.append((a, off + a, off + c, c) if i == 0 else (a, c, off + c, off + a))
    G.add_mesh_uv(f"sunshield_{k}_panel", (V, F, U), m("sunshield"), link, smooth=False)
    for s in (-1, 1):
        a = math.radians(az) + s * half * 0.8
        p = Vector((rt * math.cos(a), rt * math.sin(a), zt))
        G.add_mesh_uv(f"sunshield_{k}_hinge_{s + 1}", G.tube_uv(p - tang * 0.12, p + tang * 0.12, 0.05, 12), m("frame"), body)
        q = Vector(((rt - 0.03) * math.cos(a), (rt - 0.03) * math.sin(a), zb + 0.6))
        G.add_mesh_uv(f"sunshield_{k}_actuator_{s + 1}", G.tube_uv(q, Vector((D["lh2_r"] * math.cos(a), D["lh2_r"] * math.sin(a), zb + 1.2)),
                                                                   0.03, 10), m("strut"), link)
    G.site(f"sunshield_{k}_normal", link, tuple(polar(rt + 0.05, az, (zt + zb) / 2)), tuple(radial), kind="thermal",
           description="Deployable sunshield / radiator panel centre (+Z outward)")


def _engine(i, az, body, m):
    g = D["be7_gimbal_deg"]
    exit_z = D["be7_exit_z"]
    top_z = exit_z + D["be7_len"]
    c = polar(D["be7_radius"], az, 0)
    pivot = (c.x, c.y, top_z - 0.08)
    drive = {"kind": "position", "stiffness": 20000.0, "damping": 400.0, "max_force": 4000.0}
    gx = G.link(f"be7_{i}_gimbal_x", pivot, body, mass=5.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal", "drive": drive})
    eng = G.link(f"be7_{i}", pivot, gx, mass=180.0,
                 joint={"type": "revolute", "axis": (0, 1, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal", "drive": drive})
    rt, re, L = D["be7_throat_r"], D["be7_exit_r"], D["be7_len"]
    throat_z = exit_z + L * 0.78
    bell = [(rt + (re - rt) * (1 - (1 - t) ** 1.9), throat_z - (throat_z - exit_z) * t) for t in [k / 24 for k in range(25)]][::-1]
    ctr = (c.x, c.y, 0)
    G.add_mesh_uv(f"be7_{i}_nozzle", G.lathe_geo([(r + 0.012, z) for r, z in bell], 64, center=ctr), m("nozzle_ext"), eng)
    G.add_mesh_uv(f"be7_{i}_nozzle_inner", G.lathe_geo(bell, 64, center=ctr, flip=True), m("nozzle_int"), eng)
    G.add_mesh_uv(f"be7_{i}_lip", G.lathe_geo([(re, exit_z), (re + 0.012, exit_z)], 64, center=ctr), m("nozzle_ext"), eng)
    G.add_mesh_uv(f"be7_{i}_chamber", G.lathe_geo([(rt + 0.01, throat_z), (0.11, throat_z + 0.10), (0.11, throat_z + 0.26),
                                                    (0.13, throat_z + 0.30), (0.13, top_z - 0.12), (0.06, top_z - 0.08)], 32, center=ctr),
                  m("engine_metal"), eng)
    for s, (dx, dy) in enumerate(((0.19, 0.0), (-0.17, 0.08))):
        G.add_mesh_uv(f"be7_{i}_turbopump_{s}", G.tube_uv((c.x + dx, c.y + dy, throat_z + 0.05), (c.x + dx, c.y + dy, throat_z + 0.38), 0.07, 20,
                                                          r1=0.065), m("engine_metal"), eng)
    G.add_mesh_uv(f"be7_{i}_gimbal_block", G.box_uv(pivot, (0.16, 0.16, 0.10)), m("frame"), gx, smooth=False)
    G.thruster(f"be7_{i}_exit", eng, (c.x, c.y, exit_z), (0, 0, -1), kind="main", thrust_n=44482.0, min_thrust_n=8896.0, isp_s=460.0,
               exit_radius=re, throat_radius=rt, propellant="LOX/LH2",
               notes="BE-7 dual-expander, 10,000 lbf, 20-100% throttle; MK2 uses three (Blue Origin). Positions estimated.",
               confidence="thrust/isp/count official; geometry estimated")


def _leg(i, az, body, m):
    hp = polar(D["hard_point_r"], az, D["hard_point_z"])
    foot = polar(D["foot_r"], az, 0.02)
    roots = [polar(flat_r(D["skirt_r"]) - 0.02, az + s * 20.0, D["skirt_bot"] + 0.15) for s in (-1, 1)]
    mats = {"primary": m("leg_upper"), "collar": m("frame"), "secondary": m("leg_lower"), "piston": m("leg_lower"), "footpad": m("footpad")}
    piston, knee, axis = P.leg(i, body, hp, foot, roots, mats, stroke=D["stroke"], knee_frac=D["knee_frac"], r_outer=0.11, r_piston=0.085,
                               r_secondary=0.06, pad_r=D["pad_r"], pad_h=D["pad_h"], piston_mass=60.0, stiffness=4.0e5, damping=6.0e4,
                               max_force=2.0e6)
    G.add_mesh_uv(f"leg_{i}_hardpoint", G.box_uv(tuple(hp), (0.30, 0.30, 0.30)), m("frame"), body, smooth=False)
    G.site(f"leg_{i}_touchdown_sensor", piston, tuple(knee + axis * 0.1), tuple(axis), kind="sensor", description="Stroke / touchdown switch")


def _rcs(i, az, body, m, cfg):
    radial, tang = frame(az + 45)
    c = polar(D["cabin_r"] + 0.30, az + 45, D["rcs_z"])
    G.add_mesh_uv(f"rcs_{i}_mount", G.tube_uv(polar(D["truss_r"] - 0.05, az + 45, D["rcs_z"]), c, 0.06, 10), m("frame"), body)
    P.rcs_cluster(f"rcs_{i}", body, c, az + 45, [(1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], cfg.RCS["rcs"], m("pod"),
                  m("nozzle_ext"), pod=(0.40, 0.36, 0.50), offset=0.22)


def _crew_door(body, m):
    az = D["door_az"]
    radial, tang = frame(az)
    fr = flat_r(D["cabin_r"])
    w, h, sill = D["door_w"], D["door_h"], D["door_sill"]
    zc = sill + h / 2
    face = radial * (fr + 0.01)
    G.add_mesh_uv("crew_door_frame", G.merge_geo(*[obox(face + Vector((0, 0, zc)) + tang * s * (w / 2 + 0.06), tang, (0.12, 0.10, h + 0.24))
                                                 for s in (-1, 1)], *[obox(face + Vector((0, 0, zc + s * (h / 2 + 0.06))), tang, (w + 0.24, 0.10, 0.12))
                                                                     for s in (-1, 1)]), m("frame"), body, smooth=False)
    hinge = face + radial * 0.08 - tang * (w / 2) + Vector((0, 0, zc))
    door = G.link("crew_door", tuple(hinge), body, mass=45.0,
                  joint={"type": "revolute", "axis": tuple(tang.cross(radial)), "limit": (0.0, math.radians(110)), "role": "hatch",
                         "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 600.0}})
    dc = face + radial * 0.06 + Vector((0, 0, zc))
    G.add_mesh_uv("crew_door_panel", obox(dc, tang, (w, 0.08, h)), m("white_panel"), door, smooth=False)
    G.add_mesh_uv("crew_door_window", G.tube_uv(dc + radial * 0.04 + Vector((0, 0, 0.45)), dc + radial * 0.05 + Vector((0, 0, 0.45)), 0.11, 24),
                  m("glass"), door)
    G.add_mesh_uv("crew_door_handle", G.tube_uv(dc + radial * 0.05 + tang * (w / 2 - 0.12) - Vector((0, 0, 0.15)),
                                                dc + radial * 0.05 + tang * (w / 2 - 0.12) + Vector((0, 0, 0.15)), 0.02, 10), m("yellow"), door)
    plat_z = sill - 0.05
    plat_c = face + radial * 0.75 + Vector((0, 0, plat_z))
    G.add_mesh_uv("crew_platform", obox(plat_c, tang, (1.50, 1.30, 0.06)), m("grating"), body, smooth=False)
    for s in (-1, 1):
        a = face + tang * s * 0.75 + Vector((0, 0, plat_z))
        b = a + radial * 1.40
        G.pipe(f"crew_platform_rail_{s + 1}", [a + Vector((0, 0, 0.03)), a + Vector((0, 0, 1.05)), b + Vector((0, 0, 1.05)), b + Vector((0, 0, 0.03))],
               0.025, m("frame"), body)
        G.add_mesh_uv(f"crew_platform_brace_{s + 1}", G.tube_uv(a + radial * 0.1 - Vector((0, 0, 0.05)), a + radial * 1.3 - Vector((0, 0, 0.05)) - Vector((0, 0, 0.0)), 0.04, 10),
                      m("frame"), body)
        G.add_mesh_uv(f"crew_platform_strut_{s + 1}", G.tube_uv(face + tang * s * 0.7 + Vector((0, 0, D["skirt_bot"] + 0.3)),
                                                                a + radial * 1.25 - Vector((0, 0, 0.05)), 0.035, 10), m("frame"), body)
    top = face + radial * 1.42 + Vector((0, 0, plat_z))
    stair = G.link("crew_stair", tuple(top), body, mass=55.0,
                   joint={"type": "revolute", "axis": tuple(radial.cross(Vector((0, 0, 1)))), "limit": (0.0, math.radians(100)),
                          "role": "stair", "drive": {"kind": "position", "stiffness": 2.0e4, "damping": 2.0e3, "max_force": 8000.0}})
    foot = top + radial * 2.25 - Vector((0, 0, plat_z - 0.02))
    for s in (-1, 1):
        a, b = top + tang * s * 0.55, foot + tang * s * 0.55
        G.add_mesh_uv(f"crew_stair_stringer_{s + 1}", G.tube_uv(a, b, 0.045, 10), m("frame"), stair)
        G.pipe(f"crew_stair_rail_{s + 1}", [b + Vector((0, 0, 0.05)), b + Vector((0, 0, 0.95)), a + Vector((0, 0, 0.95)), a + Vector((0, 0, 0.05))],
               0.022, m("frame"), stair)
    nsteps = 7
    for k in range(1, nsteps + 1):
        p = top + (foot - top) * k / (nsteps + 1)
        G.add_mesh_uv(f"crew_stair_tread_{k}", obox(p, tang, (1.10, 0.26, 0.035)), m("grating"), stair, smooth=False)
    G.site("crew_door_centre", door, tuple(dc + radial * 0.05), tuple(radial), kind="hatch", description="Crew egress door (outer face)")
    G.site("crew_platform", body, tuple(plat_c + Vector((0, 0, 0.03))), (0, 0, 1), kind="crew", description="Egress platform")
    G.site("stair_foot", stair, tuple(foot), (0, 0, -1), kind="contact", description="Crew stair foot (deployed)")


def obox(c, tang, size):
    c, u = Vector(c), Vector(tang).normalized()
    w, v = Vector((0, 0, 1)), Vector((0, 0, 1)).cross(Vector(tang)).normalized() * -1
    hx, hy, hz = (x / 2 for x in size)
    V, F, U = [], [], []
    for n, a, b, hn, ha, hb in ((u, v, w, hx, hy, hz), (-u, w, v, hx, hz, hy), (v, w, u, hy, hz, hx), (-v, u, w, hy, hx, hz), (w, u, v, hz, hx, hy),
                                (-w, v, u, hz, hy, hx)):
        o = len(V)
        fc = c + n * hn
        V += [tuple(fc - a * ha - b * hb), tuple(fc + a * ha - b * hb), tuple(fc + a * ha + b * hb), tuple(fc - a * ha + b * hb)]
        U += [(0, 0), (2 * ha, 0), (2 * ha, 2 * hb), (0, 2 * hb)]
        F.append((o, o + 1, o + 2, o + 3))
    return V, F, U


def _docking_port(body, m):
    az = D["port_az"]
    radial, tang = frame(az)
    fr = flat_r(D["cabin_r"])
    c = radial * fr + Vector((0, 0, D["port_z"]))
    r = D["port_r"]
    G.add_mesh_uv("docking_collar", G.lathe_geo([(r, 0.0), (r + 0.22, 0.0), (r + 0.22, 0.30), (r + 0.10, 0.36), (r, 0.36)], 48, center=tuple(c),
                                                axis_frame=P._lathe_frame(radial)), m("frame"), body)
    G.add_mesh_uv("docking_ring", G.lathe_geo([(r + 0.04, 0.36), (r + 0.16, 0.36), (r + 0.16, 0.42), (r + 0.04, 0.42)], 48, center=tuple(c),
                                              axis_frame=P._lathe_frame(radial)), m("engine_metal"), body)
    for k in range(3):
        a = TAU * k / 3 + math.pi / 2
        p = c + radial * 0.44 + (tang * math.cos(a) + Vector((0, 0, math.sin(a)))) * (r + 0.10)
        G.add_mesh_uv(f"docking_guide_{k}", obox(p, tang, (0.12, 0.10, 0.16)), m("frame"), body, smooth=False)
    hinge = c + radial * 0.40 + tang * r
    hatch = G.link("docking_hatch", tuple(hinge), body, mass=35.0,
                   joint={"type": "revolute", "axis": tuple((-tang).cross(radial)), "limit": (0.0, math.radians(110)), "role": "hatch",
                          "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 600.0}})
    G.add_mesh_uv("docking_hatch_disc", G.lathe_geo([(1e-3, 0.0), (r - 0.02, 0.0), (r - 0.02, 0.06), (1e-3, 0.08)], 48, center=tuple(c + radial * 0.33),
                                                    axis_frame=P._lathe_frame(radial)), m("grey_panel"), hatch)
    G.site("docking_port", body, tuple(c + radial * 0.42), tuple(radial), kind="docking", description="IDSS-style docking port (Orion / Gateway); +Z outward")


def _flag(body, m):
    r = D["cabin_r"] * math.cos(math.pi / D["facets"]) + 0.012
    w, h, zc = 0.95, 0.50, D["window_z"] + 0.05
    a0 = math.radians(D["window_az"] + 24.0)
    V, U = [], []
    for k in range(9):
        a = a0 + (w / r) * k / 8
        for s in (0, 1):
            V.append((r * math.cos(a), r * math.sin(a), zc - h / 2 + s * h))
            U.append((k / 8, s))
    F = [(2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2) for k in range(8)]
    G.add_mesh("flag_decal", V, F, m("flag"), body, uvs=U)


def _windows(body, m):
    az = D["window_az"]
    radial, tang = frame(az)
    fr = flat_r(D["cabin_r"])
    for s in (-1, 1):
        c = radial * (fr + 0.02) + tang * s * 0.45 + Vector((0, 0, D["window_z"]))
        P.panel(f"window_{s + 1}", body, c, tang, (0, 0, 1), 0.50, 0.60, 0.02, m("glass_amber"), m("frame"), normal=radial)
        G.add_mesh_uv(f"window_{s + 1}_hood", obox(c + radial * 0.14 + Vector((0, 0, 0.36)), tang, (0.66, 0.30, 0.06)),
                      m("frame"), body, smooth=False)
        for t in (-1, 1):
            G.add_mesh_uv(f"window_{s + 1}_cheek_{t + 1}", obox(c + radial * 0.14 + tang * t * 0.31, tang, (0.04, 0.30, 0.72)),
                          m("frame"), body, smooth=False)
        G.sensor_camera(f"window_cam_{s + 1}", body, tuple(c + radial * 0.05), tuple(radial - Vector((0, 0, 0.3))), (0, 0, 1),
                        {"focal_mm": 14.0, "aperture_mm": (7.2, 5.4), "fstop": 4.0, "clip_m": (0.1, 500.0), "resolution": (1920, 1080),
                         "source": "Crew window viewpoint (estimated)"})


def _dish(i, az, body, m):
    radial, tang = frame(az)
    base = polar(D["dish_rad"], az, D["dish_z"] - 0.30)
    G.add_mesh_uv(f"dish_{i}_mast", G.tube_uv(base, base + Vector((0, 0, 0.30)), 0.06, 16), m("frame"), body)
    top = base + Vector((0, 0, 0.30))
    azl = G.link(f"dish_{i}_azimuth", tuple(top), body, mass=6.0,
                 joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "antenna",
                        "drive": {"kind": "position", "stiffness": 60.0, "damping": 6.0, "max_force": 40.0}})
    G.add_mesh_uv(f"dish_{i}_az_housing", G.tube_uv(top, top + Vector((0, 0, 0.12)), 0.10, 16), m("engine_metal"), azl)
    piv = top + Vector((0, 0, 0.12 + D["dish_r"] * 0.4))
    el = G.link(f"dish_{i}_elevation", tuple(piv), azl, mass=8.0,
                joint={"type": "revolute", "axis": tuple(-tang), "limit": (math.radians(-20), math.radians(90)), "role": "antenna",
                       "drive": {"kind": "position", "stiffness": 60.0, "damping": 6.0, "max_force": 40.0}})
    G.add_mesh_uv(f"dish_{i}_yoke", G.box_uv(tuple(top + Vector((0, 0, 0.06 + D["dish_r"] * 0.2))), (0.06, 0.06, 0.12 + D["dish_r"] * 0.4)),
                  m("frame"), azl, smooth=False)
    b = (radial * 0.8 + Vector((0, 0, 0.6))).normalized()
    c = piv + b * 0.06
    f = P.dish(f"dish_{i}", el, c, b, D["dish_r"], m("radome"), m("white_panel"), depth=0.3)
    G.add_mesh_uv(f"dish_{i}_feed", G.tube_uv(c, f, 0.01, 8), m("frame"), el)
    G.site(f"dish_{i}_boresight", el, tuple(f), tuple(b), kind="antenna", band="S/Ka", description="Gimballed high-gain antenna boresight (+Z)")


def _light_specs():
    out = []
    for k, az in enumerate((-35, 35, 145, 215)):
        out.append((f"dome_flood_{k}", "body", polar(D["lh2_r"] - 0.15, az, D["dome_band_z"] + 1.0),
                    tuple((polar(1, az, 0) * 0.8 - Vector((0, 0, 0.6))).normalized()), 0.12))
    radial, tang = frame(D["window_az"])
    out.append(("cabin_flood_front", "body", tuple(radial * (flat_r(D["cabin_r"]) + 0.03) + Vector((0, 0, D["window_z"] + 0.75))),
                tuple((radial - Vector((0, 0, 0.5))).normalized()), 0.10))
    radial, tang = frame(D["door_az"])
    out.append(("door_flood", "body", tuple(radial * (flat_r(D["cabin_r"]) + 0.03) + tang * 0.8 + Vector((0, 0, D["door_sill"] + D["door_h"] + 0.35))),
                tuple((radial - Vector((0, 0, 0.6))).normalized()), 0.08))
    for k, az in enumerate(D["leg_az"]):
        out.append((f"leg_flood_{k}", "body", polar(flat_r(D["skirt_r"]) + 0.03, az, D["skirt_bot"] + 0.2),
                    tuple((polar(1, az, 0) - Vector((0, 0, 0.5))).normalized()), 0.07))
    return out


def light(name, link, pos, d, m, r=0.05, intensity=200000.0):
    p, d = Vector(pos), Vector(d).normalized()
    G.add_mesh_uv(f"{name}_housing", G.tube_uv(p - d * r * 1.2, p, r, 20), m("engine_metal"), link)
    G.add_mesh_uv(f"{name}_lens", G.tube_uv(p, p + d * r * 0.16, r * 0.84, 20), m("lamp"), link)
    G.site(name, link, tuple(p + d * 0.01), tuple(d), kind="light", description="Floodlight (+Z = beam axis)", radius_m=r * 0.84,
           intensity=intensity, colour_k=5600.0)
