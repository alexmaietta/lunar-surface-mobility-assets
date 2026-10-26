import math

import rover_kit as K

ASSET_ID = "lunar_cruiser"
ASSET_PATH = "toyota_jaxa/lunar_cruiser/rover"
FAMILY = "rover"
TITLE = "JAXA / Toyota Lunar Cruiser"
DOC = ("JAXA / Toyota Lunar Cruiser pressurised rover, 2025 design (JAXA: 6.44 x 4.84 x 4.85 m, wheelbase 3.81 m, "
       "track 3.20 m, 15 t at launch, up to 18 t loaded): a white faceted cab with a two-row bronze windscreen, six "
       "brow lamp pods and a LiDAR visor, a grey radiator mid-body with an arched ribbed roof spine, a grey airlock "
       "module, grey sponsons over gunmetal skirts with angular wheel arches, and six 1.18 m metal-slat wheels with "
       "in-wheel motors on independent double-wishbone suspension (front axle steers). The two stowed solar-wing "
       "boxes swing out 90 deg on hinge joints; the Solar=deployed variant raises the 4 x 10 m wings. The rear patio "
       "has a hinged walk-in airlock hatch with a hand-wheel latch joint, a grated porch, a fold-down stair joint, "
       "handrails, an arched light bar, stowage boxes, gas bottles, a fuel-cell tank row and a stowed robotic arm.")

TEXTURE_SETS, MATERIALS = K.materials(
    overrides={
        "solar_copper": {"set": "solar_copper", "normal": 0.3},
        "gunmetal": {"set": "gunmetal", "normal": 0.6},
        "glass_bronze": {"color": (0.42, 0.28, 0.10), "roughness": 0.06, "metallic": 0.5},
        "orange": {"color": (0.85, 0.35, 0.05), "roughness": 0.4},
        "lamp_step": {"color": (1.0, 0.85, 0.6), "roughness": 0.2, "emission": (1.0, 0.82, 0.55, 8.0)},
        "frame_white": {"color": (0.88, 0.88, 0.86), "roughness": 0.35},
    },
    textures={
        "solar_copper": ("solar_cells", dict(tile_m=0.32, cell_colour=(0.10, 0.04, 0.02), backing=(0.70, 0.36, 0.18))),
        "gunmetal": ("panel", dict(colour=(0.16, 0.165, 0.17), tile_m=0.8, rough0=0.45, metallic=0.6, fastener_pitch=0.08)),
        "white_panel": ("panel", dict(colour=(0.88, 0.88, 0.87), tile_m=1.2, rough0=0.35, fastener_pitch=0.10)),
        "grey_panel": ("panel", dict(colour=(0.52, 0.53, 0.54), tile_m=0.9, rough0=0.45, metallic=0.2, fastener_pitch=0.09)),
    })

R_W, W_W = 0.59, 0.58
AXLES = (1.905, 0.0, -1.905)
TRACK = 3.20
XF, XR = 2.75, -3.10
PORCH = (-3.60, 1.05)
STAIR_FOOT = (-4.60, 0.02)
KNEE = (-4.10, 0.52)
STEPS = (0.75, 0.45, 0.15)
HATCH_Z = 2.12
HINGE_Y = -0.55
WING_PIN = (2.20, 2.30, 1.85)


def _body():
    return [
        {"kind": "loft", "name": "cab", "mat": "white_panel", "n": 4, "smooth": False,
         "stations": [(1.45, 1.90, 2.65, 1.15, 0.30), (2.20, 1.90, 2.65, 1.15, 0.45), (2.55, 1.85, 2.55, 1.05, 0.55),
                      (XF, 1.70, 2.45, 0.95, 0.45)]},
        {"kind": "loft", "name": "radiator_body", "mat": "grey_panel", "n": 3, "smooth": False,
         "stations": [(-0.90, 1.70, 3.00, 0.80, 0.35), (1.46, 1.75, 3.00, 0.80, 0.35)]},
        {"kind": "cbox", "name": "airlock_module", "c": ((XR - 0.90) / 2, 0, 2.875), "size": (-0.90 - XR, 3.30, 1.75), "r": 0.25,
         "mat": "grey_panel"},
        {"kind": "box", "name": "rear_bulkhead", "c": (XR + 0.15, 0, 1.55), "size": (0.30, 3.10, 1.00), "mat": "gunmetal"},
        {"kind": "box", "name": "upper_chassis", "c": (-0.15, 0, 1.82), "size": (5.60, 3.10, 0.75), "mat": "gunmetal"},
        {"kind": "box", "name": "keel", "c": (-0.15, 0, 0.78), "size": (5.40, 1.00, 0.56), "mat": "gunmetal"},
        {"kind": "box", "name": "spine", "c": (0.25, 0, 3.86), "size": (2.40, 0.40, 0.12), "mat": "grey_panel"},
        *[{"kind": "rail", "name": f"roof_rib_{k}", "r": 0.03, "mat": "grey_panel",
           "points": [(x, -1.60, 3.66), (x, -0.90, 3.84), (x, 0.0, 3.90), (x, 0.90, 3.84), (x, 1.60, 3.66)]}
          for k, x in enumerate((1.25, 0.75, 0.25, -0.25, -0.75))],
    ]


def _front():
    out = []
    for k, (z0, z1, w) in enumerate(((2.48, 2.92, 3.04), (2.00, 2.40, 2.83))):
        zc = (z0 + z1) / 2
        out.append({"kind": "panel", "name": f"windscreen_{k}", "c": (XF + 0.012, 0, zc), "u": (0, 1, 0), "v": (0, 0, 1), "w": w - 0.5,
                    "h": z1 - z0, "t": 0.02, "normal": (1, 0, 0), "mat": "glass_bronze", "back": "anodised_dark"})
        out.append({"kind": "box", "name": f"windscreen_{k}_bar", "c": (XF + 0.03, 0, zc), "size": (0.03, 0.08, z1 - z0 + 0.04),
                    "mat": "frame_white"})
        for s in (-1, 1):
            a = math.radians(35)
            y = s * ((w - 0.5) / 2 + 0.22 * math.cos(a))
            out.append({"kind": "panel", "name": f"windscreen_{k}_wrap_{s + 1}", "c": (XF - 0.13, y, zc), "u": (-math.sin(a), s * math.cos(a), 0),
                        "v": (0, 0, 1), "w": 0.44, "h": z1 - z0, "t": 0.02, "normal": (math.cos(a), s * math.sin(a), 0), "mat": "glass_bronze",
                        "back": "anodised_dark"})
    for z in (1.96, 2.44, 2.96):
        out.append({"kind": "box", "name": f"windscreen_frame_{int(z * 100)}", "c": (XF + 0.03, 0, z), "size": (0.03, 2.60, 0.08),
                    "mat": "frame_white"})
    out += [
        {"kind": "box", "name": "lidar_visor", "c": (2.52, 0, 3.635), "size": (0.10, 1.13, 0.19), "mat": "glass"},
        {"kind": "box", "name": "bumper_bar", "c": (XF + 0.06, 0, 1.575), "size": (0.20, 1.56, 0.35), "mat": "gunmetal"},
        {"kind": "box", "name": "bumper_plate", "c": (XF + 0.165, 0, 1.62), "size": (0.01, 0.80, 0.11), "mat": "anodised_dark"},
        {"kind": "box", "name": "armour_panel_l", "c": (XF - 0.05, 0.40, 0.90), "size": (0.25, 0.76, 1.00), "mat": "gunmetal"},
        {"kind": "box", "name": "armour_panel_r", "c": (XF - 0.05, -0.40, 0.90), "size": (0.25, 0.76, 1.00), "mat": "gunmetal"},
        {"kind": "box", "name": "cab_corner_l", "c": (XF - 0.10, 1.25, 1.55), "size": (0.30, 0.65, 0.45), "mat": "gunmetal"},
        {"kind": "box", "name": "cab_corner_r", "c": (XF - 0.10, -1.25, 1.55), "size": (0.30, 0.65, 0.45), "mat": "gunmetal"},
        {"kind": "tube", "name": "tow_stub_l", "p0": (XF - 0.10, 1.10, 0.50), "p1": (XF + 0.12, 1.10, 0.50), "r": 0.06, "mat": "titanium"},
        {"kind": "tube", "name": "tow_stub_r", "p0": (XF - 0.10, -1.10, 0.50), "p1": (XF + 0.12, -1.10, 0.50), "r": 0.06, "mat": "titanium"},
        {"kind": "box", "name": "side_marker_l", "c": (2.60, 1.58, 1.60), "size": (0.15, 0.02, 0.08), "mat": "beacon"},
        {"kind": "box", "name": "side_marker_r", "c": (2.60, -1.58, 1.60), "size": (0.15, 0.02, 0.08), "mat": "beacon"},
    ]
    return out


def _roof():
    return [
        {"kind": "box", "name": "dish_base", "c": (2.10, 0, 3.86), "size": (0.45, 0.35, 0.16), "mat": "white_panel"},
        {"kind": "tube", "name": "whip_l", "p0": (2.20, 1.45, 3.55), "p1": (2.20, 1.45, 4.20), "r": 0.03, "mat": "anodised_dark"},
        {"kind": "tube", "name": "whip_r", "p0": (2.00, -1.75, 3.55), "p1": (2.00, -1.75, 4.20), "r": 0.03, "mat": "anodised_dark"},
        {"kind": "tube", "name": "sensor_post", "p0": (1.60, -1.80, 3.60), "p1": (1.60, -1.80, 4.40), "r": 0.05, "mat": "anodised_dark"},
        {"kind": "tube", "name": "roof_stack_0", "p0": (-2.00, 1.20, 3.70), "p1": (-2.00, 1.20, 4.40), "r": 0.15, "mat": "white_panel"},
        {"kind": "tube", "name": "roof_stack_1", "p0": (-0.80, -1.30, 3.70), "p1": (-0.80, -1.30, 4.20), "r": 0.075, "mat": "white_panel"},
    ]


def _sides():
    out = []
    for s in (-1, 1):
        sd = "l" if s > 0 else "r"
        out += [
            {"kind": "cbox", "name": f"sponson_{sd}", "c": (-0.25, s * 1.90, 1.825), "size": (5.10, 0.60, 0.75), "r": 0.05, "mat": "grey_panel"},
            {"kind": "box", "name": f"wing_hinge_block_{sd}", "c": (2.15, s * 2.25, 1.965), "size": (0.60, 0.30, 0.43), "mat": "white_panel"},
            {"kind": "tube", "name": f"wing_hinge_pin_{sd}", "p0": (WING_PIN[0], s * WING_PIN[1], 1.70), "p1": (WING_PIN[0], s * WING_PIN[1], 2.22),
             "r": 0.04, "mat": "titanium"},
        ]
        arches = [x for x in AXLES]
        xs = [2.30] + [v for x in arches for v in (x + 0.78, x - 0.78)] + [-2.80]
        for k in range(0, len(xs), 2):
            x0, x1 = xs[k], xs[k + 1]
            top0 = x0 if k == 0 else x0 + 0.16
            top1 = x1 if k == len(xs) - 2 else x1 - 0.16
            prof = [(x1, 0.95), (x0, 0.95), (top0, 1.45), (top1, 1.45)]
            if x0 - x1 > 0.05:
                y0, y1 = sorted((s * 2.12, s * 2.18))
                out.append({"kind": "extrude", "name": f"skirt_{sd}_{k // 2}", "profile": prof, "y": (y0, y1), "mat": "gunmetal"})
    return out


def _wing(s):
    sd = "l" if s > 0 else "r"
    link = f"solar_wing_{sd}"
    px, py, pz = WING_PIN
    y = s * 2.30
    out = [
        {"kind": "box", "name": f"{link}_box", "link": link, "c": (-0.665, y, 1.845), "size": (4.13, 0.24, 0.63), "mat": "grey_panel"},
        {"kind": "box", "name": f"{link}_arm", "link": link, "c": (1.80, y, 1.845), "size": (0.80, 0.16, 0.30), "mat": "white_panel"},
        {"kind": "panel", "name": f"{link}_cells", "link": link, "c": (-0.665, s * 2.425, 1.845), "u": (1, 0, 0), "v": (0, 0, 1), "w": 4.05,
         "h": 0.58, "t": 0.01, "normal": (0, s, 0), "mat": "solar_copper", "back": "grey_panel"},
        {"kind": "tube", "name": f"{link}_boom_0", "link": link, "p0": (1.30, y, 2.16), "p1": (1.30, y, 12.40), "r": 0.04, "mat": "anodised_dark",
         "variant": "Solar:deployed"},
        {"kind": "tube", "name": f"{link}_boom_1", "link": link, "p0": (-2.70, y, 2.16), "p1": (-2.70, y, 12.40), "r": 0.04, "mat": "anodised_dark",
         "variant": "Solar:deployed"},
        {"kind": "tube", "name": f"{link}_top_bar", "link": link, "p0": (1.30, y, 12.40), "p1": (-2.70, y, 12.40), "r": 0.035,
         "mat": "anodised_dark", "variant": "Solar:deployed"},
        {"kind": "panel", "name": f"{link}_blanket", "link": link, "c": (-0.70, y, 7.30), "u": (1, 0, 0), "v": (0, 0, 1), "w": 3.95, "h": 10.10,
         "t": 0.012, "normal": (0, s, 0), "mat": "solar_copper", "back": "beta_white", "variant": "Solar:deployed"},
    ]
    return out


BOLTS = (("latch_bolt_upper", (0.0, 0.44, 0.45), (0, -1, 0), (0.03, 0.28, 0.06)),
         ("latch_bolt_lower", (0.0, 0.44, -0.45), (0, -1, 0), (0.03, 0.28, 0.06)),
         ("latch_bolt_top", (0.0, 0.0, 0.69), (0, 0, -1), (0.03, 0.06, 0.28)),
         ("latch_bolt_bottom", (0.0, 0.0, -0.69), (0, 0, 1), (0.03, 0.06, 0.28)))
BOLT_X = XR - 0.285
BOLT_TRAVEL = 0.10
BOLT_LINKS = [{"name": n, "parent": "airlock_hatch", "type": "prismatic", "pos": (BOLT_X, c[1], HATCH_Z + c[2]), "axis": ax,
               "limit": (0.0, BOLT_TRAVEL), "role": "latch", "mass": 0.6,
               "drive": {"kind": "position", "stiffness": 3000.0, "damping": 300.0, "max_force": 300.0}} for n, c, ax, _ in BOLTS]


def _bolt_parts():
    out = []
    for n, c, ax, size in BOLTS:
        p = (BOLT_X, c[1], HATCH_Z + c[2])
        out.append({"kind": "box", "name": f"{n}_bar", "link": n, "c": p, "size": size, "mat": "titanium"})
        out.append({"kind": "box", "name": f"{n}_tip", "link": n, "c": tuple(p[i] - ax[i] * (max(size[1:]) / 2 - 0.02) for i in range(3)),
                    "size": (0.035, 0.07, 0.07), "mat": "orange"})
        for k, f in enumerate((0.2, -0.25)):
            g = tuple(p[i] - ax[i] * f * max(size[1:]) for i in range(3))
            out.append({"kind": "box", "name": f"{n}_guide_{k}", "link": "airlock_hatch", "c": (g[0] - 0.022, g[1], g[2]),
                        "size": (0.015, 0.03, 0.10) if ax[1] else (0.015, 0.10, 0.03), "mat": "gunmetal"})
    return out


def _airlock():
    x = XR - 0.02
    out = [
        {"kind": "box", "name": "airlock_recess", "c": (x + 0.005, 0, HATCH_Z), "size": (0.02, 1.15, 1.65), "mat": "anodised_dark"},
        {"kind": "box", "name": "airlock_frame_top", "c": (x - 0.075, 0, HATCH_Z + 0.95), "size": (0.15, 1.60, 0.30), "mat": "gunmetal"},
        {"kind": "box", "name": "airlock_frame_sill", "c": (x - 0.075, 0, HATCH_Z - 0.95), "size": (0.15, 1.60, 0.30), "mat": "gunmetal"},
        {"kind": "box", "name": "airlock_frame_l", "c": (x - 0.075, 0.65, HATCH_Z), "size": (0.15, 0.30, 2.20), "mat": "gunmetal"},
        {"kind": "box", "name": "airlock_frame_r", "c": (x - 0.075, -0.65, HATCH_Z), "size": (0.15, 0.30, 2.20), "mat": "gunmetal"},
        {"kind": "rail", "name": "airlock_seal", "r": 0.012, "mat": "orange", "closed": True,
         "points": [(x - 0.155, y, z) for y, z in ((0.52, HATCH_Z - 0.78), (0.52, HATCH_Z + 0.78), (-0.52, HATCH_Z + 0.78), (-0.52, HATCH_Z - 0.78))]},
        {"kind": "tube", "name": "grab_rail", "p0": (x - 0.12, 0.85, HATCH_Z - 0.55), "p1": (x - 0.12, 0.85, HATCH_Z + 0.55), "r": 0.02,
         "mat": "yellow"},
        {"kind": "box", "name": "grab_rail_foot_0", "c": (x - 0.06, 0.85, HATCH_Z - 0.55), "size": (0.12, 0.05, 0.05), "mat": "yellow"},
        {"kind": "box", "name": "grab_rail_foot_1", "c": (x - 0.06, 0.85, HATCH_Z + 0.55), "size": (0.12, 0.05, 0.05), "mat": "yellow"},
    ]
    lugs = [(y, HATCH_Z + dz) for y in (-0.62, 0.62) for dz in (-0.60, -0.20, 0.20, 0.60)] + \
           [(dy, HATCH_Z + s * 0.92) for s in (-1, 1) for dy in (-0.25, 0.25)]
    for k, (y, z) in enumerate(lugs):
        out.append({"kind": "box", "name": f"latch_lug_{k}", "c": (x - 0.17, y, z), "size": (0.04, 0.10 if abs(y) > 0.5 else 0.12,
                    0.12 if abs(y) > 0.5 else 0.08), "mat": "titanium"})
    for k, z in enumerate((HATCH_Z - 0.55, HATCH_Z, HATCH_Z + 0.55)):
        out.append({"kind": "tube", "name": f"hinge_knuckle_{k}", "p0": (x - 0.20, HINGE_Y - 0.03, z - 0.08),
                    "p1": (x - 0.20, HINGE_Y - 0.03, z + 0.08), "r": 0.035, "mat": "titanium"})
    d, xd = "airlock_hatch", x - 0.21
    out += [
        {"kind": "box", "name": "hatch_panel", "link": d, "c": (xd, 0, HATCH_Z), "size": (0.08, 1.02, 1.50), "mat": "grey_panel"},
        {"kind": "box", "name": "hatch_stiffener_h", "link": d, "c": (xd - 0.05, 0, HATCH_Z), "size": (0.03, 0.90, 0.05), "mat": "grey_panel"},
        {"kind": "box", "name": "hatch_stiffener_v", "link": d, "c": (xd - 0.05, 0, HATCH_Z), "size": (0.03, 0.05, 1.38), "mat": "grey_panel"},
        {"kind": "rail", "name": "hatch_rim", "link": d, "r": 0.02, "mat": "white_panel", "closed": True,
         "points": [(xd - 0.05, y, z) for y, z in ((0.46, HATCH_Z - 0.70), (0.46, HATCH_Z + 0.70), (-0.46, HATCH_Z + 0.70), (-0.46, HATCH_Z - 0.70))]},
        {"kind": "ring", "name": "hatch_wheel_pocket", "link": d, "c": (xd - 0.045, 0, HATCH_Z), "n": (-1, 0, 0), "r": 0.19, "w": 0.04,
         "t": 0.015, "mat": "orange"},
    ]
    for k, z in enumerate((HATCH_Z - 0.55, HATCH_Z, HATCH_Z + 0.55)):
        out.append({"kind": "box", "name": f"hatch_hinge_leaf_{k}", "link": d, "c": (xd, HINGE_Y + 0.02, z + 0.11), "size": (0.06, 0.12, 0.06),
                    "mat": "titanium"})
    out += _bolt_parts()
    w, xw = "airlock_handwheel", xd - 0.10
    out += [
        {"kind": "ring", "name": "handwheel_rim", "link": w, "c": (xw, 0, HATCH_Z), "n": (-1, 0, 0), "r": 0.15, "w": 0.025, "t": 0.025,
         "mat": "orange"},
        {"kind": "tube", "name": "handwheel_hub", "link": w, "p0": (xw + 0.06, 0, HATCH_Z), "p1": (xw - 0.02, 0, HATCH_Z), "r": 0.04,
         "mat": "titanium"},
        {"kind": "tube", "name": "handwheel_knob", "link": w, "p0": (xw, 0.15, HATCH_Z), "p1": (xw - 0.08, 0.15, HATCH_Z), "r": 0.018,
         "mat": "orange"},
    ]
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        out.append({"kind": "tube", "name": f"handwheel_spoke_{k}", "link": w, "p0": (xw, 0, HATCH_Z),
                    "p1": (xw, 0.155 * math.cos(a), HATCH_Z + 0.155 * math.sin(a)), "r": 0.012, "mat": "orange"})
    return out


def _patio():
    px, pz = PORCH
    out = [
        {"kind": "box", "name": "porch_deck", "c": ((XR + px) / 2, 0, pz - 0.025), "size": (XR - px, 1.80, 0.05), "mat": "grating"},
        {"kind": "box", "name": "porch_edge", "c": (px + 0.03, 0, pz - 0.06), "size": (0.06, 1.80, 0.10), "mat": "gunmetal"},
        {"kind": "box", "name": "fuel_cell_housing", "c": (XR - 0.30, 0, 0.525), "size": (0.60, 1.60, 0.45), "mat": "gunmetal"},
    ]
    for k, y in enumerate((-0.60, -0.20, 0.20, 0.60)):
        out.append({"kind": "tube", "name": f"fc_tank_end_{k}", "p0": (XR - 0.58, y, 0.525), "p1": (XR - 0.66, y, 0.525), "r": 0.15,
                    "mat": "aluminium"})
    for s in (-1, 1):
        out += [
            {"kind": "beam", "name": f"porch_strut_{s + 1}", "p0": (XR, s * 0.80, 0.80), "p1": (px + 0.05, s * 0.85, pz - 0.08), "w": 0.07,
             "h": 0.07, "mat": "gunmetal"},
            {"kind": "rail", "name": f"porch_rail_{s + 1}", "r": 0.022, "mat": "aluminium",
             "points": [(XR - 0.05, s * 0.88, pz), (XR - 0.05, s * 0.88, pz + 1.0), (px + 0.04, s * 0.88, pz + 1.0), (px + 0.04, s * 0.88, pz)]},
            {"kind": "tube", "name": f"porch_midrail_{s + 1}", "p0": (XR - 0.05, s * 0.88, pz + 0.5), "p1": (px + 0.04, s * 0.88, pz + 0.5),
             "r": 0.016, "mat": "aluminium"},
        ]
    for k, z in enumerate((1.40, 1.90, 2.40)):
        out.append({"kind": "cbox", "name": f"stowage_box_{k}", "c": (XR - 0.225, 1.40, z), "size": (0.45, 0.70, 0.48), "r": 0.03,
                    "mat": "gunmetal"})
        out.append({"kind": "box", "name": f"stowage_box_{k}_latch", "c": (XR - 0.455, 1.40, z + 0.12), "size": (0.02, 0.16, 0.05),
                    "mat": "titanium"})
    out.append({"kind": "box", "name": "ribbed_strip", "c": (XR - 0.03, 0.98, 2.0), "size": (0.06, 0.08, 1.60), "mat": "grey_panel"})
    for k in range(12):
        out.append({"kind": "box", "name": f"ribbed_strip_rib_{k}", "c": (XR - 0.07, 0.98, 1.30 + 0.13 * k), "size": (0.03, 0.10, 0.03),
                    "mat": "anodised_grey"})
    for s in (-1, 1):
        for k, y in enumerate((1.20, 1.55)):
            out.append({"kind": "disc", "name": f"tank_end_{s + 1}_{k}", "c": (XR - 0.01, s * y, 3.025), "n": (-1, 0, 0), "r": 0.14, "t": 0.06,
                        "mat": "aluminium"})
    out += [
        {"kind": "lathe", "name": "gas_bottle", "c": (XR - 0.18, -1.20, 1.20), "n": (0, 0, 1), "mat": "aluminium",
         "profile": [(1e-3, 0.0), (0.09, 0.0), (0.125, 0.07), (0.125, 1.12), (0.09, 1.20), (0.035, 1.22), (0.035, 1.27), (1e-3, 1.27)]},
        *[{"kind": "ring", "name": f"gas_bottle_strap_{k}", "c": (XR - 0.18, -1.20, z), "n": (0, 0, 1), "r": 0.125, "w": 0.015, "t": 0.04,
           "mat": "anodised_dark"} for k, z in enumerate((1.55, 2.10))],
        {"kind": "cbox", "name": "canister", "c": (XR - 0.225, -1.70, 1.80), "size": (0.45, 0.55, 1.20), "r": 0.06, "mat": "aluminium"},
        {"kind": "rail", "name": "canister_handle", "r": 0.015, "mat": "titanium",
         "points": [(XR - 0.45, -1.85, 2.15), (XR - 0.52, -1.85, 2.18), (XR - 0.52, -1.55, 2.18), (XR - 0.45, -1.55, 2.15)]},
        {"kind": "rail", "name": "rear_light_bar", "r": 0.06, "mat": "lamp",
         "points": [(XR - 0.06, y, 3.58 + 0.10 * (1 - (y / 1.4) ** 2)) for y in [-1.4 + 0.28 * k for k in range(11)]]},
        {"kind": "rail", "name": "rear_light_bar_housing", "r": 0.085, "mat": "gunmetal",
         "points": [(XR - 0.01, y, 3.58 + 0.10 * (1 - (y / 1.4) ** 2)) for y in [-1.45 + 0.29 * k for k in range(11)]]},
        *[{"kind": "box", "name": f"rear_corner_lamp_{s + 1}", "c": (XR - 0.04, s * 1.60, 3.60), "size": (0.06, 0.30, 0.15), "mat": "lamp"}
          for s in (-1, 1)],
    ]
    return out


def _stair():
    (x0, z0), (x1, z1) = (PORCH[0], PORCH[1] - 0.03), STAIR_FOOT
    xk, zk = KNEE
    out = []
    for link, (a, b), yy in (("rear_stair", ((x0, z0), (xk, zk)), 0.62), ("rear_stair_lower", ((xk, zk), (x1, z1)), 0.57)):
        (ax, az), (bx, bz) = a, b
        for s in (-1, 1):
            y = s * yy
            out += [
                {"kind": "beam", "name": f"{link}_stringer_{s + 1}", "link": link, "p0": (ax, y, az), "p1": (bx, y, bz), "w": 0.05, "h": 0.12,
                 "mat": "gunmetal"},
                {"kind": "beam", "name": f"{link}_scissor_{s + 1}_0", "link": link, "p0": (ax - 0.04, y + s * 0.035, az - 0.10),
                 "p1": (bx + 0.10, y + s * 0.035, bz + 0.12), "w": 0.025, "h": 0.04, "mat": "aluminium"},
                {"kind": "beam", "name": f"{link}_scissor_{s + 1}_1", "link": link, "p0": (ax - 0.10, y + s * 0.035, az + 0.08),
                 "p1": (bx + 0.04, y + s * 0.035, bz - 0.10), "w": 0.025, "h": 0.04, "mat": "aluminium"},
            ]
        out.append({"kind": "tube", "name": f"{link}_knee_pin", "link": link, "p0": (bx if link == "rear_stair" else ax, -yy - 0.04, bz if link == "rear_stair" else az),
                    "p1": (bx if link == "rear_stair" else ax, yy + 0.04, bz if link == "rear_stair" else az), "r": 0.02, "mat": "titanium"})
    for rl in RAILINGS:
        n, h0, h1, nrm, L = rl["name"], rl["h0"], rl["h1"], rl["n"], rl["len"]
        t0, t1 = [tuple(h0[i] + (h1[i] - h0[i]) * f + nrm[i] * L for i in range(3)) for f in (0.0, 1.0)]
        for k, f in enumerate((0.0, 1.0)):
            base = tuple(h0[i] + (h1[i] - h0[i]) * f for i in range(3))
            out.append({"kind": "tube", "name": f"{n}_stanchion_{k}", "link": n, "p0": base, "p1": (t0, t1)[k], "r": 0.02, "mat": "aluminium"})
            out.append({"kind": "tube", "name": f"{n}_hinge_{k}", "link": rl["flight"], "p0": tuple(base[i] - rl["axis"][i] * 0.04 for i in range(3)),
                        "p1": tuple(base[i] + rl["axis"][i] * 0.04 for i in range(3)), "r": 0.028, "mat": "titanium"})
        out.append({"kind": "tube", "name": f"{n}_top", "link": n, "p0": t0, "p1": t1, "r": 0.022, "mat": "aluminium"})
        out.append({"kind": "sphere", "name": f"{n}_cap_0", "link": n, "c": t0, "r": 0.028, "mat": "titanium"})
        out.append({"kind": "sphere", "name": f"{n}_cap_1", "link": n, "c": t1, "r": 0.028, "mat": "titanium"})
    for k, z in enumerate(STEPS):
        t = (z0 - z) / (z0 - z1)
        link = "rear_stair" if z > zk else "rear_stair_lower"
        x = x0 + (x1 - x0) * t
        out += [
            {"kind": "box", "name": f"stair_tread_{k}", "link": link, "c": (x, 0, z), "size": (0.30, 1.10, 0.035), "mat": "grating"},
            {"kind": "box", "name": f"stair_tread_{k}_nosing", "link": link, "c": (x - 0.15, 0, z - 0.005), "size": (0.03, 1.10, 0.045),
             "mat": "gunmetal"},
            {"kind": "box", "name": f"stair_tread_{k}_led", "link": link, "c": (x - 0.168, 0, z - 0.012), "size": (0.008, 1.00, 0.015),
             "mat": "lamp_step"},
        ]
    out.append({"kind": "box", "name": "stair_foot_plate", "link": "rear_stair_lower", "c": (x1 + 0.08, 0, z1 + 0.02), "size": (0.20, 1.20, 0.04),
                "mat": "gunmetal"})
    out.append({"kind": "box", "name": "porch_led", "c": (PORCH[0] + 0.005, 0, PORCH[1] - 0.04), "size": (0.008, 1.60, 0.015),
                "mat": "lamp_step"})
    return out


def _railings():
    (x0, z0), (x1, z1) = (PORCH[0], PORCH[1] - 0.03), STAIR_FOOT
    out = []
    for flight, (ax, az), (bx, bz), yy, lift in (("rear_stair", (x0, z0), KNEE, 0.62, 0.06), ("rear_stair_lower", KNEE, (x1, z1), 0.57, 0.11)):
        ln = math.hypot(bx - ax, bz - az)
        d = ((bx - ax) / ln, 0.0, (bz - az) / ln)
        nrm = (-d[2], 0.0, d[0]) if -d[2] * 0 + d[0] * 1 > 0 else (d[2], 0.0, -d[0])
        for s in (-1, 1):
            h0 = (ax + d[0] * ln * 0.12 + nrm[0] * lift, s * yy, az + d[2] * ln * 0.12 + nrm[2] * lift)
            h1 = (ax + d[0] * ln * 0.90 + nrm[0] * lift, s * yy, az + d[2] * ln * 0.90 + nrm[2] * lift)
            axis = tuple(-c for c in d) if s > 0 else d
            out.append({"name": f"{flight}_rail_{'l' if s > 0 else 'r'}", "flight": flight, "h0": h0, "h1": h1, "n": nrm,
                        "len": min(0.65, yy - 0.03), "axis": axis})
    return out


RAILINGS = _railings()
RAIL_FOLD = math.pi / 2


def _railing_links():
    return [{"name": r["name"], "parent": r["flight"], "pos": r["h0"], "axis": r["axis"], "limit": (0.0, RAIL_FOLD + 0.02), "role": "railing",
             "mass": 3.0, "drive": {"kind": "position", "stiffness": 600.0, "damping": 60.0, "max_force": 300.0}} for r in RAILINGS]


RAIL_LINKS = _railing_links()


def _step_light_sites():
    (x0, z0), (x1, z1) = (PORCH[0], PORCH[1] - 0.03), STAIR_FOOT
    out = []
    for k, z in enumerate(STEPS):
        t = (z0 - z) / (z0 - z1)
        link = "rear_stair" if z > KNEE[1] else "rear_stair_lower"
        out.append((f"step_light_{k}", link, (x0 + (x1 - x0) * t - 0.17, 0, z - 0.02), (-0.3, 0, -1), "light",
                    "Stair tread LED strip (+Z = down/out)", {"radius_m": 0.03, "intensity": 150000.0, "colour_k": 4000.0}))
    out.append(("porch_step_light", "chassis", (PORCH[0], 0, PORCH[1] - 0.05), (-0.3, 0, -1), "light", "Porch edge LED strip",
                {"radius_m": 0.03, "intensity": 150000.0, "colour_k": 4000.0}))
    return out


ROVER = {
    "wheel": {"r": R_W, "w": W_W, "style": "solid", "grousers": 40, "chevron": False, "grouser_h": 0.04, "spokes": 12, "spoke_curve": 0.0,
              "spoke_r": 0.014, "spoke_mat": "titanium", "disc": True, "disc_mat": "anodised_dark", "tread_mat": "gunmetal",
              "grouser_mat": "titanium", "rim_mat": "gunmetal", "hub_mat": "aluminium", "hub_frac": 0.40, "mass": 200.0, "segments": 64},
    "wheels": [{"name": f"{a}{s}", "x": x, "y": sy * TRACK / 2, "steer": (math.radians(-35), math.radians(35)) if a == "f" else None}
               for a, x in zip(("f", "m", "r"), AXLES) for s, sy in (("l", 1), ("r", -1))],
    "suspension": {"type": "double_wishbone", "arm": 0.60, "kingpin_off": 0.45, "lower_dz": -0.12, "upper_dz": 0.30, "travel": (0.25, 0.25),
                   "static_rad": 0.10, "spread": 0.45, "tube_r": 0.04, "spring_mat": "titanium", "knuckle_mat": "gunmetal", "arm_mat": "gunmetal",
                   "strut_up": 0.10},
    "links": [
        {"name": "solar_wing_l", "pos": (WING_PIN[0], WING_PIN[1], WING_PIN[2]), "axis": (0, 0, -1), "limit": (0.0, math.radians(120)),
         "role": "solar", "mass": 250.0, "drive": {"kind": "position", "stiffness": 4.0e5, "damping": 4.0e4, "max_force": 2.0e4}},
        {"name": "solar_wing_r", "pos": (WING_PIN[0], -WING_PIN[1], WING_PIN[2]), "axis": (0, 0, 1), "limit": (0.0, math.radians(120)),
         "role": "solar", "mass": 250.0, "drive": {"kind": "position", "stiffness": 4.0e5, "damping": 4.0e4, "max_force": 2.0e4}},
        {"name": "airlock_hatch", "pos": (XR - 0.22, HINGE_Y - 0.03, HATCH_Z), "axis": (0, 0, 1), "limit": (0.0, math.radians(105)),
         "role": "hatch", "mass": 60.0, "drive": {"kind": "position", "stiffness": 4000.0, "damping": 400.0, "max_force": 800.0}},
        *BOLT_LINKS,
        {"name": "airlock_handwheel", "parent": "airlock_hatch", "pos": (XR - 0.33, 0, HATCH_Z), "axis": (-1, 0, 0), "limit": (-4 * math.pi, 4 * math.pi),
         "role": "latch", "mass": 2.0, "drive": {"kind": "position", "stiffness": 50.0, "damping": 5.0, "max_force": 40.0}},
        {"name": "rear_stair", "pos": (PORCH[0], 0, PORCH[1] - 0.03), "axis": (0, 1, 0), "limit": (0.0, 2.35), "role": "stair", "mass": 25.0,
         "drive": {"kind": "position", "stiffness": 8000.0, "damping": 800.0, "max_force": 4000.0}},
        {"name": "rear_stair_lower", "parent": "rear_stair", "pos": (KNEE[0], 0, KNEE[1]), "axis": (0, 1, 0), "limit": (0.0, 3.0), "role": "stair",
         "mass": 20.0, "drive": {"kind": "position", "stiffness": 4000.0, "damping": 400.0, "max_force": 2000.0}},
        *RAIL_LINKS,
    ],
    "parts": [*_body(), *_front(), *_roof(), *_sides(), *_wing(1), *_wing(-1), *_airlock(), *_patio(), *_stair()],
    "hga": {"base": (2.10, 0, 3.94), "h": 0.30, "r": 0.40, "boresight": (1, 0, 0.6), "band": "Ka", "front": "radome", "back": "white_panel"},
    "arm": {"base": (XR - 0.10, 0.98, 0.80), "up": (-1, 0, 0), "stow_dir": (0, 0, 1), "side": (0, 1, 0), "fold_off": (-1, 0, 0),
            "lengths": (0.85, 0.80, 0.25), "r": 0.06, "mat": "white_panel", "mass": 80.0, "tau": 600.0},
    "lights": [
        *[((2.73, s * y, 3.115), (1, s * (0.58 if k == 2 else 0.0), 0.05), 0.185, f"brow_lamp_{'l' if s > 0 else 'r'}{k}")
          for s in (-1, 1) for k, y in enumerate((0.94, 1.33, 1.73))],
        ((XF + 0.02, 1.10, 1.57), (1, 0, 0), 0.15, "bumper_lamp_l"),
        ((XF + 0.02, -1.10, 1.57), (1, 0, 0), 0.15, "bumper_lamp_r"),
        ((0.85, 2.19, 1.00), (0, 1, -0.2), 0.15, "work_light_l"),
        ((0.85, -2.19, 1.00), (0, -1, -0.2), 0.15, "work_light_r"),
        ((-2.83, 2.10, 1.35), (-1, 0, 0), 0.125, "rear_sponson_lamp_l"),
        ((-2.83, -2.10, 1.35), (-1, 0, 0), 0.125, "rear_sponson_lamp_r"),
        ((XR - 0.02, 1.45, 1.15), (-1, 0, 0), 0.125, "porch_lamp_l"),
        ((XR - 0.02, -1.45, 1.15), (-1, 0, 0), 0.125, "porch_lamp_r"),
    ],
    "sites": [
        ("airlock_hatch_centre", "airlock_hatch", (XR - 0.26, 0, HATCH_Z), (-1, 0, 0), "hatch",
         "Walk-in airlock hatch (1.0 x 1.5 m) outer face; +Z points aft"),
        ("airlock_sill", "chassis", (XR - 0.1, 0, HATCH_Z - 0.75), (0, 0, 1), "crew", "Airlock sill / step-over"),
        ("porch_deck", "chassis", ((XR + PORCH[0]) / 2, 0, PORCH[1]), (0, 0, 1), "crew", "Rear patio grating deck (1.8 x 0.5 m)"),
        ("stair_foot", "rear_stair_lower", (STAIR_FOOT[0], 0, STAIR_FOOT[1]), (0, 0, -1), "contact", "Fold-down stair foot (deployed)"),
        ("stair_knee", "rear_stair", (KNEE[0], 0, KNEE[1]), (0, 1, 0), "reference", "Stair knee hinge (folds the lower flight)"),
        *_step_light_sites(),
        ("driver_left", "chassis", (2.10, 0.60, 2.20), (1, 0, 0), "crew", "Cab driver station (estimated)"),
        ("driver_right", "chassis", (2.10, -0.60, 2.20), (1, 0, 0), "crew", "Cab co-driver station (estimated)"),
        ("lidar", "chassis", (2.57, 0, 3.635), (1, 0, 0), "sensor", "LiDAR window in the roof-front visor"),
        ("tow_point_l", "chassis", (XF + 0.12, 1.10, 0.50), (1, 0, 0), "hitch", "Front tow stub"),
        ("tow_point_r", "chassis", (XF + 0.12, -1.10, 0.50), (1, 0, 0), "hitch", "Front tow stub"),
        ("wing_root_l", "solar_wing_l", (-0.70, 2.30, 2.16), (0, 0, 1), "power", "Solar wing blanket root (4 x 10 m wing)"),
        ("wing_root_r", "solar_wing_r", (-0.70, -2.30, 2.16), (0, 0, 1), "power", "Solar wing blanket root (4 x 10 m wing)"),
    ],
    "imu": (0, 0, 1.6),
}

MASS = {
    "loaded": {"mass": 18000.0, "com_z": 1.60, "source": "JAXA 2025: up to 18 t fully loaded on the Moon"},
    "launch": {"mass": 15000.0, "com_z": 1.65, "source": "JAXA 2025: up to 15 t at launch"},
}
DEFAULT_MASS_STATE = "loaded"
MASS_SET = "Payload"
MASS_IS_TOTAL = True
INERTIA_BOX = (6.0, 3.6, 3.0)
GEOMETRY_VARIANTS = {"Solar": ["stowed", "deployed"]}
STOWED_POSE = {**{r["name"]: RAIL_FOLD for r in RAILINGS}, "rear_stair_lower": 3.0, "rear_stair": 2.35}
GEOMETRY_VARIANT_JOINTS = {"Solar": {"deployed": {"solar_wing_l": math.pi / 2, "solar_wing_r": math.pi / 2}}}

SEMANTIC_CLASS = ["lunar_rover", "pressurized_rover", "vehicle"]
ROBOT_TYPE = "Wheeled"
COLLIDERS, PHYSICS_MATERIAL, PHYSICS_MATERIALS = K.standard_physics(hull=("white_panel", "grey_panel", "gunmetal"))
SIMPLE_TRIS = 40000
RENDER_VIEWS = {
    **K.views(6.44, 4.84, 4.0, centre_z=2.0),
    "rear_patio": ((-10.2, -5.0, 2.9), (-3.4, 0, 1.9), 35),
    "airlock": ((-6.8, -1.9, 2.3), (-3.3, 0, 2.0), 35),
    "front": ((11.0, 0.0, 2.4), (0, 0, 2.3), 35),
    "solar_wide": ((26.0, -19.0, 5.5), (0.0, 0.0, 5.2), 30),
}
