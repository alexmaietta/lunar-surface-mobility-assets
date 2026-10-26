import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P

D = {
    "deck_z": 2.00, "deck_half": 0.90, "deck_chamfer": 0.22, "deck_t": 0.035,
    "body_top_half": 0.86, "body_bot_half": 1.04, "body_chamfer": 0.26, "body_bot_z": 0.86,
    "lower_deck_half": 1.10, "lower_deck_chamfer": 0.30, "lower_deck_t": 0.05,
    "leg_az": [45, 135, 225, 315], "hard_point_r": 1.13, "hard_point_z": 1.94, "foot_r": 1.85, "pad_r": 0.26, "pad_h": 0.09,
    "knee_frac": 0.78, "stroke": 0.10, "secondary_r": 1.08, "secondary_z": 0.80, "secondary_daz": 22.0,
    "engine_exit_z": 0.20, "engine_exit_r": 0.20, "engine_throat_r": 0.035, "engine_len": 0.55,
    "shield_top_r": 0.42, "shield_bot_r": 0.25, "shield_top_z": 0.80, "shield_bot_z": 0.52,
    "he_r": 0.20, "he_len": 0.55, "he_z": 0.60, "he_y": 0.42,
    "rcs_r": 1.06, "rcs_z": 0.66,
    "acs_r": 1.30, "acs_z": 0.82,
    "solar_w": 1.62, "solar_h": 1.08,
}


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    m = M.get
    F = cfg.FEATURES
    body = G.link("body", (0, 0, 0), mass=cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"])

    top = P.chamfer_square(D["body_top_half"], D["body_chamfer"] * D["body_top_half"] / D["body_bot_half"])
    bot = P.chamfer_square(D["body_bot_half"], D["body_chamfer"])
    zt = D["deck_z"] - D["deck_t"]
    G.add_mesh_uv("body_mli", G.puff(P.loft_geo(bot, D["body_bot_z"], top, zt, top=False, bottom=False), 0.012, 0.12, seed=5),
                  m("mli_copper"), body, smooth=False)
    deck = P.chamfer_square(D["deck_half"], D["deck_chamfer"])
    G.add_mesh_uv("top_deck", P.loft_geo(deck, zt, deck, D["deck_z"]), m("deck_panel"), body, smooth=False)
    G.add_mesh_uv("top_deck_edge", P.loft_geo(P.chamfer_square(D["deck_half"] + 0.012, D["deck_chamfer"]), zt - 0.02,
                                              P.chamfer_square(D["deck_half"] + 0.012, D["deck_chamfer"]), zt + 0.01,
                                              top=False, bottom=False), m("aluminium"), body, smooth=False)
    ld = P.chamfer_square(D["lower_deck_half"], D["lower_deck_chamfer"])
    G.add_mesh_uv("lower_deck", P.loft_geo(ld, D["body_bot_z"] - D["lower_deck_t"], ld, D["body_bot_z"]), m("mli_silver"),
                  body, smooth=False)
    under = P.chamfer_square(D["lower_deck_half"] * 0.78, D["lower_deck_chamfer"] * 0.8)
    G.add_mesh_uv("under_bay", G.puff(P.loft_geo(under, D["shield_top_z"] - 0.12, ld, D["body_bot_z"] - D["lower_deck_t"],
                                                  top=False), 0.01, 0.1, seed=6), m("mli_copper"), body, smooth=False)

    _engine(body, m)
    for s in (-1, 1):
        c = (0, s * D["he_y"], D["he_z"])
        prof = G.capsule_profile(D["he_r"], D["he_len"] - 2 * D["he_r"], 1.0)
        G.add_mesh_uv(f"helium_tank_{(s + 1) // 2}", G.lathe_geo(prof, 32, (-D["he_len"] / 2, s * D["he_y"], D["he_z"]),
                                                                  [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),
                      m("composite"), body)
        G.add_mesh_uv(f"helium_tank_{(s + 1) // 2}_band", G.tube_uv((-0.03, c[1], c[2]), (0.03, c[1], c[2]), D["he_r"] + 0.01, 24),
                      m("aluminium"), body)

    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, m)
    for i, az in enumerate((0, 90, 180, 270)):
        _rcs_pod(i, az, body, m, cfg)
    for i, az in enumerate(D["leg_az"]):
        _acs_cluster(i, az, body, m, cfg)
    for i, az in enumerate(F.get("solar_az", [])):
        _solar(i, az, body, m)
    _deck(body, m, cfg)

    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("deck_center", body, (0, 0, D["deck_z"]), kind="payload_interface", description="Top deck centre")
    G.site("imu", body, (0, 0, 1.4), kind="sensor", description="IMU / navigation reference (estimated location)")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, P.polar(D["hard_point_r"] - 0.08, az, D["deck_z"]), kind="handling",
               description="GSE lift point (deck corner)")
    return body


def _engine(body, m):
    ez, er, L = D["engine_exit_z"], D["engine_exit_r"], D["engine_len"]
    throat = P.bell("leros", body, (0, 0, ez), er, D["engine_throat_r"], L * 0.75, m("nozzle_ext"), m("nozzle_int"),
                    wall=0.006, throat_frac=1.0, power=1.6)
    G.add_mesh_uv("leros_chamber", G.lathe_geo([(D["engine_throat_r"] + 0.006, throat.z), (0.07, throat.z + 0.06),
                                                 (0.07, throat.z + 0.16), (0.10, throat.z + 0.20)], 24), m("engine_metal"), body)
    G.add_mesh_uv("leros_valve", G.box_uv((0.12, 0, throat.z + 0.16), (0.10, 0.08, 0.08)), m("engine_metal"), body, smooth=False)
    prof = [(D["shield_bot_r"], D["shield_bot_z"]), (D["shield_top_r"], D["shield_top_z"])]
    G.add_mesh_uv("engine_heat_shield", G.puff(G.lathe_geo(P.densify(prof, 6), 36), 0.012, 0.05, seed=9), m("mli_gold"), body)
    G.thruster("leros_exit", body, (0, 0, ez), (0, 0, -1), kind="main", thrust_n=1310.0, isp_s=321.0, exit_radius=er,
               throat_radius=D["engine_throat_r"], propellant="MMH/MON-3",
               notes="Nammo LEROS 4-ET; >1,000 N (Firefly), 1,310 N and 321 s used. Fixed, not gimballed. Exit size from renders.",
               confidence="thrust/isp official; geometry estimated")


def _leg(i, az, body, m):
    hp = P.polar(D["hard_point_r"], az, D["hard_point_z"])
    foot = P.polar(D["foot_r"], az, D["pad_h"] * 0.1)
    roots = [P.polar(D["secondary_r"] / math.cos(math.radians(D["secondary_daz"])) * 0.92, az + s * D["secondary_daz"],
                     D["secondary_z"]) for s in (-1, 1)]
    mats = {"primary": m("leg_mli"), "collar": m("titanium"), "secondary": m("leg_mli"), "piston": m("titanium"),
            "footpad": m("leg_mli")}
    piston, knee, axis = P.leg(i, body, hp, foot, roots, mats, stroke=D["stroke"], knee_frac=D["knee_frac"], r_outer=0.05,
                               r_piston=0.036, r_secondary=0.026, pad_r=D["pad_r"], pad_h=D["pad_h"], piston_mass=2.0,
                               stiffness=8.0e3, damping=1.2e3, max_force=2.0e4)
    G.add_mesh_uv(f"leg_{i}_hardpoint", G.box_uv(tuple(hp), (0.10, 0.10, 0.08)), m("aluminium"), body, smooth=False)
    G.site(f"leg_{i}_touchdown_sensor", piston, tuple(knee + axis * 0.08), tuple(axis), kind="sensor",
           description="Crush-core stroke / touchdown switch (estimated)")


def _rcs_pod(i, az, body, m, cfg):
    radial, tang = P.radial_frame(az)
    c = P.polar(D["rcs_r"], az, D["rcs_z"])
    G.add_mesh_uv(f"rcs_{i}_shroud", G.box_uv(tuple(c), (0.16, 0.30, 0.20)) if abs(radial.x) > 0.5 else
                  G.box_uv(tuple(c), (0.30, 0.16, 0.20)), m("beta_white"), body, smooth=False)
    s = cfg.RCS["spectre"]
    for n, t in enumerate((-1, 1)):
        base = c + tang * t * 0.07 - Vector((0, 0, 0.10))
        flow = (Vector((0, 0, -1)) + tang * t * 0.18 + radial * 0.12).normalized()
        P.thruster_cone(f"rcs_{i}_{n}", body, base, flow, s, m("nozzle_ext"), cluster=f"rcs_{i}")


def _acs_cluster(i, az, body, m, cfg):
    radial, tang = P.radial_frame(az)
    c = P.polar(D["acs_r"], az, D["acs_z"])
    G.add_mesh_uv(f"acs_{i}_bracket", G.tube_uv(P.polar(D["acs_r"] - 0.28, az, D["acs_z"]), c, 0.012, 8), m("aluminium"), body)
    P.rcs_cluster(f"acs_{i}", body, c, az, [(0, 1, 0), (0, -1, 0), (0, 0, 1)], cfg.RCS["cold_gas"], m("aluminium"),
                  m("engine_metal"), pod=(0.06, 0.06, 0.06), offset=0.03)


def _solar(i, az, body, m):
    radial, tang = P.radial_frame(az)
    zb, zt = D["body_bot_z"] + 0.04, D["deck_z"] - D["deck_t"] - 0.03
    rb, rt = D["body_bot_half"], D["body_top_half"]
    pb, pt = radial * rb + Vector((0, 0, zb)), radial * rt + Vector((0, 0, zt))
    up = (pt - pb).normalized()
    n = tang.cross(up).normalized()
    if n.dot(radial) < 0:
        n = -n
    c = (pb + pt) / 2 + n * 0.03
    P.panel(f"solar_{i}", body, c, tang, up, D["solar_w"], min(D["solar_h"], (pt - pb).length - 0.04), 0.02,
            m("solar_cells"), m("panel_frame"), normal=n)
    G.site(f"solar_{i}_normal", body, tuple(c + n * 0.02), tuple(n), kind="power", area_m2=D["solar_w"] * D["solar_h"],
           description="Body-mounted solar panel centre; +Z = cell normal")


def _deck(body, m, cfg):
    z = D["deck_z"]
    F = cfg.FEATURES
    for j, (x, y, sx, sy, sz, mat) in enumerate(cfg.DECK_BOXES):
        G.add_mesh_uv(f"deck_box_{j}", G.box_uv((x, y, z + sz / 2), (sx, sy, sz)), m(mat), body, smooth=False)
    if F.get("lexi"):
        x, y = F["lexi"]
        G.add_mesh_uv("lexi_base", G.box_uv((x, y, z + 0.10), (0.28, 0.28, 0.20)), m("mli_gold"), body, smooth=False)
        a = math.radians(50)
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((x, y, z + 0.20)) + d * 0.32
        G.add_mesh_uv("lexi_telescope", G.tube_uv(tuple(c - d * 0.32), tuple(c + d * 0.32), 0.13, 4), m("mli_gold"), body, smooth=False)
        G.site("lexi_boresight", body, tuple(c + d * 0.32), tuple(d), kind="payload",
               description="LEXI soft X-ray imager boresight (stowed pose estimated)")
    if F.get("xband"):
        _xband(body, m, F["xband"])
    for j, (x, y) in enumerate(F.get("star_trackers", [])):
        d = Vector((x, y, 0)).normalized() * 0.5 + Vector((0, 0, 0.85))
        d.normalize()
        base = Vector((x, y, z))
        G.add_mesh_uv(f"star_tracker_{j}_body", G.box_uv(base + Vector((0, 0, 0.05)), (0.10, 0.10, 0.10)), m("deck_box"),
                      body, smooth=False)
        G.add_mesh_uv(f"star_tracker_{j}_baffle", G.tube_uv(base + Vector((0, 0, 0.10)), base + Vector((0, 0, 0.10)) + d * 0.15,
                                                           0.035, 16, r1=0.05, caps=False), m("baffle"), body)
        G.site(f"star_tracker_{j}", body, tuple(base + Vector((0, 0, 0.10)) + d * 0.15), tuple(d), kind="sensor",
               description="Star tracker boresight (+Z), estimated location")
    for j, az in enumerate((0, 90, 180, 270)[: F.get("omni_antennas", 0)]):
        p = P.polar(D["deck_half"] - 0.08, az + 20, z)
        G.add_mesh_uv(f"omni_antenna_{j}_mast", G.tube_uv(p, p + Vector((0, 0, 0.10)), 0.012, 8), m("aluminium"), body)
        G.add_mesh_uv(f"omni_antenna_{j}_radome", G.lathe_geo([(1e-3, 0.10), (0.04, 0.11), (0.045, 0.14), (1e-3, 0.16)], 20,
                                                             center=p), m("radome"), body)
        G.site(f"omni_antenna_{j}", body, tuple(p + Vector((0, 0, 0.14))), kind="antenna", band="S",
               description="S-band omni antenna (estimated location)")
    if F.get("nglr"):
        x, y = F["nglr"]
        G.add_mesh_uv("nglr_base", G.tube_uv((x, y, z), (x, y, z + 0.06), 0.07, 20), m("aluminium"), body)
        G.add_mesh_uv("nglr_reflector", G.tube_uv((x, y, z + 0.06), (x, y, z + 0.13), 0.055, 20, r1=0.05), m("lens"), body)
        G.site("nglr", body, (x, y, z + 0.13), kind="payload", description="Next Generation Lunar Retroreflector (NGLR-1)")
    for j, (x, y, az) in enumerate(F.get("cameras", [])):
        p = Vector((x, y, z - 0.05))
        look = (P.polar(1, az, 0) * 0.6 + Vector((0, 0, -1))).normalized()
        G.add_mesh_uv(f"camera_{j}", G.box_uv(tuple(p), (0.07, 0.07, 0.07)), m("deck_box"), body, smooth=False)
        G.add_mesh_uv(f"camera_{j}_lens", G.tube_uv(p, p + look * 0.06, 0.02, 12), m("lens"), body)
        G.sensor_camera(f"camera_{j}", body, tuple(p + look * 0.06), tuple(look), (0, 0, 1),
                        {"focal_mm": 6.0, "aperture_mm": (7.2, 5.4), "fstop": 4.0, "clip_m": (0.05, 300.0),
                         "resolution": (2048, 1536), "source": "Blue Ghost surface / RAC cameras - optics estimated"})


def _xband(body, m, spec):
    z = D["deck_z"]
    x, y = spec["pos"]
    G.add_mesh_uv("xband_mast", G.tube_uv((x, y, z), (x, y, z + 0.18), 0.03, 12), m("aluminium"), body)
    azl = G.link("xband_azimuth", (x, y, z + 0.18), body, mass=1.5,
                 joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "antenna",
                        "drive": {"kind": "position", "stiffness": 20.0, "damping": 2.0, "max_force": 10.0}})
    G.add_mesh_uv("xband_az_housing", G.tube_uv((x, y, z + 0.18), (x, y, z + 0.26), 0.05, 16), m("deck_box"), azl)
    pivot = (x, y, z + 0.32)
    el = G.link("xband_elevation", pivot, azl, mass=2.0,
                joint={"type": "revolute", "axis": (0, 1, 0), "limit": (math.radians(-10), math.radians(100)), "role": "antenna",
                       "drive": {"kind": "position", "stiffness": 20.0, "damping": 2.0, "max_force": 10.0}})
    G.add_mesh_uv("xband_yoke", G.box_uv((x, y, z + 0.29), (0.04, 0.22, 0.04)), m("aluminium"), azl, smooth=False)
    w, h = spec.get("size", (0.50, 0.45))
    c = Vector(pivot) + Vector((0.04, 0, 0))
    P.panel("xband_panel", el, c, (0, 1, 0), (0, 0, 1), w, h, 0.03, m("radome"), m("deck_box"), normal=(1, 0, 0))
    G.site("xband_boresight", el, tuple(c + Vector((0.02, 0, 0))), (1, 0, 0), kind="antenna", band="X",
           description="X-band flat-panel antenna boresight (+Z); 2-axis gimbal (geometry estimated)")
