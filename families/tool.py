import geo as G
import materials as M
import rover as RV


def build(cfg):
    T = cfg.TOOL
    RV.LINKS.clear()
    base = G.link("base", (0, 0, 0), mass=T.get("base_mass", 10.0))
    RV.LINKS["base"] = base
    pending = RV._add_links([dict(L, parent=L.get("parent", "base")) for L in T.get("links", [])])
    if pending:
        raise ValueError(f"links with unknown parents: {[L['name'] for L in pending]}")
    for p in T["parts"]:
        RV._part(dict(p, link=p.get("link", "base")), M.get)
    for n, link, pos, z_axis, kind, desc, *extra in T.get("sites", []):
        G.site(n, RV.LINKS[link], pos, z_axis, kind=kind, description=desc, **(extra[0] if extra else {}))
    G.site("mount", base, (0, 0, 0), T.get("mount_axis", (-1, 0, 0)), kind="mount",
           description="Quick-attach coupler: mates with a rover's tool_front or tool_rear site")
    return base
