import math

import rover_kit as K

ASSET_ID = "mph"
ASSET_PATH = "asi_thales/mph/habitat"
FAMILY = "rover"
TITLE = "ASI / Thales Alenia Space Multi-Purpose Habitation (MPH)"
DOC = ("ASI / Thales Alenia Space Multi-Purpose Habitation module, 2025 reference configuration (ICES-2025-60): the first "
       "Artemis surface habitat, a rigid 3 m x 6.55 m horizontal pressure hull (14 m3 airlock + 24 m3 habitat, 8.2 psia) "
       "closed by two axial bulkheads behind thick MDPS end rings, on eight 1.44 m all-metal Astrobotic wheels (twin "
       "perforated tread bands, tensioned-cable spokes) in two walking-beam bogies per side, with the corner wheels "
       "steering. The EVA bulkhead carries a 1.25 x 1.95 m EVA door with a window, a fold-down porch and a ladder; the "
       "docking bulkhead carries a second door inside a surface docking ring (shirtsleeve path to the pressurised rover). "
       "Two 1.8 x 8 m vertical roll-out solar blankets rise from a sun-tracking roof pedestal (Solar=stowed retracts them "
       "for driving), two 3-panel radiator wings hinge from the roof shoulders, battery and power-control boxes ride on "
       "the flanks, O2 and N2 tanks under the belly, berthing ports on both flanks, gimballed dishes, lights and handrails. "
       "Overall dimensions and the wheel size come from a two-view camera match of the ICES-2025-60 CAD figures scaled "
       "to the 3 m hull.")

TEXTURE_SETS, MATERIALS = K.materials(
    overrides={
        "hull_mdps": {"set": "hull_mdps", "normal": 0.7},
        "ring_grey": {"set": "ring_grey", "normal": 0.7},
        "box_beige": {"set": "box_beige", "normal": 0.6},
        "wheel_plate": {"set": "wheel_plate", "normal": 0.8},
        "radiator_blue": {"color": (0.05, 0.07, 0.20), "roughness": 0.3, "metallic": 0.25},
        "canister_navy": {"color": (0.06, 0.08, 0.20), "roughness": 0.4, "metallic": 0.3},
        "orange": {"color": (0.85, 0.35, 0.05), "roughness": 0.4},
        "door_grey": {"color": (0.50, 0.49, 0.47), "roughness": 0.45, "metallic": 0.2},
        "lamp_step": {"color": (1.0, 0.85, 0.6), "roughness": 0.2, "emission": (1.0, 0.82, 0.55, 8.0)},
        "dish_gold": {"color": (0.78, 0.66, 0.22), "roughness": 0.35, "metallic": 0.7},
        "tank_white": {"color": (0.84, 0.84, 0.82), "roughness": 0.3, "metallic": 0.1},
        "hazard_green": {"color": (0.78, 0.86, 0.38), "roughness": 0.5},
    },
    textures={
        "hull_mdps": ("panel", dict(colour=(0.60, 0.58, 0.53), tile_m=1.1, rough0=0.5, metallic=0.1, fastener_pitch=0.12)),
        "ring_grey": ("panel", dict(colour=(0.36, 0.36, 0.36), tile_m=0.6, rough0=0.5, metallic=0.3, fastener_pitch=0.08)),
        "box_beige": ("panel", dict(colour=(0.60, 0.58, 0.54), tile_m=0.9, rough0=0.5, metallic=0.1, fastener_pitch=0.10)),
        "wheel_plate": ("perforated", dict(colour=(0.20, 0.20, 0.21), tile_m=0.25, hole_d=0.026, pitch=0.05)),
    })

R_HULL = 1.50
XE, XD = 3.275, -3.275
RING_D = 0.28
R_RING_IN = 1.20
ZA = 2.63
R_W, W_W = 0.72, 0.45
XB = 2.00
PAIR = 1.52
TRACK = 3.60
KO = 0.35
PIVOT_Z = 1.00
STEER = (math.radians(-25), math.radians(25))
DOOR_W, DOOR_H, DOOR_R = 1.25, 1.95, 0.38
SILL_Z = ZA - DOOR_H / 2
PORCH_D = 0.90
LADDER_FOOT = (XE + PORCH_D + 0.42, 0.02)
ROOF_Z = ZA + R_HULL
PED_Z = ROOF_Z + 0.42
BLANKET = dict(w=1.80, h=8.0, x=(-1.0, 1.0), z0=PED_Z + 0.30)
RAD = dict(y=0.85, z=ROOF_Z - 0.05, w=1.60, x0=-3.70, x1=3.70, tilt=math.radians(-30))
SIDE_PORT = math.radians(52)


def _wheels():
    out = []
    for b, xb in (("f", XB), ("r", -XB)):
        for k, dx in enumerate((-PAIR / 2, PAIR / 2)):
            x = xb + dx
            corner = (b == "f" and dx > 0) or (b == "r" and dx < 0)
            for sd, s in (("l", 1), ("r", -1)):
                out.append({"name": f"{b}{k}{sd}", "x": x, "y": s * TRACK / 2, "carrier": f"bogie_{b}{sd}",
                            "steer": STEER if corner else None, "suspension": {"kingpin_off": KO, "upper_dz": PIVOT_Z - R_W + 0.10}})
    return out


def _carriers():
    out = []
    for b, xb in (("f", XB), ("r", -XB)):
        for sd, s in (("l", 1), ("r", -1)):
            ky = s * (TRACK / 2 - KO)
            out.append({"name": f"bogie_{b}{sd}", "pos": (xb, ky, PIVOT_Z), "axis": (0, 1, 0), "limit": (-0.30, 0.30),
                        "role": "suspension", "drive": "spring", "stiffness": 2.0e4, "damping": 8.0e3, "mass": 180.0, "beam": 0.16,
                        "mat": "ring_grey", "beams_to": [(xb - PAIR / 2, ky, PIVOT_Z + 0.10), (xb + PAIR / 2, ky, PIVOT_Z + 0.10)]})
    return out


def _hull():
    out = [
        {"kind": "tube", "name": "hull_shell", "p0": (XD + RING_D - 0.02, 0, ZA), "p1": (XE - RING_D + 0.02, 0, ZA), "r": R_HULL - 0.03,
         "sides": 64, "mat": "hull_mdps"},
    ]
    for k, x in enumerate((-1.62, 0.0, 1.62)):
        out.append({"kind": "ring", "name": f"ring_frame_{k}", "c": (x - 0.05, 0, ZA), "n": (1, 0, 0), "r": R_HULL - 0.03, "w": 0.035,
                    "t": 0.10, "sides": 64, "mat": "ring_grey"})
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        out.append({"kind": "tube", "name": f"longeron_{k}", "p0": (XD + RING_D, 1.485 * math.cos(a), ZA + 1.485 * math.sin(a)),
                    "p1": (XE - RING_D, 1.485 * math.cos(a), ZA + 1.485 * math.sin(a)), "r": 0.018, "sides": 8, "mat": "ring_grey"})
    for tag, x0, sgn in (("eva", XE, 1), ("dock", XD, -1)):
        out += [
            {"kind": "ring", "name": f"{tag}_end_ring", "c": (x0 - sgn * RING_D, 0, ZA), "n": (sgn, 0, 0), "r": R_RING_IN, "w": R_HULL + 0.03 - R_RING_IN,
             "t": RING_D, "sides": 64, "mat": "ring_grey"},
            {"kind": "ring", "name": f"{tag}_end_ring_lip", "c": (x0, 0, ZA), "n": (-sgn, 0, 0), "r": R_RING_IN - 0.02, "w": 0.06, "t": 0.04, "sides": 64,
             "mat": "aluminium"},
            {"kind": "lathe", "name": f"{tag}_bulkhead", "c": (x0 - sgn * 0.20, 0, ZA), "n": (sgn, 0, 0), "sides": 64, "mat": "hull_mdps",
             "profile": [(1e-3, 0.06), (0.60, 0.05), (1.00, 0.02), (R_RING_IN + 0.01, -0.06), (R_RING_IN + 0.01, -0.10)]},
        ]
        for k in range(24):
            a = 2 * math.pi * k / 24
            out.append({"kind": "box", "name": f"{tag}_ring_rib_{k}", "c": (x0 - sgn * RING_D / 2, (R_HULL + 0.035) * math.cos(a), ZA + (R_HULL + 0.035) * math.sin(a)),
                        "size": (RING_D - 0.04, 0.05, 0.05), "mat": "anodised_grey"})
    return out


def _rrect(cx, y0, z0, w, h, r, n=5):
    pts = []
    for cy, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx, y0 + cy + r * math.cos(a), z0 + cz + r * math.sin(a)))
    return pts


def _door(tag, sgn, link):
    x = (XE if sgn > 0 else XD) - sgn * 0.13
    hinge_y = -sgn * (DOOR_W / 2 + 0.04)
    out = [
        {"kind": "rail", "name": f"{tag}_door_frame", "r": 0.045, "closed": True, "mat": "aluminium",
         "points": _rrect(x + sgn * 0.01, 0.0, ZA, DOOR_W + 0.10, DOOR_H + 0.10, DOOR_R + 0.05)},
        {"kind": "loft", "name": f"{tag}_doorway", "mat": "anodised_dark", "n": 5, "smooth": False,
         "stations": [(min(x + sgn * 0.005, x + sgn * 0.015), DOOR_W / 2, ZA, DOOR_H / 2, DOOR_R),
                      (max(x + sgn * 0.005, x + sgn * 0.015), DOOR_W / 2, ZA, DOOR_H / 2, DOOR_R)]},
    ]
    for k, z in enumerate((ZA - 0.62, ZA, ZA + 0.62)):
        out.append({"kind": "tube", "name": f"{tag}_door_knuckle_{k}", "p0": (x + sgn * 0.06, hinge_y, z - 0.09), "p1": (x + sgn * 0.06, hinge_y, z + 0.09),
                    "r": 0.035, "mat": "titanium"})
    xd = x + sgn * 0.08
    out += [
        {"kind": "loft", "name": f"{tag}_door_panel", "link": link, "mat": "door_grey", "n": 5, "smooth": False,
         "stations": [(min(xd - sgn * 0.04, xd + sgn * 0.04), DOOR_W / 2, ZA, DOOR_H / 2, DOOR_R),
                      (max(xd - sgn * 0.04, xd + sgn * 0.04), DOOR_W / 2, ZA, DOOR_H / 2, DOOR_R)]},
        {"kind": "rail", "name": f"{tag}_door_rim", "link": link, "r": 0.025, "closed": True, "mat": "white_panel",
         "points": _rrect(xd + sgn * 0.045, 0.0, ZA, DOOR_W - 0.14, DOOR_H - 0.14, DOOR_R - 0.07)},
        {"kind": "disc", "name": f"{tag}_door_window", "link": link, "c": (xd + sgn * 0.04, sgn * 0.22, ZA + 0.42), "n": (sgn, 0, 0), "r": 0.11,
         "t": 0.012, "mat": "glass"},
        {"kind": "ring", "name": f"{tag}_door_window_bezel", "link": link, "c": (xd + sgn * 0.04, sgn * 0.22, ZA + 0.42), "n": (sgn, 0, 0), "r": 0.11,
         "w": 0.03, "t": 0.02, "mat": "aluminium"},
        {"kind": "box", "name": f"{tag}_door_latch", "link": link, "c": (xd + sgn * 0.06, sgn * 0.42, ZA - 0.05), "size": (0.04, 0.06, 0.30), "mat": "orange"},
        {"kind": "rail", "name": f"{tag}_door_handle", "link": link, "r": 0.016, "mat": "yellow",
         "points": [(xd + sgn * 0.04, -sgn * 0.20, ZA - 0.25), (xd + sgn * 0.12, -sgn * 0.20, ZA - 0.22), (xd + sgn * 0.12, -sgn * 0.20, ZA + 0.22),
                    (xd + sgn * 0.04, -sgn * 0.20, ZA + 0.25)]},
    ]
    for s in (-1, 1):
        out.append({"kind": "rail", "name": f"{tag}_grab_{s + 1}", "r": 0.018, "mat": "yellow",
                    "points": [(x + sgn * 0.02, s * (DOOR_W / 2 + 0.22), ZA - 0.55), (x + sgn * 0.12, s * (DOOR_W / 2 + 0.22), ZA - 0.50),
                               (x + sgn * 0.12, s * (DOOR_W / 2 + 0.22), ZA + 0.10), (x + sgn * 0.02, s * (DOOR_W / 2 + 0.22), ZA + 0.15)]})
    return out


def _porch():
    x0, z = XE + 0.01, SILL_Z - 0.04
    out = [
        {"kind": "box", "name": "porch_hinge_bar", "c": (x0, 0, z), "size": (0.08, DOOR_W + 0.20, 0.08), "mat": "ring_grey"},
        {"kind": "box", "name": "porch_deck", "link": "porch", "c": (x0 + PORCH_D / 2, 0, z), "size": (PORCH_D, 1.40, 0.05), "mat": "grating"},
        {"kind": "box", "name": "porch_edge", "link": "porch", "c": (x0 + PORCH_D - 0.03, 0, z - 0.05), "size": (0.06, 1.40, 0.10), "mat": "ring_grey"},
    ]
    for s in (-1, 1):
        out += [
            {"kind": "box", "name": f"porch_side_{s + 1}", "link": "porch", "c": (x0 + PORCH_D / 2, s * 0.69, z - 0.05), "size": (PORCH_D, 0.04, 0.10),
             "mat": "ring_grey"},
            {"kind": "tube", "name": f"porch_stay_{s + 1}", "link": "porch", "p0": (x0 + PORCH_D - 0.06, s * 0.66, z + 0.03),
             "p1": (XE - 0.05, s * 0.95, ZA + 0.75), "r": 0.022, "mat": "aluminium"},
        ]
    return out


def _ladder():
    (xt, zt), (xb, zb) = (XE + PORCH_D - 0.05, SILL_Z - 0.08), LADDER_FOOT
    out = []
    for s in (-1, 1):
        out.append({"kind": "beam", "name": f"ladder_rail_{s + 1}", "link": "ladder", "p0": (xt, s * 0.26, zt), "p1": (xb, s * 0.26, zb), "w": 0.04,
                    "h": 0.06, "mat": "aluminium"})
    for k in range(1, 6):
        t = k / 6
        out.append({"kind": "tube", "name": f"ladder_rung_{k}", "link": "ladder", "p0": (xt + (xb - xt) * t, -0.26, zt + (zb - zt) * t),
                    "p1": (xt + (xb - xt) * t, 0.26, zt + (zb - zt) * t), "r": 0.018, "mat": "titanium"})
    out.append({"kind": "box", "name": "ladder_foot", "link": "ladder", "c": (xb, 0, zb + 0.02), "size": (0.12, 0.62, 0.04), "mat": "ring_grey"})
    return out


def _dock():
    x = XD + 0.11
    out = [
        {"kind": "ring", "name": "dock_ring", "c": (x, 0, ZA), "n": (-1, 0, 0), "r": 1.02, "w": 0.16, "t": 0.12, "sides": 64, "mat": "anodised_dark"},
        {"kind": "ring", "name": "dock_seal", "c": (x - 0.12, 0, ZA), "n": (-1, 0, 0), "r": 1.06, "w": 0.06, "t": 0.015, "sides": 64,
         "mat": "anodised_grey"},
    ]
    for k in range(3):
        a = math.radians(90 + 120 * k)
        out.append({"kind": "obox", "name": f"dock_guide_{k}", "c": (x - 0.20, 1.10 * math.cos(a), ZA + 1.10 * math.sin(a)), "ax": (0, -math.sin(a), math.cos(a)),
                    "ay": (-1, 0, 0), "size": (0.30, 0.16, 0.05), "mat": "aluminium"})
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        out.append({"kind": "box", "name": f"dock_latch_{k}", "c": (x - 0.06, 1.12 * math.cos(a), ZA + 1.12 * math.sin(a)), "size": (0.08, 0.07, 0.07),
                    "mat": "titanium"})
    return out


def _flanks():
    out = []
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        out += [
            {"kind": "cbox", "name": f"battery_{sd}_0", "c": (-2.30, s * 1.62, ZA - 0.42), "size": (0.95, 0.52, 0.72), "r": 0.06, "mat": "box_beige"},
            {"kind": "cbox", "name": f"battery_{sd}_1", "c": (-1.30, s * 1.62, ZA - 0.42), "size": (0.95, 0.52, 0.72), "r": 0.06, "mat": "box_beige"},
            {"kind": "cbox", "name": f"pcu_{sd}", "c": (1.70, s * 1.58, ZA - 0.78), "size": (1.40, 0.50, 0.62), "r": 0.06, "mat": "box_beige"},
            {"kind": "box", "name": f"battery_saddle_{sd}", "c": (-1.80, s * 1.40, ZA - 0.85), "size": (2.10, 0.30, 0.10), "mat": "ring_grey"},
            {"kind": "box", "name": f"pcu_saddle_{sd}", "c": (1.70, s * 1.36, ZA - 1.13), "size": (1.50, 0.30, 0.10), "mat": "ring_grey"},
            {"kind": "rail", "name": f"handrail_{sd}", "r": 0.018, "mat": "yellow",
             "points": [(-0.95, s * 1.36, ZA + 0.66), (-0.95, s * 1.42, ZA + 0.70), (0.95, s * 1.42, ZA + 0.70), (0.95, s * 1.36, ZA + 0.66)]},
        ]
        a = SIDE_PORT
        n = (0, s * math.cos(a), math.sin(a))
        c = (0.10, s * (R_HULL + 0.02) * math.cos(a), ZA + (R_HULL + 0.02) * math.sin(a))
        out += [
            {"kind": "ring", "name": f"berthing_ring_{sd}", "c": c, "n": n, "r": 0.42, "w": 0.10, "t": 0.08, "sides": 48, "mat": "ring_grey"},
            {"kind": "disc", "name": f"berthing_cover_{sd}", "c": c, "n": n, "r": 0.42, "t": 0.05, "sides": 48, "mat": "white_panel"},
            {"kind": "disc", "name": f"berthing_window_{sd}", "c": tuple(c[i] + n[i] * 0.05 for i in range(3)), "n": n, "r": 0.14, "t": 0.01, "sides": 32,
             "mat": "glass"},
        ]
        for k, x in enumerate((-0.35, -0.12, 0.11)):
            out.append({"kind": "box", "name": f"hazard_tag_{sd}_{k}", "c": (x, s * 1.47, ZA - 0.30), "size": (0.20, 0.02, 0.14), "mat": "hazard_green"})
    return out


def _belly():
    out = [
        {"kind": "box", "name": "cradle_keel", "c": (0, 0, ZA - R_HULL - 0.10), "size": (5.80, 1.10, 0.20), "mat": "ring_grey"},
    ]
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        out.append({"kind": "beam", "name": f"cradle_rail_{sd}", "p0": (-2.95, s * 1.15, ZA - 1.10), "p1": (2.95, s * 1.15, ZA - 1.10), "w": 0.14, "h": 0.18,
                    "mat": "ring_grey"})
        for xb in (XB, -XB):
            ky = s * (TRACK / 2 - KO)
            out += [
                {"kind": "beam", "name": f"bogie_hanger_{sd}_{'f' if xb > 0 else 'r'}_0", "p0": (xb - 0.35, s * 1.15, ZA - 1.10),
                 "p1": (xb, ky, PIVOT_Z + 0.08), "w": 0.12, "h": 0.12, "mat": "ring_grey"},
                {"kind": "beam", "name": f"bogie_hanger_{sd}_{'f' if xb > 0 else 'r'}_1", "p0": (xb + 0.35, s * 1.15, ZA - 1.10),
                 "p1": (xb, ky, PIVOT_Z + 0.08), "w": 0.12, "h": 0.12, "mat": "ring_grey"},
            ]
        for k, x in enumerate((-2.40, -0.80, 0.80, 2.40)):
            out.append({"kind": "beam", "name": f"cradle_saddle_{sd}_{k}", "p0": (x, s * 1.15, ZA - 1.10), "p1": (x, s * 0.70, ZA - 1.36), "w": 0.10,
                        "h": 0.10, "mat": "ring_grey"})
    for k, (y, z, rr) in enumerate(((0.42, ZA - 1.50, 0.22), (-0.42, ZA - 1.50, 0.22), (0.0, ZA - 1.62, 0.17))):
        out.append({"kind": "lathe", "name": f"gas_tank_{k}", "c": (-0.90, y, z), "n": (1, 0, 0), "mat": "tank_white", "sides": 32,
                    "profile": [(1e-3, 0.0), (rr * 0.7, 0.02), (rr, rr * 0.5), (rr, 2.10 - rr * 0.5), (rr * 0.7, 2.08), (1e-3, 2.10)]})
        for j, xx in enumerate((-0.55, 0.50)):
            out.append({"kind": "ring", "name": f"gas_tank_{k}_strap_{j}", "c": (xx, y, z), "n": (1, 0, 0), "r": rr, "w": 0.015, "t": 0.05,
                        "mat": "anodised_dark"})
    out.append({"kind": "cbox", "name": "valve_panel", "c": (0.65, 0, ZA - 1.52), "size": (0.60, 0.70, 0.30), "r": 0.04, "mat": "box_beige"})
    return out


def _roof():
    out = [
        {"kind": "cbox", "name": "solar_pedestal", "c": (0, 0, ROOF_Z + 0.16), "size": (1.40, 0.95, 0.52), "r": 0.06, "mat": "box_beige"},
        {"kind": "tube", "name": "solar_yaw_bearing", "p0": (0, 0, ROOF_Z + 0.40), "p1": (0, 0, PED_Z), "r": 0.30, "mat": "anodised_grey"},
        {"kind": "box", "name": "solar_yoke", "link": "solar_yaw", "c": (0, 0, PED_Z + 0.08), "size": (2.40, 0.42, 0.16), "mat": "box_beige"},
    ]
    for k, xc in enumerate(BLANKET["x"]):
        n = f"solar_canister_{k}"
        out += [
            {"kind": "tube", "name": n, "link": "solar_yaw", "p0": (xc - BLANKET["w"] / 2 - 0.05, 0, PED_Z + 0.24),
             "p1": (xc + BLANKET["w"] / 2 + 0.05, 0, PED_Z + 0.24), "r": 0.13, "mat": "canister_navy"},
            {"kind": "disc", "name": f"{n}_cap_0", "link": "solar_yaw", "c": (xc - BLANKET["w"] / 2 - 0.07, 0, PED_Z + 0.24), "n": (1, 0, 0), "r": 0.14,
             "t": 0.03, "mat": "aluminium"},
            {"kind": "disc", "name": f"{n}_cap_1", "link": "solar_yaw", "c": (xc + BLANKET["w"] / 2 + 0.04, 0, PED_Z + 0.24), "n": (1, 0, 0), "r": 0.14,
             "t": 0.03, "mat": "aluminium"},
            {"kind": "panel", "name": f"solar_blanket_{k}", "link": "solar_yaw", "c": (xc, 0, BLANKET["z0"] + BLANKET["h"] / 2), "u": (1, 0, 0),
             "v": (0, 0, 1), "w": BLANKET["w"], "h": BLANKET["h"], "t": 0.012, "normal": (0, -1, 0), "mat": "solar_cells", "back": "beta_white",
             "variant": "Solar:deployed"},
            {"kind": "box", "name": f"solar_spreader_{k}", "link": "solar_yaw", "c": (xc, 0, BLANKET["z0"] + BLANKET["h"] + 0.04),
             "size": (BLANKET["w"] + 0.06, 0.06, 0.08), "mat": "aluminium", "variant": "Solar:deployed"},
        ]
        for j, dx in enumerate((-BLANKET["w"] / 2 - 0.03, BLANKET["w"] / 2 + 0.03)):
            out.append({"kind": "tube", "name": f"solar_boom_{k}_{j}", "link": "solar_yaw", "p0": (xc + dx, 0, PED_Z + 0.24),
                        "p1": (xc + dx, 0, BLANKET["z0"] + BLANKET["h"] + 0.04), "r": 0.03, "mat": "anodised_dark", "variant": "Solar:deployed"})
    return out


def _radiators():
    out = []
    links = []
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        n = f"radiator_wing_{sd}"
        y0, z0 = s * RAD["y"], RAD["z"]
        out.append({"kind": "tube", "name": f"{n}_hinge_tube", "p0": (RAD["x0"] + 0.3, y0, z0), "p1": (RAD["x1"] - 0.3, y0, z0), "r": 0.035,
                    "mat": "titanium"})
        for k, x in enumerate((-2.6, 0.0, 2.6)):
            out.append({"kind": "box", "name": f"{n}_hinge_post_{k}", "c": (x, y0 * 0.98, z0 - 0.10), "size": (0.12, 0.10, 0.22), "mat": "anodised_grey"})
        ca, sa = math.cos(RAD["tilt"]), math.sin(RAD["tilt"])
        u = (0, s * ca, sa)
        L = (RAD["x1"] - RAD["x0"]) / 3
        for k in range(3):
            xc = RAD["x0"] + L * (k + 0.5)
            c = (xc, y0 + s * (RAD["w"] / 2 + 0.06) * ca, z0 + (RAD["w"] / 2 + 0.06) * sa)
            out.append({"kind": "panel", "name": f"{n}_panel_{k}", "link": n, "c": c, "u": (1, 0, 0), "v": u, "w": L - 0.06, "h": RAD["w"], "t": 0.03,
                        "normal": (0, -s * sa, ca), "mat": "radiator_blue", "back": "white_panel"})
        for k in range(4):
            xc = RAD["x0"] + L * k
            out.append({"kind": "beam", "name": f"{n}_rib_{k}", "link": n, "p0": (xc, y0 + s * 0.04 * ca, z0 + 0.04 * sa),
                        "p1": (xc, y0 + s * (RAD["w"] + 0.08) * ca, z0 + (RAD["w"] + 0.08) * sa), "w": 0.04, "h": 0.05, "mat": "aluminium"})
        out.append({"kind": "beam", "name": f"{n}_root_spar", "link": n, "p0": (RAD["x0"], y0 + s * 0.05 * ca, z0 + 0.05 * sa),
                    "p1": (RAD["x1"], y0 + s * 0.05 * ca, z0 + 0.05 * sa), "w": 0.05, "h": 0.05, "mat": "aluminium"})
        links.append({"name": n, "pos": (0, y0, z0), "axis": (s, 0, 0), "limit": (0.0, math.radians(118)), "role": "deploy", "mass": 120.0,
                      "drive": {"kind": "position", "stiffness": 2.0e5, "damping": 2.0e4, "max_force": 1.0e4}})
    return out, links


RAD_PARTS, RAD_LINKS = _radiators()


def _antennas():
    out = []
    for tag, x, s in (("eva", XE - 0.45, -1), ("dock", XD + 0.45, 1)):
        base = (x, s * 0.95, ROOF_Z - 0.32)
        out += [
            {"kind": "tube", "name": f"{tag}_antenna_post", "p0": base, "p1": (x, s * 1.02, ROOF_Z + 0.10), "r": 0.035, "mat": "aluminium"},
            {"kind": "tube", "name": f"{tag}_whip", "p0": (x - s * 0.15, s * 0.75, ROOF_Z - 0.12), "p1": (x - s * 0.15, s * 0.75, ROOF_Z + 0.75), "r": 0.012,
             "mat": "anodised_dark"},
        ]
    out.append({"kind": "lathe", "name": "dock_dish", "c": (XD + 0.45, 1.02, ROOF_Z + 0.12), "n": (-0.4, 0.3, 1), "mat": "dish_gold", "sides": 32,
                "profile": [(1e-3, 0.0), (0.08, 0.008), (0.16, 0.03), (0.22, 0.06), (0.22, 0.075), (1e-3, 0.012)]})
    return out


LINKS_ = [
    *RAD_LINKS,
    {"name": "solar_yaw", "pos": (0, 0, PED_Z), "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "solar", "mass": 260.0,
     "drive": {"kind": "position", "stiffness": 6.0e4, "damping": 6.0e3, "max_force": 3.0e3}},
    {"name": "eva_door", "pos": (XE - 0.07, -(DOOR_W / 2 + 0.04), ZA), "axis": (0, 0, -1), "limit": (0.0, math.radians(110)), "role": "hatch", "mass": 90.0,
     "drive": {"kind": "position", "stiffness": 6000.0, "damping": 600.0, "max_force": 1500.0}},
    {"name": "dock_door", "pos": (XD + 0.07, DOOR_W / 2 + 0.04, ZA), "axis": (0, 0, -1), "limit": (0.0, math.radians(110)), "role": "hatch",
     "mass": 90.0, "drive": {"kind": "position", "stiffness": 6000.0, "damping": 600.0, "max_force": 1500.0}},
    {"name": "porch", "pos": (XE + 0.01, 0, SILL_Z - 0.04), "axis": (0, 1, 0), "limit": (0.0, math.radians(92)), "role": "stair", "mass": 35.0,
     "drive": {"kind": "position", "stiffness": 8000.0, "damping": 800.0, "max_force": 4000.0}},
    {"name": "ladder", "parent": "porch", "pos": (XE + PORCH_D - 0.05, 0, SILL_Z - 0.08), "axis": (0, 1, 0), "limit": (0.0, math.radians(105)),
     "role": "stair", "mass": 15.0, "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 1500.0}},
]

ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "band", "bands": 2, "band_gap": 0.05, "grousers": 40, "chevron": False, "grouser_h": 0.03, "hub_w": 0.26,
              "drum_mat": "wheel_plate", "grouser_mat": "anodised_dark", "flange": (0.05, "aluminium"), "wire_spokes": (64, 0.005, 0.0),
              "hub_frac": 0.35, "hub_mat": "aluminium", "hub_centre_mat": "titanium", "motor_mat": "anodised_dark", "spoke_mat": "titanium",
              "mass": 80.0, "segments": 72},
    "carriers": _carriers(),
    "wheels": _wheels(),
    "suspension": {"type": "carrier", "knuckle_mat": "ring_grey", "knuckle_t": 0.12},
    "links": LINKS_,
    "parts": [*_hull(), *_door("eva", 1, "eva_door"), *_door("dock", -1, "dock_door"), *_porch(), *_ladder(), *_dock(), *_flanks(), *_belly(),
              *_roof(), *RAD_PARTS, *_antennas()],
    "hga": {"base": (XE - 0.45, -1.02, ROOF_Z + 0.10), "h": 0.25, "r": 0.28, "boresight": (0.5, -0.3, 1), "band": "S/Ka", "front": "dish_gold",
            "back": "dish_gold", "depth": 0.25, "mass": 8.0},
    "lights": [
        ((XE - 0.02, 0.95, ZA + 1.00), (1, -0.2, -0.6), 0.09, "eva_flood_l"),
        ((XE - 0.02, -0.95, ZA + 1.00), (1, 0.2, -0.6), 0.09, "eva_flood_r"),
        ((XD + 0.02, 0.95, ZA + 1.00), (-1, -0.2, -0.6), 0.09, "dock_flood_l"),
        ((XD + 0.02, -0.95, ZA + 1.00), (-1, 0.2, -0.6), 0.09, "dock_flood_r"),
        ((0.0, 1.47, ZA + 0.20), (0, 1, -0.5), 0.08, "flank_light_l"),
        ((0.0, -1.47, ZA + 0.20), (0, -1, -0.5), 0.08, "flank_light_r"),
        ((XE + 0.02, 0.0, SILL_Z - 0.20), (1, 0, -0.8), 0.06, "porch_light"),
    ],
    "sites": [
        ("eva_door", "eva_door", (XE + 0.02, 0, ZA), (1, 0, 0), "hatch", "EVA door (1.25 x 1.95 m) into the 14 m3 airlock; +Z points out"),
        ("eva_sill", "chassis", (XE - 0.05, 0, SILL_Z), (0, 0, 1), "crew", "EVA door sill"),
        ("porch_deck", "porch", (XE + PORCH_D / 2, 0, SILL_Z), (0, 0, 1), "crew", "Fold-down porch deck (1.4 x 0.9 m)"),
        ("ladder_foot", "ladder", (LADDER_FOOT[0], 0, LADDER_FOOT[1]), (0, 0, -1), "contact", "Ladder foot (deployed)"),
        ("docking_port", "chassis", (XD - 0.02, 0, ZA), (-1, 0, 0), "docking",
         "Surface docking interface on the docking bulkhead (ring 2.4 m OD) for a shirtsleeve path to the pressurised rover; standard not published"),
        ("dock_door", "dock_door", (XD - 0.02, 0, ZA), (-1, 0, 0), "hatch", "Docking-end door, doubles as the contingency exit"),
        ("berthing_port_l", "chassis", (0.10, (R_HULL + 0.08) * math.cos(SIDE_PORT), ZA + (R_HULL + 0.08) * math.sin(SIDE_PORT)),
         (0, math.cos(SIDE_PORT), math.sin(SIDE_PORT)), "docking", "Flank berthing hatch for logistics and growth elements (position estimated)"),
        ("berthing_port_r", "chassis", (0.10, -(R_HULL + 0.08) * math.cos(SIDE_PORT), ZA + (R_HULL + 0.08) * math.sin(SIDE_PORT)),
         (0, -math.cos(SIDE_PORT), math.sin(SIDE_PORT)), "docking", "Flank berthing hatch (position estimated)"),
        ("power_port", "chassis", (XD + 0.10, -1.10, ZA - 0.90), (-1, 0, 0), "power", "Bi-directional surface power umbilical (position estimated)"),
        ("o2_n2_fill", "chassis", (0.95, 0, ZA - 1.52), (1, 0, 0), "fluid", "External O2 / N2 tank service panel"),
        *[(f"lift_point_{k}", "chassis", (x, s * 1.18, ZA - 1.00), (0, 0, 1), "hitch", "Offloading lift point on the cradle rail (estimated)")
          for k, (x, s) in enumerate(((2.60, 1), (2.60, -1), (-2.60, 1), (-2.60, -1)))],
        *[(f"blanket_{k}_normal", "solar_yaw", (xc, -0.05, BLANKET["z0"] + BLANKET["h"] / 2), (0, -1, 0), "power",
           "Vertical roll-out solar blanket (1.8 x 8 m); +Z = cell normal", {"area_m2": BLANKET["w"] * BLANKET["h"]})
          for k, xc in enumerate(BLANKET["x"])],
        ("cabin_centre", "chassis", (0.0, 0, ZA), (0, 0, 1), "reference", "Pressure hull centre"),
    ],
    "imu": (0, 0, ZA - 1.0),
}

MASS = {
    "launch": {"mass": 14000.0, "com_z": 2.35, "source": "ASI / TAS ICES-2025-60: maximum mass 14,000 kg at launch"},
    "heavy": {"mass": 15000.0, "com_z": 2.35, "source": "Press (Thales programme manager, 2024): around 15 t"},
}
DEFAULT_MASS_STATE = "launch"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (6.5, 3.0, 3.0)
GEOMETRY_VARIANTS = {"Solar": ["deployed", "stowed"]}
GEOMETRY_VARIANT_JOINTS = {"Solar": {"stowed": {"radiator_wing_l": math.radians(115), "radiator_wing_r": math.radians(115)}}}

SEMANTIC_CLASS = ["lunar_habitat", "surface_habitat", "vehicle"]
ROBOT_TYPE = "Wheeled"
URDF = True
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("hull_mdps", "ring_grey"))
SIMPLE_TRIS = 40000
RENDER_VIEWS = {
    **K.views(6.9, 4.0, 4.6, centre_z=2.4),
    "eva_end": ((12.5, -5.5, 3.2), (3.2, 0, 2.2), 35),
    "dock_end": ((-12.0, 5.0, 3.4), (-3.2, 0, 2.5), 35),
    "solar_wide": ((15.5, -12.5, 5.0), (0.0, 0.0, 5.6), 35),
    "ices_front": ((16.2, 13.6, 13.6), (0.0, 0.0, 2.3), 55),
    "ices_rear": ((-16.2, -13.6, 13.6), (0.0, 0.0, 2.3), 55),
}
