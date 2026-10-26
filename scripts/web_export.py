import argparse
import datetime
import io
import json
import math
import os
import shutil
import struct
import sys
import zipfile

from PIL import Image
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg
import layout
import scene

OUT = os.path.join(assetcfg.ROOT, "web", "models")


def yup(v):
    return [round(float(v[0]), 5), round(float(v[2]), 5), round(-float(v[1]), 5)]


def read_glb(path):
    b = open(path, "rb").read()
    ln, = struct.unpack_from("<I", b, 12)
    j = json.loads(b[20:20 + ln])
    o = 20 + ln
    bin_len, = struct.unpack_from("<I", b, o)
    return j, b[o + 8:o + 8 + bin_len]


def write_glb(path, j, binary):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(binary), 0x004E4942) + binary)


def webify(src, dst, max_px, quality):
    j, binary = read_glb(src)
    normal_images = set()
    for m in j.get("materials", []):
        t = m.get("normalTexture")
        if t is not None:
            normal_images.add(j["textures"][t["index"]].get("source"))
    new_views = {}
    for i, im in enumerate(j.get("images", [])):
        if "bufferView" not in im:
            continue
        bv = j["bufferViews"][im["bufferView"]]
        raw = binary[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        img = Image.open(io.BytesIO(raw))
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        if max(img.size) > max_px:
            s = max_px / max(img.size)
            img = img.resize((max(1, round(img.size[0] * s)), max(1, round(img.size[1] * s))), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=95 if i in normal_images else quality, method=5)
        new_views[im["bufferView"]] = buf.getvalue()
        im["mimeType"] = "image/webp"
    out = bytearray()
    for k, bv in enumerate(j["bufferViews"]):
        data = new_views.get(k)
        if data is None:
            data = binary[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        out += b"\0" * (-len(out) % 4)
        bv["byteOffset"], bv["byteLength"] = len(out), len(data)
        out += data
    j["buffers"] = [{"byteLength": len(out)}]
    if new_views:
        for t in j.get("textures", []):
            if "source" in t:
                t.setdefault("extensions", {})["EXT_texture_webp"] = {"source": t.pop("source")}
        for key in ("extensionsUsed", "extensionsRequired"):
            j[key] = sorted(set(j.get(key, [])) | {"EXT_texture_webp"})
    write_glb(dst, j, bytes(out))


def joints(usd_dir):
    path = os.path.join(usd_dir, "payloads", "Physics", "physics.usda")
    if not os.path.exists(path):
        return []
    stage = Usd.Stage.Open(path)
    out = []
    for prim in stage.Traverse():
        revolute = prim.IsA(UsdPhysics.RevoluteJoint)
        if not (revolute or prim.IsA(UsdPhysics.PrismaticJoint)):
            continue
        get = lambda n, d=None: prim.GetAttribute(n).Get() if prim.HasAttribute(n) else d
        if get("physics:excludeFromArticulation", False):
            continue
        child = prim.GetRelationship("physics:body1").GetTargets()
        if not child:
            continue
        rot = get("physics:localRot0", Gf.Quatf(1, 0, 0, 0))
        axis = Gf.Rotation(Gf.Quatd(rot)).TransformDir(Gf.Vec3d(1, 0, 0))
        lo, hi = get("physics:lowerLimit"), get("physics:upperLimit")
        sc = math.radians(1) if revolute else 1.0
        out.append({"name": prim.GetName(), "node": child[0].name, "type": "revolute" if revolute else "prismatic",
                    "axis": yup(axis), "role": get("joint:role", "actuated"), "drive": get("joint:driveKind", "none"),
                    "limit": [lo * sc, hi * sc] if lo is not None and hi is not None and math.isfinite(lo) and math.isfinite(hi) else None})
    return out


def attachment_mounts(cfg, usd_dir):
    out = []
    for set_name, options in getattr(cfg, "ATTACHMENTS", {}).items():
        for opt, (dep, _mount, _dep_site) in options.items():
            layer = os.path.join(usd_dir, "payloads", set_name, f"{opt}.usda")
            base = os.path.join(usd_dir, "payloads", "base.usda")
            if not os.path.exists(layer):
                continue
            root = Sdf.Layer.CreateAnonymous(".usda")
            root.subLayerPaths = [layer, base]
            stage = Usd.Stage.Open(root, Usd.Stage.LoadNone)
            holder = next((p for p in stage.TraverseAll() if p.GetName() == dep), None)
            if holder is None:
                continue
            t = UsdGeom.XformCache().GetLocalToWorldTransform(holder).ExtractTranslation()
            out.append({"set": set_name, "option": opt, "asset": dep, "position": yup(t)})
    return out


def propulsion(usd_dir):
    p = os.path.join(usd_dir, "thrusters.json")
    if not os.path.exists(p):
        return None
    th = json.load(open(p))["thrusters"]
    mains = [t for t in th if t["kind"] == "main"]
    return {"main": [{"name": t["name"], "thrust_n": t["thrustVac"], "isp_s": t["ispVac"], "propellant": t.get("propellant", "")}
                     for t in mains],
            "other": {k: sum(1 for t in th if t["kind"] == k) for k in sorted({t["kind"] for t in th if t["kind"] != "main"})}}


def masses(cfg, usd_path):
    if getattr(cfg, "MASS", None):
        return {k: v["mass"] for k, v in cfg.MASS.items()}, getattr(cfg, "DEFAULT_MASS_STATE", next(iter(cfg.MASS)))
    m = Sdf.Layer.FindOrOpen(usd_path).customLayerData.get("mass")
    return ({"total": float(m)}, "total") if m else ({}, None)


def entry(asset, cfg, kind, max_px, quality, files):
    usd = scene.find_usd(asset, cfg)
    if not usd:
        return None
    usd_dir = os.path.dirname(usd)
    full_src = assetcfg.asset_dir(cfg, "gltf", f"{asset}.glb")
    prev_src = assetcfg.asset_dir(cfg, "simple", "gltf", f"{asset}_simple.glb")
    if not os.path.exists(full_src):
        print(f"skip {asset}: no {os.path.relpath(full_src, assetcfg.ROOT)}")
        return None
    d = os.path.join(OUT, asset)
    os.makedirs(d, exist_ok=True)
    full = os.path.join(d, "full.glb")
    webify(full_src, full, max_px, quality)
    prev = None
    if os.path.exists(prev_src):
        prev = os.path.join(d, "preview.glb")
        shutil.copy(prev_src, prev)
    lo, hi = scene.extent(usd)
    mass, mass_default = masses(cfg, usd)
    e = {"id": asset, "title": getattr(cfg, "TITLE", asset), "doc": getattr(cfg, "DOC", ""), "path": cfg.ASSET_PATH, "kind": kind,
         "dims": {"length": round(hi[0] - lo[0], 3), "width": round(hi[1] - lo[1], 3), "height": round(hi[2], 3)},
         "bounds_zup": [list(map(float, lo)), list(map(float, hi))], "mass": mass, "mass_default": mass_default,
         "propulsion": propulsion(usd_dir), "joints": joints(usd_dir), "attachments": attachment_mounts(cfg, usd_dir),
         "files": {"full": f"{asset}/full.glb", "full_bytes": os.path.getsize(full)}}
    if prev:
        e["files"].update({"preview": f"{asset}/preview.glb", "preview_bytes": os.path.getsize(prev)})
    files += [full] + ([prev] if prev else [])
    print(f"{asset:16s} full {os.path.getsize(full_src) / 1e6:6.1f} -> {os.path.getsize(full) / 1e6:5.1f} MB, "
          f"preview {(os.path.getsize(prev) / 1e6 if prev else 0):4.2f} MB, {len(e['joints'])} joints")
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-px", type=int, default=1024)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--zip", default=None, help="also write the models into this zip (for the release)")
    ap.add_argument("--only", default="", help="comma list of asset ids to re-export (manifest is rebuilt for all)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    only = {x for x in a.only.split(",") if x}
    files, entries = [], []
    host_ids = [x for x, _ in scene.hosts()]
    deps = {d for _, c in scene.hosts() for o in getattr(c, "ATTACHMENTS", {}).values() for d, _, _ in o.values()}
    old = {}
    mpath = os.path.join(OUT, "manifest.json")
    if only and os.path.exists(mpath):
        old = {e["id"]: e for e in json.load(open(mpath))["assets"]}
    for asset in host_ids + sorted(deps):
        cfg = assetcfg.load(asset)
        kind = "attachment" if asset in deps else ("lander" if cfg.ASSET_PATH.endswith("/lander") else "rover")
        if only and asset not in only and asset in old:
            e = old[asset]
            files += [os.path.join(OUT, e["files"][k]) for k in ("full", "preview") if k in e["files"]]
        else:
            e = entry(asset, cfg, kind, a.max_px, a.quality, files)
        if e:
            entries.append(e)
    placed = layout.arrange([{"asset": e["id"], "lo": e["bounds_zup"][0], "hi": e["bounds_zup"][1]}
                             for e in entries if e["kind"] != "attachment"])
    for e in entries:
        p = placed.get(e["id"])
        e["position"] = yup((p["shift"][0], p["shift"][1], 0.0)) if p else None
        e["row"] = p["row"] if p else None
    manifest = {"version": assetcfg.version(), "generated": datetime.date.today().isoformat(), "frame": "glTF Y-up, metres",
                "gravity": 1.625, "assets": entries}
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1, allow_nan=False)
    files.append(mpath)
    total = sum(os.path.getsize(f) for f in files)
    print(f"wrote {os.path.relpath(OUT, assetcfg.ROOT)}: {len(entries)} assets, {total / 1e6:.1f} MB "
          f"(previews {sum(e['files'].get('preview_bytes', 0) for e in entries) / 1e6:.1f} MB)")
    if a.zip:
        os.makedirs(os.path.dirname(os.path.abspath(a.zip)), exist_ok=True)
        with zipfile.ZipFile(a.zip, "w", zipfile.ZIP_STORED) as z:
            for f in files:
                z.write(f, os.path.relpath(f, OUT))
        print(f"zipped -> {a.zip} ({os.path.getsize(a.zip) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
