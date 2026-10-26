import math

import rover_kit as K

ASSET_ID = "eagle"
ASSET_PATH = "lunar_outpost/eagle/rover"
FAMILY = "rover"
TITLE = "Lunar Outpost Eagle"
DOC = ("Lunar Outpost Eagle Lunar Terrain Vehicle (2024-25 LTV bid with Lockheed Martin, GM, Goodyear and MDA): a "
       "cab-forward brushed-metal canopy with white side panels over two seats, battery modules along the sills, a "
       "rear cargo bed with lattice side screens under a tilting solar panel, an MDA robotic arm, a roof dish, and four "
       "1 m mesh wheels on double-wishbone suspension with all-wheel steering.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"led_cyan": {"color": (0.3, 0.9, 1.0), "roughness": 0.2, "emission": (0.2, 0.85, 1.0, 8.0)},
                                                 "gold_susp": {"color": (0.80, 0.58, 0.20), "roughness": 0.35, "metallic": 0.9}})

R_W, WB, TRACK = 0.50, 2.60, 2.10
DECK = 0.95
BED = 1.02
ROOF = 2.20
CY = 0.78
STEER = (math.radians(-30), math.radians(30))
DOOR = [(-0.42, DECK), (1.50, DECK), (1.50, 1.45), (0.68, 1.45), (0.38, 1.90), (-0.25, 1.98), (-0.42, 1.84)]
NOSE = [(1.40, 0.52), (1.96, 0.52), (1.98, 0.96), (1.84, 1.34), (1.40, 1.34)]


def _cab_side(s):
    t = "l" if s > 0 else "r"
    y = s * CY
    return [
        {"kind": "extrude", "name": f"door_panel_{t}", "profile": DOOR, "y": tuple(sorted((s * (CY - 0.04), y))), "mat": "white_panel"},
        {"kind": "rail", "name": f"cab_frame_{t}", "r": 0.04, "mat": "brushed_panel",
         "points": [(1.84, y, 1.30), (1.74, y, 1.98), (1.52, y, ROOF), (-0.42, y, ROOF), (-0.42, y, 1.84)]},
        {"kind": "tube", "name": f"b_pillar_{t}", "p0": (0.38, y, 1.90), "p1": (0.38, y, ROOF), "r": 0.03, "mat": "brushed_panel"},
        {"kind": "rail", "name": f"roof_led_{t}", "r": 0.012, "mat": "led_cyan", "points": [(1.30, y + s * 0.04, ROOF + 0.02), (0.10, y + s * 0.04, ROOF + 0.02)]},
    ]


def _sill(s):
    t = "l" if s > 0 else "r"
    out = []
    for k, x in enumerate((-0.52, 0.0, 0.52)):
        out += [{"kind": "cbox", "name": f"battery_{t}_{k}", "c": (x, s * 0.70, 0.66), "size": (0.50, 0.24, 0.34), "r": 0.03, "mat": "anodised_grey"},
                {"kind": "box", "name": f"battery_led_{t}_{k}", "c": (x - 0.12, s * 0.823, 0.72), "size": (0.10, 0.008, 0.025), "mat": "led_cyan"}]
    return out


def _bed_side(s):
    t = "l" if s > 0 else "r"
    y = s * CY
    return [
        {"kind": "panel", "name": f"bed_screen_{t}", "c": (-1.17, y, 1.42), "u": (1, 0, 0), "v": (0, 0, 1), "w": 1.36, "h": 0.74, "t": 0.01,
         "normal": (0, s, 0), "mat": "grating", "back": "grating"},
        {"kind": "rail", "name": f"bed_frame_{t}", "r": 0.03, "mat": "brushed_panel",
         "points": [(-0.44, y, BED), (-0.44, y, 1.96), (-1.88, y, 1.96), (-1.88, y, BED)]},
        {"kind": "tube", "name": f"bed_rail_{t}", "p0": (-1.88, y, 1.80), "p1": (-0.44, y, 1.80), "r": 0.02, "mat": "brushed_panel"},
    ]


ROVER = {
    "wheel": {"r": R_W, "w": 0.30, "style": "mesh", "grousers": 34, "grouser_h": 0.014, "spokes": 10, "spoke_r": 0.018, "hub_frac": 0.34,
              "rim_frac": 0.78, "mass": 25.0, "grouser_mat": "titanium", "rim_mat": "anodised_dark", "hub_mat": "anodised_dark",
              "spoke_mat": "anodised_dark"},
    "wheels": K.four_wheels(WB, TRACK, STEER),
    "suspension": {"type": "double_wishbone", "arm": 0.36, "kingpin_off": 0.25, "lower_dz": -0.08, "upper_dz": 0.18, "travel": (0.15, 0.16),
                   "static_rad": 0.12, "spread": 0.30, "arm_mat": "gold_susp", "spring_mat": "titanium"},
    "fenders": {"gap": 0.05, "arc": (-55, 65), "overhang": 0.04, "mat": "brushed_panel"},
    "parts": [
        {"kind": "cbox", "name": "tub", "c": (-0.05, 0, 0.72), "size": (3.70, 1.16, 0.46), "r": 0.05, "mat": "brushed_panel"},
        *_sill(1), *_sill(-1),
        {"kind": "box", "name": "cab_floor", "c": (0.55, 0, DECK + 0.015), "size": (1.90, 1.52, 0.03), "mat": "grey_panel"},
        {"kind": "extrude", "name": "nose", "profile": NOSE, "y": (-CY, CY), "mat": "brushed_panel"},
        {"kind": "box", "name": "nose_led", "c": (1.965, 0, 0.60), "size": (0.02, 1.30, 0.03), "mat": "led_cyan"},
        {"kind": "box", "name": "dash", "c": (1.48, 0, 1.36), "size": (0.20, 1.40, 0.06), "mat": "anodised_dark"},
        *_cab_side(1), *_cab_side(-1),
        {"kind": "extrude", "name": "roof", "profile": [(-0.44, ROOF - 0.03), (1.52, ROOF - 0.03), (1.56, ROOF + 0.02), (-0.44, ROOF + 0.03)],
         "y": (-CY - 0.02, CY + 0.02), "mat": "brushed_panel"},
        {"kind": "box", "name": "roof_led_front", "c": (1.56, 0, ROOF), "size": (0.02, 1.40, 0.025), "mat": "led_cyan"},
        {"kind": "box", "name": "cab_back", "c": (-0.43, 0, 1.40), "size": (0.03, 1.52, 0.80), "mat": "white_panel"},
        {"kind": "box", "name": "bed_floor", "c": (-1.16, 0, BED), "size": (1.46, 1.56, 0.04), "mat": "grating"},
        *_bed_side(1), *_bed_side(-1),
        {"kind": "box", "name": "tool_rack", "c": (-1.72, 0.30, BED + 0.40), "size": (0.24, 0.70, 0.76), "mat": "mli_silver"},
        {"kind": "box", "name": "tool_box", "c": (-1.72, -0.40, BED + 0.18), "size": (0.24, 0.55, 0.32), "mat": "anodised_grey"},
        {"kind": "box", "name": "cargo_pod", "c": (0.50, 0, DECK + 0.40), "size": (1.10, 1.30, 0.76), "mat": "mli_gold", "variant": "Crew:cargo"},
    ],
    "crew": {"variant": "Crew:crewed", "x": 0.45, "floor_z": DECK, "seats_y": (0.38, -0.38), "style": "seat", "seat_h": 0.42,
             "console": (1.25, 0, 1.40)},
    "masts": [{"name": "nav_mast", "base": (0.95, 0.0, ROOF + 0.03), "h": 0.06, "r": 0.025, "head": (0.09, 0.40, 0.08), "cams": (-0.15, 0.15),
               "lamp": True}],
    "hga": {"base": (0.30, -0.35, ROOF + 0.03), "h": 0.02, "r": 0.18, "boresight": (0.5, 0, 1), "band": "S/Ka", "back": "aluminium"},
    "solar": [{"name": "solar_panel", "c": (-1.16, 0, 2.00), "u": (1, 0, 0), "v": (0, 1, 0), "w": 1.42, "h": 1.50, "normal": (0, 0, 1),
               "mass": 8.0, "back": "aluminium",
               "hinge": {"pos": (-0.44, 0, 1.99), "axis": (0, 1, 0), "limit": (0.0, math.radians(85)), "k": 600.0, "c": 60.0, "tau": 300.0}}],
    "arm": {"base": (-1.72, -0.40, BED + 0.40), "lengths": (0.90, 0.85, 0.22), "r": 0.045, "stow_dir": (1, 0, 0), "mass": 45.0, "tau": 250.0},
    "lights": [((1.97, 0.58, 0.78), (1, 0, -0.05), 0.04, "headlight_l"), ((1.97, -0.58, 0.78), (1, 0, -0.05), 0.04, "headlight_r"),
               ((1.58, 0.62, ROOF - 0.08), (1, 0, -0.25), 0.04, "roof_light_l"), ((1.58, -0.62, ROOF - 0.08), (1, 0, -0.25), 0.04, "roof_light_r"),
               ((-1.92, 0.55, 1.85), (-1, 0, -0.4), 0.035, "bed_light_l"), ((-1.92, -0.55, 1.85), (-1, 0, -0.4), 0.035, "bed_light_r")],
    "sites": [
        ("cargo_bed", "chassis", (-1.16, 0, BED + 0.03), (0, 0, 1), "payload_interface", "Rear cargo bed"),
        ("tow_hitch", "chassis", (-1.95, 0, 0.62), (-1, 0, 0), "hitch", "Rear tow hitch"),
    ],
    "imu": (0, 0, 0.75),
}

MASS = {
    "empty": {"mass": 1600.0, "com_z": 0.85, "source": "estimate: 1.5-2 t (forum level)"},
    "crewed": {"mass": 2140.0, "com_z": 1.05, "com_x": 0.15, "source": "estimate: + 2 suited crew (2 x 220 kg) + 100 kg"},
}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (3.8, 1.6, 1.4)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "cargo"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("brushed_panel", "white_panel"))
SIMPLE_TRIS = 20000
RENDER_VIEWS = K.views(3.9, 2.5, 2.5, centre_z=1.1)
