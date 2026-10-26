import datetime
import json
import math
import os
import re
import shutil
import sys

import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

DEG = 180.0 / math.pi
CREATOR = "lunar-surface-mobility-assets pipeline"
PASSIVE_ROLES = {"landing_gear", "suspension", "linkage"}
LOCK_ROLES = {"deploy"}
DOUBLE_SIDED_HINTS = ("solar_cells", "leg_lattice", "flag", "rbf")

ROOT = None


def sanitize(name):
    s = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return s if s[0].isalpha() or s[0] == "_" else "_" + s


def new_stage(path, default_prim=True, sublayers=()):
    if os.path.exists(path):
        os.remove(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    layer = stage.GetRootLayer()
    layer.customLayerData = {"creator": CREATOR}
    for s in sublayers:
        layer.subLayerPaths.append(s)
    if default_prim:
        layer.defaultPrim = ROOT[1:]
    return stage


def apply_schemas(prim, names):
    ops = prim.GetMetadata("apiSchemas") or Sdf.TokenListOp()
    items = []
    for lst in (ops.explicitItems, ops.prependedItems, ops.addedItems, ops.appendedItems):
        items += [i for i in lst if i not in items]
    items += [n for n in names if n not in items]
    ops = Sdf.TokenListOp()
    ops.prependedItems = items
    prim.SetMetadata("apiSchemas", ops)


def set_attr(prim, name, vtype, value, uniform=False, custom=False):
    a = prim.CreateAttribute(name, vtype, custom, Sdf.VariabilityUniform if uniform else Sdf.VariabilityVarying)
    a.Set(value)
    return a


def xform_ops(prim, translate=(0, 0, 0), orient=Gf.Quatd(1, 0, 0, 0), scale=(1, 1, 1)):
    x = UsdGeom.Xformable(prim)
    x.ClearXformOpOrder()
    x.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*translate))
    x.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(orient))
    x.AddScaleOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*scale))


def retarget(layer, old, new, root=None):
    old, new = Sdf.Path(old), Sdf.Path(new)

    def fix(p):
        return p.ReplacePrefix(old, new) if p.HasPrefix(old) else p

    def visit(path):
        spec = layer.GetObjectAtPath(path)
        if isinstance(spec, Sdf.RelationshipSpec):
            items = list(spec.targetPathList.explicitItems) or list(spec.targetPathList.prependedItems)
            if items:
                spec.targetPathList.ClearEdits()
                spec.targetPathList.explicitItems = [fix(p) for p in items]
        elif isinstance(spec, Sdf.AttributeSpec):
            items = list(spec.connectionPathList.explicitItems) or list(spec.connectionPathList.prependedItems)
            if items:
                spec.connectionPathList.ClearEdits()
                spec.connectionPathList.explicitItems = [fix(p) for p in items]

    layer.Traverse(Sdf.Path(root) if root else Sdf.Path.absoluteRootPath, visit)


class Source:

    def __init__(self, d):
        self.dir = d
        self.layer = Sdf.Layer.FindOrOpen(os.path.join(d, "visuals.usdc"))
        self.stage = Usd.Stage.Open(self.layer)
        self.items = {}
        for link_prim in self.stage.GetPrimAtPath("/visuals").GetChildren():
            if not link_prim.GetName().startswith("L_"):
                continue
            out = []
            for obj in link_prim.GetChildren():
                mesh = next((c for c in Usd.PrimRange(obj) if c.IsA(UsdGeom.Mesh)), None)
                if mesh is None:
                    continue
                m = UsdGeom.Xformable(obj).GetLocalTransformation()
                if mesh != obj:
                    m = UsdGeom.Xformable(mesh).GetLocalTransformation() * m
                tgt = UsdShade.MaterialBindingAPI(mesh).GetDirectBindingRel().GetTargets()
                out.append((sanitize(obj.GetName()), mesh.GetPath(), m, tgt[0].name if tgt else None))
            self.items[link_prim.GetName()[2:]] = out

    def points(self, link, names=None, skip=None):
        pts = []
        for g, mp, m, _mat in self.items.get(link, []):
            if names and not any(t in g for t in names):
                continue
            if skip and skip(g):
                continue
            p = UsdGeom.Mesh(self.stage.GetPrimAtPath(mp)).GetPointsAttr().Get()
            if p:
                pts += [m.Transform(Gf.Vec3d(*q)) for q in p]
        return np.array([[q[0], q[1], q[2]] for q in pts]) if pts else np.zeros((0, 3))


def link_paths(links, root_link):
    paths = {}

    def path(name):
        if name not in paths:
            parent = links[name]["parent"]
            paths[name] = f"{ROOT}/Geometry/{name}" if parent is None else f"{path(parent)}/{name}"
        return paths[name]

    for n in links:
        path(n)
    return paths


def dfs(links, root):
    kids = {}
    for n, L in links.items():
        if L["parent"]:
            kids.setdefault(L["parent"], []).append(n)
    order = []

    def walk(n):
        order.append(n)
        for c in sorted(kids.get(n, [])):
            walk(c)

    walk(root)
    return order


def is_open(mesh):
    counts, idx = mesh.GetFaceVertexCountsAttr().Get(), mesh.GetFaceVertexIndicesAttr().Get()
    if not counts or not idx:
        return False
    edges, o = {}, 0
    for c in counts:
        f = idx[o:o + c]
        for i in range(c):
            a, b = f[i], f[(i + 1) % c]
            k = (a, b) if a < b else (b, a)
            edges[k] = edges.get(k, 0) + 1
        o += c
    return any(v == 1 for v in edges.values())


def hull_mesh(points):
    from scipy.spatial import ConvexHull
    if len(points) > 4000:
        points = points[np.random.default_rng(0).choice(len(points), 4000, replace=False)]
    h = ConvexHull(points)
    if len(h.vertices) > 200:
        v = points[h.vertices]
        keep = v[np.random.default_rng(1).choice(len(v), 200, replace=False)]
        h = ConvexHull(keep)
        points = keep
    used = sorted(set(h.simplices.ravel()))
    remap = {o: i for i, o in enumerate(used)}
    c = points.mean(0)
    tris = []
    for s, eq in zip(h.simplices, h.equations):
        a, b, d = (points[i] for i in s)
        n = np.cross(b - a, d - a)
        tris.append([remap[i] for i in (s if np.dot(n, eq[:3]) > 0 else s[::-1])])
    return [tuple(map(float, points[o])) for o in used], [3] * len(tris), [i for t in tris for i in t]


def collider_specs(src, links, cfg):
    out = {}
    for link, groups in cfg.COLLIDERS.items():
        for prefix, tokens in groups:
            targets = [l for l in links if re.fullmatch(link, l)]
            for t in targets:
                pts = src.points(t, tokens, skip=lambda g: (v := variant_of(g, cfg)) is not None
                                 and v[1] != cfg.GEOMETRY_VARIANTS[v[0]][0])
                if len(pts) < 8:
                    continue
                out.setdefault(t, []).append((f"{t}_{prefix}_col", hull_mesh(pts), cfg.PHYSICS_MATERIAL.get(prefix, "structure")))
    return out


def write_geometries(src, path, colliders):
    stage = new_stage(path, default_prim=False)
    layer = stage.GetRootLayer()
    UsdGeom.Scope.Define(stage, "/Geometries")
    for items in src.items.values():
        for g, mesh_path, _m, mat in items:
            UsdGeom.Xform.Define(stage, f"/Geometries/{g}")
            Sdf.CopySpec(src.layer, mesh_path, layer, Sdf.Path(f"/Geometries/{g}/{g}"))
            spec = layer.GetPrimAtPath(f"/Geometries/{g}/{g}")
            for rel in [r for r in spec.relationships if r.name.startswith("material:binding")]:
                spec.RemoveProperty(rel)
            if "apiSchemas" in spec.ListInfoKeys():
                spec.ClearInfo("apiSchemas")
            mesh = UsdGeom.Mesh(stage.GetPrimAtPath(f"/Geometries/{g}/{g}"))
            mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
            if (mat and any(h in mat for h in DOUBLE_SIDED_HINTS)) or is_open(mesh):
                mesh.CreateDoubleSidedAttr().Set(True)
    for cols in colliders.values():
        for name, (pts, counts, idx), _pm in cols:
            UsdGeom.Xform.Define(stage, f"/Geometries/{name}")
            m = UsdGeom.Mesh.Define(stage, f"/Geometries/{name}/{name}")
            m.CreatePointsAttr(pts)
            m.CreateFaceVertexCountsAttr(counts)
            m.CreateFaceVertexIndicesAttr(idx)
            m.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
            m.CreateExtentAttr(UsdGeom.Mesh.ComputeExtent(pts))
            nrm = []
            for k in range(0, len(idx), 3):
                a, b, c = (np.array(pts[i]) for i in idx[k:k + 3])
                n = np.cross(b - a, c - a)
                n = n / (np.linalg.norm(n) + 1e-12)
                nrm += [Gf.Vec3f(*map(float, n))] * 3
            m.CreateNormalsAttr(nrm)
            m.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    layer.Save()


def write_materials(src, path, tex_out):
    stage = new_stage(path, default_prim=False)
    layer = stage.GetRootLayer()
    UsdGeom.Scope.Define(stage, "/Materials")
    names = [c.name for c in src.layer.GetPrimAtPath("/visuals/_materials").nameChildren]
    for n in names:
        Sdf.CopySpec(src.layer, f"/visuals/_materials/{n}", layer, Sdf.Path(f"/Materials/{n}"))
    retarget(layer, "/visuals/_materials", "/Materials")
    os.makedirs(tex_out, exist_ok=True)
    for prim in stage.Traverse():
        if not prim.IsA(UsdShade.Shader):
            continue
        sh = UsdShade.Shader(prim)
        sid = sh.GetIdAttr().Get()
        if sid == "UsdPrimvarReader_float2":
            sh.GetInput("varname").Set("st")
        elif sid == "UsdUVTexture":
            f = sh.GetInput("file")
            fname = os.path.basename(f.Get().path)
            src_file = os.path.join(src.dir, "textures", fname)
            if os.path.exists(src_file):
                shutil.copy(src_file, os.path.join(tex_out, fname))
            f.Set(Sdf.AssetPath(f"./Textures/{fname}"))
            st = sh.GetInput("st")
            conn = st.GetConnectedSource() if st else None
            if conn and UsdShade.Shader(conn[0].GetPrim()).GetIdAttr().Get() == "UsdTransform2d":
                up = UsdShade.Shader(conn[0].GetPrim()).GetInput("in").GetConnectedSource()
                if up:
                    st.ConnectToSource(up[0], up[1])
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdShade.Shader) and UsdShade.Shader(prim).GetIdAttr().Get() == "UsdTransform2d":
            stage.RemovePrim(prim.GetPath())
    layer.Save()
    return names


def write_physics_materials(path, cfg):
    stage = new_stage(path, default_prim=False)
    UsdGeom.Scope.Define(stage, "/PhysicsMaterials")
    for name, (mu_s, mu_d, e) in cfg.PHYSICS_MATERIALS.items():
        m = UsdShade.Material.Define(stage, f"/PhysicsMaterials/{name}")
        api = UsdPhysics.MaterialAPI.Apply(m.GetPrim())
        api.CreateStaticFrictionAttr(mu_s)
        api.CreateDynamicFrictionAttr(mu_d)
        api.CreateRestitutionAttr(e)
        apply_schemas(m.GetPrim(), ["NewtonMaterialAPI"])
        set_attr(m.GetPrim(), "newton:torsionalFriction", Sdf.ValueTypeNames.Float, 0.005)
        set_attr(m.GetPrim(), "newton:rollingFriction", Sdf.ValueTypeNames.Float, 0.0001)
    stage.GetRootLayer().Save()


def write_instances(src, path, colliders):
    stage = new_stage(path, default_prim=False)
    UsdGeom.Scope.Define(stage, "/Instances")
    for items in src.items.values():
        for g, _mp, _m, mat in items:
            inst = UsdGeom.Xform.Define(stage, f"/Instances/{g}").GetPrim()
            inst.GetReferences().AddReference("./geometries.usd", f"/Geometries/{g}")
            if mat:
                UsdGeom.Scope.Define(stage, f"/Instances/{g}/VisualMaterials")
                mp = stage.DefinePrim(f"/Instances/{g}/VisualMaterials/{mat}", "Material")
                mp.GetReferences().AddReference("./materials.usda", f"/Materials/{mat}")
                mp.SetInstanceable(True)
                mesh = stage.OverridePrim(f"/Instances/{g}/{g}")
                UsdShade.MaterialBindingAPI.Apply(mesh).Bind(UsdShade.Material(mp))
    for cols in colliders.values():
        for name, _geo, pmat in cols:
            inst = UsdGeom.Xform.Define(stage, f"/Instances/{name}").GetPrim()
            inst.GetReferences().AddReference("./geometries.usd", f"/Geometries/{name}")
            mesh = stage.OverridePrim(f"/Instances/{name}/{name}")
            UsdPhysics.CollisionAPI.Apply(mesh)
            UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr(UsdPhysics.Tokens.convexHull)
            apply_schemas(mesh, ["NewtonCollisionAPI", "NewtonMeshCollisionAPI", "PhysxConvexHullCollisionAPI"])
            set_attr(mesh, "newton:maxHullVertices", Sdf.ValueTypeNames.Int, 255, uniform=True)
            set_attr(mesh, "physxConvexHullCollision:hullVertexLimit", Sdf.ValueTypeNames.Int, 255)
            UsdGeom.Imageable(mesh).CreatePurposeAttr(UsdGeom.Tokens.guide)
            UsdGeom.Scope.Define(stage, f"/Instances/{name}/PhysicsMaterials")
            pm = stage.DefinePrim(f"/Instances/{name}/PhysicsMaterials/{pmat}", "Material")
            pm.GetReferences().AddReference("./physics_materials.usda", f"/PhysicsMaterials/{pmat}")
            UsdShade.MaterialBindingAPI.Apply(mesh).Bind(UsdShade.Material(pm), UsdShade.Tokens.weakerThanDescendants,
                                                       "physics")
    stage.GetRootLayer().Save()


def _site_xform(site, links):
    o = Gf.Vec3d(*links[site["link"]]["origin"])
    w, x, y, z = site["quat"]
    return Gf.Vec3d(*site["pos"]) - o, Gf.Quatd(w, x, y, z)


def write_base(src, path, links, paths, colliders, sites, cameras, cfg):
    t = Sdf.ValueTypeNames
    stage = new_stage(path, sublayers=["./robot.usda"])
    root = UsdGeom.Xform.Define(stage, ROOT).GetPrim()
    root.SetMetadata("kind", "component")
    root.SetMetadata("assetInfo", {"name": ROOT[1:], "version": assetcfg.version(), "identifier": Sdf.AssetPath(f"./{ROOT[1:]}.usda")})
    root.SetMetadata("documentation", cfg.DOC)
    apply_schemas(root, ["GeomModelAPI", "SemanticsLabelsAPI:class"])
    set_attr(root, "semantics:labels:class", t.TokenArray, cfg.SEMANTIC_CLASS)
    UsdGeom.Scope.Define(stage, f"{ROOT}/Geometry")
    UsdGeom.Scope.Define(stage, f"{ROOT}/Physics")
    UsdGeom.Scope.Define(stage, f"{ROOT}/Materials")
    UsdGeom.Scope.Define(stage, f"{ROOT}/VisualMaterials")
    for name in paths:
        L = links[name]
        po = Gf.Vec3d(*links[L["parent"]]["origin"]) if L["parent"] else Gf.Vec3d(0, 0, 0)
        prim = UsdGeom.Xform.Define(stage, paths[name]).GetPrim()
        xform_ops(prim, Gf.Vec3d(*L["origin"]) - po)
        for g, _mp, m, _mat in src.items.get(name, []):
            inst = stage.DefinePrim(f"{paths[name]}/{g}", "Xform")
            inst.GetReferences().AddReference("./instances.usda", f"/Instances/{g}")
            inst.SetInstanceable(True)
            tf = Gf.Transform(m)
            xform_ops(inst, tf.GetTranslation(), tf.GetRotation().GetQuat(), tf.GetScale())
        for cname, _geo, _pm in colliders.get(name, []):
            inst = stage.DefinePrim(f"{paths[name]}/{cname}", "Xform")
            inst.GetReferences().AddReference("./instances.usda", f"/Instances/{cname}")
            inst.SetInstanceable(True)
            xform_ops(inst)
    for s in sites:
        prim = UsdGeom.Xform.Define(stage, f"{paths[s['link']]}/{s['name']}").GetPrim()
        pos, q = _site_xform(s, links)
        xform_ops(prim, pos, q)
        set_attr(prim, "site:kind", t.Token, s["kind"], custom=True)
        for k, v in s["attrs"].items():
            key = k if ":" in k else f"site:{k}"
            vt = t.Double if isinstance(v, float) else t.Int if isinstance(v, int) and not isinstance(v, bool) else t.String
            set_attr(prim, key, vt, v, custom=True)
        if s["kind"] == "thruster":
            UsdGeom.Imageable(prim).CreatePurposeAttr(UsdGeom.Tokens.guide)
        if s["kind"] == "light":
            a = s["attrs"]
            lux = UsdLux.DiskLight.Define(stage, f"{paths[s['link']]}/{s['name']}/emitter")
            xform_ops(lux.GetPrim(), (0, 0, float(a.get("radius_m", 0.05)) * 0.3 + 0.02), Gf.Quatd(0, 1, 0, 0))
            lux.CreateRadiusAttr(float(a.get("radius_m", 0.05)))
            lux.CreateIntensityAttr(float(a.get("intensity", 30000.0)))
            lux.CreateEnableColorTemperatureAttr(True)
            lux.CreateColorTemperatureAttr(float(a.get("colour_k", 5600.0)))
            UsdLux.ShapingAPI.Apply(lux.GetPrim()).CreateShapingConeAngleAttr(float(a.get("cone_deg", 60.0)))
    for c in cameras:
        o = Gf.Vec3d(*links[c["link"]]["origin"])
        fwd, up = Gf.Vec3d(*c["forward"]), Gf.Vec3d(*c["up"])
        right = Gf.Cross(fwd, up).GetNormalized()
        up = Gf.Cross(right, fwd).GetNormalized()
        rot = Gf.Matrix3d(right[0], right[1], right[2], up[0], up[1], up[2], -fwd[0], -fwd[1], -fwd[2])
        cam = UsdGeom.Camera.Define(stage, f"{paths[c['link']]}/{c['name']}")
        xform_ops(cam.GetPrim(), Gf.Vec3d(*c["pos"]) - o, rot.ExtractRotation().GetQuat())
        cam.CreateFocalLengthAttr(c["focal_mm"])
        cam.CreateHorizontalApertureAttr(c["aperture_mm"][0])
        cam.CreateVerticalApertureAttr(c["aperture_mm"][1])
        cam.CreateFStopAttr(c.get("fstop", 0.0))
        cam.CreateClippingRangeAttr(Gf.Vec2f(*c.get("clip_m", (0.05, 1000.0))))
        set_attr(cam.GetPrim(), "sensor:resolution", t.Int2, Gf.Vec2i(*c.get("resolution", (1920, 1080))), custom=True)
        set_attr(cam.GetPrim(), "sensor:source", t.String, c.get("source", ""), custom=True)
    stage.GetRootLayer().Save()


def write_robot(path, links, paths, sites, joints, root_link, cfg):
    t = Sdf.ValueTypeNames
    stage = new_stage(path)
    root = stage.OverridePrim(ROOT)
    apply_schemas(root, ["IsaacRobotAPI"])
    set_attr(root, "isaac:robotType", t.Token, cfg.ROBOT_TYPE)
    set_attr(root, "isaac:description", t.String, cfg.TITLE)
    set_attr(root, "isaac:namespace", t.String, ROOT[1:])
    set_attr(root, "isaac:license", t.Token, "Other")
    set_attr(root, "isaac:version", t.String, assetcfg.version())
    set_attr(root, "isaac:source", t.String, CREATOR)
    by_link = {}
    for s in sites:
        by_link.setdefault(s["link"], []).append(f"{paths[s['link']]}/{s['name']}")
    order = []
    for n in dfs(links, root_link):
        order.append(paths[n])
        order += by_link.get(n, [])
    rl = root.CreateRelationship("isaac:physics:robotLinks", False)
    rj = root.CreateRelationship("isaac:physics:robotJoints", False)
    for rel, targets in ((rl, order), (rj, [f"{ROOT}/Physics/{j}" for j in joints])):
        for tgt in targets:
            rel.AddTarget(Sdf.Path(tgt))
    for n in links:
        apply_schemas(stage.OverridePrim(paths[n]), ["IsaacLinkAPI"])
    for s in sites:
        sp = stage.OverridePrim(f"{paths[s['link']]}/{s['name']}")
        apply_schemas(sp, ["IsaacSiteAPI"])
        set_attr(sp, "isaac:Description", t.String, s["attrs"].get("description", s["attrs"].get("thruster:notes", s["kind"])))
        set_attr(sp, "isaac:forwardAxis", t.Token, "Z", uniform=True)
    for j, spec in joints.items():
        jp = stage.OverridePrim(f"{ROOT}/Physics/{j}")
        apply_schemas(jp, ["IsaacJointAPI"])
        set_attr(jp, "isaac:actuator", t.BoolArray, [spec.get("role") not in PASSIVE_ROLES | LOCK_ROLES])
    stage.GetRootLayer().Save()


def mass_props(src, links, cfg, state):
    out = {}
    for name, L in links.items():
        pts = src.points(name)
        if L["parent"] is None and getattr(cfg, "MASS", None):
            ms = cfg.MASS[state]
            m = ms["mass"]
            if getattr(cfg, "MASS_IS_TOTAL", False):
                m -= sum((K.get("mass") or 1.0) for n, K in links.items() if K["parent"] is not None)
            com = Gf.Vec3f(ms.get("com_x", 0.0), 0, ms["com_z"])
            if getattr(cfg, "INERTIA_BOX", None):
                sx, sy, sz = cfg.INERTIA_BOX
                out[name] = (m, com, Gf.Vec3f(m / 12 * (sy * sy + sz * sz), m / 12 * (sx * sx + sz * sz), m / 12 * (sx * sx + sy * sy)))
                continue
            r, h = cfg.INERTIA_ENVELOPE
            ixx = m * (3 * r * r + h * h) / 12
            out[name] = (m, com, Gf.Vec3f(ixx, ixx, 0.5 * m * r * r))
            continue
        m = L.get("mass") or 1.0
        if len(pts):
            lo, hi = pts.min(0), pts.max(0)
            com, size = Gf.Vec3f(*((lo + hi) / 2)), [max(float(s), 0.02) for s in hi - lo]
        else:
            com, size = Gf.Vec3f(0, 0, 0), [0.05] * 3
        sx, sy, sz = size
        out[name] = (m, com, Gf.Vec3f(m / 12 * (sy * sy + sz * sz), m / 12 * (sx * sx + sz * sz), m / 12 * (sx * sx + sy * sy)))
    return out


def write_physics(path, links, paths, masses, root_link, loops=()):
    t = Sdf.ValueTypeNames
    stage = new_stage(path)
    for name in dfs(links, root_link):
        prim = stage.OverridePrim(paths[name])
        apis = ["PhysicsRigidBodyAPI", "PhysicsMassAPI"]
        if name == root_link:
            apis += ["PhysicsArticulationRootAPI", "NewtonArticulationRootAPI"]
        apply_schemas(prim, apis)
        m, com, inertia = masses[name]
        set_attr(prim, "physics:mass", t.Float, m)
        set_attr(prim, "physics:centerOfMass", t.Point3f, com)
        set_attr(prim, "physics:diagonalInertia", t.Float3, inertia)
        set_attr(prim, "physics:principalAxes", t.Quatf, Gf.Quatf(1, 0, 0, 0))
        if name == root_link:
            set_attr(prim, "newton:selfCollisionEnabled", t.Bool, False)
    stage.OverridePrim(f"{ROOT}/Physics")

    def joint(name, spec, parent, child, pos0, pos1, loop=False):
        jt = spec["type"]
        kind = {"revolute": "PhysicsRevoluteJoint", "prismatic": "PhysicsPrismaticJoint",
                "spherical": "PhysicsSphericalJoint", "fixed": "PhysicsFixedJoint"}[jt]
        prim = stage.DefinePrim(f"{ROOT}/Physics/{name}", kind)
        prim.CreateRelationship("physics:body0", False).SetTargets([Sdf.Path(paths[parent])])
        prim.CreateRelationship("physics:body1", False).SetTargets([Sdf.Path(paths[child])])
        rot = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1, 0, 0), Gf.Vec3d(*spec.get("axis", (1, 0, 0)))).GetQuat())
        set_attr(prim, "physics:localPos0", t.Point3f, Gf.Vec3f(*pos0))
        set_attr(prim, "physics:localPos1", t.Point3f, Gf.Vec3f(*pos1))
        set_attr(prim, "physics:localRot0", t.Quatf, rot)
        set_attr(prim, "physics:localRot1", t.Quatf, rot)
        if loop:
            set_attr(prim, "physics:excludeFromArticulation", t.Bool, True, uniform=True)
            set_attr(prim, "joint:role", t.Token, "loop_closure", uniform=True, custom=True)
        if jt == "spherical" and not loop:
            set_attr(prim, "joint:role", t.Token, spec.get("role", "passive"), uniform=True, custom=True)
            set_attr(prim, "joint:driveKind", t.Token, "none", uniform=True, custom=True)
        if jt == "spherical" and "cone" in spec:
            set_attr(prim, "physics:axis", t.Token, "X", uniform=True)
            set_attr(prim, "physics:coneAngle0Limit", t.Float, float(spec["cone"]))
            set_attr(prim, "physics:coneAngle1Limit", t.Float, float(spec["cone"]))
        if jt in ("fixed", "spherical"):
            return
        set_attr(prim, "physics:axis", t.Token, "X", uniform=True)
        angular = jt == "revolute"
        sc = DEG if angular else 1.0
        if "limit" in spec:
            lo, hi = spec["limit"]
            set_attr(prim, "physics:lowerLimit", t.Float, lo * sc)
            set_attr(prim, "physics:upperLimit", t.Float, hi * sc)
        if loop:
            return
        set_attr(prim, "joint:role", t.Token, spec.get("role", "actuated"), uniform=True, custom=True)
        set_attr(prim, "joint:driveKind", t.Token, spec.get("drive", {}).get("kind", "none"), uniform=True, custom=True)
        tok = "angular" if angular else "linear"
        apply_schemas(prim, [f"PhysicsJointStateAPI:{tok}", f"PhysicsDriveAPI:{tok}"])
        set_attr(prim, f"state:{tok}:physics:position", t.Float, 0.0)
        set_attr(prim, f"state:{tok}:physics:velocity", t.Float, 0.0)
        d = spec.get("drive", {"stiffness": 0.0, "damping": 0.0, "max_force": 1e6})
        base = f"drive:{tok}:physics:"
        set_attr(prim, base + "type", t.Token, "force", uniform=True)
        set_attr(prim, base + "stiffness", t.Float, d.get("stiffness", 0.0) / sc)
        set_attr(prim, base + "damping", t.Float, d.get("damping", 0.0) / sc)
        set_attr(prim, base + "maxForce", t.Float, d.get("max_force", 1000.0))
        set_attr(prim, base + "targetPosition", t.Float, d.get("target", 0.0) * sc)
        set_attr(prim, base + "targetVelocity", t.Float, d.get("target_velocity", 0.0) * sc)

    joints = {}
    for name in dfs(links, root_link)[1:]:
        L = links[name]
        po, co = Gf.Vec3d(*links[L["parent"]]["origin"]), Gf.Vec3d(*L["origin"])
        joint(name, L["joint"], L["parent"], name, co - po, (0, 0, 0))
        joints[name] = L["joint"]
    for lp in loops:
        po, co = Gf.Vec3d(*links[lp["parent"]]["origin"]), Gf.Vec3d(*links[lp["child"]]["origin"])
        a = Gf.Vec3d(*lp["anchor"])
        joint(lp["name"], {"type": lp["type"], "axis": lp["axis"]}, lp["parent"], lp["child"], a - po, a - co, loop=True)
    stage.GetRootLayer().Save()
    return joints


def write_physx(path, joints, paths, root_link):
    t = Sdf.ValueTypeNames
    stage = new_stage(path, sublayers=["./physics.usda"])
    ch = stage.OverridePrim(paths[root_link])
    apply_schemas(ch, ["PhysxArticulationAPI"])
    set_attr(ch, "physxArticulation:enabledSelfCollisions", t.Bool, False)
    set_attr(ch, "physxArticulation:solverPositionIterationCount", t.Int, 32)
    set_attr(ch, "physxArticulation:solverVelocityIterationCount", t.Int, 1)
    for j, spec in joints.items():
        if spec["type"] in ("fixed", "spherical"):
            continue
        jp = stage.OverridePrim(f"{ROOT}/Physics/{j}")
        apply_schemas(jp, ["PhysxJointAPI"])
        set_attr(jp, "physxJoint:maxJointVelocity", t.Float, 2.0 if spec["type"] == "prismatic" else 180.0)
    stage.GetRootLayer().Save()


def write_mujoco(path, joints):
    t = Sdf.ValueTypeNames
    stage = new_stage(path, sublayers=["./physics.usda"])
    for j, spec in joints.items():
        if spec["type"] in ("fixed", "spherical"):
            continue
        jp = stage.OverridePrim(f"{ROOT}/Physics/{j}")
        apply_schemas(jp, ["MjcJointAPI"])
        set_attr(jp, "mjc:armature", t.Double, 0.01, uniform=True)
        d = spec.get("drive")
        if not d or spec.get("role") in PASSIVE_ROLES:
            continue
        tok = "angular" if spec["type"] == "revolute" else "linear"
        jp.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(
            deletedItems=[f"PhysicsDriveAPI:{tok}", f"PhysicsJointStateAPI:{tok}"], prependedItems=["MjcJointAPI"]))
        act = stage.DefinePrim(f"{ROOT}/Physics/{j}_actuator", "MjcActuator")
        act.CreateRelationship("mjc:target", False).SetTargets([jp.GetPath()])
        f = d.get("max_force", 1000.0)
        set_attr(act, "mjc:forceRange:min", t.Double, -f, uniform=True)
        set_attr(act, "mjc:forceRange:max", t.Double, f, uniform=True)
        set_attr(act, "mjc:forceLimited", t.Token, "true", uniform=True)
        kp, kd = d.get("stiffness", 0.0), d.get("damping", 0.0)
        gain, bias = ([kd], [0.0, 0.0, -kd]) if kp == 0.0 else ([kp], [0.0, -kp, -kd])
        set_attr(act, "mjc:gainPrm", t.DoubleArray, gain + [0.0] * (10 - len(gain)), uniform=True)
        set_attr(act, "mjc:biasType", t.Token, "affine", uniform=True)
        set_attr(act, "mjc:biasPrm", t.DoubleArray, bias + [0.0] * (10 - len(bias)), uniform=True)
    stage.GetRootLayer().Save()


def write_propellant(out_dir, src, links, paths, cfg, root_link):
    t = Sdf.ValueTypeNames
    for state in cfg.MASS:
        st = new_stage(os.path.join(out_dir, f"{state}.usda"))
        prim = st.OverridePrim(paths[root_link])
        m, com, inertia = mass_props(src, links, cfg, state)[root_link]
        set_attr(prim, "physics:mass", t.Float, m)
        set_attr(prim, "physics:centerOfMass", t.Point3f, com)
        set_attr(prim, "physics:diagonalInertia", t.Float3, inertia)
        set_attr(prim, "propellant:source", t.String, cfg.MASS[state]["source"], custom=True)
        st.GetRootLayer().Save()


def write_fidelity(out_dir, src, lods, paths):
    full = new_stage(os.path.join(out_dir, "full.usda"))
    full.OverridePrim(ROOT)
    full.GetRootLayer().Save()
    for lod, lsrc in lods.items():
        st = new_stage(os.path.join(out_dir, f"{lod}.usd"))
        layer = st.GetRootLayer()
        st.OverridePrim(ROOT)
        for link, items in src.items.items():
            for g, *_ in items:
                st.OverridePrim(f"{paths[link]}/{g}").SetActive(False)
        looks = f"{ROOT}/{lod.capitalize()}Looks"
        UsdGeom.Scope.Define(st, looks)
        for m in lsrc.layer.GetPrimAtPath("/visuals/_materials").nameChildren:
            Sdf.CopySpec(lsrc.layer, m.path, layer, Sdf.Path(f"{looks}/{m.name}"))
        for link, items in lsrc.items.items():
            holder = f"{paths[link]}/{lod}_visuals"
            UsdGeom.Xform.Define(st, holder)
            for g, mesh_path, m, _mat in items:
                Sdf.CopySpec(lsrc.layer, mesh_path, layer, Sdf.Path(f"{holder}/{g}"))
                tf = Gf.Transform(m)
                xform_ops(st.GetPrimAtPath(f"{holder}/{g}"), tf.GetTranslation(), tf.GetRotation().GetQuat(), tf.GetScale())
        retarget(layer, "/visuals/_materials", looks)
        layer.Save()


def write_articulation(out_dir, links, paths, joints, root_link, loops=()):
    art = new_stage(os.path.join(out_dir, "articulated.usda"))
    art.OverridePrim(ROOT)
    art.GetRootLayer().Save()
    st = new_stage(os.path.join(out_dir, "rigid.usda"))
    st.OverridePrim(ROOT)
    for name in links:
        if name != root_link:
            st.OverridePrim(paths[name]).SetMetadata("apiSchemas", Sdf.TokenListOp.Create(deletedItems=["PhysicsRigidBodyAPI", "PhysicsMassAPI"]))
    for j in list(joints) + [lp["name"] for lp in loops]:
        for prim in (f"{ROOT}/Physics/{j}", f"{ROOT}/Physics/{j}_actuator"):
            st.OverridePrim(prim).SetActive(False)
    st.GetRootLayer().Save()


def variant_of(g, cfg):
    for set_name, options in getattr(cfg, "GEOMETRY_VARIANTS", {}).items():
        for o in options:
            if g.endswith(f"__{set_name}_{o}") or f"__{set_name}_{o}_" in g:
                return set_name, o
    return None


def write_geometry_variants(pay, cfg, src, paths):
    for set_name, options in getattr(cfg, "GEOMETRY_VARIANTS", {}).items():
        for opt in options:
            st = new_stage(os.path.join(pay, set_name, f"{opt}.usda"))
            st.OverridePrim(ROOT)
            for link, items in src.items.items():
                for g, *_ in items:
                    v = variant_of(g, cfg)
                    if v and v[0] == set_name and v[1] != opt:
                        st.OverridePrim(f"{paths[link]}/{g}").SetActive(False)
            for j, q in getattr(cfg, "GEOMETRY_VARIANT_JOINTS", {}).get(set_name, {}).get(opt, {}).items():
                jp = st.OverridePrim(f"{ROOT}/Physics/{j}")
                set_attr(jp, "drive:angular:physics:targetPosition", Sdf.ValueTypeNames.Float, q * DEG)
                set_attr(jp, "state:angular:physics:position", Sdf.ValueTypeNames.Float, q * DEG)
            st.GetRootLayer().Save()


def write_joint_variants(pay, cfg, joints):
    t = Sdf.ValueTypeNames
    for set_name, options in getattr(cfg, "JOINT_VARIANTS", {}).items():
        for opt, rules in options.items():
            st = new_stage(os.path.join(pay, set_name, f"{opt}.usda"))
            st.OverridePrim(ROOT)
            for pattern, o in rules.items():
                for j, spec in joints.items():
                    if not re.fullmatch(pattern, j) or spec["type"] not in ("prismatic", "revolute"):
                        continue
                    jp = st.OverridePrim(f"{ROOT}/Physics/{j}")
                    angular = spec["type"] == "revolute"
                    sc, tok = (DEG, "angular") if angular else (1.0, "linear")
                    if "limit" in o:
                        set_attr(jp, "physics:lowerLimit", t.Float, o["limit"][0] * sc)
                        set_attr(jp, "physics:upperLimit", t.Float, o["limit"][1] * sc)
                        set_attr(jp, "newton:limitStiffness", t.Float, o.get("limit_ke", 1.0e7))
                        set_attr(jp, "newton:limitDamping", t.Float, o.get("limit_kd", 1.0e5))
                    if "drive" in o:
                        d = o["drive"]
                        set_attr(jp, "joint:driveKind", t.Token, d.get("kind", "none"), uniform=True, custom=True)
                        set_attr(jp, f"drive:{tok}:physics:stiffness", t.Float, d.get("stiffness", 0.0) / sc)
                        set_attr(jp, f"drive:{tok}:physics:damping", t.Float, d.get("damping", 0.0) / sc)
                        set_attr(jp, f"drive:{tok}:physics:maxForce", t.Float, d.get("max_force", 1e6))
                    f = o.get("friction", 0.0)
                    set_attr(jp, "newton:friction", t.Float, f)
                    set_attr(jp, "mjc:frictionloss", t.Double, f, uniform=True)
                    if f:
                        set_attr(jp, "mjc:solreffriction", t.Double2, Gf.Vec2d(*o.get("friction_solref", (0.004, 1.0))))
                        set_attr(jp, "mjc:solimpfriction", t.DoubleArray, list(o.get("friction_solimp", (0.9999, 0.9999, 0.001, 0.5, 2.0))))
                    if "armature" in o:
                        set_attr(jp, "newton:armature", t.Float, o["armature"])
                        set_attr(jp, "mjc:armature", t.Double, o["armature"], uniform=True)
                    if "stage_load" in o:
                        set_attr(jp, "joint:crushLoad", t.Float, o["stage_load"], uniform=True, custom=True)
            st.GetRootLayer().Save()


def write_lights(pay, sites, paths):
    lights = [s for s in sites if s["kind"] == "light"]
    if not lights:
        return False
    for opt in ("on", "off"):
        st = new_stage(os.path.join(pay, "Lights", f"{opt}.usda"))
        st.OverridePrim(ROOT)
        if opt == "off":
            for s in lights:
                st.OverridePrim(f"{paths[s['link']]}/{s['name']}/emitter").SetActive(False)
        st.GetRootLayer().Save()
    return True


def write_attachments(pay, cfg, links, paths, sites):
    t = Sdf.ValueTypeNames
    for set_name, options in getattr(cfg, "ATTACHMENTS", {}).items():
        for opt, (dep, mount_site, dep_site) in options.items():
            dep_pkg = os.path.join(assetcfg.ROOT, "build", dep, "usd", dep)
            if not os.path.exists(os.path.join(dep_pkg, f"{dep}.usda")):
                raise SystemExit(f"attachment {dep} is not packaged yet: run ./pipeline.sh {dep} first")
            dst = os.path.join(pay, "attachments", dep)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(dep_pkg, dst)
            with open(os.path.join(assetcfg.ROOT, "build", dep, "export", "full", "asset.json")) as f:
                dg = json.load(f)
            dep_root = next(n for n, L in dg["links"].items() if L["parent"] is None)
            ds = next(x for x in dg["sites"] if x["name"] == dep_site)
            ms = next(x for x in sites if x["name"] == mount_site)
            link = ms["link"]
            rel = Gf.Vec3d(*ms["pos"]) - Gf.Vec3d(*links[link]["origin"]) - Gf.Vec3d(*ds["pos"])
            st = new_stage(os.path.join(pay, set_name, f"{opt}.usda"))
            st.OverridePrim(ROOT)
            holder = f"{paths[link]}/{dep}"
            att = st.DefinePrim(holder, "Xform")
            att.GetReferences().AddReference(f"../attachments/{dep}/{dep}.usda")
            att.SetMetadata("kind", "subcomponent")
            xform_ops(att, rel)
            att.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(deletedItems=["IsaacRobotAPI"]))
            droot = st.OverridePrim(f"{holder}/Geometry/{dep_root}")
            droot.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(
                deletedItems=["PhysicsArticulationRootAPI", "NewtonArticulationRootAPI", "PhysxArticulationAPI"]))
            j = st.DefinePrim(f"{ROOT}/Physics/{dep}_mount", "PhysicsFixedJoint")
            j.CreateRelationship("physics:body0", False).SetTargets([Sdf.Path(paths[link])])
            j.CreateRelationship("physics:body1", False).SetTargets([Sdf.Path(f"{holder}/Geometry/{dep_root}")])
            set_attr(j, "physics:localPos0", t.Point3f, Gf.Vec3f(rel))
            set_attr(j, "physics:localPos1", t.Point3f, Gf.Vec3f(0, 0, 0))
            set_attr(j, "physics:localRot0", t.Quatf, Gf.Quatf(1, 0, 0, 0))
            set_attr(j, "physics:localRot1", t.Quatf, Gf.Quatf(1, 0, 0, 0))
            st.GetRootLayer().Save()


def write_interface(path, cfg, links, extents, lods):
    stage = new_stage(path)
    layer = stage.GetRootLayer()
    root = stage.DefinePrim(ROOT, "Xform")
    root.GetReferences().AddReference("./payloads/base.usda")
    sets = [
        ("Physics", {"none": None, "physics": "Physics/physics.usda", "physx": "Physics/physx.usda", "mujoco": "Physics/mujoco.usda"}, "physx"),
        ("Fidelity", {"none": None, "full": "Fidelity/full.usda", **{lod: f"Fidelity/{lod}.usd" for lod in lods}}, "full"),
        ("Articulation", {"articulated": "Articulation/articulated.usda", "rigid": "Articulation/rigid.usda"}, "articulated"),
    ]
    if getattr(cfg, "MASS", None):
        ms = getattr(cfg, "MASS_SET", "Propellant")
        sets.append((ms, {"none": None, **{s: f"Propellant/{s}.usda" for s in cfg.MASS}}, cfg.DEFAULT_MASS_STATE))
    for set_name, options in getattr(cfg, "GEOMETRY_VARIANTS", {}).items():
        sets.append((set_name, {o: f"{set_name}/{o}.usda" for o in options}, options[0]))
    if os.path.exists(os.path.join(os.path.dirname(path), "payloads", "Lights", "off.usda")):
        sets.append(("Lights", {"on": "Lights/on.usda", "off": "Lights/off.usda"}, "on"))
    for set_name, options in getattr(cfg, "JOINT_VARIANTS", {}).items():
        sets.append((set_name, {o: f"{set_name}/{o}.usda" for o in options}, next(iter(options))))
    for set_name, options in getattr(cfg, "ATTACHMENTS", {}).items():
        sets.append((set_name, {"none": None, **{o: f"{set_name}/{o}.usda" for o in options}}, "none"))
    weakest = ("Fidelity", "Physics")
    sets = [x for x in sets if x[0] not in weakest] + [x for w in weakest for x in sets if x[0] == w]
    for set_name, options, default in sets:
        vs = root.GetVariantSets().AddVariantSet(set_name)
        for opt, payload in options.items():
            vs.AddVariant(opt)
            if payload:
                vs.SetVariantSelection(opt)
                with vs.GetVariantEditContext():
                    root.GetPayloads().AddPayload(f"./payloads/{payload}")
        vs.SetVariantSelection(default)
    today = datetime.date.today().isoformat()
    meta = {"asset_name": ROOT[1:], "asset_version": assetcfg.version(), "usd_version": ".".join(map(str, Usd.GetVersion())),
            "asset_type": "robot", "category": "spacecraft", "asset_license": "CC-BY-4.0",
            "source_file": f"build/{ROOT[1:]}/{ROOT[1:]}.blend (scripts/build.py)", "usd_date_generated": today,
            "rigid_body_count": len(links), "asset_extents": Gf.Vec3f(*extents),
            "mass": float(cfg.MASS[cfg.DEFAULT_MASS_STATE]["mass"]) if getattr(cfg, "MASS", None)
            else float(sum((L.get("mass") or 1.0) for L in links.values()))}
    layer.customLayerData = {"creator": CREATOR, "asset_name": ROOT[1:], "asset_version": assetcfg.version(), "asset_type": "robot",
                             "usd_date_generated": today, "SimReady_Metadata": meta}
    layer.Save()


def finish_extents(asset_dir, asset):
    stage = Usd.Stage.Open(os.path.join(asset_dir, f"{asset}.usda"))
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), UsdGeom.Imageable.GetOrderedPurposeTokens())
    hint = UsdGeom.ModelAPI(stage.GetPrimAtPath(ROOT)).ComputeExtentsHint(cache)
    vis = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    rng = vis.ComputeWorldBound(stage.GetPrimAtPath(ROOT)).ComputeAlignedRange()
    base = Usd.Stage.Open(os.path.join(asset_dir, "payloads", "base.usda"))
    UsdGeom.ModelAPI(base.GetPrimAtPath(ROOT)).SetExtentsHint(hint)
    base.GetRootLayer().Save()
    return tuple(rng.GetSize())


def write_thrusters(path, sites, links, paths):
    out = []
    for s in sites:
        if s["kind"] != "thruster":
            continue
        a = s["attrs"]
        w, x, y, z = s["quat"]
        flow = Gf.Rotation(Gf.Quatd(w, x, y, z)).TransformDir(Gf.Vec3d(0, 0, 1))
        out.append({"name": s["name"], "prim": f"{paths[s['link']]}/{s['name']}", "link": s["link"],
                    "exit_center_m": s["pos"], "flow_dir": [round(c, 6) for c in flow], "thrust_dir": [round(-c, 6) for c in flow],
                    **{k.split(":", 1)[1]: v for k, v in a.items()}})
    with open(path, "w") as f:
        json.dump({"frame": "asset root at rest pose (Z up, metres); site +Z = exhaust flow direction",
                   "thrusters": out}, f, indent=1)
    return out


def main():
    global ROOT
    argv = sys.argv[1:]
    asset = assetcfg.arg(argv, "--asset")
    cfg = assetcfg.load(asset)
    ROOT = f"/{asset}"
    exp = assetcfg.build_dir(asset, "export")
    out = os.path.join(assetcfg.ROOT, "build", asset, "usd", asset)
    if os.path.exists(out):
        shutil.rmtree(out)
    pay = os.path.join(out, "payloads")
    os.makedirs(pay)
    src = Source(os.path.join(exp, "full"))
    lods = {lod: Source(os.path.join(exp, lod)) for lod in ("simple", "proxy")
            if os.path.exists(os.path.join(exp, lod, "visuals.usdc"))}
    with open(os.path.join(exp, "full", "asset.json")) as f:
        graph = json.load(f)
    links, sites, cameras = graph["links"], graph["sites"], graph["cameras"]
    root_link = next(n for n, L in links.items() if L["parent"] is None)
    paths = link_paths(links, root_link)
    colliders = collider_specs(src, links, cfg)

    write_geometries(src, os.path.join(pay, "geometries.usd"), colliders)
    write_materials(src, os.path.join(pay, "materials.usda"), os.path.join(pay, "Textures"))
    write_physics_materials(os.path.join(pay, "physics_materials.usda"), cfg)
    write_instances(src, os.path.join(pay, "instances.usda"), colliders)
    masses = mass_props(src, links, cfg, getattr(cfg, "DEFAULT_MASS_STATE", None))
    joints = write_physics(os.path.join(pay, "Physics", "physics.usda"), links, paths, masses, root_link, graph.get("loops", []))
    write_physx(os.path.join(pay, "Physics", "physx.usda"), joints, paths, root_link)
    write_mujoco(os.path.join(pay, "Physics", "mujoco.usda"), joints)
    write_robot(os.path.join(pay, "robot.usda"), links, paths, sites, joints, root_link, cfg)
    write_base(src, os.path.join(pay, "base.usda"), links, paths, colliders, sites, cameras, cfg)
    if getattr(cfg, "MASS", None):
        write_propellant(os.path.join(pay, "Propellant"), src, links, paths, cfg, root_link)
    write_attachments(pay, cfg, links, paths, sites)
    write_fidelity(os.path.join(pay, "Fidelity"), src, lods, paths)
    write_articulation(os.path.join(pay, "Articulation"), links, paths, joints, root_link, graph.get("loops", []))
    write_geometry_variants(pay, cfg, src, paths)
    write_lights(pay, sites, paths)
    write_joint_variants(pay, cfg, joints)
    write_interface(os.path.join(out, f"{asset}.usda"), cfg, links, (0, 0, 0), lods)
    extents = finish_extents(out, asset)
    write_interface(os.path.join(out, f"{asset}.usda"), cfg, links, extents, lods)
    thr = write_thrusters(os.path.join(out, "thrusters.json"), sites, links, paths)
    thumb = os.path.join(assetcfg.ROOT, "build", asset, "renders", "thumb_256.png")
    if os.path.exists(thumb):
        os.makedirs(os.path.join(out, ".thumbs", "256x256"), exist_ok=True)
        shutil.copy(thumb, os.path.join(out, ".thumbs", "256x256", f"{asset}.usda.png"))
    ncol = sum(len(v) for v in colliders.values())
    print(f"packaged {asset}: {len(links)} links, {len(joints)} joints, {len(sites)} sites ({len(thr)} thrusters), "
          f"{len(cameras)} cameras, {ncol} colliders, extents {tuple(round(e, 2) for e in extents)} -> {out}")


if __name__ == "__main__":
    main()
