ASSET_ID = "apollo_lm"
ASSET_PATH = "grumman/apollo_lm/lander"
FAMILY = "apollo_lm"
TITLE = "Apollo Lunar Module"
DOC = ("Grumman Apollo Lunar Module (J-mission, LM-10 to LM-12): a 7.04 m tall two-stage crewed lander with a "
       "4.2 m octagonal descent stage in amber Kapton, four cantilever legs on a 9.45 m footprint with 0.94 m pads, a "
       "gimballed throttleable descent engine with the J-mission nozzle extension, an ascent stage with a forward-leaning "
       "crew cabin, triangular windows, forward hatch, docking tunnel, fixed ascent engine, four RCS quads, a steerable "
       "S-band dish and the rendezvous radar.")

TEXTURE_SETS = {
    "mli_amber": ("mli", dict(colour=(0.86, 0.48, 0.10), tile_m=1.2, gloss=0.10)),
    "mli_gold": ("mli", dict(colour=(0.90, 0.64, 0.14), tile_m=0.5, gloss=0.12, tape=False)),
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=0.8, gloss=0.08, tape=False)),
    "mli_black": ("mli", dict(colour=(0.05, 0.05, 0.055), tile_m=0.8, gloss=0.25, tape=False)),
    "as_panel": ("panel", dict(colour=(0.60, 0.58, 0.54), tile_m=0.5, rough0=0.45, metallic=0.3, fastener_pitch=0.05)),
    "as_hatch": ("panel", dict(colour=(0.70, 0.69, 0.66), tile_m=0.4, rough0=0.45, metallic=0.3, fastener_pitch=0.04)),
    "ds_deck": ("panel", dict(colour=(0.55, 0.55, 0.55), tile_m=0.8, rough0=0.5, metallic=0.2, fastener_pitch=0.08)),
    "anodised_dark": ("anodised", dict(colour=(0.05, 0.05, 0.055), tile_m=0.3, rough0=0.45)),
    "aluminium": ("brushed", dict(colour=(0.78, 0.78, 0.78), tile_m=0.4, rough0=0.30)),
    "polished": ("brushed", dict(colour=(0.88, 0.88, 0.88), tile_m=0.3, rough0=0.12, along=0)),
    "osr": ("osr", dict(tile_m=0.2, tile=0.04)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.16, 0.14, 0.13), tile_m=0.5, rough0=0.5, bands=40)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.40, 0.30, 0.22), tile_m=0.5, rough0=0.4)),
    "engine_metal": ("anodised", dict(colour=(0.50, 0.50, 0.51), tile_m=0.3, rough0=0.35)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "mli_amber": {"set": "mli_amber", "normal": 1.0, "preview": (0.84, 0.50, 0.14)},
    "leg_mli": {"set": "mli_gold", "normal": 0.8, "preview": (0.88, 0.64, 0.18)},
    "footpad": {"set": "mli_gold", "normal": 0.8, "preview": (0.88, 0.64, 0.18)},
    "mli_silver": {"set": "mli_silver", "normal": 0.8},
    "mli_black": {"set": "mli_black", "normal": 0.8},
    "as_panel": {"set": "as_panel", "normal": 1.0},
    "as_hatch": {"set": "as_hatch", "normal": 1.0},
    "as_black": {"set": "anodised_dark", "normal": 0.5},
    "ds_deck": {"set": "ds_deck", "normal": 1.0},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "polished": {"set": "polished", "normal": 0.3},
    "radiator": {"set": "osr", "normal": 0.6},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "engine_metal": {"set": "engine_metal", "normal": 0.5},
    "dish": {"color": (0.80, 0.79, 0.76), "roughness": 0.55},
    "window": {"color": (0.01, 0.012, 0.015), "roughness": 0.04, "metallic": 0.0},
}

RCS = {
    "quad": {"kind": "rcs_hot_gas", "thrust_n": 445.0, "isp_s": 290.0, "exit_r": 0.07, "nozzle_len": 0.25,
             "propellant": "Aerozine 50/N2O4",
             "notes": "Marquardt R-4D, 100 lbf; 16 thrusters in four quads (Grumman/NASA). Plume deflectors not modelled.",
             "confidence": "official; quad positions measured from drawings"},
}

MASS = {
    "launch": {"mass": 16400.0, "com_z": 2.99, "source": "J-mission LM launch mass ~16,400 kg (NASA News Reference)"},
    "touchdown": {"mass": 8000.0, "com_z": 3.69, "source": "estimate: ascent stage wet ~4,700 kg + descent dry 2,770 kg + ~500 kg residuals"},
    "dry": {"mass": 4900.0, "com_z": 3.40, "source": "ascent dry ~2,130 kg + descent dry ~2,770 kg"},
}
DEFAULT_MASS_STATE = "touchdown"
MASS_IS_TOTAL = True

LBF = 4.44822
IN = 0.0254
ARM = 20.0
CRUSH_DAMPING = {"kind": "none", "stiffness": 0.0, "damping": 500.0}
SPRING = {"kind": "spring", "stiffness": 9.0e4, "damping": 1.5e4, "max_force": 4.0e5}
LOCKED = {"limit": (0.0, 1e-5), "drive": {"kind": "none", "stiffness": 0.0, "damping": 0.0}, "armature": 10.0}
JOINT_VARIANTS = {
    "LandingGear": {
        "spring": {
            r"leg_\d_primary_stage1": {"limit": (0.0, 32 * IN), "drive": SPRING, "armature": 20.0},
            r"leg_\d_primary_inner": LOCKED,
            r"leg_\d_secondary_[ab]_(compression|tension1|outer)": LOCKED,
        },
        "crush": {
            r"leg_\d_primary_stage1": {"limit": (0.0, 12 * IN), "drive": CRUSH_DAMPING, "friction": 4500 * LBF,
                                        "stage_load": 4500 * LBF, "armature": ARM},
            r"leg_\d_primary_inner": {"limit": (0.0, 20 * IN), "drive": CRUSH_DAMPING, "friction": 9500 * LBF,
                                       "stage_load": 9500 * LBF, "armature": ARM},
            r"leg_\d_secondary_[ab]_compression": {"limit": (-14 * IN, 0.0), "drive": CRUSH_DAMPING, "friction": 4500 * LBF,
                                                   "stage_load": 4500 * LBF, "armature": ARM},
            r"leg_\d_secondary_[ab]_tension1": {"limit": (0.0, 6 * IN), "drive": CRUSH_DAMPING, "friction": 500 * LBF,
                                                "stage_load": 500 * LBF, "armature": ARM},
            r"leg_\d_secondary_[ab]_outer": {"limit": (0.0, 12 * IN), "drive": CRUSH_DAMPING, "friction": 5000 * LBF,
                                             "stage_load": 5000 * LBF, "armature": ARM},
        },
    },
}

SEMANTIC_CLASS = ["lunar_lander", "spacecraft", "crewed_spacecraft"]
WIKIDATA = ["Q188386"]

ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (2.1, 5.0)
COLLIDERS = {
    "body": [("hull", ["mli_amber", "ds_deck", "mli_black", "mli_silver", "as_panel", "as_black", "as_hatch", "radiator"])],
    r"leg_\d_footpad": [("foot", None)],
    "dps": [("nozzle", ["nozzle_ext"])],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure", "nozzle": "structure"}
PHYSICS_MATERIALS = {
    "footpad": (0.8, 0.7, 0.0),
    "structure": (0.5, 0.4, 0.05),
}

RENDER_VIEWS = {
    "front_three_quarter": ((14.5, 11.5, 3.6), (0, 0, 3.4), 45),
    "side": ((19.0, 0.0, 3.0), (0, 0, 3.4), 45),
    "low_engine": ((5.6, 3.6, 0.35), (0, 0, 1.6), 24),
    "top_deck": ((6.0, 5.0, 11.5), (0, 0, 5.0), 35),
    "thumb": ((13.5, 10.5, 4.2), (0, 0, 3.4), 40),
}
