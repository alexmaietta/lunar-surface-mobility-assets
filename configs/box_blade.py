import tool_kit as T

ASSET_ID = "box_blade"
ASSET_PATH = "concepts/construction_tools/box_blade"
FAMILY = "tool"
TITLE = "Box blade with scarifier (concept rover attachment)"
DOC = ("Rear-mounted box blade for Lunar Terrain Vehicle-class rovers, the finishing tool for landing-pad foundations and "
       "roads. Towed forward, the main blade cuts high spots and carries the spoil inside the box, dropping it into low "
       "spots so repeated passes level a pad to grade. A row of scarifier teeth on a prismatic slide drops ahead of the "
       "blade to break up a crust. The 2.4 m width covers the rover's track so each pass grades the wheel ruts.")

TEXTURE_SETS, MATERIALS = T.materials()

W = 2.40
LIFT = (-0.10, 0.0, 0.0)
X_FRONT, X_BLADE = -0.66, -1.22
BOX_TOP = T.EDGE_Z + 0.42
TEETH = 9
CAP = 0.25


def _box():
    out = []
    blade = T.bezier((X_BLADE - 0.02, T.EDGE_Z), (X_BLADE - 0.10, T.EDGE_Z + 0.20), (X_BLADE + 0.0, BOX_TOP), 8)
    prof = [(x, z) for x, z in T.thick_profile([(-x, z) for x, z in blade], 0.018)]
    out.append({"kind": "extrude", "name": "main_blade", "link": "box_lift", "profile": [(-x, z) for x, z in prof], "y": (-W / 2, W / 2),
                "mat": "composite"})
    out.append({"kind": "box", "name": "main_edge", "link": "box_lift", "c": (X_BLADE - 0.01, 0, T.EDGE_Z + 0.04),
                "size": (0.03, W, 0.08), "mat": "wear_steel"})
    for sd, s in (("l", 1), ("r", -1)):
        y = s * (W / 2 + 0.01)
        out.append({"kind": "extrude", "name": f"side_plate_{sd}", "link": "box_lift",
                    "profile": [(X_FRONT, T.EDGE_Z + 0.06), (X_BLADE - 0.02, T.EDGE_Z), (X_BLADE - 0.02, BOX_TOP), (X_FRONT, BOX_TOP)],
                    "y": tuple(sorted((y, y - s * 0.015))), "mat": "white_panel"})
        out.append({"kind": "box", "name": f"side_runner_{sd}", "link": "box_lift", "c": ((X_FRONT + X_BLADE) / 2, y, T.EDGE_Z + 0.01),
                    "size": (abs(X_BLADE - X_FRONT), 0.05, 0.02), "mat": "wear_steel"})
    out += [{"kind": "beam", "name": "top_rail_front", "link": "box_lift", "p0": (X_FRONT, W / 2, BOX_TOP), "p1": (X_FRONT, -W / 2, BOX_TOP),
             "w": 0.08, "h": 0.08, "mat": "white_panel"},
            {"kind": "beam", "name": "top_rail_rear", "link": "box_lift", "p0": (X_BLADE, W / 2, BOX_TOP), "p1": (X_BLADE, -W / 2, BOX_TOP),
             "w": 0.08, "h": 0.08, "mat": "white_panel"},
            {"kind": "box", "name": "scarifier_housing", "link": "box_lift", "c": (X_FRONT - 0.06, 0, BOX_TOP - 0.10),
             "size": (0.10, W - 0.3, 0.12), "mat": "anodised_grey"}]
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"lower_link_{sd}", "link": "box_lift", "p0": (LIFT[0], s * 0.30, 0.0),
                    "p1": (X_FRONT, s * 0.55, BOX_TOP), "w": 0.06, "h": 0.09, "mat": "white_panel"})
    return out


def _scarifier():
    out = [{"kind": "box", "name": "tooth_bar", "link": "scarifier", "c": (X_FRONT - 0.15, 0, BOX_TOP - 0.10), "size": (0.06, W - 0.4, 0.06),
            "mat": "steel"}]
    for k in range(TEETH):
        y = -(W - 0.5) / 2 + (W - 0.5) * k / (TEETH - 1)
        out.append({"kind": "obox", "name": f"tooth_{k}", "link": "scarifier", "c": (X_FRONT - 0.17, y, (BOX_TOP - 0.10 + T.EDGE_Z + 0.06) / 2),
                    "ax": (0.15, 0, 1), "ay": (0, 1, 0), "size": (BOX_TOP - 0.10 - T.EDGE_Z - 0.04, 0.03, 0.05), "mat": "wear_steel"})
    return out


TOOL = {
    "base_mass": 15.0,
    "mount_axis": (1, 0, 0),
    "links": [
        {"name": "box_lift", "pos": LIFT, "axis": (0, 1, 0), "limit": (-0.35, 0.40), "role": "tool", "mass": 90.0,
         "drive": T.drive(50000.0, 5000.0, 8000.0)},
        {"name": "scarifier", "parent": "box_lift", "type": "prismatic", "pos": (X_FRONT - 0.15, 0, BOX_TOP - 0.10), "axis": (0, 0, -1),
         "limit": (0.0, 0.16), "role": "tool", "mass": 15.0, "drive": T.drive(20000.0, 2000.0, 3000.0)},
    ],
    "parts": [*T.coupler(-1), *_box(), *_scarifier(), *T.clevis("lift_clevis_l", (LIFT[0], 0.30, 0.0), gap=0.10),
              *T.clevis("lift_clevis_r", (LIFT[0], -0.30, 0.0), gap=0.10),
              *T.actuator("lift_ram", (-0.06, 0, 0.18), (X_FRONT + 0.10, 0, BOX_TOP + 0.04), r=0.04, link0="base", link1="box_lift"),
              {"kind": "box", "name": "lift_ram_mount", "c": (-0.06, 0, 0.18), "size": (0.06, 0.10, 0.06), "mat": "steel"},
              {"kind": "tube", "name": "lift_shaft", "link": "box_lift", "p0": (LIFT[0], -0.34, 0), "p1": (LIFT[0], 0.34, 0), "r": 0.03,
               "mat": "steel"}],
    "sites": [
        ("box_blade_edge", "box_lift", (X_BLADE - 0.02, 0, T.EDGE_Z), (1, 0, 0), "tool_edge",
         "Main blade cutting edge centre (+Z = towing direction); spoil is carried inside the box",
         {"tool": "box_blade", "width_m": W, "height_m": BOX_TOP - T.EDGE_Z, "capacity_m3": CAP, "bulk_density_kg_m3": T.BULK}),
        ("scarifier_tips", "scarifier", (X_FRONT - 0.13, 0, T.EDGE_Z + 0.06), (1, 0, 0), "tool_edge",
         "Scarifier tooth tip line centre", {"tool": "ripper", "width_m": W - 0.5, "teeth": TEETH, "loosen_width_m": W - 0.4}),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"box_lift": [("box", ["white_panel", "composite", "wear_steel"])]}
PHYSICS_MATERIAL = {"box": "steel"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.4, W, 0.8, -0.75, sx=-1)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "box_blade", "grader"]
