import math

import rover_kit as K

ASSET_ID = "viper"
ASSET_PATH = "nasa/viper/rover"
FAMILY = "rover"
TITLE = "NASA VIPER"
DOC = ("NASA VIPER (Volatiles Investigating Polar Exploration Rover), flight design for Blue Moon MK1 delivery: 1.7 x 1.7 "
       "x 2.5 m and 447 kg roving, a silver-MLI body with solar arrays hanging from the port, starboard and aft deck "
       "edges, deck radiators, a front mast with a gimballed navigation camera and light bar at 2.0 m and a high-gain "
       "antenna at 2.3 m, the TRIDENT 1 m drill on the front-right corner, and four 0.5 m grousered wheels, each on an "
       "active swing-arm suspension (wheel walking, 7-43 cm clearance) with +/-50 deg steering and hub drive.")

TEXTURE_SETS, MATERIALS = K.materials(overrides={"instrument_yellow": {"color": (0.85, 0.66, 0.08), "roughness": 0.5, "metallic": 0.3}})

R_W, WB, TRACK = 0.25, 1.00, 1.33
DECK = 1.25
HALF = 0.80
ARR_BOT = 0.27
MAST_X = 0.60
DRILL = (0.75, -0.42)


def _arrays():
    h = DECK - 0.03 - ARR_BOT
    zc = ARR_BOT + h / 2
    out = []
    for n, s in (("port", 1), ("starboard", -1)):
        out.append({"kind": "panel", "name": f"solar_{n}", "c": (0, s * (HALF + 0.02), zc), "u": (1, 0, 0), "v": (0, -s * 0.05, 1), "w": 1.64, "h": h,
                    "t": 0.025, "normal": (0, s, 0.05), "mat": "solar_cells", "back": "mli_silver"})
        out.append({"kind": "beam", "name": f"solar_{n}_frame_low", "p0": (-0.82, s * (HALF + 0.045), ARR_BOT), "p1": (0.82, s * (HALF + 0.045), ARR_BOT),
                    "w": 0.03, "h": 0.03, "mat": "aluminium"})
    out.append({"kind": "panel", "name": "solar_aft", "c": (-(HALF + 0.02), 0, zc), "u": (0, 1, 0), "v": (0.05, 0, 1), "w": 1.64, "h": h, "t": 0.025,
                "normal": (-1, 0, 0.05), "mat": "solar_cells", "back": "mli_silver"})
    out.append({"kind": "beam", "name": "solar_aft_frame_low", "p0": (-(HALF + 0.045), -0.82, ARR_BOT), "p1": (-(HALF + 0.045), 0.82, ARR_BOT),
                "w": 0.03, "h": 0.03, "mat": "aluminium"})
    return out


def _body():
    return [
        {"kind": "cbox", "name": "deck_body", "c": (0, 0, DECK - 0.16), "size": (2 * HALF, 2 * HALF, 0.32), "r": 0.03, "mat": "mli_silver"},
        {"kind": "cbox", "name": "warm_box", "c": (-0.05, 0, 0.64), "size": (1.05, 0.78, 0.62), "r": 0.03, "mat": "mli_silver"},
        {"kind": "box", "name": "front_apron", "c": (HALF - 0.01, 0, 0.83), "size": (0.02, 2 * HALF - 0.02, 0.70), "mat": "mli_silver"},
        {"kind": "box", "name": "instrument_bay", "c": (0.45, 0.05, 0.40), "size": (0.34, 0.50, 0.20), "mat": "instrument_yellow"},
        {"kind": "box", "name": "nirvss_window", "c": (0.62, 0.05, 0.43), "size": (0.01, 0.16, 0.06), "mat": "glass"},
        {"kind": "panel", "name": "deck_radiator_fwd", "c": (0.15, 0.20, DECK + 0.006), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.80, "h": 1.10,
         "t": 0.01, "mat": "radiator", "back": "mli_silver"},
        {"kind": "panel", "name": "deck_radiator_aft", "c": (-0.50, 0, DECK + 0.006), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.55, "h": 1.50,
         "t": 0.01, "mat": "radiator", "back": "mli_silver"},
        {"kind": "box", "name": "star_tracker", "c": (-0.10, -0.55, DECK + 0.08), "size": (0.14, 0.14, 0.16), "mat": "anodised_dark"},
        {"kind": "tube", "name": "star_tracker_baffle", "p0": (-0.10, -0.55, DECK + 0.16), "p1": (-0.14, -0.59, DECK + 0.30), "r": 0.045,
         "mat": "anodised_dark"},
        {"kind": "tube", "name": "lga", "p0": (-0.55, 0.60, DECK), "p1": (-0.55, 0.60, DECK + 0.30), "r": 0.03, "mat": "white_panel"},
        {"kind": "cbox", "name": "mast_column", "c": (MAST_X, 0, DECK + 0.30), "size": (0.15, 0.15, 0.60), "r": 0.02, "mat": "mli_silver"},
        {"kind": "box", "name": "trident_tower", "c": (DRILL[0], DRILL[1], 0.98), "size": (0.22, 0.22, 1.10), "mat": "aluminium"},
        {"kind": "box", "name": "trident_motor", "c": (DRILL[0], DRILL[1], 1.58), "size": (0.18, 0.18, 0.12), "mat": "anodised_dark"},
        {"kind": "beam", "name": "trident_brace", "p0": (DRILL[0] - 0.05, DRILL[1] + 0.10, 1.45), "p1": (MAST_X, -0.07, DECK + 0.05), "w": 0.04,
         "h": 0.04, "mat": "aluminium"},
        {"kind": "tube", "name": "trident_drill_rod", "link": "trident_drill", "p0": (DRILL[0], DRILL[1], 0.18), "p1": (DRILL[0], DRILL[1], 1.48),
         "r": 0.02, "mat": "titanium"},
        {"kind": "tube", "name": "trident_bit", "link": "trident_drill", "p0": (DRILL[0], DRILL[1], 0.12), "p1": (DRILL[0], DRILL[1], 0.20),
         "r": 0.026, "r1": 0.012, "mat": "anodised_dark"},
        {"kind": "box", "name": "trident_carriage", "link": "trident_drill", "c": (DRILL[0], DRILL[1], 1.46), "size": (0.12, 0.12, 0.08),
         "mat": "anodised_grey"},
    ]


ROVER = {
    "wheel": {"r": R_W, "w": 0.20, "style": "grouser", "grousers": 20, "grouser_h": 0.025, "spokes": 8, "spoke_curve": 0.5, "spoke_r": 0.008,
              "hub_frac": 0.30, "rim_frac": 0.86, "mass": 8.0, "drum_mat": "aluminium", "grouser_mat": "aluminium", "spoke_mat": "aluminium",
              "hub_mat": "anodised_dark"},
    "wheels": K.four_wheels(WB, TRACK, (math.radians(-50), math.radians(50))),
    "suspension": {"type": "trailing_arm", "active": True, "arm_dx": 0.30, "pivot_dz": 0.30, "kingpin_off": 0.15, "travel": (0.19, 0.19),
                   "static_rad": 0.10, "beam": 0.06, "arm_mat": "mli_silver", "knuckle_mat": "aluminium"},
    "links": [
        {"name": "trident_drill", "type": "prismatic", "pos": (DRILL[0], DRILL[1], 1.46), "axis": (0, 0, -1), "limit": (0.0, 1.10), "role": "arm",
         "mass": 4.0, "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 500.0}},
    ],
    "parts": [*_body(), *_arrays()],
    "masts": [{"name": "nav_mast", "base": (MAST_X, 0, DECK + 0.60), "h": 0.03, "r": 0.06, "head": (0.12, 0.70, 0.10), "cams": (-0.12, 0.12),
               "head_mat": "mli_silver", "foot": None, "focal_mm": 6.0, "source": "VIPER NavCam stereo pair (optics estimated)"}],
    "hga": {"base": (MAST_X, 0, 2.06), "h": 0.12, "r": 0.18, "mast_r": 0.025, "boresight": (1, 0, 0.5), "band": "X", "depth": 0.25,
            "front": "white_panel", "back": "mli_silver"},
    "lights": [
        ((MAST_X + 0.06, 0.29, 2.0), (1, 0, -0.35), 0.045, "nav_light_l", "nav_mast_tilt"),
        ((MAST_X + 0.06, -0.29, 2.0), (1, 0, -0.35), 0.045, "nav_light_r", "nav_mast_tilt"),
        ((HALF, 0.55, 0.60), (1, 0.3, -0.5), 0.03, "haz_light_fl"),
        ((HALF, -0.20, 0.60), (1, -0.3, -0.5), 0.03, "haz_light_fr"),
        ((HALF, 0.20, 0.60), (1, 0, -0.5), 0.03, "haz_light_fc"),
        ((-(HALF + 0.035), 0.45, 0.24), (-1, 0, -0.5), 0.03, "haz_light_al"),
        ((-(HALF + 0.035), -0.45, 0.24), (-1, 0, -0.5), 0.03, "haz_light_ar"),
    ],
    "sites": [("trident_bit", "trident_drill", (DRILL[0], DRILL[1], 0.12), (0, 0, -1), "tool", "TRIDENT drill bit (1 m depth)"),
              ("haz_cam_front", "chassis", (HALF + 0.01, 0.40, 0.60), (1, 0, -0.5), "sensor", "Front hazard camera pair (estimated)"),
              ("lift_point", "chassis", (0, 0, DECK), (0, 0, 1), "handling", "Deck lift point")],
    "imu": (0, 0, 0.9),
}

MASS = {"roving": {"mass": 447.0, "com_z": 0.80, "source": "NASA: 447 kg roving"},
        "launch": {"mass": 490.0, "com_z": 0.80, "source": "NASA: 490 kg at launch"}}
DEFAULT_MASS_STATE = "roving"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (1.6, 1.6, 1.0)

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("mli_silver",))
SIMPLE_TRIS = 16000
RENDER_VIEWS = {**K.views(1.7, 1.7, 2.5, centre_z=1.1), "front": ((5.5, 0.0, 1.4), (0, 0, 1.2), 35)}
