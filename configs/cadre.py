import math

import rover_kit as K

ASSET_ID = "cadre"
ASSET_PATH = "nasa_jpl/cadre/rover"
FAMILY = "rover"
TITLE = "NASA JPL CADRE rover"
DOC = ("One of the three NASA JPL CADRE (Cooperative Autonomous Distributed Robotic Exploration) suitcase-sized "
       "rovers for Intuitive Machines IM-3: 0.546 x 0.385 x 0.235 m and 8.6 kg, a silver-MLI deck over an amber "
       "thermally controlled housing and a ground-penetrating-radar antenna, two solar wings hinged on the long "
       "sides (folded on the deck when stowed), GPR sync and comm antennas, a sun sensor, front and rear stereo "
       "cameras behind flip-up covers, and four 6-spoke grousered aluminium wheels with skid steering.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"brass": {"color": (0.78, 0.62, 0.30), "roughness": 0.35, "metallic": 0.9}})

R_W, WB, TRACK = 0.078, 0.30, 0.32
DECK = 0.205
HINGE_Z = {1: 0.020, -1: 0.028}
WING_W = 0.21


def _wing(s):
    n = f"solar_wing_{'l' if s > 0 else 'r'}"
    y = s * 0.1925
    return [
        {"kind": "panel", "name": f"{n}_panel", "link": n, "c": (0, y + s * (WING_W / 2 + 0.005), DECK + HINGE_Z[s]), "u": (1, 0, 0), "v": (0, 1, 0),
         "w": 0.52, "h": WING_W, "t": 0.006, "normal": (0, 0, 1), "mat": "solar_cells", "back": "mli_silver"},
        {"kind": "tube", "name": f"{n}_hinge", "link": n, "p0": (-0.25, y, DECK + HINGE_Z[s]), "p1": (0.25, y, DECK + HINGE_Z[s]), "r": 0.004,
         "mat": "brass"},
    ]


def _camera_cover(tag, x, sgn):
    n = f"{tag}_camera_cover"
    return [
        {"kind": "box", "name": f"{tag}_camera_box", "c": (x - sgn * 0.01, 0, DECK - 0.035), "size": (0.02, 0.12, 0.05), "mat": "anodised_dark"},
        {"kind": "box", "name": f"{n}_plate", "link": n, "c": (x + sgn * 0.004, 0, DECK - 0.035), "size": (0.004, 0.13, 0.055), "mat": "kapton"},
    ]


ROVER = {
    "wheel": {"r": R_W, "w": 0.035, "style": "grouser", "grousers": 24, "grouser_h": 0.006, "spokes": 6, "spoke_curve": 0.0, "spoke_r": 0.0035,
              "hub_frac": 0.25, "rim_frac": 0.85, "mass": 0.25, "drum_mat": "aluminium", "grouser_mat": "aluminium", "spoke_mat": "aluminium",
              "segments": 32},
    "wheels": K.four_wheels(WB, TRACK, None),
    "suspension": {"type": "carrier", "kingpin_off": 0.035, "upper_dz": 0.09, "knuckle_t": 0.022, "knuckle_mat": "brass"},
    "links": [
        {"name": "solar_wing_l", "pos": (0, 0.1925, DECK + HINGE_Z[1]), "axis": (1, 0, 0), "limit": (0.0, math.pi), "role": "solar", "mass": 0.25,
         "drive": {"kind": "position", "stiffness": 2.0, "damping": 0.2, "max_force": 1.0}},
        {"name": "solar_wing_r", "pos": (0, -0.1925, DECK + HINGE_Z[-1]), "axis": (-1, 0, 0), "limit": (0.0, math.pi), "role": "solar", "mass": 0.25,
         "drive": {"kind": "position", "stiffness": 2.0, "damping": 0.2, "max_force": 1.0}},
        {"name": "front_camera_cover", "pos": (0.260, 0, DECK - 0.008), "axis": (0, -1, 0), "limit": (0.0, 1.60), "role": "hatch", "mass": 0.02,
         "drive": {"kind": "position", "stiffness": 0.2, "damping": 0.02, "max_force": 0.2}},
        {"name": "rear_camera_cover", "pos": (-0.260, 0, DECK - 0.008), "axis": (0, 1, 0), "limit": (0.0, 1.60), "role": "hatch", "mass": 0.02,
         "drive": {"kind": "position", "stiffness": 0.2, "damping": 0.02, "max_force": 0.2}},
    ],
    "parts": [
        {"kind": "box", "name": "deck", "c": (0, 0, DECK - 0.0075), "size": (0.546, 0.385, 0.015), "mat": "mli_silver"},
        {"kind": "box", "name": "thermal_box", "c": (0, 0, DECK - 0.065), "size": (0.40, 0.22, 0.10), "mat": "mli_silver"},
        {"kind": "box", "name": "motor_controller", "c": (0.0, 0.0, DECK - 0.03), "size": (0.46, 0.30, 0.03), "mat": "kapton"},
        *[{"kind": "box", "name": f"wing_hinge_block_{k}", "c": (x, s * 0.185, DECK + 0.006), "size": (0.03, 0.02, 0.012), "mat": "brass"}
          for k, (x, s) in enumerate(((0.2, 1), (-0.2, 1), (0.2, -1), (-0.2, -1)))],
        {"kind": "box", "name": "gpr_antenna", "c": (0, 0, DECK - 0.120), "size": (0.30, 0.15, 0.008), "mat": "composite"},
        {"kind": "tube", "name": "gpr_sync_0", "p0": (0.10, 0.08, DECK), "p1": (0.10, 0.08, DECK + 0.15), "r": 0.003, "mat": "white_panel"},
        {"kind": "tube", "name": "gpr_sync_1", "p0": (-0.10, -0.08, DECK), "p1": (-0.10, -0.08, DECK + 0.15), "r": 0.003, "mat": "white_panel"},
        {"kind": "tube", "name": "comm_antenna", "p0": (-0.05, 0.05, DECK), "p1": (-0.05, 0.05, DECK + 0.06), "r": 0.005, "mat": "yellow"},
        {"kind": "box", "name": "sun_sensor", "c": (0.06, -0.06, DECK + 0.007), "size": (0.025, 0.025, 0.014), "mat": "blue_paint"},
        *[{"kind": "box", "name": f"wheel_bracket_{k}", "c": (x, y * 0.15, DECK - 0.04), "size": (0.03, 0.03, 0.06), "mat": "brass"}
          for k, (x, y) in enumerate(((0.15, 1), (0.15, -1), (-0.15, 1), (-0.15, -1)))],
        *_wing(1), *_wing(-1),
        *_camera_cover("front", 0.258, 1), *_camera_cover("rear", -0.258, -1),
    ],
    "masts": [{"name": "front_stereo", "base": (0.247, 0, DECK - 0.035), "h": 0.0, "pan_tilt": False, "head": (0.002, 0.10, 0.03),
               "cams": (-0.035, 0.035), "foot": None, "focal_mm": 3.0, "source": "CADRE front stereo pair (optics estimated)"},
              {"name": "rear_stereo", "base": (-0.247, 0, DECK - 0.035), "h": 0.0, "pan_tilt": False, "head": (0.002, 0.10, 0.03),
               "cams": (-0.035, 0.035), "foot": None, "focal_mm": 3.0, "forward": (-1, 0, 0), "source": "CADRE rear stereo pair (optics estimated)"}],
    "sites": [("tether_point", "chassis", (0, 0, DECK + 0.01), (0, 0, 1), "handling", "Deployer tether attach (lowered ~1.2 m from IM-3)"),
              ("gpr_phase_centre", "chassis", (0, 0, DECK - 0.124), (0, 0, -1), "sensor", "Ground-penetrating radar antenna")],
    "imu": (0, 0, 0.17),
}

MASS = {"flight": {"mass": 8.6, "com_z": 0.16, "source": "JPL fact sheet: 8.6 kg"}}
DEFAULT_MASS_STATE = "flight"
GEOMETRY_VARIANTS = {"Solar": ["deployed", "stowed"]}
GEOMETRY_VARIANT_JOINTS = {"Solar": {"stowed": {"solar_wing_l": math.pi, "solar_wing_r": math.pi}}}
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (0.55, 0.39, 0.12)

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("mli_silver", "kapton"))
SIMPLE_TRIS = 8000
RENDER_VIEWS = K.views(0.55, 0.80, 0.40, centre_z=0.14)
