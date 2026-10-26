import math

import rover_kit as K

ASSET_ID = "ltv_concept"
ASSET_PATH = "concepts/ltv/rover"
FAMILY = "rover"
TITLE = "Generic Lunar Terrain Vehicle (concept)"
DOC = ("Generic Artemis-class Lunar Terrain Vehicle built from the common features of the 2020s LTV designs: four "
       "airless spring-tyre wheels on double-wishbone active suspension with coilover struts, independent steering "
       "and hub-motor drive on every corner, a battery/avionics tub with deck radiators, two seated crew stations "
       "with a hand controller (or an uncrewed cargo pallet), a tilting rear solar array, a pan-tilt navigation mast, "
       "a gimballed high-gain antenna, front hazard cameras, side boarding steps, eight named lamps and a five-axis "
       "robotic arm. Payload states follow the NASA LTV requirement: 2 suited crew (550 kg) + 250 kg cargo, or "
       "1,600 kg uncrewed.")

TEXTURE_SETS, MATERIALS = K.materials()

WB, TRACK, R_W = 2.60, 2.40, 0.45
STEER = (math.radians(-60), math.radians(60))
TUB = dict(x=(-1.75, 1.75), hw=0.50, z=(0.38, 0.82))
DECK_Z = TUB["z"][1] + 0.03

ROVER = {
    "wheel": {"r": R_W, "w": 0.30, "style": "spring", "grousers": 22, "spokes": 12, "mass": 30.0},
    "wheels": [
        {"name": "fl", "x": WB / 2, "y": TRACK / 2, "steer": STEER},
        {"name": "fr", "x": WB / 2, "y": -TRACK / 2, "steer": STEER},
        {"name": "rl", "x": -WB / 2, "y": TRACK / 2, "steer": STEER},
        {"name": "rr", "x": -WB / 2, "y": -TRACK / 2, "steer": STEER},
    ],
    "suspension": {"type": "double_wishbone", "active": True, "arm": 0.42, "kingpin_off": 0.25, "lower_dz": -0.08,
                   "upper_dz": 0.20, "travel": (0.18, 0.16), "static_rad": 0.12, "spread": 0.36},
    "fenders": {"gap": 0.05, "arc": (-55, 75), "mat": "white_panel"},
    "parts": [
        {"kind": "cbox", "name": "tub", "c": (0, 0, sum(TUB["z"]) / 2), "size": (3.5, 2 * TUB["hw"], TUB["z"][1] - TUB["z"][0]),
         "r": 0.08, "mat": "white_panel"},
        {"kind": "box", "name": "belly_pan", "c": (0, 0, TUB["z"][0] - 0.01), "size": (3.3, 0.9, 0.02), "mat": "grey_panel"},
        {"kind": "box", "name": "deck", "c": (0, 0, DECK_Z - 0.015), "size": (3.6, 1.60, 0.03), "mat": "grey_panel"},
        {"kind": "beam", "name": "deck_rail_l", "p0": (-1.8, 0.80, DECK_Z - 0.03), "p1": (1.8, 0.80, DECK_Z - 0.03), "w": 0.06, "h": 0.08,
         "mat": "anodised_grey"},
        {"kind": "beam", "name": "deck_rail_r", "p0": (-1.8, -0.80, DECK_Z - 0.03), "p1": (1.8, -0.80, DECK_Z - 0.03), "w": 0.06, "h": 0.08,
         "mat": "anodised_grey"},
        {"kind": "box", "name": "front_bumper", "c": (1.80, 0, 0.62), "size": (0.10, 1.40, 0.18), "mat": "anodised_grey"},
        {"kind": "box", "name": "rear_bumper", "c": (-1.80, 0, 0.62), "size": (0.10, 1.40, 0.18), "mat": "anodised_grey"},
        {"kind": "box", "name": "battery_box", "c": (-0.90, 0, DECK_Z + 0.16), "size": (1.10, 1.30, 0.32), "mat": "white_panel"},
        {"kind": "panel", "name": "battery_radiator", "c": (-0.90, 0, DECK_Z + 0.33), "u": (1, 0, 0), "v": (0, 1, 0), "w": 1.05, "h": 1.25,
         "t": 0.01, "mat": "radiator", "back": "white_panel"},
        {"kind": "box", "name": "avionics_box", "c": (0.10, 0, DECK_Z + 0.12), "size": (0.40, 0.60, 0.24), "mat": "mli_gold"},
        {"kind": "box", "name": "cargo_pallet", "c": (0.95, 0, DECK_Z + 0.03), "size": (1.30, 1.50, 0.06), "mat": "grey_panel",
         "variant": "Crew:uncrewed"},
        {"kind": "box", "name": "cargo_box_0", "c": (1.25, 0.38, DECK_Z + 0.26), "size": (0.60, 0.60, 0.40), "mat": "beta_white",
         "variant": "Crew:uncrewed"},
        {"kind": "box", "name": "cargo_box_1", "c": (0.65, -0.35, DECK_Z + 0.21), "size": (0.55, 0.65, 0.30), "mat": "mli_silver",
         "variant": "Crew:uncrewed"},
        *[{"kind": "box", "name": f"hazcam_{sd}", "c": (1.87, s * 0.20, 0.78), "size": (0.08, 0.16, 0.08), "mat": "anodised_dark"}
          for sd, s in (("l", 1), ("r", -1))],
        *[{"kind": "disc", "name": f"hazcam_{sd}_lens", "c": (1.91, s * 0.20, 0.78), "n": (1, 0, 0), "r": 0.025, "t": 0.01, "mat": "lens"}
          for sd, s in (("l", 1), ("r", -1))],
        *[{"kind": "box", "name": f"side_step_{sd}", "c": (0.95, s * 0.86, 0.46), "size": (0.45, 0.20, 0.03), "mat": "grating"}
          for sd, s in (("l", 1), ("r", -1))],
        *[{"kind": "beam", "name": f"side_step_{sd}_hanger_{k}", "p0": (x, s * 0.80, DECK_Z - 0.04), "p1": (x, s * 0.88, 0.46), "w": 0.03,
           "h": 0.03, "mat": "anodised_grey"} for sd, s in (("l", 1), ("r", -1)) for k, x in enumerate((0.76, 1.14))],
        *[{"kind": "tube", "name": f"tie_down_{k}", "p0": (x, -0.78, DECK_Z), "p1": (x, -0.78, DECK_Z + 0.05), "r": 0.02, "mat": "yellow"}
          for k, x in enumerate((-1.6, -0.2, 0.3, 1.6))],
        {"kind": "tube", "name": "mast_light_bar", "p0": (1.69, -0.27, DECK_Z + 0.88), "p1": (1.69, 0.27, DECK_Z + 0.88), "r": 0.02,
         "mat": "anodised_dark"},
        {"kind": "box", "name": "battery_box_mli", "c": (-0.90, 0, DECK_Z + 0.06), "size": (1.12, 1.32, 0.12), "mat": "mli_silver"},
        {"kind": "box", "name": "tow_hitch", "c": (-1.90, 0, 0.55), "size": (0.12, 0.12, 0.08), "mat": "titanium"},
    ],
    "crew": {"variant": "Crew:crewed", "x": 0.85, "floor_z": DECK_Z, "seats_y": (0.42, -0.42), "style": "seat",
             "console": (1.45, 0, DECK_Z + 0.75),
             "handholds": [[(0.30, 0.80, DECK_Z), (0.30, 0.80, DECK_Z + 0.85), (1.55, 0.80, DECK_Z + 0.85), (1.55, 0.80, DECK_Z)],
                           [(0.30, -0.80, DECK_Z), (0.30, -0.80, DECK_Z + 0.85), (1.55, -0.80, DECK_Z + 0.85), (1.55, -0.80, DECK_Z)]]},
    "masts": [{"name": "nav_mast", "base": (1.72, 0.0, DECK_Z), "h": 1.05, "r": 0.03, "head": (0.10, 0.34, 0.09), "cams": (-0.12, 0.12),
               "lamp": True}],
    "hga": {"base": (-1.55, -0.55, DECK_Z), "h": 0.55, "r": 0.28, "boresight": (-0.3, 0, 1), "band": "S/Ka"},
    "solar": [{"name": "solar_array", "c": (-1.62, 0.25, DECK_Z + 0.95), "u": (0, 1, 0), "v": (0, 0, 1), "w": 1.10, "h": 1.10,
               "normal": (-1, 0, 0), "mass": 8.0,
               "hinge": {"pos": (-1.62, 0.25, DECK_Z + 0.40), "axis": (0, -1, 0), "limit": (math.radians(-90), math.radians(30)),
                         "k": 600.0, "c": 60.0, "tau": 300.0}}],
    "arm": {"base": (-0.25, 0.70, DECK_Z + 0.36), "lengths": (1.05, 0.95, 0.30), "r": 0.045, "stow_dir": (-1, 0, 0), "mass": 45.0, "tau": 350.0},
    "lights": [((1.86, 0.55, 0.66), (1, 0, -0.1), 0.06, "headlight_l"), ((1.86, -0.55, 0.66), (1, 0, -0.1), 0.06, "headlight_r"),
               ((-1.86, 0.55, 0.66), (-1, 0, -0.1), 0.05, "rear_light_l"), ((-1.86, -0.55, 0.66), (-1, 0, -0.1), 0.05, "rear_light_r"),
               ((1.72, 0.22, DECK_Z + 0.88), (1, 0, -0.35), 0.05, "mast_flood_l"), ((1.72, -0.22, DECK_Z + 0.88), (1, 0, -0.35), 0.05, "mast_flood_r"),
               ((-1.50, 0.80, DECK_Z + 0.10), (0, 1, -0.6), 0.04, "work_light_l"), ((-1.50, -0.80, DECK_Z + 0.10), (0, -1, -0.6), 0.04, "work_light_r")],
    "sites": [
        ("payload_front", "chassis", (0.95, 0, DECK_Z + 0.06), (0, 0, 1), "payload_interface", "Front deck / cargo pallet interface"),
        ("payload_rear", "chassis", (-0.90, 0, DECK_Z + 0.34), (0, 0, 1), "payload_interface", "Rear deck payload interface"),
        ("tow_hitch", "chassis", (-1.96, 0, 0.55), (-1, 0, 0), "hitch", "Rear tow / trailer hitch"),
        ("hazcam_l", "chassis", (1.92, 0.20, 0.78), (1, 0, 0), "sensor", "Front hazard camera"),
        ("hazcam_r", "chassis", (1.92, -0.20, 0.78), (1, 0, 0), "sensor", "Front hazard camera"),
        ("lift_point_fl", "chassis", (1.6, 0.75, DECK_Z), (0, 0, 1), "handling", "Offload lift point"),
        ("lift_point_fr", "chassis", (1.6, -0.75, DECK_Z), (0, 0, 1), "handling", "Offload lift point"),
        ("lift_point_rl", "chassis", (-1.6, 0.75, DECK_Z), (0, 0, 1), "handling", "Offload lift point"),
        ("lift_point_rr", "chassis", (-1.6, -0.75, DECK_Z), (0, 0, 1), "handling", "Offload lift point"),
    ],
    "imu": (0, 0, 0.6),
}

MASS = {
    "unloaded": {"mass": 1100.0, "com_z": 0.72, "source": "concept: LTV-class 1,000-1,500 kg empty"},
    "crewed": {"mass": 1900.0, "com_z": 0.98, "com_x": 0.30, "source": "NASA LTV: + 2 suited crew (550 kg) + 250 kg cargo"},
    "uncrewed": {"mass": 2700.0, "com_z": 0.95, "com_x": 0.20, "source": "NASA LTV: + up to 1,600 kg uncrewed payload, reduced speed"},
}
DEFAULT_MASS_STATE = "unloaded"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (3.5, 1.6, 0.6)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "uncrewed"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS = {
    "chassis": [("hull", ["white_panel", "grey_panel"])],
    r"\w+_wheel": [("tyre", None)],
}
PHYSICS_MATERIAL = {"tyre": "tyre", "hull": "structure"}
PHYSICS_MATERIALS = {"tyre": (0.9, 0.8, 0.0), "structure": (0.5, 0.4, 0.05)}
SIMPLE_TRIS = 20000
RENDER_VIEWS = K.views(4.0, 2.8, 2.2)
