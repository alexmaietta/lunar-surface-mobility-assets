import math

import tool_kit as T

ASSET_ID = "roller_compactor"
ASSET_PATH = "concepts/construction_tools/roller_compactor"
FAMILY = "tool"
TITLE = "Towed vibratory roller compactor (concept rover attachment)"
DOC = ("Towed smooth-drum vibratory roller for Lunar Terrain Vehicle-class rovers, after the compactor developed by Michigan "
       "Tech for the Lunar Outpost / Colorado School of Mines ASPECT site-preparation rover. A passive yaw-and-pitch hitch "
       "and A-frame drawbar pull a 1.8 m drum carried in a yoke with an eccentric-mass vibrator at one end. A hopper on the "
       "yoke can be filled with regolith ballast, since a rover cannot afford to launch a heavy roller. Use for "
       "compacting landing-pad foundations (NASA's Lunar Innovation Park plan calls for 80 % relative density) and berms.")

TEXTURE_SETS, MATERIALS = T.materials()

R, DW = 0.33, 1.80
HITCH = (-0.12, 0.0, 0.0)
AXLE = (-1.55, 0.0, T.GROUND + R)
YOKE_Y = DW / 2 + 0.06


def _hitch():
    return [{"kind": "lathe", "name": "hitch_ball_socket", "link": "hitch_yaw", "c": HITCH, "n": (0, 0, 1),
             "profile": [(0.001, -0.06), (0.06, -0.06), (0.06, 0.06), (0.001, 0.06)], "mat": "steel"},
            {"kind": "box", "name": "hitch_tongue", "c": (-0.07, 0, 0), "size": (0.10, 0.10, 0.08), "mat": "steel"},
            {"kind": "tube", "name": "hitch_pitch_pin", "link": "hitch_pitch", "p0": (HITCH[0], -0.08, 0), "p1": (HITCH[0], 0.08, 0),
             "r": 0.02, "mat": "steel"}]


def _frame():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"drawbar_{sd}", "link": "hitch_pitch", "p0": (HITCH[0] - 0.05, s * 0.04, 0.0),
                    "p1": (AXLE[0] + 0.45, s * YOKE_Y, AXLE[2] + 0.22), "w": 0.06, "h": 0.08, "mat": "white_panel"})
        out.append({"kind": "box", "name": f"yoke_plate_{sd}", "link": "hitch_pitch", "c": (AXLE[0], s * YOKE_Y, AXLE[2] + 0.10),
                    "size": (0.90, 0.025, 0.36), "mat": "white_panel"})
        out.append({"kind": "lathe", "name": f"bearing_{sd}", "link": "hitch_pitch", "c": (AXLE[0], s * (YOKE_Y + 0.012), AXLE[2]),
                    "n": (0, s, 0), "sides": 24, "mat": "anodised_dark",
                    "profile": [(0.001, 0), (0.08, 0), (0.08, 0.05), (0.001, 0.05)]})
    out += [{"kind": "beam", "name": "yoke_front_beam", "link": "hitch_pitch", "p0": (AXLE[0] + 0.45, YOKE_Y, AXLE[2] + 0.22),
             "p1": (AXLE[0] + 0.45, -YOKE_Y, AXLE[2] + 0.22), "w": 0.08, "h": 0.08, "mat": "white_panel"},
            {"kind": "beam", "name": "yoke_rear_beam", "link": "hitch_pitch", "p0": (AXLE[0] - 0.45, YOKE_Y, AXLE[2] + 0.22),
             "p1": (AXLE[0] - 0.45, -YOKE_Y, AXLE[2] + 0.22), "w": 0.08, "h": 0.08, "mat": "white_panel"},
            {"kind": "frustum", "name": "ballast_hopper", "link": "hitch_pitch", "c": (AXLE[0], 0),
             "bottom": (AXLE[2] + R + 0.08, 0.62, 1.30), "top": (AXLE[2] + R + 0.32, 0.76, 1.50), "caps": (True, False), "mat": "white_panel"},
            {"kind": "box", "name": "hopper_rim", "link": "hitch_pitch", "c": (AXLE[0], 0, AXLE[2] + R + 0.33), "size": (0.80, 1.54, 0.03),
             "mat": "anodised_grey"},
            {"kind": "lathe", "name": "vibrator_housing", "link": "hitch_pitch", "c": (AXLE[0], -(YOKE_Y + 0.06), AXLE[2]), "n": (0, -1, 0),
             "sides": 32, "mat": "anodised_dark", "profile": [(0.001, 0), (0.15, 0), (0.15, 0.16), (0.10, 0.20), (0.001, 0.20)]},
            {"kind": "box", "name": "scraper_bar", "link": "hitch_pitch", "c": (AXLE[0] - R - 0.05, 0, AXLE[2] + 0.05),
             "size": (0.03, DW, 0.06), "mat": "wear_steel"}]
    return out


def _drum():
    out = [{"kind": "lathe", "name": "drum_shell", "link": "roller", "c": AXLE, "n": (0, 1, 0), "sides": 64, "mat": "steel",
            "profile": [(R - 0.015, -DW / 2), (R - 0.004, -DW / 2), (R, -DW / 2 + 0.01), (R, DW / 2 - 0.01), (R - 0.004, DW / 2),
                        (R - 0.015, DW / 2), (R - 0.015, -DW / 2)]}]
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "lathe", "name": f"drum_end_{sd}", "link": "roller", "c": (AXLE[0], s * (DW / 2 - 0.004), AXLE[2]), "n": (0, s, 0),
                    "sides": 48, "mat": "anodised_grey", "profile": [(0.001, -0.004), (R - 0.012, -0.004), (R - 0.012, 0.004), (0.001, 0.004)]})
        for k in range(6):
            a = 2 * math.pi * k / 6
            out.append({"kind": "disc", "name": f"drum_end_{sd}_hole_{k}", "link": "roller",
                        "c": (AXLE[0] + math.cos(a) * R * 0.6, s * (DW / 2 + 0.001), AXLE[2] + math.sin(a) * R * 0.6), "n": (0, s, 0),
                        "r": 0.04, "t": 0.002, "sides": 16, "mat": "anodised_dark"})
    out.append({"kind": "tube", "name": "drum_axle", "link": "roller", "p0": (AXLE[0], -YOKE_Y, AXLE[2]), "p1": (AXLE[0], YOKE_Y, AXLE[2]),
                "r": 0.04, "mat": "steel"})
    return out


TOOL = {
    "base_mass": 10.0,
    "mount_axis": (1, 0, 0),
    "links": [
        {"name": "hitch_yaw", "pos": HITCH, "axis": (0, 0, 1), "limit": (math.radians(-75), math.radians(75)), "role": "hitch",
         "mass": 4.0, "drive": T.passive(5.0)},
        {"name": "hitch_pitch", "parent": "hitch_yaw", "pos": HITCH, "axis": (0, 1, 0), "limit": (math.radians(-30), math.radians(30)),
         "role": "hitch", "mass": 80.0, "drive": T.passive(5.0)},
        {"name": "roller", "parent": "hitch_pitch", "pos": AXLE, "axis": (0, 1, 0), "role": "roller", "mass": 120.0,
         "drive": T.passive(2.0)},
    ],
    "parts": [*T.coupler(-1), *_hitch(), *_frame(), *_drum()],
    "sites": [
        ("roller_contact", "hitch_pitch", (AXLE[0], 0, T.GROUND), (0, 0, -1), "tool_edge",
         "Drum contact line centre (+Z = into the ground); compacts width_m per pass",
         {"tool": "compactor", "width_m": DW, "radius_m": R, "vibration_hz": 30.0, "centrifugal_force_n": 4000.0}),
        ("ballast_hopper", "hitch_pitch", (AXLE[0], 0, AXLE[2] + R + 0.12), (0, 0, 1), "payload",
         "Regolith ballast hopper (fill to add drum load)", {"volume_m3": 0.26, "capacity_kg": 0.26 * T.BULK, "bulk_density_kg_m3": T.BULK}),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"roller": [("drum", ["steel"])],
             "hitch_pitch": [("yoke", ["white_panel", "anodised_grey"])]}
PHYSICS_MATERIAL = {"drum": "steel", "yoke": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(2.0, 2.0, 1.2, -1.1, sx=-1)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "compactor", "roller"]
