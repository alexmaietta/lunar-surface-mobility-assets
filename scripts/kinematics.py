import math

import numpy as np
from scipy.optimize import least_squares

FIXED_PRISMATIC_RANGE = 1e-3
SAMPLES = 41
DEFAULT_TOLERANCE = {"rest_fail_mm": 0.5, "warn_mm": 10.0, "fail_mm": 40.0, "warn_deg": 1.0, "fail_deg": 5.0}


def rot(axis, angle):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


def urdf_type(joint):
    jt = joint["type"]
    if jt == "spherical":
        return "fixed"
    if jt == "prismatic":
        lim = joint.get("limit")
        if lim is not None and lim[1] - lim[0] < FIXED_PRISMATIC_RANGE:
            return "fixed"
    if jt == "revolute" and "limit" not in joint:
        return "continuous"
    return jt


def chain(links, name):
    out = []
    while name is not None:
        out.append(name)
        name = links[name]["parent"]
    return out


def forward(links, q, names=None):
    names = names or list(links)
    pose = {}

    def visit(n):
        if n in pose:
            return pose[n]
        L = links[n]
        if L["parent"] is None:
            pose[n] = (np.eye(3), np.array(L["origin"], float))
            return pose[n]
        Rp, pp = visit(L["parent"])
        rel = np.array(L["origin"], float) - np.array(links[L["parent"]]["origin"], float)
        J = L["joint"]
        v = q.get(n, 0.0)
        R, p = Rp, pp + Rp @ rel
        if v and J["type"] in ("revolute", "continuous"):
            R = Rp @ rot(J["axis"], v)
        elif v and J["type"] == "prismatic":
            p = p + Rp @ (np.asarray(J["axis"], float) / np.linalg.norm(J["axis"]) * v)
        pose[n] = (R, p)
        return pose[n]

    for n in names:
        visit(n)
    return pose


def world_point(links, pose, link, x):
    R, p = pose[link]
    return p + R @ (np.asarray(x, float) - np.array(links[link]["origin"], float))


def closure_residual(links, loop, pose):
    a, b = loop["parent"], loop["child"]
    gap = world_point(links, pose, a, loop["anchor"]) - world_point(links, pose, b, loop["anchor"])
    if loop["type"] != "revolute":
        return gap, np.zeros(3)
    axis = np.asarray(loop["axis"], float)
    return gap, np.cross(pose[a][0] @ axis, pose[b][0] @ axis)


def loop_joints(links, loop):
    ca, cb = chain(links, loop["parent"]), chain(links, loop["child"])
    common = next(x for x in ca if x in cb)
    return ca[:ca.index(common)] + cb[:cb.index(common)]


def plan_loops(links, loops):
    groups, rigid = {}, []
    for lp in loops:
        movable = [j for j in loop_joints(links, lp) if urdf_type(links[j]["joint"]) != "fixed"]
        drivers = [j for j in movable if links[j]["joint"].get("role") != "linkage"]
        passive = [j for j in movable if links[j]["joint"].get("role") == "linkage"]
        if not movable:
            rigid.append(lp["name"])
            continue
        if len(drivers) != 1:
            raise SystemExit(f"loop {lp['name']}: expected one non-linkage driver joint, found {drivers or 'none'} among {movable}")
        g = groups.setdefault(drivers[0], {"driver": drivers[0], "loops": [], "passive": []})
        g["loops"].append(lp)
        g["passive"] += [j for j in passive if j not in g["passive"]]
    owner = {}
    for d, g in groups.items():
        for j in g["passive"]:
            if owner.setdefault(j, d) != d:
                raise SystemExit(f"linkage joint {j} is closed by loops driven by both {owner[j]} and {d}")
    return list(groups.values()), rigid


def driver_samples(joint):
    lo, hi = joint.get("limit", (-math.pi, math.pi))
    start = min(max(0.0, lo), hi)
    n = SAMPLES // 2
    return start, list(np.linspace(start, hi, n + 1)[1:]), list(np.linspace(start, lo, n + 1)[1:])


def group_residual(links, group, q):
    names = set()
    for lp in group["loops"]:
        names |= set(chain(links, lp["parent"])) | set(chain(links, lp["child"]))
    pose = forward(links, q, sorted(names))
    out = []
    for lp in group["loops"]:
        gap, ang = closure_residual(links, lp, pose)
        out += [gap, ang]
    return np.concatenate(out)


def solve_group(links, group):
    d, passive = group["driver"], group["passive"]
    start, up, down = driver_samples(links[d]["joint"])
    bounds = ([links[j]["joint"].get("limit", (-math.pi, math.pi))[0] for j in passive],
              [links[j]["joint"].get("limit", (-math.pi, math.pi))[1] for j in passive])

    def solve(qd, x0):
        f = lambda x: group_residual(links, group, {d: qd, **dict(zip(passive, x))})
        r = least_squares(f, x0, bounds=bounds, xtol=1e-12, ftol=1e-12, gtol=1e-12)
        return r.x, float(np.max(np.abs(r.fun))) if len(r.fun) else 0.0

    x_rest, res_rest = solve(start, np.zeros(len(passive)))
    rows = [(start, x_rest, res_rest)]
    for seq in (up, down):
        x = x_rest
        for qd in seq:
            x, res = solve(qd, x)
            rows.append((qd, x, res))
    rows.sort(key=lambda r: r[0])
    return start, rows


def fit_mimic(links, group, start, rows, reachable_tol=1e-4):
    d = group["driver"]
    good = [r for r in rows if r[2] < reachable_tol]
    qd = np.array([r[0] for r in good]) - start
    X = np.array([r[1] for r in good])
    x_rest = next(r[1] for r in rows if r[0] == start)
    mimic = {}
    for i, j in enumerate(group["passive"]):
        m = float(np.dot(qd, X[:, i] - x_rest[i]) / np.dot(qd, qd))
        mimic[j] = {"joint": d, "multiplier": m, "offset": float(x_rest[i] - m * start)}
    return mimic, len(good), len(rows)


def closure_error(links, loops, mimic, driver, samples):
    worst = {lp["name"]: [0.0, 0.0] for lp in loops}
    for qd in samples:
        q = {driver: qd}
        q.update({j: m["multiplier"] * qd + m["offset"] for j, m in mimic.items() if m["joint"] == driver})
        pose = forward(links, q)
        for lp in loops:
            gap, ang = closure_residual(links, lp, pose)
            w = worst[lp["name"]]
            w[0] = max(w[0], float(np.linalg.norm(gap)) * 1000)
            w[1] = max(w[1], math.degrees(math.asin(min(1.0, float(np.linalg.norm(ang))))))
    return worst


def status(mm, deg, rest_mm, tol):
    if mm > tol["fail_mm"] or deg > tol["fail_deg"] or rest_mm > tol["rest_fail_mm"]:
        return "fail"
    if mm > tol["warn_mm"] or deg > tol["warn_deg"]:
        return "warn"
    return "ok"


def solve_loops(links, loops, tolerance=None):
    tol = {**DEFAULT_TOLERANCE, **(tolerance or {})}
    groups, rigid = plan_loops(links, loops)
    mimic, report = {}, []
    for g in groups:
        start, rows = solve_group(links, g)
        m, n_good, n_all = fit_mimic(links, g, start, rows)
        mimic.update(m)
        reach = [r[0] for r in rows if r[2] < 1e-4]
        lo, hi = min(reach), max(reach)
        central = [q for q in reach if (start - lo) / -2 <= q - start <= (hi - start) / 2]
        err = closure_error(links, g["loops"], m, g["driver"], reach)
        mid = closure_error(links, g["loops"], m, g["driver"], central)
        rest = closure_error(links, g["loops"], m, g["driver"], [start])
        for lp in g["loops"]:
            n = lp["name"]
            report.append({"loop": n, "closure": lp["type"], "driver": g["driver"], "parent": lp["parent"], "child": lp["child"],
                           "anchor": [round(float(x), 6) for x in lp["anchor"]], "axis": [round(float(x), 6) for x in lp["axis"]],
                           "passive": [j for j in g["passive"] if j in loop_joints(links, lp)],
                           "max_gap_mm": round(err[n][0], 3), "max_angle_deg": round(err[n][1], 3),
                           "central_gap_mm": round(mid[n][0], 3), "rest_gap_mm": round(rest[n][0], 4),
                           "driver_range": [round(float(lo), 6), round(float(hi), 6)], "samples_closed": f"{n_good}/{n_all}",
                           "status": status(err[n][0], err[n][1], rest[n][0], tol)})
    return mimic, report, rigid, tol
