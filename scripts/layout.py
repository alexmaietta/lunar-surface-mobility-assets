GAP = 2.0
ROW_GAP = 6.0
ROWS = [
    ["cadre", "mapp"],
    None,
    None,
    ["*", "peregrine", "nova_c", "blue_ghost", "*"],
    ["lunar_cruiser", "mk1", "apollo_lm", "pr_concept"],
]


def arrange(items, rows_spec=ROWS, gap=GAP, row_gap=ROW_GAP):
    by = {it["asset"]: it for it in items}
    named = {a for row in rows_spec if row for a in row if a != "*"}
    rest = sorted((it for it in items if it["asset"] not in named), key=lambda it: -it["hi"][2])
    slots = sum(row.count("*") for row in rows_spec if row)
    fill, rest = rest[:slots], rest[slots:]
    auto = [i for i, row in enumerate(rows_spec) if row is None]
    rows = []
    for i, row in enumerate(rows_spec):
        if row is None:
            k, n = auto.index(i), len(rest)
            chunk = sorted(rest, key=lambda it: it["hi"][2])[n * k // len(auto):n * (k + 1) // len(auto)]
            order = []
            for j, it in enumerate(chunk):
                order = order + [it] if j % 2 else [it] + order
            rows.append(order)
        else:
            rows.append([fill.pop(0) if a == "*" else by[a] for a in row if a == "*" and fill or a in by])
    out, y = {}, 0.0
    for r, order in enumerate([r for r in rows if r]):
        width = sum(it["hi"][0] - it["lo"][0] for it in order) + gap * (len(order) - 1)
        x = -width / 2
        depth = max(it["hi"][1] - it["lo"][1] for it in order)
        for it in order:
            out[it["asset"]] = {"shift": (x - it["lo"][0], y + depth / 2 - (it["lo"][1] + it["hi"][1]) / 2), "row": r}
            x += it["hi"][0] - it["lo"][0] + gap
        y += depth + row_gap
    return out
