import tool_kit as T

ASSET_ID = "rock_rake"
ASSET_PATH = "concepts/construction_tools/rock_rake"
FAMILY = "tool"
TITLE = "Rock rake (concept rover attachment)"
DOC = ("Front rock rake for Lunar Terrain Vehicle-class rovers, after the rock and regolith grader on the Colorado School of "
       "Mines / Lunar Outpost ASPECT rover and the rock clearing done with NASA's LANCE blade. Seventeen curved steel tines "
       "on a 2.5 m toolbar sift cobbles and boulders out of the top layer and roll them into a windrow while fine regolith "
       "passes between the tines, clearing a landing-pad or road site before grading.")

TEXTURE_SETS, MATERIALS = T.materials()

W, PITCH = 2.50, 0.15
LIFT = (0.10, 0.0, 0.0)
BAR = (0.86, 0.0, -0.22)
TINES = 17


def _tines():
    out = []
    for k in range(TINES):
        y = -PITCH * (TINES - 1) / 2 + PITCH * k
        pts = [(BAR[0] + 0.03, y, BAR[2] - 0.02), (BAR[0] + 0.08, y, BAR[2] - 0.16), (BAR[0] + 0.13, y, T.EDGE_Z + 0.05),
               (BAR[0] + 0.21, y, T.EDGE_Z)]
        out.append({"kind": "rail", "name": f"tine_{k}", "link": "rake_lift", "points": pts, "r": 0.012, "mat": "wear_steel"})
        out.append({"kind": "box", "name": f"tine_{k}_clamp", "link": "rake_lift", "c": (BAR[0] + 0.03, y, BAR[2] - 0.01),
                    "size": (0.05, 0.04, 0.05), "mat": "steel"})
    return out


def _frame():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"push_arm_{sd}", "link": "rake_lift", "p0": (LIFT[0], s * 0.30, 0.0),
                    "p1": (BAR[0] - 0.05, s * 0.55, BAR[2]), "w": 0.06, "h": 0.08, "mat": "white_panel"})
        out.append({"kind": "box", "name": f"gauge_skid_{sd}", "link": "rake_lift", "c": (BAR[0] - 0.02, s * (W / 2 - 0.05), T.EDGE_Z + 0.06),
                    "size": (0.40, 0.03, 0.06), "mat": "wear_steel"})
        out.append({"kind": "beam", "name": f"skid_post_{sd}", "link": "rake_lift", "p0": (BAR[0] - 0.02, s * (W / 2 - 0.05), BAR[2]),
                    "p1": (BAR[0] - 0.02, s * (W / 2 - 0.05), T.EDGE_Z + 0.08), "w": 0.04, "h": 0.04, "mat": "white_panel"})
    out += [{"kind": "beam", "name": "toolbar", "link": "rake_lift", "p0": (BAR[0], W / 2, BAR[2]), "p1": (BAR[0], -W / 2, BAR[2]),
             "w": 0.10, "h": 0.10, "mat": "white_panel"},
            {"kind": "beam", "name": "push_arm_brace", "link": "rake_lift", "p0": (0.45, 0.42, -0.11), "p1": (0.45, -0.42, -0.11),
             "w": 0.05, "h": 0.06, "mat": "white_panel"},
            {"kind": "tube", "name": "lift_shaft", "link": "rake_lift", "p0": (LIFT[0], -0.34, 0), "p1": (LIFT[0], 0.34, 0), "r": 0.03,
             "mat": "steel"}]
    out += T.clevis("lift_clevis_l", (LIFT[0], 0.30, 0.0), gap=0.10)
    out += T.clevis("lift_clevis_r", (LIFT[0], -0.30, 0.0), gap=0.10)
    out += T.actuator("lift_ram", (0.06, 0, 0.16), (0.45, 0, -0.08), r=0.035, link0="base", link1="rake_lift")
    out.append({"kind": "box", "name": "lift_ram_mount", "c": (0.06, 0, 0.16), "size": (0.06, 0.10, 0.06), "mat": "steel"})
    return out


TOOL = {
    "base_mass": 15.0,
    "links": [{"name": "rake_lift", "pos": LIFT, "axis": (0, -1, 0), "limit": (-0.30, 0.45), "role": "tool", "mass": 55.0,
               "drive": T.drive(30000.0, 3000.0, 4000.0)}],
    "parts": [*T.coupler(1), *_frame(), *_tines()],
    "sites": [("rake_edge", "rake_lift", (BAR[0] + 0.21, 0, T.EDGE_Z), (1, 0, 0), "tool_edge",
               "Tine tip line centre (+Z = raking direction); fines pass between tines, rocks are carried",
               {"tool": "rake", "width_m": W, "tine_pitch_m": PITCH, "tines": TINES, "pass_size_m": PITCH - 0.024})],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"rake_lift": [("rake", ["white_panel", "wear_steel"])]}
PHYSICS_MATERIAL = {"rake": "steel"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.1, W, 0.8, 0.55)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "rock_rake"]
