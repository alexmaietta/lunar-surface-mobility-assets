import math

from mathutils import Vector

import geo as G
import materials as M

TAU = 2 * math.pi
D = {
    "height": 8.05,
    "deck_flat": 4.30,
    "ring_h": 0.80,
    "shoulder_h": 0.55,
    "core_d": 3.08,
    "upper_h": 1.95,
    "waist_h": 0.85,
    "waist_d": 3.50,
    "core_mli_r": 1.64,
    "body_bottom": 1.20,
    "skirt_flat": 1.95,
    "lox_r": 0.88, "lox_len": 1.30, "lox_dome": 0.68, "lox_radius": 1.38,
    "gas_r": 0.32, "gas_len": 1.10, "gas_dome": 0.85, "gas_radius": 2.02,
    "be7_exit_r": 0.34, "be7_throat_r": 0.036, "be7_len": 1.45, "be7_exit_z": 1.25, "be7_gimbal_deg": 6.0,
    "leg_az": [45, 135, 225, 315],
    "foot_radius": 3.05, "foot_pad_r": 0.18, "hard_point_z": 3.90, "hard_point_r": 1.85,
    "knee_frac": 0.58, "stroke": 0.30,
    "rcs_az": [45, 135, 225, 315], "rcs_z": 7.70, "rcs_out": 0.30,
    "rcs_lower_az": [0, 90, 180, 270], "rcs_lower_z": 1.32,
    "solar_w": 1.20, "solar_h": 2.90, "solar_hinge_z": 4.05, "solar_tilt_deg": 10.0,
}


def z_levels():
    z = {"top": D["height"]}
    z["ring_bot"] = z["top"] - D["ring_h"]
    z["shoulder_bot"] = z["ring_bot"] - D["shoulder_h"]
    z["upper_bot"] = z["shoulder_bot"] - D["upper_h"]
    z["waist_bot"] = z["upper_bot"] - D["waist_h"]
    z["lower_bot"] = D["body_bottom"]
    return z


def polar(r, az_deg, z):
    a = math.radians(az_deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def build(cfg):
    D.update(getattr(cfg, "DIMENSIONS", {}))
    mat = lambda role: M.get(cfg.ROLE_MATERIALS[role])
    F = cfg.FEATURES
    z = z_levels()
    body = G.link("body", (0, 0, 0), mass=cfg.MASS["touchdown"]["mass"])

    rv = D["deck_flat"] / 2 / math.cos(math.pi / 8)
    ph = 0.0

    ring = G.prism_geo(8, D["deck_flat"] / 2, z["ring_bot"], z["top"] - 0.04, phase=ph + math.pi / 8)
    G.add_mesh_uv("avionics_ring", ring, mat("ring_panel"), body, smooth=False)
    deck = G.prism_geo(8, D["deck_flat"] / 2 + 0.02, z["top"] - 0.04, z["top"], phase=ph + math.pi / 8)
    G.add_mesh_uv("top_deck", deck, mat("deck_top"), body, smooth=False)
    lip = G.puff(G.prism_geo(8, D["deck_flat"] / 2 + 0.035, z["top"] - 0.10, z["top"] + 0.015,
                             phase=ph + math.pi / 8, top=False, bottom=False), 0.012, 0.15, seed=3)
    G.add_mesh_uv("deck_rim_mli", lip, mat("mli_rim"), body, smooth=True)
    for k in range(8):
        p = polar(rv - 0.035, k * 45, 0)
        G.add_mesh_uv(f"ring_post_{k}", G.box_uv((p.x, p.y, (z["ring_bot"] + z["top"] - 0.04) / 2),
                                                  (0.05, 0.05, D["ring_h"] - 0.06)), mat("frame"), body, smooth=False)
    for zz in (z["ring_bot"] + 0.015, z["top"] - 0.055):
        fr = G.prism_geo(8, D["deck_flat"] / 2 + 0.008, zz - 0.015, zz + 0.015, phase=ph + math.pi / 8)
        G.add_mesh_uv(f"ring_frame_{zz:.2f}", fr, mat("frame"), body, smooth=False)

    r_ring = D["deck_flat"] / 2 * 0.985
    r_core = D["core_mli_r"]
    shoulder = [(r_ring, z["ring_bot"] + 0.02), (r_ring * 0.995, z["ring_bot"] - 0.12),
                (r_core + 0.25, z["shoulder_bot"] + 0.25), (r_core, z["shoulder_bot"])]
    sh = G.lathe_geo(shoulder[::-1], 64)
    G.add_mesh_uv("mli_shoulder", G.puff(sh, 0.035, 0.25, seed=11), mat("mli_shoulder"), body)
    upper = [(r_core, z["upper_bot"]), (r_core + 0.03, z["upper_bot"] + D["upper_h"] * 0.5), (r_core, z["shoulder_bot"])]
    up = G.lathe_geo(_densify(upper, 10), 72)
    G.add_mesh_uv("mli_upper_tank", G.puff(up, 0.04, 0.3, seed=12), mat("mli_upper"), body)
    band = G.lathe_geo([(r_core + 0.05, z["shoulder_bot"] - 0.10), (r_core + 0.05, z["shoulder_bot"] - 0.02)], 72)
    G.add_mesh_uv("mli_upper_belt", band, mat("mli_upper"), body)

    wr = D["waist_d"] / 2
    waist = [(r_core + 0.04, z["upper_bot"]), (wr - 0.02, z["upper_bot"] - 0.25), (wr - 0.06, z["waist_bot"] + 0.25),
             (wr - 0.12, z["waist_bot"])]
    G.add_mesh_uv("mli_waist", G.puff(G.lathe_geo(_densify(waist, 6), 72), 0.06, 0.18, seed=13), mat("mli_lower"), body)
    for zz, nm in ((z["upper_bot"] - 0.02, "upper"), (z["waist_bot"] + 0.02, "lower")):
        G.add_mesh_uv(f"structural_ring_{nm}", G.lathe_geo([(wr + 0.03, zz - 0.04), (wr + 0.03, zz + 0.04)], 72),
                      mat("frame"), body, smooth=True)

    lox_h = D["lox_len"] + 2 * D["lox_dome"] * D["lox_r"]
    lox_z0 = z["lower_bot"] + 0.12
    for k in range(4):
        az = k * 90
        c = polar(D["lox_radius"], az, lox_z0)
        prof = G.capsule_profile(D["lox_r"], D["lox_len"], D["lox_dome"])
        tank = G.puff(G.lathe_geo(prof, 48, center=c), 0.03, 0.18, seed=20 + k)
        G.add_mesh_uv(f"lox_tank_{k}", tank, mat("mli_tank"), body)
    rw = D["lox_radius"] + 0.05
    web = [(rw, z["lower_bot"] + 0.05), (rw + 0.08, z["lower_bot"] + 0.6), (rw + 0.1, z["waist_bot"] - 0.4), (wr - 0.08, z["waist_bot"])]
    G.add_mesh_uv("mli_lower_web", G.puff(G.lathe_geo(_densify(web, 6), 64), 0.06, 0.2, seed=21), mat("mli_lower"), body)
    skirt = G.prism_geo(8, D["skirt_flat"], z["lower_bot"], z["lower_bot"] + 0.16, phase=ph + math.pi / 8)
    G.add_mesh_uv("thrust_skirt", skirt, mat("frame"), body, smooth=False)
    plate = G.lathe_geo([(D["be7_exit_r"] + 0.12, z["lower_bot"] + 0.02), (D["skirt_flat"] - 0.02, z["lower_bot"] + 0.02)], 48)
    G.add_mesh_uv("base_heat_shield", plate, mat("heat_shield"), body)

    gas_h = D["gas_len"] + 2 * D["gas_dome"] * D["gas_r"]
    gas_top = z["ring_bot"] - 0.10
    for i, az in enumerate((45, 135, 225, 315)):
        c = polar(D["gas_radius"], az, gas_top - gas_h)
        prof = G.capsule_profile(D["gas_r"], D["gas_len"], D["gas_dome"])
        role = cfg.GAS_TANK_ROLES[i]
        G.add_mesh_uv(f"gas_tank_{i}", G.lathe_geo(prof, 40, center=c), mat(role), body)
        for dz in (0.15, gas_h - 0.15):
            p0 = polar(D["gas_radius"] - D["gas_r"] * 0.7, az, c.z + dz)
            p1 = polar(r_core, az, c.z + dz)
            G.add_mesh_uv(f"gas_tank_{i}_strut_{int(dz * 100)}", G.tube_uv(p0, p1, 0.018, 10), mat("strut"), body)
        if F.get("rbf_tags"):
            _rbf_tag(f"gas_tank_{i}", polar(D["gas_radius"] + D["gas_r"], az, c.z + gas_h * 0.6), body, mat)

    for i, az in enumerate((20, 110, 200, 290)):
        pts = [polar(r_core + 0.08, az, z["ring_bot"] - 0.2), polar(r_core + 0.1, az + 3, z["upper_bot"] + 0.6),
               polar(wr + 0.06, az + 8, z["upper_bot"] - 0.2), polar(wr + 0.02, az + 12, z["waist_bot"] - 0.05)]
        G.pipe(f"feed_line_{i}", _smooth_path(pts, 6), 0.022, mat("line"), body, sides=10)

    if F.get("radiator"):
        rx = r_core + 0.22
        G.add_mesh_uv("radiator", G.box_uv((rx, 0, z["upper_bot"] + 1.0), (0.05, 0.62, 2.0)), mat("radiator"), body, smooth=False)
        for dz in (-0.8, 0.8):
            G.add_mesh_uv(f"radiator_standoff_{dz:+.1f}", G.tube_uv((r_core + 0.02, 0, z["upper_bot"] + 1.0 + dz),
                                                                    (rx - 0.02, 0, z["upper_bot"] + 1.0 + dz), 0.02, 8),
                          mat("strut"), body)

    _engine(body, z, mat)

    for i, az in enumerate(D["leg_az"]):
        _leg(i, az, body, z, mat)

    for i, az in enumerate(D["rcs_az"]):
        _rcs_pod(i, az, body, z, mat, cfg)
    if F.get("rcs_lower", True):
        for i, az in enumerate(D["rcs_lower_az"]):
            _rcs_lower_pod(i, az, body, z, mat, cfg)

    for i, az in enumerate(F.get("solar_az", [])):
        _solar_array(i, az, body, z, mat)

    _deck_equipment(body, z, mat, cfg)
    if F.get("offloader_mount"):
        x, y = F["offloader_mount"]
        G.site("offloader_mount", body, (x, y, z["top"]), (0, 0, 1), kind="mount",
               description="Deck mounting interface for the payload offloader (mates with mk1_offloader 'mount')")
        G.add_mesh_uv("offloader_mount_pad", G.box_uv((x, y, z["top"] + 0.005), (0.66, 0.66, 0.01)), mat("frame"), body, smooth=False)
    if F.get("scalpss"):
        _scalpss(body, z, mat)
    if F.get("flag_decal"):
        _flag(body, z, mat)

    G.site("vehicle_origin", body, (0, 0, 0), kind="reference", description="Ground point under the centreline, legs at nominal stroke")
    G.site("deck_center", body, (0, 0, z["top"]), kind="payload_interface", description="Top deck centre (payload mounting plane)")
    G.site("imu", body, (0, 0, z["ring_bot"] + 0.3), kind="sensor", description="IMU / navigation reference (estimated location)")
    for i, az in enumerate(D["leg_az"]):
        G.site(f"lift_point_{i}", body, polar(rv - 0.05, az, z["top"]), kind="handling", description="GSE lift point (deck corner)")
    return body


def _engine(body, z, mat):
    g = D["be7_gimbal_deg"]
    exit_z = D["be7_exit_z"]
    top_z = exit_z + D["be7_len"]
    pivot = (0, 0, top_z - 0.08)
    gx = G.link("be7_gimbal_x", pivot, body, mass=5.0,
                joint={"type": "revolute", "axis": (1, 0, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                       "drive": {"kind": "position", "stiffness": 20000.0, "damping": 400.0, "max_force": 4000.0}})
    eng = G.link("be7", pivot, gx, mass=180.0,
                 joint={"type": "revolute", "axis": (0, 1, 0), "limit": (-math.radians(g), math.radians(g)), "role": "gimbal",
                        "drive": {"kind": "position", "stiffness": 20000.0, "damping": 400.0, "max_force": 4000.0}})
    rt, re, L = D["be7_throat_r"], D["be7_exit_r"], D["be7_len"]
    throat_z = exit_z + L * 0.78
    bell = []
    for i in range(25):
        t = i / 24
        r = rt + (re - rt) * (1 - (1 - t) ** 1.9)
        bell.append((r, throat_z - (throat_z - exit_z) * t))
    bell = bell[::-1]
    outer = [(r + 0.012, zz) for r, zz in bell]
    G.add_mesh_uv("be7_nozzle", G.lathe_geo(outer, 64), mat("nozzle_ext"), eng)
    G.add_mesh_uv("be7_nozzle_inner", G.lathe_geo(bell, 64, flip=True), mat("nozzle_int"), eng)
    lip = G.lathe_geo([(re, exit_z), (re + 0.012, exit_z)], 64)
    G.add_mesh_uv("be7_nozzle_lip", lip, mat("nozzle_ext"), eng)
    G.add_mesh_uv("be7_chamber", G.lathe_geo([(rt + 0.01, throat_z), (0.11, throat_z + 0.10), (0.11, throat_z + 0.26),
                                               (0.09, throat_z + 0.30)], 32), mat("engine_metal"), eng)
    G.add_mesh_uv("be7_injector", G.lathe_geo([(0.13, throat_z + 0.30), (0.13, top_z - 0.12), (0.06, top_z - 0.08)], 32),
                  mat("engine_metal"), eng)
    for s, (dx, dy) in enumerate(((0.19, 0.0), (-0.17, 0.08))):
        G.add_mesh_uv(f"be7_turbopump_{s}", G.tube_uv((dx, dy, throat_z + 0.05), (dx, dy, throat_z + 0.38), 0.07, 20, r1=0.065),
                      mat("engine_metal"), eng)
    G.pipe("be7_feed_ox", [(0.19, 0.0, throat_z + 0.38), (0.19, 0, top_z - 0.15), (0.06, 0, top_z - 0.1)], 0.03,
           mat("line"), eng, sides=10)
    G.pipe("be7_regen_manifold", [(re * 0.55 * math.cos(a), re * 0.55 * math.sin(a), exit_z + 0.55) for a in
                                  [TAU * i / 32 for i in range(33)]], 0.016, mat("engine_metal"), eng, closed=True)
    for ax, (dx, dy) in (("x", (0, 0.42)), ("y", (0.42, 0))):
        G.add_mesh_uv(f"be7_actuator_{ax}", G.tube_uv((dx, dy, top_z + 0.25), (dx * 0.5, dy * 0.5, throat_z + 0.1), 0.025, 12),
                      mat("strut"), eng)
    G.add_mesh_uv("be7_gimbal_block", G.box_uv(pivot, (0.16, 0.16, 0.1)), mat("frame"), gx, smooth=False)
    G.thruster("be7_exit", eng, (0, 0, exit_z), (0, 0, -1), kind="main", thrust_n=44482.0, min_thrust_n=8896.0,
               isp_s=460.0, exit_radius=re, throat_radius=rt, propellant="LOX/LH2",
               notes="BE-7 dual-expander; 10,000 lbf, 20-100% throttle (Blue Origin). Exit radius estimated from photos.",
               confidence="thrust/isp official; geometry estimated")
    G.site("be7_gimbal_center", body, pivot, kind="reference", description="BE-7 gimbal pivot")


def _leg(i, az, body, z, mat):
    hp = polar(D["hard_point_r"], az, D["hard_point_z"])
    foot = polar(D["foot_radius"], az, D["foot_pad_r"] * 0.0 + 0.06)
    axis = (foot - hp).normalized()
    knee = hp + (foot - hp) * D["knee_frac"]
    G.add_mesh_uv(f"leg_{i}_primary_upper", G.tube_uv(hp, knee, 0.075, 24), mat("leg_lattice"), body)
    G.add_mesh_uv(f"leg_{i}_primary_core", G.tube_uv(hp, knee, 0.05, 16), mat("leg_tube"), body)
    G.add_mesh_uv(f"leg_{i}_hardpoint", G.box_uv(hp, (0.16, 0.16, 0.16)), mat("frame"), body, smooth=False)
    for s, daz in enumerate((-24, 24)):
        root = polar(D["skirt_flat"] / math.cos(math.pi / 8) - 0.05, az + daz * 0 + (daz / abs(daz)) * 22.5, z["lower_bot"] + 0.10)
        G.add_mesh_uv(f"leg_{i}_secondary_{s}", G.tube_uv(root, knee - axis * 0.05, 0.035, 14), mat("leg_lattice"), body)
        G.add_mesh_uv(f"leg_{i}_secondary_{s}_core", G.tube_uv(root, knee - axis * 0.05, 0.022, 10), mat("leg_tube"), body)
    G.add_mesh_uv(f"leg_{i}_knee_collar", G.tube_uv(knee - axis * 0.12, knee + axis * 0.06, 0.088, 24), mat("frame"), body)
    piston = G.link(f"leg_{i}_piston", knee, body, mass=12.0,
                    joint={"type": "prismatic", "axis": tuple(-axis), "limit": (0.0, D["stroke"]), "role": "landing_gear",
                           "drive": {"kind": "spring", "stiffness": 6.0e4, "damping": 8.0e3, "max_force": 2.0e5}})
    G.add_mesh_uv(f"leg_{i}_piston_rod", G.tube_uv(knee - axis * 0.2, foot - axis * 0.12, 0.048, 20, r1=0.04),
                  mat("piston"), piston)
    fp = G.lathe_geo([(0.04, foot.z + 0.12), (0.06, foot.z + 0.07), (D["foot_pad_r"], foot.z + 0.02),
                      (D["foot_pad_r"], foot.z - 0.01), (D["foot_pad_r"] * 0.85, foot.z - 0.05), (1e-3, foot.z - 0.06)][::-1], 32,
                     center=(foot.x, foot.y, 0))
    G.add_mesh_uv(f"leg_{i}_footpad", fp, mat("footpad"), piston)
    G.site(f"leg_{i}_foot_contact", piston, (foot.x, foot.y, foot.z - 0.06), (0, 0, -1), kind="contact",
           description="Footpad contact point (touchdown sensing)")
    G.site(f"leg_{i}_touchdown_sensor", piston, knee + axis * 0.1, tuple(axis), kind="sensor",
           description="Stroke / touchdown switch (estimated)")


def _rcs_pod(i, az, body, z, mat, cfg):
    rv = D["deck_flat"] / 2 / math.cos(math.pi / 8)
    a = math.radians(az)
    radial = Vector((math.cos(a), math.sin(a), 0))
    tang = Vector((-math.sin(a), math.cos(a), 0))
    c = polar(rv + D["rcs_out"], az, D["rcs_z"])
    for dz in (-0.18, 0.18):
        for dt in (-0.12, 0.12):
            p0 = polar(rv - 0.02, az, D["rcs_z"] + dz) + tang * dt
            G.add_mesh_uv(f"rcs_{i}_bracket_{dz:+.2f}_{dt:+.2f}", G.tube_uv(p0, c - radial * 0.06, 0.012, 8), mat("strut"), body)
    G.add_mesh_uv(f"rcs_{i}_pod", G.puff(G.box_uv(c, (0.16, 0.20, 0.22)), 0.006, 0.05, seed=40 + i),
                  mat("rcs_pod"), body, smooth=False)
    spec = cfg.RCS
    n = 0
    for kind, dirs in (("hot_gas", spec["hot_gas"]["dirs"]), ("cold_gas", spec["cold_gas"]["dirs"])):
        s = spec[kind]
        for d in dirs:
            flow = (radial * d[0] + tang * d[1] + Vector((0, 0, d[2]))).normalized()
            off = 0.10 if kind == "hot_gas" else 0.12
            exit_p = c + flow * (off + s["nozzle_len"])
            base = c + flow * off
            if kind == "cold_gas":
                base += Vector((0, 0, 0.06)) if d[2] == 0 else radial * 0.05
                exit_p = base + flow * s["nozzle_len"]
            G.add_mesh_uv(f"rcs_{i}_{kind}_{n}", G.tube_uv(base, exit_p, s["exit_r"] * 0.45, 16, r1=s["exit_r"], caps=False),
                          mat("rcs_nozzle"), body)
            G.thruster(f"rcs_{i}_{kind}_{n}", body, tuple(exit_p), tuple(flow), kind=f"rcs_{kind}", thrust_n=s["thrust_n"],
                       isp_s=s["isp_s"], exit_radius=s["exit_r"], propellant=s["propellant"], cluster=f"rcs_{i}",
                       notes=s["notes"], confidence=s["confidence"])
            n += 1


def _solar_array(i, az, body, z, mat):
    a = math.radians(az)
    radial = Vector((math.cos(a), math.sin(a), 0))
    tang = Vector((-math.sin(a), math.cos(a), 0))
    w, h = D["solar_w"], D["solar_h"]
    r_hinge = D["waist_d"] / 2 + 0.25
    hinge = polar(r_hinge, az, D["solar_hinge_z"])
    tilt = math.radians(D["solar_tilt_deg"])
    lk = G.link(f"solar_array_{i}", tuple(hinge), body, mass=18.0,
                joint={"type": "revolute", "axis": tuple(-tang), "limit": (math.radians(-tilt * 0 - 15), math.radians(95)),
                       "role": "deploy", "drive": {"kind": "position", "stiffness": 500.0, "damping": 50.0, "max_force": 400.0,
                                                   "target": 0.0}})
    up = (Vector((0, 0, 1)) * math.cos(tilt) + radial * math.sin(tilt)).normalized()
    n = radial.cross(Vector((0, 0, 1))).cross(up).normalized() * -1
    n = (radial * math.cos(tilt) - Vector((0, 0, 1)) * math.sin(tilt)).normalized()
    c = hinge + up * h / 2
    corners = [c + tang * sx * w / 2 + up * sy * h / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    t = 0.03
    V = [p + n * t / 2 for p in corners] + [p - n * t / 2 for p in corners]
    uv = [(0, 0), (w, 0), (w, h), (0, h)]
    G.add_mesh(f"solar_array_{i}_cells", V[:4], [(0, 1, 2, 3)], mat("solar"), lk, uvs=uv)
    G.add_mesh(f"solar_array_{i}_substrate", V[4:] + V[:4],
               [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
               mat("panel_back"), lk, uvs=uv + uv)
    back = -n * (t / 2 + 0.05)
    for sx in (-0.42, 0.42):
        p0 = hinge + tang * sx * w + back
        G.add_mesh_uv(f"solar_array_{i}_rail_{sx:+.2f}", G.box_uv(tuple(p0 + up * h / 2), (0.05, 0.05, h)) if False else
                      G.tube_uv(p0, p0 + up * h, 0.025, 8), mat("frame"), lk)
    for k in range(13):
        p0 = hinge + up * (h * (k + 0.5) / 13) + back
        G.add_mesh_uv(f"solar_array_{i}_rung_{k}", G.tube_uv(p0 - tang * 0.42 * w, p0 + tang * 0.42 * w, 0.012, 6), mat("frame"), lk)
    G.add_mesh_uv(f"solar_array_{i}_hinge", G.tube_uv(hinge - tang * w * 0.45, hinge + tang * w * 0.45, 0.035, 12), mat("frame"), body)
    top_back = hinge + up * (h * 0.92) + back
    G.add_mesh_uv(f"solar_array_{i}_stay", G.tube_uv(polar(D["core_mli_r"] + 0.02, az, top_back.z + 0.05), top_back, 0.015, 8),
                  mat("strut"), lk)
    G.site(f"solar_array_{i}_normal", lk, tuple(c + n * 0.02), tuple(n), kind="power", area_m2=w * h,
           description="Solar array centre; +Z = cell normal")


def _rcs_lower_pod(i, az, body, z, mat, cfg):
    a = math.radians(az)
    radial = Vector((math.cos(a), math.sin(a), 0))
    tang = Vector((-math.sin(a), math.cos(a), 0))
    r = D["skirt_flat"] / math.cos(math.pi / 8) * 0.0 + D["skirt_flat"] + 0.12
    c = polar(r, az + 22.5, D["rcs_lower_z"])
    a2 = math.radians(az + 22.5)
    radial = Vector((math.cos(a2), math.sin(a2), 0))
    tang = Vector((-math.sin(a2), math.cos(a2), 0))
    G.add_mesh_uv(f"rcs_low_{i}_pod", G.box_uv(tuple(c), (0.14, 0.18, 0.14)), mat("frame"), body, smooth=False)
    s = cfg.RCS["hot_gas"]
    for n, d in enumerate([(0, 0, -1), (0, 1, 0), (0, -1, 0)]):
        flow = (radial * d[0] + tang * d[1] + Vector((0, 0, d[2]))).normalized()
        base = c + flow * 0.08
        exit_p = base + flow * s["nozzle_len"]
        G.add_mesh_uv(f"rcs_low_{i}_hot_gas_{n}", G.tube_uv(base, exit_p, s["exit_r"] * 0.45, 16, r1=s["exit_r"], caps=False),
                      mat("rcs_nozzle"), body)
        G.thruster(f"rcs_low_{i}_hot_gas_{n}", body, tuple(exit_p), tuple(flow), kind="rcs_hot_gas", thrust_n=s["thrust_n"],
                   isp_s=s["isp_s"], exit_radius=s["exit_r"], propellant=s["propellant"], cluster=f"rcs_low_{i}",
                   notes=s["notes"] + " Aft cluster.", confidence=s["confidence"])


def _deck_equipment(body, z, mat, cfg):
    top = z["top"]
    F = cfg.FEATURES
    for j, (x, y, sx, sy, sz) in enumerate(cfg.DECK_BOXES):
        G.add_mesh_uv(f"deck_box_{j}", G.box_uv((x, y, top + sz / 2), (sx, sy, sz)), mat("deck_box"), body, smooth=False)
    for j, az in enumerate((180 - 22.5, 270 + 22.5)):
        rv = D["deck_flat"] / 2
        base = polar(rv - 0.25, az, top)
        d = (polar(1, az, 0) - Vector((0, 0, 0))).normalized() * 0.5 + Vector((0, 0, 0.85))
        d.normalize()
        G.add_mesh_uv(f"star_tracker_{j}_body", G.box_uv(base + Vector((0, 0, 0.06)), (0.14, 0.14, 0.12)), mat("deck_box"), body, smooth=False)
        G.add_mesh_uv(f"star_tracker_{j}_baffle", G.tube_uv(base + Vector((0, 0, 0.12)), base + Vector((0, 0, 0.12)) + d * 0.22,
                                                           0.05, 20, r1=0.07, caps=False), mat("baffle"), body)
        G.site(f"star_tracker_{j}", body, tuple(base + Vector((0, 0, 0.12)) + d * 0.22), tuple(d), kind="sensor",
               description="Star tracker boresight (+Z), estimated location")
    for j, az in enumerate((0, 90, 180, 270)[: F.get("omni_antennas", 2)]):
        rv = D["deck_flat"] / 2 / math.cos(math.pi / 8)
        p = polar(rv - 0.15, az, top)
        G.add_mesh_uv(f"omni_antenna_{j}_mast", G.tube_uv(p, p + Vector((0, 0, 0.18)), 0.015, 8), mat("strut"), body)
        G.add_mesh_uv(f"omni_antenna_{j}_radome", G.lathe_geo([(1e-3, 0.18), (0.06, 0.20), (0.065, 0.24), (1e-3, 0.27)], 24,
                                                             center=p), mat("radome"), body)
        G.site(f"omni_antenna_{j}", body, tuple(p + Vector((0, 0, 0.24))), kind="antenna", band="S",
               description="Low-gain / omni antenna phase centre (estimated)")
    if F.get("hga"):
        _hga(body, z, mat, F["hga"])
    if F.get("lra"):
        x, y = F["lra"]
        G.add_mesh_uv("lra_base", G.lathe_geo([(1e-3, top), (0.07, top), (0.07, top + 0.02)], 24, center=(x, y, 0)), mat("frame"), body)
        G.add_mesh_uv("lra_dome", G.lathe_geo([(0.065, top + 0.02), (0.05, top + 0.05), (1e-3, top + 0.065)], 24, center=(x, y, 0)),
                      mat("lra"), body)
        G.site("lra", body, (x, y, top + 0.05), kind="payload", description="NASA GSFC Laser Retroreflector Array (8 reflectors)")


def _hga(body, z, mat, spec):
    top = z["top"]
    x, y = spec["pos"]
    mast_h, dish_r = spec.get("mast_h", 0.45), spec.get("dish_r", 0.30)
    G.add_mesh_uv("hga_mast", G.tube_uv((x, y, top), (x, y, top + mast_h), 0.04, 16), mat("frame"), body)
    azl = G.link("hga_azimuth", (x, y, top + mast_h), body, mass=3.0,
                 joint={"type": "revolute", "axis": (0, 0, 1), "limit": (-math.pi, math.pi), "role": "antenna",
                        "drive": {"kind": "position", "stiffness": 50.0, "damping": 5.0, "max_force": 20.0}})
    G.add_mesh_uv("hga_az_housing", G.tube_uv((x, y, top + mast_h), (x, y, top + mast_h + 0.12), 0.07, 20), mat("deck_box"), azl)
    G.add_mesh_uv("hga_yoke", G.box_uv((x, y, top + mast_h + 0.2), (0.05, 0.36, 0.06)), mat("frame"), azl, smooth=False)
    pivot = (x, y, top + mast_h + 0.26)
    el = G.link("hga_elevation", pivot, azl, mass=4.0,
                joint={"type": "revolute", "axis": (0, 1, 0), "limit": (math.radians(-10), math.radians(100)), "role": "antenna",
                       "drive": {"kind": "position", "stiffness": 50.0, "damping": 5.0, "max_force": 20.0}})
    f = dish_r * 0.9
    prof = [(dish_r * i / 12, (dish_r * i / 12) ** 2 / (4 * f)) for i in range(13)]
    frame = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
    c = Vector(pivot) + Vector((0.06, 0, 0))
    G.add_mesh_uv("hga_dish_front", G.lathe_geo([(max(r, 1e-3), zz) for r, zz in prof], 48, c, frame), mat("hga_dish"), el)
    G.add_mesh_uv("hga_dish_back", G.lathe_geo([(max(r, 1e-3), zz - 0.01) for r, zz in prof], 48, c, frame, flip=True),
                  mat("deck_box"), el)
    G.add_mesh_uv("hga_feed", G.tube_uv(c, c + Vector((f, 0, 0)), 0.018, 12), mat("strut"), el)
    G.site("hga_boresight", el, tuple(c + Vector((f, 0, 0))), (1, 0, 0), kind="antenna", band=spec.get("band", "X"),
           description="High-gain antenna boresight (+Z); steerable (estimated configuration)")


def _scalpss(body, z, mat):
    for j, az in enumerate((0 + 22.5, 90 + 22.5, 180 + 22.5, 270 + 22.5)):
        p = polar(D["skirt_flat"] + 0.08, az, z["lower_bot"] + 0.25)
        look = (Vector((0, 0, 0)) - Vector((p.x, p.y, 0))).normalized() * 0.55 + Vector((0, 0, -1))
        look.normalize()
        G.add_mesh_uv(f"scalpss_cam_{j}", G.box_uv(tuple(p), (0.10, 0.10, 0.12)), mat("deck_box"), body, smooth=False)
        G.add_mesh_uv(f"scalpss_cam_{j}_lens", G.tube_uv(p, p + look * 0.08, 0.025, 16, caps=True), mat("lens"), body)
        G.sensor_camera(f"scalpss_cam_{j}", body, tuple(p + look * 0.08), tuple(look), (0, 0, 1),
                        {"focal_mm": 8.0, "aperture_mm": (11.3, 7.1), "fstop": 4.0, "clip_m": (0.05, 500.0),
                         "resolution": (4096, 2160), "source": "SCALPSS (NASA LaRC) - optics estimated"})


def _flag(body, z, mat):
    r = D["core_mli_r"] + 0.10
    zc = z["shoulder_bot"] - 0.55
    w, h = 0.95, 0.5
    a0 = -w / 2 / r + math.radians(-28)
    V, U = [], []
    for k in range(9):
        a = a0 + (w / r) * k / 8
        for s in (0, 1):
            V.append((r * math.cos(a), r * math.sin(a), zc - h / 2 + s * h))
            U.append((k / 8, s))
    F = [(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1) for k in range(8)]
    G.add_mesh("flag_decal", V, F, mat("flag"), body, uvs=U)


def _rbf_tag(name, p, body, mat):
    p = Vector(p)
    V = [p + Vector((0.0, -0.025, 0)), p + Vector((0.0, 0.025, 0)), p + Vector((0.01, 0.025, -0.38)), p + Vector((0.01, -0.025, -0.38))]
    G.add_mesh(f"{name}_rbf", V, [(0, 1, 2, 3)], mat("rbf"), body, uvs=[(0, 0), (0.05, 0), (0.05, 0.38), (0, 0.38)])


def _densify(profile, k):
    out = []
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        for i in range(k):
            t = i / k
            out.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
    out.append(profile[-1])
    return out


def _smooth_path(pts, k):
    pts = [Vector(p) for p in pts]
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(k):
            t = j / k
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return [tuple(p) for p in out]
