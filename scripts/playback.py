import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

import assetcfg
import geo as G
import render as R

SHOTS = {
    "lunar_cruiser": [
        (0.0, (9.0, -7.5, 3.4), (0.0, 0.0, 1.8), 35),
        (5.0, (1.5, -12.0, 2.6), (0.0, 0.0, 1.8), 35),
        (12.0, (19.0, -11.0, 5.5), (0.0, 0.0, 5.0), 28),
        (19.0, (-2.0, -16.0, 8.0), (-1.0, 0.0, 3.0), 30),
        (21.5, (-9.4, -5.2, 2.6), (-3.9, 0.0, 1.3), 35),
        (29.0, (-6.6, -2.2, 2.4), (-3.3, 0.0, 2.1), 35),
        (35.5, (-7.5, 4.2, 2.6), (-3.2, 0.9, 1.5), 35),
        (42.0, (-13.0, -8.0, 4.2), (-2.0, 0.0, 2.2), 32),
    ],
}
BLANKET = (16.5, 19.5)
DUSK = (41.5, 45.0)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def shot(shots, t, blend=2.0):
    i = max(k for k, s in enumerate(shots) if s[0] <= t)
    a = shots[i]
    if i + 1 == len(shots):
        return a[1:]
    b = shots[i + 1]
    f = smooth((t - (b[0] - blend)) / blend)
    lerp = lambda u, v: tuple(x + (y - x) * f for x, y in zip(u, v))
    return lerp(a[1], b[1]), lerp(a[2], b[2]), a[3] + (b[3] - a[3]) * f


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    asset = assetcfg.arg(a, "--asset")
    cfg = assetcfg.load(asset)
    run = np.load(assetcfg.arg(a, "--run", os.path.join(assetcfg.ROOT, "build", asset, "demo_run.npz")))
    body_q, times, lights, names = run["body_q"], run["t"], run["lights"], [str(n) for n in run["bodies"]]
    out = os.path.abspath(assetcfg.arg(a, "--out", os.path.join(assetcfg.ROOT, "build", asset, "video")))
    os.makedirs(out, exist_ok=True)
    keep = dict(kv.split(":") for kv in assetcfg.arg(a, "--variant", "").split(",") if kv)
    G.prune_variants(cfg, keep)
    grow = [o for o in bpy.data.objects if o.get("variant", "").startswith("Solar:deployed")] if keep.get("Solar") == "deployed" else []
    R.setup_render(int(assetcfg.arg(a, "--samples", "16")), tuple(int(x) for x in assetcfg.arg(a, "--res", "1280x720").split("x")))
    if "--eevee" in a:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
        ee = bpy.context.scene.eevee
        ee.taa_render_samples = int(assetcfg.arg(a, "--samples", "16"))
        ee.shadow_pool_size = "1024"
        ee.shadow_ray_count = 4
        ee.shadow_step_count = 12
        ee.light_threshold = 0.001
    bpy.context.scene.render.image_settings.file_format = "JPEG"
    R.lunar(assetcfg.build_dir(asset, "textures"))
    R.add_lights(float(assetcfg.arg(a, "--light-scale", "1.0")))
    lamps = [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("lamp_")]
    for o in lamps:
        o.data.shadow_filter_radius = 2.0
        o.data.shadow_maximum_resolution = 0.002
    energy = {o.name: o.data.energy for o in lamps}
    sun, fill = bpy.data.objects["env_sun"], bpy.data.objects["env_fill"]
    if "sun_az" in run:
        az, el = float(run["sun_az"]), float(run["sun_el"])
        to_sun = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        sun.rotation_mode = fill.rotation_mode = "QUATERNION"
        sun.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(to_sun)
        back = Vector((-to_sun.x, -to_sun.y, 0.6)).normalized()
        fill.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(back)
        fill.data.energy = 0.6
    sun_e, fill_e = sun.data.energy, fill.data.energy
    empties = {o["link"]: o for o in bpy.data.objects if o.type == "EMPTY" and "link" in o}
    for e in empties.values():
        mw = e.matrix_world.copy()
        e.parent = None
        e.matrix_world = mw
        e.rotation_mode = "QUATERNION"
    idx = {n: names.index(n) for n in empties if n in names}
    root = names.index("chassis")
    shots = SHOTS.get(asset, SHOTS["lunar_cruiser"])
    start, end = int(assetcfg.arg(a, "--start", "0")), int(assetcfg.arg(a, "--end", str(len(times))))
    step = int(assetcfg.arg(a, "--step", "1"))
    for f in range(start, min(end, len(times)), step):
        path = os.path.join(out, f"frame_{f:05d}.jpg")
        if os.path.exists(path) and "--force" not in a:
            continue
        t = float(times[f])
        q = body_q[f]
        for n, i in idx.items():
            x, y, z, qx, qy, qz, qw = q[i]
            empties[n].location = (x, y, z)
            empties[n].rotation_quaternion = Quaternion((qw, qx, qy, qz))
        s = max(0.002, smooth((t - BLANKET[0]) / (BLANKET[1] - BLANKET[0])))
        for o in grow:
            o.scale = (1.0, 1.0, s)
        d = smooth((t - DUSK[0]) / (DUSK[1] - DUSK[0]))
        sun.data.energy = sun_e * (1 - 0.96 * d)
        fill.data.energy = fill_e * (1 - 0.9 * d)
        for o in lamps:
            o.data.energy = energy[o.name] if lights[f] else 0.0
        bpy.context.view_layer.update()
        c = Vector(q[root][:3])
        qx, qy, qz, qw = q[root][3:7]
        yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
        rot = Matrix.Rotation(yaw, 3, "Z")
        cam, tgt, lens = shot(shots, t)
        flat = Vector((c.x, c.y, 0.0))
        for ob in [o for o in bpy.data.objects if o.name == "env_cam"]:
            bpy.data.objects.remove(ob)
        R.camera(tuple(flat + rot @ Vector(cam)), tuple(flat + rot @ Vector(tgt)), lens)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"frame {f} t={t:.2f}", flush=True)


if __name__ == "__main__":
    main()
