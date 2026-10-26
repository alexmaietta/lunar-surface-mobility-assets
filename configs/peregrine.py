ASSET_ID = "peregrine"
ASSET_PATH = "astrobotic/peregrine/lander"
FAMILY = "peregrine"
TITLE = "Astrobotic Peregrine"
DOC = ("Astrobotic Peregrine lunar lander (Peregrine Mission One, January 2024): a 1.9 m tall bus in silver MLI around "
       "four propellant tanks and a central helium tank, with two white-radiator avionics enclosures, two open payload "
       "decks, a single top-mounted solar panel, five pulsed main engines inside the launch-adapter cone, twelve ACS "
       "thrusters and four gold-Kapton legs on a 2.5 m face-on footprint.")

TEXTURE_SETS = {
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=0.7, gloss=0.07)),
    "mli_gold": ("mli", dict(colour=(0.90, 0.64, 0.14), tile_m=0.3, gloss=0.12, tape=False)),
    "deck_panel": ("panel", dict(colour=(0.62, 0.62, 0.62), tile_m=0.5, rough0=0.55, metallic=0.15, fastener_pitch=0.05)),
    "radiator": ("panel", dict(colour=(0.86, 0.86, 0.85), tile_m=0.4, rough0=0.25, fastener_pitch=0.08)),
    "aluminium": ("brushed", dict(colour=(0.78, 0.78, 0.78), tile_m=0.3, rough0=0.30)),
    "polished": ("brushed", dict(colour=(0.90, 0.90, 0.90), tile_m=0.2, rough0=0.10, along=0)),
    "champagne": ("anodised", dict(colour=(0.74, 0.66, 0.52), tile_m=0.2, rough0=0.30)),
    "bronze": ("anodised", dict(colour=(0.45, 0.32, 0.18), tile_m=0.2, rough0=0.40)),
    "anodised_dark": ("anodised", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, rough0=0.5)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.40, 0.38, 0.36), tile_m=0.1, rough0=0.40, bands=16)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.50, 0.36, 0.26), tile_m=0.1, rough0=0.35)),
    "engine_metal": ("anodised", dict(colour=(0.55, 0.55, 0.56), tile_m=0.2, rough0=0.35)),
    "solar_cells": ("solar_cells", dict(tile_m=0.32)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "mli_silver": {"set": "mli_silver", "normal": 1.0},
    "leg_kapton": {"set": "mli_gold", "normal": 0.6, "preview": (0.88, 0.64, 0.18)},
    "payload_gold": {"set": "mli_gold", "normal": 0.8, "preview": (0.88, 0.64, 0.18)},
    "deck_panel": {"set": "deck_panel", "normal": 1.0},
    "radiator": {"set": "radiator", "normal": 0.6},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "polished": {"set": "polished", "normal": 0.3},
    "footpad": {"set": "champagne", "normal": 0.4},
    "leg_band": {"set": "bronze", "normal": 0.4},
    "deck_box": {"set": "anodised_dark", "normal": 0.5},
    "frame_dark": {"set": "anodised_dark", "normal": 0.5},
    "baffle": {"set": "anodised_dark", "normal": 0.5},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "engine_metal": {"set": "engine_metal", "normal": 0.5},
    "solar_cells": {"set": "solar_cells", "normal": 0.3},
    "radome": {"color": (0.82, 0.81, 0.78), "roughness": 0.6},
    "lens": {"color": (0.01, 0.01, 0.012), "roughness": 0.05, "metallic": 0.0},
}

FEATURES = {
    "mga": True,
    "star_trackers": [(0.62, -0.42), (-0.62, 0.42)],
}

DECK_PAYLOADS = [
    (-0.30, 0.88, 0.30, 0.18, 0.22, "payload_gold"),
    (0.28, 0.88, 0.26, 0.16, 0.16, "deck_box"),
    (0.38, 0.55, 0.16, 0.20, 0.12, "mli_silver"),
]

MAIN_ENGINE = {"thrust_n": 667.0, "isp_s": 310.0, "propellant": "MMH/MON-25",
               "notes": "Frontier Aerospace 150 lbf (667 N) bipropellant engine, one of five; throttled by pulsing (Astrobotic). "
                        "Isp and nozzle size are not published and are estimated.",
               "confidence": "count/thrust official; Isp and geometry estimated"}

RCS = {
    "acs": {"kind": "rcs_hot_gas", "thrust_n": 45.0, "isp_s": 290.0, "exit_r": 0.02, "nozzle_len": 0.05, "propellant": "MMH/MON-25",
            "notes": "ACS thruster, 12 x 45 N in four clusters of three (Astrobotic). Cluster positions partly inferred from photos.",
            "confidence": "count/thrust official; layout estimated"},
}

MASS = {
    "launch": {"mass": 1283.0, "com_z": 1.20, "source": "Astrobotic: 1,283 kg fuelled (PM1)"},
    "touchdown": {"mass": 580.0, "com_z": 1.25, "source": "estimate: ~413 kg dry bus + 90 kg payload + ~75 kg residuals"},
    "dry": {"mass": 503.0, "com_z": 1.27, "source": "estimate: ~413 kg dry bus (rocket equation) + 90 kg payload (official)"},
}
DEFAULT_MASS_STATE = "touchdown"

SEMANTIC_CLASS = ["lunar_lander", "spacecraft"]
WIKIDATA = []

ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (1.0, 1.5)
COLLIDERS = {
    "body": [("hull", ["mli_silver", "deck_panel", "radiator", "solar_cells", "frame_dark"])],
    r"leg_\d_piston": [("foot", None)],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure"}
PHYSICS_MATERIALS = {
    "footpad": (0.8, 0.7, 0.0),
    "structure": (0.5, 0.4, 0.05),
}

RENDER_VIEWS = {
    "front_three_quarter": ((6.0, -4.3, 1.4), (0, 0, 1.0), 45),
    "side": ((0.0, -7.4, 1.0), (0, 0, 1.0), 45),
    "low_engine": ((2.2, -1.5, 0.15), (0, 0, 0.55), 24),
    "top_deck": ((2.4, -2.0, 4.5), (0, 0, 1.6), 35),
    "thumb": ((5.6, -3.9, 1.6), (0, 0, 1.0), 40),
}
