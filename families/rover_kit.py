import math

G_MOON = 1.625

TEXTURE_SETS = {
    "white_panel": ("panel", dict(colour=(0.86, 0.86, 0.84), tile_m=0.8, rough0=0.45, fastener_pitch=0.08)),
    "grey_panel": ("panel", dict(colour=(0.46, 0.47, 0.48), tile_m=0.6, rough0=0.5, metallic=0.2, fastener_pitch=0.06)),
    "aluminium": ("brushed", dict(colour=(0.80, 0.80, 0.80), tile_m=0.3, rough0=0.30)),
    "titanium": ("brushed", dict(colour=(0.60, 0.58, 0.55), tile_m=0.2, rough0=0.25, along=0)),
    "anodised_dark": ("anodised", dict(colour=(0.06, 0.06, 0.065), tile_m=0.3, rough0=0.5)),
    "anodised_grey": ("anodised", dict(colour=(0.30, 0.31, 0.32), tile_m=0.3, rough0=0.45)),
    "composite": ("composite", dict(colour=(0.07, 0.07, 0.08), tile_m=0.15)),
    "mli_gold": ("mli", dict(colour=(0.90, 0.62, 0.12), tile_m=0.5, gloss=0.10)),
    "mli_silver": ("mli", dict(colour=(0.80, 0.81, 0.83), tile_m=0.5, gloss=0.08, tape=False)),
    "beta_white": ("beta_cloth", dict(colour=(0.84, 0.83, 0.80), tile_m=0.4)),
    "solar_cells": ("solar_cells", dict(tile_m=0.32)),
    "osr": ("osr", dict(tile_m=0.2)),
    "tyre_mesh": ("perforated", dict(colour=(0.62, 0.62, 0.60), tile_m=0.12, hole_d=0.012, pitch=0.016)),
    "tread": ("anodised", dict(colour=(0.035, 0.035, 0.038), tile_m=0.2, rough0=0.75)),
    "seat_cloth": ("cloth", dict(colour=(0.55, 0.55, 0.52), tile_m=0.1)),
    "grating": ("perforated", dict(colour=(0.55, 0.55, 0.56), tile_m=0.15, hole_d=0.022, pitch=0.03)),
    "brushed_panel": ("brushed", dict(colour=(0.70, 0.71, 0.72), tile_m=1.0, rough0=0.28)),
    "regolith": ("regolith", dict(tile_m=4.0)),
}

MATERIALS = {
    "white_panel": {"set": "white_panel", "normal": 0.8},
    "grey_panel": {"set": "grey_panel", "normal": 0.8},
    "aluminium": {"set": "aluminium", "normal": 0.5},
    "titanium": {"set": "titanium", "normal": 0.4},
    "anodised_dark": {"set": "anodised_dark", "normal": 0.5},
    "anodised_grey": {"set": "anodised_grey", "normal": 0.5},
    "composite": {"set": "composite", "normal": 0.5},
    "mli_gold": {"set": "mli_gold", "normal": 1.0},
    "mli_silver": {"set": "mli_silver", "normal": 0.8},
    "beta_white": {"set": "beta_white", "normal": 0.8},
    "solar_cells": {"set": "solar_cells", "normal": 0.3},
    "radiator": {"set": "osr", "normal": 0.3},
    "tyre_mesh": {"set": "tyre_mesh", "normal": 0.6, "alpha": True},
    "tread": {"set": "tread", "normal": 0.5},
    "seat_cloth": {"set": "seat_cloth", "normal": 0.6},
    "accent": {"color": (0.80, 0.30, 0.05), "roughness": 0.5},
    "glass": {"color": (0.02, 0.025, 0.03), "roughness": 0.04, "metallic": 0.0},
    "lens": {"color": (0.01, 0.01, 0.012), "roughness": 0.05, "metallic": 0.0},
    "lamp": {"color": (0.95, 0.95, 0.90), "roughness": 0.2, "emission": (1.0, 0.97, 0.90, 6.0)},
    "lamp_blue": {"color": (0.6, 0.8, 1.0), "roughness": 0.2, "emission": (0.55, 0.8, 1.0, 6.0)},
    "radome": {"color": (0.82, 0.81, 0.78), "roughness": 0.6},
    "grating": {"set": "grating", "normal": 0.6, "alpha": True},
    "brushed_panel": {"set": "brushed_panel", "normal": 0.4},
    "gold_anodised": {"color": (0.80, 0.58, 0.20), "roughness": 0.35, "metallic": 0.9},
    "kapton": {"color": (0.72, 0.42, 0.10), "roughness": 0.25, "metallic": 0.5},
    "blue_paint": {"color": (0.05, 0.22, 0.70), "roughness": 0.45},
    "yellow": {"color": (0.85, 0.65, 0.05), "roughness": 0.45},
    "beacon": {"color": (1.0, 0.45, 0.05), "roughness": 0.3, "emission": (1.0, 0.45, 0.05, 3.0)},
    "cable": {"color": (0.08, 0.08, 0.08), "roughness": 0.55},
}


def materials(overrides=None, textures=None):
    t = {k: (g, dict(kw)) for k, (g, kw) in TEXTURE_SETS.items()}
    for k, v in (textures or {}).items():
        t[k] = v
    m = {k: dict(v) for k, v in MATERIALS.items()}
    for k, v in (overrides or {}).items():
        m[k] = v
    return t, m


def views(length, width, height, centre_z=None):
    cz = height * 0.45 if centre_z is None else centre_z
    s = max(length, width, height * 1.6)
    return {
        "front_three_quarter": ((s * 1.55, -s * 1.15, s * 0.42), (0, 0, cz), 40),
        "side": ((0.0, -s * 2.1, s * 0.25), (0, 0, cz), 40),
        "rear_three_quarter": ((-s * 1.5, -s * 1.1, s * 0.5), (0, 0, cz), 40),
        "wheel": ((length * 0.42 + s * 0.35, -width * 0.5 - s * 0.55, s * 0.12), (length * 0.32, -width * 0.42, height * 0.18), 35),
        "top_deck": ((s * 0.6, -s * 0.5, s * 1.5), (0, 0, height * 0.6), 35),
        "thumb": ((s * 1.5, -s * 1.1, s * 0.5), (0, 0, cz), 38),
    }


def suspension_tuning(total_mass, n_wheels, arm, static_rad=0.12, zeta=0.45):
    fw = total_mass * G_MOON / n_wheels
    k = fw * arm / static_rad
    kv = k / (arm * arm)
    c = 2 * zeta * math.sqrt(kv * total_mass / n_wheels) * arm * arm
    return k, c, -static_rad


def four_wheels(wb, track, steer=None, rear_steer=True, z=None, extra=None):
    out = []
    for a, x in (("f", wb / 2), ("r", -wb / 2)):
        for sd, y in (("l", track / 2), ("r", -track / 2)):
            w = {"name": f"{a}{sd}", "x": x, "y": y, "steer": steer if (a == "f" or rear_steer) else None}
            if z is not None:
                w["z"] = z
            w.update(extra or {})
            out.append(w)
    return out


def standard_physics(wheel_tokens=None, hull=("white_panel", "grey_panel")):
    return ({"chassis": [("hull", list(hull))], r"\w+_wheel": [("tyre", wheel_tokens)]},
            {"tyre": "tyre", "hull": "structure"},
            {"tyre": (0.9, 0.8, 0.0), "structure": (0.5, 0.4, 0.05)})
