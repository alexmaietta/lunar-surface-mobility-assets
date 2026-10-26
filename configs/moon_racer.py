import math

import rover_kit as K

ASSET_ID = "moon_racer"
ASSET_PATH = "intuitive_machines/moon_racer/rover"
FAMILY = "rover"
TITLE = "Intuitive Machines Moon RACER"
DOC = ("Intuitive Machines Moon RACER Lunar Terrain Vehicle (2024-25 LTV bid with AVL, Boeing, Michelin, Northrop "
       "Grumman and Roush; not selected in 2026): 4.34 m long with a white hood and blue stripe, two seats with a "
       "joystick under a black sensor tower carrying stereo cameras, orange beacons and a dish, a rear deck with a "
       "robotic arm, two vertical solar panels and storage boxes, a tow hitch, and four Michelin airless tyres on "
       "double-wishbone suspension with blue coil-over dampers and front steering.")

TEXTURE_SETS, MATERIALS = K.materials()

R_W, WB, TRACK = 0.40, 2.70, 2.20
FLOOR, DECK = 0.64, 0.68
STEER = (math.radians(-35), math.radians(35))
HOOD = [(2.25, 0.40), (2.25, 0.58), (1.60, 0.72), (0.85, 0.76), (0.85, 0.40)]
TOWER = dict(x=(-0.55, 0.40), z=(1.64, 2.20), hw=1.10)
TX = (TOWER["x"][0] + TOWER["x"][1]) / 2


def _stripe(name, a, b, w=0.40):
    ax = (b[0] - a[0], 0, b[1] - a[1])
    L = math.hypot(ax[0], ax[2])
    return {"kind": "obox", "name": name, "c": ((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2 + 0.008), "ax": ax, "ay": (0, 1, 0), "size": (L, w, 0.02),
            "mat": "blue_paint"}


ROVER = {
    "wheel": {"r": R_W, "w": 0.28, "style": "spring", "grousers": 20, "spokes": 24, "spoke_curve": 0.25, "hub_frac": 0.40, "mass": 22.0,
              "rim_mat": "anodised_dark", "hub_mat": "anodised_dark", "spoke_mat": "anodised_dark"},
    "wheels": K.four_wheels(WB, TRACK, STEER, rear_steer=False),
    "suspension": {"type": "double_wishbone", "arm": 0.36, "kingpin_off": 0.24, "lower_dz": -0.06, "upper_dz": 0.16, "travel": (0.12, 0.15),
                   "static_rad": 0.12, "spread": 0.30, "spring_mat": "blue_paint"},
    "fenders": {"gap": 0.04, "arc": (-40, 75), "overhang": 0.02, "mat": "anodised_dark"},
    "parts": [
        {"kind": "cbox", "name": "tub", "c": (0.05, 0, 0.48), "size": (3.70, 1.14, 0.30), "r": 0.04, "mat": "white_panel"},
        {"kind": "extrude", "name": "hood", "profile": HOOD, "y": (-0.85, 0.85), "mat": "white_panel"},
        _stripe("hood_stripe_front", HOOD[1], HOOD[2]),
        _stripe("hood_stripe", HOOD[2], HOOD[3]),
        {"kind": "box", "name": "dash", "c": (0.90, 0, 0.86), "size": (0.10, 1.40, 0.20), "mat": "white_panel"},
        {"kind": "box", "name": "dash_badge", "c": (0.955, 0, 0.88), "size": (0.01, 0.50, 0.14), "mat": "blue_paint"},
        {"kind": "box", "name": "front_bumper", "c": (2.29, 0, 0.42), "size": (0.10, 1.20, 0.15), "mat": "anodised_dark"},
        {"kind": "box", "name": "front_light_bar", "c": (2.255, 0, 0.53), "size": (0.02, 1.10, 0.03), "mat": "lamp"},
        {"kind": "box", "name": "front_sensor_box", "c": (2.30, -0.30, 0.30), "size": (0.16, 0.30, 0.14), "mat": "anodised_dark"},
        {"kind": "box", "name": "floor", "c": (0.30, 0, FLOOR - 0.005), "size": (1.20, 1.60, 0.03), "mat": "grey_panel"},
        {"kind": "extrude", "name": "side_panel_l", "y": (0.78, 0.82), "mat": "white_panel",
         "profile": [(-0.55, FLOOR - 0.10), (0.85, FLOOR - 0.10), (0.85, 0.80), (0.55, 1.02), (-0.55, 1.02)]},
        {"kind": "extrude", "name": "side_panel_r", "y": (-0.82, -0.78), "mat": "white_panel",
         "profile": [(-0.55, FLOOR - 0.10), (0.85, FLOOR - 0.10), (0.85, 0.80), (0.55, 1.02), (-0.55, 1.02)]},
        {"kind": "box", "name": "side_trim_l", "c": (0.15, 0.825, 0.70), "size": (1.20, 0.01, 0.05), "mat": "blue_paint"},
        {"kind": "box", "name": "side_trim_r", "c": (0.15, -0.825, 0.70), "size": (1.20, 0.01, 0.05), "mat": "blue_paint"},
        {"kind": "beam", "name": "tower_post_fl", "p0": (0.95, 0.80, 0.80), "p1": (0.36, 1.02, TOWER["z"][0] + 0.05), "w": 0.06, "h": 0.06,
         "mat": "anodised_dark"},
        {"kind": "beam", "name": "tower_post_fr", "p0": (0.95, -0.80, 0.80), "p1": (0.36, -1.02, TOWER["z"][0] + 0.05), "w": 0.06, "h": 0.06,
         "mat": "anodised_dark"},
        {"kind": "beam", "name": "tower_post_rl", "p0": (-0.75, 0.80, DECK), "p1": (-0.50, 1.02, TOWER["z"][0] + 0.05), "w": 0.06, "h": 0.06,
         "mat": "anodised_dark"},
        {"kind": "beam", "name": "tower_post_rr", "p0": (-0.75, -0.80, DECK), "p1": (-0.50, -1.02, TOWER["z"][0] + 0.05), "w": 0.06, "h": 0.06,
         "mat": "anodised_dark"},
        {"kind": "box", "name": "sensor_tower", "c": (TX, 0, sum(TOWER["z"]) / 2), "size": (TOWER["x"][1] - TOWER["x"][0], 2 * TOWER["hw"],
                                                                                         TOWER["z"][1] - TOWER["z"][0]), "mat": "anodised_dark"},
        {"kind": "extrude", "name": "tower_hopper", "y": (-0.80, 0.80), "mat": "anodised_dark",
         "profile": [(-0.55, 1.18), (-0.40, 1.18), (-0.08, TOWER["z"][0]), (-0.55, TOWER["z"][0])]},
        {"kind": "box", "name": "tower_rail_front", "c": (TOWER["x"][1] + 0.02, 0, TOWER["z"][1] - 0.04), "size": (0.03, 2.20, 0.03),
         "mat": "blue_paint"},
        {"kind": "obox", "name": "tower_cam_box_l", "c": (0.44, 0.62, 1.70), "ax": (1, 0.3, 0), "ay": (0, 0, 1), "size": (0.20, 0.30, 0.22),
         "mat": "white_panel"},
        {"kind": "obox", "name": "tower_cam_box_r", "c": (0.44, -0.62, 1.70), "ax": (1, -0.3, 0), "ay": (0, 0, 1), "size": (0.20, 0.30, 0.22),
         "mat": "white_panel"},
        {"kind": "box", "name": "tower_cam_lens_l", "c": (0.55, 0.62, 1.70), "size": (0.02, 0.16, 0.08), "mat": "lens"},
        {"kind": "box", "name": "tower_cam_lens_r", "c": (0.55, -0.62, 1.70), "size": (0.02, 0.16, 0.08), "mat": "lens"},
        {"kind": "box", "name": "stereo_pod", "c": (0.48, -0.10, 1.80), "size": (0.16, 0.42, 0.24), "mat": "blue_paint"},
        {"kind": "disc", "name": "stereo_lens_0", "c": (0.56, -0.00, 1.82), "n": (1, 0, 0), "r": 0.045, "t": 0.02, "mat": "lens"},
        {"kind": "disc", "name": "stereo_lens_1", "c": (0.56, -0.20, 1.82), "n": (1, 0, 0), "r": 0.045, "t": 0.02, "mat": "lens"},
        {"kind": "box", "name": "top_cam_0", "c": (0.20, -0.08, TOWER["z"][1] + 0.16), "size": (0.20, 0.22, 0.20), "mat": "anodised_dark"},
        {"kind": "tube", "name": "top_cam_0_post", "p0": (0.20, -0.08, TOWER["z"][1]), "p1": (0.20, -0.08, TOWER["z"][1] + 0.06), "r": 0.03,
         "mat": "blue_paint"},
        {"kind": "box", "name": "top_cam_1", "c": (0.15, -0.55, TOWER["z"][1] + 0.12), "size": (0.30, 0.26, 0.16), "mat": "anodised_dark"},
        {"kind": "tube", "name": "beacon_l", "p0": (0.20, 0.30, TOWER["z"][1]), "p1": (0.20, 0.30, TOWER["z"][1] + 0.20), "r": 0.07, "mat": "beacon"},
        {"kind": "tube", "name": "beacon_r", "p0": (0.25, -0.95, TOWER["z"][1]), "p1": (0.25, -0.95, TOWER["z"][1] + 0.20), "r": 0.07, "mat": "beacon"},
        {"kind": "box", "name": "dish_base", "c": (-0.20, 0.70, TOWER["z"][1] + 0.06), "size": (0.36, 0.32, 0.12), "mat": "white_panel"},
        {"kind": "box", "name": "eva_tool_box_l", "c": (-0.75, 0.42, DECK + 0.22), "size": (0.40, 0.70, 0.44), "mat": "white_panel"},
        {"kind": "box", "name": "eva_tool_box_r", "c": (-0.75, -0.42, DECK + 0.22), "size": (0.40, 0.70, 0.44), "mat": "white_panel"},
        {"kind": "box", "name": "side_locker_l", "c": (-0.75, 0.98, 1.12), "size": (0.55, 0.32, 0.26), "mat": "anodised_dark"},
        {"kind": "box", "name": "side_locker_r", "c": (-0.75, -0.98, 1.12), "size": (0.55, 0.32, 0.26), "mat": "anodised_dark"},
        {"kind": "box", "name": "rear_deck", "c": (-1.45, 0, DECK + 0.01), "size": (1.20, 1.60, 0.03), "mat": "grating"},
        {"kind": "box", "name": "rear_deck_stripe", "c": (-1.45, 0, DECK + 0.026), "size": (1.20, 0.30, 0.004), "mat": "blue_paint"},
        {"kind": "box", "name": "storage_box_l", "c": (-1.20, 0.58, DECK + 0.19), "size": (0.60, 0.40, 0.36), "mat": "anodised_dark"},
        {"kind": "box", "name": "storage_box_r", "c": (-1.20, -0.58, DECK + 0.17), "size": (0.55, 0.40, 0.32), "mat": "white_panel"},
        {"kind": "tube", "name": "arm_pedestal", "p0": (-1.55, 0, DECK), "p1": (-1.55, 0, DECK + 0.40), "r": 0.08, "mat": "anodised_dark"},
        {"kind": "box", "name": "tow_hitch", "c": (-2.02, 0, 0.42), "size": (0.12, 0.10, 0.08), "mat": "titanium"},
        {"kind": "box", "name": "rear_bumper", "c": (-1.92, 0, 0.42), "size": (0.08, 1.00, 0.12), "mat": "anodised_dark"},
    ],
    "crew": {"variant": "Crew:crewed", "x": 0.35, "floor_z": FLOOR, "seat_h": 0.30, "seats_y": (0.42, -0.42), "style": "seat",
             "console": (0.80, 0, 1.08),
             "handholds": [[(0.90, 0.72, 0.86), (0.80, 0.70, 1.15), (0.55, 0.70, 1.15)], [(0.90, -0.72, 0.86), (0.80, -0.70, 1.15), (0.55, -0.70, 1.15)]],
             "rail_mat": "anodised_dark"},
    "hga": {"base": (-0.20, 0.70, TOWER["z"][1] + 0.12), "h": 0.04, "r": 0.22, "boresight": (0.3, 0, 1), "band": "S", "front": "radome",
            "back": "white_panel"},
    "solar": [{"name": f"solar_panel_{n}", "c": (-1.85, s * 0.42, DECK + 0.78), "u": (0, 1, 0), "v": (0, 0, 1), "w": 0.80, "h": 1.30,
               "normal": (-1, 0, 0), "mass": 5.0, "back": "white_panel"} for n, s in (("l", 1), ("r", -1))],
    "arm": {"base": (-1.55, 0, DECK + 0.40), "lengths": (0.70, 0.65, 0.20), "r": 0.04, "stow_dir": (1, 0, 0), "mass": 30.0, "tau": 160.0},
    "lights": [((2.30, 0.45, 0.47), (1, 0, -0.05), 0.045, "headlight_l"), ((2.30, -0.45, 0.47), (1, 0, -0.05), 0.045, "headlight_r"),
               ((0.42, 0.95, 1.66), (1, 0, -0.3), 0.05, "tower_light_l"), ((0.42, -0.95, 1.66), (1, 0, -0.3), 0.05, "tower_light_r"),
               ((-0.56, 0.0, 1.70), (-1, 0, -0.5), 0.05, "deck_light")],
    "sites": [
        ("rear_deck", "chassis", (-1.45, 0, DECK + 0.03), (0, 0, 1), "payload_interface", "Rear payload deck (400 kg)"),
        ("tow_hitch", "chassis", (-2.08, 0, 0.42), (-1, 0, 0), "hitch", "Trailer hitch (800 kg trailer)"),
        ("tower_hazcam_l", "chassis", (0.56, 0.62, 1.70), (1, 0, 0), "sensor", "Tower hazard camera pod"),
        ("tower_hazcam_r", "chassis", (0.56, -0.62, 1.70), (1, 0, 0), "sensor", "Tower hazard camera pod"),
        ("tower_stereo", "chassis", (0.58, -0.10, 1.82), (1, 0, 0), "sensor", "Tower stereo navigation camera pod"),
        ("beacon_l", "chassis", (0.20, 0.30, TOWER["z"][1] + 0.20), (0, 0, 1), "light", "Orange beacon",
         {"radius_m": 0.07, "intensity": 3000.0, "colour_k": 2000.0}),
        ("beacon_r", "chassis", (0.25, -0.95, TOWER["z"][1] + 0.20), (0, 0, 1), "light", "Orange beacon",
         {"radius_m": 0.07, "intensity": 3000.0, "colour_k": 2000.0}),
    ],
    "imu": (0, 0, 0.6),
}

MASS = {
    "empty": {"mass": 1100.0, "com_z": 0.70, "source": "estimate: 1-1.2 t (not published)"},
    "crewed": {"mass": 1650.0, "com_z": 0.85, "source": "estimate: + 2 suited crew (550 kg)"},
    "loaded": {"mass": 2050.0, "com_z": 0.85, "com_x": -0.2, "source": "estimate: + 2 suited crew (550 kg) + 400 kg rear-deck cargo"},
}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (4.0, 1.6, 0.9)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "uncrewed"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics()
SIMPLE_TRIS = 20000
RENDER_VIEWS = K.views(4.34, 2.5, 2.6, centre_z=1.0)
