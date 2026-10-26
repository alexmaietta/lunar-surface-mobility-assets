import datetime
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmesh
import bpy
from mathutils import Matrix, Vector

import assetcfg
import geo as G
from export import simple, triangles


def mass_props(cfg, link_masses, lo, hi):
    if getattr(cfg, "MASS", None):
        ms = cfg.MASS[cfg.DEFAULT_MASS_STATE]
        m = ms["mass"] + (0.0 if getattr(cfg, "MASS_IS_TOTAL", False) else sum(link_masses))
        if getattr(cfg, "INERTIA_BOX", None):
            sx, sy, sz = cfg.INERTIA_BOX
            return m, (ms.get("com_x", 0.0), 0.0, ms["com_z"]), (m / 12 * (sy * sy + sz * sz), m / 12 * (sx * sx + sz * sz),
                                                                m / 12 * (sx * sx + sy * sy))
        r, h = cfg.INERTIA_ENVELOPE
        ixx = m * (3 * r * r + h * h) / 12
        return m, (0.0, 0.0, ms["com_z"]), (ixx, ixx, 0.5 * m * r * r)
    m = sum(link_masses) or 1.0
    sx, sy, sz = (max(hi[i] - lo[i], 0.02) for i in range(3))
    com = tuple((lo[i] + hi[i]) / 2 for i in range(3))
    return m, com, (m / 12 * (sy * sy + sz * sz), m / 12 * (sx * sx + sz * sz), m / 12 * (sx * sx + sy * sy))


def link_hulls(meshes):
    groups = {}
    for ob in meshes:
        p = ob.parent
        while p is not None and "link" not in p:
            p = p.parent
        groups.setdefault(p["link"] if p is not None else "body", []).append(ob)
    hulls = {}
    for link, obs in groups.items():
        bm = bmesh.new()
        for ob in obs:
            for v in ob.data.vertices:
                bm.verts.new(ob.matrix_world @ v.co)
        if len(bm.verts) >= 4:
            res = bmesh.ops.convex_hull(bm, input=bm.verts)
            drop = [g for g in dict.fromkeys(res["geom_interior"] + res["geom_unused"]) if isinstance(g, bmesh.types.BMVert)]
            bmesh.ops.delete(bm, geom=drop, context="VERTS")
            bm.verts.index_update()
            hulls[link] = ([tuple(v.co) for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
        bm.free()
    return hulls


def write_usd(path, name, cfg, mass, hulls):
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(path)
    root = stage.GetPrimAtPath(f"/{name}")
    stage.SetDefaultPrim(root)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    root.SetMetadata("kind", "component")
    root.SetMetadata("assetInfo", {"name": name, "version": assetcfg.version(), "identifier": Sdf.AssetPath(f"./{name}.usd")})
    m, com, inertia = mass
    UsdPhysics.RigidBodyAPI.Apply(root)
    mapi = UsdPhysics.MassAPI.Apply(root)
    mapi.CreateMassAttr(float(m))
    mapi.CreateCenterOfMassAttr(Gf.Vec3f(*com))
    mapi.CreateDiagonalInertiaAttr(Gf.Vec3f(*inertia))
    mapi.CreatePrincipalAxesAttr(Gf.Quatf(1, 0, 0, 0))
    UsdGeom.Scope.Define(stage, f"/{name}/colliders")
    for link, (pts, faces) in hulls.items():
        mesh = UsdGeom.Mesh.Define(stage, f"/{name}/colliders/{link}")
        points = [Gf.Vec3f(*p) for p in pts]
        mesh.CreatePointsAttr(points)
        mesh.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(points))
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        normals = [Gf.GetNormalized(Gf.Cross(points[f[1]] - points[f[0]], points[f[2]] - points[f[0]])) for f in faces]
        mesh.CreateNormalsAttr(normals)
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.uniform)
        mesh.CreateFaceVertexCountsAttr([len(f) for f in faces])
        mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f])
        mesh.CreatePurposeAttr(UsdGeom.Tokens.guide)
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr(UsdPhysics.Tokens.convexHull)
        for api in ("NewtonCollisionAPI", "NewtonMeshCollisionAPI", "PhysxConvexHullCollisionAPI"):
            mesh.GetPrim().AddAppliedSchema(api)
        mesh.GetPrim().CreateAttribute("newton:maxHullVertices", Sdf.ValueTypeNames.Int, variability=Sdf.VariabilityUniform).Set(255)
        mesh.GetPrim().CreateAttribute("physxConvexHullCollision:hullVertexLimit", Sdf.ValueTypeNames.Int).Set(255)
    stage.GetRootLayer().customLayerData = {
        "creator": "lunar-surface-mobility-assets pipeline", "asset_name": name, "asset_version": assetcfg.version(),
        "usd_date_generated": datetime.date.today().isoformat(), "mass": float(m), "source": f"{cfg.ASSET_ID} (simple)"}
    stage.GetRootLayer().Save()
    return len(hulls)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    asset = assetcfg.arg(argv, "--asset", bpy.context.scene.get("asset_id"))
    cfg = assetcfg.load(asset)
    G.prune_variants(cfg)
    name = f"{asset}_simple"
    link_masses = [float(o.get("mass") or 0.0) for o in bpy.data.objects
                   if o.type == "EMPTY" and "link" in o and o.parent is not None]
    if not getattr(cfg, "MASS", None):
        link_masses = [float(o.get("mass") or 1.0) for o in bpy.data.objects if o.type == "EMPTY" and "link" in o]
    for ob in [o for o in bpy.data.objects if o.name.startswith("site:") or o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(ob)
    simple(getattr(cfg, "SIMPLE_TRIS", 8000))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    hulls = link_hulls(meshes)
    for ob in meshes:
        ob.data.transform(ob.matrix_world)
        ob.parent = None
        ob.matrix_world = Matrix.Identity(4)
    for ob in [o for o in bpy.data.objects if o.type == "EMPTY"]:
        bpy.data.objects.remove(ob)
    with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes, object=meshes[0]):
        bpy.ops.object.join()
    ob = meshes[0]
    ob.name = ob.data.name = name
    pts = [Vector(c) for c in ob.bound_box]
    lo = tuple(min(p[i] for p in pts) for i in range(3))
    hi = tuple(max(p[i] for p in pts) for i in range(3))
    out = assetcfg.asset_dir(cfg, "simple")
    if os.path.exists(out):
        shutil.rmtree(out)
    for fmt in ("usd", "gltf", "obj"):
        os.makedirs(os.path.join(out, fmt))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "gltf", f"{name}.glb"), export_format="GLB",
                              export_cameras=False, export_lights=False, export_yup=True, export_extras=False)
    bpy.ops.wm.obj_export(filepath=os.path.join(out, "obj", f"{name}.obj"), export_materials=True,
                          forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=False, export_normals=True)
    usd = os.path.join(out, "usd", f"{name}.usd")
    bpy.ops.wm.usd_export(filepath=usd, root_prim_path=f"/{name}", export_materials=True,
                          generate_preview_surface=True, export_textures_mode="KEEP", export_lights=False,
                          export_cameras=False, export_custom_properties=False, export_uvmaps=False,
                          convert_scene_units="METERS")
    ncol = write_usd(usd, name, cfg, mass_props(cfg, link_masses, lo, hi), hulls)
    print(f"exported {name}: {triangles(ob)} triangles, {len(ob.material_slots)} materials, {ncol} convex-hull colliders "
          f"-> {os.path.relpath(out, assetcfg.ROOT)}")


if __name__ == "__main__":
    main()
