import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P

D = {
    "flat_r": 0.785, "body_bot": 0.95, "body_top": 4.05, "deck_t": 0.04,
    "top_array_r": 0.95, "top_array_z": 4.20,
    "leg_az": [30, 90, 150, 210, 270, 330], "hard_point_z": 1.35, "foot_r": 2.30, "pad_r": 0.15, "pad_h": 0.07,
    "knee_frac": 0.86, "stroke": 0.15,
    "skirt_r": 0.45, "skirt_bot": 0.65,
    "engine_exit_z": 0.35, "engine_exit_r": 0.235, "engine_throat_r": 0.045, "engine_top_z": 1.45, "gimbal_deg": 5.0,
    "he_z": 2.60, "he_r": 0.31, "he_len": 0.85, "he_out": 0.18,
    "rcs_r": 1.10, "rcs_z": 3.98,
    "hga_z": 3.70, "hga_r": 0.185,
    "solar_side_w": 0.70, "solar_side_z": (1.45, 3.65),
}


def corner_r():
    return D["flat_r"] / math.cos(math.pi / 6)


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    m = M.get
    F = cfg.FEATURES
    body = G.link("body", (0, 0, 0), mass=cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"])
    fr, zb, zt = D["flat_r"], D["body_bot"], D["body_top"]

    G.add_mesh_uv("hull_core", G.prism_geo(6, fr, zb, zt), m("white_panel"), body, smooth=False)
    face_w = 2 * corner_r() * math.sin(math.pi / 6)
    for az, bands in cfg.FACES.items():
        radial, tang = P.radial_frame(az)
        for j, (z0, z1, mat) in enumerate(bands):
            c = radial * (fr + 0.008) + Vector((0, 0, (z0 + z1) / 2))
            P.panel(f"face_{az}_{j}", body, c, tang, (0, 0, 1), face_w - 0.03, z1 - z0 - 0.01, 0.012, m(mat), m(mat), normal=radial)
    for k in range(6):
        p = P.polar(corner_r(), 30 + 60 * k, 0)
        G.add_mesh_uv(f"longeron_{k}", G.box_uv((p.x, p.y, (zb + zt) / 2), (0.05, 0.05, zt - zb)), m("aluminium"), body, smooth=False)
    for z in (zb + 0.02, 2.30, zt - 0.02):
        G.add_mesh_uv(f"frame_ring_{z:.2f}", G.prism_geo(6, fr + 0.016, z - 0.02, z + 0.02, top=False, bottom=False),
                      m("aluminium"), body, smooth=False)
    G.add_mesh_uv("top_deck", G.prism_geo(6, fr + 0.02, zt, zt + D["deck_t"]), m("deck_panel"), body, smooth=False)

    _top_array(body, m)
    G.add_mesh_uv("heat_shield_skirt", G.prism_geo(6, fr * 0.98, D["skirt_bot"] + 0.12, zb), m("mli_silver"), body, smooth=False)
    G.add_mesh_uv("heat_shield_ring", G.lathe_geo([(D["skirt_r"], D["skirt_bot"]), (fr * 0.98, D["skirt_bot"] + 0.12)], 48),
                  m("beta_white"), body)
    G.add_mesh_uv("heat_shield_floor", G.lathe_geo([(D["engine_exit_r"] * 0.55, D["skirt_bot"]), (D["skirt_r"], D["skirt_bot"])], 48),
                  m("beta_white"), body)
    _engine(body, m)

    _he_tank(body, m, 0)
    if F.get("second_he_tank"):
        _he_tank(body, m, 180)
    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, m)
    for i, az in enumerate(D["leg_az"]):
        _rcs_pod(i, az, body, m, cfg)
    for i, az in enumerate(F.get("solar_side_az", [])):
        _side_array(i, az, body, m)
    _hga(body, m)
    _deck(body, m, cfg)

    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("deck_center", body, (0, 0, D["top_array_z"]), kind="payload_interface", description="Top deck centre (above the array)")
    G.site("imu", body, (0, 0, 3.0), kind="sensor", description="IMU / navigation reference (estimated location)")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, P.polar(corner_r() - 0.05, az, zt), kind="handling", description="GSE lift point (deck corner)")
    return body


def _top_array(body, m):
    z = D["top_array_z"]
    r = D["top_array_r"]
    for k in range(6):
        p = P.polar(D["flat_r"] - 0.1, 60 * k, D["body_top"] + D["deck_t"])
        G.add_mesh_uv(f"top_array_standoff_{k}", G.tube_uv(p, p + Vector((0, 0, z - 0.02 - p.z)), 0.015, 8), m("aluminium"), body)
    G.add_mesh_uv("top_array_cells", G.prism_geo(6, r * math.cos(math.pi / 6) - 0.04, z - 0.01, z + 0.01, bottom=False),
                  m("solar_cells"), body, smooth=False)
    G.add_mesh_uv("top_array_frame", G.prism_geo(6, r * math.cos(math.pi / 6), z - 0.03, z + 0.008, top=False),
                  m("frame_yellow"), body, smooth=False)
    G.add_mesh_uv("top_array_back", G.prism_geo(6, r * math.cos(math.pi / 6), z - 0.035, z - 0.03, top=False), m("frame_yellow"),
                  body, smooth=False)
    G.site("top_array_normal", body, (0, 0, z + 0.02), (0, 0, 1), kind="power", area_m2=2.6 * r * r,
           description="Top-deck solar array centre; +Z = cell normal")


def _engine(body, m):
    g = D["gimbal_deg"]
    ez, re, rt = D["engine_exit_z"], D["engine_exit_r"], D["engine_throat_r"]
    pivot = (0, 0, D["engine_top_z"] - 0.06)
    drive = {"kind": "position", "stiffness": 3000.0, "damping": 60.0, "max_force": 600.0}
    gx = G.link("vr900_gimbal_x", pivot, body, mass=1.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                       "drive": drive})
    eng = G.link("vr900", pivot, gx, mass=25.0,
                 joint={"type": "revolute", "axis": (0, 1, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                        "drive": drive})
    L = 1.05 - ez + 0.35
    throat = P.bell("vr900", eng, (0, 0, ez), re, rt, L, m("nozzle_ext"), m("nozzle_int"), wall=0.008, throat_frac=1.0, power=2.0)
    G.add_mesh_uv("vr900_chamber", G.lathe_geo([(rt + 0.008, throat.z), (0.08, throat.z + 0.07), (0.08, throat.z + 0.20),
                                                 (0.10, throat.z + 0.24), (0.10, pivot[2] - 0.08)], 24), m("engine_metal"), eng)
    for s, (dx, dy) in enumerate(((0.14, 0.0), (-0.14, 0.0))):
        G.add_mesh_uv(f"vr900_valve_{s}", G.box_uv((dx, dy, throat.z + 0.2), (0.08, 0.10, 0.12)), m("engine_metal"), eng, smooth=False)
    G.add_mesh_uv("vr900_gimbal_block", G.box_uv(pivot, (0.12, 0.12, 0.08)), m("aluminium"), gx, smooth=False)
    G.thruster("vr900_exit", eng, (0, 0, ez), (0, 0, -1), kind="main", thrust_n=3100.0, min_thrust_n=1400.0, isp_s=324.0,
               exit_radius=re, throat_radius=rt, propellant="LOX/LCH4",
               notes="Intuitive Machines VR900, helium pressure-fed, throttleable, 2-axis gimbal (IM). Throttle floor, "
                     "gimbal range and exit size estimated.",
               confidence="thrust press, Isp official; geometry estimated")
    G.site("vr900_gimbal_center", body, pivot, kind="reference", description="VR900 gimbal pivot")


def _he_tank(body, m, az):
    radial, tang = P.radial_frame(az)
    c = radial * (D["flat_r"] + D["he_out"] - D["he_r"] * 0.4) + Vector((0, 0, D["he_z"]))
    L = D["he_len"]
    frame = [[radial.x, 0, tang.x], [radial.y, 0, tang.y], [0, 1, 0]]
    prof = G.capsule_profile(D["he_r"], L - 2 * D["he_r"] * 0.75, 0.75)
    base = c - tang * L / 2
    G.add_mesh_uv(f"he_tank_{az}", G.puff(G.lathe_geo(prof, 40, tuple(base), frame), 0.015, 0.08, seed=az + 3), m("mli_copper"), body)
    for s in (-1, 1):
        G.add_mesh_uv(f"he_tank_{az}_mount_{s}", G.box_uv(tuple(c + tang * s * L * 0.3 - radial * D["he_r"] * 0.6),
                                                           (0.12, 0.12, 0.12)), m("aluminium"), body, smooth=False)


def _leg(i, az, body, m):
    hp = P.polar(corner_r(), az, D["hard_point_z"])
    foot = P.polar(D["foot_r"], az, D["pad_h"] * 0.1)
    roots = [P.polar(D["flat_r"] + 0.01, az + s * 30, D["body_bot"]) for s in (-1, 1)]
    mats = {"primary": m("aluminium"), "collar": m("aluminium"), "secondary": m("aluminium"), "piston": m("aluminium"),
            "footpad": m("footpad")}
    piston, knee, axis = P.leg(i, body, hp, foot, roots, mats, stroke=D["stroke"], knee_frac=D["knee_frac"], r_outer=0.033,
                               r_piston=0.026, r_secondary=0.025, pad_r=D["pad_r"], pad_h=D["pad_h"], piston_mass=1.5,
                               stiffness=1.2e4, damping=1.8e3, max_force=3.0e4)
    G.add_mesh_uv(f"leg_{i}_node", G.box_uv(tuple(hp), (0.09, 0.09, 0.09)), m("aluminium"), body, smooth=False)
    G.site(f"leg_{i}_touchdown_sensor", piston, tuple(knee + axis * 0.05), tuple(axis), kind="sensor",
           description="Crush-core stroke / touchdown switch (estimated)")


def _rcs_pod(i, az, body, m, cfg):
    c = P.polar(D["rcs_r"], az, D["rcs_z"])
    G.add_mesh_uv(f"rcs_{i}_boom", G.tube_uv(P.polar(corner_r() - 0.02, az, D["rcs_z"]), c, 0.015, 8), m("aluminium"), body)
    P.rcs_cluster(f"rcs_{i}", body, c, az, [(0, 1, 0), (0, -1, 0), (0, 0, -1) if i % 2 else (0, 0, 1)], cfg.RCS["cold_gas"],
                  m("white_panel"), m("engine_metal"), pod=(0.10, 0.10, 0.10), offset=0.05)


def _side_array(i, az, body, m):
    radial, tang = P.radial_frame(az)
    z0, z1 = D["solar_side_z"]
    c = radial * (D["flat_r"] + 0.05) + Vector((0, 0, (z0 + z1) / 2))
    P.panel(f"side_array_{i}", body, c, tang, (0, 0, 1), D["solar_side_w"], z1 - z0, 0.025, m("solar_cells"), m("frame_dark"),
            normal=radial)
    G.site(f"side_array_{i}_normal", body, tuple(c + radial * 0.02), tuple(radial), kind="power",
           area_m2=D["solar_side_w"] * (z1 - z0), description="Body-mounted side array centre; +Z = cell normal")


def _hga(body, m):
    radial = Vector((1, 0, 0))
    base = radial * (D["flat_r"] + 0.02) + Vector((0, 0, D["hga_z"]))
    bore = (radial + Vector((0, 0, 1))).normalized()
    c = base + radial * 0.10
    G.add_mesh_uv("hga_strut", G.tube_uv(base, c, 0.02, 10), m("aluminium"), body)
    feed = P.dish("hga", body, c, bore, D["hga_r"], m("radome"), m("aluminium"), depth=0.25)
    G.add_mesh_uv("hga_feed", G.tube_uv(c, feed, 0.012, 8), m("aluminium"), body)
    G.site("hga_boresight", body, tuple(feed), tuple(bore), kind="antenna", band="S",
           description="Fixed 16 dBi S-band high-gain antenna boresight (+Z); pointing estimated")


def _deck(body, m, cfg):
    F = cfg.FEATURES
    zt = D["body_top"]
    for j, az in enumerate(F.get("lga_az", [])):
        p0 = P.polar(corner_r(), az, zt - 0.15)
        p1 = P.polar(corner_r() + 0.22, az, zt - 0.05)
        G.add_mesh_uv(f"lga_{j}_boom", G.tube_uv(p0, p1, 0.012, 8), m("aluminium"), body)
        G.add_mesh_uv(f"lga_{j}_radome", G.lathe_geo([(1e-3, 0.0), (0.05, 0.01), (0.05, 0.05), (1e-3, 0.08)], 20,
                                                      center=tuple(p1)), m("radome"), body)
        G.site(f"lga_{j}", body, tuple(p1 + Vector((0, 0, 0.05))), kind="antenna", band="S",
               description="5 dBi low-gain antenna (estimated location)")
    if F.get("nav_pod"):
        az = F["nav_pod"]
        radial, tang = P.radial_frame(az)
        c = radial * (D["flat_r"] + 0.17) + Vector((0, 0, 3.30))
        G.add_mesh_uv("nav_pod", G.box_uv(tuple(c), (0.30, 0.30, 0.30)), m("deck_box"), body, smooth=False)
        for j, t in enumerate((-0.08, 0.08)):
            p = c + tang * t + radial * 0.08 - Vector((0, 0, 0.15))
            look = (radial * 0.35 + Vector((0, 0, -1))).normalized()
            G.add_mesh_uv(f"nav_cam_{j}_lens", G.tube_uv(p, p + look * 0.05, 0.025, 12), m("lens"), body)
            G.sensor_camera(f"nav_cam_{j}", body, tuple(p + look * 0.05), tuple(look), tuple(radial),
                            {"focal_mm": 12.0, "aperture_mm": (7.2, 5.4), "fstop": 4.0, "clip_m": (0.1, 5000.0),
                             "resolution": (2048, 2048), "source": "Nova-C TRN cameras - optics estimated"})
        G.site("ndl", body, tuple(c - Vector((0, 0, 0.15))), (0, 0, -1), kind="sensor",
               description="NASA Navigation Doppler Lidar optical head (location estimated)")
    for j, az in enumerate(F.get("scalpss_az", [])):
        p = P.polar(D["flat_r"] + 0.06, az, D["body_bot"] + 0.15)
        look = (-P.polar(1, az, 0) * 0.5 + Vector((0, 0, -1))).normalized()
        G.add_mesh_uv(f"scalpss_{j}", G.box_uv(tuple(p), (0.08, 0.08, 0.10)), m("deck_box"), body, smooth=False)
        G.sensor_camera(f"scalpss_{j}", body, tuple(p + look * 0.06), tuple(look), (0, 0, 1),
                        {"focal_mm": 8.0, "aperture_mm": (11.3, 7.1), "fstop": 4.0, "clip_m": (0.05, 300.0),
                         "resolution": (4096, 2160), "source": "SCALPSS (NASA LaRC) - optics estimated"})
    if F.get("lra"):
        x, y = F["lra"]
        z = D["top_array_z"] + 0.01
        G.add_mesh_uv("lra_dome", G.lathe_geo([(0.03, z), (0.025, z + 0.012), (1e-3, z + 0.017)], 16, center=(x, y, 0)), m("lens"), body)
        G.site("lra", body, (x, y, z + 0.017), kind="payload", description="NASA GSFC Laser Retroreflector Array")
