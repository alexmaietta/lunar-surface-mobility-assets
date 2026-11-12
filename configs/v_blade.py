import math

import tool_kit as T

ASSET_ID = "v_blade"
ASSET_PATH = "concepts/construction_tools/v_blade"
FAMILY = "tool"
TITLE = "Hinged V-blade plow (concept rover attachment)"
DOC = ("Front-mounted hinged V-blade for Lunar Terrain Vehicle-class rovers, after terrestrial V-plows. Two 1.45 m curved "
       "composite wings pivot independently on a steel nose post at the end of a lifting push frame, so the blade works as "
       "a V (splits regolith to both sides, opens a track or trench line), straight (dozing), scoop or inverted V (carries "
       "a load), or angled left or right (casts a windrow to one side when building a berm line). The wings are modelled "
       "in a 25 degree V; each wing joint runs from a 25 degree scoop through straight to a 35 degree V.")

TEXTURE_SETS, MATERIALS = T.materials()

L, H = 1.45, 0.62
SWEEP = math.radians(25)
LIFT = (0.10, 0.0, 0.0)
NOSE = (0.98, 0.0, -0.28)
PROFILE = [(0.05, T.EDGE_Z), (-0.03, T.EDGE_Z + 0.16), (-0.06, T.EDGE_Z + 0.34), (-0.05, T.EDGE_Z + 0.50), (0.00, T.EDGE_Z + H)]


def _dirs(s):
    d = (-math.sin(SWEEP), s * math.cos(SWEEP), 0.0)
    n = (math.cos(SWEEP), s * math.sin(SWEEP), 0.0)
    return d, n


def _wing(tag, s):
    link = f"wing_{tag}"
    d, n = _dirs(s)
    o = (NOSE[0] + d[0] * 0.05, NOSE[1] + d[1] * 0.05, 0.0)
    out = T.moldboard_strips(f"{link}_moldboard", link, o, d, n, L, PROFILE, 0.022, "composite")
    e0 = PROFILE[0]
    out.append({"kind": "obox", "name": f"{link}_cutting_edge", "link": link,
                "c": (o[0] + d[0] * L / 2 + n[0] * (e0[0] - 0.01), o[1] + d[1] * L / 2 + n[1] * (e0[0] - 0.01), e0[1] + 0.045),
                "ax": d, "ay": (0, 0, 1), "size": (L, 0.09, 0.03), "mat": "wear_steel"})
    tip = (o[0] + d[0] * L, o[1] + d[1] * L)
    out.append({"kind": "obox", "name": f"{link}_end_plate", "link": link, "c": (tip[0] - n[0] * 0.02, tip[1] - n[1] * 0.02, T.EDGE_Z + H / 2),
                "ax": n, "ay": (0, 0, 1), "size": (0.16, H, 0.02), "mat": "wear_steel"})
    for k, f in enumerate((0.2, 0.55, 0.9)):
        p = (o[0] + d[0] * L * f - n[0] * 0.10, o[1] + d[1] * L * f - n[1] * 0.10)
        out.append({"kind": "obox", "name": f"{link}_rib_{k}", "link": link, "c": (p[0], p[1], T.EDGE_Z + H * 0.48), "ax": n,
                    "ay": (0, 0, 1), "size": (0.10, H * 0.8, 0.02), "mat": "white_panel"})
    out.append({"kind": "obox", "name": f"{link}_back_beam", "link": link,
                "c": (o[0] + d[0] * L * 0.5 - n[0] * 0.13, o[1] + d[1] * L * 0.5 - n[1] * 0.13, NOSE[2]), "ax": d, "ay": (0, 0, 1),
                "size": (L - 0.1, 0.10, 0.06), "mat": "white_panel"})
    hinge = (NOSE[0], NOSE[1], 0)
    for k, z in enumerate((T.EDGE_Z + 0.10, T.EDGE_Z + H - 0.12)):
        out.append({"kind": "obox", "name": f"{link}_hinge_knuckle_{k}", "link": link,
                    "c": (hinge[0] + d[0] * 0.05, hinge[1] + d[1] * 0.05, z + s * 0.04), "ax": d, "ay": (0, 0, 1),
                    "size": (0.12, 0.08, 0.05), "mat": "steel"})
    ram_end = (o[0] + d[0] * L * 0.55 - n[0] * 0.14, o[1] + d[1] * L * 0.55 - n[1] * 0.14, NOSE[2] + 0.04)
    out += T.actuator(f"{link}_swing_ram", (0.58, s * 0.20, -0.20), ram_end, r=0.028, link0="blade_lift", link1=link)
    return out


def _frame():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"push_arm_{sd}", "link": "blade_lift", "p0": (LIFT[0], s * 0.30, 0.0),
                    "p1": (NOSE[0] - 0.14, s * 0.07, NOSE[2]), "w": 0.07, "h": 0.09, "mat": "white_panel"})
    z0, z1 = T.EDGE_Z - 0.02, T.EDGE_Z + H + 0.04
    out += [{"kind": "beam", "name": "push_arm_brace", "link": "blade_lift", "p0": (0.45, 0.22, -0.13), "p1": (0.45, -0.22, -0.13),
             "w": 0.05, "h": 0.06, "mat": "white_panel"},
            {"kind": "box", "name": "nose_block", "link": "blade_lift", "c": (NOSE[0] - 0.10, 0, NOSE[2]), "size": (0.10, 0.20, 0.14),
             "mat": "anodised_grey"},
            {"kind": "tube", "name": "nose_post", "link": "blade_lift", "p0": (NOSE[0], 0, z0), "p1": (NOSE[0], 0, z1), "r": 0.045,
             "mat": "steel"},
            {"kind": "lathe", "name": "nose_cap", "link": "blade_lift", "c": (NOSE[0], 0, z1), "n": (0, 0, 1),
             "profile": [(0.001, 0), (0.06, 0), (0.05, 0.03), (0.001, 0.05)], "mat": "steel"},
            {"kind": "frustum", "name": "nose_shoe", "link": "blade_lift", "c": (NOSE[0] + 0.03, 0),
             "bottom": (T.EDGE_Z - 0.02, 0.12, 0.10), "top": (T.EDGE_Z + 0.12, 0.08, 0.10), "mat": "wear_steel"},
            {"kind": "tube", "name": "lift_shaft", "link": "blade_lift", "p0": (LIFT[0], -0.34, 0), "p1": (LIFT[0], 0.34, 0), "r": 0.03,
             "mat": "steel"}]
    out += T.clevis("lift_clevis_l", (LIFT[0], 0.30, 0.0), gap=0.10)
    out += T.clevis("lift_clevis_r", (LIFT[0], -0.30, 0.0), gap=0.10)
    out += T.actuator("lift_ram", (0.06, 0, 0.16), (0.48, 0, -0.10), r=0.04, link0="base", link1="blade_lift")
    out.append({"kind": "box", "name": "lift_ram_mount", "c": (0.06, 0, 0.16), "size": (0.06, 0.10, 0.06), "mat": "steel"})
    return out


def _edge_site(tag, s):
    d, n = _dirs(s)
    o = (NOSE[0] + d[0] * 0.05, NOSE[1] + d[1] * 0.05)
    c = (o[0] + d[0] * L / 2 + n[0] * PROFILE[0][0], o[1] + d[1] * L / 2 + n[1] * PROFILE[0][0], T.EDGE_Z)
    return (f"wing_{tag}_edge", f"wing_{tag}", c, n, "tool_edge",
            f"{'Left' if s > 0 else 'Right'} wing cutting edge centre (+Z = wing face normal); the wing spans width_m along it",
            {"tool": "blade", "width_m": L, "height_m": H, "capacity_m3": 0.22, "bulk_density_kg_m3": T.BULK})


WING_LIMIT = (math.radians(-50), math.radians(10))

TOOL = {
    "base_mass": 15.0,
    "links": [
        {"name": "blade_lift", "pos": LIFT, "axis": (0, -1, 0), "limit": (-0.30, 0.45), "role": "tool", "mass": 45.0,
         "drive": T.drive(40000.0, 4000.0, 6000.0)},
        {"name": "wing_l", "parent": "blade_lift", "pos": NOSE, "axis": (0, 0, 1), "limit": WING_LIMIT, "role": "tool", "mass": 40.0,
         "drive": T.drive(20000.0, 2000.0, 3000.0)},
        {"name": "wing_r", "parent": "blade_lift", "pos": NOSE, "axis": (0, 0, -1), "limit": WING_LIMIT, "role": "tool", "mass": 40.0,
         "drive": T.drive(20000.0, 2000.0, 3000.0)},
    ],
    "parts": [*T.coupler(1), *_frame(), *_wing("l", 1), *_wing("r", -1)],
    "sites": [_edge_site("l", 1), _edge_site("r", -1),
              ("nose_point", "blade_lift", (NOSE[0] + 0.05, 0, T.EDGE_Z), (1, 0, 0), "reference", "V nose at the cutting edge")],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {r"wing_[lr]": [("wing", ["composite", "wear_steel"])],
             "blade_lift": [("push_frame", ["white_panel", "anodised_grey"])]}
PHYSICS_MATERIAL = {"wing": "steel", "push_frame": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.3, 2.7, 0.9, 0.7)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "v_blade", "plow"]
