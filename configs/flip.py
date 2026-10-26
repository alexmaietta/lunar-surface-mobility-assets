import math

import rover_kit as K

ASSET_ID = "flip"
ASSET_PATH = "astrolab/flip/rover"
FAMILY = "rover"
TITLE = "Astrolab FLIP"
DOC = ("Astrolab FLIP (FLEX Lunar Innovation Platform), flying on Astrobotic Griffin-1: a 480 kg uncrewed rover "
       "(about 2.35 x 1.9 x 2.3 m, wheelbase 1.4 m, track 1.58 m) with a low silver 1.6 x 0.7 x 0.4 m chassis, a "
       "vertical wedge tower over the front axle carrying solar cells and an antenna spike, a rear payload plate, "
       "and four 0.93 m Venturi hyper-deformable cable-spoke wheels on active corner swing arms with all-wheel "
       "steering. Geometry is measured from renders (no official dimensions).")

TEXTURE_SETS, MATERIALS = K.materials()

R_W, W_W, WB, TRACK = 0.465, 0.32, 1.40, 1.58
CL, CW, BELLY, CTOP = 1.60, 0.70, 0.28, 0.68
TOWER = [(0.30, CTOP), (0.80, CTOP), (0.78, 1.90), (0.50, 1.90)]
TY = 0.17
PIVOT_X, PIVOT_Z, KY = 0.25, 0.565, TRACK / 2 - 0.30


def _chassis():
    out = [{"kind": "cbox", "name": "chassis_body", "c": (0, 0, (BELLY + CTOP) / 2), "size": (CL, CW, CTOP - BELLY), "r": 0.06,
            "mat": "brushed_panel"},
           {"kind": "box", "name": "top_deck", "c": (-0.25, 0, CTOP + 0.005), "size": (1.00, CW - 0.06, 0.01), "mat": "mli_silver"},
           {"kind": "box", "name": "nose_band", "c": (CL / 2 + 0.005, 0, 0.42), "size": (0.01, CW - 0.08, 0.06), "mat": "anodised_dark"},
           {"kind": "box", "name": "tail_band", "c": (-CL / 2 - 0.005, 0, 0.42), "size": (0.01, CW - 0.08, 0.06), "mat": "anodised_dark"}]
    for s in (-1, 1):
        out.append({"kind": "box", "name": f"side_stripe_{s + 1}", "c": (0, s * (CW / 2 + 0.003), 0.50), "size": (1.40, 0.01, 0.08),
                    "mat": "anodised_grey"})
        out.append({"kind": "box", "name": f"side_light_bar_{s + 1}", "c": (CL / 2 - 0.12, s * (CW / 2 + 0.006), 0.40),
                    "size": (0.12, 0.01, 0.025), "mat": "lamp"})
        for e in (-1, 1):
            out.append({"kind": "beam", "name": f"arm_bracket_{s + 1}_{e + 1}", "p0": (e * PIVOT_X, s * (CW / 2 - 0.02), PIVOT_Z),
                        "p1": (e * PIVOT_X, s * (KY - 0.10), PIVOT_Z), "w": 0.10, "h": 0.12, "mat": "anodised_grey"})
    return out


def _tower():
    xm = sum(x for x, _ in TOWER) / 4
    return [
        {"kind": "extrude", "name": "tower", "profile": TOWER, "y": (-TY, TY), "mat": "mli_silver"},
        {"kind": "panel", "name": "tower_cells_l", "c": (0.62, TY + 0.004, 1.22), "u": (1, 0, 0), "v": (0, 0, 1), "w": 0.26, "h": 1.00, "t": 0.006,
         "normal": (0, 1, 0), "mat": "solar_cells", "back": "brushed_panel"},
        {"kind": "panel", "name": "tower_cells_r", "c": (0.62, -TY - 0.004, 1.22), "u": (1, 0, 0), "v": (0, 0, 1), "w": 0.26, "h": 1.00, "t": 0.006,
         "normal": (0, -1, 0), "mat": "solar_cells", "back": "brushed_panel"},
        {"kind": "panel", "name": "tower_radiator", "c": (0.795, 0, 1.25), "u": (0, 1, 0), "v": (0, 0, 1), "w": 2 * TY - 0.04, "h": 1.00, "t": 0.006,
         "normal": (1, 0, 0), "mat": "radiator", "back": "brushed_panel"},
        {"kind": "box", "name": "tower_cap", "c": (0.64, 0, 1.92), "size": (0.30, 2 * TY + 0.02, 0.04), "mat": "anodised_grey"},
        {"kind": "box", "name": "tower_collar", "c": (xm, 0, CTOP + 0.04), "size": (0.56, 2 * TY + 0.04, 0.08), "mat": "anodised_grey"},
        {"kind": "tube", "name": "tower_spike_base", "p0": (0.64, 0, 1.94), "p1": (0.64, 0, 2.02), "r": 0.05, "mat": "anodised_dark"},
        {"kind": "tube", "name": "tower_spike", "p0": (0.64, 0, 2.02), "p1": (0.64, 0, 2.30), "r": 0.03, "r1": 0.004, "mat": "aluminium"},
    ]


def _wheel_faces():
    out = []
    for n, side in (("fl", 1), ("fr", -1), ("rl", 1), ("rr", -1)):
        x = WB / 2 if n[0] == "f" else -WB / 2
        y = side * (TRACK / 2 + W_W / 2 + 0.004)
        out.append({"kind": "lathe", "name": f"{n}_side_ring", "link": f"{n}_wheel", "c": (x, y, R_W), "n": (0, side, 0),
                    "profile": [(0.33, 0.0), (0.42, 0.0)], "sides": 48, "mat": "aluminium"})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "mesh", "grousers": 48, "chevron": False, "grouser_h": 0.012, "spokes": 12, "spoke_r": 0.016,
              "spoke_curve": 0.0, "hub_frac": 0.26, "rim_frac": 0.70, "mass": 20.0, "grouser_mat": "titanium", "spoke_mat": "aluminium",
              "rim_mat": "aluminium", "hub_mat": "aluminium"},
    "wheels": K.four_wheels(WB, TRACK, (math.radians(-60), math.radians(60))),
    "suspension": {"type": "trailing_arm", "active": True, "arm_dx": WB / 2 - PIVOT_X, "pivot_dz": PIVOT_Z - R_W, "kingpin_off": TRACK / 2 - KY,
                   "upper_dz": 0.20, "travel": (0.20, 0.25), "static_rad": 0.05, "beam": 0.07, "arm_mat": "brushed_panel",
                   "knuckle_mat": "brushed_panel"},
    "parts": [
        *_chassis(),
        *_tower(),
        *_wheel_faces(),
        {"kind": "box", "name": "payload_plate", "c": (-0.35, 0, CTOP + 0.025), "size": (0.60, 0.56, 0.03), "mat": "grey_panel"},
        {"kind": "box", "name": "lidar", "c": (0.81, 0, 1.70), "size": (0.06, 0.14, 0.10), "mat": "anodised_dark"},
    ],
    "masts": [{"name": "nav_mast", "base": (0.70, 0.26, CTOP), "h": 0.14, "r": 0.022, "head": (0.08, 0.20, 0.07), "cams": (-0.06, 0.06),
               "head_mat": "aluminium"},
              {"name": "rear_cam", "base": (-0.72, 0, CTOP), "h": 0.08, "r": 0.02, "head": (0.07, 0.18, 0.06), "cams": (-0.06, 0.06),
               "head_mat": "aluminium", "forward": (-1, 0, 0)}],
    "lights": [((CL / 2 + 0.01, 0.24, 0.52), (1, 0, -0.1), 0.045, "head_lamp_l"), ((CL / 2 + 0.01, -0.24, 0.52), (1, 0, -0.1), 0.045, "head_lamp_r"),
               ((-CL / 2 - 0.01, 0.24, 0.52), (-1, 0, -0.1), 0.035, "rear_lamp_l"), ((-CL / 2 - 0.01, -0.24, 0.52), (-1, 0, -0.1), 0.035, "rear_lamp_r")],
    "sites": [("payload_plate", "chassis", (-0.35, 0, CTOP + 0.04), (0, 0, 1), "payload_interface", "Payload plate (30 kg)"),
              ("lift_point", "chassis", (0.64, 0, 1.94), (0, 0, 1), "handling", "Tower lift point"),
              ("lidar", "chassis", (0.84, 0, 1.70), (1, 0, 0), "sensor", "Lidar 3D mapper (estimated position)")],
    "imu": (0, 0, 0.5),
}

MASS = {"flight": {"mass": 480.0, "com_z": 0.62, "com_x": 0.12, "source": "press (Oct 2026): 480 kg"}}
DEFAULT_MASS_STATE = "flight"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (1.6, 0.7, 0.9)

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("brushed_panel", "mli_silver"))
SIMPLE_TRIS = 16000
RENDER_VIEWS = {**K.views(2.4, 2.0, 2.3, centre_z=0.9), "front": ((6.5, 0.0, 1.2), (0, 0, 0.9), 35)}
