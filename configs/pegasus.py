import math

import rover_kit as K

ASSET_ID = "pegasus"
ASSET_PATH = "lunar_outpost/pegasus/rover"
FAMILY = "rover"
TITLE = "Lunar Outpost Pegasus"
DOC = ("Lunar Outpost Pegasus Lunar Terrain Vehicle (NASA LTV demonstration task order, May 2026): an LRV-like low "
       "brushed-aluminium rover of about 1 t with two seats side by side, a central hand controller and display, gold "
       "hand-holds, a lattice-fronted cargo box, an open-front rear shell carrying two hinged solar wings and a dish mast, "
       "cyan LED bars, and four Goodyear spring-mesh wheels on double-wishbone suspension with all-wheel steering.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"handhold": {"color": (0.85, 0.62, 0.20), "roughness": 0.3, "metallic": 0.9},
                                                 "led_cyan": {"color": (0.3, 0.9, 1.0), "roughness": 0.2, "emission": (0.2, 0.85, 1.0, 8.0)}})

R_W, WB, TRACK = 0.41, 2.50, 2.25
FLOOR = 0.55
STEER = (math.radians(-30), math.radians(30))
SX0, SX1, ST, SW = -1.66, -0.80, 1.86, 0.76
BOX_X = -1.24
SHELL = [(SX0, 0.40), (SX1, 0.40), (SX1, 1.02), (-0.98, ST - 0.02), (-1.50, ST), (SX0, ST - 0.14)]
HOOD = [(0.62, 0.74), (1.84, 0.74), (1.84, 0.80), (1.70, 0.83), (0.62, 0.90)]


def _wing(s):
    a = math.radians(35)
    hinge = (BOX_X + 0.02, s * SW, ST - 0.02)
    d = (0, s * math.cos(a), math.sin(a))
    c = (hinge[0], hinge[1] + d[1] * 0.47, hinge[2] + d[2] * 0.47)
    return {"name": f"solar_wing_{'l' if s > 0 else 'r'}", "c": c, "u": (1, 0, 0), "v": d, "w": 1.0, "h": 0.90,
            "normal": (0, -s * math.sin(a), math.cos(a)), "mass": 6.0, "back": "aluminium",
            "hinge": {"pos": hinge, "axis": (s, 0, 0), "limit": (math.radians(-35), math.radians(55)), "k": 300.0, "c": 30.0, "tau": 120.0}}


def _side(s):
    y = s * 0.75
    return [
        {"kind": "extrude", "name": f"shell_cheek_{'l' if s > 0 else 'r'}", "profile": SHELL, "y": tuple(sorted((s * (SW - 0.05), s * SW))),
         "mat": "brushed_panel"},
        {"kind": "rail", "name": f"shell_led_{'l' if s > 0 else 'r'}", "r": 0.012, "mat": "led_cyan",
         "points": [(SX1 + 0.01, s * (SW + 0.005), FLOOR), (SX1 + 0.01, s * (SW + 0.005), 1.02), (-0.97, s * (SW + 0.005), ST - 0.01),
                    (-1.50, s * (SW + 0.005), ST + 0.01), (SX0 - 0.005, s * (SW + 0.005), ST - 0.14)]},
        {"kind": "box", "name": f"side_sill_{'l' if s > 0 else 'r'}", "c": (-0.02, y, 0.55), "size": (1.52, 0.04, 0.34), "mat": "brushed_panel"},
        {"kind": "panel", "name": f"sill_grille_{'l' if s > 0 else 'r'}", "c": (0.30, s * 0.772, 0.55), "u": (1, 0, 0), "v": (0, 0, 1),
         "w": 0.55, "h": 0.22, "t": 0.006, "normal": (0, s, 0), "mat": "grating", "back": "anodised_dark"},
        {"kind": "rail", "name": f"roll_rail_{'l' if s > 0 else 'r'}", "r": 0.02, "mat": "aluminium",
         "points": [(0.72, s * 0.74, 0.88), (0.52, s * 0.74, 1.24), (-0.80, s * 0.74, 1.24)]},
        {"kind": "tube", "name": f"roll_post_{'l' if s > 0 else 'r'}", "p0": (0.10, s * 0.74, 0.72), "p1": (0.10, s * 0.74, 1.24), "r": 0.02,
         "mat": "aluminium"},
    ]


ROVER = {
    "wheel": {"r": R_W, "w": 0.25, "style": "mesh", "grousers": 32, "grouser_h": 0.012, "spokes": 8, "spoke_r": 0.016, "hub_frac": 0.30,
              "rim_frac": 0.80, "mass": 18.0, "grouser_mat": "titanium", "rim_mat": "aluminium", "hub_mat": "aluminium", "spoke_mat": "aluminium"},
    "wheels": K.four_wheels(WB, TRACK, STEER),
    "suspension": {"type": "double_wishbone", "arm": 0.34, "kingpin_off": 0.21, "lower_dz": -0.07, "upper_dz": 0.15, "travel": (0.12, 0.14),
                   "static_rad": 0.12, "spread": 0.28, "spring_mat": "titanium", "arm_mat": "aluminium"},
    "fenders": {"gap": 0.04, "arc": (-55, 100), "overhang": 0.05, "mat": "aluminium"},
    "parts": [
        {"kind": "cbox", "name": "tub", "c": (-0.05, 0, 0.47), "size": (3.10, 1.24, 0.24), "r": 0.04, "mat": "brushed_panel"},
        {"kind": "box", "name": "floor", "c": (-0.10, 0, FLOOR + 0.01), "size": (1.40, 1.46, 0.02), "mat": "grating"},
        {"kind": "cbox", "name": "cargo_box", "c": (1.33, 0, 0.52), "size": (0.98, 1.35, 0.44), "r": 0.03, "mat": "brushed_panel"},
        {"kind": "panel", "name": "cargo_lattice", "c": (1.825, 0, 0.52), "u": (0, 1, 0), "v": (0, 0, 1), "w": 1.25, "h": 0.38, "t": 0.01,
         "normal": (1, 0, 0), "mat": "grating", "back": "mli_gold"},
        {"kind": "extrude", "name": "hood", "profile": HOOD, "y": (-0.80, 0.80), "mat": "anodised_grey"},
        {"kind": "box", "name": "led_bar_front", "c": (1.85, 0, 0.775), "size": (0.025, 1.30, 0.03), "mat": "led_cyan"},
        {"kind": "box", "name": "led_bar_hood", "c": (0.66, 0, 0.91), "size": (0.03, 1.40, 0.02), "mat": "led_cyan"},
        {"kind": "extrude", "name": "rear_box", "profile": [(SX0, 0.40), (BOX_X, 0.40), (BOX_X, ST - 0.02), (-1.50, ST), (SX0, ST - 0.14)],
         "y": (-SW + 0.05, SW - 0.05), "mat": "brushed_panel"},
        {"kind": "panel", "name": "rear_box_face", "c": (BOX_X + 0.006, 0, 1.12), "u": (0, 1, 0), "v": (0, 0, 1), "w": 1.40, "h": 1.40, "t": 0.01,
         "normal": (1, 0, 0), "mat": "anodised_dark", "back": "anodised_dark"},
        {"kind": "extrude", "name": "shell_roof", "profile": [(-1.50, ST - 0.03), (-0.98, ST - 0.05), (-0.98, ST - 0.01), (-1.50, ST + 0.01)],
         "y": (-SW, SW), "mat": "brushed_panel"},
        {"kind": "box", "name": "led_bar_roof", "c": (-0.975, 0, ST - 0.025), "size": (0.02, 1.50, 0.025), "mat": "led_cyan"},
        {"kind": "panel", "name": "rear_box_lattice", "c": (SX0 - 0.006, 0, 1.05), "u": (0, 1, 0), "v": (0, 0, 1), "w": 1.20, "h": 0.80, "t": 0.01,
         "normal": (-1, 0, 0), "mat": "grating", "back": "anodised_dark"},
        {"kind": "box", "name": "led_bar_rear", "c": (SX0 - 0.01, 0, 1.52), "size": (0.02, 1.30, 0.025), "mat": "led_cyan"},
        *_side(1), *_side(-1),
        {"kind": "box", "name": "cargo_pallet", "c": (-0.30, 0, FLOOR + 0.30), "size": (0.80, 1.30, 0.56), "mat": "mli_gold", "variant": "Crew:cargo"},
    ],
    "crew": {"variant": "Crew:crewed", "x": -0.42, "floor_z": FLOOR, "seats_y": (0.43, -0.43), "style": "seat", "seat_h": 0.40,
             "console": (-0.05, 0, 1.02), "rail_mat": "handhold",
             "handholds": [[(-0.20, 0.70, FLOOR + 0.40), (-0.20, 0.70, FLOOR + 0.62), (-0.62, 0.70, FLOOR + 0.62), (-0.62, 0.70, FLOOR + 0.40)],
                           [(-0.20, -0.70, FLOOR + 0.40), (-0.20, -0.70, FLOOR + 0.62), (-0.62, -0.70, FLOOR + 0.62), (-0.62, -0.70, FLOOR + 0.40)],
                           [(0.05, 0.16, FLOOR + 0.42), (0.05, 0.16, FLOOR + 0.60), (-0.30, 0.16, FLOOR + 0.60)],
                           [(0.05, -0.16, FLOOR + 0.42), (0.05, -0.16, FLOOR + 0.60), (-0.30, -0.16, FLOOR + 0.60)]]},
    "masts": [{"name": "nav_mast", "base": (-1.02, 0.0, ST - 0.04), "h": 0.06, "r": 0.025, "head": (0.08, 0.32, 0.07), "cams": (-0.12, 0.12)}],
    "hga": {"base": (-1.42, 0, ST), "h": 0.60, "r": 0.25, "boresight": (1, 0, 0.25), "band": "S/X", "back": "aluminium"},
    "solar": [_wing(1), _wing(-1)],
    "lights": [((1.86, 0.58, 0.69), (1, 0, -0.05), 0.035, "headlight_l"), ((1.86, -0.58, 0.69), (1, 0, -0.05), 0.035, "headlight_r"),
               ((-0.97, 0.62, ST - 0.10), (1, 0, -0.35), 0.035, "work_light_l"), ((-0.97, -0.62, ST - 0.10), (1, 0, -0.35), 0.035, "work_light_r")],
    "sites": [
        ("cargo_box_lid", "chassis", (1.30, 0, 0.83), (0, 0, 1), "payload_interface", "Front cargo box under hood"),
        ("rear_box_top", "chassis", (-1.25, 0, ST + 0.01), (0, 0, 1), "payload_interface", "Rear shell roof"),
        ("tow_hitch", "chassis", (SX0 - 0.06, 0, 0.48), (-1, 0, 0), "hitch", "Rear tow hitch"),
    ],
    "imu": (0, 0, 0.55),
}

MASS = {
    "empty": {"mass": 1000.0, "com_z": 0.65, "source": "press: about 1 t"},
    "crewed": {"mass": 1540.0, "com_z": 0.85, "source": "estimate: + 2 suited crew (2 x 220 kg) + 100 kg"},
}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (3.5, 1.5, 1.0)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "cargo"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("brushed_panel",))
SIMPLE_TRIS = 20000
RENDER_VIEWS = K.views(3.6, 2.6, 2.8, centre_z=1.0)
