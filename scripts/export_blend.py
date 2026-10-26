import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

import assetcfg


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    asset = assetcfg.arg(argv, "--asset")
    cfg = assetcfg.load(asset)
    out = os.path.abspath(assetcfg.arg(argv, "--out", assetcfg.asset_dir(cfg, "blender", f"{asset}.blend")))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
    print(f"saved {out}: {len(bpy.data.objects)} objects, {len(bpy.data.images)} packed images")


if __name__ == "__main__":
    main()
