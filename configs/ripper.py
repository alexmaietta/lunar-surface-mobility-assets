import tool_kit as T

ASSET_ID = "ripper"
ASSET_PATH = "concepts/construction_tools/ripper"
FAMILY = "tool"
TITLE = "Three-shank ripper (concept rover attachment)"
DOC = ("Rear-mounted ripper for Lunar Terrain Vehicle-class rovers. Lunar regolith densifies quickly below the loose top "
       "few centimetres (about 1.3 g/cm3 at the surface to 1.85 g/cm3 by 30-60 cm), so a ripper loosens the dense layer "
       "before a blade, bucket or drum digs it. Three curved steel shanks with replaceable tips hang from a toolbar on a "
       "lifting frame and reach about 0.35 m below grade at full depth.")

TEXTURE_SETS, MATERIALS = T.materials()

LIFT = (-0.10, 0.0, 0.0)
BAR = (-0.68, 0.0, -0.06)
SHANK_Y = (-0.60, 0.0, 0.60)
TIP = (-0.96, T.EDGE_Z + 0.04)


def _shank(k, y):
    pts = [(BAR[0] - 0.02, y, BAR[2] + 0.04), (BAR[0] - 0.10, y, BAR[2] - 0.18), (BAR[0] - 0.20, y, T.EDGE_Z + 0.18), (TIP[0] + 0.05, y, TIP[1] + 0.03)]
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        c = tuple((a[j] + b[j]) / 2 for j in range(3))
        d = tuple(b[j] - a[j] for j in range(3))
        L = sum(v * v for v in d) ** 0.5
        out.append({"kind": "obox", "name": f"shank_{k}_seg_{i}", "link": "ripper_lift", "c": c, "ax": tuple(v / L for v in d),
                    "ay": (0, 1, 0), "size": (L + 0.03, 0.04, 0.12 - 0.02 * i), "mat": "steel"})
    out.append({"kind": "obox", "name": f"shank_{k}_tip", "link": "ripper_lift", "c": (TIP[0] + 0.02, y, TIP[1] + 0.02),
                "ax": (-0.85, 0, -0.53), "ay": (0, 1, 0), "size": (0.16, 0.05, 0.04), "mat": "wear_steel"})
    out.append({"kind": "box", "name": f"shank_{k}_pocket", "link": "ripper_lift", "c": (BAR[0] - 0.02, y, BAR[2]),
                "size": (0.12, 0.08, 0.16), "mat": "anodised_grey"})
    return out


def _frame():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out.append({"kind": "beam", "name": f"lower_link_{sd}", "link": "ripper_lift", "p0": (LIFT[0], s * 0.30, 0.0),
                    "p1": (BAR[0] + 0.05, s * 0.45, BAR[2]), "w": 0.06, "h": 0.09, "mat": "white_panel"})
    out += [{"kind": "beam", "name": "toolbar", "link": "ripper_lift", "p0": (BAR[0], 0.85, BAR[2]), "p1": (BAR[0], -0.85, BAR[2]),
             "w": 0.12, "h": 0.12, "mat": "white_panel"},
            {"kind": "beam", "name": "link_brace", "link": "ripper_lift", "p0": (-0.40, 0.36, -0.03), "p1": (-0.40, -0.36, -0.03),
             "w": 0.05, "h": 0.06, "mat": "white_panel"},
            {"kind": "tube", "name": "lift_shaft", "link": "ripper_lift", "p0": (LIFT[0], -0.34, 0), "p1": (LIFT[0], 0.34, 0), "r": 0.03,
             "mat": "steel"}]
    out += T.clevis("lift_clevis_l", (LIFT[0], 0.30, 0.0), gap=0.10)
    out += T.clevis("lift_clevis_r", (LIFT[0], -0.30, 0.0), gap=0.10)
    out += T.actuator("lift_ram", (-0.06, 0, 0.18), (-0.45, 0, 0.0), r=0.04, link0="base", link1="ripper_lift")
    out.append({"kind": "box", "name": "lift_ram_mount", "c": (-0.06, 0, 0.18), "size": (0.06, 0.10, 0.06), "mat": "steel"})
    return out


TOOL = {
    "base_mass": 15.0,
    "mount_axis": (1, 0, 0),
    "links": [{"name": "ripper_lift", "pos": LIFT, "axis": (0, 1, 0), "limit": (-0.55, 0.35), "role": "tool", "mass": 70.0,
               "drive": T.drive(50000.0, 5000.0, 8000.0)}],
    "parts": [*T.coupler(-1), *_frame(), *[q for k, y in enumerate(SHANK_Y) for q in _shank(k, y)]],
    "sites": [(f"shank_{k}_tip", "ripper_lift", (TIP[0], y, TIP[1]), (1, 0, 0), "tool_edge",
               "Ripper tip (+Z = towing direction); loosens a narrow strip of dense regolith",
               {"tool": "ripper", "width_m": 0.06, "loosen_width_m": 0.35}) for k, y in enumerate(SHANK_Y)],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"ripper_lift": [("ripper", ["white_panel", "steel"])]}
PHYSICS_MATERIAL = {"ripper": "steel"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.1, 1.8, 0.8, -0.55, sx=-1)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "ripper"]
