ASSET_ID = "mk1"
ASSET_PATH = "blue_origin/mk1/lander"
FAMILY = "mk1"
TITLE = "Blue Moon MK1"
DOC = ("Blue Origin Blue Moon Mark 1 lunar lander: a single-stage uncrewed cargo lander about 8 m tall with an "
       "octagonal avionics ring, an MLI-wrapped LH2 tank, four capsule propellant tanks around one gimballed BE-7 "
       "LOX/LH2 engine, four legs with stroking pistons, corner RCS pods, a steerable high-gain antenna and a deck "
       "mount for an optional payload offloader.")

TEXTURE_SETS = {
    "mli_gold": ("mli", dict(colour=(0.90, 0.52, 0.06), tile_m=1.2, gloss=0.10, res=4096)),
    "mli_amber": ("mli", dict(colour=(0.84, 0.33, 0.05), tile_m=1.2, gloss=0.11, res=4096)),
    "mli_silver": ("mli", dict(colour=(0.82, 0.83, 0.85), tile_m=0.6, gloss=0.08, tape=False)),
    "ring_panel": ("panel", dict(colour=(0.78, 0.78, 0.76), tile_m=0.6, rough0=0.55, fastener_pitch=0.06)),
    "deck_panel": ("panel", dict(colour=(0.70, 0.70, 0.69), tile_m=0.8, rough0=0.55, metallic=0.15, fastener_pitch=0.08)),
    "aluminium": ("brushed", dict(colour=(0.80, 0.80, 0.80), tile_m=0.4, rough0=0.30)),
    "anodised_dark": ("anodised", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, rough0=0.5)),
    "leg_lattice": ("perforated", dict(colour=(0.78, 0.78, 0.78), tile_m=0.24, hole_d=0.026, pitch=0.04)),
    "titanium": ("brushed", dict(colour=(0.58, 0.56, 0.53), tile_m=0.25, rough0=0.22, along=0)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.30, 0.24, 0.20), tile_m=0.35, rough0=0.45, bands=48)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.55, 0.30, 0.16), tile_m=0.35, rough0=0.35)),
    "engine_metal": ("anodised", dict(colour=(0.55, 0.55, 0.56), tile_m=0.3, rough0=0.35)),
    "osr": ("osr", dict(tile_m=0.2, tile=0.04)),
    "solar_cells": ("solar_cells", dict(tile_m=0.32, res=4096)),
    "beta_white": ("beta_cloth", dict(colour=(0.80, 0.79, 0.75), tile_m=0.6)),
    "rbf_cloth": ("cloth", dict(colour=(0.60, 0.03, 0.03), tile_m=0.1)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "mli_gold": {"set": "mli_gold", "normal": 1.0, "preview": (0.86, 0.6, 0.13)},
    "mli_amber": {"set": "mli_amber", "normal": 1.0, "preview": (0.82, 0.42, 0.10)},
    "mli_silver": {"set": "mli_silver", "normal": 0.8},
    "ring_panel": {"set": "ring_panel", "normal": 1.0},
    "deck_panel": {"set": "deck_panel", "normal": 1.0},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "anodised_dark": {"set": "anodised_dark", "normal": 0.5},
    "leg_lattice": {"set": "leg_lattice", "normal": 0.6, "alpha": True},
    "titanium": {"set": "titanium", "normal": 0.4},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "engine_metal": {"set": "engine_metal", "normal": 0.5},
    "osr": {"set": "osr", "normal": 0.6},
    "solar_cells": {"set": "solar_cells", "normal": 0.3},
    "beta_white": {"set": "beta_white", "normal": 0.8},
    "rbf": {"set": "rbf_cloth", "normal": 0.5},
    "radome": {"color": (0.80, 0.79, 0.76), "roughness": 0.6},
    "lens": {"color": (0.01, 0.01, 0.012), "roughness": 0.05, "metallic": 0.0},
    "cable": {"color": (0.05, 0.05, 0.05), "roughness": 0.6},
}

ROLE_MATERIALS = {
    "ring_panel": "ring_panel", "deck_top": "deck_panel", "mli_rim": "mli_silver", "frame": "aluminium",
    "mli_upper": "mli_gold", "mli_shoulder": "mli_amber", "mli_lower": "mli_amber", "mli_tank": "mli_gold", "heat_shield": "mli_silver",
    "strut": "aluminium", "line": "aluminium", "radiator": "osr",
    "gas_mli": "mli_gold", "gas_white": "beta_white",
    "nozzle_ext": "nozzle_ext", "nozzle_int": "nozzle_int", "engine_metal": "engine_metal",
    "leg_lattice": "leg_lattice", "leg_tube": "aluminium", "piston": "titanium", "footpad": "aluminium",
    "rcs_nozzle": "engine_metal", "rcs_pod": "mli_amber",
    "solar": "solar_cells", "panel_back": "beta_white",
    "deck_box": "ring_panel", "baffle": "anodised_dark", "radome": "radome", "lra": "lens", "lens": "lens",
    "hga_dish": "beta_white", "crane_truss": "leg_lattice", "cable": "cable", "flag": "ring_panel", "rbf": "rbf",
}
GAS_TANK_ROLES = ["gas_mli", "gas_mli", "gas_mli", "gas_mli"]

FEATURES = {
    "radiator": True,
    "solar_az": [90, 270],
    "hga": {"pos": (0.9, -0.95), "mast_h": 0.40, "dish_r": 0.28, "band": "X"},
    "omni_antennas": 4,
    "lra": (-0.3, -0.9),
    "offloader_mount": (-0.9, 1.0),
    "scalpss": True,
    "crane": False,
    "flag_decal": False,
    "rbf_tags": False,
}

DECK_BOXES = [(-0.6, 0.0, 0.8, 0.6, 0.25), (0.5, 0.7, 0.5, 0.4, 0.18), (0.3, -0.2, 0.4, 0.4, 0.12)]

RCS = {
    "hot_gas": {"thrust_n": 445.0, "isp_s": 350.0, "exit_r": 0.035, "nozzle_len": 0.10, "propellant": "GO2/GH2",
                "dirs": [(0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)],
                "notes": "Hot-gas biprop fed by the GO2/GH2 corner tanks ('GO2 2' label on the photographed tank). "
                         "Thrust/Isp are assumptions (Apollo-LM-class quad).",
                "confidence": "layout inferred from photos; performance assumed"},
    "cold_gas": {"thrust_n": 22.0, "isp_s": 70.0, "exit_r": 0.012, "nozzle_len": 0.05, "propellant": "GN2 (assumed)",
                 "dirs": [(0, 1, 0), (0, -1, 0)],
                 "notes": "Cold-gas fine attitude thrusters (Gunter's Space Page: hot and cold gas thrusters). Values assumed.",
                 "confidence": "existence reported; layout and performance assumed"},
}

MASS = {
    "launch": {"mass": 21350.0, "com_z": 3.6, "source": "Wikipedia / Blue Origin fueled mass"},
    "touchdown": {"mass": 7900.0, "com_z": 4.1, "source": "estimate: dry + ~0.9 t residuals"},
    "dry": {"mass": 7000.0, "com_z": 4.3, "source": "estimate"},
}
DEFAULT_MASS_STATE = "touchdown"

SEMANTIC_CLASS = ["lunar_lander", "spacecraft"]
WIKIDATA = []

ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (2.0, 6.8)
COLLIDERS = {
    "body": [("hull", ["mli_gold", "mli_amber", "ring_panel", "deck_panel", "mli_silver"])],
    r"leg_\d_piston": [("foot", None)],
    "be7": [("nozzle", ["nozzle_ext"])],
    r"solar_array_\d": [("panel", ["solar_cells", "beta_white"])],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure", "nozzle": "structure", "panel": "structure"}
PHYSICS_MATERIALS = {
    "footpad": (0.8, 0.7, 0.0),
    "structure": (0.5, 0.4, 0.05),
}

ATTACHMENTS = {"Offloader": {"crane": ("mk1_offloader", "offloader_mount", "mount")}}
