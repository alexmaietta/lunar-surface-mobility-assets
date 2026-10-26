import argparse
import glob
import os
import sys
from collections import defaultdict

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg


def triangles(path):
    scene = trimesh.load(path, force="scene")
    out = []
    for node in scene.graph.nodes_geometry:
        tf, geom = scene.graph[node]
        mesh = scene.geometry[geom]
        if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces):
            continue
        v = trimesh.transform_points(mesh.vertices, tf)
        out.append((node, v[mesh.faces]))
    return out


def planes(tris, min_area):
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    n = np.cross(e1, e2)
    area = np.linalg.norm(n, axis=1) / 2
    keep = area > min_area
    n = n[keep] / (2 * area[keep, None])
    t = tris[keep]
    d = np.einsum("ij,ij->i", n, t[:, 0])
    return t, n, d


def basis(n):
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def check(path, min_area, min_overlap, ang_bins, dist_mm):
    groups = defaultdict(list)
    for node, tris in triangles(path):
        t, n, d = planes(tris, min_area)
        keys = np.round(np.c_[n * ang_bins, d * 1000.0 / dist_mm]).astype(np.int64)
        for k, tri, nn in zip(map(tuple, keys), t, n):
            groups[k].append((node, tri, nn))
    hits = defaultdict(float)
    where = {}
    for faces in groups.values():
        nodes = {f[0] for f in faces}
        if len(nodes) < 2:
            continue
        u, v = basis(faces[0][2])
        polys = defaultdict(list)
        for node, tri, _ in faces:
            p = Polygon([(x @ u, x @ v) for x in tri])
            if p.is_valid and p.area > 0:
                polys[node].append(p)
        merged = {k: unary_union(ps) for k, ps in polys.items()}
        names = sorted(merged)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                inter = merged[a].intersection(merged[b])
                if inter.area > min_overlap:
                    hits[(a, b)] += inter.area
                    c = inter.centroid
                    where[(a, b)] = faces[0][2] * np.einsum("i,i", faces[0][2], faces[0][1][0]) + u * c.x + v * c.y
    return sorted(((area, a, b, where[(a, b)]) for (a, b), area in hits.items()), reverse=True)


def main():
    ap = argparse.ArgumentParser(description="Find coplanar overlapping faces between different meshes (z-fighting) in glTF assets.")
    ap.add_argument("paths", nargs="*", help="glb files (default: web/models/*/full.glb)")
    ap.add_argument("--min-area", type=float, default=1e-5, help="ignore triangles smaller than this [m^2]")
    ap.add_argument("--min-overlap", type=float, default=2e-4, help="report overlaps larger than this [m^2]")
    ap.add_argument("--dist-mm", type=float, default=0.3, help="plane offset tolerance [mm]")
    ap.add_argument("--ang-bins", type=float, default=60.0, help="normal quantisation (60 ~ 1 deg)")
    a = ap.parse_args()
    paths = a.paths or sorted(glob.glob(os.path.join(assetcfg.ROOT, "web", "models", "*", "full.glb")))
    total = 0
    for p in paths:
        hits = check(p, a.min_area, a.min_overlap, a.ang_bins, a.dist_mm)
        name = os.path.basename(os.path.dirname(p)) if p.endswith("full.glb") else os.path.basename(p)
        print(f"{name}: {len(hits)} z-fighting pair(s)")
        for area, x, y, c in hits[:25]:
            print(f"  {area * 1e4:8.1f} cm2  {x}  <->  {y}  near ({c[0]:+.2f}, {c[1]:+.2f}, {c[2]:+.2f}) Y-up")
        total += len(hits)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
