import argparse
import glob
import os
import sys

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

G_MOON = 1.625
GAP = 3.0


def hosts():
    cfgs = {os.path.splitext(os.path.basename(p))[0]: assetcfg.load(os.path.splitext(os.path.basename(p))[0])
            for p in sorted(glob.glob(os.path.join(assetcfg.ROOT, "configs", "*.py")))}
    deps = {dep for c in cfgs.values() for opts in getattr(c, "ATTACHMENTS", {}).values() for dep, _, _ in opts.values()}
    return [(a, c) for a, c in cfgs.items() if a not in deps]


def find_usd(asset, cfg):
    for p in (assetcfg.asset_dir(cfg, "usd", f"{asset}.usda"), os.path.join(assetcfg.ROOT, "build", asset, "usd", asset, f"{asset}.usda")):
        if os.path.exists(p):
            return p
    return None


def extent(path):
    st = Usd.Stage.Open(path, Usd.Stage.LoadNone)
    hint = UsdGeom.ModelAPI(st.GetDefaultPrim()).GetExtentsHintAttr().Get()
    if hint:
        return Gf.Vec3d(hint[0]), Gf.Vec3d(hint[1])
    return Gf.Vec3d(-2, -2, 0), Gf.Vec3d(2, 2, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(assetcfg.ROOT, "assets", "lunar_vehicles.usda"))
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    stage = Usd.Stage.CreateNew(out)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(G_MOON)
    ground = UsdGeom.Cube.Define(stage, "/World/Ground")
    ground.CreateSizeAttr(1.0)
    ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
    ground.AddScaleOp().Set(Gf.Vec3f(400, 400, 0.1))
    ground.CreateDisplayColorAttr([Gf.Vec3f(0.42, 0.41, 0.39)])
    UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

    UsdGeom.Scope.Define(stage, "/World/Vehicles")
    placed, x, rows = [], 0.0, []
    for asset, cfg in hosts():
        path = find_usd(asset, cfg)
        if not path:
            print(f"skip {asset}: not built")
            continue
        lo, hi = extent(path)
        tx = x - lo[0]
        prim = UsdGeom.Xform.Define(stage, f"/World/Vehicles/{asset}")
        prim.GetPrim().GetReferences().AddReference(os.path.relpath(path, os.path.dirname(out)))
        prim.AddTranslateOp().Set(Gf.Vec3d(tx, 0, 0))
        prim.GetPrim().SetMetadata("kind", "component")
        prim.GetPrim().SetDocumentation(getattr(cfg, "TITLE", asset))
        x = tx + hi[0] + GAP
        rows.append(f"{asset:18s} x {tx:7.2f}  {hi[0] - lo[0]:5.2f} x {hi[1] - lo[1]:5.2f} x {hi[2]:5.2f} m  {os.path.relpath(path, assetcfg.ROOT)}")
        placed.append(asset)
    stage.GetRootLayer().customLayerData = {"creator": "lunar-surface-mobility-assets pipeline", "assets": ",".join(placed),
                                             "asset_version": assetcfg.version()}
    stage.GetRootLayer().Save()
    print("\n".join(rows))
    print(f"wrote {os.path.relpath(out, assetcfg.ROOT)}: {len(placed)} vehicles in a row, {x - GAP:.1f} m long")


if __name__ == "__main__":
    main()
