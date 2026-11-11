import glob
import os
import re
import sys

from pxr import Sdf, Usd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def text_patterns(old, new):
    o = re.escape(old)
    return [(re.compile(rf'(asset_version = "){o}(")'), rf"\g<1>{new}\g<2>"),
            (re.compile(rf'(string version = "){o}(")'), rf"\g<1>{new}\g<2>"),
            (re.compile(rf'(isaac:version = "){o}(")'), rf"\g<1>{new}\g<2>"),
            (re.compile(rf"(lunar surface mobility assets v){o}\b"), rf"\g<1>{new}"),
            (re.compile(rf'("version": "){o}(")'), rf"\g<1>{new}\g<2>")]


def restamp_text(paths, old, new):
    pats, n = text_patterns(old, new), 0
    for p in paths:
        with open(p) as f:
            s = f.read()
        t = s
        for rx, rep in pats:
            t = rx.sub(rep, t)
        if t != s:
            with open(p, "w") as f:
                f.write(t)
            n += 1
    return n


def restamp_layer(path, old, new):
    layer = Sdf.Layer.FindOrOpen(path)
    data = dict(layer.customLayerData)
    if data.get("asset_version") == old:
        data["asset_version"] = new
        layer.customLayerData = data
    for prim in layer.rootPrims:
        info = dict(prim.assetInfo)
        if info.get("version") == old:
            info["version"] = new
            prim.assetInfo = info
    if not layer.dirty:
        return False
    layer.Save()
    return True


def stale_stamps(root, new):
    bad = [p for p in glob.glob(os.path.join(root, "assets", "*", "*", "*", "usd", "*.usda"))
           if f'asset_version = "{new}"' not in open(p).read()]
    for p in glob.glob(os.path.join(root, "assets", "*", "*", "*", "simple", "usd", "*.usd")):
        stage = Usd.Stage.Open(p)
        if stage.GetRootLayer().customLayerData.get("asset_version") != new or stage.GetDefaultPrim().GetAssetInfo().get("version") != new:
            bad.append(p)
    for p in glob.glob(os.path.join(root, "assets", "*", "*", "*", "urdf", "*.urdf.json")):
        if f'"version": "{new}"' not in open(p).read():
            bad.append(p)
    return bad


def main(argv):
    if len(argv) != 1 or not SEMVER.match(argv[0]):
        raise SystemExit("usage: bump_version.py <major.minor.patch>")
    root, new, old = assetcfg.ROOT, argv[0], assetcfg.version()
    if new == old:
        raise SystemExit(f"VERSION is already {old}")
    if tuple(map(int, new.split("."))) < tuple(map(int, old.split("."))):
        raise SystemExit(f"{new} is older than the current {old}")
    text = (glob.glob(os.path.join(root, "assets", "**", "*.usda"), recursive=True)
            + glob.glob(os.path.join(root, "assets", "*", "*", "*", "NOTICE"))
            + glob.glob(os.path.join(root, "assets", "*", "*", "*", "urdf", "*.urdf.json"))
            + glob.glob(os.path.join(root, "build", "*", "usd", "**", "*.usda"), recursive=True))
    n_text = restamp_text(text, old, new)
    n_bin = sum(restamp_layer(p, old, new) for p in glob.glob(os.path.join(root, "assets", "*", "*", "*", "simple", "usd", "*.usd")))
    with open(os.path.join(root, "VERSION"), "w") as f:
        f.write(new + "\n")
    bad = stale_stamps(root, new)
    print(f"bumped {old} -> {new}: {n_text} text files, {n_bin} simple USD files")
    if bad:
        raise SystemExit("not stamped " + new + ":\n  " + "\n  ".join(os.path.relpath(p, root) for p in bad))
    print(f"next: git add -u && git commit -m \"Release v{new}\" && git tag v{new} && git push origin main v{new}")


if __name__ == "__main__":
    main(sys.argv[1:])
