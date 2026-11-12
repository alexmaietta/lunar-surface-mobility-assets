import math

import tool_kit as T

ASSET_ID = "dozer_blade"
ASSET_PATH = "concepts/construction_tools/dozer_blade"
FAMILY = "tool"
TITLE = "Power-angle-tilt dozer blade (concept rover attachment)"
DOC = ("Front-mounted six-way dozer blade for Lunar Terrain Vehicle-class rovers, sized after NASA's LANCE blade on Chariot "
       "(composite moldboard on a light aluminium frame, about 70 % lighter than a steel blade). A quick-attach coupler carries "
       "an A-frame push arm on a lift pivot, and a C-frame on the arm nose gives power angle (yaw) and tilt (roll). The 2.7 m "
       "curved composite moldboard has a replaceable steel cutting edge and end bits. Use for clearing, grading, dozing "
       "and building berms and ramps.")

TEXTURE_SETS, MATERIALS = T.materials()

W, H = 2.70, 0.68
LIFT = (0.10, 0.0, 0.0)
PIVOT = (0.82, 0.0, -0.30)
EDGE = (1.02, T.EDGE_Z)
TOP = (0.95, T.EDGE_Z + H)


def _moldboard():
    front = T.bezier(EDGE, (0.80, T.EDGE_Z + 0.30), TOP, 12) + [(0.99, TOP[1] + 0.03)]
    prof = T.thick_profile(front, 0.025)
    out = [{"kind": "extrude", "name": "moldboard", "link": "blade_tilt", "profile": prof, "y": (-W / 2, W / 2), "mat": "composite"},
           {"kind": "box", "name": "cutting_edge", "link": "blade_tilt", "c": (EDGE[0] - 0.005, 0, EDGE[1] + 0.05),
            "size": (0.035, W, 0.10), "mat": "wear_steel"}]
    side = [(EDGE[0] + 0.015, EDGE[1]), *front[1:], (0.84, TOP[1]), (0.82, EDGE[1] + 0.10)]
    for sd, s in (("l", 1), ("r", -1)):
        y0 = s * W / 2
        out.append({"kind": "extrude", "name": f"end_bit_{sd}", "link": "blade_tilt", "profile": side,
                    "y": tuple(sorted((y0, y0 - s * 0.02))), "mat": "wear_steel"})
    for k, y in enumerate([-1.05, -0.55, 0.0, 0.55, 1.05]):
        rib = [(0.83, EDGE[1] + 0.06), (0.80, EDGE[1] + 0.35), (0.86, TOP[1] - 0.05), (0.93, TOP[1] - 0.02),
               (0.86, EDGE[1] + 0.35), (0.92, EDGE[1] + 0.06)]
        out.append({"kind": "extrude", "name": f"rib_{k}", "link": "blade_tilt", "profile": rib, "y": (y - 0.012, y + 0.012),
                    "mat": "white_panel"})
    out += [{"kind": "box", "name": "back_beam", "link": "blade_tilt", "c": (0.83, 0, PIVOT[2]), "size": (0.10, W - 0.3, 0.14),
             "mat": "white_panel"},
            {"kind": "box", "name": "top_beam", "link": "blade_tilt", "c": (0.89, 0, TOP[1] - 0.06), "size": (0.06, W - 0.2, 0.06),
             "mat": "white_panel"},
            {"kind": "lathe", "name": "tilt_boss", "link": "blade_tilt", "c": (PIVOT[0] - 0.02, 0, PIVOT[2]), "n": (1, 0, 0),
             "profile": [(0.001, -0.06), (0.07, -0.06), (0.07, 0.06), (0.001, 0.06)], "mat": "steel"},
            *[{"kind": "box", "name": f"tilt_link_{sd}", "link": "blade_tilt", "c": (0.80, s * 0.45, TOP[1] - 0.10),
               "size": (0.08, 0.05, 0.10), "mat": "steel"} for sd, s in (("l", 1), ("r", -1))]]
    return out


def _frames():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"push_arm_{sd}", "link": "blade_lift", "p0": (LIFT[0], s * 0.30, 0.0),
                    "p1": (PIVOT[0] - 0.12, s * 0.10, PIVOT[2]), "w": 0.07, "h": 0.09, "mat": "white_panel"})
    out += [{"kind": "beam", "name": "push_arm_brace", "link": "blade_lift", "p0": (0.42, 0.22, -0.13), "p1": (0.42, -0.22, -0.13),
             "w": 0.05, "h": 0.06, "mat": "white_panel"},
            {"kind": "box", "name": "nose_block", "link": "blade_lift", "c": (PIVOT[0] - 0.09, 0, PIVOT[2]), "size": (0.10, 0.26, 0.14),
             "mat": "anodised_grey"},
            {"kind": "tube", "name": "lift_shaft", "link": "blade_lift", "p0": (LIFT[0], -0.34, 0), "p1": (LIFT[0], 0.34, 0), "r": 0.03,
             "mat": "steel"},
            {"kind": "lathe", "name": "angle_kingpin", "link": "blade_angle", "c": (PIVOT[0] - 0.03, 0, PIVOT[2] - 0.09), "n": (0, 0, 1),
             "profile": [(0.001, 0), (0.045, 0), (0.045, 0.18), (0.001, 0.18)], "mat": "steel"},
            {"kind": "box", "name": "c_frame", "link": "blade_angle", "c": (PIVOT[0] - 0.06, 0, PIVOT[2] + 0.11),
             "size": (0.08, 1.1, 0.06), "mat": "white_panel"}]
    for sd, s in (("l", 1), ("r", -1)):
        out += T.actuator(f"angle_ram_{sd}", (0.50, s * 0.24, -0.15), (PIVOT[0] - 0.04, s * 0.50, PIVOT[2] + 0.11), r=0.028,
                          link0="blade_lift", link1="blade_angle")
        out += T.actuator(f"tilt_ram_{sd}", (PIVOT[0] - 0.04, s * 0.45, PIVOT[2] + 0.13), (0.80, s * 0.45, TOP[1] - 0.14), r=0.022,
                          link0="blade_angle", link1="blade_tilt", split=0.5)
    out += T.clevis("lift_clevis_l", (LIFT[0], 0.30, 0.0), gap=0.10)
    out += T.clevis("lift_clevis_r", (LIFT[0], -0.30, 0.0), gap=0.10)
    out += T.actuator("lift_ram", (0.06, 0, 0.16), (0.45, 0, -0.10), r=0.04, link0="base", link1="blade_lift")
    out.append({"kind": "box", "name": "lift_ram_mount", "c": (0.06, 0, 0.16), "size": (0.06, 0.10, 0.06), "mat": "steel"})
    return out


TOOL = {
    "base_mass": 15.0,
    "links": [
        {"name": "blade_lift", "pos": LIFT, "axis": (0, -1, 0), "limit": (-0.30, 0.45), "role": "tool", "mass": 40.0,
         "drive": T.drive(40000.0, 4000.0, 6000.0)},
        {"name": "blade_angle", "parent": "blade_lift", "pos": PIVOT, "axis": (0, 0, 1), "limit": (math.radians(-30), math.radians(30)),
         "role": "tool", "mass": 12.0, "drive": T.drive(20000.0, 2000.0, 3000.0)},
        {"name": "blade_tilt", "parent": "blade_angle", "pos": PIVOT, "axis": (1, 0, 0), "limit": (math.radians(-8), math.radians(8)),
         "role": "tool", "mass": 70.0, "drive": T.drive(20000.0, 2000.0, 3000.0)},
    ],
    "parts": [*T.coupler(1), *_frames(), *_moldboard()],
    "sites": [
        ("blade_edge", "blade_tilt", (EDGE[0], 0, EDGE[1]), (1, 0, 0), "tool_edge",
         "Cutting edge centre (+Z = cutting direction); the moldboard spans width_m across it",
         {"tool": "blade", "width_m": W, "height_m": H, "capacity_m3": 0.45, "bulk_density_kg_m3": T.BULK}),
        ("blade_top", "blade_tilt", (TOP[0], 0, TOP[1]), (0, 0, 1), "reference", "Top of the moldboard (spill-over height)"),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"blade_tilt": [("moldboard", ["composite", "wear_steel"])],
             "blade_lift": [("push_frame", ["white_panel", "anodised_grey"])]}
PHYSICS_MATERIAL = {"moldboard": "steel", "push_frame": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.1, W, 0.9, 0.6)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "dozer_blade"]
