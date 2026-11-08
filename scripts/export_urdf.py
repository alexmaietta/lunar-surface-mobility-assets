import json
import math
import os
import shutil
import sys
from xml.dom import minidom
from xml.etree import ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade

DEFAULT_VELOCITY = {"revolute": 2 * math.pi, "continuous": 2 * math.pi, "prismatic": 0.5}


def fmt(v):
    return " ".join(f"{x:.6g}" for x in v)


def link_meshes(stage, link):
    group = stage.GetPrimAtPath(f"/visuals/L_{link}")
    if not group:
        return []
    out = []
    for prim in Usd.PrimRange(group):
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(prim)
        mat = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()[0]
        st = UsdGeom.PrimvarsAPI(prim).GetPrimvar("st")
        out.append({"points": np.array(mesh.GetPointsAttr().Get(), float), "counts": list(mesh.GetFaceVertexCountsAttr().Get()),
                    "indices": list(mesh.GetFaceVertexIndicesAttr().Get()),
                    "st": np.array(st.Get(), float) if st and st.Get() is not None else None,
                    "st_interp": st.GetInterpolation() if st else None,
                    "st_indices": list(st.GetIndices()) if st and st.IsIndexed() else None,
                    "material": mat.GetPrim().GetName() if mat else "default", "mat_prim": mat.GetPrim() if mat else None})
    return out


def material_info(mat_prim, tex_names):
    colour, texture = (0.6, 0.6, 0.6), None
    if mat_prim is None:
        return colour, texture
    for p in Usd.PrimRange(mat_prim):
        sid = p.GetAttribute("info:id").Get() if p.HasAttribute("info:id") else None
        if sid == "UsdPreviewSurface":
            a = p.GetAttribute("inputs:diffuseColor")
            if a and a.Get() is not None and not a.HasAuthoredConnections():
                colour = tuple(a.Get())
        if sid == "UsdUVTexture":
            f = p.GetAttribute("inputs:file").Get()
            name = os.path.basename(f.path) if f else ""
            if "basecolor" in name and name in tex_names:
                texture = name
    return colour, texture


def write_obj(path, meshes, mtl_name):
    lines = [f"mtllib {mtl_name}"]
    v_off = vt_off = 1
    for i, m in enumerate(meshes):
        lines.append(f"o part_{i}")
        lines += [f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in m["points"]]
        uv = None
        if m["st"] is not None and m["st_interp"] in ("faceVarying", "vertex"):
            uv = m["st"] if m["st_indices"] is None else m["st"][m["st_indices"]]
            lines += [f"vt {u[0]:.6f} {u[1]:.6f}" for u in uv]
        lines.append(f"usemtl {m['material']}")
        k = 0
        for c in m["counts"]:
            ids = m["indices"][k:k + c]
            if uv is None:
                lines.append("f " + " ".join(str(v_off + i) for i in ids))
            elif m["st_interp"] == "faceVarying":
                lines.append("f " + " ".join(f"{v_off + i}/{vt_off + k + j}" for j, i in enumerate(ids)))
            else:
                lines.append("f " + " ".join(f"{v_off + i}/{vt_off + i}" for i in ids))
            k += c
        v_off += len(m["points"])
        if uv is not None:
            vt_off += len(uv)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_mtl(path, materials, tex_rel):
    lines = []
    for name, (colour, texture) in sorted(materials.items()):
        lines += [f"newmtl {name}", "Ka 0 0 0", f"Kd {colour[0]:.4f} {colour[1]:.4f} {colour[2]:.4f}", "Ks 0.1 0.1 0.1", "Ns 50", "d 1"]
        if texture:
            lines.append(f"map_Kd {tex_rel}/{texture}")
        lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))


COMPOUND_MIN = 8


def collider_meshes(stage, link_path, link_names):
    out = []
    it = iter(Usd.PrimRange(stage.GetPrimAtPath(link_path), Usd.TraverseInstanceProxies()))
    for prim in it:
        if prim.GetPath() != link_path and prim.GetName() in link_names:
            it.PruneChildren()
            continue
        if prim.IsA(UsdGeom.Mesh) and prim.HasAPI(UsdPhysics.CollisionAPI):
            mesh = UsdGeom.Mesh(prim)
            rel = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0) * \
                UsdGeom.Xformable(stage.GetPrimAtPath(link_path)).ComputeLocalToWorldTransform(0).GetInverse()
            pts = np.array([rel.Transform(Gf.Vec3d(*p)) for p in mesh.GetPointsAttr().Get()], float)
            out.append({"name": prim.GetName(), "points": pts, "counts": list(mesh.GetFaceVertexCountsAttr().Get()),
                        "indices": list(mesh.GetFaceVertexIndicesAttr().Get()), "st": None, "st_interp": None, "st_indices": None,
                        "material": "collision"})
    return out


def inertial(prim):
    mp = UsdPhysics.MassAPI(prim)
    mass = mp.GetMassAttr().Get() or 0.0
    com = mp.GetCenterOfMassAttr().Get() or Gf.Vec3f(0, 0, 0)
    diag = mp.GetDiagonalInertiaAttr().Get() or Gf.Vec3f(0, 0, 0)
    axes = mp.GetPrincipalAxesAttr().Get() or Gf.Quatf(1, 0, 0, 0)
    r = np.array(Gf.Matrix3d().SetRotate(Gf.Quatd(axes)))
    tensor = r.T @ np.diag(np.array(diag, float)) @ r
    return float(mass), tuple(com), tensor


def mimic_four_bar(links, loops):
    mimic = {}
    for lp in loops:
        upper, upright = lp["parent"], lp["child"]
        lower = links[upright]["parent"]
        if links[upper]["parent"] != links[lower]["parent"]:
            continue
        mimic[upper] = (lower, 1.0)
        mimic[upright] = (lower, -1.0)
    return mimic


def main(argv):
    asset = assetcfg.arg(argv, "--asset")
    cfg = assetcfg.load(asset)
    if not getattr(cfg, "URDF", False) and "--force" not in argv:
        print(f"urdf {asset}: skipped (set URDF = True in configs/{asset}.py)")
        return
    root_dir = os.path.join(assetcfg.ROOT, "assets", cfg.ASSET_PATH)
    build = os.path.join(assetcfg.ROOT, "build", asset)
    with open(os.path.join(build, "export", "full", "asset.json")) as f:
        graph = json.load(f)
    links, loops = graph["links"], graph.get("loops", [])
    visuals = Usd.Stage.Open(os.path.join(build, "export", "full", "visuals.usdc"))
    usd = Usd.Stage.Open(os.path.join(build, "usd", asset, f"{asset}.usda"))
    paths = {p.GetName(): p.GetPath() for p in usd.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI) or p.HasAPI(UsdPhysics.MassAPI)}
    out = os.path.join(root_dir, "urdf")
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "meshes", "visual"))
    os.makedirs(os.path.join(out, "meshes", "collision"))
    tex_dir = os.path.join(root_dir, "obj")
    tex_names = set(os.listdir(tex_dir)) if os.path.isdir(tex_dir) else set()
    mimic = mimic_four_bar(links, loops)

    robot = ET.Element("robot", name=asset)
    root_link = next(n for n, L in links.items() if L["parent"] is None)
    order = [root_link]
    for n in order:
        order += sorted(c for c, L in links.items() if L["parent"] == n)
    ET.SubElement(robot, "link", name="base_link")
    j = ET.SubElement(robot, "joint", name=f"base_link_to_{root_link}", type="fixed")
    ET.SubElement(j, "parent", link="base_link")
    ET.SubElement(j, "child", link=root_link)
    ET.SubElement(j, "origin", xyz=fmt(links[root_link]["origin"]), rpy="0 0 0")
    n_tris = 0
    for name in order:
        L = links[name]
        link = ET.SubElement(robot, "link", name=name)
        if name in paths:
            mass, com, tensor = inertial(usd.GetPrimAtPath(paths[name]))
            if mass > 0:
                ine = ET.SubElement(link, "inertial")
                ET.SubElement(ine, "origin", xyz=fmt(com), rpy="0 0 0")
                ET.SubElement(ine, "mass", value=f"{mass:.6g}")
                ET.SubElement(ine, "inertia", ixx=f"{tensor[0, 0]:.6g}", ixy=f"{tensor[0, 1]:.6g}", ixz=f"{tensor[0, 2]:.6g}",
                              iyy=f"{tensor[1, 1]:.6g}", iyz=f"{tensor[1, 2]:.6g}", izz=f"{tensor[2, 2]:.6g}")
        meshes = link_meshes(visuals, name)
        if meshes:
            mats = {m["material"]: material_info(m["mat_prim"], tex_names) for m in meshes}
            write_obj(os.path.join(out, "meshes", "visual", f"{name}.obj"), meshes, f"{name}.mtl")
            write_mtl(os.path.join(out, "meshes", "visual", f"{name}.mtl"), mats, "../../../obj")
            n_tris += sum(sum(c - 2 for c in m["counts"]) for m in meshes)
            vis = ET.SubElement(link, "visual")
            ET.SubElement(vis, "origin", xyz="0 0 0", rpy="0 0 0")
            ET.SubElement(ET.SubElement(vis, "geometry"), "mesh", filename=f"meshes/visual/{name}.obj")
        if name in paths:
            cols = collider_meshes(usd, paths[name], set(links))
            groups = [(f"{name}_compound_col", cols)] if len(cols) > COMPOUND_MIN else [(c["name"], [c]) for c in cols]
            for cname, parts in groups:
                fn = f"{cname}.obj"
                write_obj(os.path.join(out, "meshes", "collision", fn), parts, "collision.mtl")
                col = ET.SubElement(link, "collision", name=cname)
                ET.SubElement(col, "origin", xyz="0 0 0", rpy="0 0 0")
                ET.SubElement(ET.SubElement(col, "geometry"), "mesh", filename=f"meshes/collision/{fn}")
        if L["parent"] is None:
            continue
        J = L["joint"]
        jt = J["type"]
        if jt == "revolute" and "limit" not in J:
            jt = "continuous"
        joint = ET.SubElement(robot, "joint", name=name, type=jt)
        ET.SubElement(joint, "parent", link=L["parent"])
        ET.SubElement(joint, "child", link=name)
        rel = np.array(L["origin"]) - np.array(links[L["parent"]]["origin"])
        ET.SubElement(joint, "origin", xyz=fmt(rel), rpy="0 0 0")
        if jt != "fixed":
            ET.SubElement(joint, "axis", xyz=fmt(J["axis"]))
            drive = J.get("drive") or {}
            effort = float(drive.get("max_force") or 1000.0)
            velocity = float(drive.get("max_velocity") or DEFAULT_VELOCITY.get(jt, 1.0))
            attrs = {"effort": f"{effort:.6g}", "velocity": f"{velocity:.6g}"}
            if jt in ("revolute", "prismatic"):
                attrs.update(lower=f"{J['limit'][0]:.6g}", upper=f"{J['limit'][1]:.6g}")
            ET.SubElement(joint, "limit", **attrs)
            ET.SubElement(joint, "dynamics", damping=f"{float(drive.get('damping') or 0.0):.6g}", friction="0")
            if name in mimic:
                ET.SubElement(joint, "mimic", joint=mimic[name][0], multiplier=f"{mimic[name][1]:g}", offset="0")
    frames = [(c["name"], c["link"], c["pos"], c["forward"], c.get("up", (0, 0, 1))) for c in graph.get("cameras", [])]
    for s in graph.get("sites", []):
        if s["kind"] in ("light", "sensor", "tool", "antenna"):
            q = Gf.Quatd(*s["quat"])
            z = Gf.Rotation(q).TransformDir(Gf.Vec3d(0, 0, 1))
            frames.append((s["name"], s["link"], s["pos"], tuple(z), None))
    for fname, parent, pos, fwd, up in frames:
        fl = f"{fname}_frame"
        ET.SubElement(robot, "link", name=fl)
        j = ET.SubElement(robot, "joint", name=f"{fl}_joint", type="fixed")
        ET.SubElement(j, "parent", link=parent)
        ET.SubElement(j, "child", link=fl)
        fwd = np.array(fwd, float) / np.linalg.norm(fwd)
        yaw = math.atan2(fwd[1], fwd[0])
        pitch = -math.asin(max(-1.0, min(1.0, fwd[2])))
        ET.SubElement(j, "origin", xyz=fmt(np.array(pos) - np.array(links[parent]["origin"])), rpy=fmt((0.0, pitch, yaw)))
    with open(os.path.join(out, "meshes", "collision", "collision.mtl"), "w") as f:
        f.write("newmtl collision\nKd 0.8 0.3 0.1\n")
    xml = minidom.parseString(ET.tostring(robot)).toprettyxml(indent="  ")
    with open(os.path.join(out, f"{asset}.urdf"), "w") as f:
        f.write(xml)
    n_joints = sum(1 for n in links if links[n]["parent"] is not None)
    print(f"urdf {asset}: {len(links)} links, {n_joints} joints ({len(mimic)} mimic), {len(frames)} sensor/light frames, "
          f"{n_tris} visual triangles -> {os.path.relpath(out, assetcfg.ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
