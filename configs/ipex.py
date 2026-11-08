import math

import rover_kit as K

ASSET_ID = "ipex"
ASSET_PATH = "nasa/ipex/rover"
FAMILY = "rover"
TITLE = "NASA IPEx excavator"
DOC = ("NASA KSC Swamp Works IPEx (ISRU, now Infrastructure, Pilot Excavator), TRL 5/6 design: a 30 kg-class regolith "
       "excavator, 1.33 x 0.64 x 0.57 m with its arms at the 40 deg driving pose. A white chassis with an actuated "
       "Cerakote radiator cover over a PCM heat sink and a wireless-charging receive coil, four 0.305 m skid-steered wheels "
       "with gold conversion-coated rings and spokes and perforated hard-anodised cleat plates, no suspension, and one arm "
       "at each end carrying a pair of 0.30 x 0.26 m billet-aluminium bucket drums on a through-shaft actuator. The front "
       "and rear drums dig in opposite directions so the excavation forces cancel; each cycle carries up to 30 kg of "
       "regolith, dumped by reversing the drums. Two 5 cm stereo pairs, four mono cameras and six LED lights.")

TEXTURE_SETS, MATERIALS = K.materials(
    textures={
        "ipex_white": ("worn_coating", dict(colour=(0.78, 0.78, 0.76), tile_m=0.3, metallic=0.0, rough0=0.7, seed=5101)),
        "ipex_cover": ("worn_coating", dict(colour=(0.75, 0.75, 0.73), tile_m=0.3, metallic=0.0, rough0=0.5, seed=5102)),
        "drum_anodise": ("bead_blast", dict(colour=(0.12, 0.12, 0.115), tile_m=0.20, rough0=0.5, metallic=0.28, grain=1.2, mottle=0.08,
                                            edge_wear=0.4, seed=5103)),
        "drum_frame": ("bead_blast", dict(colour=(0.10, 0.10, 0.095), tile_m=0.20, rough0=0.5, metallic=0.28, grain=0.8, seed=5104)),
        "cleat_plate": ("perforated_oval", dict(colour=(0.07, 0.07, 0.065), tile_m=0.12, hole=(0.027, 0.016), pitch=(0.040, 0.040),
                                                rough0=0.55, metallic=0.3, seed=5105)),
        "gold_conversion": ("bead_blast", dict(colour=(0.59, 0.47, 0.20), tile_m=0.15, rough0=0.5, metallic=0.9, grain=0.7, mottle=0.12,
                                               edge_wear=0.3, seed=5106)),
        "radiator_s13": ("panel", dict(colour=(0.90, 0.90, 0.88), tile_m=0.3, rough0=0.7, fastener_pitch=0.05)),
    },
    overrides={
        "ipex_white": {"set": "ipex_white", "normal": 0.5},
        "ipex_cover": {"set": "ipex_cover", "normal": 0.5},
        "drum_anodise": {"set": "drum_anodise", "normal": 0.6},
        "drum_frame": {"set": "drum_frame", "normal": 0.5},
        "cleat_plate": {"set": "cleat_plate", "normal": 0.5, "alpha": True},
        "gold_conversion": {"set": "gold_conversion", "normal": 0.4},
        "radiator_s13": {"set": "radiator_s13", "normal": 0.4},
        "grouser_anodise": {"color": (0.07, 0.07, 0.065), "roughness": 0.52, "metallic": 0.28},
        "scoop_shadow": {"color": (0.015, 0.015, 0.017), "roughness": 0.8},
        "spiral_groove": {"color": (0.12, 0.12, 0.13), "roughness": 0.6, "metallic": 0.6},
        "coil_green": {"color": (0.05, 0.25, 0.10), "roughness": 0.4},
        "lens_blue": {"color": (0.02, 0.10, 0.30), "roughness": 0.05, "metallic": 0.2},
        "fiducial": {"color": (0.02, 0.02, 0.02), "roughness": 0.7},
    })

R_W, GROUSER_H = 0.1655, 0.013
WB, TRACK = 0.466, 0.51
SHOULDER = (0.235, 0.185)
ARM_LEN, ARM_POSE = 0.36, math.radians(40)
DRUM_R, DRUM_W = 0.150, 0.255
DRUM_Y = (0.065, 0.320)
BODY_TOP = 0.250
COVER_HINGE_X = -0.135
DRUM_SPEED = 2000.0 / 160.0 * 2 * math.pi / 60.0
END_T, FRAME_T, WALL_T = 0.003, 0.003, 0.002
RASSOR_SPIRAL = ((0, 0.214), (30, 0.201), (60, 0.188), (90, 0.176), (120, 0.168), (150, 0.166), (180, 0.165), (210, 0.152), (240, 0.126),
                 (270, 0.098), (300, 0.078), (330, 0.066), (350, 0.064))
SPIRAL_SCALE = (DRUM_R - WALL_T / 2) / RASSOR_SPIRAL[0][1]
SPIRAL_PHI = (0.0, 350.0)
SPIRAL_R = (RASSOR_SPIRAL[-1][1] * SPIRAL_SCALE, RASSOR_SPIRAL[6][1] * SPIRAL_SCALE, DRUM_R - WALL_T / 2)
SPIRAL_CHUNKS = 16
REGOLITH_BULK = 1500.0


def _drum_centre(sx):
    return (sx * (SHOULDER[0] + ARM_LEN * math.cos(ARM_POSE)), 0.0, SHOULDER[1] + ARM_LEN * math.sin(ARM_POSE))


def _radial(c, a, r, y):
    return (c[0] + r * math.cos(a), y, c[2] + r * math.sin(a))


def _ring(name, link, c, r0, r1, y0, y1, mat="drum_anodise"):
    y0, y1 = min(y0, y1), max(y0, y1)
    e = 0.0003
    prof = [(r0, y0), (r1 - 0.003, y0), (r1 - e, y0), (r1, y0 + e), (r1, y1 - e), (r1 - e, y1), (r1 - 0.003, y1), (r0, y1)]
    return {"kind": "lathe", "name": name, "link": link, "c": (c[0], 0.0, c[2]), "n": (0, 1, 0), "profile": prof, "sides": 48, "mat": mat}


def _spiral_r(phi):
    a = SPIRAL_PHI[1] - phi
    for (a0, r0), (a1, r1) in zip(RASSOR_SPIRAL, RASSOR_SPIRAL[1:]):
        if a0 <= a <= a1:
            return (r0 + (r1 - r0) * (a - a0) / (a1 - a0)) * SPIRAL_SCALE
    return RASSOR_SPIRAL[-1][1] * SPIRAL_SCALE


def _drum(tag, sx, sy):
    link = f"{tag}_drums"
    c = _drum_centre(sx)
    lead = -sx
    y_in, y_out = sy * DRUM_Y[0], sy * DRUM_Y[1]
    pre = f"{tag}_drum_{'l' if sy > 0 else 'r'}"
    out = [_ring(f"{pre}_end_plate", link, c, 0.001, DRUM_R, y_out - sy * END_T, y_out),
           _ring(f"{pre}_inner_plate", link, c, 0.001, DRUM_R - 0.002, y_in, y_in + sy * END_T)]
    span = DRUM_W - 2 * END_T
    slice_w = (span - 3 * FRAME_T) / 4
    phase = 22.5 if sy > 0 else 0.0
    for k in range(4):
        s0 = y_in + sy * (END_T + k * (slice_w + FRAME_T))
        s1 = s0 + sy * slice_w
        y0, y1 = min(s0, s1), max(s0, s1)
        for j in range(2):
            base = phase + 45.0 * k + 180.0 * j
            pts = []
            phi = SPIRAL_PHI[0]
            while phi <= SPIRAL_PHI[1] + 1e-6:
                a = math.radians(base + lead * phi)
                r = _spiral_r(phi)
                pts.append((r * math.cos(a), r * math.sin(a)))
                phi += 3.0
            out.append({"kind": "wall", "name": f"{pre}_s{k}_spiral_{j}", "link": link, "c": (c[0], 0.0, c[2]), "points": pts, "t": WALL_T,
                        "y": (y0, y1), "chunks": SPIRAL_CHUNKS, "mat": "drum_anodise"})
            a = math.radians(base + lead * SPIRAL_PHI[1])
            tan = (-math.sin(a) * lead, 0, math.cos(a) * lead)
            out.append({"kind": "obox", "name": f"{pre}_s{k}_lip_{j}", "link": link, "c": _radial(c, a, SPIRAL_R[2] + 0.004, (y0 + y1) / 2),
                        "ax": (0, 1, 0), "ay": tan, "size": (slice_w * 0.96, 0.014, 0.010), "mat": "drum_anodise"})
        if k < 3:
            f0 = s1
            f1 = s1 + sy * FRAME_T
            out.append(_ring(f"{pre}_frame_{k}_rim", link, c, SPIRAL_R[2] - 0.016, SPIRAL_R[2] - 0.004, f0, f1, mat="drum_frame"))
            out.append(_ring(f"{pre}_frame_{k}_hub", link, c, 0.012, 0.030, f0, f1, mat="drum_frame"))
            for q in range(4):
                a = math.radians(phase + 45.0 * k + 90.0 * q + 20.0)
                mid = (0.030 + SPIRAL_R[2] - 0.016) / 2
                out.append({"kind": "obox", "name": f"{pre}_frame_{k}_spoke_{q}", "link": link, "c": _radial(c, a, mid, (f0 + f1) / 2),
                            "ax": (math.cos(a), 0, math.sin(a)), "ay": (0, 1, 0), "size": (SPIRAL_R[2] - 0.016 - 0.030 + 0.004, FRAME_T, 0.016),
                            "mat": "drum_frame"})
    yf = y_out + sy * 0.0012
    for arm in range(2):
        pts = []
        for i in range(41):
            t = i / 40
            a = math.pi * arm - lead * sy * 1.6 * math.pi * t
            r = 0.022 + 0.105 * t
            pts.append((c[0] + r * math.cos(a), yf, c[2] + r * math.sin(a)))
        out.append({"kind": "rail", "name": f"{pre}_spiral_mark_{arm}", "link": link, "points": pts, "r": 0.0016, "mat": "spiral_groove"})
    return out


def _drum_volume(sx):
    n = 720
    area = 0.0
    for i in range(n):
        a0 = 360.0 * i / n
        rs = []
        for j in range(2):
            for phi in (a0 - 180.0 * j + 360.0 * m for m in range(-2, 3)):
                if SPIRAL_PHI[0] <= phi <= SPIRAL_PHI[1]:
                    rs.append(_spiral_r(phi))
        rs.sort()
        inner = rs[0] if len(rs) > 1 else 0.0
        area += 0.5 * (min(rs[-1], DRUM_R) ** 2 - inner ** 2) * math.radians(360.0 / n) if rs else 0.0
    return area * 4 * ((DRUM_W - 2 * END_T - 3 * FRAME_T) / 4) * 2


def _arm(tag, sx):
    link = f"{tag}_arm"
    s = (sx * SHOULDER[0], 0.0, SHOULDER[1])
    c = _drum_centre(sx)
    d = (math.cos(ARM_POSE) * sx, 0, math.sin(ARM_POSE))
    cam = (c[0] + sx * 0.050, 0.0, c[2] - 0.035)
    return [
        {"kind": "tube", "name": f"{tag}_arm_tube", "link": link, "p0": s, "p1": c, "r": 0.020, "mat": "ipex_white"},
        {"kind": "tube", "name": f"{tag}_shoulder_tee", "link": link, "p0": (s[0], -0.042, s[2]), "p1": (s[0], 0.042, s[2]), "r": 0.040,
         "mat": "ipex_white"},
        {"kind": "tube", "name": f"{tag}_arm_root", "link": link, "p0": s, "p1": tuple(s[i] + d[i] * 0.07 for i in range(3)), "r": 0.028,
         "mat": "ipex_white"},
        {"kind": "tube", "name": f"{tag}_drum_actuator", "link": link, "p0": (c[0], -DRUM_Y[0] + 0.004, c[2]), "p1": (c[0], DRUM_Y[0] - 0.004, c[2]),
         "r": 0.046, "mat": "ipex_white"},
        {"kind": "box", "name": f"{tag}_mono_cam_box", "link": link, "c": (cam[0] - sx * 0.022, 0.0, cam[2]), "size": (0.050, 0.060, 0.045),
         "mat": "ipex_white"},
    ]


def _chassis():
    out = [
        {"kind": "box", "name": "lower_body", "c": (0, 0, 0.165), "size": (0.37, 0.30, 0.080), "mat": "ipex_white"},
        {"kind": "box", "name": "upper_body", "c": (0, 0, 0.226), "size": (0.30, 0.28, 0.046), "mat": "ipex_white"},
        {"kind": "box", "name": "radiator_s13", "c": (0, 0, BODY_TOP - 0.002), "size": (0.26, 0.26, 0.004), "mat": "radiator_s13"},
        {"kind": "box", "name": "belly_plate", "c": (0, 0, 0.127), "size": (0.33, 0.26, 0.006), "mat": "aluminium"},
        {"kind": "box", "name": "lift_knob_base", "c": (0.0, 0.135, BODY_TOP + 0.004), "size": (0.03, 0.03, 0.008), "mat": "aluminium"},
        {"kind": "tube", "name": "lift_knob", "p0": (0.0, 0.135, BODY_TOP + 0.008), "p1": (0.0, 0.135, BODY_TOP + 0.030), "r": 0.010,
         "mat": "aluminium"},
    ]
    for sx in (-1, 1):
        x, z = sx * SHOULDER[0], SHOULDER[1]
        tag = "front" if sx > 0 else "rear"
        out.append({"kind": "box", "name": f"{tag}_shoulder_saddle", "c": (sx * 0.205, 0, 0.180), "size": (0.06, 0.30, 0.07), "mat": "ipex_white"})
        for sy in (-1, 1):
            out.append({"kind": "tube", "name": f"{tag}_shoulder_housing_{'l' if sy > 0 else 'r'}", "p0": (x, sy * 0.046, z),
                        "p1": (x, sy * 0.165, z), "r": 0.052, "mat": "ipex_white"})
            out.append({"kind": "tube", "name": f"{tag}_shoulder_cap_{'l' if sy > 0 else 'r'}", "p0": (x, sy * 0.165, z),
                        "p1": (x, sy * 0.170, z), "r": 0.044, "mat": "aluminium"})
            out.append({"kind": "tube", "name": f"{tag}_wheel_actuator_{'l' if sy > 0 else 'r'}", "p0": (sx * WB / 2, sy * 0.150, R_W),
                        "p1": (sx * WB / 2, sy * 0.188, R_W), "r": 0.040, "mat": "ipex_white"})
    for sy in (-1, 1):
        nm = "l" if sy > 0 else "r"
        out.append({"kind": "box", "name": f"side_cam_mount_{nm}", "c": (0, sy * 0.165, 0.215), "size": (0.06, 0.03, 0.05), "mat": "ipex_white"})
        for dx in (-0.025, 0.025):
            out.append({"kind": "tube", "name": f"side_cam_strut_{nm}_{'fa'[dx > 0]}", "p0": (dx, sy * 0.175, 0.20),
                        "p1": (0, sy * 0.268, 0.222), "r": 0.004, "mat": "titanium"})
        out.append({"kind": "box", "name": f"side_cam_box_{nm}", "c": (0, sy * 0.282, 0.225), "size": (0.06, 0.035, 0.05), "mat": "ipex_white"})
    for sx, sy, kind in ((1, 1, "stereo"), (1, -1, "lights"), (-1, -1, "stereo"), (-1, 1, "lights")):
        tag = ("front" if sx > 0 else "rear") + "_" + kind
        out.append({"kind": "box", "name": f"{tag}_box", "c": (sx * 0.250, sy * 0.105, 0.262), "size": (0.055, 0.105, 0.050), "mat": "ipex_white"})
        out.append({"kind": "box", "name": f"{tag}_post", "c": (sx * 0.240, sy * 0.105, 0.230), "size": (0.03, 0.04, 0.03), "mat": "ipex_white"})
    return out


def _cover():
    link = "radiator_cover"
    cx = COVER_HINGE_X + 0.135
    z = BODY_TOP + 0.006
    return [
        {"kind": "box", "name": "radiator_cover_panel", "link": link, "c": (cx, 0, z), "size": (0.27, 0.27, 0.008), "mat": "ipex_cover"},
        {"kind": "tube", "name": "radiator_cover_hinge", "link": link, "p0": (COVER_HINGE_X, -0.12, z), "p1": (COVER_HINGE_X, 0.12, z),
         "r": 0.007, "mat": "aluminium"},
        {"kind": "tube", "name": "charger_receiver", "link": link, "p0": (cx - 0.02, 0, z + 0.004), "p1": (cx - 0.02, 0, z + 0.034), "r": 0.060,
         "mat": "ipex_white"},
        {"kind": "disc", "name": "charger_coil", "link": link, "c": (cx - 0.02, 0, z + 0.034), "n": (0, 0, 1), "r": 0.050, "t": 0.002,
         "mat": "gold_conversion"},
        {"kind": "disc", "name": "charger_coil_centre", "link": link, "c": (cx - 0.02, 0, z + 0.036), "n": (0, 0, 1), "r": 0.030, "t": 0.001,
         "mat": "coil_green"},
        {"kind": "box", "name": "cover_fiducial_0", "link": link, "c": (cx + 0.085, 0.085, z + 0.0045), "size": (0.03, 0.03, 0.001), "mat": "fiducial"},
        {"kind": "box", "name": "cover_fiducial_1", "link": link, "c": (cx + 0.085, -0.085, z + 0.0045), "size": (0.03, 0.03, 0.001), "mat": "fiducial"},
        {"kind": "box", "name": "cover_actuator", "c": (COVER_HINGE_X - 0.008, -0.11, z - 0.014), "size": (0.03, 0.04, 0.016), "mat": "anodised_dark"},
    ]


def _lights():
    out = []
    for sx, sy in ((1, -1), (-1, 1)):
        for dy in (-0.025, 0.025):
            nm = f"{'front' if sx > 0 else 'rear'}_light_{'io'[(dy * sy) > 0]}"
            out.append({"name": nm, "pos": (sx * 0.279, sy * 0.105 + dy, 0.262), "dir": (sx, 0, -0.25), "radius_m": 0.014,
                        "housing_mat": "ipex_white", "lens_mat": "lamp", "group": "work", "lumens": 3000.0, "colour_k": 5000.0,
                        "fwhm_h_deg": 42.0, "fwhm_v_deg": 42.0, "beam_shape": 2.0, "cone_deg": 50.0, "cone_softness": 0.3, "ies_name": "ipex_led",
                        "description": "IPEx LED light unit (3 LEDs)",
                        "source": "IPEx TRL 5 design: 6 LED units, 3000 lm, 42 deg FWHM; placement from TRL 5 Fig. 28, side units inferred"})
    for sy in (-1, 1):
        out.append({"name": f"side_light_{'l' if sy > 0 else 'r'}", "pos": (0.040, sy * 0.300, 0.225), "dir": (0, sy, -0.2), "radius_m": 0.012,
                    "housing_mat": "ipex_white", "lens_mat": "lamp", "group": "work", "lumens": 3000.0, "colour_k": 5000.0, "fwhm_h_deg": 42.0,
                    "fwhm_v_deg": 42.0, "beam_shape": 2.0, "cone_deg": 50.0, "cone_softness": 0.3, "ies_name": "ipex_led",
                    "description": "IPEx LED light unit (3 LEDs)", "source": "IPEx TRL 5 design: 6 LED units; side placement inferred"})
    return out


def _cam(desc, focal, focus):
    return {"focal_mm": focal, "aperture_mm": (5.63, 4.69), "fstop": 4.0, "f_number": 4.0, "focus_m": focus, "clip_m": (0.03, 200.0),
            "resolution": (2472, 2064), "source": f"{desc}; Sony IMX547 5.1 MP, S-mount f/4 lens, ejectable EDS dust shield (IPEx TRL 5 paper)"}


def _cameras():
    out = []
    for sx, sy in ((1, 1), (-1, -1)):
        end = "front" if sx > 0 else "rear"
        for k, dy in enumerate((-0.025, 0.025)):
            out.append({"name": f"{end}_stereo_{'lr'[(dy * sy) < 0]}", "pos": (sx * 0.279, sy * 0.105 + dy, 0.264), "forward": (sx, 0, -0.30),
                        "housing": {"r": 0.015, "len": 0.02, "mat": "ipex_white", "hood_mat": "ipex_white"},
                        "spec": _cam(f"IPEx {end} stereo pair, 5 cm baseline", 4.4, 1.5)})
    for sx in (-1, 1):
        end = "front" if sx > 0 else "rear"
        c = _drum_centre(sx)
        out.append({"name": f"{end}_drum_cam", "link": f"{end}_arm", "pos": (c[0] + sx * 0.050, 0.0, c[2] - 0.035), "forward": (sx, 0, -0.6),
                    "housing": {"r": 0.016, "len": 0.02, "mat": "ipex_white", "hood_mat": "ipex_white"},
                    "spec": _cam(f"IPEx {end} mono camera between the drums", 4.4, 0.8)})
    for sy in (-1, 1):
        out.append({"name": f"side_cam_{'l' if sy > 0 else 'r'}", "pos": (0, sy * 0.300, 0.225), "forward": (0, sy, -0.25),
                    "housing": {"r": 0.016, "len": 0.02, "mat": "ipex_white", "hood_mat": "ipex_white"},
                    "spec": _cam("IPEx side-facing mono camera", 6.0, 1.0)})
    return out


def _wheel_face(name, x, y):
    side = 1 if y > 0 else -1
    yo = y + side * 0.058
    c = (x, yo, R_W)
    link = f"{name}_wheel"
    out = [{"kind": "disc", "name": f"{name}_hub_flange", "link": link, "c": c, "n": (0, side, 0), "r": 0.036, "t": 0.006, "mat": "gold_conversion"},
           {"kind": "disc", "name": f"{name}_hub_bore", "link": link, "c": (x, yo + side * 0.006, R_W), "n": (0, side, 0), "r": 0.018, "t": 0.002,
            "mat": "anodised_dark"}]
    for tag, sg, chamfer in (("outer", side, 0.006), ("inner", -side, 0.0)):
        y0, y1 = y + sg * 0.0662, y + sg * 0.0722
        prof = [(0.136, y0), (R_W - GROUSER_H, y0), (R_W - GROUSER_H, y0 + sg * 0.0015), (R_W - GROUSER_H - chamfer, y1), (0.136, y1), (0.136, y0)]
        out.append({"kind": "lathe", "name": f"{name}_side_ring_{tag}", "link": link, "c": (x, 0.0, R_W), "n": (0, 1, 0), "profile": prof, "sides": 64,
                    "mat": "gold_conversion"})
    for k in range(5):
        a = math.pi / 2 + 2 * math.pi * k / 5
        d = (math.cos(a), 0, math.sin(a))
        mid = 0.03 + (0.140 - 0.03) / 2
        out.append({"kind": "obox", "name": f"{name}_spoke_{k}", "link": link, "c": (x + d[0] * mid, yo + side * 0.002, R_W + d[2] * mid),
                    "ax": d, "ay": (-d[2], 0, d[0]), "size": (0.110, 0.020, 0.006), "mat": "gold_conversion"})
        for j in range(3):
            r = 0.060 + 0.028 * j
            out.append({"kind": "disc", "name": f"{name}_spoke_hole_{k}_{j}", "link": link, "c": (x + d[0] * r, yo + side * 0.0045, R_W + d[2] * r),
                        "n": (0, side, 0), "r": 0.0055, "t": 0.0012, "sides": 12, "mat": "anodised_dark"})
    return out


def _arm_link(tag, sx):
    return {"name": f"{tag}_arm", "pos": (sx * SHOULDER[0], 0.0, SHOULDER[1]), "axis": (0, -sx, 0), "limit": (-1.05, 1.05), "role": "arm",
            "mass": 1.5, "drive": {"kind": "position", "stiffness": 400.0, "damping": 40.0, "max_force": 60.0}}


def _drum_link(tag, sx):
    return {"name": f"{tag}_drums", "parent": f"{tag}_arm", "type": "revolute", "pos": _drum_centre(sx), "axis": (0, sx, 0), "role": "excavate",
            "mass": 7.0, "drive": {"kind": "velocity", "stiffness": 0.0, "damping": 20.0, "max_force": 50.0}}


ROVER = {
    "wheel": {"r": R_W, "w": 0.13, "style": "grouser", "grousers": 24, "grouser_h": GROUSER_H, "chevron": False, "spokes": 0, "hub_frac": 0.12, "rim_frac": 0.90, "mass": 1.0, "drum_mat": "cleat_plate", "grouser_mat": "grouser_anodise",
              "spoke_mat": "gold_conversion", "rim_mat": "gold_conversion", "hub_mat": "gold_conversion", "hub_cap_mat": "aluminium", "drive_tau": 15.0, "segments": 48},
    "wheels": K.four_wheels(WB, TRACK, None),
    "suspension": {"type": "carrier", "kingpin_off": 0.068, "upper_dz": 0.0, "knuckle_t": 0.03, "knuckle_mat": "ipex_white"},
    "links": [_arm_link("front", 1), _arm_link("rear", -1), _drum_link("front", 1), _drum_link("rear", -1),
              {"name": "radiator_cover", "pos": (COVER_HINGE_X, 0, BODY_TOP + 0.006), "axis": (0, -1, 0), "limit": (0.0, math.pi / 2),
               "role": "hatch", "mass": 0.4, "drive": {"kind": "position", "stiffness": 5.0, "damping": 0.5, "max_force": 5.0}}],
    "parts": [*_chassis(), *_cover(), *_arm("front", 1), *_arm("rear", -1),
              *[q for w in K.four_wheels(WB, TRACK) for q in _wheel_face(w["name"], w["x"], w["y"])],
              *_drum("front", 1, 1), *_drum("front", 1, -1), *_drum("rear", -1, 1), *_drum("rear", -1, -1)],
    "lights": _lights(),
    "cameras": _cameras(),
    "sites": [("front_drums_cut", "front_arm", (_drum_centre(1)[0], 0, _drum_centre(1)[2] - DRUM_R), (0, 0, -1), "tool",
               "Front bucket-drum pair, lowest scoop lip (cutting edge when digging)"),
              ("rear_drums_cut", "rear_arm", (_drum_centre(-1)[0], 0, _drum_centre(-1)[2] - DRUM_R), (0, 0, -1), "tool",
               "Rear bucket-drum pair, lowest scoop lip (cutting edge when digging)"),
              *[(f"{tag}_drums_volume", f"{tag}_drums", _drum_centre(sx), (0, 1, 0), "payload",
                 "Bucket-drum pair regolith store (two drums, spiral-baffle channels between the outer shells and the inner spiral turns)",
                 {"volume_m3": round(_drum_volume(sx), 4), "capacity_kg": round(_drum_volume(sx) * REGOLITH_BULK, 1), "nominal_load_kg": 15.0,
                  "bulk_density_kg_m3": REGOLITH_BULK, "radius_m": DRUM_R, "width_m": DRUM_W, "drums": 2})
                for tag, sx in (("front", 1), ("rear", -1))],
              ("charger_coil", "radiator_cover", (-0.02, 0, BODY_TOP + 0.042), (0, 0, 1), "power",
               "WiBotic wireless-charging receive coil (dock under the lander transmitter)"),
              ("lift_point", "chassis", (0.0, 0.135, BODY_TOP + 0.03), (0, 0, 1), "handling", "Knurled lift knob")],
    "imu": (0, 0, 0.20),
}

MASS = {"empty": {"mass": 30.0, "com_z": 0.21, "source": "NASA: 30 kg-class excavator (TRL 5 paper)"},
        "loaded": {"mass": 60.0, "com_z": 0.28, "source": "30 kg vehicle plus 30 kg of regolith in the four drums (TRL 5 paper: up to 30 kg per cycle)"}}
DEFAULT_MASS_STATE = "empty"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (0.40, 0.35, 0.15)

SEMANTIC_CLASS = ["lunar_rover", "excavator", "vehicle"]
ROBOT_TYPE = "Wheeled"
URDF = True
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("ipex_white",))
COLLIDERS["(front|rear)_drums"] = [("drum", ["drum_anodise"], {"islands": True})]
PHYSICS_MATERIAL["drum"] = "anodised_aluminium"
PHYSICS_MATERIALS["anodised_aluminium"] = (0.6, 0.5, 0.05)
SEPARATE_COPLANAR = False
SIMPLE_TRIS = 12000
RENDER_VIEWS = {**K.views(1.05, 0.64, 0.57, centre_z=0.26), "drums": ((1.45, -0.95, 0.75), (0.45, 0, 0.36), 32),
                "digging": ((1.6, -1.3, 0.55), (0, 0, 0.18), 38)}
