import tool_kit as T

ASSET_ID = "loader_bucket"
ASSET_PATH = "concepts/construction_tools/loader_bucket"
FAMILY = "tool"
TITLE = "Front loader bucket (concept rover attachment)"
DOC = ("Front loader for Lunar Terrain Vehicle-class rovers: two lift arms on the quick-attach coupler raise a 1.6 m "
       "general-purpose bucket (about 0.18 m3 struck, roughly 270 kg of loose regolith) high enough to dump into the "
       "dump trailer, and a curl joint rolls the bucket back to carry or forward to dump. Sized so a 1 t rover stays "
       "stable in lunar gravity with a full bucket.")

TEXTURE_SETS, MATERIALS = T.materials()

W = 1.60
LIFT = (0.08, 0.0, 0.22)
CURL = (0.91, 0.0, -0.36)
EDGE = (1.50, T.EDGE_Z)
ARM_Y = 0.52
CAP = 0.18


def _bucket():
    shell = [EDGE, (1.12, T.EDGE_Z), (1.00, T.EDGE_Z + 0.08), (0.96, T.EDGE_Z + 0.28), (0.99, T.EDGE_Z + 0.46), (1.08, T.EDGE_Z + 0.52)]
    out = [{"kind": "extrude", "name": "shell", "link": "bucket", "profile": T.thick_profile(shell, 0.014), "y": (-W / 2, W / 2),
            "mat": "white_panel"},
           {"kind": "box", "name": "cutting_edge", "link": "bucket", "c": (EDGE[0] - 0.05, 0, EDGE[1] + 0.008), "size": (0.12, W, 0.02),
            "mat": "wear_steel"},
           {"kind": "box", "name": "spill_guard", "link": "bucket", "c": (1.07, 0, T.EDGE_Z + 0.58), "size": (0.03, W - 0.1, 0.12),
            "mat": "grating"}]
    side = [(EDGE[0], EDGE[1] - 0.01), (EDGE[0] - 0.02, EDGE[1] + 0.12), (1.20, T.EDGE_Z + 0.52), (1.08, T.EDGE_Z + 0.53), *reversed(shell[1:-1])]
    for sd, s in (("l", 1), ("r", -1)):
        y0 = s * W / 2
        out.append({"kind": "extrude", "name": f"side_plate_{sd}", "link": "bucket", "profile": side,
                    "y": tuple(sorted((y0, y0 + s * 0.012))), "mat": "wear_steel"})
        out += [{"kind": "box", "name": f"curl_lug_{sd}", "link": "bucket", "c": (CURL[0] + 0.02, s * ARM_Y, CURL[2]), "size": (0.12, 0.05, 0.14),
                 "mat": "steel"},
                {"kind": "box", "name": f"link_lug_{sd}", "link": "bucket", "c": (0.93, s * 0.22, T.EDGE_Z + 0.44), "size": (0.10, 0.05, 0.10),
                 "mat": "steel"}]
    for k, y in enumerate((-0.45, 0.0, 0.45)):
        out.append({"kind": "box", "name": f"back_stiffener_{k}", "link": "bucket", "c": (0.95, y, T.EDGE_Z + 0.26), "size": (0.03, 0.04, 0.40),
                    "mat": "white_panel"})
    return out


def _arms():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out += [{"kind": "beam", "name": f"lift_arm_{sd}", "link": "loader_lift", "p0": (LIFT[0], s * 0.28, LIFT[2]),
                 "p1": (0.55, s * ARM_Y, 0.02), "w": 0.06, "h": 0.10, "mat": "white_panel"},
                {"kind": "beam", "name": f"lift_arm_{sd}_lower", "link": "loader_lift", "p0": (0.55, s * ARM_Y, 0.02),
                 "p1": (CURL[0], s * ARM_Y, CURL[2]), "w": 0.06, "h": 0.10, "mat": "white_panel"}]
        out += T.clevis(f"lift_clevis_{sd}", (LIFT[0], s * 0.28, LIFT[2]), gap=0.08)
        out += T.actuator(f"lift_ram_{sd}", (0.05, s * 0.18, -0.12), (0.52, s * (ARM_Y - 0.08), 0.0), r=0.035, link0="base",
                          link1="loader_lift")
        out += T.actuator(f"curl_ram_{sd}", (0.50, s * 0.22, 0.10), (0.93, s * 0.22, T.EDGE_Z + 0.44), r=0.03, link0="loader_lift",
                          link1="bucket")
    out += [{"kind": "beam", "name": "cross_tube", "link": "loader_lift", "p0": (0.55, ARM_Y, 0.02), "p1": (0.55, -ARM_Y, 0.02),
             "w": 0.07, "h": 0.07, "mat": "white_panel"},
            {"kind": "tube", "name": "curl_pivot", "link": "loader_lift", "p0": (CURL[0], -ARM_Y - 0.04, CURL[2]),
             "p1": (CURL[0], ARM_Y + 0.04, CURL[2]), "r": 0.025, "mat": "steel"},
            {"kind": "box", "name": "tower", "c": (0.04, 0, 0.18), "size": (0.06, 0.62, 0.12), "mat": "anodised_grey"},
            {"kind": "box", "name": "ram_base", "c": (0.04, 0, -0.12), "size": (0.06, 0.50, 0.06), "mat": "steel"}]
    return out


TOOL = {
    "base_mass": 20.0,
    "links": [
        {"name": "loader_lift", "pos": LIFT, "axis": (0, -1, 0), "limit": (-0.15, 1.15), "role": "tool", "mass": 45.0,
         "drive": T.drive(60000.0, 6000.0, 9000.0)},
        {"name": "bucket", "parent": "loader_lift", "pos": CURL, "axis": (0, -1, 0), "limit": (-1.0, 0.85), "role": "tool", "mass": 55.0,
         "drive": T.drive(30000.0, 3000.0, 5000.0)},
    ],
    "parts": [*T.coupler(1), *_arms(), *_bucket()],
    "sites": [
        ("bucket_edge", "bucket", (EDGE[0], 0, EDGE[1]), (1, 0, 0), "tool_edge",
         "Bucket cutting edge centre (+Z = cutting direction)",
         {"tool": "bucket", "width_m": W, "height_m": 0.52, "capacity_m3": CAP, "bulk_density_kg_m3": T.BULK}),
        ("bucket_volume", "bucket", (1.18, 0, T.EDGE_Z + 0.20), (0, 0, 1), "payload", "Bucket load centroid (struck capacity)",
         {"volume_m3": CAP, "capacity_kg": CAP * T.BULK, "bulk_density_kg_m3": T.BULK}),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"bucket": [("bucket", ["white_panel", "wear_steel"])],
             "loader_lift": [("arms", ["white_panel"])]}
PHYSICS_MATERIAL = {"bucket": "steel", "arms": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.6, W, 1.0, 0.75)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "loader_bucket"]
