import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "families")]
import bpy

import assetcfg
import geo as G
import materials as M

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
asset = assetcfg.arg(argv, "--asset")
cfg = assetcfg.load(asset)
G.reset()
M.configure(assetcfg.build_dir(asset, "textures"), cfg.MATERIALS)
family = importlib.import_module(cfg.FAMILY)
family.build(cfg)
sc = bpy.context.scene
sc["asset_id"] = asset
for i, ob in enumerate(o for o in bpy.data.objects if o.type == "MESH"):
    G.ensure_uvs(ob)
    if getattr(cfg, "SEPARATE_COPLANAR", True):
        G.separate_coplanar(ob, i)


def merge_rigid_parts():
    groups = {}
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.parent is None or "link" not in ob.parent:
            continue
        mat = ob.data.materials[0].name if ob.data.materials else "none"
        groups.setdefault((ob.parent["link"], mat, ob.get("variant", "")), []).append(ob)
    for (link, mat, variant), obs in groups.items():
        target = obs[0]
        if len(obs) > 1:
            for o in obs:
                if o.data.users > 1:
                    o.data = o.data.copy()
            with bpy.context.temp_override(active_object=target, selected_editable_objects=obs, object=target):
                bpy.ops.object.join()
        target.name = target.data.name = f"{link}__{mat}" + (f"__{variant.replace(':', '_').replace(',', '_')}" if variant else "")
    return len(groups)


if "--no-merge" not in argv:
    print(f"merged rigid parts into {merge_rigid_parts()} meshes")
out = assetcfg.arg(argv, "--out", os.path.join(assetcfg.build_dir(asset), f"{asset}.blend"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
nm = sum(1 for o in bpy.data.objects if o.type == "MESH")
nl = sum(1 for o in bpy.data.objects if "link" in o)
print(f"built {asset}: {nm} meshes, {nl} links, {len(G._registry('sites'))} sites -> {out}")
