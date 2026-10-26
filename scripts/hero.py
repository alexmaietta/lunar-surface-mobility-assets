import glob
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import assetcfg
import geo as G
import layout
import render as R

MARGIN = 0.03
AZIMUTH = 25.0
ELEVATION = 8.0
LENS = 80.0
CROP_HEADROOM = 1.02


def hosts():
    cfgs = {os.path.splitext(os.path.basename(p))[0]: assetcfg.load(os.path.splitext(os.path.basename(p))[0])
            for p in sorted(glob.glob(os.path.join(assetcfg.ROOT, "configs", "*.py")))}
    deps = {dep for c in cfgs.values() for opts in getattr(c, "ATTACHMENTS", {}).values() for dep, _, _ in opts.values()}
    return [(a, c) for a, c in cfgs.items() if a not in deps]


def append(asset, offset):
    path = os.path.join(assetcfg.ROOT, "build", asset, f"{asset}.blend")
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = list(src.objects)
    obs = [ob for ob in dst.objects if ob is not None]
    for ob in obs:
        bpy.context.scene.collection.objects.link(ob)
    for ob in obs:
        if ob.parent is None:
            ob.location = ob.location + offset
    bpy.context.view_layer.update()
    return obs


def bounds(obs):
    pts = [ob.matrix_world @ Vector(c) for ob in obs if ob.type == "MESH" for c in ob.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.abspath(assetcfg.arg(a, "--out", os.path.join(assetcfg.ROOT, "docs", "images", "hero.jpg")))
    res = tuple(int(x) for x in assetcfg.arg(a, "--res", "4800x2400").split("x"))
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    groups = []
    for asset, cfg in hosts():
        obs = append(asset, Vector((0, 0, 0)))
        obs = G.prune_variants(cfg, obs=obs)
        for opts in getattr(cfg, "ATTACHMENTS", {}).values():
            dep, mount_site, _ = next(iter(opts.values()))
            site = next(ob for ob in obs if ob.name.split(".")[0] == f"site:{mount_site}")
            obs += append(dep, site.matrix_world.translation.copy())
        lo, hi = bounds(obs)
        groups.append({"asset": asset, "obs": obs, "lo": lo, "hi": hi, "lander": cfg.ASSET_PATH.endswith("/lander")})
    placed = layout.arrange(groups)
    everything = []
    for g in groups:
        sx, sy = placed[g["asset"]]["shift"]
        for ob in g["obs"]:
            if ob.parent is None:
                ob.location += Vector((sx, sy, 0))
        everything += g["obs"]
        print(f"placed {g['asset']} row {placed[g['asset']]['row']} shift ({sx:.1f}, {sy:.1f})")
    bpy.context.view_layer.update()
    lo, hi = bounds(everything)
    heights = sorted(g["hi"].z for g in groups)
    crop = heights[-2] * CROP_HEADROOM if "--crop" in a and len(heights) > 1 else hi.z
    cropped = crop < hi.z
    hi.z = min(hi.z, crop)
    centre = (lo + hi) / 2
    size = hi - lo
    corners = [ob.matrix_world @ Vector(c) for ob in everything if ob.type == "MESH" for c in ob.bound_box]
    corners = [Vector((c.x, c.y, min(c.z, crop))) for c in corners]
    R.setup_render(int(assetcfg.arg(a, "--samples", "256")), res)
    R.lunar(assetcfg.build_dir(hosts()[0][0], "textures"))
    bpy.context.scene.cycles.use_auto_tile = True
    bpy.context.scene.cycles.tile_size = 1024
    bpy.context.scene.render.use_simplify = True
    bpy.context.scene.cycles.texture_limit_render = "2048"
    bpy.context.scene.cycles.denoiser = "OPTIX"
    bpy.context.scene.cycles.denoising_use_gpu = True
    az, el = math.radians(AZIMUTH), math.radians(ELEVATION)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    target = Vector((centre.x, centre.y, size.z * 0.25))
    sc = bpy.context.scene
    aspect = res[1] / res[0]

    def frame(dist):
        for ob in [o for o in bpy.data.objects if o.name.startswith("env_cam")]:
            bpy.data.objects.remove(ob)
        cam = R.camera(tuple(target + d * dist), tuple(target), LENS)
        cam.data.clip_end = dist * 3
        bpy.context.view_layer.update()
        v = [world_to_camera_view(sc, cam, c) for c in corners]
        xs, ys = [p.x for p in v], [p.y for p in v]
        ok = all(p.z > 0 for p in v) and max(xs) - min(xs) <= 1 - 2 * MARGIN and max(ys) - min(ys) <= 1 - 2 * MARGIN
        sy = (max(ys) - 1 + MARGIN) * aspect if cropped else ((min(ys) + max(ys)) / 2 - 0.5) * aspect
        return cam, ok, ((min(xs) + max(xs)) / 2 - 0.5, sy)

    near, far = 1.0, 5000.0
    for _ in range(40):
        dist = (near + far) / 2
        near, far = (near, dist) if frame(dist)[1] else (dist, far)
    cam, _, (sx, sy) = frame(far)
    cam.data.shift_x, cam.data.shift_y = sx, sy
    print(f"camera {LENS:.0f} mm, {far:.1f} m, azimuth {AZIMUTH:.0f} deg, elevation {ELEVATION:.0f} deg, shift ({sx:+.3f}, {sy:+.3f})")
    if cropped:
        bpy.context.view_layer.update()
        low = min(world_to_camera_view(sc, cam, c).y for c in corners)
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = 0.0, 1.0
        sc.render.border_min_y, sc.render.border_max_y = max(0.0, low - MARGIN), 1.0
        print(f"cropped to the lowest {100 * (1 - sc.render.border_min_y):.0f}% of the frame height")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


if __name__ == "__main__":
    main()
