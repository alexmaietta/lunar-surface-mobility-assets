import math

import rover_kit as K

ASSET_ID = "promise"
ASSET_PATH = "nasa_jpl/promise/rover"
FAMILY = "rover"
TITLE = "NASA / JPL PROMISE"
DOC = ("NASA / JPL PROMISE (Polar Rover for Observation, Mapping, and In-Situ Exploration), November 2026 announcement: "
       "the Curiosity vehicle-system test bed reflown to the lunar south pole on Blue Moon MK1, about 1,000 kg. A white "
       "warm-electronics box on Curiosity's six-wheel rocker-bogie with a deck differential bar, four steering corner "
       "wheels and 50 cm aluminium chevron-grouser wheels with curved titanium spokes. No arm: the VIPER-heritage TRIDENT "
       "1 m drill rides a tower on the front-left corner. A flight-spare MMRTG sits at the rear between two heat "
       "exchangers with gold tubing, the remote-sensing mast carries the Lunar Dashcam stereo pairs, and blue LED panels "
       "light the body. Suspension pivots follow the JPL Mars 2020 kinematic layout (the shared Curiosity mobility "
       "design); deck equipment, comms and instrument placement are estimated from NASA's render.")

TEXTURE_SETS, MATERIALS = K.materials(
    textures={
        "promise_white": ("panel", dict(colour=(0.84, 0.84, 0.82), tile_m=0.7, rough0=0.45, fastener_pitch=0.07)),
        "wheel_alu": ("sheet_metal", dict(colour=(0.66, 0.66, 0.65), tile_m=0.5, rivet_pitch=0.03, seed=5101)),
        "rocker_black": ("anodised", dict(colour=(0.04, 0.04, 0.045), tile_m=0.3, rough0=0.45)),
        "rtg_fin": ("worn_coating", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, metallic=0.6, rough0=0.5, seed=5102)),
        "hrs_white": ("worn_coating", dict(colour=(0.82, 0.82, 0.80), tile_m=0.4, metallic=0.0, rough0=0.5, seed=5103)),
    },
    overrides={
        "promise_white": {"set": "promise_white", "normal": 0.8},
        "wheel_alu": {"set": "wheel_alu", "normal": 0.7},
        "rocker_black": {"set": "rocker_black", "normal": 0.5},
        "rtg_fin": {"set": "rtg_fin", "normal": 0.6},
        "hrs_white": {"set": "hrs_white", "normal": 0.6},
        "copper": {"color": (0.78, 0.45, 0.22), "roughness": 0.3, "metallic": 0.9},
        "gold_foil": {"color": (0.85, 0.62, 0.18), "roughness": 0.25, "metallic": 0.9},
        "lamp_window": {"color": (0.55, 0.56, 0.58), "roughness": 0.06, "metallic": 0.9},
        "kapton": {"color": (0.72, 0.42, 0.10), "roughness": 0.25, "metallic": 0.5},
    })

R_W, W_W = 0.25, 0.40
ROCKER = (0.304, 0.800, 0.893)
BOGIE = (-0.450, 0.920, 0.663)
DIFF = (-0.052, 1.170)
DIFF_Y = 0.70
LEVER_Z = 1.170
X_F, X_M, X_R = 1.185, 0.0, -1.075
Y_C, Y_M = 1.0625, 1.1845
KO = 0.24
UP_DZ = 0.34
STEER = (math.radians(-90), math.radians(90))
BODY_X, BODY_Y, BODY_Z = (-0.80, 0.90), 0.68, (0.62, 1.10)
DECK = BODY_Z[1]
MAST = (0.70, -0.50)
MAST_TOP = 1.95
DRILL = (1.00, 0.60)
TOWER_Z = (0.36, 1.98)
BIT_Z = 0.32
RTG_C = (-1.12, 0.0, 1.00)
RTG_AXIS = (-0.64, 0.0, 0.77)
LED_NM, LED_FWHM = 457.0, 22.0


def _leg_top(x, y, steer):
    return (x, y, R_W + UP_DZ + (0.11 if steer else 0.04))


def _carriers():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        rp = (ROCKER[0], s * ROCKER[1], ROCKER[2])
        bp = (BOGIE[0], s * BOGIE[1], BOGIE[2])
        out.append({"name": f"rocker_{sd}", "pos": rp, "axis": (0, 1, 0), "limit": (-0.45, 0.45), "role": "linkage", "drive": "none",
                    "damping": 0.0, "mass": 25.0, "beam": 0.07, "mat": "rocker_black",
                    "beams_to": [_leg_top(X_F, s * Y_C, True), bp, (rp[0], rp[1], LEVER_Z)]})
        out.append({"name": f"bogie_{sd}", "parent": f"rocker_{sd}", "pos": bp, "axis": (0, 1, 0), "limit": (-0.60, 0.60), "role": "suspension",
                    "drive": "spring", "stiffness": 0.0, "damping": 60.0, "mass": 15.0, "beam": 0.06, "mat": "rocker_black",
                    "beams_to": [_leg_top(X_M, s * (Y_M - KO), False), _leg_top(X_R, s * Y_C, True)]})
    return out


def _wheels():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        out += [{"name": f"f{sd}", "x": X_F, "y": s * Y_C, "carrier": f"rocker_{sd}", "steer": STEER},
                {"name": f"m{sd}", "x": X_M, "y": s * Y_M, "carrier": f"bogie_{sd}", "steer": None},
                {"name": f"r{sd}", "x": X_R, "y": s * Y_C, "carrier": f"bogie_{sd}", "steer": STEER}]
    return out


def _differential():
    links = [{"name": "diff_bar", "pos": (DIFF[0], 0, DIFF[1]), "axis": (0, 0, 1), "limit": (-0.20, 0.20), "role": "suspension", "mass": 6.0,
              "drive": {"kind": "spring", "stiffness": 0.0, "damping": 400.0, "max_force": 1.0e6, "target": 0.0}}]
    parts = [{"kind": "tube", "name": "diff_pivot_post", "p0": (DIFF[0], 0, DECK), "p1": (DIFF[0], 0, DIFF[1]), "r": 0.045, "mat": "titanium"},
             {"kind": "beam", "name": "diff_bar_beam", "link": "diff_bar", "p0": (DIFF[0], -DIFF_Y, DIFF[1]), "p1": (DIFF[0], DIFF_Y, DIFF[1]),
              "w": 0.06, "h": 0.05, "mat": "rocker_black"}]
    loops = []
    for sd, s in (("l", 1), ("r", -1)):
        lever = (ROCKER[0], s * ROCKER[1], LEVER_Z)
        end = (DIFF[0], s * DIFF_Y, DIFF[1])
        links += [{"name": f"diff_rod_{sd}_yaw", "parent": f"rocker_{sd}", "pos": lever, "axis": (0, 0, 1), "limit": (-0.6, 0.6), "role": "linkage",
                   "mass": 0.3, "drive": {"kind": "none", "stiffness": 0.0, "damping": 0.0}},
                  {"name": f"diff_rod_{sd}", "parent": f"diff_rod_{sd}_yaw", "pos": lever, "axis": (0, 1, 0), "limit": (-0.8, 0.8), "role": "linkage",
                   "mass": 0.7, "drive": {"kind": "none", "stiffness": 0.0, "damping": 0.0}}]
        parts += [{"kind": "tube", "name": f"diff_rod_{sd}_tube", "link": f"diff_rod_{sd}", "p0": lever, "p1": end, "r": 0.018, "mat": "titanium"},
                  {"kind": "sphere", "name": f"diff_rod_{sd}_eye_rocker", "link": f"diff_rod_{sd}", "c": lever, "r": 0.03, "mat": "titanium"},
                  {"kind": "sphere", "name": f"diff_rod_{sd}_eye_bar", "link": "diff_bar", "c": end, "r": 0.03, "mat": "titanium"}]
        loops.append({"name": f"diff_end_{sd}", "parent": "diff_bar", "child": f"diff_rod_{sd}", "anchor": end, "axis": (0, 0, 1), "type": "spherical"})
    return links, parts, loops


def _body():
    (x0, x1), (z0, z1) = BODY_X, BODY_Z
    out = [
        {"kind": "box", "name": "web_body", "c": ((x0 + x1) / 2, 0, (z0 + z1) / 2), "size": (x1 - x0, 2 * BODY_Y, z1 - z0), "mat": "promise_white"},
        {"kind": "box", "name": "deck_plate", "c": ((x0 + x1) / 2, 0, z1 + 0.01), "size": (x1 - x0 + 0.04, 2 * BODY_Y + 0.04, 0.02),
         "mat": "promise_white"},
        {"kind": "box", "name": "belly_plate", "c": ((x0 + x1) / 2, 0, z0 - 0.01), "size": (x1 - x0 - 0.10, 2 * BODY_Y - 0.10, 0.02),
         "mat": "anodised_grey"},
    ]
    for s in (-1, 1):
        out += [
            {"kind": "obox", "name": f"front_chevron_{'rl'[s > 0]}", "c": (x1 + 0.006, s * 0.30, z1 - 0.12), "ax": (0, s * 0.85, -0.53), "ay": (0, 0.53 * s, 0.85),
             "size": (0.62, 0.16, 0.012), "mat": "rocker_black"},
            {"kind": "box", "name": f"rocker_bearing_{'rl'[s > 0]}", "c": (ROCKER[0], s * (BODY_Y + 0.04), ROCKER[2]), "size": (0.18, 0.08, 0.18),
             "mat": "anodised_grey"},
            {"kind": "box", "name": f"side_panel_{'rl'[s > 0]}", "c": (0.05, s * (BODY_Y + 0.004), (z0 + z1) / 2), "size": (1.10, 0.008, 0.30),
             "mat": "hrs_white"},
        ]
    return out


def _deck():
    out = [
        {"kind": "box", "name": "comms_box", "c": (-0.52, -0.25, DECK + 0.13), "size": (0.40, 0.32, 0.24), "mat": "anodised_grey"},
        {"kind": "box", "name": "avionics_cover", "c": (0.30, 0.22, DECK + 0.06), "size": (0.50, 0.40, 0.10), "mat": "promise_white"},
        {"kind": "box", "name": "rad_detector", "c": (0.05, -0.30, DECK + 0.06), "size": (0.20, 0.16, 0.10), "mat": "gold_foil"},
        {"kind": "disc", "name": "lra_base", "c": (-0.20, 0.50, DECK + 0.02), "n": (0, 0, 1), "r": 0.03, "t": 0.015, "mat": "aluminium"},
        {"kind": "lathe", "name": "uhf_helix", "c": (-0.68, 0.45, DECK + 0.02), "n": (0, 0, 1), "mat": "promise_white", "sides": 24,
         "profile": [(1e-3, 0.0), (0.045, 0.0), (0.045, 0.16), (0.03, 0.19), (1e-3, 0.19)]},
        {"kind": "box", "name": "laforge_head", "c": (0.84, 0.10, DECK + 0.08), "size": (0.12, 0.14, 0.12), "mat": "kapton"},
        {"kind": "box", "name": "nss_head", "c": (0.70, -(BODY_Y + 0.04), BODY_Z[0] + 0.12), "size": (0.06, 0.22, 0.15), "mat": "kapton"},
        {"kind": "box", "name": "msolo_inlet", "c": (BODY_X[1] + 0.02, 0.42, BODY_Z[0] + 0.10), "size": (0.04, 0.10, 0.07), "mat": "rocker_black"},
        {"kind": "box", "name": "nirvss_head", "c": (0.55, 0.30, BODY_Z[0] - 0.05), "size": (0.12, 0.12, 0.06), "mat": "rocker_black"},
        {"kind": "box", "name": "scan3d_lidar", "c": (0.78, -0.12, DECK + 0.07), "size": (0.10, 0.12, 0.10), "mat": "anodised_dark"},
    ]
    return out


def _rtg():
    ax = RTG_AXIS
    n = math.sqrt(sum(a * a for a in ax))
    ax = tuple(a / n for a in ax)
    c = RTG_C
    p0 = tuple(c[i] - ax[i] * 0.33 for i in range(3))
    p1 = tuple(c[i] + ax[i] * 0.33 for i in range(3))
    perp = (ax[2], 0.0, -ax[0])
    out = [{"kind": "tube", "name": "mmrtg_core", "p0": p0, "p1": p1, "r": 0.17, "sides": 32, "mat": "rtg_fin"},
           {"kind": "disc", "name": "mmrtg_cap_low", "c": p0, "n": tuple(-a for a in ax), "r": 0.19, "t": 0.03, "mat": "anodised_grey"},
           {"kind": "disc", "name": "mmrtg_cap_high", "c": p1, "n": ax, "r": 0.19, "t": 0.03, "mat": "anodised_grey"}]
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        rd = tuple(perp[i] * math.cos(a) + (0, 1, 0)[i] * math.sin(a) for i in range(3))
        out.append({"kind": "obox", "name": f"mmrtg_fin_{k}", "c": tuple(c[i] + rd[i] * 0.245 for i in range(3)), "ax": ax, "ay": rd,
                    "size": (0.60, 0.15, 0.012), "mat": "rtg_fin"})
    for s in (-1, 1):
        out.append({"kind": "beam", "name": f"mmrtg_strut_{'rl'[s > 0]}", "p0": (BODY_X[0], s * 0.30, 0.80), "p1": (p0[0], s * 0.12, p0[2] + 0.04),
                    "w": 0.04, "h": 0.04, "mat": "anodised_grey"})
        out.append({"kind": "beam", "name": f"mmrtg_upper_strut_{'rl'[s > 0]}", "p0": (BODY_X[0], s * 0.30, DECK - 0.05), "p1": (c[0], s * 0.14, c[2] + 0.05),
                    "w": 0.04, "h": 0.04, "mat": "anodised_grey"})
        y = s * 0.50
        out.append({"kind": "panel", "name": f"heat_exchanger_{'rl'[s > 0]}", "c": (-1.10, y, 1.02), "u": (1, 0, 0), "v": (0, 0, 1), "w": 0.56, "h": 0.52,
                    "t": 0.025, "normal": (0, s, 0), "mat": "hrs_white", "back": "hrs_white"})
        pts = []
        for j in range(6):
            z = 0.80 + j * 0.088
            xs = (-1.34, -0.86) if j % 2 == 0 else (-0.86, -1.34)
            pts += [(xs[0], y + s * 0.02, z), (xs[1], y + s * 0.02, z)]
        out.append({"kind": "rail", "name": f"heat_exchanger_tube_{'rl'[s > 0]}", "points": pts, "r": 0.008, "mat": "copper"})
        out.append({"kind": "beam", "name": f"heat_exchanger_mount_{'rl'[s > 0]}", "p0": (BODY_X[0], s * 0.45, 1.02), "p1": (-0.84, y, 1.02),
                    "w": 0.04, "h": 0.04, "mat": "anodised_grey"})
    return out


def _drill():
    x, y = DRILL
    out = [
        {"kind": "beam", "name": "trident_tower", "p0": (x, y + 0.07, TOWER_Z[0]), "p1": (x, y + 0.07, TOWER_Z[1]), "w": 0.06, "h": 0.08, "mat": "rocker_black"},
        {"kind": "beam", "name": "trident_rail", "p0": (x, y - 0.07, TOWER_Z[0] + 0.1), "p1": (x, y - 0.07, TOWER_Z[1]), "w": 0.03, "h": 0.03, "mat": "rocker_black"},
        {"kind": "box", "name": "trident_head_block", "c": (x, y, TOWER_Z[1] + 0.03), "size": (0.14, 0.22, 0.06), "mat": "rocker_black"},
        {"kind": "beam", "name": "trident_mount_upper", "p0": (BODY_X[1], y, DECK - 0.04), "p1": (x, y + 0.07, DECK - 0.04), "w": 0.05, "h": 0.05,
         "mat": "anodised_grey"},
        {"kind": "beam", "name": "trident_mount_lower", "p0": (BODY_X[1], y, BODY_Z[0] + 0.04), "p1": (x, y + 0.07, BODY_Z[0] + 0.04), "w": 0.05, "h": 0.05,
         "mat": "anodised_grey"},
        {"kind": "box", "name": "trident_carriage", "link": "trident_deploy", "c": (x, y, 1.70), "size": (0.10, 0.12, 0.14), "mat": "anodised_grey"},
        {"kind": "box", "name": "trident_motor", "link": "trident_deploy", "c": (x, y, 1.80), "size": (0.12, 0.12, 0.08), "mat": "rocker_black"},
        {"kind": "tube", "name": "trident_auger_rod", "link": "trident_auger", "p0": (x, y, BIT_Z + 0.05), "p1": (x, y, 1.64), "r": 0.0127, "mat": "titanium"},
        {"kind": "tube", "name": "trident_bit", "link": "trident_auger", "p0": (x, y, BIT_Z), "p1": (x, y, BIT_Z + 0.05), "r": 0.0127, "r1": 0.008,
         "mat": "rocker_black"},
    ]
    turns, z0, z1 = 26, BIT_Z + 0.05, BIT_Z + 1.08
    pts = []
    for i in range(turns * 16 + 1):
        t = i / (turns * 16)
        a = 2 * math.pi * turns * t
        pts.append((x + 0.019 * math.cos(a), y + 0.019 * math.sin(a), z0 + (z1 - z0) * t))
    out.append({"kind": "rail", "name": "trident_auger_flight", "link": "trident_auger", "points": pts, "r": 0.0045, "mat": "titanium"})
    return out


def _light(name, pos, d, w, h, desc, group):
    return {"name": name, "pos": pos, "dir": d, "shape": "rect", "width_m": w, "height_m": h, "housing": (w + 0.03, h + 0.03, 0.045),
            "housing_mat": "anodised_dark", "lens_mat": "lamp_window", "group": group, "peak_nm": LED_NM, "fwhm_nm": LED_FWHM,
            "radiant_w": 32.0, "fwhm_h_deg": 110.0, "fwhm_v_deg": 90.0, "beam_shape": 4.0, "cone_deg": 80.0, "cone_softness": 0.3,
            "ies_name": "hazlight", "max_on_s": 10.0, "max_duty": 0.5, "description": desc,
            "source": "VIPER HazLight heritage assumed (LPSC 2022 #2466); positions read from NASA's PROMISE render"}


def _lights():
    (x0, x1), zl = BODY_X, 0.86
    out = []
    for s, sd in ((1, "l"), (-1, "r")):
        out += [_light(f"haz_light_front_{sd}", (x1 + 0.005, s * 0.52, zl), (1, s * 0.3, -0.45), 0.08, 0.08, "Front-corner LED HazLight", "haz"),
                _light(f"haz_light_side_{sd}", (0.45, s * (BODY_Y + 0.01), 0.80), (0.3, s, -0.5), 0.08, 0.08, "Side LED HazLight", "haz"),
                _light(f"haz_light_rear_{sd}", (-0.55, s * (BODY_Y + 0.01), 0.80), (-0.3, s, -0.5), 0.08, 0.08, "Rear-side LED HazLight", "haz")]
    return out


def _cam(focal_mm, desc, focus_m):
    return {"focal_mm": focal_mm, "aperture_mm": (11.264, 11.264), "fstop": 0.0, "f_number": 6.7, "focus_m": focus_m, "clip_m": (0.05, 500.0),
            "resolution": (2048, 2048), "source": f"{desc}; optics estimated from VIPER VIS heritage"}


def _cameras():
    out = []
    for s, nm in ((1, "left"), (-1, "right")):
        out.append({"name": f"front_haz_cam_{nm}", "pos": (BODY_X[1] + 0.01, s * 0.16, 0.70), "forward": (1, 0, -0.6),
                    "housing": {"r": 0.03, "len": 0.08, "mat": "rocker_black"},
                    "spec": _cam(3.94, "Front HazCam stereo pair, 32 cm baseline (estimated)", 1.5)})
        out.append({"name": f"rear_haz_cam_{nm}", "pos": (BODY_X[0] - 0.01, s * 0.16, 0.70), "forward": (-1, 0, -0.6),
                    "housing": {"r": 0.03, "len": 0.08, "mat": "rocker_black"},
                    "spec": _cam(3.94, "Rear HazCam stereo pair, 32 cm baseline (estimated)", 1.5)})
    return out


DIFF_LINKS, DIFF_PARTS, DIFF_LOOPS = _differential()

ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "grouser", "grousers": 24, "grouser_h": 0.0075, "chevron": True, "chevron_deg": 22,
              "hub_frac": 0.24, "rim_frac": 0.84, "mass": 7.0, "drum_mat": "wheel_alu", "grouser_mat": "wheel_alu", "spokes": 6,
              "spoke_curve": 0.9, "spoke_r": 0.012, "spoke_mat": "titanium", "rim_mat": "wheel_alu", "hub_mat": "rocker_black",
              "hub_cap_mat": "aluminium", "segments": 64},
    "carriers": _carriers(),
    "wheels": _wheels(),
    "suspension": {"type": "carrier", "kingpin_off": KO, "steer_off": 0.0, "upper_dz": UP_DZ, "knuckle_t": 0.05, "knuckle_mat": "rocker_black"},
    "links": [
        *DIFF_LINKS,
        {"name": "trident_deploy", "type": "prismatic", "pos": (DRILL[0], DRILL[1], 1.70), "axis": (0, 0, -1), "limit": (0.0, BIT_Z), "role": "arm",
         "mass": 6.0, "drive": {"kind": "position", "stiffness": 4000.0, "damping": 400.0, "max_force": 800.0}},
        {"name": "trident_feed", "parent": "trident_deploy", "type": "prismatic", "pos": (DRILL[0], DRILL[1], 1.66), "axis": (0, 0, -1),
         "limit": (0.0, 1.0), "role": "arm", "mass": 3.0, "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 500.0}},
        {"name": "trident_auger", "parent": "trident_feed", "type": "revolute", "pos": (DRILL[0], DRILL[1], 1.0), "axis": (0, 0, -1),
         "role": "drill", "mass": 1.5, "drive": {"kind": "velocity", "stiffness": 0.0, "damping": 20.0, "max_force": 60.0}},
    ],
    "loops": DIFF_LOOPS,
    "parts": [*_body(), *_deck(), *DIFF_PARTS, *_rtg(), *_drill()],
    "masts": [{"name": "rsm", "base": (MAST[0], MAST[1], DECK), "h": MAST_TOP - DECK, "r": 0.055, "mat": "rocker_black", "foot": (0.18, 0.18, 0.06),
               "head": (0.16, 0.50, 0.14), "head_mat": "promise_white", "cams": (-0.20, -0.12, 0.12, 0.20), "focal_mm": 12.0,
               "source": "Lunar Dashcam stereo suite on the remote-sensing mast (optics estimated)"}],
    "hga": {"base": (-0.30, 0.42, DECK + 0.02), "h": 0.22, "r": 0.15, "mast_r": 0.025, "boresight": (-0.3, 0, 1), "band": "X", "flat": (0.30, 0.30, 0.03),
            "front": "promise_white", "back": "mli_silver", "frame_mat": "aluminium"},
    "lights": _lights(),
    "cameras": _cameras(),
    "sites": [
        ("trident_bit", "trident_feed", (DRILL[0], DRILL[1], BIT_Z), (0, 0, -1), "tool", "TRIDENT 25.4 mm bit (1 m max depth)"),
        ("mmrtg", "chassis", RTG_C, RTG_AXIS, "power", "Flight-spare MMRTG, about 110 W(e) at fuelling; +Z = cylinder axis", {"power_w": 110.0}),
        ("lra", "chassis", (-0.20, 0.50, DECK + 0.035), (0, 0, 1), "reference", "Laser retroreflector array"),
        ("scan3d_lidar", "chassis", (0.83, -0.12, DECK + 0.07), (1, 0, -0.2), "sensor", "SCAN-3D lidar technology demo (placement estimated)"),
        ("laforge", "chassis", (0.90, 0.10, DECK + 0.08), (1, 0, -0.6), "sensor", "LAFORGE infrared radiometer (placement estimated)"),
        ("nss", "chassis", (0.70, -BODY_Y - 0.07, BODY_Z[0] + 0.12), (0, -1, 0), "sensor", "Neutron spectrometer (placement estimated)"),
        ("nirvss", "chassis", (0.55, 0.30, BODY_Z[0] - 0.08), (0, 0, -1), "sensor", "NIRVSS near-infrared spectrometer (placement estimated)"),
        ("lift_point", "chassis", (0, 0, DECK + 0.02), (0, 0, 1), "handling", "Deck lift point (estimated)"),
    ],
    "imu": (0, 0, 0.85),
}

MASS = {"roving": {"mass": 1000.0, "com_z": 0.85, "source": "Planetary Society estimate, about 1,000 kg (NASA has not published a mass)"}}
DEFAULT_MASS_STATE = "roving"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (1.7, 1.4, 0.5)

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("promise_white",))
SIMPLE_TRIS = 20000
RENDER_VIEWS = {**K.views(3.0, 2.7, 2.2, centre_z=1.0), "front": ((6.5, 0.0, 1.4), (0, 0, 1.0), 35),
                "drill": ((3.0, 2.6, 1.6), (DRILL[0], DRILL[1], 1.1), 35), "rtg": ((-3.4, -1.8, 2.0), (-1.1, 0, 1.0), 35)}
