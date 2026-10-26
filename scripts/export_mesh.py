import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

import assetcfg
import geo as G
from export import bake_uv_tiling


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    asset = assetcfg.arg(argv, "--asset", bpy.context.scene.get("asset_id"))
    cfg = assetcfg.load(asset)
    G.prune_variants(cfg)
    for ob in [o for o in bpy.data.objects if o.name.startswith("site:") or o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(ob)
    for ob in bpy.data.objects:
        if ob.type == "EMPTY" and "link" in ob:
            ob.name = ob["link"]
    bpy.context.view_layer.update()
    bake_uv_tiling()
    for fmt in ("gltf", "obj"):
        d = assetcfg.asset_dir(cfg, fmt)
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    bpy.ops.export_scene.gltf(filepath=assetcfg.asset_dir(cfg, "gltf", f"{asset}.glb"), export_format="GLB",
                              export_cameras=False, export_lights=False, export_yup=True, export_apply=True,
                              export_extras=False)
    bpy.ops.wm.obj_export(filepath=assetcfg.asset_dir(cfg, "obj", f"{asset}.obj"), export_materials=True,
                          path_mode="COPY", forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True,
                          export_normals=True, apply_modifiers=True, export_eval_mode="DAG_EVAL_RENDER")
    print(f"exported {asset}: gltf/{asset}.glb, obj/{asset}.obj -> {os.path.relpath(assetcfg.asset_dir(cfg), assetcfg.ROOT)}")


if __name__ == "__main__":
    main()
