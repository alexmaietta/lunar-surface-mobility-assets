ASSET_ID = "mk1_offloader"
ASSET_PATH = "blue_origin/mk1/offloader"
FAMILY = "offloader"
TITLE = "Blue Moon MK1 payload offloader"
DOC = ("Deck-mounted payload offloader for the Blue Origin Blue Moon MK1 lander: a slewing turret, a perforated mast "
       "and a luffing twin-boom jib with a sheave head, hoist line and spreader for lowering rovers to the surface.")

TEXTURE_SETS = {
    "aluminium": ("brushed", dict(colour=(0.80, 0.80, 0.80), tile_m=0.4, rough0=0.30)),
    "truss": ("perforated", dict(colour=(0.82, 0.82, 0.82), tile_m=0.20, hole_d=0.035, pitch=0.05)),
    "housing": ("panel", dict(colour=(0.74, 0.74, 0.72), tile_m=0.4, rough0=0.5, fastener_pitch=0.05)),
    "steel": ("brushed", dict(colour=(0.55, 0.55, 0.56), tile_m=0.2, rough0=0.35)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}
MATERIALS = {
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "truss": {"set": "truss", "normal": 0.6, "alpha": True},
    "housing": {"set": "housing", "normal": 0.8},
    "steel": {"set": "steel", "normal": 0.4},
    "cable": {"color": (0.08, 0.08, 0.08), "roughness": 0.55},
}
ROLE_MATERIALS = {"frame": "aluminium", "truss": "truss", "housing": "housing", "fastener": "steel", "cable": "cable"}
LINK_MASSES = {"base": 6.0, "crane_slew": 18.0, "crane_luff": 30.0, "crane_hoist": 6.0}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {
    "crane_luff": [("jib", ["truss", "housing"])],
    "crane_slew": [("mast", ["truss", "housing"])],
    "crane_hoist": [("spreader", ["truss", "housing"])],
}
PHYSICS_MATERIAL = {"jib": "structure", "mast": "structure", "spreader": "structure"}
PHYSICS_MATERIALS = {"structure": (0.5, 0.4, 0.05)}

RENDER_VIEWS = {
    "lunar": ((5.0, -6.0, 1.6), (1.8, 0, 0.8), 40),
    "thumb": ((5.0, -6.0, 1.6), (1.8, 0, 0.8), 40),
}
SEMANTIC_CLASS = ["crane", "payload_offloader"]
