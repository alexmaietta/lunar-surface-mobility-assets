import math

import rover_kit as K

ASSET_ID = "viper"
ASSET_PATH = "nasa/viper/rover"
FAMILY = "rover"
TITLE = "NASA VIPER"
DOC = ("NASA VIPER (Volatiles Investigating Polar Exploration Rover), flight design for Blue Moon MK1 delivery: 1.7 x 1.7 "
       "x 2.5 m and 447 kg roving. Silver-MLI body over a narrower lower warm box, solar arrays hanging from the port, "
       "starboard and aft deck edges, four OSR radiators on a peaked deck, a front-port mast with the NavCam stereo pair "
       "(40 cm baseline) and two 457 nm NavLight LED panels on a pan-tilt gimbal at 2.0 m and a flat high-gain antenna on "
       "its own gimbal at 2.3 m, the TRIDENT drill chimney with calibration targets, aft stereo cameras, four wheel-well "
       "HazCams and six HazLights. Four 0.5 m wire-spoked grousered drum wheels, each on an active four-bar suspension "
       "(360 mm stroke, 7-43 cm clearance) with +/-50 deg offset-kingpin steering and hub drive. Lights carry measured "
       "spectra and lumens (UsdLux plus Omniverse RTX photometric schemas); cameras carry the VIS monochrome responsivity.")

TEXTURE_SETS, MATERIALS = K.materials(
    textures={
        "mli_viper": ("mli_flight", dict(colour=(0.80, 0.80, 0.78), tile_m=1.2, quilt=0.15, tape=(0.86, 0.84, 0.78), seed=4101, gloss=0.45,
                                         metal=0.35)),
        "mli_viper_aft": ("mli_flight", dict(colour=(0.78, 0.78, 0.76), tile_m=1.2, quilt=0.15, tape=(0.86, 0.84, 0.78), seed=4102,
                                             grime=1.6, gloss=0.45, metal=0.35)),
        "solar_viper": ("solar_array_flight", dict(tile_m=0.40, cell=(0.08, 0.04), seed=4103)),
        "osr_viper": ("osr_flight", dict(tile_m=0.40, tile=0.05, seed=4104)),
        "wheel_alu": ("sheet_metal", dict(colour=(0.62, 0.62, 0.61), tile_m=0.5, rivet_pitch=0.025, seed=4105)),
        "frame_alu": ("sheet_metal", dict(colour=(0.47, 0.30, 0.13), tile_m=0.6, rivet_pitch=0.04, seed=4106, iridite=0.35, rough0=0.35)),
        "housing_alu": ("sheet_metal", dict(colour=(0.78, 0.78, 0.77), tile_m=0.3, rivet_pitch=0.0, seed=4111, rough0=0.38)),
        "sock": ("fabric_boot", dict(colour=(0.24, 0.23, 0.215), tile_m=0.30, seed=4107)),
        "black_anodise": ("worn_coating", dict(colour=(0.035, 0.035, 0.038), tile_m=0.25, metallic=0.85, rough0=0.42, seed=4108)),
        "white_paint": ("worn_coating", dict(colour=(0.84, 0.84, 0.82), tile_m=0.3, metallic=0.0, rough0=0.55, seed=4109)),
        "checker": ("checkerboard", dict(tile_m=0.16, squares=12, seed=4110)),
    },
    overrides={
        "mli_viper": {"set": "mli_viper", "normal": 1.0},
        "mli_viper_aft": {"set": "mli_viper_aft", "normal": 1.0},
        "solar_viper": {"set": "solar_viper", "normal": 0.4},
        "osr_viper": {"set": "osr_viper", "normal": 0.5},
        "wheel_alu": {"set": "wheel_alu", "normal": 0.7},
        "wheel_flange": {"set": "black_anodise", "normal": 0.6},
        "frame_alu": {"set": "frame_alu", "normal": 0.6},
        "housing_alu": {"set": "housing_alu", "normal": 0.5},
        "hub_white": {"color": (0.42, 0.40, 0.39), "roughness": 0.5, "metallic": 0.6},
        "alodine": {"color": (0.47, 0.30, 0.13), "roughness": 0.35, "metallic": 0.85},
        "lamp_window": {"color": (0.55, 0.56, 0.58), "roughness": 0.06, "metallic": 0.9},
        "sock": {"set": "sock", "normal": 1.0},
        "black_anodise": {"set": "black_anodise", "normal": 0.6},
        "white_paint": {"set": "white_paint", "normal": 0.6},
        "checker": {"set": "checker", "normal": 0.2},
        "lamp_blue": {"color": (0.10, 0.12, 0.30), "roughness": 0.15, "emission": (0.03, 0.0, 1.0, 4.0)},
        "lamp_lens_off": {"color": (0.55, 0.57, 0.62), "roughness": 0.08, "metallic": 0.6},
        "kapton": {"color": (0.72, 0.42, 0.10), "roughness": 0.25, "metallic": 0.5},
        "grey_90": {"color": (0.90, 0.90, 0.90), "roughness": 0.9},
        "grey_60": {"color": (0.60, 0.60, 0.60), "roughness": 0.9},
        "grey_35": {"color": (0.35, 0.35, 0.35), "roughness": 0.9},
        "grey_18": {"color": (0.18, 0.18, 0.18), "roughness": 0.9},
        "grey_05": {"color": (0.05, 0.05, 0.05), "roughness": 0.9},
    })

R_W, WB, TRACK = 0.25, 1.00, 1.30
HALF = 0.80
HULL_Z = (0.72, 1.22)
DECK_PEAK = 1.27
LOWER = (0.52, 0.26, 0.25, 0.47)
ARR_BOT = 0.50
MAST = (0.60, 0.30)
MAST_TOP = 1.92
TILT_Z = 2.04
CHIMNEY = (0.12, -0.28)
DRILL = (0.12, -0.20)
LED_NM, LED_FWHM = 457.0, 22.0
VIS_SOURCE = "VIPER Visible Imaging System, Beyer et al. LPSC 2022 #2466"


def _vis_responsivity():
    qe = ((400, 0.30), (425, 0.40), (450, 0.48), (475, 0.53), (500, 0.56), (525, 0.58))
    out = []
    for nm in range(400, 522, 2):
        q = next(b + (nm - a) * (d - b) / (c - a) for (a, b), (c, d) in zip(qe, qe[1:]) if a <= nm <= c)
        filt = 0.92 / (1 + math.exp(-(nm - 425) / 2.5)) / (1 + math.exp((nm - 495) / 2.5))
        out.append((float(nm), round(q * filt, 5)))
    peak = max(v for _, v in out)
    return [(w, round(v / peak, 5)) for w, v in out]


def _vis(focal_mm, desc, focus_m):
    return {"focal_mm": focal_mm, "aperture_mm": (11.264, 11.264), "fstop": 0.0, "f_number": 6.7, "focus_m": focus_m, "clip_m": (0.05, 500.0), "resolution": (2048, 2048),
            "responsivity": _vis_responsivity(), "source": f"{desc}; CMV4000 2048x2048 5.5 um mono, 425-495 nm bandpass; {VIS_SOURCE}"}


def _hull():
    x0, y0, zb, zt = LOWER
    out = [
        {"kind": "box", "name": "hull", "c": (0, 0, sum(HULL_Z) / 2), "size": (2 * HALF - 0.04, 2 * HALF - 0.04, HULL_Z[1] - HULL_Z[0]),
         "mat": "mli_viper"},
        {"kind": "frustum", "name": "deck_roof", "c": (0, 0), "bottom": (HULL_Z[1], 2 * HALF - 0.04, 2 * HALF - 0.04),
         "top": (DECK_PEAK, 0.50, 0.50), "caps": (False, True), "mat": "mli_viper"},
        {"kind": "frustum", "name": "hopper", "c": (0, 0), "bottom": (zt, 2 * x0, 2 * y0), "top": (HULL_Z[0], 2 * HALF - 0.10, 2 * HALF - 0.10),
         "caps": (False, False), "mat": "mli_viper_aft"},
        {"kind": "box", "name": "warm_box_lower", "c": (0, 0, (zb + zt) / 2), "size": (2 * x0, 2 * y0, zt - zb), "mat": "mli_viper_aft"},
        {"kind": "box", "name": "belly_plate", "c": (0, 0, zb + 0.004), "size": (2 * x0 - 0.04, 2 * y0 - 0.04, 0.008), "mat": "frame_alu"},
        {"kind": "box", "name": "front_skirt", "c": (HALF - 0.03, 0, 0.62), "size": (0.02, 0.72, 0.20), "mat": "mli_viper"},
        {"kind": "box", "name": "msolo_inlet", "c": (x0 + 0.01, -0.12, 0.38), "size": (0.03, 0.10, 0.07), "mat": "black_anodise"},
        {"kind": "tube", "name": "msolo_port", "p0": (x0 + 0.025, -0.12, 0.38), "p1": (x0 + 0.035, -0.12, 0.38), "r": 0.018, "mat": "lens"},
        {"kind": "box", "name": "nss_head", "c": (HALF - 0.01, -0.42, 1.04), "size": (0.06, 0.22, 0.15), "mat": "kapton"},
        {"kind": "box", "name": "nss_electronics", "c": (HALF - 0.035, -0.42, 0.93), "size": (0.04, 0.16, 0.06), "mat": "black_anodise"},
        {"kind": "box", "name": "nirvss_bracket", "c": (0.30, -0.06, zb - 0.03), "size": (0.20, 0.16, 0.05), "mat": "frame_alu"},
        {"kind": "box", "name": "nirvss_head", "c": (0.30, -0.06, zb - 0.07), "size": (0.12, 0.12, 0.04), "mat": "black_anodise"},
        {"kind": "tube", "name": "nirvss_spot_lamp", "p0": (0.34, -0.10, zb - 0.09), "p1": (0.34, -0.10, zb - 0.10), "r": 0.012,
         "mat": "lamp_lens_off"},
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append({"kind": "beam", "name": f"warm_box_post_{'fa'[sx > 0]}{'rl'[sy > 0]}",
                        "p0": (sx * (x0 - 0.02), sy * (y0 - 0.02), zb), "p1": (sx * (HALF - 0.08), sy * (HALF - 0.08), HULL_Z[0]),
                        "w": 0.035, "h": 0.035, "mat": "frame_alu"})
    return out


def _flaps():
    out = []
    for i in range(6):
        out.append({"kind": "panel", "name": f"mli_flap_front_{i}", "c": (HALF - 0.012, -0.60 + i * 0.24, HULL_Z[0] + 0.03), "u": (0, 1, 0),
                    "v": (0, 0, 1), "w": 0.09, "h": 0.07, "t": 0.003, "normal": (1, 0, 0), "mat": "white_paint", "back": "mli_viper"})
    for i, y in enumerate((-0.16, 0.0, 0.16)):
        out.append({"kind": "panel", "name": f"mli_flap_lower_{i}", "c": (LOWER[0] + 0.006, y, LOWER[2] + 0.04), "u": (0, 1, 0),
                    "v": (0, 0, 1), "w": 0.08, "h": 0.06, "t": 0.003, "normal": (1, 0, 0), "mat": "white_paint", "back": "mli_viper"})
    return out


def _arrays():
    h = HULL_Z[1] - ARR_BOT
    zc = ARR_BOT + h / 2
    flare = math.radians(3.0)
    out = []
    for n, s in (("port", 1), ("starboard", -1)):
        out.append({"kind": "panel", "name": f"solar_{n}", "c": (0, s * (HALF + 0.015 + h / 2 * math.sin(flare)), zc), "u": (1, 0, 0),
                    "v": (0, -s * math.sin(flare), math.cos(flare)), "w": 1.66, "h": h, "t": 0.022, "normal": (0, s, math.sin(flare)),
                    "mat": "solar_viper", "back": "frame_alu"})
        for z, nm in ((ARR_BOT, "low"), (HULL_Z[1], "high")):
            off = (HULL_Z[1] - z) * math.sin(flare)
            out.append({"kind": "beam", "name": f"solar_{n}_frame_{nm}", "p0": (-0.83, s * (HALF + 0.03 + off), z),
                        "p1": (0.83, s * (HALF + 0.03 + off), z), "w": 0.025, "h": 0.025, "mat": "white_paint"})
    out.append({"kind": "panel", "name": "solar_aft", "c": (-(HALF + 0.015 + h / 2 * math.sin(flare)), 0, zc), "u": (0, 1, 0),
                "v": (math.sin(flare), 0, math.cos(flare)), "w": 1.66, "h": h, "t": 0.022, "normal": (-1, 0, math.sin(flare)),
                "mat": "solar_viper", "back": "frame_alu"})
    for z, nm in ((ARR_BOT, "low"), (HULL_Z[1], "high")):
        off = (HULL_Z[1] - z) * math.sin(flare)
        out.append({"kind": "beam", "name": f"solar_aft_frame_{nm}", "p0": (-(HALF + 0.03 + off), -0.83, z),
                    "p1": (-(HALF + 0.03 + off), 0.83, z), "w": 0.025, "h": 0.025, "mat": "white_paint"})
    for s in (-1, 1):
        out.append({"kind": "panel", "name": f"sun_shade_{'rl'[s > 0]}", "c": (-(HALF + 0.03), s * 0.55, ARR_BOT - 0.10), "u": (0, 1, 0),
                    "v": (0, 0, 1), "w": 0.50, "h": 0.20, "t": 0.004, "normal": (-1, 0, 0), "mat": "mli_viper_aft", "back": "mli_viper_aft"})
    return out


def _deck():
    out = [
        {"kind": "panel", "name": "radiator_aft_port", "c": (-0.42, 0.36, DECK_PEAK - 0.012), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.62,
         "h": 0.56, "t": 0.012, "mat": "osr_viper", "back": "frame_alu"},
        {"kind": "panel", "name": "radiator_aft_stbd", "c": (-0.42, -0.36, DECK_PEAK - 0.012), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.62,
         "h": 0.56, "t": 0.012, "mat": "osr_viper", "back": "frame_alu"},
        {"kind": "panel", "name": "radiator_mid_port", "c": (0.10, 0.42, DECK_PEAK - 0.02), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.36,
         "h": 0.42, "t": 0.012, "mat": "osr_viper", "back": "frame_alu"},
        {"kind": "panel", "name": "radiator_fwd_stbd", "c": (0.55, -0.50, DECK_PEAK - 0.03), "u": (1, 0, 0), "v": (0, 1, 0), "w": 0.36,
         "h": 0.40, "t": 0.012, "mat": "osr_viper", "back": "frame_alu"},
        {"kind": "box", "name": "star_tracker", "c": (-0.20, 0.66, DECK_PEAK - 0.02 + 0.07), "size": (0.12, 0.12, 0.14), "mat": "black_anodise"},
        {"kind": "tube", "name": "star_tracker_baffle", "p0": (-0.20, 0.66, DECK_PEAK + 0.12), "p1": (-0.25, 0.70, DECK_PEAK + 0.30), "r": 0.05,
         "r1": 0.065, "mat": "black_anodise"},
        {"kind": "box", "name": "reflectance_target_base", "c": (0.38, 0.12, DECK_PEAK + 0.01), "size": (0.06, 0.32, 0.02), "mat": "frame_alu"},
    ]
    for i, g in enumerate(("grey_90", "grey_60", "grey_35", "grey_18", "grey_05")):
        out.append({"kind": "box", "name": f"reflectance_patch_{i}", "c": (0.38, 0.24 - i * 0.06, DECK_PEAK + 0.023), "size": (0.05, 0.05, 0.006),
                    "mat": g})
    out.append({"kind": "panel", "name": "cal_checker_deck", "c": (0.40, -0.06, DECK_PEAK + 0.06), "u": (0, 1, 0), "v": (-0.5, 0, 0.866),
                "w": 0.16, "h": 0.16, "t": 0.008, "normal": (0.866, 0, 0.5), "mat": "checker", "back": "frame_alu"})
    out.append({"kind": "beam", "name": "cal_checker_deck_leg", "p0": (0.42, -0.06, DECK_PEAK - 0.02), "p1": (0.40, -0.06, DECK_PEAK + 0.02),
                "w": 0.02, "h": 0.02, "mat": "frame_alu"})
    return out


def _chimney():
    cx, cy = CHIMNEY
    z0, z1 = DECK_PEAK - 0.04, 1.80
    out = [
        {"kind": "box", "name": "trident_chimney", "c": (cx, cy, (z0 + z1) / 2), "size": (0.30, 0.26, z1 - z0), "mat": "mli_viper"},
        {"kind": "frustum", "name": "trident_chimney_cap", "c": (cx, cy), "bottom": (z1, 0.30, 0.26), "top": (z1 + 0.10, 0.10, 0.20),
         "top_offset": (-0.08, 0), "mat": "mli_viper"},
        {"kind": "panel", "name": "cal_checker_chimney", "c": (cx + 0.155, cy, 1.60), "u": (0, 1, 0), "v": (0, 0, 1), "w": 0.16, "h": 0.16,
         "t": 0.006, "normal": (1, 0, 0), "mat": "checker", "back": "frame_alu"},
        {"kind": "box", "name": "trident_motor_housing", "c": (cx - 0.04, cy, z1 - 0.06), "size": (0.14, 0.14, 0.10), "mat": "black_anodise"},
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append({"kind": "beam", "name": f"trident_chimney_post_{'fa'[sx > 0]}{'rl'[sy > 0]}",
                        "p0": (cx + sx * 0.155, cy + sy * 0.135, z0), "p1": (cx + sx * 0.155, cy + sy * 0.135, z1), "w": 0.018, "h": 0.018,
                        "mat": "frame_alu"})
    out.append({"kind": "beam", "name": "mast_brace", "p0": (cx + 0.15, cy + 0.13, 1.70), "p1": (MAST[0] - 0.03, MAST[1] - 0.04, 1.62),
                "w": 0.028, "h": 0.028, "mat": "frame_alu"})
    return out


def _drill():
    x, y = DRILL
    out = [
        {"kind": "box", "name": "trident_carriage", "link": "trident_deploy", "c": (x, y, 1.70), "size": (0.10, 0.10, 0.12), "mat": "frame_alu"},
        {"kind": "tube", "name": "trident_auger_rod", "link": "trident_auger", "p0": (x, y, LOWER[2] + 0.06), "p1": (x, y, 1.66), "r": 0.0127,
         "mat": "titanium"},
        {"kind": "tube", "name": "trident_bit", "link": "trident_auger", "p0": (x, y, LOWER[2] + 0.02), "p1": (x, y, LOWER[2] + 0.07), "r": 0.0127,
         "r1": 0.008, "mat": "black_anodise"},
        {"kind": "tube", "name": "trident_bit_tip", "link": "trident_auger", "p0": (x, y, LOWER[2] + 0.02), "p1": (x, y, LOWER[2] + 0.002),
         "r": 0.0127, "r1": 0.002, "mat": "titanium"},
    ]
    turns, z0, z1 = 26, LOWER[2] + 0.07, LOWER[2] + 1.10
    pts = []
    for i in range(turns * 16 + 1):
        t = i / (turns * 16)
        a = 2 * math.pi * turns * t
        pts.append((x + 0.019 * math.cos(a), y + 0.019 * math.sin(a), z0 + (z1 - z0) * t))
    out.append({"kind": "rail", "name": "trident_auger_flight", "link": "trident_auger", "points": pts, "r": 0.0045, "mat": "titanium"})
    return out


def _mast_head():
    x, y = MAST
    out = [
        *[{"kind": "disc", "name": f"nav_cam_{nm}_cover_plate", "link": f"nav_cam_{nm}_cover", "c": (x + 0.112, y + s * 0.20, TILT_Z - 0.09),
           "n": (1, 0, 0), "r": 0.036, "t": 0.006, "mat": "white_paint"} for s, nm in ((1, "left"), (-1, "right"))],
        *[{"kind": "tube", "name": f"nav_cam_{nm}_cover_hinge", "link": "nav_mast_tilt", "p0": (x + 0.115, y + s * 0.20 - 0.025, TILT_Z - 0.045),
           "p1": (x + 0.115, y + s * 0.20 + 0.025, TILT_Z - 0.045), "r": 0.006, "mat": "titanium"} for s, nm in ((1, "left"), (-1, "right"))],
        {"kind": "tube", "name": "nav_crossbar", "link": "nav_mast_tilt", "p0": (x, y - 0.44, TILT_Z), "p1": (x, y + 0.44, TILT_Z), "r": 0.022,
         "mat": "frame_alu"},
        {"kind": "box", "name": "nav_gimbal_block", "link": "nav_mast_tilt", "c": (x, y, TILT_Z), "size": (0.10, 0.14, 0.10), "mat": "mli_viper"},
    ]
    for s in (-1, 1):
        out.append({"kind": "box", "name": f"navlight_bracket_{'rl'[s > 0]}", "link": "nav_mast_tilt", "c": (x - 0.01, y + s * 0.40, TILT_Z),
                    "size": (0.05, 0.08, 0.04), "mat": "frame_alu"})
    return out


def _lights():
    x, y = MAST
    out = []
    cant = math.radians(10)
    for s, nm in ((1, "l"), (-1, "r")):
        out.append({"name": f"nav_light_{nm}", "link": "nav_mast_tilt", "pos": (x + 0.035, y + s * 0.38, TILT_Z),
                    "dir": (math.cos(cant), s * math.sin(cant), 0), "x_axis": (0, 1, 0), "shape": "rect", "width_m": 0.12, "height_m": 0.12,
                    "housing": (0.16, 0.16, 0.08), "housing_mat": "housing_alu", "lens_mat": "lamp_window", "group": "nav",
                    "peak_nm": LED_NM, "fwhm_nm": LED_FWHM, "radiant_w": 190.0, "fwhm_h_deg": 94.0, "fwhm_v_deg": 100.0, "beam_shape": 3.0,
                    "cone_deg": 75.0, "cone_softness": 0.3, "ies_name": "navlight",
                    "max_on_s": 10.0, "max_duty": 0.5, "description": "VIPER NavLight, 457 nm LED array with parabolic reflector",
                    "source": "LPSC 2022 #2466 (190 W light, 94 x 100 deg FOV); LPSC 2023 #2508"})
    x0, y0 = LOWER[0], LOWER[1]
    haz = [("haz_light_fl", (0.42, 0.37, 0.50), (0.45, 0.75, -0.50)),
           ("haz_light_fr", (0.42, -0.37, 0.50), (0.45, -0.75, -0.50)),
           ("haz_light_rl", (-0.42, 0.37, 0.50), (-0.45, 0.75, -0.50)),
           ("haz_light_rr", (-0.42, -0.37, 0.50), (-0.45, -0.75, -0.50)),
           ("haz_light_front", (x0 + 0.012, 0.0, 0.40), (1.0, 0.0, -0.55)),
           ("haz_light_aft", (-(x0 + 0.012), 0.0, 0.40), (-1.0, 0.0, -0.55))]
    for name, p, d in haz:
        out.append({"name": name, "pos": p, "dir": d, "shape": "rect", "width_m": 0.08, "height_m": 0.045, "housing": (0.11, 0.075, 0.045),
                    "housing_mat": "housing_alu", "lens_mat": "lamp_window", "group": "haz", "peak_nm": LED_NM, "fwhm_nm": LED_FWHM,
                    "radiant_w": 32.0, "fwhm_h_deg": 110.0, "fwhm_v_deg": 90.0, "beam_shape": 4.0, "cone_deg": 80.0, "cone_softness": 0.3,
                    "ies_name": "hazlight", "max_on_s": 10.0, "max_duty": 0.5,
                    "description": "VIPER HazLight, 457 nm LED with side-throw internal reflector",
                    "source": "LPSC 2022 #2466 (32 W light, 100 deg FOV); position inferred from Fig. 1 and LSIC 2024 CAD"})
    for i, (nm_peak, fw) in enumerate(((340, 12), (410, 15), (540, 30), (640, 20), (740, 30), (905, 40), (940, 40))):
        a = 2 * math.pi * i / 7
        out.append({"name": f"nirvss_led_{nm_peak}", "pos": (0.30 + 0.045 * math.cos(a), -0.06 + 0.045 * math.sin(a), LOWER[2] - 0.091),
                    "dir": (0, 0, -1), "radius_m": 0.006, "housing_mat": "black_anodise", "lens_mat": "lamp_lens_off", "group": "nirvss",
                    "peak_nm": float(nm_peak), "fwhm_nm": float(fw), "radiant_w": 0.5, "cone_deg": 60.0,
                    "description": f"NIRVSS AIM illumination LED set, {nm_peak} nm",
                    "source": "NIRVSS AIM LED wavelengths from the VIPER PIP; output and layout estimated"})
    return out


def _cameras():
    x, y = MAST
    out = []
    for s, nm in ((1, "left"), (-1, "right")):
        out.append({"name": f"nav_cam_{nm}", "link": "nav_mast_tilt", "pos": (x + 0.075, y + s * 0.20, TILT_Z), "forward": (1, 0, 0),
                    "housing": {"r": 0.034, "len": 0.10, "mat": "white_paint", "hood_mat": "alodine", "ring": (0.07, 0.035), "ring_mat": "white_paint"},
                    "spec": _vis(8.0, "VIPER NavCam stereo pair, 40 cm baseline, 70 x 70 deg", 3.0)})
        out.append({"name": f"aft_cam_{nm}", "pos": (-(HALF - 0.06), s * 0.15, DECK_PEAK + 0.04), "forward": (-1, 0, -0.45),
                    "housing": {"r": 0.03, "len": 0.08, "mat": "black_anodise"},
                    "spec": _vis(3.94, "VIPER AftCam stereo pair, 30 cm baseline, 110 x 110 deg (pinhole approximation)", 2.0)})
    for nm, sx, sy in (("fl", 1, 1), ("fr", 1, -1), ("rl", -1, 1), ("rr", -1, -1)):
        p = (sx * 0.12, sy * 0.68, HULL_Z[0] - 0.06)
        wheel = (sx * WB / 2, sy * (TRACK / 2 - 0.04), R_W * 0.8)
        out.append({"name": f"haz_cam_{nm}", "pos": p, "forward": tuple(b - a for a, b in zip(p, wheel)),
                    "housing": {"r": 0.028, "len": 0.07, "mat": "black_anodise"},
                    "spec": _vis(3.94, "VIPER HazCam, wheel-well mono camera, 110 x 110 deg (pinhole approximation)", 0.7)})
    out.append({"name": "nirvss_aim", "pos": (0.30, -0.06, LOWER[2] - 0.092), "forward": (0, 0, -1), "up": (1, 0, 0), "housing": False,
                "spec": {"focal_mm": 16.0, "aperture_mm": (11.264, 11.264), "fstop": 0.0, "f_number": 8.0, "focus_m": 0.3, "clip_m": (0.05, 20.0), "resolution": (2048, 2048),
                         "source": "NIRVSS Ancillary Imaging Module, 4 MP CMOS, f/8 16 mm (sensor size estimated)"}})
    return out


ROVER = {
    "wheel": {"r": R_W, "w": 0.20, "style": "grouser", "grousers": 20, "grouser_h": 0.025, "chevron": False, "hub_frac": 0.22,
              "rim_frac": 0.86, "mass": 8.0, "drum_mat": "wheel_alu", "grouser_mat": "wheel_alu", "spoke_mat": "titanium",
              "hub_mat": "hub_white", "hub_centre_mat": "alodine", "motor_mat": "black_anodise", "flange": (0.035, "wheel_flange"), "wire_spokes": (24, 0.0016, 0.09),
              "gussets": ((0.045, 0.035, 0.004), "alodine", 0.0035)},
    "wheels": K.four_wheels(WB, TRACK, (math.radians(-50), math.radians(50))),
    "suspension": {"type": "double_wishbone", "active": True, "arm": 0.26, "upper_ratio": 1.0, "upper_dz": 0.30, "lower_dz": 0.12,
                   "kingpin_off": 0.14, "travel": (0.18, 0.18), "static_rad": 0.08, "strut": False, "spread": 0.10, "tube_r": 0.016,
                   "arm_mat": "frame_alu", "knuckle_mat": "frame_alu", "boot": "sock", "actuator": (0.14, 0.09, 0.22),
                   "actuator_mat": "black_anodise"},
    "links": [
        {"name": "trident_deploy", "type": "prismatic", "pos": (DRILL[0], DRILL[1], 1.70), "axis": (0, 0, -1), "limit": (0.0, 0.38), "role": "arm",
         "mass": 6.0, "drive": {"kind": "position", "stiffness": 4000.0, "damping": 400.0, "max_force": 800.0}},
        {"name": "trident_feed", "parent": "trident_deploy", "type": "prismatic", "pos": (DRILL[0], DRILL[1], 1.66), "axis": (0, 0, -1),
         "limit": (0.0, 1.24), "role": "arm", "mass": 3.0, "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 500.0}},
        {"name": "trident_auger", "parent": "trident_feed", "type": "revolute", "pos": (DRILL[0], DRILL[1], 1.0), "axis": (0, 0, -1),
         "role": "drill", "mass": 1.5, "drive": {"kind": "velocity", "stiffness": 0.0, "damping": 20.0, "max_force": 60.0}},
        *[{"name": f"nav_cam_{nm}_cover", "parent": "nav_mast_tilt", "type": "revolute",
           "pos": (MAST[0] + 0.115, MAST[1] + s * 0.20, TILT_Z - 0.045), "axis": (0, -1, 0), "limit": (0.0, math.pi), "role": "hatch",
           "mass": 0.05, "drive": {"kind": "position", "stiffness": 2.0, "damping": 0.2, "max_force": 2.0}} for s, nm in ((1, "left"), (-1, "right"))],
    ],
    "parts": [*_hull(), *_flaps(), *_arrays(), *_deck(), *_chimney(), *_drill(), *_mast_head()],
    "masts": [{"name": "nav_mast", "base": (MAST[0], MAST[1], DECK_PEAK - 0.03), "h": MAST_TOP - DECK_PEAK + 0.03, "r": 0.05, "mat": "mli_viper",
               "foot": (0.16, 0.16, 0.05), "head": (0.06, 0.06, 0.10), "head_mat": "mli_viper", "cams": ()}],
    "hga": {"base": (MAST[0], MAST[1], MAST_TOP), "h": 0.24, "r": 0.18, "mast_r": 0.022, "boresight": (1, 0, 0.3), "band": "X",
            "flat": (0.34, 0.34, 0.03), "front": "white_paint", "back": "mli_viper", "frame_mat": "frame_alu", "lga": 0.08},
    "lights": _lights(),
    "cameras": _cameras(),
    "sites": [("trident_bit", "trident_feed", (DRILL[0], DRILL[1], LOWER[2] + 0.002), (0, 0, -1), "tool", "TRIDENT 25.4 mm bit (1.02 m max depth)"),
              ("lift_point", "chassis", (0, 0, DECK_PEAK), (0, 0, 1), "handling", "Deck lift point")],
    "imu": (0, 0, 0.6),
}

MASS = {"roving": {"mass": 447.0, "com_z": 0.62, "source": "NASA: 447 kg roving"},
        "launch": {"mass": 490.0, "com_z": 0.62, "source": "NASA: 490 kg at launch"}}
DEFAULT_MASS_STATE = "roving"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (1.6, 1.6, 1.0)

SEMANTIC_CLASS = ["lunar_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
URDF = True
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("mli_viper", "mli_viper_aft"))
SIMPLE_TRIS = 20000
RENDER_VIEWS = {**K.views(1.7, 1.7, 2.5, centre_z=1.1), "front": ((5.5, 0.0, 1.4), (0, 0, 1.2), 35),
                "mast": ((2.4, 1.6, 2.3), (MAST[0], MAST[1], 2.1), 30), "night_drive": ((-4.6, -2.4, 3.8), (3.0, 0.4, 0.0), 30)}
