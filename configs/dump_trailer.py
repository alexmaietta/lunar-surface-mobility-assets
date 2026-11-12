import math

import tool_kit as T

ASSET_ID = "dump_trailer"
ASSET_PATH = "concepts/construction_tools/dump_trailer"
FAMILY = "tool"
TITLE = "Tipping dump trailer (concept rover attachment)"
DOC = ("Two-wheel tipping dump trailer for Lunar Terrain Vehicle-class rovers, the hauler in a dig-haul-dump cycle (loader "
       "bucket or drum excavator fills it, the rover tows it to the berm or pad, the bed tips to dump). A passive "
       "yaw-and-pitch hitch and drawbar pull an axle frame on two free-rolling 0.70 m spring-mesh wheels. The 1.6 x 1.4 m "
       "bed holds about 0.8 m3 (1.2 t of loose regolith) and tips up to 55 degrees about its rear hinge on an electric ram.")

TEXTURE_SETS, MATERIALS = T.materials()

HITCH = (-0.12, 0.0, 0.0)
WR, WW = 0.35, 0.22
AXLE = (-1.95, 0.0, T.GROUND + WR)
TRACK = 1.70
BED_X = (-2.62, -1.02)
BED_W, BED_H = 1.40, 0.42
FLOOR = AXLE[2] + 0.22
HINGE = (BED_X[0] + 0.04, 0.0, FLOOR - 0.04)
CAP = 0.80


def _hitch():
    return [{"kind": "lathe", "name": "hitch_ball_socket", "link": "hitch_yaw", "c": HITCH, "n": (0, 0, 1),
             "profile": [(0.001, -0.06), (0.06, -0.06), (0.06, 0.06), (0.001, 0.06)], "mat": "steel"},
            {"kind": "box", "name": "hitch_tongue", "c": (-0.07, 0, 0), "size": (0.10, 0.10, 0.08), "mat": "steel"},
            {"kind": "tube", "name": "hitch_pitch_pin", "link": "hitch_pitch", "p0": (HITCH[0], -0.08, 0), "p1": (HITCH[0], 0.08, 0),
             "r": 0.02, "mat": "steel"}]


def _chassis():
    out = []
    zf = FLOOR - 0.09
    for sd, s in (("l", 1), ("r", -1)):
        out += [{"kind": "beam", "name": f"drawbar_{sd}", "link": "hitch_pitch", "p0": (HITCH[0] - 0.05, s * 0.04, 0.0),
                 "p1": (BED_X[1] + 0.05, s * 0.45, zf), "w": 0.06, "h": 0.08, "mat": "white_panel"},
                {"kind": "beam", "name": f"frame_rail_{sd}", "link": "hitch_pitch", "p0": (BED_X[1] + 0.05, s * 0.45, zf),
                 "p1": (BED_X[0], s * 0.45, zf), "w": 0.07, "h": 0.10, "mat": "white_panel"},
                {"kind": "beam", "name": f"axle_stub_{sd}", "link": "hitch_pitch", "p0": (AXLE[0], s * 0.45, AXLE[2]),
                 "p1": (AXLE[0], s * (TRACK / 2 - WW / 2 - 0.03), AXLE[2]), "w": 0.06, "h": 0.06, "mat": "steel"},
                {"kind": "beam", "name": f"axle_hanger_{sd}", "link": "hitch_pitch", "p0": (AXLE[0], s * 0.45, zf),
                 "p1": (AXLE[0], s * 0.45, AXLE[2]), "w": 0.07, "h": 0.07, "mat": "white_panel"},
                {"kind": "box", "name": f"fender_{sd}", "link": "hitch_pitch", "c": (AXLE[0], s * TRACK / 2, AXLE[2] + WR + 0.06),
                 "size": (0.80, WW + 0.06, 0.02), "mat": "white_panel"},
                {"kind": "beam", "name": f"fender_strut_{sd}", "link": "hitch_pitch", "p0": (AXLE[0], s * 0.45, zf),
                 "p1": (AXLE[0], s * (TRACK / 2 - WW / 2 - 0.02), AXLE[2] + WR + 0.05), "w": 0.03, "h": 0.03, "mat": "anodised_grey"}]
    out += [{"kind": "beam", "name": "frame_cross_front", "link": "hitch_pitch", "p0": (BED_X[1] + 0.05, 0.45, zf),
             "p1": (BED_X[1] + 0.05, -0.45, zf), "w": 0.07, "h": 0.07, "mat": "white_panel"},
            {"kind": "beam", "name": "frame_cross_rear", "link": "hitch_pitch", "p0": (BED_X[0], 0.45, zf), "p1": (BED_X[0], -0.45, zf),
             "w": 0.07, "h": 0.07, "mat": "white_panel"},
            {"kind": "box", "name": "hinge_block", "link": "hitch_pitch", "c": (HINGE[0], 0, HINGE[2] - 0.03), "size": (0.08, 0.80, 0.06),
             "mat": "steel"},
            {"kind": "box", "name": "jack_stand", "link": "hitch_pitch", "c": (BED_X[1] + 0.25, 0, T.GROUND + 0.20), "size": (0.05, 0.05, 0.40),
             "mat": "steel"}]
    out += T.actuator("tip_ram", (BED_X[1] - 0.10, 0, zf + 0.02), (BED_X[1] - 0.45, 0, FLOOR - 0.03), r=0.04, link0="hitch_pitch",
                      link1="bed", split=0.6)
    return out


def _bed():
    x0, x1 = BED_X
    out = [{"kind": "box", "name": "bed_floor", "link": "bed", "c": ((x0 + x1) / 2, 0, FLOOR), "size": (x1 - x0, BED_W, 0.02), "mat": "white_panel"},
           {"kind": "box", "name": "bed_front", "link": "bed", "c": (x1 - 0.01, 0, FLOOR + BED_H / 2), "size": (0.02, BED_W, BED_H),
            "mat": "white_panel"},
           {"kind": "box", "name": "head_guard", "link": "bed", "c": (x1 + 0.03, 0, FLOOR + BED_H + 0.08), "size": (0.06, BED_W, 0.16),
            "mat": "grating"},
           {"kind": "box", "name": "tailgate", "link": "bed", "c": (x0 + 0.01, 0, FLOOR + BED_H * 0.45), "size": (0.02, BED_W - 0.04, BED_H * 0.9),
            "mat": "anodised_grey"}]
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "box", "name": f"bed_side_{sd}", "link": "bed", "c": ((x0 + x1) / 2, s * (BED_W / 2 - 0.01), FLOOR + BED_H / 2),
                    "size": (x1 - x0, 0.02, BED_H), "mat": "white_panel"})
        out.append({"kind": "beam", "name": f"bed_top_rail_{sd}", "link": "bed", "p0": (x1, s * BED_W / 2, FLOOR + BED_H),
                    "p1": (x0, s * BED_W / 2, FLOOR + BED_H), "w": 0.04, "h": 0.04, "mat": "anodised_grey"})
        for k in range(3):
            x = x0 + (x1 - x0) * (k + 1) / 4
            out.append({"kind": "box", "name": f"bed_rib_{sd}_{k}", "link": "bed", "c": (x, s * (BED_W / 2 + 0.01), FLOOR + BED_H / 2),
                        "size": (0.04, 0.02, BED_H), "mat": "anodised_grey"})
    for k in range(4):
        x = x0 + (x1 - x0) * (k + 0.5) / 4
        out.append({"kind": "box", "name": f"floor_bearer_{k}", "link": "bed", "c": (x, 0, FLOOR - 0.03), "size": (0.05, BED_W - 0.1, 0.04),
                    "mat": "anodised_grey"})
    return out


TOOL = {
    "base_mass": 10.0,
    "mount_axis": (1, 0, 0),
    "links": [
        {"name": "hitch_yaw", "pos": HITCH, "axis": (0, 0, 1), "limit": (math.radians(-75), math.radians(75)), "role": "hitch",
         "mass": 4.0, "drive": T.passive(5.0)},
        {"name": "hitch_pitch", "parent": "hitch_yaw", "pos": HITCH, "axis": (0, 1, 0), "limit": (math.radians(-30), math.radians(30)),
         "role": "hitch", "mass": 75.0, "drive": T.passive(5.0)},
        {"name": "bed", "parent": "hitch_pitch", "pos": HINGE, "axis": (0, -1, 0), "limit": (0.0, math.radians(55)), "role": "tool",
         "mass": 70.0, "drive": T.drive(30000.0, 3000.0, 9000.0)},
        *[{"name": f"trailer_{sd}_wheel", "parent": "hitch_pitch", "pos": (AXLE[0], s * TRACK / 2, AXLE[2]), "axis": (0, 1, 0),
           "role": "free_wheel", "mass": 14.0, "drive": T.passive(0.5)} for sd, s in (("l", 1), ("r", -1))],
    ],
    "parts": [*T.coupler(-1), *_hitch(), *_chassis(), *_bed(),
              *[q for sd, s in (("l", 1), ("r", -1)) for q in T.wheel_parts(f"trailer_{sd}_wheel", f"trailer_{sd}_wheel",
                                                                               (AXLE[0], s * TRACK / 2, AXLE[2]), WR, WW)]],
    "sites": [
        ("bed_volume", "bed", ((BED_X[0] + BED_X[1]) / 2, 0, FLOOR + 0.20), (0, 0, 1), "payload", "Bed load centroid (struck capacity)",
         {"volume_m3": CAP, "capacity_kg": CAP * T.BULK, "bulk_density_kg_m3": T.BULK, "length_m": BED_X[1] - BED_X[0], "width_m": BED_W}),
        ("dump_lip", "bed", (BED_X[0], 0, FLOOR), (-1, 0, 0), "reference", "Rear dump lip (spoil leaves the bed here)"),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {r"trailer_[lr]_wheel": [("tyre", ["tyre_mesh"])],
             "bed": [("bed", ["white_panel", "anodised_grey"])],
             "hitch_pitch": [("frame", ["white_panel"])]}
PHYSICS_MATERIAL = {"tyre": "tyre", "bed": "structure", "frame": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(2.8, 2.0, 1.3, -1.4, sx=-1)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "trailer", "dump_trailer"]
