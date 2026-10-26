import math

from mathutils import Vector

import geo as G
import materials as M

D = {
    "plate": (0.60, 0.60, 0.05),
    "turret_r": 0.14, "turret_h": 0.22,
    "mast_w": 0.18, "mast_h": 0.85,
    "jib_len": 4.2, "jib_gap": 0.60, "jib_w": 0.10, "jib_h": 0.16,
    "tail": 0.6,
    "sheave_r": 0.09,
    "line_len0": 0.45,
    "spreader": (0.55, 0.55, 0.06),
}


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    mat = lambda role: M.get(cfg.ROLE_MATERIALS[role])
    m = cfg.LINK_MASSES
    px, py, pz = D["plate"]
    base = G.link("base", (0, 0, 0), mass=m["base"])
    G.add_mesh_uv("mount_plate", G.box_uv((0, 0, pz / 2), D["plate"]), mat("frame"), base, smooth=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * (px / 2 - 0.05), sy * (py / 2 - 0.05), pz)
            G.add_mesh_uv(f"mount_bolt_{sx}{sy}", G.lathe_geo([(0.018, p[2]), (0.018, p[2] + 0.015), (1e-3, p[2] + 0.02)], 12,
                                                              center=(p[0], p[1], 0)), mat("fastener"), base)
    G.add_mesh_uv("slew_bearing", G.lathe_geo([(D["turret_r"] + 0.04, pz), (D["turret_r"] + 0.04, pz + 0.06),
                                               (D["turret_r"], pz + 0.06)], 32), mat("frame"), base)
    z_slew = pz + 0.06
    slew = G.link("crane_slew", (0, 0, z_slew), base, mass=m["crane_slew"],
                  joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "crane",
                         "drive": {"kind": "position", "stiffness": 6000.0, "damping": 2500.0, "max_force": 2000.0}})
    G.add_mesh_uv("turret", G.lathe_geo([(D["turret_r"], z_slew), (D["turret_r"], z_slew + D["turret_h"]),
                                          (D["turret_r"] * 0.7, z_slew + D["turret_h"] + 0.03)], 32), mat("housing"), slew)
    G.add_mesh_uv("slew_drive", G.box_uv((D["turret_r"] + 0.06, 0, z_slew + 0.1), (0.12, 0.14, 0.16)), mat("housing"), slew, smooth=False)
    z0 = z_slew + D["turret_h"]
    mw, mh = D["mast_w"], D["mast_h"]
    G.add_mesh_uv("mast", G.box_uv((0, 0, z0 + mh / 2), (mw, mw, mh)), mat("truss"), slew, smooth=False)
    G.add_mesh_uv("mast_core", G.box_uv((0, 0, z0 + mh / 2), (mw * 0.6, mw * 0.6, mh)), mat("frame"), slew, smooth=False)
    pivot = Vector((0, 0, z0 + mh))
    for sy in (-1, 1):
        G.add_mesh_uv(f"luff_clevis_{sy}", G.box_uv(tuple(pivot + Vector((0, sy * (D["jib_gap"] / 2 + 0.07), -0.05))),
                                                    (0.12, 0.03, 0.2)), mat("frame"), slew, smooth=False)
    luff = G.link("crane_luff", tuple(pivot), slew, mass=m["crane_luff"],
                  joint={"type": "revolute", "axis": (0, 1, 0), "limit": (math.radians(-30), math.radians(60)), "role": "crane",
                         "drive": {"kind": "position", "stiffness": 20000.0, "damping": 4500.0, "max_force": 5000.0}})
    L, gap, w, h = D["jib_len"], D["jib_gap"], D["jib_w"], D["jib_h"]
    G.add_mesh_uv("luff_pin", G.tube_uv(pivot + Vector((0, -gap / 2 - 0.09, 0)), pivot + Vector((0, gap / 2 + 0.09, 0)), 0.03, 16),
                  mat("frame"), luff)
    for sy in (-1, 1):
        c = pivot + Vector(((L - D["tail"]) / 2, sy * gap / 2, 0))
        G.add_mesh_uv(f"jib_boom_{sy}", G.box_uv(tuple(c), (L + D["tail"], w, h)), mat("truss"), luff, smooth=False)
        G.add_mesh_uv(f"jib_boom_core_{sy}", G.box_uv(tuple(c), (L + D["tail"], w * 0.5, h * 0.6)), mat("frame"), luff, smooth=False)
    for k in range(7):
        x = -D["tail"] + 0.1 + (L + D["tail"] - 0.2) * k / 6
        G.add_mesh_uv(f"jib_cross_{k}", G.tube_uv(pivot + Vector((x, -gap / 2, 0)), pivot + Vector((x, gap / 2, 0)), 0.018, 8),
                      mat("frame"), luff)
    tip = pivot + Vector((L, 0, 0))
    G.add_mesh_uv("jib_head", G.box_uv(tuple(tip + Vector((0.05, 0, 0))), (0.14, gap + w, h * 1.1)), mat("housing"), luff, smooth=False)
    sheave_c = tip + Vector((0.12, 0, -h / 2 - D["sheave_r"]))
    G.add_mesh_uv("sheave", G.tube_uv(sheave_c + Vector((0, -0.03, 0)), sheave_c + Vector((0, 0.03, 0)), D["sheave_r"], 24),
                  mat("fastener"), luff)
    G.add_mesh_uv("hoist_winch", G.tube_uv(pivot + Vector((-D["tail"] + 0.15, -0.18, 0.12)), pivot + Vector((-D["tail"] + 0.15, 0.18, 0.12)),
                                           0.08, 20), mat("housing"), luff)
    G.add_mesh_uv("luff_actuator", G.tube_uv(pivot + Vector((0.0, 0, -mh * 0.8)), pivot + Vector((0.9, 0, -0.02)), 0.035, 12),
                  mat("frame"), slew)
    G.site("cable_anchor", luff, tuple(sheave_c + Vector((0, 0, -D["sheave_r"]))), (0, 0, -1), kind="cable_anchor",
           description="Hoist line leaves the sheave here (+Z = down the line); attach point for a simulated cable")
    line_top = sheave_c + Vector((0, 0, -D["sheave_r"]))
    hoist = G.link("crane_hoist", tuple(line_top), luff, mass=m["crane_hoist"],
                   joint={"type": "prismatic", "axis": (0, 0, -1), "limit": (0.0, 9.0), "role": "crane",
                          "drive": {"kind": "position", "stiffness": 5000.0, "damping": 500.0, "max_force": 6000.0}})
    hook = line_top + Vector((0, 0, -D["line_len0"]))
    G.add_mesh_uv("hoist_line", G.tube_uv(line_top, hook, 0.005, 8, caps=False), mat("cable"), hoist)
    G.add_mesh_uv("hook_block", G.box_uv(tuple(hook + Vector((0, 0, -0.05))), (0.10, 0.08, 0.10)), mat("housing"), hoist, smooth=False)
    sx, sy, sz = D["spreader"]
    sp_c = hook + Vector((0, 0, -0.14))
    G.add_mesh_uv("spreader", G.box_uv(tuple(sp_c), D["spreader"]), mat("truss"), hoist, smooth=False)
    for cx in (-1, 1):
        for cy in (-1, 1):
            G.add_mesh_uv(f"sling_{cx}{cy}", G.tube_uv(hook + Vector((0, 0, -0.1)), sp_c + Vector((cx * sx / 2.2, cy * sy / 2.2, sz / 2)),
                                                       0.004, 6, caps=False), mat("cable"), hoist)
            G.site(f"spreader_pick_{'p' if cx > 0 else 'n'}{'p' if cy > 0 else 'n'}", hoist,
                   tuple(sp_c + Vector((cx * sx / 2.2, cy * sy / 2.2, -sz / 2))), (0, 0, -1), kind="payload_interface",
                   description="Spreader pick point (payload sling / latch attach)")
    G.site("cable_hook", hoist, tuple(hook), (0, 0, -1), kind="cable_anchor",
           description="Lower end of the hoist line (hook block); attach point for a simulated cable")
    G.site("mount", base, (0, 0, 0), (0, 0, -1), kind="mount", description="Mounting interface: mates with a lander's offloader_mount site")
    return base
