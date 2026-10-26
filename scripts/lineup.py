import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

import assetcfg
import geo as G
import hero as H
import render as R


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    assets = assetcfg.arg(a, "--assets", "apollo_lm,mk1,mk2").split(",")
    out = os.path.abspath(assetcfg.arg(a, "--out", os.path.join(assetcfg.ROOT, "build", "lineup.jpg")))
    res = tuple(int(x) for x in assetcfg.arg(a, "--res", "2400x1200").split("x"))
    gap = float(assetcfg.arg(a, "--gap", "1.5"))
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    x, everything = 0.0, []
    for asset in assets:
        obs = G.prune_variants(assetcfg.load(asset), obs=H.append(asset, Vector((0, 0, 0))))
        lo, hi = H.bounds(obs)
        shift = Vector((x - lo.x, -(lo.y + hi.y) / 2, 0))
        for ob in obs:
            if ob.parent is None:
                ob.location += shift
        bpy.context.view_layer.update()
        lo, hi = H.bounds(obs)
        print(f"placed {asset}: {hi.x - lo.x:.2f} x {hi.y - lo.y:.2f} x {hi.z:.2f} m")
        x = hi.x + gap
        everything += obs
    lo, hi = H.bounds(everything)
    size = hi - lo
    R.setup_render(int(assetcfg.arg(a, "--samples", "128")), res)
    R.lunar(assetcfg.build_dir(assets[0], "textures"))
    lens = float(assetcfg.arg(a, "--lens", "85"))
    fov = 2 * math.atan(36 / 2 / lens)
    fit = max(size.x * 1.08, size.z * res[0] / res[1] * 1.25)
    dist = fit / 2 / math.tan(fov / 2) + size.y
    el = math.radians(float(assetcfg.arg(a, "--elevation", "4")))
    az = math.radians(float(assetcfg.arg(a, "--azimuth", "-90")))
    target = Vector(((lo.x + hi.x) / 2, 0, size.z * 0.45))
    cam = target + Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))) * dist
    R.camera(tuple(cam), tuple(target), lens)
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


if __name__ == "__main__":
    main()
