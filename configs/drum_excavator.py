import math

import tool_kit as T

ASSET_ID = "drum_excavator"
ASSET_PATH = "concepts/construction_tools/drum_excavator"
FAMILY = "tool"
TITLE = "Bucket-drum excavator (concept rover attachment)"
DOC = ("Front bucket-drum excavator for Lunar Terrain Vehicle-class rovers, after NASA's RASSOR and IPEx drums and the "
       "drum-excavator attachments shown on Astrolab FLEX by Astroport and Interlune. A pitching arm on the quick-attach "
       "coupler carries a pair of 0.54 m diameter, 0.62 m wide hollow drums on one powered shaft. Staggered scoops fill "
       "the drums when they turn one way at a shallow cut, so excavation forces stay low for a light vehicle, and "
       "reversing the drums dumps the load (about 0.10 m3, 150 kg).")

TEXTURE_SETS, MATERIALS = T.materials()

R, DW, GAP = 0.27, 0.62, 0.08
SHOULDER = (0.10, 0.0, 0.05)
AXLE = (0.98, 0.0, T.EDGE_Z + R)
ARM_Y = DW + GAP / 2 + 0.06
CAP = 0.10
SCOOPS = 8


def _drum(tag, y0, y1):
    yc = (y0 + y1) / 2
    out = [{"kind": "lathe", "name": f"drum_{tag}_shell", "link": "drums", "c": (AXLE[0], yc, AXLE[2]), "n": (0, 1, 0), "sides": 48,
            "mat": "anodised_grey",
            "profile": [(R - 0.012, -(y1 - y0) / 2), (R, -(y1 - y0) / 2), (R, (y1 - y0) / 2), (R - 0.012, (y1 - y0) / 2),
                        (R - 0.012, -(y1 - y0) / 2)]}]
    for sd, y in (("a", y0), ("b", y1)):
        out.append({"kind": "lathe", "name": f"drum_{tag}_end_{sd}", "link": "drums", "c": (AXLE[0], y, AXLE[2]), "n": (0, 1, 0), "sides": 48,
                    "mat": "white_panel", "profile": [(0.001, -0.006), (R + 0.006, -0.006), (R + 0.006, 0.006), (0.001, 0.006)]})
    for row, (ya, yb) in enumerate(((y0 + 0.03, yc - 0.015), (yc + 0.015, y1 - 0.03))):
        for k in range(SCOOPS):
            a = 2 * math.pi * (k + 0.5 * row) / SCOOPS
            rd = (math.cos(a), 0.0, math.sin(a))
            tg = (-math.sin(a), 0.0, math.cos(a))
            c = (AXLE[0] + rd[0] * (R + 0.003), (ya + yb) / 2, AXLE[2] + rd[2] * (R + 0.003))
            out.append({"kind": "obox", "name": f"drum_{tag}_slot_{row}_{k}", "link": "drums", "c": c, "ax": tg, "ay": (0, 1, 0),
                        "size": (0.09, yb - ya, 0.004), "mat": "anodised_dark"})
            lip = (c[0] + tg[0] * 0.05 + rd[0] * 0.012, c[1], c[2] + tg[2] * 0.05 + rd[2] * 0.012)
            out.append({"kind": "obox", "name": f"drum_{tag}_lip_{row}_{k}", "link": "drums", "c": lip, "ax": tg, "ay": (0, 1, 0),
                        "size": (0.02, yb - ya, 0.024), "mat": "wear_steel"})
    return out


def _arm():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        y = s * ARM_Y
        out += [{"kind": "beam", "name": f"arm_{sd}", "link": "drum_arm", "p0": (SHOULDER[0], s * 0.30, SHOULDER[2]),
                 "p1": (0.55, y, -0.12), "w": 0.06, "h": 0.09, "mat": "white_panel"},
                {"kind": "beam", "name": f"arm_{sd}_fore", "link": "drum_arm", "p0": (0.55, y, -0.12), "p1": AXLE[:1] + (y, AXLE[2]),
                 "w": 0.06, "h": 0.09, "mat": "white_panel"},
                {"kind": "lathe", "name": f"drive_housing_{sd}", "link": "drum_arm", "c": (AXLE[0], y, AXLE[2]), "n": (0, s, 0), "sides": 32,
                 "mat": "anodised_dark", "profile": [(0.001, -0.03), (0.09, -0.03), (0.09, 0.06), (0.05, 0.09), (0.001, 0.09)]}]
        out += T.clevis(f"shoulder_clevis_{sd}", (SHOULDER[0], s * 0.30, SHOULDER[2]), gap=0.08)
        out += T.actuator(f"arm_ram_{sd}", (0.05, s * 0.20, 0.20), (0.55, s * (ARM_Y - 0.05), -0.08), r=0.035, link0="base",
                          link1="drum_arm")
    out += [{"kind": "beam", "name": "arm_cross", "link": "drum_arm", "p0": (0.55, ARM_Y, -0.12), "p1": (0.55, -ARM_Y, -0.12),
             "w": 0.07, "h": 0.07, "mat": "white_panel"},
            {"kind": "box", "name": "dust_shield", "link": "drum_arm", "c": (AXLE[0] - 0.12, 0, AXLE[2] + R + 0.06),
             "size": (0.42, 2 * DW + GAP, 0.012), "mat": "white_panel"},
            {"kind": "tube", "name": "shoulder_shaft", "link": "drum_arm", "p0": (SHOULDER[0], -0.34, SHOULDER[2]),
             "p1": (SHOULDER[0], 0.34, SHOULDER[2]), "r": 0.03, "mat": "steel"},
            {"kind": "box", "name": "ram_mount", "c": (0.05, 0, 0.20), "size": (0.06, 0.48, 0.06), "mat": "steel"}]
    return out


TOOL = {
    "base_mass": 15.0,
    "links": [
        {"name": "drum_arm", "pos": SHOULDER, "axis": (0, -1, 0), "limit": (-0.45, 0.85), "role": "tool", "mass": 35.0,
         "drive": T.drive(40000.0, 4000.0, 6000.0)},
        {"name": "drums", "parent": "drum_arm", "pos": AXLE, "axis": (0, 1, 0), "role": "excavate", "mass": 45.0,
         "drive": {"kind": "velocity", "stiffness": 0.0, "damping": 400.0, "max_force": 900.0}},
    ],
    "parts": [*T.coupler(1), *_arm(), *_drum("l", GAP / 2, GAP / 2 + DW), *_drum("r", -GAP / 2 - DW, -GAP / 2),
              {"kind": "tube", "name": "drum_shaft", "link": "drums", "p0": (AXLE[0], -ARM_Y + 0.03, AXLE[2]),
               "p1": (AXLE[0], ARM_Y - 0.03, AXLE[2]), "r": 0.035, "mat": "steel"}],
    "sites": [
        ("drum_cut", "drum_arm", (AXLE[0], 0, AXLE[2] - R), (1, 0, 0), "tool_edge",
         "Lowest scoop lip of the drum pair (cutting line when digging, +Z = cutting direction)",
         {"tool": "drum", "width_m": 2 * DW + GAP, "radius_m": R, "capacity_m3": CAP, "bulk_density_kg_m3": T.BULK}),
        ("drum_volume", "drums", AXLE, (0, 1, 0), "payload", "Drum pair regolith store",
         {"volume_m3": CAP, "capacity_kg": CAP * T.BULK, "bulk_density_kg_m3": T.BULK}),
    ],
}

ROBOT_TYPE = "Manipulator"
COLLIDERS = {"drums": [("drum", ["anodised_grey", "white_panel"], {"islands": True})],
             "drum_arm": [("arm", ["white_panel"])]}
PHYSICS_MATERIAL = {"drum": "steel", "arm": "structure"}
PHYSICS_MATERIALS = T.PHYSICS_MATERIALS
RENDER_VIEWS = T.views(1.4, 2 * DW + GAP + 0.3, 0.9, 0.65)
RENDER_GROUND_Z = T.GROUND
SEMANTIC_CLASS = ["construction_tool", "excavator", "bucket_drum"]
