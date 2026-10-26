import math

from mathutils import Vector

import geo as G
import materials as M
import parts as P

D = {
    "ds_bot": 1.481, "ds_top": 3.230, "ds_half": 2.057, "ds_face_half": 0.686,
    "as_bot": 3.332, "as_top": 5.735, "tunnel_top": 6.062, "tunnel_r": 0.406,
    "cabin_half": 1.17, "cabin_chamfer": 0.45, "cabin_bot": 3.40, "cabin_top": 5.70, "cabin_back": 0.0,
    "front_bot_y": 1.64, "front_top_y": 2.19,
    "mid_half": 1.20, "mid_y": (-0.70, 0.05),
    "aft_half": 0.95, "aft_y": (-1.85, -0.70), "aft_z": (4.35, 5.45),
    "aps_tank_r": 0.50, "aps_tank_c": (1.22, -0.35, 4.25),
    "leg_az": [0, 90, 180, 270], "apex_r": 2.72, "apex_z": 3.00, "foot_r": 4.255, "pad_r": 0.47, "pad_h": 0.22,
    "outer_len": 2.00, "secondary_attach": 1.95, "stroke": 0.813, "secondary_z": 1.56,
    "dps_exit_z": 0.215, "dps_exit_r": 0.80, "dps_throat_r": 0.16, "dps_len": 2.413, "gimbal_deg": 6.0,
    "aps_exit_z": 3.40, "aps_exit_r": 0.394, "aps_throat_r": 0.11, "aps_len": 1.194,
    "rcs_r": 2.35, "rcs_z": 4.60,
    "sband_c": (2.15, 2.00, 6.65), "sband_r": 0.33,
    "rr_c": (0.0, 1.50, 6.45), "rr_r": 0.30,
}


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    m = M.get
    body = G.link("body", (0, 0, 0), mass=cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"])
    _descent_stage(body, m)
    _dps(body, m)
    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, m)
    _ascent_stage(body, m)
    _aps(body, m)
    _rcs(body, m, cfg)
    _sband(body, m)
    _rendezvous_radar(body, m)
    _antennas(body, m)

    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("stage_interface", body, (0, 0, D["as_bot"]), kind="interface",
           description="Ascent/descent stage interface (LM station X200); ascent separation plane")
    G.site("docking_port", body, (0, 0, D["tunnel_top"]), (0, 0, 1), kind="interface",
           description="Overhead docking tunnel / drogue interface")
    G.site("forward_hatch", body, (0, D["front_bot_y"] + 0.1, 3.90), (0, 1, 0), kind="interface", description="Forward EVA hatch (0.81 m square)")
    G.site("imu", body, (0, 0.8, 5.2), kind="sensor", description="Inertial measurement unit (navigation base, approximate)")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, P.polar(D["ds_half"], az, D["ds_top"]), kind="handling", description="GSE lift point")
    return body


def _octagon(half, face_half):
    return [(half, -face_half), (half, face_half), (face_half, half), (-face_half, half),
            (-half, face_half), (-half, -face_half), (-face_half, -half), (face_half, -half)]


def _descent_stage(body, m):
    oc = _octagon(D["ds_half"], D["ds_face_half"])
    zb, zt = D["ds_bot"], D["ds_top"]
    G.add_mesh_uv("ds_sides", G.puff(P.loft_geo(oc, zb + 0.06, oc, zt - 0.04, top=False, bottom=False), 0.03, 0.25, seed=1),
                  m("mli_amber"), body, smooth=False)
    G.add_mesh_uv("ds_top_deck", P.loft_geo(oc, zt - 0.04, oc, zt, bottom=False), m("ds_deck"), body, smooth=False)
    inner = _octagon(D["ds_half"] * 0.80, D["ds_face_half"] * 0.80)
    G.add_mesh_uv("ds_base_heat_shield", G.puff(P.loft_geo(inner, zb - 0.05, oc, zb + 0.06, top=False), 0.02, 0.2, seed=2),
                  m("mli_black"), body, smooth=False)
    for k in range(8):
        a, b = Vector((*oc[k], 0)), Vector((*oc[(k + 1) % 8], 0))
        G.add_mesh_uv(f"ds_beam_cap_{k}", G.box_uv(tuple((a + b) / 2 + Vector((0, 0, zt - 0.06))), (0.05, 0.05, 0.05)),
                      m("aluminium"), body, smooth=False)
    for s in (-1, 1):
        for t in (-1, 1):
            G.add_mesh_uv(f"ds_corner_post_{s}{t}", G.box_uv((s * D["ds_half"], t * D["ds_face_half"], (zb + zt) / 2),
                                                             (0.07, 0.07, zt - zb)), m("aluminium"), body, smooth=False)
            G.add_mesh_uv(f"ds_corner_post_t{s}{t}", G.box_uv((t * D["ds_face_half"], s * D["ds_half"], (zb + zt) / 2),
                                                              (0.07, 0.07, zt - zb)), m("aluminium"), body, smooth=False)
    G.add_mesh_uv("mesa", G.box_uv((-1.35, 1.35, 2.55), (0.95, 0.95, 0.9)), m("mli_silver"), body, smooth=False)
    G.add_mesh_uv("porch", G.box_uv((0, D["ds_half"] + 0.30, zt - 0.03), (0.80, 0.60, 0.04)), m("aluminium"), body, smooth=False)
    for s in (-1, 1):
        G.add_mesh_uv(f"porch_rail_{s}", G.tube_uv((s * 0.38, D["ds_half"] + 0.55, zt), (s * 0.38, D["ds_half"] + 0.10, zt + 0.80),
                                                  0.015, 8), m("aluminium"), body)
    G.add_mesh_uv("ds_skirt_lower", G.puff(P.loft_geo(inner, zb - 0.075, inner, zb - 0.02), 0.01, 0.2, seed=3), m("mli_silver"),
                  body, smooth=False)


def _dps(body, m):
    g = D["gimbal_deg"]
    ez, re, rt, L = D["dps_exit_z"], D["dps_exit_r"], D["dps_throat_r"], D["dps_len"]
    pivot = (0, 0, ez + L + 0.05)
    drive = {"kind": "position", "stiffness": 40000.0, "damping": 800.0, "max_force": 8000.0}
    gx = G.link("dps_gimbal_x", pivot, body, mass=10.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                       "drive": drive})
    eng = G.link("dps", pivot, gx, mass=180.0,
                 joint={"type": "revolute", "axis": (0, 1, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                        "drive": drive})
    throat = P.bell("dps", eng, (0, 0, ez), re, rt, L * 0.80, m("nozzle_ext"), m("nozzle_int"), wall=0.012, segments=64,
                    throat_frac=1.0, power=1.7)
    G.add_mesh_uv("dps_chamber", G.lathe_geo([(rt + 0.012, throat.z), (0.24, throat.z + 0.12), (0.26, throat.z + 0.30),
                                               (0.30, pivot[2] - 0.12), (0.12, pivot[2] - 0.05)], 32), m("engine_metal"), eng)
    for ax, (dx, dy) in (("x", (0, 0.55)), ("y", (0.55, 0))):
        G.add_mesh_uv(f"dps_actuator_{ax}", G.tube_uv((dx, dy, pivot[2] + 0.10), (dx * 0.55, dy * 0.55, throat.z + 0.15), 0.03, 12),
                      m("aluminium"), eng)
    G.add_mesh_uv("dps_gimbal_ring", G.tube_uv((0, 0, pivot[2] - 0.06), (0, 0, pivot[2] + 0.06), 0.34, 32), m("aluminium"), gx)
    G.thruster("dps_exit", eng, (0, 0, ez), (0, 0, -1), kind="main", thrust_n=43900.0, min_thrust_n=4700.0, isp_s=311.0,
               exit_radius=re, throat_radius=rt, propellant="Aerozine 50/N2O4",
               notes="TRW LM Descent Propulsion System (J-mission, 10 in nozzle extension): 9,870 lbf full thrust, "
                     "~10-65% throttle, +/-6 deg gimbal (Grumman/NASA News Reference).",
               confidence="official")
    G.site("dps_gimbal_center", body, pivot, kind="reference", description="DPS gimbal pivot")


def _leg(i, az, body, m):
    radial, tang = P.radial_frame(az)
    apex = P.polar(D["apex_r"], az, D["apex_z"])
    foot = P.polar(D["foot_r"], az, 0.0)
    ankle = foot + Vector((0, 0, D["pad_h"] * 0.75))
    u = (ankle - apex).normalized()
    knee = apex + u * D["outer_len"]
    attach = apex + u * D["secondary_attach"]
    fh = D["ds_face_half"] * 0.9
    edge = radial * D["ds_half"]
    for s in (-1, 1):
        for z in (D["ds_top"] - 0.08, D["ds_bot"] + 0.15):
            G.add_mesh_uv(f"leg_{i}_outrigger_{s}_{z:.1f}", G.tube_uv(edge + tang * s * fh + Vector((0, 0, z)), apex, 0.035, 10),
                          m("leg_mli"), body)
    G.add_mesh_uv(f"leg_{i}_apex", G.box_uv(tuple(apex), (0.16, 0.16, 0.16)), m("aluminium"), body, smooth=False)

    gear = {"role": "landing_gear"}
    spring = {"kind": "spring", "stiffness": 9.0e4, "damping": 1.5e4, "max_force": 4.0e5}
    outer = G.link(f"leg_{i}_primary", tuple(apex), body, mass=18.0, joint={"type": "spherical", "cone": 20, **gear})
    G.add_mesh_uv(f"leg_{i}_primary_outer", G.tube_uv(apex, knee, 0.075, 20), m("leg_mli"), outer)
    G.add_mesh_uv(f"leg_{i}_primary_end_cap", G.tube_uv(knee - u * 0.10, knee, 0.085, 20), m("aluminium"), outer)
    G.add_mesh_uv(f"leg_{i}_primary_lug", G.box_uv(tuple(attach), (0.12, 0.12, 0.12)), m("aluminium"), outer, smooth=False)
    stage1 = G.link(f"leg_{i}_primary_stage1", tuple(knee), outer, mass=2.0,
                    joint={"type": "prismatic", "axis": tuple(-u), "limit": (0.0, D["stroke"]), **gear, "drive": spring})
    G.add_mesh_uv(f"leg_{i}_separation_plate", G.tube_uv(knee - u * 0.30, knee - u * 0.28, 0.068, 16), m("aluminium"), stage1)
    inner = G.link(f"leg_{i}_primary_inner", tuple(knee), stage1, mass=14.0,
                   joint={"type": "prismatic", "axis": tuple(-u), "limit": (0.0, 1e-5), **gear, "drive": spring})
    G.add_mesh_uv(f"leg_{i}_primary_inner_rod", G.tube_uv(knee - u * 0.85, ankle - u * 0.06, 0.058, 20), m("polished"), inner)
    G.add_mesh_uv(f"leg_{i}_primary_socket", P.sphere_geo(ankle - u * 0.02, 0.07, 8, 16), m("aluminium"), inner)
    pad = G.link(f"leg_{i}_footpad", tuple(ankle), inner, mass=12.0, joint={"type": "spherical", "cone": 30, **gear})
    P.footpad(f"leg_{i}_footpad_dish", pad, (foot.x, foot.y, foot.z), D["pad_r"], D["pad_h"], m("footpad"))
    G.site(f"leg_{i}_foot_contact", pad, tuple(foot), (0, 0, -1), kind="contact", description="Footpad contact point (touchdown sensing)")
    G.site(f"leg_{i}_touchdown_sensor", inner, tuple(knee), tuple(-u), kind="sensor",
           description="Primary strut stroke: 4,500 lb stage to 12 in, 9,500 lb stage to 32 in (NASA TN D-6850)")

    for k, s in enumerate((-1, 1)):
        n = f"leg_{i}_secondary_{'ab'[k]}"
        root = edge + tang * s * fh + Vector((0, 0, D["secondary_z"]))
        w = (attach - root).normalized()
        L = (attach - root).length
        mid = root + w * (L * 0.55)
        sin = G.link(f"{n}_inner", tuple(root), body, mass=5.0, joint={"type": "spherical", **gear})
        G.add_mesh_uv(f"{n}_inner_tube", G.tube_uv(root, mid + w * 0.30, 0.03, 12), m("polished"), sin)
        G.add_mesh_uv(f"{n}_truss_fitting", G.box_uv(tuple(root), (0.09, 0.09, 0.09)), m("aluminium"), body, smooth=False)
        comp = G.link(f"{n}_compression", tuple(mid), sin, mass=1.5,
                      joint={"type": "prismatic", "axis": tuple(w), "limit": (0.0, 1e-5), **gear, "drive": spring})
        G.add_mesh_uv(f"{n}_bearing", G.tube_uv(mid - w * 0.02, mid + w * 0.02, 0.036, 12), m("aluminium"), comp)
        ten1 = G.link(f"{n}_tension1", tuple(mid), comp, mass=1.5,
                      joint={"type": "prismatic", "axis": tuple(w), "limit": (0.0, 1e-5), **gear, "drive": spring})
        G.add_mesh_uv(f"{n}_tension_rod", G.tube_uv(mid - w * 0.04, mid + w * 0.04, 0.02, 10), m("aluminium"), ten1)
        sout = G.link(f"{n}_outer", tuple(mid), ten1, mass=5.0,
                      joint={"type": "prismatic", "axis": tuple(w), "limit": (0.0, 1e-5), **gear, "drive": spring})
        G.add_mesh_uv(f"{n}_outer_tube", G.tube_uv(mid - w * 0.05, attach - w * 0.06, 0.045, 16), m("leg_mli"), sout)
        G.add_mesh_uv(f"{n}_ball", P.sphere_geo(attach - w * 0.05, 0.05, 8, 12), m("aluminium"), sout)
        G.loop_joint(f"{n}_ball", f"leg_{i}_primary", f"{n}_outer", tuple(attach), tuple(w), jtype="spherical")
    if az == 90:
        _ladder(outer, apex, u, m)


def _ladder(link, apex, u, m):
    top, bottom = apex + u * 0.25, apex + u * (D["outer_len"] + 0.55)
    out = Vector((0, 1, 0)) * 0.16
    for s in (-1, 1):
        off = Vector((s * 0.22, 0, 0))
        G.add_mesh_uv(f"ladder_rail_{s}", G.tube_uv(top + off + out, bottom + off + out, 0.016, 8), m("aluminium"), link)
    for k in range(9):
        p = top + (bottom - top) * ((k + 0.5) / 9) + out
        G.add_mesh_uv(f"ladder_rung_{k}", G.tube_uv(p - Vector((0.22, 0, 0)), p + Vector((0.22, 0, 0)), 0.012, 6), m("aluminium"), link)


def _ascent_stage(body, m):
    h, c = D["cabin_half"], D["cabin_chamfer"]
    zb, zt = D["cabin_bot"], D["cabin_top"]
    outline = [(-h + c, zb), (h - c, zb), (h, zb + c), (h, zt - c), (h - c, zt), (-h + c, zt), (-h, zt - c), (-h, zb + c)]
    fy = lambda z: D["front_bot_y"] + (D["front_top_y"] - D["front_bot_y"]) * (z - zb) / (zt - zb)
    back = [(x, D["cabin_back"], z) for x, z in outline]
    front = [(x, fy(z), z) for x, z in outline]
    G.add_mesh_uv("as_cabin", P.ring_loft_geo([back, front], cap_first=False), m("as_panel"), body, smooth=False)
    for s in (-1, 1):
        tri = [(s * 0.18, 5.48), (s * 0.98, 5.48), (s * 0.98, 4.88)]
        V = [Vector((x, fy(z) + 0.012, z)) for x, z in tri]
        G.add_mesh(f"window_{s}", V, [(0, 1, 2) if s > 0 else (2, 1, 0)], m("window"), body,
                   uvs=[(0, 0), (0.8, 0), (0.8, 0.6)])
        Vf = [Vector((x, fy(z) + 0.008, z)) for x, z in ((s * 0.12, 5.54), (s * 1.04, 5.54), (s * 1.04, 4.80))]
        G.add_mesh(f"window_frame_{s}", Vf, [(0, 1, 2) if s > 0 else (2, 1, 0)], m("as_black"), body,
                   uvs=[(0, 0), (0.9, 0), (0.9, 0.7)])
    hz = 3.90
    hatch = [Vector((x, fy(z) + 0.01, z)) for x, z in ((-0.405, hz - 0.405), (0.405, hz - 0.405), (0.405, hz + 0.405),
                                                       (-0.405, hz + 0.405))]
    G.add_mesh("forward_hatch", hatch, [(3, 2, 1, 0)], m("as_hatch"), body,
               uvs=[(0, 0), (0.81, 0), (0.81, 0.81), (0, 0.81)])
    lift = [(x * (h + 0.012) / h, z + (0.012 if z >= zt - 1e-6 else 0.0)) for x, z in outline[3:7]]
    G.add_mesh_uv("as_upper_black", P.ring_loft_geo([[(x, D["cabin_back"] + 0.01, z) for x, z in lift],
                                                      [(x, fy(z) - 0.25, z) for x, z in lift]],
                                                     cap_first=False, cap_last=False), m("as_black"), body, smooth=False)
    mh = D["mid_half"]
    y0, y1 = D["mid_y"]
    G.add_mesh_uv("as_midsection", G.box_uv((0, (y0 + y1) / 2, (D["as_bot"] + D["as_top"]) / 2),
                                            (2 * mh, y1 - y0, D["as_top"] - D["as_bot"])), m("as_panel"), body, smooth=False)
    G.add_mesh_uv("as_upper_deck", G.box_uv((0, (y0 + y1) / 2, D["as_top"] + 0.015), (2 * mh - 0.1, y1 - y0 - 0.05, 0.02)),
                  m("as_black"), body, smooth=False)
    a0, a1 = D["aft_y"]
    za, zb2 = D["aft_z"]
    G.add_mesh_uv("as_aft_bay", G.box_uv((0, (a0 + a1 + 0.05) / 2, (za + zb2) / 2), (2 * D["aft_half"], a1 + 0.05 - a0, zb2 - za)),
                  m("as_black"), body, smooth=False)
    for s in (-1, 1):
        G.add_mesh_uv(f"as_aft_strut_{s}", G.tube_uv((s * D["aft_half"] * 0.8, a0 + 0.1, za), (s * mh * 0.8, y0, D["as_bot"] + 0.1),
                                                     0.025, 8), m("aluminium"), body)
        x, y, z = D["aps_tank_c"]
        G.add_mesh_uv(f"aps_tank_{'ox' if s > 0 else 'fuel'}", P.sphere_geo((s * x, y, z), D["aps_tank_r"], rings=6, segments=10),
                      m("as_panel"), body, smooth=False)
        G.add_mesh_uv(f"as_radiator_{s}", G.box_uv((s * (D["aft_half"] + 0.016), (a0 + a1) / 2, (za + zb2) / 2),
                                                    (0.02, (a1 - a0) * 0.9, (zb2 - za) * 0.85)), m("radiator"), body, smooth=False)
    G.add_mesh_uv("docking_tunnel", G.tube_uv((0, 0, D["as_top"] - 0.05), (0, 0, D["tunnel_top"] - 0.03), D["tunnel_r"], 32),
                  m("as_panel"), body)
    G.add_mesh_uv("docking_ring", G.tube_uv((0, 0, D["tunnel_top"] - 0.04), (0, 0, D["tunnel_top"]), D["tunnel_r"] + 0.03, 32),
                  m("aluminium"), body)
    G.add_mesh_uv("docking_target_mast", G.tube_uv((0.55, 0.3, D["as_top"] - 0.05), (0.55, 0.3, D["as_top"] + 0.35), 0.02, 8),
                  m("aluminium"), body)
    G.add_mesh_uv("docking_target_plate", G.box_uv((0.55, 0.3, D["as_top"] + 0.38), (0.25, 0.02, 0.25)), m("as_black"), body,
                  smooth=False)


def _aps(body, m):
    ez = D["aps_exit_z"]
    throat = P.bell("aps", body, (0, 0, ez), D["aps_exit_r"], D["aps_throat_r"], D["aps_len"] * 0.7, m("nozzle_ext"),
                    m("nozzle_int"), wall=0.01, segments=40, throat_frac=1.0)
    G.add_mesh_uv("aps_chamber", G.tube_uv(throat, (0, 0, ez + D["aps_len"]), 0.17, 24), m("engine_metal"), body)
    G.thruster("aps_exit", body, (0, 0, ez), (0, 0, -1), kind="ascent", thrust_n=15570.0, isp_s=311.0, exit_radius=D["aps_exit_r"],
               throat_radius=D["aps_throat_r"], propellant="Aerozine 50/N2O4",
               notes="Bell LM Ascent Propulsion System: 3,500 lbf fixed, not throttleable or gimballed (NASA News Reference). "
                     "Exit plane height inferred.",
               confidence="performance official; exit height inferred")


def _rcs(body, m, cfg):
    spec = cfg.RCS["quad"]
    for i, az in enumerate((45, 135, 225, 315)):
        radial, tang = P.radial_frame(az)
        c = P.polar(D["rcs_r"], az, D["rcs_z"])
        sx = 1 if radial.x > 0 else -1
        sy = 1 if radial.y > 0 else -1
        root = P.polar(1.25, az, D["rcs_z"])
        G.add_mesh_uv(f"rcs_{i}_boom", G.tube_uv(root, c - radial * 0.12, 0.05, 12), m("aluminium"), body)
        G.add_mesh_uv(f"rcs_{i}_housing", G.box_uv(tuple(c), (0.28, 0.28, 0.30)), m("as_black"), body, smooth=False)
        for n, d in enumerate(((0, 0, 1), (0, 0, -1), (sx, 0, 0), (0, sy, 0))):
            flow = Vector(d)
            P.thruster_cone(f"rcs_{i}_{n}", body, c + flow * 0.15, flow, spec, m("nozzle_ext"), cluster=f"rcs_quad_{i}")


def _sband(body, m):
    c = Vector(D["sband_c"])
    base = Vector((0.95, 1.30, 5.55))
    hinge = c - Vector((0, 0, 0.42))
    G.add_mesh_uv("sband_boom", G.tube_uv(base, hinge, 0.035, 10), m("aluminium"), body)
    azl = G.link("sband_azimuth", tuple(hinge), body, mass=2.0,
                 joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.radians(174), math.radians(174)), "role": "antenna",
                        "drive": {"kind": "position", "stiffness": 30.0, "damping": 3.0, "max_force": 15.0}})
    G.add_mesh_uv("sband_az_housing", G.tube_uv(hinge, hinge + Vector((0, 0, 0.14)), 0.06, 16), m("as_black"), azl)
    G.add_mesh_uv("sband_yoke", G.tube_uv(hinge + Vector((0, 0, 0.14)), c - Vector((0, 0, 0.06)), 0.025, 8), m("aluminium"), azl)
    el = G.link("sband_elevation", tuple(c - Vector((0, 0, 0.06))), azl, mass=3.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (math.radians(-75), math.radians(75)), "role": "antenna",
                       "drive": {"kind": "position", "stiffness": 30.0, "damping": 3.0, "max_force": 15.0}})
    feed = P.dish("sband", el, c, (0.2, 0.6, 0.77), D["sband_r"], m("dish"), m("as_black"), depth=0.28)
    G.add_mesh_uv("sband_feed", G.tube_uv(c, feed, 0.012, 8), m("aluminium"), el)
    G.site("sband_boresight", el, tuple(feed), tuple(Vector((0.2, 0.6, 0.77)).normalized()), kind="antenna", band="S",
           description="Steerable S-band antenna boresight (+Z), 26 in dish")


def _rendezvous_radar(body, m):
    c = Vector(D["rr_c"])
    base = Vector((c.x, c.y - 0.15, D["cabin_top"]))
    G.add_mesh_uv("rr_pedestal", G.tube_uv(base - Vector((0, 0, 0.05)), base + Vector((0, 0, 0.30)), 0.06, 12), m("as_black"), body)
    pivot = base + Vector((0, 0, 0.36))
    sh = G.link("rr_shaft", tuple(pivot), body, mass=4.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (math.radians(-70), math.radians(70)),
                       "role": "antenna", "drive": {"kind": "position", "stiffness": 40.0, "damping": 4.0, "max_force": 20.0}})
    G.add_mesh_uv("rr_yoke", G.box_uv(tuple(pivot), (0.40, 0.06, 0.06)), m("aluminium"), sh, smooth=False)
    tr = G.link("rr_trunnion", tuple(pivot), sh, mass=6.0,
                joint={"type": "revolute", "axis": (0, 0, 1), "limit": (math.radians(-70), math.radians(70)),
                       "role": "antenna", "drive": {"kind": "position", "stiffness": 40.0, "damping": 4.0, "max_force": 20.0}})
    dc = pivot + Vector((0, 0.12, 0.10))
    bore = Vector((0, 0.45, 1)).normalized()
    feed = P.dish("rr", tr, dc, bore, D["rr_r"], m("dish"), m("as_black"), depth=0.25)
    for k in range(3):
        a = 2 * math.pi * k / 3
        rim = dc + Vector((math.cos(a), math.sin(a) * 0.4, 0)) * D["rr_r"] * 0.8
        G.add_mesh_uv(f"rr_feed_strut_{k}", G.tube_uv(rim, feed, 0.008, 6), m("aluminium"), tr)
    G.site("rr_boresight", tr, tuple(feed), tuple(bore), kind="antenna", band="X",
           description="Rendezvous radar boresight (+Z), shaft/trunnion mount")


def _antennas(body, m):
    for j, (p, d) in enumerate((((-0.9, -0.5, D["as_top"]), (-0.3, -0.3, 1)), ((0.9, -1.6, D["aft_z"][1]), (0.3, -0.4, 1)))):
        p = Vector(p)
        G.add_mesh_uv(f"vhf_{j}", G.tube_uv(p, p + Vector(d).normalized() * 0.65, 0.008, 6), m("aluminium"), body)
        G.site(f"vhf_{j}", body, tuple(p + Vector(d).normalized() * 0.65), tuple(Vector(d).normalized()), kind="antenna", band="VHF",
               description="VHF in-flight antenna")
    for j, x in enumerate((-0.55, 0.55)):
        p = Vector((x, -0.3, D["as_top"]))
        G.add_mesh_uv(f"sband_inflight_{j}", G.tube_uv(p - Vector((0, 0, 0.05)), p + Vector((0, 0, 0.18)), 0.04, 10, r1=0.06), m("as_black"), body)
