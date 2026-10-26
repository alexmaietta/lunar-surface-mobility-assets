import math

import rover_kit as K

ASSET_ID = "clv1"
ASSET_PATH = "astrolab/clv1/rover"
FAMILY = "rover"
TITLE = "Astrolab CLV-1"
DOC = ("Astrolab CLV-1 crewed Lunar Terrain Vehicle (NASA LTV demonstration task order, May 2026; derived from FLEX): "
       "about 4.0 x 2.3 x 2.6 m deployed (wheelbase 3.05 m, track 2.05 m) and up to 950 kg, two seated crew side by "
       "side with a central console in an open tub under a white tube roll cage with a roof light bar, a front fascia "
       "with a triangle grille and LED headlamps, a tall chamfered rear avionics box carrying the high-gain antenna, "
       "an open rear cargo rack, and four 0.93 m Venturi cable-spoke wheels with white side rings on active "
       "wheel-on-limb legs with tall steer posts and all-wheel steering.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"frame_white": {"color": (0.88, 0.88, 0.86), "roughness": 0.35},
                                                 "ring_white": {"color": (0.86, 0.86, 0.85), "roughness": 0.7},
                                                 "lamp_amber": {"color": (1.0, 0.55, 0.15), "roughness": 0.2,
                                                                "emission": (1.0, 0.50, 0.12, 5.0)}})

R_W, W_W, WB, TRACK = 0.465, 0.28, 3.05, 2.05
BW = 0.80
BELLY, DECK, SILL = 0.58, 0.90, 1.12
XF, XB = 1.625, -1.625
COWL = 1.30
BOX = (-0.42, -1.05)
BOX_TOP = 2.30
ROOF = 2.30
CAGE_Y = 0.74
STEER = (math.radians(-90), math.radians(90))


def _tub():
    out = [{"kind": "cbox", "name": "tub", "c": ((XF + XB) / 2, 0, (BELLY + DECK) / 2), "size": (XF - XB, 2 * BW, DECK - BELLY), "r": 0.06,
            "mat": "white_panel"},
           {"kind": "cbox", "name": "front_cowl", "c": ((XF + COWL) / 2, 0, (DECK + SILL + 0.06) / 2), "size": (XF - COWL, 2 * BW, SILL + 0.06 - DECK),
            "r": 0.05, "mat": "white_panel"},
           {"kind": "box", "name": "floor", "c": ((COWL + BOX[0]) / 2, 0, DECK + 0.01), "size": (COWL - BOX[0], 2 * BW - 0.12, 0.02),
            "mat": "grey_panel"},
           {"kind": "box", "name": "belly_pan", "c": (0, 0, BELLY - 0.01), "size": (XF - XB - 0.3, 2 * BW - 0.3, 0.02), "mat": "anodised_grey"}]
    for s in (-1, 1):
        out.append({"kind": "box", "name": f"side_sill_{s + 1}", "c": ((COWL + BOX[0]) / 2, s * (BW - 0.04), (DECK + SILL) / 2),
                    "size": (COWL - BOX[0], 0.08, SILL - DECK), "mat": "white_panel"})
        out.append({"kind": "box", "name": f"sill_stripe_{s + 1}", "c": ((COWL + BOX[0]) / 2, s * BW, SILL - 0.05),
                    "size": (COWL - BOX[0] - 0.1, 0.01, 0.03), "mat": "yellow"})
        out.append({"kind": "box", "name": f"side_skirt_{s + 1}", "c": (0, s * (BW + 0.005), (BELLY + DECK) / 2 - 0.04),
                    "size": (XF - XB - 0.5, 0.01, 0.10), "mat": "anodised_grey"})
    return out


def _grille():
    x = XF + 0.005
    out = [{"kind": "box", "name": "grille_panel", "c": (x, 0, 0.74), "size": (0.02, 1.30, 0.22), "mat": "grey_panel"},
           {"kind": "box", "name": "lamp_band", "c": (x, 0, 1.02), "size": (0.02, 1.50, 0.10), "mat": "anodised_dark"},
           {"kind": "box", "name": "logo_band", "c": (x + 0.002, 0, 0.92), "size": (0.02, 0.40, 0.04), "mat": "accent"}]
    for k in range(6):
        y = -0.55 + 0.22 * k
        out.append({"kind": "extrude", "name": f"grille_slot_{k}", "y": (y - 0.09, y + 0.09), "mat": "anodised_dark",
                    "profile": [(x, 0.66), (x + 0.02, 0.66), (x + 0.02, 0.80), (x, 0.80)]})
    return out


def _cage():
    out = []
    for s in (-1, 1):
        y = s * CAGE_Y
        out.append({"kind": "rail", "name": f"roll_cage_{s + 1}", "r": 0.04, "mat": "frame_white",
                    "points": [(COWL + 0.05, s * (BW - 0.04), SILL + 0.04), (1.00, y, ROOF), (BOX[0] - 0.02, y, ROOF)]})
        out.append({"kind": "rail", "name": f"cage_brace_{s + 1}", "r": 0.03, "mat": "frame_white",
                    "points": [(0.15, s * (BW - 0.04), SILL), (-0.05, y, ROOF - 0.20), (BOX[0] - 0.02, y, ROOF - 0.20)]})
        out.append({"kind": "rail", "name": f"grab_handle_{s + 1}", "r": 0.018, "mat": "yellow",
                    "points": [(1.15, y, 1.55), (1.10, y - s * 0.06, 1.62), (1.03, y - s * 0.06, 1.85), (1.00, y, 1.92)]})
    for x in (1.00, 0.30, BOX[0] - 0.02):
        out.append({"kind": "tube", "name": f"roof_bar_{int(x * 100)}", "p0": (x, -CAGE_Y, ROOF), "p1": (x, CAGE_Y, ROOF), "r": 0.035,
                    "mat": "frame_white"})
    out.append({"kind": "tube", "name": "roof_spine", "p0": (1.00, 0, ROOF), "p1": (BOX[0] - 0.02, 0, ROOF), "r": 0.03, "mat": "frame_white"})
    out.append({"kind": "box", "name": "roof_light_bar", "c": (1.02, 0, ROOF + 0.07), "size": (0.10, 1.30, 0.10), "mat": "frame_white"})
    out.append({"kind": "tube", "name": "console_pillar", "p0": (0.98, 0, DECK), "p1": (0.98, 0, 1.30), "r": 0.05, "mat": "frame_white"})
    return out


def _rear():
    x0, x1 = BOX
    out = [{"kind": "loft", "name": "avionics_box", "mat": "white_panel", "n": 1, "smooth": False,
            "stations": [(x0, 0.66, (DECK + BOX_TOP) / 2, (BOX_TOP - DECK) / 2, 0.24), (x1, 0.66, (DECK + BOX_TOP) / 2, (BOX_TOP - DECK) / 2, 0.24)]},
           {"kind": "panel", "name": "avionics_logo_panel", "c": (x1 - 0.005, 0, 1.70), "u": (0, 1, 0), "v": (0, 0, 1), "w": 0.90, "h": 0.70, "t": 0.01,
            "normal": (-1, 0, 0), "mat": "beta_white", "back": "white_panel"},
           {"kind": "box", "name": "avionics_accent", "c": (x0 + 0.01, 0, 1.95), "size": (0.02, 1.20, 0.04), "mat": "yellow"},
           {"kind": "box", "name": "seat_bulkhead", "c": (x0 + 0.02, 0, 1.25), "size": (0.04, 1.40, 0.70), "mat": "grey_panel"},
           {"kind": "box", "name": "cargo_floor", "c": ((x1 - 0.02 + XB - 0.18) / 2, 0, DECK + 0.01), "size": (x1 - 0.02 - XB + 0.18, 1.50, 0.03),
            "mat": "grating"}]
    xr = XB - 0.18
    for s in (-1, 1):
        y = s * 0.74
        out.append({"kind": "rail", "name": f"cargo_rack_{s + 1}", "r": 0.025, "mat": "frame_white",
                    "points": [(x1 - 0.02, y, DECK), (x1 - 0.02, y, 1.32), (xr, y, 1.32), (xr, y, DECK)]})
        out.append({"kind": "tube", "name": f"cargo_rail_mid_{s + 1}", "p0": (x1 - 0.02, y, 1.12), "p1": (xr, y, 1.12), "r": 0.02,
                    "mat": "frame_white"})
    out.append({"kind": "tube", "name": "cargo_rack_back", "p0": (xr, -0.74, 1.32), "p1": (xr, 0.74, 1.32), "r": 0.025, "mat": "frame_white"})
    out.append({"kind": "tube", "name": "cargo_rack_back_mid", "p0": (xr, -0.74, 1.12), "p1": (xr, 0.74, 1.12), "r": 0.02, "mat": "frame_white"})
    out.append({"kind": "box", "name": "tail_panel", "c": (XB + 0.005, 0, (BELLY + DECK) / 2), "size": (0.02, 1.40, 0.20), "mat": "grey_panel"})
    return out


def _wheel_rings():
    out = []
    for n, side in (("fl", 1), ("fr", -1), ("rl", 1), ("rr", -1)):
        x = WB / 2 if n[0] == "f" else -WB / 2
        y = side * (TRACK / 2 + W_W / 2 + 0.004)
        out.append({"kind": "lathe", "name": f"{n}_side_ring", "link": f"{n}_wheel", "c": (x, y, R_W), "n": (0, side, 0),
                    "profile": [(0.335, 0.0), (0.45, 0.0)], "sides": 48, "mat": "ring_white"})
        out.append({"kind": "lathe", "name": f"{n}_inner_ring", "link": f"{n}_wheel", "c": (x, y - side * (W_W + 0.008), R_W), "n": (0, -side, 0),
                    "profile": [(0.35, 0.0), (0.45, 0.0)], "sides": 48, "mat": "ring_white"})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "mesh", "grousers": 48, "chevron": False, "grouser_h": 0.012, "spokes": 16, "spoke_r": 0.009, "spoke_curve": 0.0, "hub_frac": 0.24,
              "rim_frac": 0.72, "mass": 22.0, "grouser_mat": "titanium", "spoke_mat": "aluminium", "rim_mat": "aluminium", "hub_mat": "aluminium"},
    "wheels": K.four_wheels(WB, TRACK, STEER),
    "suspension": {"type": "trailing_arm", "active": True, "arm_dx": 0.55, "pivot_dz": 0.45, "upper_dz": 0.64, "kingpin_off": 0.18,
                   "travel": (0.25, 0.30), "static_rad": 0.10, "beam": 0.09, "arm_mat": "frame_white", "knuckle_mat": "frame_white"},
    "parts": [
        *_tub(),
        *_grille(),
        *_cage(),
        *_rear(),
        *_wheel_rings(),
        {"kind": "box", "name": "cargo_box", "c": (0.45, 0, 1.22), "size": (1.20, 1.40, 0.60), "mat": "mli_silver", "variant": "Crew:cargo"},
        {"kind": "box", "name": "box_mast_foot", "c": (-0.60, 0.50, BOX_TOP + 0.02), "size": (0.10, 0.10, 0.04), "mat": "anodised_dark"},
    ],
    "crew": {"variant": "Crew:crewed", "x": 0.30, "floor_z": DECK, "seats_y": (0.40, -0.40), "seat_h": 0.32, "style": "seat",
             "console": (0.98, 0, 1.40), "handholds": [[(0.90, 0.20, 1.46), (0.90, 0.20, 1.56), (0.90, -0.20, 1.56), (0.90, -0.20, 1.46)]],
             "rail_mat": "yellow"},
    "masts": [{"name": "nav_mast", "base": (0.90, 0.56, ROOF + 0.035), "h": 0.10, "r": 0.025, "head": (0.10, 0.26, 0.08), "cams": (-0.09, 0.09)},
              {"name": "rear_mast", "base": (-0.60, 0.50, BOX_TOP + 0.04), "h": 0.08, "r": 0.02, "head": (0.08, 0.16, 0.06), "cams": (-0.05, 0.05),
               "forward": (-1, 0, 0)}],
    "hga": {"base": (-0.80, -0.38, BOX_TOP), "h": 0.04, "r": 0.13, "depth": 0.25, "boresight": (0, 0, 1), "band": "S/Ka"},
    "lights": [
        *[((XF + 0.015, s * y, 1.02), (1, 0, -0.06), 0.035, f"head_lamp_{'l' if s > 0 else 'r'}{k}")
          for s in (-1, 1) for k, y in enumerate((0.36, 0.50, 0.64))],
        *[((1.075, y, ROOF + 0.07), (1, 0, -0.25), 0.04, f"roof_lamp_{k}") for k, y in enumerate((-0.48, -0.16, 0.16, 0.48))],
        ((XB - 0.01, 0.58, (BELLY + DECK) / 2), (-1, 0, 0), 0.04, "tail_lamp_l"),
        ((XB - 0.01, -0.58, (BELLY + DECK) / 2), (-1, 0, 0), 0.04, "tail_lamp_r"),
        ((BOX[1] - 0.01, 0.50, 2.12), (-1, 0, -0.3), 0.045, "cargo_lamp_l"),
        ((BOX[1] - 0.01, -0.50, 2.12), (-1, 0, -0.3), 0.045, "cargo_lamp_r"),
    ],
    "sites": [
        ("cargo_rack", "chassis", ((BOX[1] + XB - 0.18) / 2, 0, DECK + 0.03), (0, 0, 1), "payload_interface", "Rear open cargo rack"),
        ("front_payload", "chassis", (0.45, 0, DECK + 0.03), (0, 0, 1), "payload_interface", "Crew deck / uncrewed cargo interface"),
        ("roof_point", "chassis", (0.30, 0, ROOF + 0.04), (0, 0, 1), "handling", "Roll-cage lift point"),
    ],
    "imu": (0, 0, 0.8),
}

MASS = {
    "empty": {"mass": 950.0, "com_z": 0.95, "source": "Astrolab: up to 950 kg"},
    "crewed": {"mass": 1490.0, "com_z": 1.15, "com_x": 0.2, "source": "estimate: + 2 suited crew (2 x 220 kg) + 100 kg"},
}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (3.3, 1.6, 1.4)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "cargo"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics()
SIMPLE_TRIS = 24000
RENDER_VIEWS = {**K.views(4.0, 2.4, 2.6, centre_z=1.1), "front": ((10.0, 0.0, 1.5), (0, 0, 1.3), 35),
                "rear": ((-10.0, 0.0, 2.0), (0, 0, 1.3), 35)}
