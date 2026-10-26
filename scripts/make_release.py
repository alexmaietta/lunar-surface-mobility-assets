import argparse
import glob
import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

FORMATS = {"usd": "usd", "blend": "blender", "gltf": "gltf", "obj": "obj",
           "simple-usd": "simple/usd", "simple-gltf": "simple/gltf", "simple-obj": "simple/obj"}
DESCRIBE = {
    "usd": "USD asset (`{a}/{a}.usda`) with all variants and textures",
    "blend": "Blender model (`{a}/{a}.blend`), textures packed",
    "gltf": "glTF binary (`{a}/{a}.glb`), Y-up, textures embedded, one node per link",
    "obj": "OBJ (`{a}/{a}.obj`, `.mtl` and textures), Y-up, rest pose",
    "simple-usd": "simple USD (`{a}_simple/{a}_simple.usd`): one decimated mesh, flat materials, one rigid body",
    "simple-gltf": "simple glTF (`{a}_simple/{a}_simple.glb`): one decimated mesh, flat materials",
    "simple-obj": "simple OBJ (`{a}_simple/{a}_simple.obj` + `.mtl`): one decimated mesh, flat materials",
}


def zip_dir(src_dir, arc_root, zip_path, extras):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dirpath, dirnames, files in os.walk(src_dir):
            dirnames.sort()
            for f in sorted(x for x in files if not x.endswith(".blend1")):
                p = os.path.join(dirpath, f)
                z.write(p, os.path.join(arc_root, os.path.relpath(p, src_dir)))
        for p in extras:
            z.write(p, os.path.basename(p))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(assetcfg.ROOT, "build", "release"))
    a = ap.parse_args()
    version = assetcfg.version()
    out = os.path.join(a.out, f"v{version}")
    os.makedirs(out, exist_ok=True)
    sums, rows = [], []
    for p in sorted(glob.glob(os.path.join(assetcfg.ROOT, "configs", "*.py"))):
        asset = os.path.splitext(os.path.basename(p))[0]
        cfg = assetcfg.load(asset)
        extras = [assetcfg.asset_dir(cfg, n) for n in ("LICENSE", "NOTICE")]
        for name, folder in FORMATS.items():
            src = assetcfg.asset_dir(cfg, folder)
            if not os.path.isdir(src):
                raise SystemExit(f"missing assets/{cfg.ASSET_PATH}/{folder}: run ./pipeline.sh update first")
            zp = os.path.join(out, f"{asset}-{name}.zip")
            zip_dir(src, f"{asset}_simple" if name.startswith("simple") else asset, zp, extras)
            sums.append(f"{sha256(zp)}  {os.path.basename(zp)}")
            rows.append(f"| `{os.path.basename(zp)}` | {cfg.TITLE}: {DESCRIBE[name].format(a=asset)} |")
            print(f"wrote {zp} ({os.path.getsize(zp) / 1e6:.0f} MB)")
    with open(os.path.join(out, "SHA256SUMS"), "w") as f:
        f.write("\n".join(sums) + "\n")
    with open(os.path.join(out, "RELEASE_NOTES.md"), "w") as f:
        f.write(f"Lunar surface mobility assets v{version}.\n\n| File | Contents |\n|---|---|\n" + "\n".join(rows) + "\n\n"
                "Assets are licensed CC BY 4.0 (LICENSE and NOTICE in each zip). Checksums: `SHA256SUMS`.\n")
    print(f"release files in {out}")


if __name__ == "__main__":
    main()
