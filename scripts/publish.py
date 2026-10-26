import datetime
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

REPO = "https://github.com/alexmaietta/lunar-surface-mobility-assets"


def main():
    asset = assetcfg.arg(sys.argv[1:], "--asset")
    cfg = assetcfg.load(asset)
    src = os.path.join(assetcfg.ROOT, "build", asset, "usd", asset)
    if not os.path.exists(os.path.join(src, f"{asset}.usda")):
        raise SystemExit(f"{asset} is not packaged yet: run ./pipeline.sh {asset} package")
    dst = assetcfg.asset_dir(cfg)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, os.path.join(dst, "usd"))
    shutil.copy(os.path.join(assetcfg.ROOT, "LICENSE-ASSETS"), os.path.join(dst, "LICENSE"))
    with open(os.path.join(dst, "NOTICE"), "w") as f:
        f.write(f"{cfg.TITLE} ({asset}), lunar surface mobility assets v{assetcfg.version()}\n"
                f"Copyright {datetime.date.today().year} Alex Maietta\n\n"
                "Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0); see LICENSE.\n"
                f"Attribution: \"{cfg.TITLE} model by Alex Maietta\" ({REPO})\n\n"
                "Built from public sources; dimensions and performance figures not published by the manufacturer are\n"
                "estimates. Not affiliated with or endorsed by the vehicle manufacturer or NASA. Vehicle and company names\n"
                "are trademarks of their owners; manufacturer logos and wordmarks are left off the model.\n")
    print(f"published {asset} -> {os.path.relpath(dst, assetcfg.ROOT)}")


if __name__ == "__main__":
    main()
