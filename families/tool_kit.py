import math

import rover_kit as K

MOUNT_H = 0.60
EDGE_CLEAR = 0.08
GROUND = -MOUNT_H
EDGE_Z = GROUND + EDGE_CLEAR
BULK = 1500.0

FRONT_TOOLS = ("dozer_blade", "v_blade", "loader_bucket", "drum_excavator", "rock_rake")
REAR_TOOLS = ("ripper", "box_blade", "roller_compactor", "dump_trailer")


def attachments():
    return {"FrontTool": {t: (t, "tool_front", "mount") for t in FRONT_TOOLS},
            "RearTool": {t: (t, "tool_rear", "mount") for t in REAR_TOOLS}}


def mount_sites(front, rear):
    return [("tool_front", "chassis", front, (1, 0, 0), "mount",
             "Front tool interface (quick-attach coupler, mates with a construction tool's mount site)"),
            ("tool_rear", "chassis", rear, (-1, 0, 0), "mount",
             "Rear tool interface (quick-attach coupler, mates with a towed or three-point tool's mount site)")]


def mount_brackets(face_x, mount, sx, z=None, mat="anodised_grey", spread=0.15):
    mx, _, mz = mount
    bz = mz if z is None else z
    out = []
    if abs(mx - face_x) > 0.01:
        for sd, y in (("l", spread), ("r", -spread)):
            out.append({"kind": "beam", "name": f"tool_{'front' if sx > 0 else 'rear'}_bracket_{sd}", "p0": (face_x, y, bz),
                        "p1": (mx, y, bz), "w": 0.06, "h": 0.06, "mat": mat})
    out.append({"kind": "box", "name": f"tool_{'front' if sx > 0 else 'rear'}_receiver", "c": (mx - sx * 0.015, 0, mz),
                "size": (0.03, 0.36, 0.26), "mat": mat})
    return out


TOOL_TEXTURES = {
    "steel": ("brushed", dict(colour=(0.40, 0.40, 0.41), tile_m=0.25, rough0=0.38)),
    "wear_steel": ("brushed", dict(colour=(0.30, 0.29, 0.28), tile_m=0.2, rough0=0.5)),
}
TOOL_MATERIALS = {
    "steel": {"set": "steel", "normal": 0.5},
    "wear_steel": {"set": "wear_steel", "normal": 0.6},
}


def materials():
    return K.materials(TOOL_MATERIALS, TOOL_TEXTURES)


def views(length, width, height, cx, cz=None, sx=1):
    s = max(length, width, height * 1.6)
    c = (cx, 0, GROUND + height * 0.5 if cz is None else cz)
    return {
        "front_three_quarter": ((cx + sx * s * 1.05, -s * 0.85, GROUND + s * 0.5), c, 45),
        "side": ((cx, -s * 1.6, GROUND + s * 0.25), c, 45),
        "top_deck": ((cx + sx * s * 0.45, -s * 0.45, GROUND + s * 1.2), c, 38),
        "lunar": ((cx + sx * s * 1.05, -s * 0.85, GROUND + s * 0.5), c, 45),
        "thumb": ((cx + sx * s * 1.05, -s * 0.85, GROUND + s * 0.55), c, 42),
    }


def drive(stiffness, damping, max_force):
    return {"kind": "position", "stiffness": stiffness, "damping": damping, "max_force": max_force}


def passive(damping=0.5):
    return {"kind": "none", "stiffness": 0.0, "damping": damping}


def coupler(sx=1):
    out = [{"kind": "box", "name": "coupler_plate", "c": (sx * 0.02, 0, 0), "size": (0.04, 0.40, 0.30), "mat": "anodised_grey"}]
    for sd, y in (("l", 0.14), ("r", -0.14)):
        out.append({"kind": "box", "name": f"coupler_hook_{sd}", "c": (-sx * 0.012, y, 0.13), "size": (0.024, 0.05, 0.05),
                    "mat": "steel"})
        out.append({"kind": "tube", "name": f"coupler_lock_pin_{sd}", "p0": (sx * 0.0, y, -0.11), "p1": (-sx * 0.03, y, -0.11),
                    "r": 0.015, "mat": "steel"})
    out.append({"kind": "box", "name": "coupler_connector", "c": (sx * 0.05, 0.0, 0.07), "size": (0.04, 0.10, 0.06), "mat": "anodised_dark"})
    return out


def clevis(name, c, axis_y=True, gap=0.12, link="base", size=(0.10, 0.025, 0.12), mat="steel"):
    x, y, z = c
    out = []
    for sd, s in (("a", 1), ("b", -1)):
        out.append({"kind": "box", "name": f"{name}_{sd}", "link": link, "c": (x, y + s * gap / 2, z), "size": size, "mat": mat})
    out.append({"kind": "tube", "name": f"{name}_pin", "link": link, "p0": (x, y - gap / 2 - 0.03, z), "p1": (x, y + gap / 2 + 0.03, z),
                "r": 0.018, "mat": "steel"})
    return out


def actuator(name, p0, p1, r=0.035, link0="base", link1=None, split=0.55):
    p0, p1 = list(p0), list(p1)
    mid = [p0[i] + (p1[i] - p0[i]) * split for i in range(3)]
    out = [{"kind": "tube", "name": f"{name}_barrel", "link": link0, "p0": tuple(p0), "p1": tuple(mid), "r": r, "mat": "white_panel"},
           {"kind": "tube", "name": f"{name}_rod", "link": link1 or link0, "p0": tuple(mid), "p1": tuple(p1), "r": r * 0.55, "mat": "steel"}]
    return out


def bezier(p0, p1, p2, n=10):
    out = []
    for k in range(n + 1):
        t = k / n
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def thick_profile(front, t):
    back = []
    n = len(front)
    for i, (x, z) in enumerate(front):
        a, b = front[max(i - 1, 0)], front[min(i + 1, n - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = dz / L, -dx / L
        back.append((x - nx * t, z - nz * t))
    return front + list(reversed(back))


def moldboard_strips(name, link, origin, d, n, length, profile, t, mat, chunks=1):
    out = []
    ox, oy, oz = origin
    for k in range(len(profile) - 1):
        (f0, z0), (f1, z1) = profile[k], profile[k + 1]
        fm, zm = (f0 + f1) / 2, (z0 + z1) / 2
        seg = math.hypot(f1 - f0, z1 - z0)
        ay = (n[0] * (f1 - f0) / seg, n[1] * (f1 - f0) / seg, (z1 - z0) / seg)
        for c in range(chunks):
            s = (c + 0.5) / chunks * length
            out.append({"kind": "obox", "name": f"{name}_{k}" + (f"_{c}" if chunks > 1 else ""), "link": link,
                        "c": (ox + d[0] * s + n[0] * fm, oy + d[1] * s + n[1] * fm, zm), "ax": (d[0], d[1], 0.0), "ay": ay,
                        "size": (length / chunks + 0.002, seg + 0.004, t), "mat": mat})
    return out


def wheel_parts(name, link, c, r, w, mat_tyre="tyre_mesh", mat_hub="anodised_dark", spokes=8):
    x, y, z = c
    side = 1 if y >= 0 else -1
    out = [{"kind": "lathe", "name": f"{name}_tyre", "link": link, "c": (x, y, z), "n": (0, 1, 0), "sides": 40, "mat": mat_tyre,
            "profile": [(r * 0.80, -w / 2), (r, -w / 2 + 0.02), (r, w / 2 - 0.02), (r * 0.80, w / 2), (r * 0.80, -w / 2)]},
           {"kind": "lathe", "name": f"{name}_rim", "link": link, "c": (x, y, z), "n": (0, 1, 0), "sides": 32, "mat": "aluminium",
            "profile": [(r * 0.74, -w / 2 + 0.01), (r * 0.80, -w / 2 + 0.01), (r * 0.80, w / 2 - 0.01), (r * 0.74, w / 2 - 0.01),
                        (r * 0.74, -w / 2 + 0.01)]},
           {"kind": "lathe", "name": f"{name}_hub", "link": link, "c": (x, y, z), "n": (0, side, 0), "sides": 24, "mat": mat_hub,
            "profile": [(0.001, -w * 0.3), (r * 0.22, -w * 0.3), (r * 0.22, w * 0.35), (0.001, w * 0.42)]}]
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = (math.cos(a), 0.0, math.sin(a))
        mid = (r * 0.22 + r * 0.74) / 2
        out.append({"kind": "obox", "name": f"{name}_spoke_{k}", "link": link, "c": (x + d[0] * mid, y, z + d[2] * mid), "ax": d,
                    "ay": (0, 1, 0), "size": (r * 0.54, 0.03, 0.012), "mat": "aluminium"})
    return out


PHYSICS_MATERIALS = {"structure": (0.5, 0.4, 0.05), "tyre": (0.9, 0.8, 0.0), "steel": (0.45, 0.35, 0.05)}
