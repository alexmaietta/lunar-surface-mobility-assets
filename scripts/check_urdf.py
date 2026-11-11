import glob
import json
import math
import os
import sys
from xml.etree import ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg
import kinematics


def vec(s, n=3):
    return np.array([float(x) for x in s.split()]) if s else np.zeros(n)


def rpy_matrix(r, p, y):
    return kinematics.rot((0, 0, 1), y) @ kinematics.rot((0, 1, 0), p) @ kinematics.rot((1, 0, 0), r)


class Urdf:
    def __init__(self, path):
        self.path = path
        self.root = ET.parse(path).getroot()
        self.links = {L.get("name"): L for L in self.root.findall("link")}
        self.joints = {}
        for j in self.root.findall("joint"):
            o = j.find("origin")
            lim = j.find("limit")
            mim = j.find("mimic")
            self.joints[j.get("name")] = {
                "type": j.get("type"), "parent": j.find("parent").get("link"), "child": j.find("child").get("link"),
                "xyz": vec(o.get("xyz")) if o is not None else np.zeros(3),
                "rpy": vec(o.get("rpy")) if o is not None else np.zeros(3),
                "axis": vec(j.find("axis").get("xyz")) if j.find("axis") is not None else np.array([1.0, 0, 0]),
                "limit": (float(lim.get("lower", 0)), float(lim.get("upper", 0))) if lim is not None else None,
                "has_limit": lim is not None,
                "mimic": (mim.get("joint"), float(mim.get("multiplier", 1)), float(mim.get("offset", 0))) if mim is not None else None}
        self.child_joint = {j["child"]: n for n, j in self.joints.items()}

    def forward(self, q):
        q = dict(q)
        for n, j in self.joints.items():
            if j["mimic"]:
                t, m, o = j["mimic"]
                q[n] = m * q.get(t, 0.0) + o
        pose = {}

        def visit(link):
            if link in pose:
                return pose[link]
            jn = self.child_joint.get(link)
            if jn is None:
                pose[link] = (np.eye(3), np.zeros(3))
                return pose[link]
            j = self.joints[jn]
            Rp, pp = visit(j["parent"])
            R = Rp @ rpy_matrix(*j["rpy"])
            p = pp + Rp @ j["xyz"]
            v = q.get(jn, 0.0)
            if j["type"] in ("revolute", "continuous"):
                R = R @ kinematics.rot(j["axis"], v)
            elif j["type"] == "prismatic":
                p = p + R @ (j["axis"] / np.linalg.norm(j["axis"]) * v)
            pose[link] = (R, p)
            return pose[link]

        for L in self.links:
            visit(L)
        return pose


def check_structure(u, errs):
    names = [L.get("name") for L in u.root.findall("link")]
    if len(names) != len(set(names)):
        errs.append("duplicate link names")
    jn = [j.get("name") for j in u.root.findall("joint")]
    if len(jn) != len(set(jn)):
        errs.append("duplicate joint names")
    roots = [L for L in u.links if L not in u.child_joint]
    if roots != ["base_link"]:
        errs.append(f"expected a single root base_link, found {roots}")
    for n, j in u.joints.items():
        for end in ("parent", "child"):
            if j[end] not in u.links:
                errs.append(f"joint {n} {end} {j[end]} is not a link")
        if j["type"] in ("revolute", "prismatic") and (not j["has_limit"] or j["limit"][0] > j["limit"][1]):
            errs.append(f"joint {n} ({j['type']}) has no valid limit")
        if j["type"] not in ("fixed", "revolute", "continuous", "prismatic"):
            errs.append(f"joint {n} has type {j['type']}")
        if j["mimic"]:
            t = j["mimic"][0]
            if t not in u.joints:
                errs.append(f"joint {n} mimics missing joint {t}")
            elif u.joints[t]["mimic"]:
                errs.append(f"joint {n} mimics {t}, which is itself a mimic")
    for L in u.links:
        link, steps = L, 0
        while link in u.child_joint and steps <= len(u.links):
            link, steps = u.joints[u.child_joint[link]]["parent"], steps + 1
        if steps > len(u.links):
            errs.append(f"cycle through {L}")


def check_files(u, errs):
    base = os.path.dirname(u.path)
    meshes = {m.get("filename") for m in u.root.iter("mesh")}
    for fn in sorted(meshes):
        p = os.path.join(base, fn)
        if not os.path.isfile(p):
            errs.append(f"missing mesh {fn}")
            continue
        with open(p, "rb") as f:
            head = f.read(200)
        if head.startswith(b"version https://git-lfs"):
            errs.append(f"mesh {fn} is an LFS pointer (run git lfs pull)")
            continue
        with open(p) as f:
            mtl = next((ln.split(None, 1)[1].strip() for ln in f if ln.startswith("mtllib")), None)
        if mtl is None:
            continue
        mp = os.path.join(os.path.dirname(p), mtl)
        if not os.path.isfile(mp):
            errs.append(f"{fn} references missing {mtl}")
            continue
        with open(mp) as f:
            for ln in f:
                if ln.startswith("map_Kd"):
                    tex = os.path.normpath(os.path.join(os.path.dirname(mp), ln.split(None, 1)[1].strip()))
                    if not os.path.isfile(tex):
                        errs.append(f"{os.path.relpath(mp, base)} references missing texture {os.path.relpath(tex, base)}")
    return len(meshes)


def check_inertia(u, errs):
    total = 0.0
    for name, L in u.links.items():
        ine = L.find("inertial")
        if ine is None:
            continue
        m = float(ine.find("mass").get("value"))
        i = ine.find("inertia")
        I = np.array([[float(i.get("ixx")), float(i.get("ixy")), float(i.get("ixz"))],
                      [float(i.get("ixy")), float(i.get("iyy")), float(i.get("iyz"))],
                      [float(i.get("ixz")), float(i.get("iyz")), float(i.get("izz"))]])
        ev = np.linalg.eigvalsh(I)
        if m <= 0:
            errs.append(f"link {name} has mass {m}")
        if ev.min() <= 0:
            errs.append(f"link {name} inertia is not positive definite (eigenvalues {ev})")
        elif ev[0] + ev[1] < ev[2] * (1 - 1e-4):
            errs.append(f"link {name} inertia violates the triangle inequality (eigenvalues {ev})")
        total += m
    return total


def usd_links(cfg, asset):
    from pxr import Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(assetcfg.asset_dir(cfg, "usd", f"{asset}.usda"))
    out, mass = {}, 0.0
    for p in stage.Traverse():
        if p.HasAPI(UsdPhysics.RigidBodyAPI):
            m = np.array(UsdGeom.Xformable(p).ComputeLocalToWorldTransform(0))
            out[p.GetName()] = (m[:3, :3].T, m[3, :3])
            if p.HasAPI(UsdPhysics.MassAPI):
                mass += UsdPhysics.MassAPI(p).GetMassAttr().Get() or 0.0
    up = UsdGeom.GetStageUpAxis(stage)
    return out, mass, up


def check_pose(u, cfg, asset, errs, tol=1e-4):
    links, usd_mass, up = usd_links(cfg, asset)
    if up != "Z":
        errs.append(f"USD up axis is {up}, URDF assumes Z")
    pose = u.forward({})
    worst, compared = 0.0, 0
    for name, (R, p) in links.items():
        if name not in pose:
            errs.append(f"USD rigid body {name} has no URDF link")
            continue
        Ru, pu = pose[name]
        d = float(np.linalg.norm(pu - p))
        a = float(np.linalg.norm(Ru - R))
        worst = max(worst, d)
        compared += 1
        if d > tol or a > 1e-3:
            errs.append(f"link {name} rest pose differs from USD by {d * 1000:.3f} mm / {a:.2e} rotation")
    return compared, worst, usd_mass


def check_loops(u, side, errs, samples=41):
    out = []
    rest = u.forward({})
    for r in side.get("loops", []):
        d = r["driver"]
        lo, hi = r["driver_range"]
        local = {link: rest[link][0].T @ (np.array(r["anchor"]) - rest[link][1]) for link in (r["parent"], r["child"])}
        worst = 0.0
        for qd in np.linspace(lo, hi, samples):
            pose = u.forward({d: qd})
            a, b = (pose[link][1] + pose[link][0] @ local[link] for link in (r["parent"], r["child"]))
            worst = max(worst, float(np.linalg.norm(a - b)) * 1000)
        if abs(worst - r["max_gap_mm"]) > max(0.05 * r["max_gap_mm"], 0.5):
            errs.append(f"loop {r['loop']}: URDF gap {worst:.2f} mm, sidecar says {r['max_gap_mm']} mm")
        if r["status"] == "fail":
            errs.append(f"loop {r['loop']} is marked fail in the sidecar")
        out.append((r["loop"], worst))
    return out


def check_mujoco(path, errs):
    try:
        import mujoco
    except ImportError:
        return "skipped (no mujoco)"
    try:
        m = mujoco.MjModel.from_xml_path(path)
    except Exception as e:
        errs.append(f"mujoco failed to load: {str(e).splitlines()[0]}")
        return "failed"
    return f"{m.nbody} bodies, {m.njnt} joints, {float(sum(m.body_mass)):.1f} kg on moving bodies"


def check(asset, use_mujoco=True):
    cfg = assetcfg.load(asset)
    base = assetcfg.asset_dir(cfg, "urdf")
    path = os.path.join(base, f"{asset}.urdf")
    errs = []
    if not os.path.isfile(path):
        return [f"missing {os.path.relpath(path, assetcfg.ROOT)}"], ""
    u = Urdf(path)
    side_path = os.path.join(base, f"{asset}.urdf.json")
    side = json.load(open(side_path)) if os.path.isfile(side_path) else None
    if side is None:
        errs.append(f"missing sidecar {asset}.urdf.json")
    elif side.get("version") != assetcfg.version():
        errs.append(f"sidecar version {side.get('version')} does not match VERSION {assetcfg.version()}")
    check_structure(u, errs)
    n_mesh = check_files(u, errs)
    mass = check_inertia(u, errs)
    compared, worst, usd_mass = check_pose(u, cfg, asset, errs)
    if usd_mass and abs(mass - usd_mass) > 1e-3 * usd_mass:
        errs.append(f"URDF mass {mass:.3f} kg differs from USD {usd_mass:.3f} kg")
    loops = check_loops(u, side, errs) if side else []
    mj = check_mujoco(path, errs) if use_mujoco else "skipped"
    mimic = sum(1 for j in u.joints.values() if j["mimic"])
    worst_loop = max(loops, key=lambda x: x[1], default=None)
    summary = (f"{len(u.links)} links, {len(u.joints)} joints ({mimic} mimic), {n_mesh} meshes, {mass:.1f} kg, "
               f"{compared} links match USD (max {worst * 1000:.3f} mm), {len(loops)} loops"
               + (f" (max gap {worst_loop[1]:.1f} mm)" if worst_loop else "") + f", mujoco {mj}")
    return errs, summary


def main(argv):
    asset = assetcfg.arg(argv, "--asset")
    ids = [asset] if asset else sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(assetcfg.ROOT, "configs", "*.py")))
    failed = 0
    for a in ids:
        if not getattr(assetcfg.load(a), "URDF", True):
            print(f"{a}: skipped (URDF = False)")
            continue
        errs, summary = check(a, "--no-mujoco" not in argv)
        print(f"{'FAIL' if errs else 'ok  '} {a}: {summary}")
        for e in errs:
            print(f"     {e}")
        failed += bool(errs)
    if failed:
        raise SystemExit(f"{failed} asset(s) failed")


if __name__ == "__main__":
    main(sys.argv[1:])
