ASSET_ID = "mk2"
ASSET_PATH = "blue_origin/mk2/lander"
FAMILY = "mk2"
TITLE = "Blue Moon MK2"
DOC = ("Blue Origin Blue Moon Mark 2 crewed lunar lander (NASA Artemis Human Landing System), about 15.3 m tall and more "
       "than 45 t fuelled: a faceted white crew cabin at the base over a gold-MLI engine skirt with three gimballed BE-7 "
       "LOX/LH2 engines, a hinged crew door with an egress platform and deployable stair, a side IDSS-style docking port "
       "with a hinged hatch and two hooded windows; above it a triangulated truss cage around two oblate propellant tanks, "
       "and the MLI-wrapped LH2 tank inside four hinged sunshield panels under a white dome with a blue band, floodlights "
       "and two gimballed dish antennas. Four sprung legs with large dish footpads.")

TEXTURE_SETS = {
    "white_panel": ("panel", dict(colour=(0.87, 0.87, 0.86), tile_m=2.4, rough0=0.42, fastener_pitch=0.15, seams=2, res=4096)),
    "grey_panel": ("panel", dict(colour=(0.55, 0.56, 0.57), tile_m=1.0, rough0=0.45, metallic=0.2, fastener_pitch=0.10)),
    "sunshield": ("panel", dict(colour=(0.74, 0.74, 0.73), tile_m=2.4, rough0=0.38, metallic=0.35, fastener_pitch=0.24, seams=4, res=4096)),
    "mli_gold": ("mli", dict(colour=(0.88, 0.55, 0.10), tile_m=1.4, gloss=0.10, res=4096)),
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=1.8, gloss=0.08, res=4096)),
    "mli_white": ("mli", dict(colour=(0.90, 0.90, 0.88), tile_m=2.2, gloss=0.18, crinkle=0.8, res=4096)),
    "flag": ("flag", dict(tile_m=1.0)),
    "aluminium": ("brushed", dict(colour=(0.80, 0.80, 0.80), tile_m=0.4, rough0=0.30)),
    "anodised_grey": ("anodised", dict(colour=(0.36, 0.37, 0.38), tile_m=0.3, rough0=0.45)),
    "titanium": ("brushed", dict(colour=(0.58, 0.56, 0.53), tile_m=0.25, rough0=0.22, along=0)),
    "nozzle_ext": ("nozzle_metal", dict(colour=(0.30, 0.24, 0.20), tile_m=0.35, rough0=0.45, bands=48)),
    "nozzle_int": ("nozzle_metal", dict(colour=(0.52, 0.36, 0.24), tile_m=0.3, rough0=0.35)),
    "grating": ("perforated", dict(colour=(0.62, 0.62, 0.63), tile_m=0.15, hole_d=0.022, pitch=0.03)),
    "beta_white": ("beta_cloth", dict(colour=(0.84, 0.83, 0.80), tile_m=0.4)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "white_panel": {"set": "white_panel", "normal": 0.8},
    "grey_panel": {"set": "grey_panel", "normal": 0.8},
    "sunshield": {"set": "sunshield", "normal": 0.6},
    "mli_gold": {"set": "mli_gold", "normal": 1.0, "preview": (0.86, 0.58, 0.15)},
    "mli_silver": {"set": "mli_silver", "normal": 1.0, "metallic": 0.55},
    "mli_white": {"set": "mli_white", "normal": 1.0, "metallic": 0.05},
    "frame": {"set": "anodised_grey", "normal": 0.5},
    "strut": {"set": "aluminium", "normal": 0.5},
    "engine_metal": {"set": "titanium", "normal": 0.4},
    "nozzle_ext": {"set": "nozzle_ext", "normal": 0.6},
    "nozzle_int": {"set": "nozzle_int", "normal": 0.4},
    "leg_upper": {"set": "aluminium", "normal": 0.5},
    "leg_lower": {"set": "mli_gold", "normal": 1.0, "preview": (0.86, 0.58, 0.15)},
    "footpad": {"set": "aluminium", "normal": 0.5},
    "pod": {"set": "beta_white", "normal": 0.7},
    "grating": {"set": "grating", "normal": 0.6, "alpha": True},
    "blue_paint": {"color": (0.06, 0.16, 0.55), "roughness": 0.4},
    "flag": {"set": "flag", "normal": 0.2},
    "yellow": {"color": (0.85, 0.65, 0.05), "roughness": 0.45},
    "glass": {"color": (0.02, 0.025, 0.03), "roughness": 0.04},
    "glass_amber": {"color": (0.45, 0.30, 0.10), "roughness": 0.06, "metallic": 0.4},
    "radome": {"color": (0.84, 0.83, 0.80), "roughness": 0.6},
    "lamp": {"color": (0.95, 0.95, 0.90), "roughness": 0.2, "emission": (1.0, 0.97, 0.90, 6.0)},
}

RCS = {
    "rcs": {"kind": "rcs_hot_gas", "thrust_n": 445.0, "isp_s": 300.0, "exit_r": 0.05, "nozzle_len": 0.16, "propellant": "unknown (assumed storable)",
            "notes": "RCS thruster count, thrust and propellant not published; 4 pods x 5 thrusters assumed (MK1 heritage).",
            "confidence": "layout and performance assumed"},
}

MASS = {
    "launch": {"mass": 45000.0, "com_z": 8.2, "source": "Blue Origin / press: more than 45 t fuelled"},
    "touchdown": {"mass": 30000.0, "com_z": 7.2, "source": "estimate: dry + ascent propellant and reserves"},
    "dry": {"mass": 16000.0, "com_z": 6.4, "source": "press: about 16 t dry"},
}
DEFAULT_MASS_STATE = "touchdown"

SEMANTIC_CLASS = ["lunar_lander", "crewed_lander", "spacecraft"]
WIKIDATA = []
ROBOT_TYPE = "Aerial"
INERTIA_ENVELOPE = (3.0, 15.3)
COLLIDERS = {
    "body": [("hull", ["white_panel", "mli_gold", "sunshield", "mli_silver", "mli_white", "grey_panel"])],
    r"leg_\d_piston": [("foot", None)],
}
PHYSICS_MATERIAL = {"foot": "footpad", "hull": "structure"}
PHYSICS_MATERIALS = {"footpad": (0.8, 0.7, 0.0), "structure": (0.5, 0.4, 0.05)}
SIMPLE_TRIS = 16000

RENDER_VIEWS = {
    "front_three_quarter": ((20.5, -15.0, 5.5), (0, 0, 7.4), 40),
    "side": ((0.0, -36.0, 5.0), (0, 0, 7.4), 40),
    "low_engine": ((7.5, -5.5, 0.45), (0, 0, 1.6), 28),
    "crew_door": ((-5.0, 10.2, 3.4), (-2.0, 2.6, 2.8), 35),
    "ref_front": ((30.0, -3.5, 3.2), (0, 0, 7.6), 50),
    "top_deck": ((10.0, -8.0, 22.0), (0, 0, 13.0), 35),
    "thumb": ((26.0, -19.0, 6.5), (0, 0, 7.4), 40),
}
