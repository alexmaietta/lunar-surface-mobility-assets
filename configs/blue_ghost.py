ASSET_ID = "blue_ghost"
ASSET_PATH = "firefly/blue_ghost/lander"
FAMILY = "blue_ghost"
TITLE = "Firefly Blue Ghost"
DOC = ("Firefly Aerospace Blue Ghost Mission 1 lunar lander (landed in Mare Crisium, March 2025): a 2 m tall "
       "chamfered-square body in copper MLI with two body-mounted solar panels, four carbon legs with crush-core "
       "strokes and saucer footpads, a fixed Nammo LEROS 4-ET main engine, eight Spectre RCS thrusters, twelve "
       "cold-gas ACS thrusters and a gimballed X-band panel antenna.")

TEXTURE_SETS = {
    "mli_copper": ("mli", dict(colour=(0.92, 0.50, 0.17), tile_m=0.8, gloss=0.08)),
    "mli_gold": ("mli", dict(colour=(0.90, 0.62, 0.12), tile_m=0.5, gloss=0.10)),
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=0.6, gloss=0.08, tape=False)),
    "deck_panel": ("panel", dict(colour=(0.62, 0.62, 0.62), tile_m=0.6, rough0=0.55, metallic=0.15, fastener_pitch=0.06)),
    "aluminium": ("brushed", dict(colour=(0.80, 0.80, 0.80), tile_m=0.3, rough0=0.30)),
    "titanium": ("brushed", dict(colour=(0.62, 0.60, 0.57), tile_m=0.2, rough0=0.25, along=0)),
    "composite": ("composite", dict(colour=(0.07, 0.07, 0.08), tile_m=0.15)),
    "anodised_dark": ("anodised", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, rough0=0.5)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.42, 0.40, 0.38), tile_m=0.2, rough0=0.40, bands=24)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.50, 0.36, 0.26), tile_m=0.2, rough0=0.35)),
    "engine_metal": ("anodised", dict(colour=(0.55, 0.55, 0.56), tile_m=0.2, rough0=0.35)),
    "solar_cells": ("solar_cells", dict(tile_m=0.32)),
    "beta_white": ("beta_cloth", dict(colour=(0.84, 0.83, 0.80), tile_m=0.4)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "mli_copper": {"set": "mli_copper", "normal": 1.0, "preview": (0.80, 0.45, 0.18)},
    "leg_mli": {"set": "mli_copper", "normal": 1.0, "preview": (0.80, 0.45, 0.18)},
    "mli_gold": {"set": "mli_gold", "normal": 1.0, "preview": (0.86, 0.62, 0.15)},
    "mli_silver": {"set": "mli_silver", "normal": 0.8},
    "deck_panel": {"set": "deck_panel", "normal": 1.0},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "titanium": {"set": "titanium", "normal": 0.4},
    "composite": {"set": "composite", "normal": 0.5},
    "baffle": {"set": "anodised_dark", "normal": 0.5},
    "deck_box": {"set": "anodised_dark", "normal": 0.5},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "engine_metal": {"set": "engine_metal", "normal": 0.5},
    "solar_cells": {"set": "solar_cells", "normal": 0.3},
    "panel_frame": {"set": "beta_white", "normal": 0.6},
    "beta_white": {"set": "beta_white", "normal": 0.8},
    "radome": {"color": (0.82, 0.81, 0.78), "roughness": 0.6},
    "lens": {"color": (0.01, 0.01, 0.012), "roughness": 0.05, "metallic": 0.0},
}

FEATURES = {
    "solar_az": [0, 180],
    "lexi": (-0.35, 0.30),
    "xband": {"pos": (0.45, -0.45), "size": (0.50, 0.45)},
    "star_trackers": [(-0.62, -0.50), (0.55, 0.55)],
    "omni_antennas": 3,
    "nglr": (0.25, 0.55),
    "cameras": [(0.70, 0.0, 0), (0.0, -0.70, 270), (-0.70, 0.0, 180), (0.0, 0.70, 90)],
}

DECK_BOXES = [
    (0.05, -0.15, 0.45, 0.35, 0.14, "deck_box"),
    (-0.30, -0.55, 0.30, 0.22, 0.10, "mli_gold"),
    (0.55, 0.15, 0.25, 0.30, 0.12, "beta_white"),
]

RCS = {
    "spectre": {"kind": "rcs_hot_gas", "thrust_n": 200.0, "isp_s": 290.0, "exit_r": 0.03, "nozzle_len": 0.09,
                "propellant": "MMH/MON-3",
                "notes": "Firefly Spectre bipropellant RCS; 8 thrusters, ~1,600 N total (Firefly). Pod layout from renders.",
                "confidence": "count/total thrust official; Isp and layout estimated"},
    "cold_gas": {"kind": "rcs_cold_gas", "thrust_n": 5.0, "isp_s": 65.0, "exit_r": 0.008, "nozzle_len": 0.03,
                 "propellant": "GHe (assumed)",
                 "notes": "Cold-gas ACS; 12 thrusters (Firefly). Thrust, Isp and clustering assumed.",
                 "confidence": "count official; layout and performance assumed"},
}

MASS = {
    "launch": {"mass": 1517.0, "com_z": 1.25, "source": "Firefly: 1,517 kg fuelled"},
    "touchdown": {"mass": 560.0, "com_z": 1.15, "source": "estimate: 469 kg dry incl. payloads + ~90 kg residuals"},
    "dry": {"mass": 469.0, "com_z": 1.18, "source": "Firefly: 469 kg dry with payloads"},
}
DEFAULT_MASS_STATE = "touchdown"

SEMANTIC_CLASS = ["lunar_lander", "spacecraft"]
WIKIDATA = []

ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (1.0, 1.9)
COLLIDERS = {
    "body": [("hull", ["mli_copper", "deck_panel", "mli_silver", "solar_cells", "panel_frame"])],
    r"leg_\d_piston": [("foot", None)],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure"}
PHYSICS_MATERIALS = {
    "footpad": (0.8, 0.7, 0.0),
    "structure": (0.5, 0.4, 0.05),
}

RENDER_VIEWS = {
    "front_three_quarter": ((6.2, -4.4, 1.5), (0, 0, 1.05), 45),
    "side": ((0.0, -7.6, 1.1), (0, 0, 1.05), 45),
    "low_engine": ((2.3, -1.6, 0.18), (0, 0, 0.55), 24),
    "top_deck": ((2.4, -2.0, 4.6), (0, 0, 1.9), 35),
    "thumb": ((5.8, -4.0, 1.7), (0, 0, 1.05), 40),
}
