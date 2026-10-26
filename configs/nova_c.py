ASSET_ID = "nova_c"
ASSET_PATH = "intuitive_machines/nova_c/lander"
FAMILY = "nova_c"
TITLE = "Intuitive Machines Nova-C"
DOC = ("Intuitive Machines Nova-C lunar lander (IM-1 Odysseus / IM-2 Athena class): a 4.3 m tall hexagonal prism, "
       "1.57 m across flats, with two stacked composite LOX/LCH4 tanks, copper-wrapped helium tanks, a gimballed VR900 "
       "main engine under a heat-shield skirt, six crush-core tripod legs on a 4.6 m footprint, a top-deck hex array and "
       "two body-mounted side arrays, helium cold-gas RCS on corner booms and a fixed S-band high-gain dish.")

TEXTURE_SETS = {
    "white_panel": ("panel", dict(colour=(0.82, 0.82, 0.80), tile_m=0.6, rough0=0.5, fastener_pitch=0.06)),
    "deck_panel": ("panel", dict(colour=(0.66, 0.66, 0.65), tile_m=0.6, rough0=0.55, metallic=0.15, fastener_pitch=0.06)),
    "mli_gold": ("mli", dict(colour=(0.90, 0.64, 0.16), tile_m=0.8, gloss=0.12)),
    "mli_copper": ("mli", dict(colour=(0.88, 0.45, 0.16), tile_m=0.5, gloss=0.08)),
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=0.6, gloss=0.08, tape=False)),
    "mli_black": ("mli", dict(colour=(0.05, 0.05, 0.055), tile_m=0.6, gloss=0.25, tape=False)),
    "aluminium": ("brushed", dict(colour=(0.84, 0.84, 0.84), tile_m=0.3, rough0=0.22)),
    "anodised_dark": ("anodised", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, rough0=0.5)),
    "anodised_yellow": ("anodised", dict(colour=(0.80, 0.62, 0.10), tile_m=0.3, rough0=0.4)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.30, 0.29, 0.28), tile_m=0.25, rough0=0.45, bands=32)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.48, 0.34, 0.24), tile_m=0.25, rough0=0.35)),
    "engine_metal": ("anodised", dict(colour=(0.55, 0.55, 0.56), tile_m=0.2, rough0=0.35)),
    "solar_cells": ("solar_cells", dict(tile_m=0.32)),
    "beta_white": ("beta_cloth", dict(colour=(0.84, 0.83, 0.80), tile_m=0.4)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "white_panel": {"set": "white_panel", "normal": 1.0},
    "deck_panel": {"set": "deck_panel", "normal": 1.0},
    "mli_gold": {"set": "mli_gold", "normal": 1.0, "preview": (0.88, 0.64, 0.18)},
    "mli_copper": {"set": "mli_copper", "normal": 1.0, "preview": (0.82, 0.45, 0.18)},
    "mli_silver": {"set": "mli_silver", "normal": 0.8},
    "mli_black": {"set": "mli_black", "normal": 0.8},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "footpad": {"set": "aluminium", "normal": 0.5},
    "deck_box": {"set": "anodised_dark", "normal": 0.5},
    "frame_dark": {"set": "anodised_dark", "normal": 0.5},
    "frame_yellow": {"set": "anodised_yellow", "normal": 0.5},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "engine_metal": {"set": "engine_metal", "normal": 0.5},
    "solar_cells": {"set": "solar_cells", "normal": 0.3},
    "beta_white": {"set": "beta_white", "normal": 0.8},
    "radome": {"color": (0.82, 0.81, 0.78), "roughness": 0.6},
    "lens": {"color": (0.01, 0.01, 0.012), "roughness": 0.05, "metallic": 0.0},
}

FACES = {
    0: [(0.95, 2.30, "mli_gold"), (2.30, 4.05, "white_panel")],
    60: [(0.95, 1.45, "mli_black")],
    120: [(0.95, 2.30, "mli_black"), (2.30, 4.05, "white_panel")],
    180: [(0.95, 2.30, "mli_gold"), (2.30, 4.05, "white_panel")],
    240: [(0.95, 2.30, "mli_black"), (2.30, 4.05, "white_panel")],
    300: [(0.95, 1.45, "mli_black")],
}

FEATURES = {
    "second_he_tank": True,
    "solar_side_az": [60, 300],
    "lga_az": [90, 150, 210, 330],
    "nav_pod": 180,
    "scalpss_az": [0, 90, 180, 270],
    "lra": (0.30, -0.25),
}

RCS = {
    "cold_gas": {"kind": "rcs_cold_gas", "thrust_n": 4.45, "isp_s": 70.0, "exit_r": 0.008, "nozzle_len": 0.04,
                 "propellant": "GHe",
                 "notes": "Helium cold-gas RCS, 4.45 N (1 lbf) per thruster (IM / press). Thruster count and pod layout assumed.",
                 "confidence": "propellant/thrust official; count and layout assumed"},
}

MASS = {
    "launch": {"mass": 1908.0, "com_z": 2.20, "source": "IM-1 fuelled mass 1,908 kg (Intuitive Machines)"},
    "touchdown": {"mass": 860.0, "com_z": 2.45, "source": "estimate: 675 kg dry + ~100 kg payload + ~85 kg residuals"},
    "dry": {"mass": 775.0, "com_z": 2.50, "source": "675 kg dry bus (IM) + ~100 kg payload"},
}
DEFAULT_MASS_STATE = "touchdown"

SEMANTIC_CLASS = ["lunar_lander", "spacecraft"]
WIKIDATA = []

ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (0.9, 3.4)
COLLIDERS = {
    "body": [("hull", ["white_panel", "deck_panel", "mli_gold", "mli_black", "mli_silver", "solar_cells", "frame_yellow"])],
    r"leg_\d_piston": [("foot", None)],
    "vr900": [("nozzle", ["nozzle_ext"])],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure", "nozzle": "structure"}
PHYSICS_MATERIALS = {
    "footpad": (0.8, 0.7, 0.0),
    "structure": (0.5, 0.4, 0.05),
}

RENDER_VIEWS = {
    "front_three_quarter": ((9.4, -6.6, 2.4), (0, 0, 2.15), 45),
    "side": ((0.0, -11.5, 2.0), (0, 0, 2.15), 45),
    "low_engine": ((3.0, -2.1, 0.25), (0, 0, 0.9), 24),
    "top_deck": ((3.4, -2.9, 7.6), (0, 0, 4.0), 35),
    "thumb": ((8.8, -6.0, 2.8), (0, 0, 2.15), 40),
}
