import math

import rover_kit as K

ASSET_ID = "sev"
ASSET_PATH = "nasa/sev/rover"
FAMILY = "rover"
TITLE = "NASA Space Exploration Vehicle (SEV)"
DOC = ("NASA Space Exploration Vehicle / Lunar Electric Rover (2010 Gen 1B, Desert RATS): a white composite pressurised "
       "cabin on the Chariot chassis, 4.9 m long over the wheels and 3 m tall at the roof, with twelve wheels on six gold "
       "steering columns that pivot 360 deg (crab steering and turn-in-place) on active-suspension legs able to kneel. "
       "Two hinged suitport hatches on the D-shaped aft bulkhead (optional inflatable suitport cover), a hinged side "
       "docking hatch over the middle module, forward windows with a lower bubble window, an aft driving deck with a "
       "standing station, roof LED light bars, a copper hand-rail hoop and camera masts.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"frame_gold": {"color": (0.82, 0.62, 0.18), "roughness": 0.35, "metallic": 0.8},
                                                 "rail_yellow": {"color": (0.86, 0.66, 0.16), "roughness": 0.45, "metallic": 0.4},
                                                 "copper": {"color": (0.72, 0.38, 0.18), "roughness": 0.3, "metallic": 0.9},
                                                 "gloss_white": {"color": (0.90, 0.90, 0.88), "roughness": 0.18}})

R_W, W_W = 0.40, 0.30
COL_Y, DUAL, COL_Z = 1.65, 0.26, 0.95
COLS = (("f", 2.0), ("m", 0.0), ("a", -2.0))
X_AFT, X_NOSE = -0.85, 2.50
BELLY, ROOF = 0.65, 2.92
DECK_Z = 0.80
HATCH_Y = -1.36
SP_Z = 2.0


def _circle_x(x, yc, zc, r, n=24):
    return [(x, yc + r * math.cos(2 * math.pi * k / n), zc + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _columns():
    carriers, wheels = [], []
    for tag, x in COLS:
        for sd, s in (("l", 1), ("r", -1)):
            n = f"{tag}{sd}"
            carriers.append({"name": f"leg_{n}", "type": "prismatic", "axis": (0, 0, 1), "pos": (x, s * COL_Y, COL_Z), "limit": (-0.25, 0.25),
                             "role": "active_suspension", "drive": "position", "auto_spring": {"wheels": 2, "static": 0.02}, "gain": 6.0, "damping": 1.5e4,
                             "mass": 40.0, "column": {"from": (0, 0, -0.10), "to": (0, 0, 0.12), "r": 0.075, "mat": "titanium"},
                             "sleeve": {"from": (0, 0, 0.05), "to": (0, 0, 0.36), "r": 0.13, "mat": "frame_gold"}})
            carriers.append({"name": f"{n}_steer", "parent": f"leg_{n}", "axis": (0, 0, 1), "pos": (x, s * COL_Y, COL_Z),
                             "limit": (-math.pi, math.pi), "role": "steer", "drive": "position", "stiffness": 2.0e4, "damping": 2.0e3,
                             "max_force": 6.0e3, "mass": 30.0, "pivot": False,
                             "column": {"from": (0, 0, -0.26), "to": (0, 0, 0.0), "r": 0.11, "mat": "frame_gold"}})
            for nm, dy, ko, drv in ((n, DUAL, DUAL, True), (f"{n}_dual", -DUAL, -DUAL, False)):
                wheels.append({"name": nm, "x": x, "y": s * (COL_Y + dy), "carrier": f"{n}_steer", "drive": drv,
                               "suspension": {"kingpin_off": ko, "upper_dz": COL_Z - R_W}})
    return carriers, wheels


CARRIERS, WHEELS = _columns()


def _cabin():
    zc = (BELLY + ROOF) / 2
    hh = (ROOF - BELLY) / 2
    out = [
        {"kind": "loft", "name": "cabin", "mat": "gloss_white", "n": 6,
         "stations": [(X_AFT, 1.10, zc, hh - 0.02, 0.45), (X_AFT + 0.12, 1.22, zc, hh, 0.50), (1.70, 1.25, zc, hh, 0.50),
                      (2.15, 1.20, zc - 0.03, hh - 0.04, 0.55), (2.38, 1.08, zc - 0.07, hh - 0.14, 0.52),
                      (X_NOSE, 0.98, zc - 0.10, hh - 0.27, 0.46)]},
        {"kind": "box", "name": "cabin_saddle", "c": (0.80, 0, BELLY - 0.03), "size": (3.00, 1.50, 0.06), "mat": "grey_panel"},
        {"kind": "box", "name": "nose_bumper", "c": (2.38, 0, 0.47), "size": (0.22, 1.50, 0.30), "mat": "rail_yellow"},
        {"kind": "rail", "name": "windscreen_frame", "r": 0.018, "mat": "grey_panel", "closed": True,
         "points": [(X_NOSE + 0.01, y, z) for y, z in ((-0.86, 1.82), (0.86, 1.82), (0.86, 2.40), (0.52, 2.50), (-0.52, 2.50), (-0.86, 2.40))]},
        {"kind": "rail", "name": "window_bay_frame", "r": 0.018, "mat": "grey_panel", "closed": True,
         "points": [(X_NOSE + 0.01, y, z) for y, z in ((-0.80, 1.72), (0.80, 1.72), (0.80, 1.20), (0.52, 1.02), (-0.52, 1.02), (-0.80, 1.20))]},
        {"kind": "sphere", "name": "bubble_window", "c": (X_NOSE - 0.02, 0, 1.34), "r": 0.21, "mat": "glass"},
        {"kind": "rail", "name": "bubble_window_ring", "points": _circle_x(X_NOSE + 0.005, 0, 1.34, 0.225), "closed": True, "r": 0.02,
         "mat": "grey_panel"},
    ]
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        out += [
            {"kind": "panel", "name": f"windscreen_{sd}", "c": (X_NOSE + 0.008, s * 0.43, 2.14), "u": (0, 1, 0), "v": (0, 0, 1), "w": 0.78, "h": 0.60,
             "t": 0.01, "normal": (1, 0, 0), "mat": "glass", "back": "anodised_dark"},
            {"kind": "panel", "name": f"lower_window_{sd}", "c": (X_NOSE + 0.008, s * 0.60, 1.40), "u": (0, 1, 0), "v": (0, 0, 1), "w": 0.30,
             "h": 0.42, "t": 0.01, "normal": (1, 0, 0), "mat": "glass", "back": "anodised_dark"},
            {"kind": "panel", "name": f"side_window_{sd}", "c": (1.95, s * 1.235, 2.25), "u": (1, 0, 0), "v": (0, 0, 1), "w": 0.62, "h": 0.52,
             "t": 0.01, "normal": (0, s, 0), "mat": "glass", "back": "anodised_dark"},
            {"kind": "rail", "name": f"side_window_frame_{sd}", "r": 0.015, "mat": "grey_panel", "closed": True,
             "points": [(x, s * 1.245, z) for x, z in ((1.63, 1.98), (2.27, 1.98), (2.27, 2.52), (1.63, 2.52))]},
        ]
    return out


def _docking_hatch():
    y0 = -1.0
    return [
        {"kind": "cbox", "name": "docking_hatch_housing", "c": (0.0, (y0 + HATCH_Y) / 2, 1.90), "size": (1.45, abs(HATCH_Y - y0), 2.0), "r": 0.06,
         "mat": "gloss_white"},
        {"kind": "rail", "name": "docking_hatch_seal", "r": 0.025, "mat": "grey_panel", "closed": True,
         "points": [(x, HATCH_Y - 0.005, z) for x, z in ((-0.62, 1.02), (0.62, 1.02), (0.62, 2.78), (-0.62, 2.78))]},
        {"kind": "box", "name": "docking_hatch_door", "link": "docking_hatch", "c": (0.0, HATCH_Y - 0.03, 1.90), "size": (1.16, 0.05, 1.68),
         "mat": "gloss_white"},
        {"kind": "rail", "name": "docking_hatch_rim", "link": "docking_hatch", "r": 0.015, "mat": "white_panel", "closed": True,
         "points": [(x, HATCH_Y - 0.06, z) for x, z in ((-0.52, 1.12), (0.52, 1.12), (0.52, 2.68), (-0.52, 2.68))]},
        {"kind": "disc", "name": "docking_hatch_window", "link": "docking_hatch", "c": (0.0, HATCH_Y - 0.055, 2.42), "n": (0, -1, 0), "r": 0.09,
         "t": 0.01, "mat": "glass"},
        {"kind": "lathe", "name": "docking_hatch_logo", "link": "docking_hatch", "c": (0.0, HATCH_Y - 0.056, 1.95), "n": (0, -1, 0),
         "profile": [(0.001, 0.0), (0.28, 0.0)], "mat": "blue_paint"},
        {"kind": "tube", "name": "docking_hatch_handle", "link": "docking_hatch", "p0": (0.45, HATCH_Y - 0.06, 1.75), "p1": (0.45, HATCH_Y - 0.06, 2.05),
         "r": 0.015, "mat": "aluminium"},
        *[{"kind": "tube", "name": f"docking_hatch_hinge_{k}", "p0": (-0.61, HATCH_Y - 0.05, z - 0.08), "p1": (-0.61, HATCH_Y - 0.05, z + 0.08),
           "r": 0.025, "mat": "titanium"} for k, z in enumerate((1.25, 2.55))],
    ]


def _suitports():
    out = []
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        y = s * 0.50
        d = [(0.30, -0.45), (0.30, 0.20), (0.22, 0.38), (0.0, 0.45), (-0.22, 0.38), (-0.30, 0.20), (-0.30, -0.45)]
        out += [
            {"kind": "rail", "name": f"suitport_ring_{sd}", "r": 0.035, "mat": "frame_gold", "closed": True,
             "points": [(X_AFT - 0.02, y + dy * 1.05, SP_Z + dz * 1.05) for dy, dz in d]},
            {"kind": "cbox", "name": f"suitport_hatch_{sd}", "link": f"suitport_hatch_{sd}", "c": (X_AFT - 0.055, y, SP_Z), "size": (0.05, 0.58, 0.88),
             "r": 0.12, "mat": "white_panel"},
            {"kind": "rail", "name": f"suitport_hatch_wheel_{sd}", "link": f"suitport_hatch_{sd}", "points": _circle_x(X_AFT - 0.10, y, SP_Z, 0.12, 16),
             "closed": True, "r": 0.012, "mat": "anodised_grey"},
            {"kind": "tube", "name": f"suitport_hatch_hub_{sd}", "link": f"suitport_hatch_{sd}", "p0": (X_AFT - 0.08, y, SP_Z), "p1": (X_AFT - 0.11, y, SP_Z),
             "r": 0.03, "mat": "anodised_grey"},
            {"kind": "tube", "name": f"suitport_hinge_{sd}", "p0": (X_AFT - 0.06, s * 0.80, SP_Z - 0.40), "p1": (X_AFT - 0.06, s * 0.80, SP_Z + 0.40),
             "r": 0.02, "mat": "titanium"},
        ]
    out += [
        {"kind": "loft", "name": "suitport_cover", "mat": "beta_white", "variant": "SuitportCover:installed", "n": 6,
         "stations": [(X_AFT - 0.02 - d, r, 1.92, r, r) for d, r in ((0.95, 0.06), (0.92, 0.38), (0.82, 0.68), (0.66, 0.90), (0.45, 1.03), (0.22, 1.09),
                                                                    (0.0, 1.10))]},
        {"kind": "rail", "name": "suitport_cover_collar", "points": _circle_x(X_AFT - 0.04, 0, 1.92, 1.10, 40), "closed": True, "r": 0.04,
         "mat": "white_panel", "variant": "SuitportCover:installed"},
    ]
    return out


def _chassis():
    out = []
    zr = BELLY - 0.12
    for s in (-1, 1):
        out.append({"kind": "beam", "name": f"frame_rail_{s + 1}", "p0": (-2.35, s * 0.78, zr), "p1": (2.30, s * 0.78, zr), "w": 0.12, "h": 0.16,
                    "mat": "rail_yellow"})
        for tag, x in COLS:
            out.append({"kind": "beam", "name": f"leg_arm_{tag}_{s + 1}", "p0": (x, s * 0.78, zr), "p1": (x, s * (COL_Y - 0.12), COL_Z + 0.10),
                        "w": 0.10, "h": 0.12, "mat": "frame_gold"})
            out.append({"kind": "beam", "name": f"leg_strut_{tag}_{s + 1}", "p0": (x - 0.35, s * 0.78, zr), "p1": (x, s * (COL_Y - 0.12), COL_Z + 0.25),
                        "w": 0.05, "h": 0.05, "mat": "anodised_dark"})
            out.append({"kind": "tube", "name": f"column_cap_{tag}_{s + 1}", "p0": (x, s * COL_Y, COL_Z + 0.36), "p1": (x, s * COL_Y, COL_Z + 0.56),
                        "r": 0.11, "mat": "white_panel"})
    for x in (-2.30, -0.85, 1.0, 2.25):
        out.append({"kind": "beam", "name": f"frame_cross_{int(x * 100)}", "p0": (x, -0.78, zr), "p1": (x, 0.78, zr), "w": 0.10, "h": 0.12,
                    "mat": "rail_yellow"})
    xd0, xd1 = -2.35, X_AFT - 0.05
    out += [
        {"kind": "box", "name": "aft_deck", "c": ((xd0 + xd1) / 2, 0, DECK_Z - 0.02), "size": (xd1 - xd0, 2.0, 0.04), "mat": "grating"},
        {"kind": "beam", "name": "aft_deck_edge", "p0": (xd0, -1.0, DECK_Z - 0.06), "p1": (xd0, 1.0, DECK_Z - 0.06), "w": 0.06, "h": 0.10,
         "mat": "rail_yellow"},
        {"kind": "box", "name": "aft_deck_riser", "c": (-1.6, 0, (zr + DECK_Z) / 2), "size": (1.4, 1.5, DECK_Z - zr - 0.04), "mat": "grey_panel"},
        {"kind": "box", "name": "tool_interface", "c": (xd0 - 0.06, 0, 0.55), "size": (0.12, 0.70, 0.30), "mat": "titanium"},
        {"kind": "box", "name": "aft_equipment_rack", "c": (-2.05, 0.62, DECK_Z + 0.32), "size": (0.45, 0.55, 0.60), "mat": "white_panel"},
        {"kind": "box", "name": "aft_equipment_vent", "c": (-2.05, 0.62 - 0.28, DECK_Z + 0.32), "size": (0.36, 0.01, 0.42), "mat": "grating"},
    ]
    for s in (-1, 1):
        out.append({"kind": "rail", "name": f"aft_rail_{s + 1}", "r": 0.022, "mat": "rail_yellow",
                    "points": [(X_AFT - 0.10, s * 0.98, DECK_Z), (X_AFT - 0.10, s * 0.98, DECK_Z + 1.05), (-2.30, s * 0.98, DECK_Z + 1.05),
                               (-2.30, s * 0.98, DECK_Z)]})
        out.append({"kind": "tube", "name": f"aft_rail_mid_{s + 1}", "p0": (X_AFT - 0.10, s * 0.98, DECK_Z + 0.55), "p1": (-2.30, s * 0.98, DECK_Z + 0.55),
                    "r": 0.016, "mat": "rail_yellow"})
    out.append({"kind": "tube", "name": "aft_rail_back", "p0": (-2.30, -0.98, DECK_Z + 1.05), "p1": (-2.30, 0.98, DECK_Z + 1.05), "r": 0.022,
                "mat": "rail_yellow"})
    return out


def _roof():
    z = ROOF
    out = [
        {"kind": "rail", "name": "roof_hoop", "r": 0.02, "mat": "copper", "closed": True,
         "points": [(2.08, 0.62, z + 0.05), (2.15, 0.0, z + 0.07), (2.08, -0.62, z + 0.05), (1.70, -0.86, z + 0.06), (-0.55, -0.86, z + 0.06),
                    (-0.62, 0.0, z + 0.07), (-0.55, 0.86, z + 0.06), (1.70, 0.86, z + 0.06)]},
        *[{"kind": "tube", "name": f"roof_hoop_post_{k}", "p0": (x, y, z - 0.08), "p1": (x, y, z + 0.06), "r": 0.015, "mat": "copper"}
          for k, (x, y) in enumerate(((1.70, 0.86), (1.70, -0.86), (-0.55, 0.86), (-0.55, -0.86), (0.6, 0.86), (0.6, -0.86)))],
        {"kind": "box", "name": "roof_flag_plate", "c": (2.0, 0, z + 0.06), "size": (0.25, 0.40, 0.03), "mat": "white_panel"},
        {"kind": "box", "name": "roof_equipment", "c": (0.3, 0.0, z + 0.06), "size": (1.10, 0.90, 0.12), "mat": "white_panel"},
    ]
    for k, y in enumerate((-0.68, -0.24, 0.24, 0.68)):
        out.append({"kind": "box", "name": f"light_bar_front_{k}", "c": (2.02, y, z + 0.04), "size": (0.10, 0.34, 0.08), "mat": "anodised_dark"})
    for k, y in enumerate((-0.45, 0.45)):
        out.append({"kind": "box", "name": f"light_bar_aft_{k}", "c": (-0.58, y, z + 0.04), "size": (0.10, 0.34, 0.08), "mat": "anodised_dark"})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "solid", "grousers": 30, "chevron": False, "grouser_h": 0.02, "spokes": 0, "disc": True,
              "disc_mat": "frame_gold", "rim_mat": "frame_gold", "hub_mat": "frame_gold", "hub_frac": 0.16, "rim_frac": 0.56, "mass": 25.0},
    "carriers": CARRIERS,
    "wheels": WHEELS,
    "suspension": {"type": "carrier", "knuckle_mat": "frame_gold", "knuckle_t": 0.09},
    "links": [
        {"name": "docking_hatch", "pos": (-0.61, HATCH_Y - 0.05, 1.90), "axis": (0, 0, -1), "limit": (0.0, math.radians(100)), "role": "hatch",
         "mass": 60.0, "drive": {"kind": "position", "stiffness": 4000.0, "damping": 400.0, "max_force": 1000.0}},
        *[{"name": f"suitport_hatch_{'l' if s > 0 else 'r'}", "pos": (X_AFT - 0.06, s * 0.80, SP_Z), "axis": (0, 0, -s),
           "limit": (0.0, math.radians(100)), "role": "hatch", "mass": 15.0,
           "drive": {"kind": "position", "stiffness": 1500.0, "damping": 150.0, "max_force": 400.0}} for s in (1, -1)],
    ],
    "parts": [*_chassis(), *_cabin(), *_docking_hatch(), *_suitports(), *_roof()],
    "crew": {"x": -1.55, "floor_z": DECK_Z, "seats_y": (-0.35,), "style": "stand", "console": (-1.10, -0.35, DECK_Z + 0.80)},
    "masts": [{"name": "nav_mast", "base": (2.05, 0.0, ROOF + 0.05), "h": 0.22, "r": 0.025, "head": (0.10, 0.30, 0.08), "cams": (-0.11, 0.11)},
              {"name": "aft_mast", "base": (-0.40, -1.12, 2.45), "h": 1.05, "r": 0.03, "pan_tilt": False, "head": (0.10, 0.10, 0.14),
               "cams": (0.0,), "head_mat": "white_panel", "foot": (0.10, 0.10, 0.10), "forward": (-1, 0, 0)},
              {"name": "sci_mast", "base": (-0.40, 1.12, 2.45), "h": 0.95, "r": 0.03, "pan_tilt": False, "head": (0.10, 0.10, 0.14),
               "cams": (0.0,), "head_mat": "white_panel", "foot": (0.10, 0.10, 0.10)}],
    "lights": [
        *[((2.08, y, ROOF + 0.04), (1, 0, -0.15), 0.035, f"roof_bar_{k}") for k, y in enumerate((-0.68, -0.24, 0.24, 0.68))],
        *[((-0.64, y, ROOF + 0.04), (-1, 0, -0.25), 0.035, f"aft_bar_{k}") for k, y in enumerate((-0.45, 0.45))],
        ((2.50, 0.45, 0.47), (1, 0, 0), 0.05, "bumper_lamp_l"),
        ((2.50, -0.45, 0.47), (1, 0, 0), 0.05, "bumper_lamp_r"),
        ((0.80, HATCH_Y - 0.01, 2.75), (0, -1, -0.4), 0.05, "docking_lamp"),
        ((-2.30, 0.98, DECK_Z + 1.10), (-1, 0, -0.4), 0.05, "deck_lamp_l"),
        ((-2.30, -0.98, DECK_Z + 1.10), (-1, 0, -0.4), 0.05, "deck_lamp_r"),
    ],
    "sites": [
        ("suitport_l", "suitport_hatch_l", (X_AFT - 0.09, 0.50, SP_Z), (-1, 0, 0), "hatch", "Suitport hatch (0.6 x 0.9 m D-shape), centre 2.0 m"),
        ("suitport_r", "suitport_hatch_r", (X_AFT - 0.09, -0.50, SP_Z), (-1, 0, 0), "hatch", "Suitport hatch (0.6 x 0.9 m D-shape), centre 2.0 m"),
        ("docking_hatch", "docking_hatch", (0.0, HATCH_Y - 0.06, 1.90), (0, -1, 0), "docking",
         "Side docking hatch (frame 1.45 x 2.0 m) for rover-to-rover / habitat docking"),
        ("aft_deck", "chassis", (-1.60, 0, DECK_Z), (0, 0, 1), "crew", "Aft driving / work deck (suitport porch)"),
        ("tool_interface", "chassis", (-2.48, 0, 0.55), (-1, 0, 0), "hitch", "Aft work package interface (winch, blade, crane)"),
    ],
    "imu": (0.5, 0, 1.2),
}

MASS = {
    "unloaded": {"mass": 3000.0, "com_z": 1.35, "com_x": 0.4, "source": "NASA: about 3,000 kg including the 1,000 kg Chariot"},
    "loaded": {"mass": 4000.0, "com_z": 1.30, "com_x": 0.2, "source": "NASA: + 1,000 kg payload"},
}
DEFAULT_MASS_STATE = "unloaded"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (4.5, 2.4, 2.3)
GEOMETRY_VARIANTS = {"SuitportCover": ["off", "installed"]}

SEMANTIC_CLASS = ["lunar_rover", "pressurized_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("gloss_white", "white_panel", "grey_panel"))
SIMPLE_TRIS = 30000
RENDER_VIEWS = {**K.views(4.9, 4.1, 3.0, centre_z=1.5), "aft": ((-8.5, -3.5, 2.6), (-1.0, 0, 1.6), 35),
                "front": ((9.0, 0.0, 1.8), (0, 0, 1.6), 35), "hatch": ((0.5, -7.5, 2.0), (0, 0, 1.6), 35)}
