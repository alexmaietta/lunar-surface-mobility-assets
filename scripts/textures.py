import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assetcfg
import texgen

argv = sys.argv[1:]
asset = assetcfg.arg(argv, "--asset")
cfg = assetcfg.load(asset)
only = assetcfg.arg(argv, "--only")
texgen.generate(assetcfg.build_dir(asset, "textures"), cfg.TEXTURE_SETS, res=int(assetcfg.arg(argv, "--res", 2048)),
                only=only.split(",") if only else None)
