import math

import rover_kit as K

ASSET_ID = "pr_concept"
ASSET_PATH = "concepts/pressurized/rover"
FAMILY = "rover"
TITLE = "Generic Pressurised Rover (concept)"
DOC = ("Generic modern two-crew pressurised rover concept (about 9 t, 7.0 m long, 3.3 m wide over the tyres, 3.3 m to the roof and 4.1 m to the dish): a smooth white composite "
       "pressure cabin with a raked nose and a wrap-around amber window band, carried on a grey chassis keel with "
       "dust skirts over six 1.1 m airless wheels. Every wheel sits on active double-wishbone suspension and steers "
       "(+/-45 deg, crab and turn-in-place). Two suitports on the aft bulkhead with top-hinged hatch joints (or, in "
       "the Ports=airlock variant, a walk-in airlock door), a grated aft porch with handrails, an IDSS-style docking "
       "ring with a hinged hatch on the left flank, flank radiators, two roof solar wings that hinge up from stowed "
       "flat to vertical, a gimballed 0.75 m dish, a pan-tilt navigation mast, eight brow and bumper lamps plus work "
       "and porch lights, and a 2.6 m five-joint robotic arm on the aft bulkhead.")

TEXTURE_SETS, MATERIALS = K.materials(
    overrides={
        "glass_amber": {"color": (0.40, 0.26, 0.08), "roughness": 0.05, "metallic": 0.6},
        "skirt": {"set": "skirt", "normal": 0.6},
        "keel": {"set": "keel", "normal": 0.6},
        "orange": {"color": (0.85, 0.35, 0.05), "roughness": 0.4},
        "lamp_step": {"color": (1.0, 0.85, 0.6), "roughness": 0.2, "emission": (1.0, 0.82, 0.55, 8.0)},
    },
    textures={
        "skirt": ("panel", dict(colour=(0.20, 0.205, 0.21), tile_m=0.8, rough0=0.5, metallic=0.4, fastener_pitch=0.08)),
        "keel": ("panel", dict(colour=(0.36, 0.37, 0.38), tile_m=0.8, rough0=0.5, metallic=0.3, fastener_pitch=0.08)),
        "white_panel": ("panel", dict(colour=(0.88, 0.88, 0.87), tile_m=1.2, rough0=0.35, fastener_pitch=0.10)),
    })

R_W, W_W = 0.55, 0.40
AXLES = (2.20, 0.0, -2.20)
TRACK = 2.90
STEER = (math.radians(-45), math.radians(45))
CAB_Z0, CAB_Z1, CAB_HW = 1.40, 3.30, 1.25
XN, XA = 3.30, -2.70
ZC, HH = (CAB_Z0 + CAB_Z1) / 2, (CAB_Z1 - CAB_Z0) / 2
PORCH_X, PORCH_Z = -3.55, 1.05
SP_Y, SP_Z = 0.56, 2.30
DOCK = (0.30, CAB_HW, 2.30)
WING = dict(x=(-1.95, 1.45), y=1.02, w=0.92, z=CAB_Z1 + 0.08)
ROOF = CAB_Z1


def _cabin():
    return [
        {"kind": "loft", "name": "cabin", "mat": "white_panel", "n": 5,
         "stations": [(XA, CAB_HW - 0.05, ZC, HH - 0.05, 0.40), (XA + 0.15, CAB_HW, ZC, HH, 0.40), (2.30, CAB_HW, ZC, HH, 0.40),
                      (2.85, CAB_HW - 0.03, ZC - 0.12, HH - 0.12, 0.38), (XN, CAB_HW - 0.10, ZC - 0.25, HH - 0.25, 0.32)]},
        {"kind": "loft", "name": "keel", "mat": "grey_panel", "n": 3, "smooth": False,
         "stations": [(-2.95, 0.70, 1.02, 0.30, 0.10), (2.95, 0.70, 1.02, 0.30, 0.10), (3.30, 0.60, 1.10, 0.22, 0.08)]},
        {"kind": "box", "name": "belly_pan", "c": (0.0, 0, 0.71), "size": (5.60, 1.20, 0.02), "mat": "keel"},
        {"kind": "box", "name": "cabin_saddle", "c": (0.0, 0, 1.35), "size": (5.40, 1.90, 0.10), "mat": "keel"},
        {"kind": "box", "name": "front_bumper", "c": (3.40, 0, 1.05), "size": (0.16, 1.80, 0.26), "mat": "skirt"},
        {"kind": "box", "name": "front_bumper_plate", "c": (3.485, 0, 1.05), "size": (0.01, 1.10, 0.10), "mat": "anodised_dark"},
        {"kind": "tube", "name": "tow_stub_l", "p0": (3.30, 0.75, 0.80), "p1": (3.55, 0.75, 0.80), "r": 0.05, "mat": "titanium"},
        {"kind": "tube", "name": "tow_stub_r", "p0": (3.30, -0.75, 0.80), "p1": (3.55, -0.75, 0.80), "r": 0.05, "mat": "titanium"},
        {"kind": "box", "name": "brow", "c": (XN - 0.02, 0, 2.645), "size": (0.10, 2.10, 0.20), "mat": "skirt"},
        {"kind": "box", "name": "chin", "c": (XN - 0.02, 0, 1.58), "size": (0.10, 2.10, 0.16), "mat": "skirt"},
        {"kind": "rail", "name": "roof_handrail_l", "r": 0.018, "mat": "yellow",
         "points": [(-2.40, 0.55, ROOF - 0.02), (-2.40, 0.55, ROOF + 0.06), (2.30, 0.55, ROOF + 0.06), (2.30, 0.55, ROOF - 0.02)]},
        {"kind": "rail", "name": "roof_handrail_r", "r": 0.018, "mat": "yellow",
         "points": [(-2.40, -0.55, ROOF - 0.02), (-2.40, -0.55, ROOF + 0.06), (2.30, -0.55, ROOF + 0.06), (2.30, -0.55, ROOF - 0.02)]},
        {"kind": "box", "name": "star_tracker", "c": (1.95, -0.25, ROOF + 0.07), "size": (0.16, 0.16, 0.14), "mat": "anodised_dark"},
        {"kind": "tube", "name": "whip_l", "p0": (-2.35, 0.95, ROOF - 0.15), "p1": (-2.35, 0.95, ROOF + 0.85), "r": 0.015, "mat": "anodised_dark"},
        {"kind": "tube", "name": "whip_r", "p0": (-2.35, -0.95, ROOF - 0.15), "p1": (-2.35, -0.95, ROOF + 0.85), "r": 0.015, "mat": "anodised_dark"},
    ]


def _windows():
    z0, z1 = 1.74, 2.48
    zc, h = (z0 + z1) / 2, z1 - z0
    out = [
        {"kind": "panel", "name": "window_band", "c": (XN + 0.012, 0, zc), "u": (0, 1, 0), "v": (0, 0, 1), "w": 2.06, "h": h, "t": 0.02,
         "normal": (1, 0, 0), "mat": "glass_amber", "back": "anodised_dark"},
        {"kind": "box", "name": "window_mullion", "c": (XN + 0.03, 0, zc), "size": (0.03, 0.07, h + 0.04), "mat": "skirt"},
        {"kind": "box", "name": "window_frame_top", "c": (XN + 0.03, 0, z1 + 0.03), "size": (0.03, 2.20, 0.06), "mat": "skirt"},
        {"kind": "box", "name": "window_frame_sill", "c": (XN + 0.03, 0, z0 - 0.03), "size": (0.03, 2.20, 0.06), "mat": "skirt"},
    ]
    dx, dy = 0.45, -0.07
    L = math.hypot(dx, dy)
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        out.append({"kind": "panel", "name": f"window_wrap_{sd}", "c": (3.08, s * 1.198, zc), "u": (dx / L, s * dy / L, 0), "v": (0, 0, 1),
                    "w": 0.38, "h": h - 0.04, "t": 0.02, "normal": (-dy / L, s * dx / L, 0), "mat": "glass_amber", "back": "anodised_dark"})
        out.append({"kind": "panel", "name": f"side_port_{sd}", "c": (2.35, s * (CAB_HW + 0.012), 2.30), "u": (1, 0, 0), "v": (0, 0, 1), "w": 0.50,
                    "h": 0.42, "t": 0.02, "normal": (0, s, 0), "mat": "glass_amber", "back": "anodised_dark"})
        out.append({"kind": "rail", "name": f"side_port_frame_{sd}", "r": 0.025, "mat": "skirt", "closed": True,
                    "points": [(2.35 + dx_, s * (CAB_HW + 0.02), 2.30 + dz_) for dx_, dz_ in ((0.27, -0.23), (0.27, 0.23), (-0.27, 0.23), (-0.27, -0.23))]})
    return out


def _flanks():
    out = []
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        y = s * (CAB_HW + 0.01)
        spans = [(-2.35, -0.55), (1.15, 2.05)] if s > 0 else [(-2.35, 2.05)]
        for k, (x0, x1) in enumerate(spans):
            out.append({"kind": "panel", "name": f"radiator_{sd}_{k}", "c": ((x0 + x1) / 2, y, 2.98), "u": (1, 0, 0), "v": (0, 0, 1), "w": x1 - x0,
                        "h": 0.42, "t": 0.015, "normal": (0, s, 0), "mat": "radiator", "back": "white_panel"})
        out.append({"kind": "beam", "name": f"mmod_belt_{sd}", "p0": (-2.55, s * (CAB_HW + 0.01), 1.62), "p1": (2.80, s * (CAB_HW + 0.01), 1.62),
                    "w": 0.03, "h": 0.30, "mat": "anodised_grey"})
        for a, x in zip(("f", "m", "r"), AXLES):
            out.append({"kind": "extrude", "name": f"skirt_{sd}_{a}", "y": tuple(sorted((s * 1.72, s * 1.76))), "mat": "skirt",
                        "profile": [(x + 0.75, 1.02), (x + 0.75, 1.20), (x + 0.45, 1.36), (x - 0.45, 1.36), (x - 0.75, 1.20), (x - 0.75, 1.02),
                                    (x - 0.68, 1.02), (x - 0.62, 1.16), (x - 0.38, 1.29), (x + 0.38, 1.29), (x + 0.62, 1.16), (x + 0.68, 1.02)]})
            out.append({"kind": "box", "name": f"skirt_top_{sd}_{a}", "c": (x, s * 1.50, 1.345), "size": (0.90, 0.50, 0.03), "mat": "skirt"})
        for k, (x0, x1) in enumerate(((-2.95, -2.95), (-0.80, -1.40), (1.40, 0.80), (2.95, 3.00))):
            if abs(x0 - x1) > 0.05:
                out.append({"kind": "box", "name": f"sponson_{sd}_{k}", "c": ((x0 + x1) / 2, s * 1.42, 1.25), "size": (abs(x1 - x0), 0.58, 0.22),
                            "mat": "keel"})
        out.append({"kind": "box", "name": f"stowage_{sd}", "c": (-2.25, s * 1.30, 1.28), "size": (0.55, 0.40, 0.30), "mat": "skirt"})
    return out


def _dock():
    x, y, z = DOCK
    hinge = (x + 0.52, y + 0.10, z)
    out = [
        {"kind": "ring", "name": "dock_collar", "c": (x, y - 0.02, z), "n": (0, 1, 0), "r": 0.42, "w": 0.24, "t": 0.08, "mat": "aluminium", "sides": 48},
        {"kind": "ring", "name": "dock_seal", "c": (x, y + 0.06, z), "n": (0, 1, 0), "r": 0.44, "w": 0.06, "t": 0.015, "mat": "anodised_dark", "sides": 48},
        {"kind": "disc", "name": "dock_tunnel", "c": (x, y - 0.02, z), "n": (0, 1, 0), "r": 0.42, "t": 0.01, "mat": "anodised_dark", "sides": 48},
        {"kind": "tube", "name": "dock_hinge_pin", "p0": (hinge[0], hinge[1], z - 0.30), "p1": (hinge[0], hinge[1], z + 0.30), "r": 0.025,
         "mat": "titanium"},
    ]
    for k in range(3):
        a = math.radians(90 + 120 * k)
        out.append({"kind": "obox", "name": f"dock_guide_{k}", "c": (x + 0.60 * math.cos(a), y + 0.12, z + 0.60 * math.sin(a)),
                    "ax": (math.cos(a), 0, math.sin(a)), "ay": (0, 1, 0), "size": (0.10, 0.18, 0.16), "mat": "aluminium"})
    d = "dock_hatch"
    out += [
        {"kind": "disc", "name": "dock_hatch_plate", "link": d, "c": (x, y + 0.07, z), "n": (0, 1, 0), "r": 0.43, "t": 0.05, "mat": "white_panel",
         "sides": 48},
        {"kind": "ring", "name": "dock_hatch_rim", "link": d, "c": (x, y + 0.12, z), "n": (0, 1, 0), "r": 0.30, "w": 0.04, "t": 0.02, "mat": "orange"},
        {"kind": "disc", "name": "dock_hatch_window", "link": d, "c": (x, y + 0.12, z + 0.12), "n": (0, 1, 0), "r": 0.07, "t": 0.012, "mat": "glass"},
        {"kind": "box", "name": "dock_hatch_arm", "link": d, "c": (x + 0.40, y + 0.12, z), "size": (0.26, 0.04, 0.10), "mat": "titanium"},
        {"kind": "tube", "name": "dock_hatch_handle", "link": d, "p0": (x - 0.18, y + 0.15, z - 0.12), "p1": (x - 0.18, y + 0.15, z + 0.12),
         "r": 0.015, "mat": "yellow"},
    ]
    return out, hinge


DOCK_PARTS, DOCK_HINGE = _dock()


def _suitports():
    x = XA
    out = [
        {"kind": "box", "name": "aft_bulkhead", "c": (x - 0.04, 0, ZC - 0.10), "size": (0.08, 2.10, 1.50), "mat": "grey_panel"},
    ]
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        y = s * SP_Y
        ring = [(x - 0.09, y + 0.30 * math.sin(t), SP_Z + (0.45 if math.cos(t) > 0 else 0.45) * math.cos(t) - 0.0)
                for t in [2 * math.pi * k / 24 for k in range(24)]]
        out += [
            {"kind": "rail", "name": f"suitport_ring_{sd}", "r": 0.035, "mat": "aluminium", "closed": True, "points": ring, "variant": "Ports:suitports"},
            {"kind": "rail", "name": f"suitport_seal_{sd}", "r": 0.012, "mat": "orange", "closed": True,
             "points": [(px - 0.035, y + (py - y) * 0.92, SP_Z + (pz - SP_Z) * 0.92) for px, py, pz in ring], "variant": "Ports:suitports"},
            {"kind": "box", "name": f"suitport_hinge_block_{sd}", "c": (x - 0.10, y, SP_Z + 0.52), "size": (0.10, 0.34, 0.07), "mat": "titanium",
             "variant": "Ports:suitports"},
            {"kind": "tube", "name": f"suitport_grab_{sd}", "p0": (x - 0.14, y + s * 0.42, SP_Z - 0.35), "p1": (x - 0.14, y + s * 0.42, SP_Z + 0.35),
             "r": 0.018, "mat": "yellow"},
        ]
        h = f"suitport_hatch_{sd}"
        hx = x - 0.13
        out += [
            {"kind": "obox", "name": f"{h}_plate", "link": h, "c": (hx, y, SP_Z), "ax": (0, 1, 0), "ay": (0, 0, 1), "size": (0.56, 0.86, 0.05),
             "mat": "white_panel", "variant": "Ports:suitports"},
            {"kind": "box", "name": f"{h}_rib_h", "link": h, "c": (hx - 0.04, y, SP_Z), "size": (0.03, 0.46, 0.05), "mat": "grey_panel",
             "variant": "Ports:suitports"},
            {"kind": "box", "name": f"{h}_rib_v", "link": h, "c": (hx - 0.04, y, SP_Z), "size": (0.03, 0.05, 0.76), "mat": "grey_panel",
             "variant": "Ports:suitports"},
            {"kind": "box", "name": f"{h}_leaf", "link": h, "c": (hx, y, SP_Z + 0.46), "size": (0.06, 0.28, 0.08), "mat": "titanium",
             "variant": "Ports:suitports"},
            {"kind": "tube", "name": f"{h}_handle", "link": h, "p0": (hx - 0.05, y - 0.12, SP_Z - 0.32), "p1": (hx - 0.05, y + 0.12, SP_Z - 0.32),
             "r": 0.015, "mat": "orange", "variant": "Ports:suitports"},
        ]
    a = "airlock_door"
    out += [
        {"kind": "box", "name": "airlock_vestibule", "c": (x - 0.13, 0, 2.12), "size": (0.26, 1.40, 1.90), "mat": "grey_panel",
         "variant": "Ports:airlock"},
        {"kind": "rail", "name": "airlock_seal", "r": 0.014, "mat": "orange", "closed": True, "variant": "Ports:airlock",
         "points": [(x - 0.265, y, z) for y, z in ((0.52, 1.36), (0.52, 2.86), (-0.52, 2.86), (-0.52, 1.36))]},
        {"kind": "box", "name": "airlock_door_panel", "link": a, "c": (x - 0.30, 0, 2.11), "size": (0.06, 1.00, 1.46), "mat": "white_panel",
         "variant": "Ports:airlock"},
        {"kind": "box", "name": "airlock_door_rib", "link": a, "c": (x - 0.34, 0, 2.11), "size": (0.03, 0.80, 0.06), "mat": "grey_panel",
         "variant": "Ports:airlock"},
        {"kind": "disc", "name": "airlock_door_window", "link": a, "c": (x - 0.335, 0, 2.55), "n": (-1, 0, 0), "r": 0.10, "t": 0.01, "mat": "glass",
         "variant": "Ports:airlock"},
        {"kind": "tube", "name": "airlock_door_handle", "link": a, "p0": (x - 0.36, 0.35, 1.95), "p1": (x - 0.36, 0.35, 2.25), "r": 0.016,
         "mat": "orange", "variant": "Ports:airlock"},
    ]
    return out


def _porch():
    x0, x1 = XA - 0.05, PORCH_X
    out = [
        {"kind": "box", "name": "porch_deck", "c": ((x0 + x1) / 2, 0, PORCH_Z - 0.025), "size": (x0 - x1, 2.00, 0.05), "mat": "grating"},
        {"kind": "box", "name": "porch_edge", "c": (x1 + 0.03, 0, PORCH_Z - 0.07), "size": (0.06, 2.00, 0.10), "mat": "skirt"},
        {"kind": "box", "name": "porch_led", "c": (x1 - 0.002, 0, PORCH_Z - 0.06), "size": (0.008, 1.80, 0.015), "mat": "lamp_step"},
        {"kind": "box", "name": "rear_bumper", "c": (-3.10, 0, 0.82), "size": (0.20, 1.60, 0.22), "mat": "skirt"},
        {"kind": "box", "name": "tow_hitch", "c": (-3.27, 0, 0.78), "size": (0.14, 0.14, 0.10), "mat": "titanium"},
    ]
    for s in (-1, 1):
        out += [
            {"kind": "beam", "name": f"porch_strut_{s + 1}", "p0": (XA, s * 0.80, 0.95), "p1": (x1 + 0.05, s * 0.90, PORCH_Z - 0.08), "w": 0.06,
             "h": 0.06, "mat": "skirt"},
            {"kind": "rail", "name": f"porch_rail_{s + 1}", "r": 0.02, "mat": "aluminium",
             "points": [(x0 - 0.02, s * 1.0, PORCH_Z), (x0 - 0.02, s * 1.0, PORCH_Z + 1.0), (x1 + 0.04, s * 1.0, PORCH_Z + 1.0),
                        (x1 + 0.04, s * 1.0, PORCH_Z + 0.55)]},
            {"kind": "tube", "name": f"porch_midrail_{s + 1}", "p0": (x0 - 0.02, s * 1.0, PORCH_Z + 0.5), "p1": (x1 + 0.04, s * 1.0, PORCH_Z + 0.5),
             "r": 0.015, "mat": "aluminium"},
        ]
    for k, z in enumerate((0.72, 0.40)):
        xs = x1 - 0.10 - 0.22 * k
        out.append({"kind": "box", "name": f"porch_step_{k}", "c": (xs, 0, z), "size": (0.26, 0.80, 0.035), "mat": "grating"})
        for s in (-1, 1):
            out.append({"kind": "beam", "name": f"porch_step_{k}_hanger_{s + 1}", "p0": (xs + 0.10, s * 0.42, z), "p1": (x1 + 0.05, s * 0.42, PORCH_Z - 0.06),
                        "w": 0.03, "h": 0.03, "mat": "skirt"})
    return out


def _wings():
    out, links = [], []
    x0, x1 = WING["x"]
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        n = f"solar_wing_{sd}"
        yh = s * WING["y"]
        yc = s * (WING["y"] - WING["w"] / 2)
        links.append({"name": n, "pos": ((x0 + x1) / 2, yh, WING["z"]), "axis": (-s, 0, 0), "limit": (0.0, math.radians(95)), "role": "solar",
                      "mass": 45.0, "drive": {"kind": "position", "stiffness": 2.0e4, "damping": 2.0e3, "max_force": 2.0e3}})
        out += [
            {"kind": "panel", "name": f"{n}_cells", "link": n, "c": ((x0 + x1) / 2, yc, WING["z"] + 0.02), "u": (1, 0, 0), "v": (0, 1, 0),
             "w": x1 - x0, "h": WING["w"], "t": 0.02, "normal": (0, 0, 1), "mat": "solar_cells", "back": "beta_white"},
            {"kind": "box", "name": f"{n}_frame_root", "link": n, "c": ((x0 + x1) / 2, yh - s * 0.02, WING["z"] + 0.01), "size": (x1 - x0, 0.04, 0.05),
             "mat": "aluminium"},
            {"kind": "box", "name": f"{n}_frame_tip", "link": n, "c": ((x0 + x1) / 2, yh - s * (WING["w"] - 0.02), WING["z"] + 0.01),
             "size": (x1 - x0, 0.04, 0.05), "mat": "aluminium"},
        ]
        for k, x in enumerate((x0 + 0.25, (x0 + x1) / 2, x1 - 0.25)):
            out.append({"kind": "tube", "name": f"{n}_hinge_{k}", "p0": (x - 0.10, yh, WING["z"]), "p1": (x + 0.10, yh, WING["z"]), "r": 0.03,
                        "mat": "titanium"})
            out.append({"kind": "box", "name": f"{n}_hinge_post_{k}", "c": (x, yh, (WING["z"] + ROOF) / 2 - 0.05), "size": (0.10, 0.06,
                        WING["z"] - ROOF + 0.10), "mat": "anodised_grey"})
    return out, links


WING_PARTS, WING_LINKS = _wings()

LINKS_ = [
    *WING_LINKS,
    {"name": "dock_hatch", "pos": DOCK_HINGE, "axis": (0, 0, -1), "limit": (0.0, math.radians(110)), "role": "hatch", "mass": 40.0,
     "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 600.0}},
    *[{"name": f"suitport_hatch_{sd}", "pos": (XA - 0.13, s * SP_Y, SP_Z + 0.46), "axis": (0, 1, 0), "limit": (0.0, math.radians(100)),
       "role": "hatch", "mass": 18.0, "drive": {"kind": "position", "stiffness": 1500.0, "damping": 150.0, "max_force": 300.0}}
      for sd, s in (("l", 1), ("r", -1))],
    {"name": "airlock_door", "pos": (XA - 0.30, -0.52, 2.11), "axis": (0, 0, 1), "limit": (0.0, math.radians(105)), "role": "hatch", "mass": 50.0,
     "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 600.0}},
]

ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "spring", "grousers": 26, "spokes": 14, "spoke_curve": 0.45, "hub_frac": 0.32, "mass": 70.0,
              "rim_mat": "anodised_grey", "hub_mat": "anodised_dark", "segments": 56},
    "wheels": [{"name": f"{a}{sd}", "x": x, "y": s * TRACK / 2, "steer": STEER}
               for a, x in zip(("f", "m", "r"), AXLES) for sd, s in (("l", 1), ("r", -1))],
    "suspension": {"type": "double_wishbone", "active": True, "arm": 0.55, "kingpin_off": 0.36, "lower_dz": -0.10, "upper_dz": 0.24,
                   "travel": (0.20, 0.18), "static_rad": 0.07, "spread": 0.42, "tube_r": 0.032, "arm_mat": "anodised_grey",
                   "knuckle_mat": "anodised_grey", "spring_mat": "titanium", "strut_up": 0.05},
    "links": LINKS_,
    "parts": [*_cabin(), *_windows(), *_flanks(), *DOCK_PARTS, *_suitports(), *_porch(), *WING_PARTS],
    "masts": [{"name": "nav_mast", "base": (2.45, 0.0, ROOF - 0.08), "h": 0.55, "r": 0.035, "head": (0.12, 0.40, 0.10), "cams": (-0.15, 0.15),
               "lamp": True}],
    "hga": {"base": (-2.20, 0.0, ROOF - 0.10), "h": 0.55, "r": 0.375, "boresight": (-0.4, 0, 1), "band": "Ka", "front": "radome",
            "back": "white_panel"},
    "arm": {"base": (XA - 0.10, -1.02, 1.60), "up": (-1, 0, 0), "stow_dir": (0, 0, 1), "side": (0, 1, 0), "fold_off": (-1, 0, 0),
            "lengths": (1.20, 1.10, 0.30), "r": 0.055, "mat": "white_panel", "mass": 70.0, "tau": 500.0},
    "lights": [
        *[((XN + 0.06, s * y, 2.645), (1, s * (0.35 if k == 2 else 0.0), -0.05), 0.075, f"brow_lamp_{'l' if s > 0 else 'r'}{k}")
          for s in (-1, 1) for k, y in enumerate((0.25, 0.55, 0.85))],
        ((3.49, 0.62, 1.05), (1, 0, -0.05), 0.09, "bumper_lamp_l"),
        ((3.49, -0.62, 1.05), (1, 0, -0.05), 0.09, "bumper_lamp_r"),
        ((0.30, 1.30, 3.12), (0, 1, -0.6), 0.08, "dock_work_light"),
        ((1.10, -1.27, 3.12), (0, -1, -0.6), 0.08, "work_light_r"),
        ((XA - 0.03, 0.95, 3.05), (-1, 0, -0.5), 0.09, "porch_lamp_l"),
        ((XA - 0.03, -0.30, 3.05), (-1, 0, -0.5), 0.09, "porch_lamp_r"),
    ],
    "sites": [
        ("suitport_l", "suitport_hatch_l", (XA - 0.16, SP_Y, SP_Z), (-1, 0, 0), "hatch", "Suitport hatch (0.6 x 0.9 m); +Z points aft"),
        ("suitport_r", "suitport_hatch_r", (XA - 0.16, -SP_Y, SP_Z), (-1, 0, 0), "hatch", "Suitport hatch (0.6 x 0.9 m); +Z points aft"),
        ("airlock_door", "airlock_door", (XA - 0.34, 0, 2.11), (-1, 0, 0), "hatch", "Walk-in airlock door (1.0 x 1.5 m), Ports=airlock"),
        ("docking_port", "chassis", (DOCK[0], DOCK[1] + 0.10, DOCK[2]), (0, 1, 0), "docking",
         "IDSS-style side docking port (0.8 m clear, 1.3 m collar)"),
        ("porch_deck", "chassis", ((XA + PORCH_X) / 2, 0, PORCH_Z), (0, 0, 1), "crew", "Aft porch grating deck"),
        ("driver_left", "chassis", (2.55, 0.50, 2.20), (1, 0, 0), "crew", "Cab driver station (estimated)"),
        ("driver_right", "chassis", (2.55, -0.50, 2.20), (1, 0, 0), "crew", "Cab co-driver station (estimated)"),
        ("tow_hitch", "chassis", (-3.34, 0, 0.78), (-1, 0, 0), "hitch", "Rear tow hitch"),
        ("tow_point_l", "chassis", (3.55, 0.75, 0.80), (1, 0, 0), "hitch", "Front tow stub"),
        ("tow_point_r", "chassis", (3.55, -0.75, 0.80), (1, 0, 0), "hitch", "Front tow stub"),
        ("star_tracker", "chassis", (1.95, -0.25, ROOF + 0.14), (0, 0, 1), "sensor", "Star tracker"),
    ],
    "imu": (0, 0, 1.5),
}

MASS = {
    "nominal": {"mass": 9000.0, "com_z": 1.75, "source": "concept: 8-10 t two-crew pressurised rover, consumables for 14 days"},
    "dry": {"mass": 7800.0, "com_z": 1.80, "source": "concept: no crew, consumables or payload"},
    "loaded": {"mass": 10000.0, "com_z": 1.70, "source": "concept: + 2 crew, full consumables and 500 kg samples/payload"},
}
DEFAULT_MASS_STATE = "nominal"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (6.0, 2.6, 2.6)
GEOMETRY_VARIANTS = {"Ports": ["suitports", "airlock"], "Solar": ["stowed", "deployed"]}
GEOMETRY_VARIANT_JOINTS = {"Solar": {"deployed": {"solar_wing_l": math.pi / 2, "solar_wing_r": math.pi / 2}}}

SEMANTIC_CLASS = ["lunar_rover", "pressurized_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS = {
    "chassis": [("hull", ["white_panel"]), ("keel", ["grey_panel"])],
    r"\w+_wheel": [("tyre", None)],
}
PHYSICS_MATERIAL = {"tyre": "tyre", "hull": "structure", "keel": "structure"}
PHYSICS_MATERIALS = {"tyre": (0.9, 0.8, 0.0), "structure": (0.5, 0.4, 0.05)}
SIMPLE_TRIS = 40000
RENDER_VIEWS = {
    **K.views(7.0, 3.4, 3.5, centre_z=1.8),
    "aft": ((-11.0, -4.5, 3.0), (-2.8, 0, 1.9), 35),
    "dock": ((1.5, 9.5, 2.6), (0.3, 1.2, 2.2), 35),
    "front": ((12.0, 0.0, 2.4), (0, 0, 2.0), 35),
}
