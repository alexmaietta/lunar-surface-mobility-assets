import math

import rover_kit as K

ASSET_ID = "flex"
ASSET_PATH = "astrolab/flex/rover"
FAMILY = "rover"
TITLE = "Astrolab FLEX"
DOC = ("Venturi Astrolab FLEX (Flexible Logistics and Exploration) full-scale terrestrial prototype, the basis of the "
       "CLV-1 Lunar Terrain Vehicle (3.35 x 2.50 m over tyres, wheelbase 2.7 m, track 2.1 m, deck rim 2.0 m, about "
       "500 kg): an open U-frame with bronze trapezoid side walls inside white frames, a front avionics bay with a "
       "4 x 3 drawer grid, an open underslung cargo bay, four active wheel-on-limb legs with belt-driven pivots, "
       "all-wheel and crab steering, hub motors and carbon fenders on 0.67 m airless tyres, two standing crew "
       "stations on a removable rear deck, a 2.4 m six-axis arm folded across the front, lamp pods on the four "
       "corner posts, a tall antenna mast and a hinged 3 m2 solar array that stows flat on the top deck and "
       "tilts up into a vertical tower.")

TEXTURE_SETS, MATERIALS = K.materials(
    overrides={"panel_bronze": {"set": "panel_bronze", "normal": 0.5}, "frame_white": {"color": (0.88, 0.88, 0.86), "roughness": 0.35},
               "lamp_amber": {"color": (1.0, 0.55, 0.15), "roughness": 0.2, "emission": (1.0, 0.50, 0.12, 5.0)}},
    textures={"panel_bronze": ("panel", dict(colour=(0.25, 0.20, 0.13), tile_m=1.0, rough0=0.30, metallic=0.7, fastener_pitch=0.12))})

R_W, W_W, WB, TRACK = 0.335, 0.35, 2.70, 2.10
TOP = 2.00
WY = 0.80
WALL = [(-0.60, 0.55), (0.60, 0.55), (1.00, TOP), (-1.00, TOP)]
POST_X = 0.97
BAY = (0.62, 1.04)
GRID_Z = (0.66, 1.62)
STEER = (math.radians(-90), math.radians(90))
SOLAR_HINGE = (-0.96, 0, TOP + 0.05)
SOLAR_L, SOLAR_W = 1.80, 1.66
ARM_BASE = (BAY[1] + 0.12, WY - 0.12, TOP - 0.14)


def _walls():
    out = []
    for s in (-1, 1):
        out.append({"kind": "extrude", "name": f"side_wall_{s + 1}", "profile": WALL, "y": (s * WY - 0.015, s * WY + 0.015), "mat": "panel_bronze"})
        out.append({"kind": "rail", "name": f"wall_frame_{s + 1}", "r": 0.04, "mat": "frame_white", "closed": True,
                    "points": [(x, s * (WY + 0.02), z) for x, z in WALL]})
        out.append({"kind": "box", "name": f"top_rail_{s + 1}", "c": (0, s * (WY + 0.02), TOP + 0.02), "size": (2.10, 0.10, 0.08),
                    "mat": "frame_white"})
        for e in (-1, 1):
            out.append({"kind": "box", "name": f"post_{s + 1}_{e + 1}", "c": (e * POST_X, s * (WY + 0.03), 1.25), "size": (0.09, 0.09, 1.56),
                        "mat": "frame_white"})
            out.append({"kind": "box", "name": f"limb_mount_{s + 1}_{e + 1}", "c": (e * (POST_X - 0.07), s * (WY + 0.06), 0.80),
                        "size": (0.22, 0.10, 0.30), "mat": "frame_white"})
            out.append({"kind": "box", "name": f"lamp_pod_{s + 1}_{e + 1}", "c": (e * (POST_X + 0.02), s * (WY + 0.13), TOP - 0.16),
                        "size": (0.12, 0.17, 0.30), "mat": "anodised_dark"})
            out.append({"kind": "box", "name": f"lamp_strip_{s + 1}_{e + 1}", "c": (e * (POST_X + 0.085), s * (WY + 0.13), TOP - 0.32),
                        "size": (0.01, 0.12, 0.03), "mat": "lamp" if e > 0 else "lamp_amber"})
    out.append({"kind": "box", "name": "rear_top_beam", "c": (-POST_X, 0, TOP - 0.08), "size": (0.10, 2 * WY, 0.22), "mat": "anodised_dark"})
    out.append({"kind": "box", "name": "rear_low_beam", "c": (-POST_X, 0, 0.56), "size": (0.08, 2 * WY, 0.08), "mat": "anodised_dark"})
    out.append({"kind": "box", "name": "top_cross_mid", "c": (0, 0, TOP + 0.02), "size": (0.08, 2 * WY, 0.06), "mat": "frame_white"})
    for x in (0.55, -0.55):
        out.append({"kind": "beam", "name": f"belly_cross_{int(x * 100)}", "p0": (x, -WY, 0.58), "p1": (x, WY, 0.58), "w": 0.06, "h": 0.06,
                    "mat": "anodised_dark"})
    return out


def _avionics_bay():
    x0, x1 = BAY
    out = [{"kind": "box", "name": "avionics_bay", "c": ((x0 + x1) / 2 - 0.02, 0, (GRID_Z[0] - 0.04 + TOP) / 2),
            "size": (x1 - x0 - 0.04, 2 * WY - 0.04, TOP - GRID_Z[0] + 0.04), "mat": "white_panel"},
           {"kind": "box", "name": "drawer_frame", "c": (x1 + 0.005, 0, (GRID_Z[0] + GRID_Z[1]) / 2),
            "size": (0.03, 2 * WY - 0.10, GRID_Z[1] - GRID_Z[0] + 0.04), "mat": "anodised_dark"},
           {"kind": "box", "name": "upper_fascia", "c": (x1 - 0.01, 0, (GRID_Z[1] + TOP) / 2 + 0.02),
            "size": (0.04, 2 * WY - 0.04, TOP - GRID_Z[1] - 0.04), "mat": "white_panel"},
           {"kind": "box", "name": "fascia_band", "c": (x1 + 0.012, 0, TOP - 0.06), "size": (0.02, 2 * WY - 0.30, 0.08), "mat": "anodised_dark"}]
    cw = (2 * WY - 0.14) / 4
    rh = (GRID_Z[1] - GRID_Z[0]) / 3
    faces = ("grey_panel", "anodised_dark", "mli_gold", "white_panel")
    for i in range(4):
        for j in range(3):
            out.append({"kind": "box", "name": f"drawer_{i}_{j}", "c": (x1 + 0.03, -WY + 0.07 + cw * (i + 0.5), GRID_Z[0] + rh * (j + 0.5)),
                        "size": (0.03, cw - 0.03, rh - 0.03), "mat": faces[(i * 2 + j * 3) % 4]})
    return out


def _crew_deck():
    v = "Crew:crewed"
    x0, x1 = -POST_X - 0.05, -1.58
    z = 0.95
    out = [{"kind": "box", "name": "crew_deck", "c": ((x0 + x1) / 2, 0, z), "size": (x0 - x1, 1.50, 0.04), "mat": "grating", "variant": v}]
    for s in (-1, 1):
        out.append({"kind": "beam", "name": f"crew_deck_strut_{s + 1}", "p0": (x0 + 0.05, s * 0.72, z - 0.03), "p1": (x1, s * 0.72, z - 0.03),
                    "w": 0.06, "h": 0.07, "mat": "frame_white", "variant": v})
        out.append({"kind": "beam", "name": f"crew_deck_brace_{s + 1}", "p0": (x0, s * 0.72, 0.62), "p1": (x1 + 0.10, s * 0.72, z - 0.06),
                    "w": 0.05, "h": 0.05, "mat": "frame_white", "variant": v})
    out.append({"kind": "box", "name": "crew_backrest_bar", "c": (x1 + 0.08, 0, z + 1.00), "size": (0.06, 1.30, 0.06), "mat": "frame_white",
                "variant": v})
    out.append({"kind": "box", "name": "console_arm", "c": (-0.98, 0, 1.50), "size": (0.08, 0.10, 0.20), "mat": "aluminium", "variant": v})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "spring", "grousers": 20, "spokes": 10, "spoke_curve": 0.25, "hub_frac": 0.42, "rim_frac": 0.74,
              "grouser_h": 0.03, "mass": 18.0, "spoke_mat": "anodised_dark", "rim_mat": "aluminium", "hub_mat": "aluminium"},
    "wheels": K.four_wheels(WB, TRACK, STEER),
    "suspension": {"type": "trailing_arm", "active": True, "arm_dx": 0.45, "pivot_dz": 0.47, "upper_dz": 0.36, "kingpin_off": 0.23,
                   "travel": (0.30, 0.36), "static_rad": 0.10, "beam": 0.09, "arm_mat": "anodised_dark", "knuckle_mat": "anodised_dark"},
    "fenders": {"gap": 0.04, "overhang": 0.015, "arc": (-75, 65), "mat": "composite"},
    "parts": [
        *_walls(),
        *_avionics_bay(),
        *_crew_deck(),
        {"kind": "box", "name": "cargo_container", "c": (0, 0, 1.20), "size": (1.10, 1.40, 1.00), "mat": "mli_gold", "variant": "Crew:cargo"},
        {"kind": "box", "name": "cargo_hanger", "c": (0, 0, 1.85), "size": (1.20, 1.50, 0.06), "mat": "anodised_dark", "variant": "Crew:cargo"},
        {"kind": "box", "name": "antenna_base", "c": (0.90, -(WY + 0.02), TOP + 0.08), "size": (0.10, 0.10, 0.10), "mat": "anodised_dark"},
        {"kind": "tube", "name": "antenna_mast", "p0": (0.90, -(WY + 0.02), TOP + 0.12), "p1": (0.90, -(WY + 0.02), 3.85), "r": 0.022, "r1": 0.014,
         "mat": "anodised_dark"},
        {"kind": "tube", "name": "antenna_tip", "p0": (0.90, -(WY + 0.02), 3.85), "p1": (0.90, -(WY + 0.02), 3.92), "r": 0.025, "mat": "radome"},
        {"kind": "box", "name": "arm_pedestal", "c": (BAY[1] + 0.06, ARM_BASE[1], ARM_BASE[2]), "size": (0.10, 0.22, 0.22), "mat": "anodised_dark"},
        {"kind": "box", "name": "solar_cradle_f", "c": (0.78, 0, TOP + 0.04), "size": (0.06, 1.40, 0.04), "mat": "anodised_dark"},
    ],
    "crew": {"variant": "Crew:crewed", "x": -1.28, "floor_z": 0.97, "seats_y": (0.38, -0.38), "style": "stand", "console": (-0.92, 0, 1.68)},
    "masts": [{"name": "nav_mast", "base": (0.90, 0.45, TOP + 0.02), "h": 0.16, "r": 0.03, "head": (0.10, 0.32, 0.09), "cams": (-0.12, 0.12),
               "lamp": True}],
    "solar": [{"name": "solar_array", "c": (SOLAR_HINGE[0] + SOLAR_L / 2 + 0.02, 0, TOP + 0.08), "u": (1, 0, 0), "v": (0, 1, 0), "w": SOLAR_L,
               "h": SOLAR_W, "normal": (0, 0, 1), "mass": 15.0,
               "hinge": {"pos": SOLAR_HINGE, "axis": (0, -1, 0), "limit": (0.0, math.radians(95)), "k": 3000.0, "c": 300.0, "tau": 800.0}}],
    "arm": {"base": ARM_BASE, "up": (1, 0, 0), "stow_dir": (0, 0, -1), "side": (0, 1, 0), "fold_off": (1, 0, 0),
            "lengths": (0.975, 0.90, 0.307), "r": 0.05, "mat": "white_panel", "mass": 45.0, "tau": 600.0},
    "lights": [
        ((POST_X + 0.09, WY + 0.13, TOP - 0.14), (1, 0, -0.15), 0.06, "head_lamp_l"),
        ((POST_X + 0.09, -(WY + 0.13), TOP - 0.14), (1, 0, -0.15), 0.06, "head_lamp_r"),
        ((-(POST_X + 0.09), WY + 0.13, TOP - 0.14), (-1, 0, -0.15), 0.06, "rear_lamp_l"),
        ((-(POST_X + 0.09), -(WY + 0.13), TOP - 0.14), (-1, 0, -0.15), 0.06, "rear_lamp_r"),
    ],
    "sites": [
        ("underslung_bay", "chassis", (0, 0, 0.58), (0, 0, -1), "payload_interface", "Underslung cargo bay (1.5 x 2.0 x 1.0 m envelope)"),
        ("top_payload_l", "chassis", (0, 0.40, TOP + 0.05), (0, 0, 1), "payload_interface", "Top-deck payload envelope (1.5 x 0.75 m)"),
        ("top_payload_r", "chassis", (0, -0.40, TOP + 0.05), (0, 0, 1), "payload_interface", "Top-deck payload envelope (1.5 x 0.75 m)"),
        ("drawer_grid", "chassis", (BAY[1] + 0.05, 0, (GRID_Z[0] + GRID_Z[1]) / 2), (1, 0, 0), "payload_interface",
         "Front avionics bay 4 x 3 drawer grid"),
        *[(f"lift_point_{n}", "chassis", (e * POST_X, s * (WY + 0.03), TOP + 0.06), (0, 0, 1), "handling", "Corner-post lift point")
          for n, e, s in (("fl", 1, 1), ("fr", 1, -1), ("rl", -1, 1), ("rr", -1, -1))],
    ],
    "imu": (0, 0, 1.0),
}

MASS = {
    "empty": {"mass": 500.0, "com_z": 1.10, "source": "press: terrestrial prototype about 500 kg (1,100 lb)"},
    "crewed": {"mass": 1040.0, "com_z": 1.30, "com_x": -0.45, "source": "estimate: + 2 suited crew (2 x 220 kg) + 100 kg"},
    "cargo": {"mass": 1500.0, "com_z": 1.05, "source": "Astrolab: up to 1,000 kg payload"},
}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (2.0, 1.7, 1.5)
GEOMETRY_VARIANTS = {"Crew": ["crewed", "cargo"], "Solar": ["stowed", "deployed"]}
GEOMETRY_VARIANT_JOINTS = {"Solar": {"deployed": {"solar_array": math.pi / 2}}}

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("panel_bronze", "white_panel", "frame_white"))
SIMPLE_TRIS = 24000
RENDER_VIEWS = {**K.views(3.4, 2.5, 2.4, centre_z=1.2), "front": ((8.5, 0.0, 1.6), (0, 0, 1.2), 35),
                "rear": ((-8.5, 0.0, 1.8), (0, 0, 1.2), 35)}
