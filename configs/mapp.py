import rover_kit as K

ASSET_ID = "mapp"
ASSET_PATH = "lunar_outpost/mapp/rover"
FAMILY = "rover"
TITLE = "Lunar Outpost MAPP"
DOC = ("Lunar Outpost MAPP (Mobile Autonomous Prospecting Platform), the CLPS-class small rover flown on IM-2: about "
       "45 x 38 x 40 cm and 10 kg, a hexagonal-section aluminium body with solar cells on both sides and a three-lens "
       "camera bracket on the front, a tube truss carrying a top rail with camera and antenna brackets, and four gold "
       "paddle wheels with inboard hub motors on articulated rocker suspension with skid steering.")

TEXTURE_SETS, MATERIALS = K.materials()

R_W, WB, TRACK = 0.0575, 0.29, 0.30
BY = 0.12
TOP = 0.24
RAIL = 0.40
HEX = [(-0.09, 0.07), (0.09, 0.07), (0.16, 0.13), (0.145, TOP), (-0.145, TOP), (-0.16, 0.13)]
FN = (0.991, 0, 0.135)
FA = (-0.135, 0, 0.991)


def _frame():
    out = []
    for s in (-1, 1):
        y = s * (BY + 0.002)
        out.append({"kind": "rail", "name": f"edge_frame_{s + 1}", "r": 0.004, "closed": True, "mat": "aluminium",
                    "points": [(x, y, z) for x, z in HEX]})
        out.append({"kind": "panel", "name": f"cells_{'l' if s > 0 else 'r'}", "c": (0.0, s * (BY + 0.003), 0.178), "u": (1, 0, 0), "v": (0, 0, 1),
                    "w": 0.25, "h": 0.105, "t": 0.004, "normal": (0, s, 0), "mat": "solar_cells", "back": "brushed_panel"})
    for k, x in enumerate((-0.145, 0.145)):
        out.append({"kind": "tube", "name": f"top_cross_{k}", "p0": (x, -BY, TOP), "p1": (x, BY, TOP), "r": 0.004, "mat": "aluminium"})
    return out


def _truss():
    out = [{"kind": "tube", "name": "top_rail", "p0": (-0.20, 0, RAIL), "p1": (0.20, 0, RAIL), "r": 0.0055, "mat": "aluminium"}]
    for k, (xb, xt, xl) in enumerate(((0.12, 0.19, 0.16), (-0.12, -0.19, -0.16))):
        for s in (-1, 1):
            out.append({"kind": "tube", "name": f"truss_{k}_{s + 1}", "p0": (xb, s * BY, TOP), "p1": (xt, 0, RAIL), "r": 0.0035, "mat": "aluminium"})
            out.append({"kind": "tube", "name": f"truss_low_{k}_{s + 1}", "p0": (xl, s * (BY - 0.01), 0.13), "p1": (xt, 0, RAIL), "r": 0.003,
                        "mat": "aluminium"})
        out.append({"kind": "disc", "name": f"rail_node_{k}", "c": (xt, 0, RAIL - 0.008), "n": (0, 0, 1), "r": 0.014, "t": 0.012, "mat": "aluminium"})
    for s in (-1, 1):
        out.append({"kind": "tube", "name": f"truss_mid_{s + 1}", "p0": (0.0, s * BY, TOP), "p1": (0.0, 0, RAIL), "r": 0.0035, "mat": "aluminium"})
    out += [
        {"kind": "disc", "name": "rail_node_mid", "c": (0.0, 0, RAIL - 0.008), "n": (0, 0, 1), "r": 0.014, "t": 0.012, "mat": "aluminium"},
        {"kind": "box", "name": "rail_camera_bracket", "c": (0.205, 0, RAIL), "size": (0.03, 0.05, 0.025), "mat": "aluminium"},
        {"kind": "tube", "name": "rail_camera_lens", "p0": (0.22, 0, RAIL), "p1": (0.232, 0, RAIL), "r": 0.009, "mat": "lens"},
        {"kind": "box", "name": "rail_mid_bracket", "c": (0.0, 0, RAIL + 0.012), "size": (0.06, 0.05, 0.012), "mat": "aluminium"},
        {"kind": "tube", "name": "rail_mid_camera", "p0": (0.0, 0.0, RAIL + 0.03), "p1": (0.022, 0.0, RAIL + 0.03), "r": 0.008, "mat": "lens"},
        {"kind": "box", "name": "rail_antenna_bracket", "c": (-0.205, 0, RAIL), "size": (0.03, 0.05, 0.02), "mat": "aluminium"},
        {"kind": "tube", "name": "rail_antenna", "p0": (-0.205, 0, RAIL + 0.01), "p1": (-0.205, 0, RAIL + 0.03), "r": 0.004, "mat": "white_panel"},
        {"kind": "tube", "name": "lte_whip_f", "p0": (0.205, 0, RAIL + 0.012), "p1": (0.205, 0, RAIL + 0.45), "r": 0.004, "mat": "white_panel",
         "variant": "Antennas:field_test"},
        {"kind": "tube", "name": "lte_whip_r", "p0": (-0.205, 0, RAIL + 0.03), "p1": (-0.205, 0, RAIL + 0.45), "r": 0.004, "mat": "white_panel",
         "variant": "Antennas:field_test"},
    ]
    return out


def _hub_motors():
    out = []
    for n, s in (("l", 1), ("r", -1)):
        for x in (WB / 2, -WB / 2):
            out.append({"kind": "tube", "name": f"hub_motor_{n}_{'f' if x > 0 else 'r'}", "p0": (x, s * 0.108, R_W), "p1": (x, s * 0.072, R_W),
                        "r": 0.019, "mat": "aluminium", "link": f"rocker_{n}"})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": 0.085, "style": "grouser", "grousers": 12, "grouser_h": 0.014, "spokes": 6, "spoke_r": 0.003, "spoke_curve": 0.5,
              "disc": False, "drum_mat": "gold_anodised", "grouser_mat": "gold_anodised", "hub_frac": 0.28, "hub_mat": "anodised_grey",
              "rim_mat": "gold_anodised", "spoke_mat": "gold_anodised", "mass": 0.40, "segments": 32},
    "carriers": [{"name": f"rocker_{n}", "pos": (0, s * 0.125, R_W), "axis": (0, 1, 0), "limit": (-0.30, 0.30), "stiffness": 3.0,
                  "damping": 0.3, "mass": 0.3, "beam": 0.010, "mat": "aluminium",
                  "beams_to": [(WB / 2, s * 0.125, R_W), (-WB / 2, s * 0.125, R_W)]} for n, s in (("l", 1), ("r", -1))],
    "wheels": [dict(w, carrier=f"rocker_{w['name'][1]}") for w in K.four_wheels(WB, TRACK, None)],
    "suspension": {"type": "carrier", "kingpin_off": 0.025, "upper_dz": 0.012, "knuckle_t": 0.014, "knuckle_mat": "aluminium"},
    "parts": [
        {"kind": "extrude", "name": "body", "profile": HEX, "y": (-BY, BY), "mat": "brushed_panel"},
        *_frame(),
        {"kind": "obox", "name": "camera_bracket", "c": (0.1545, 0, 0.19), "ax": FA, "ay": (0, 1, 0), "size": (0.075, 0.13, 0.008), "mat": "aluminium"},
        *[{"kind": "disc", "name": f"camera_lens_{k}", "c": (0.158 - 0.135 * (z - 0.19), y, z), "n": FN, "r": 0.011, "t": 0.008, "mat": "lens"}
          for k, (y, z) in enumerate(((0.042, 0.205), (-0.042, 0.205), (0.0, 0.175)))],
        {"kind": "box", "name": "rocker_pivot_block", "c": (0, 0, 0.072), "size": (0.05, 0.22, 0.012), "mat": "anodised_grey"},
        *_hub_motors(),
        *_truss(),
    ],
    "sites": [("front_cameras", "chassis", (0.165, 0, 0.19), FN, "sensor", "Three-lens front camera bracket"),
              ("payload_rail", "chassis", (0, 0, RAIL + 0.006), (0, 0, 1), "payload_interface", "Top rail (15 kg payload capacity)")],
    "imu": (0, 0, 0.15),
}

MASS = {"flight": {"mass": 10.0, "com_z": 0.15, "source": "Lunar Outpost: 5-10 kg (10 kg used)"}}
DEFAULT_MASS_STATE = "flight"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (0.32, 0.24, 0.17)
GEOMETRY_VARIANTS = {"Antennas": ["flight", "field_test"]}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("brushed_panel",))
SIMPLE_TRIS = 8000
RENDER_VIEWS = K.views(0.45, 0.40, 0.50, centre_z=0.2)
