import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P

D = {
    "bus_bot": 0.75, "bus_top": 1.84, "core_half": 0.60, "core_chamfer": 0.22,
    "tank_r": 0.29, "tank_len": 1.05, "tank_radius": 0.50, "tank_zc": 1.30, "he_r": 0.225,
    "encl_x": (0.55, 1.00), "encl_y": 0.55, "encl_chamfer": 0.15, "encl_z": (0.80, 1.85),
    "deck_z": 1.10, "deck_w": 1.01, "deck_y": (0.41, 1.00), "deck_t": 0.03,
    "solar": 1.90, "solar_t": 0.04, "top_z": 1.90,
    "cone_bot_r": 0.597, "cone_top_r": 0.725, "cone_bot_z": 0.40, "cone_top_z": 0.75,
    "engine_exit_z": 0.42, "engine_exit_r": 0.065, "engine_throat_r": 0.012, "engine_len": 0.25, "engine_ring_r": 0.33,
    "leg_az": [45, 135, 225, 315], "hard_point_r": 0.95, "hard_point_z": 0.95, "foot_r": 1.75, "pad_r": 0.19, "pad_h": 0.07,
    "knee_frac": 0.62, "stroke": 0.15, "secondary_r": 0.75, "secondary_z": 0.75, "secondary_daz": 28.0,
}


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    m = M.get
    F = cfg.FEATURES
    body = G.link("body", (0, 0, 0), mass=cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"])
    zb, zt = D["bus_bot"], D["bus_top"]

    core = P.chamfer_square(D["core_half"], D["core_chamfer"], 45)
    G.add_mesh_uv("bus_core", G.puff(P.loft_geo(core, zb, core, zt), 0.012, 0.1, seed=2), m("mli_silver"), body, smooth=False)
    G.add_mesh_uv("bus_top_deck", G.prism_geo(8, D["core_half"] + 0.02, zt, zt + 0.02), m("deck_panel"), body, smooth=False)
    for k, az in enumerate((0, 90, 180, 270)):
        c = P.polar(D["tank_radius"], az, D["tank_zc"] - D["tank_len"] / 2)
        prof = G.capsule_profile(D["tank_r"], D["tank_len"] - 2 * D["tank_r"] * 0.7, 0.7)
        G.add_mesh_uv(f"prop_tank_{k}", G.puff(G.lathe_geo(prof, 40, center=tuple(c)), 0.02, 0.1, seed=10 + k),
                      m("mli_silver"), body)
    G.add_mesh_uv("he_tank", P.sphere_geo((0, 0, D["tank_zc"]), D["he_r"]), m("mli_silver"), body)

    for s in (-1, 1):
        _enclosure(s, body, m)
    for s in (-1, 1):
        _payload_deck(s, body, m, cfg)
    x0 = -D["encl_x"][1] + 0.05
    G.add_mesh_uv("small_deck", G.box_uv((x0 - 0.10, 0, D["encl_z"][0] - 0.02), (0.22, 1.09, 0.03)), m("deck_panel"), body, smooth=False)

    _solar(body, m)
    _cone_and_engines(body, m, cfg)
    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, m)
    _acs(body, m, cfg)
    _sensors(body, m, cfg)

    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("deck_center", body, (0, 0, D["top_z"]), kind="reference", description="Top of the solar panel")
    G.site("imu", body, (0.7, 0, 1.3), kind="sensor", description="IMU / navigation reference (estimated location)")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, P.polar(D["hard_point_r"], az, D["hard_point_z"]), kind="handling",
               description="GSE lift point (leg hard point)")
    return body


def _enclosure(s, body, m):
    x0, x1 = D["encl_x"]
    y, c = D["encl_y"], D["encl_chamfer"]
    poly = [(x0, -y), (x1 - c, -y), (x1, -y + c), (x1, y - c), (x1 - c, y), (x0, y)]
    if s < 0:
        poly = [(-px, -py) for px, py in poly]
    z0, z1 = D["encl_z"]
    G.add_mesh_uv(f"enclosure_{'p' if s > 0 else 'n'}", P.loft_geo(poly, z0, poly, z1), m("mli_silver"), body, smooth=False)
    radial = Vector((s, 0, 0))
    P.panel(f"radiator_{'p' if s > 0 else 'n'}", body, (s * (x1 + 0.006), 0, (z0 + z1) / 2), (0, 1, 0), (0, 0, 1),
            2 * (y - c) - 0.04, z1 - z0 - 0.06, 0.01, m("radiator"), m("radiator"), normal=radial)
    for t in (-1, 1):
        n = Vector((s, t, 0)).normalized()
        cc = Vector((s * (x1 - c / 2), t * (y - c / 2), (z0 + z1) / 2)) + n * 0.006
        P.panel(f"radiator_{'p' if s > 0 else 'n'}_{'p' if t > 0 else 'n'}", body, cc, Vector((-t, s, 0)).normalized(),
                (0, 0, 1), c * math.sqrt(2) - 0.03, z1 - z0 - 0.06, 0.01, m("radiator"), m("radiator"), normal=n)


def _payload_deck(s, body, m, cfg):
    y0, y1 = D["deck_y"]
    w, z, t = D["deck_w"], D["deck_z"], D["deck_t"]
    yt = D["tank_radius"] + D["tank_r"] + 0.02
    G.add_mesh_uv(f"deck_{s}_outer", G.box_uv((0, s * (yt + y1) / 2, z), (w, y1 - yt, t)), m("deck_panel"), body, smooth=False)
    wing = (w / 2 - (D["tank_r"] + 0.02))
    for k in (-1, 1):
        G.add_mesh_uv(f"deck_{s}_wing_{k}", G.box_uv((k * (w / 2 - wing / 2), s * (y0 + yt) / 2, z), (wing, yt - y0, t)),
                      m("deck_panel"), body, smooth=False)
        G.add_mesh_uv(f"deck_{s}_strut_{k}", G.tube_uv((k * w / 2 * 0.9, s * y1 * 0.97, z), (k * 0.4, s * 0.55, D["bus_top"] - 0.05),
                                                       0.015, 8), m("aluminium"), body)
    for j, (x, y, sx, sy, sz, mat) in enumerate(cfg.DECK_PAYLOADS):
        G.add_mesh_uv(f"deck_{s}_payload_{j}", G.box_uv((x, s * y, z + t / 2 + sz / 2), (sx, sy, sz)), m(mat), body, smooth=False)
    G.site(f"payload_deck_{'p' if s > 0 else 'n'}y", body, (0, s * (yt + y1) / 2, z + t / 2), (0, 0, 1), kind="payload_interface",
           description="Standard payload deck (Astrobotic PUG v5)")


def _solar(body, m):
    a, t, zt = D["solar"], D["solar_t"], D["top_z"]
    for k, az in enumerate((45, 135, 225, 315)):
        p = P.polar(D["core_half"] * 0.9, az, D["bus_top"] + 0.02)
        G.add_mesh_uv(f"solar_standoff_{k}", G.tube_uv(p, p + Vector((0, 0, zt - t - p.z)), 0.02, 8), m("aluminium"), body)
    P.panel("solar", body, (0, 0, zt - t / 2), (1, 0, 0), (0, 1, 0), a, a, t, m("solar_cells"), m("frame_dark"), normal=(0, 0, 1))
    G.site("solar_normal", body, (0, 0, zt + 0.01), (0, 0, 1), kind="power", area_m2=a * a,
           description="Top-mounted solar panel centre; +Z = cell normal")


def _cone_and_engines(body, m, cfg):
    G.add_mesh_uv("lv_adapter_cone", G.lathe_geo([(D["cone_bot_r"], D["cone_bot_z"]), (D["cone_top_r"], D["cone_top_z"])], 64),
                  m("aluminium"), body)
    G.add_mesh_uv("lv_clamp_ring", G.lathe_geo([(D["cone_bot_r"] + 0.02, D["cone_bot_z"]), (D["cone_bot_r"] + 0.02, D["cone_bot_z"] + 0.05)], 64),
                  m("aluminium"), body)
    G.add_mesh_uv("engine_bay_floor", G.lathe_geo([(1e-3, D["cone_top_z"] - 0.02), (D["cone_top_r"], D["cone_top_z"] - 0.02)][::-1], 48),
                  m("mli_silver"), body)
    s = cfg.MAIN_ENGINE
    spots = [(0.0, 0.0)] + [(D["engine_ring_r"] * math.cos(math.radians(a)), D["engine_ring_r"] * math.sin(math.radians(a)))
                            for a in (0, 90, 180, 270)]
    for k, (x, y) in enumerate(spots):
        ez = D["engine_exit_z"]
        throat = P.bell(f"main_{k}", body, (x, y, ez), D["engine_exit_r"], D["engine_throat_r"], D["engine_len"] * 0.7,
                        m("nozzle_ext"), m("nozzle_int"), wall=0.004, segments=24, throat_frac=1.0)
        G.add_mesh_uv(f"main_{k}_chamber", G.tube_uv(throat, (x, y, D["cone_top_z"] - 0.02), 0.03, 12), m("engine_metal"), body)
        G.thruster(f"main_{k}_exit", body, (x, y, ez), (0, 0, -1), kind="main", thrust_n=s["thrust_n"], isp_s=s["isp_s"],
                   exit_radius=D["engine_exit_r"], throat_radius=D["engine_throat_r"], propellant=s["propellant"],
                   cluster="main", notes=s["notes"], confidence=s["confidence"])


def _leg(i, az, body, m):
    hp = P.polar(D["hard_point_r"], az, D["hard_point_z"])
    foot = P.polar(D["foot_r"], az, D["pad_h"] * 0.1)
    roots = [P.polar(D["secondary_r"], az + k * D["secondary_daz"], D["secondary_z"]) for k in (-1, 1)]
    mats = {"primary": m("leg_kapton"), "collar": m("leg_band"), "secondary": m("leg_kapton"), "piston": m("polished"),
            "footpad": m("footpad")}
    piston, knee, axis = P.leg(i, body, hp, foot, roots, mats, stroke=D["stroke"], knee_frac=D["knee_frac"], r_outer=0.045,
                               r_piston=0.035, r_secondary=0.025, pad_r=D["pad_r"], pad_h=D["pad_h"], piston_mass=2.0,
                               stiffness=1.0e4, damping=1.5e3, max_force=2.5e4)
    G.add_mesh_uv(f"leg_{i}_band", G.tube_uv(knee + axis * 0.15, knee + axis * 0.19, 0.038, 16), m("leg_band"), piston)
    G.add_mesh_uv(f"leg_{i}_hardpoint", G.box_uv(tuple(hp), (0.10, 0.10, 0.10)), m("aluminium"), body, smooth=False)
    G.site(f"leg_{i}_touchdown_sensor", piston, tuple(knee + axis * 0.05), tuple(axis), kind="sensor",
           description="Leg stroke / touchdown switch (estimated)")


def _acs(body, m, cfg):
    spec = cfg.RCS["acs"]
    x1, y = D["encl_x"][1], D["encl_y"]
    for k, (x, yy, z, dirs) in enumerate(((x1, y, 1.80, [(1, 0, 0), (0, 1, 0), (0, -1, 0)]),
                                           (-x1, -y, 1.80, [(1, 0, 0), (0, 1, 0), (0, -1, 0)]),
                                           (0, 0.70, 0.80, [(0, 0, -1), (0, 1, 0), (0, -1, 0)]),
                                           (0, -0.70, 0.80, [(0, 0, -1), (0, 1, 0), (0, -1, 0)]))):
        az = math.degrees(math.atan2(yy, x))
        P.rcs_cluster(f"acs_{k}", body, (x, yy, z), az, dirs, spec, m("aluminium"), m("engine_metal"), pod=(0.08, 0.08, 0.08),
                      offset=0.04)


def _sensors(body, m, cfg):
    F = cfg.FEATURES
    x1 = D["encl_x"][1]
    if F.get("mga"):
        c = Vector((x1 - D["encl_chamfer"] / 2 + 0.03, D["encl_y"] - D["encl_chamfer"] / 2 + 0.03, 1.45))
        n = Vector((1, 1, 0)).normalized()
        P.panel("mga", body, c, Vector((-1, 1, 0)).normalized(), (0, 0, 1), 0.20, 0.30, 0.02, m("radome"), m("deck_box"), normal=n)
        G.site("mga_boresight", body, tuple(c + n * 0.02), tuple(n), kind="antenna", band="X",
               description="Medium-gain antenna boresight (+Z), estimated")
    for j, s in enumerate((1, -1)):
        p = Vector((s * 0.80, 0.25 * s, D["encl_z"][0] - 0.05))
        look = Vector((0.2 * s, 0, -1)).normalized()
        G.add_mesh_uv(f"trn_optics_{j}", G.box_uv(tuple(p), (0.14, 0.14, 0.10)), m("deck_box"), body, smooth=False)
        G.add_mesh_uv(f"trn_optics_{j}_lens", G.tube_uv(p - Vector((0, 0, 0.05)), p - Vector((0, 0, 0.05)) + look * 0.04, 0.03, 12),
                      m("lens"), body)
        G.sensor_camera(f"trn_camera_{j}", body, tuple(p - Vector((0, 0, 0.05)) + look * 0.04), tuple(look), (s, 0, 0),
                        {"focal_mm": 12.0, "aperture_mm": (7.2, 5.4), "fstop": 4.0, "clip_m": (0.1, 5000.0),
                         "resolution": (2048, 2048), "source": "Peregrine TRN / lidar optics - location and optics estimated"})
    for j, (x, y) in enumerate(F.get("star_trackers", [])):
        base = Vector((x, y, D["bus_top"] - 0.15))
        d = Vector((x, y, 0)).normalized() * 0.7 + Vector((0, 0, 0.7))
        d.normalize()
        G.add_mesh_uv(f"star_tracker_{j}_baffle", G.tube_uv(base, base + d * 0.14, 0.03, 16, r1=0.045, caps=False), m("baffle"), body)
        G.site(f"star_tracker_{j}", body, tuple(base + d * 0.14), tuple(d), kind="sensor",
               description="Star tracker boresight (+Z), estimated location")
