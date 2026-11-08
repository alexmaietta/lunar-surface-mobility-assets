import json
import math
import os
import struct
import zlib

import numpy as np


def _rng(seed):
    return np.random.default_rng(seed)


def pnoise(n, feature_px, seed, octaves=4, persistence=0.5):
    rng = _rng(seed)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    out = np.zeros((n, n))
    amp, fp, total = 1.0, feature_px, 0.0
    for _ in range(octaves):
        w = rng.standard_normal((n, n))
        f0 = 1.0 / max(fp, 1.0)
        band = np.exp(-((f - f0) ** 2) / (2 * (0.6 * f0) ** 2))
        layer = np.real(np.fft.ifft2(np.fft.fft2(w) * band))
        layer /= layer.std() + 1e-9
        out += amp * layer
        total += amp
        amp *= persistence
        fp /= 2.0
    out /= total
    return np.clip(0.5 + out * 0.18, 0, 1)


def streaks(n, seed, along=1, length_px=900, width_px=1.2):
    rng = _rng(seed)
    w = rng.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    fa, fc = (fx, fy) if along == 1 else (fy, fx)
    band = np.exp(-(fa * length_px) ** 2) * np.exp(-(np.abs(fc) * width_px) ** 2 / 50)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * band))
    out /= out.std() + 1e-9
    return np.clip(0.5 + out * 0.2, 0, 1)


def scratches(n, seed, count=220, max_len=0.35, depth=1.0):
    rng = _rng(seed)
    h = np.zeros((n, n))
    for _ in range(count):
        x0, y0 = rng.random(2) * n
        ang = rng.normal(0.3, 0.5)
        ln = rng.random() ** 2 * max_len * n
        steps = int(ln)
        if steps < 2:
            continue
        t = np.linspace(0, ln, steps)
        xs = (x0 + np.cos(ang) * t).astype(int) % n
        ys = (y0 + np.sin(ang) * t + np.sin(t / 60) * 3).astype(int) % n
        h[ys, xs] -= depth * (0.3 + 0.7 * rng.random())
    k = np.fft.fft2(np.pad(np.ones((2, 2)), ((0, n - 2), (0, n - 2))))
    return np.real(np.fft.ifft2(np.fft.fft2(h) * k)) / 4


def _upsample(a, n):
    from scipy.ndimage import zoom
    if a.shape[0] == n:
        return a
    return zoom(a, n / a.shape[0], order=1, mode="grid-wrap")


def crumple(n, seed, folds=90, kmax=7, sharp=1.0, warp_px=40.0):
    m = min(n, 1024)
    return _upsample(_crumple(m, seed, folds, kmax, sharp, warp_px * m / n), n)


def _crumple(n, seed, folds=90, kmax=7, sharp=1.0, warp_px=40.0):
    rng = _rng(seed)
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / n
    wx = (pnoise(n, warp_px * 4, seed + 1, octaves=2) - 0.5) * warp_px / n
    wy = (pnoise(n, warp_px * 4, seed + 2, octaves=2) - 0.5) * warp_px / n
    x, y = x + wx, y + wy
    h = np.zeros((n, n))
    for i in range(folds):
        while True:
            kx, ky = rng.integers(-kmax, kmax + 1, 2)
            if kx or ky:
                break
        kl = math.hypot(kx, ky)
        phase = rng.random()
        t = np.abs(np.mod(kx * x + ky * y + phase, 1.0) - 0.5)
        env = pnoise(n, n / (1.5 + rng.random() * 2), seed + 10 + i, octaves=1)
        env = np.clip((env - 0.42) * 6, 0, 1)
        h += t * env * (1.0 / kl) ** sharp
    return (h - h.min()) / (np.ptp(h) + 1e-9)


def facets(n, seed, cells, tilt_deg, stretch=1.0):
    from scipy.spatial import cKDTree
    rng = _rng(seed)
    pts = rng.random((cells, 2)) * n
    tree = cKDTree(pts * [1 / stretch, 1], boxsize=[n / stretch, n])
    cid = np.empty((n, n), np.int32)
    edge = np.empty((n, n), np.float32)
    xs = (np.arange(n) + 0.5) / stretch % (n / stretch)
    rows = max(1, (1 << 20) // n)
    for r0 in range(0, n, rows):
        r1 = min(n, r0 + rows)
        yy, xx = np.meshgrid(np.arange(r0, r1) + 0.5, xs, indexing="ij")
        d, idx = tree.query(np.stack([xx.ravel(), yy.ravel() % n], 1), k=2)
        cid[r0:r1] = idx[:, 0].reshape(r1 - r0, n)
        edge[r0:r1] = ((d[:, 1] - d[:, 0]) * 0.5).reshape(r1 - r0, n)
    t = np.radians(tilt_deg) * np.sqrt(rng.random(cells))
    a = rng.random(cells) * 2 * math.pi
    nx, ny = np.sin(t) * np.cos(a), np.sin(t) * np.sin(a)
    nz = np.sqrt(1 - nx ** 2 - ny ** 2)
    nrm = np.stack([nx[cid], ny[cid], nz[cid]], -1).astype(np.float32)
    return nrm, cid, edge


def _encode_normal(nrm):
    nrm = nrm / np.linalg.norm(nrm, axis=-1, keepdims=True)
    return nrm * 0.5 + 0.5


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5


def tint(var, colour, amount):
    c = np.array(colour)[None, None, :]
    return c * (1 + (var[..., None] - 0.5) * 2 * amount)


def _grid_lines(n, cells, width_px, offset=0.0):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    p = n / cells
    dx = np.abs(np.mod(x / p + offset, 1.0) - 0.5) * p
    dy = np.abs(np.mod(y / p + offset, 1.0) - 0.5) * p
    d = np.minimum(p / 2 - dx, p / 2 - dy)
    return np.clip(width_px / 2 - d + 0.5, 0, 1), x, y


def _dots(n, pitch_px, r_px, offset=(0.5, 0.5), stagger=False):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    u = x / pitch_px + offset[0]
    v = y / pitch_px + offset[1]
    if stagger:
        u = u + 0.5 * (np.floor(v) % 2)
    du = (np.mod(u, 1.0) - 0.5) * pitch_px
    dv = (np.mod(v, 1.0) - 0.5) * pitch_px
    d = np.sqrt(du * du + dv * dv)
    mask = np.clip(r_px - d + 0.5, 0, 1)
    dome = np.sqrt(np.clip(1 - (d / r_px) ** 2, 0, 1))
    return mask, dome


def _to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def _srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def write_png(path, a8):
    h, w = a8.shape[:2]
    ch = 1 if a8.ndim == 2 else a8.shape[2]
    raw = np.concatenate([np.zeros((h, 1), np.uint8), a8.reshape(h, w * ch)], 1).tobytes()

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0 if ch == 1 else 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


def save_set(out, name, tile_m, **maps):
    d = os.path.join(out, name)
    os.makedirs(d, exist_ok=True)
    for k, a in maps.items():
        if np.ndim(a) == 0:
            continue
        a8 = _to8(_srgb(a)) if k == "basecolor" else _to8(a)
        write_png(os.path.join(d, f"{name}_{k}.png"), a8)
    meta = {"tile_m": tile_m, "maps": sorted(k for k, a in maps.items() if np.ndim(a) != 0)}
    with open(os.path.join(d, "set.json"), "w") as f:
        json.dump(meta, f)
    return meta


def mli(n, seed, colour, tile_m=1.0, gloss=0.06, tape=True, crinkle=1.0):
    big, cid, e1 = facets(n, seed, int((tile_m / 0.20) ** 2 * 1.3), 14, stretch=1.25)
    fine, _, e2 = facets(n, seed + 1, int((tile_m / 0.045) ** 2 * 1.3 * crinkle), 12, stretch=1.15)
    micro, _, _ = facets(n, seed + 6, int((tile_m / 0.016) ** 2 * 1.3 * crinkle), 7, stretch=1.3)
    puff = pnoise(n, n / 3, seed + 3, octaves=2)
    pn = normal_from_height(puff, 6.0 * n / 2048) * 2 - 1
    folds = crumple(n, seed + 2, folds=60, kmax=7, sharp=0.9, warp_px=25)
    fn = normal_from_height(folds, 14.0 * n / 2048) * 2 - 1
    nrm = big * 0.8 + fine * 0.8 + micro * 0.45 + pn * 0.6 + fn * 1.3
    nrm[..., 2] = np.abs(nrm[..., 2]) + 0.3
    var = pnoise(n, n / 5, seed + 4, octaves=3)
    smudge = pnoise(n, n / 12, seed + 5, octaves=3)
    crease = np.clip(1.5 - e1 / (1.5 * n / 2048), 0, 1)
    fvar = ((np.sin(cid * 12.9898) * 43758.5453) % 1.0)
    base = tint(var * 0.6 + fvar * 0.4, colour, 0.08) * (1 - 0.08 * crease[..., None])
    rough = np.clip(gloss + (smudge > 0.6) * 0.08 + crease * 0.06 + fvar * 0.04, 0.02, 1)
    if tape:
        y, x = np.mgrid[0:n, 0:n] + 0.5
        w = 0.05 / tile_m * n
        seam = ((np.abs(x - n * 0.37) < w / 2) | (np.abs(y - n * 0.71) < w / 2)).astype(float)
        rough = np.clip(rough + seam * 0.10, 0, 1)
        base = base * (1 - 0.06 * seam[..., None])
        nrm = nrm * (1 - 0.75 * seam[..., None]) + np.array([0, 0, 1.0]) * 0.75 * seam[..., None]
    return dict(basecolor=base, roughness=rough, metallic=np.ones((n, n)), normal=_encode_normal(nrm)), tile_m


def beta_cloth(n, seed, colour, tile_m=0.6, rough0=0.75):
    y, x = np.mgrid[0:n, 0:n]
    p = n / (tile_m / 0.0012)
    weave = np.abs(np.sin(math.pi * x / p)) * 0.5 + np.abs(np.sin(math.pi * y / p)) * 0.5
    sag = pnoise(n, n / 4, seed, octaves=3)
    wr = crumple(n, seed + 1, folds=50, kmax=8, sharp=1.0)
    h = sag * 2.0 + wr * 1.2 + weave * 0.04
    var = pnoise(n, n / 6, seed + 2)
    base = tint(var, colour, 0.03) * (0.95 + 0.05 * weave[..., None])
    rough = np.clip(rough0 + (var - 0.5) * 0.08, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)),
                normal=normal_from_height(h, 4.0 * n / 2048)), tile_m


def panel(n, seed, colour, tile_m=0.5, rough0=0.5, fastener_pitch=0.05, metallic=0.0, seams=1):
    peel = pnoise(n, 10, seed, octaves=3)
    var = pnoise(n, n / 4, seed + 1)
    grime = pnoise(n, n / 10, seed + 2, octaves=4)
    line, x, y = _grid_lines(n, seams, 2.0 * n / 2048, offset=0.0)
    p = n / seams
    inset = 0.02 / tile_m * n
    dxs = np.abs(np.mod(x, p) - inset)
    dys = np.abs(np.mod(y, p) - inset)
    pitch = fastener_pitch / tile_m * n
    r = 0.0035 / tile_m * n
    fx = np.sqrt(dxs ** 2 + ((np.mod(y, pitch)) - pitch / 2) ** 2)
    fy = np.sqrt(dys ** 2 + ((np.mod(x, pitch)) - pitch / 2) ** 2)
    fd = np.minimum(fx, fy)
    head = np.clip(r - fd + 0.5, 0, 1)
    dome = np.sqrt(np.clip(1 - (fd / r) ** 2, 0, 1))
    base = tint(var, colour, 0.03) * (1 - 0.06 * (grime[..., None] - 0.5)) * (1 - 0.35 * line[..., None])
    base = base * (1 - head[..., None]) + np.array([0.55, 0.55, 0.56]) * head[..., None]
    rough = np.clip(rough0 + (peel - 0.5) * 0.1 + (var - 0.5) * 0.06 - head * 0.2, 0, 1)
    met = np.clip(metallic + head, 0, 1)
    h = peel * 0.3 - line * 1.5 + dome * 1.2
    return dict(basecolor=base, roughness=rough, metallic=met,
                normal=normal_from_height(h, 2.0 * n / 2048)), tile_m


def brushed(n, seed, colour, tile_m=0.4, rough0=0.3, along=1):
    st = streaks(n, seed, along)
    var = pnoise(n, n / 4, seed + 1)
    sc = scratches(n, seed + 2, count=160)
    base = tint(var, colour, 0.06) * (0.92 + 0.16 * st[..., None])
    rough = np.clip(rough0 + (st - 0.5) * 0.25 + (var - 0.5) * 0.1 - sc * 0.1, 0.05, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.ones((n, n)),
                normal=normal_from_height(st * 0.6 + sc * 0.8, 1.5)), tile_m


def anodised(n, seed, colour, tile_m=0.3, rough0=0.45):
    pit = pnoise(n, 4.0, seed, octaves=3)
    var = pnoise(n, n / 5, seed + 1)
    base = tint(var, colour, 0.07) * (0.94 + 0.12 * pit[..., None])
    rough = np.clip(rough0 + (pit - 0.5) * 0.3 + (var - 0.5) * 0.1, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.full((n, n), 0.9),
                normal=normal_from_height(pit, 2.0)), tile_m


def perforated(n, seed, colour, tile_m=0.2, hole_d=0.022, pitch=0.04, rough0=0.35):
    pitch_px = pitch / tile_m * n
    hole, dome = _dots(n, pitch_px, hole_d / 2 / tile_m * n, stagger=False)
    st = streaks(n, seed, 1)
    var = pnoise(n, n / 4, seed + 1)
    rim, _ = _dots(n, pitch_px, (hole_d / 2 + 0.002) / tile_m * n)
    base = tint(var, colour, 0.05) * (0.94 + 0.1 * st[..., None]) * (1 - 0.2 * (rim - hole)[..., None])
    rough = np.clip(rough0 + (st - 0.5) * 0.2, 0, 1)
    h = st * 0.4 - (rim - hole) * 1.0
    return dict(basecolor=base, roughness=rough, metallic=np.ones((n, n)),
                normal=normal_from_height(h, 1.5), opacity=1 - hole), tile_m


def solar_cells(n, seed, tile_m=0.32, cell=(0.08, 0.04), gap=0.0015, cell_colour=(0.018, 0.022, 0.055),
                backing=(0.65, 0.63, 0.58)):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    cw, ch = cell[0] / tile_m * n, cell[1] / tile_m * n
    u, v = np.mod(x, cw), np.mod(y, ch)
    g = gap / tile_m * n
    in_cell = (u > g) & (u < cw - g) & (v > g) & (v < ch - g)
    fingers = (np.abs(np.mod(u, cw / 40) - cw / 80) < 0.35 * n / 2048) & in_cell
    bus = (np.abs(v - ch * 0.08) < 1.5 * n / 2048) & in_cell
    cid = np.floor(x / cw) * 7 + np.floor(y / ch) * 13
    var = (np.sin(cid * 12.9898) * 43758.5453) % 1.0
    cellc = np.array(cell_colour) * (0.85 + 0.3 * var[..., None])
    base = np.where(in_cell[..., None], cellc, np.array(backing))
    base = np.where((fingers | bus)[..., None], np.array([0.55, 0.55, 0.57]), base)
    rough = np.where(in_cell, 0.08, 0.5) + 0.0 * x
    met = np.where(fingers | bus, 1.0, 0.0)
    h = in_cell * 0.5 + (fingers | bus) * 0.3
    return dict(basecolor=base, roughness=rough, metallic=met, normal=normal_from_height(h, 1.0)), tile_m


def osr(n, seed, tile_m=0.2, tile=0.04):
    line, x, y = _grid_lines(n, int(round(tile_m / tile)), 3.0 * n / 2048)
    tid = np.floor(x / (n * tile / tile_m)) * 3 + np.floor(y / (n * tile / tile_m)) * 17
    var = (np.sin(tid * 78.233) * 43758.5453) % 1.0
    base = np.array([0.80, 0.81, 0.82])[None, None, :] * (0.94 + 0.08 * var[..., None]) * (1 - 0.6 * line[..., None])
    rough = 0.03 + 0.04 * var + line * 0.5
    return dict(basecolor=base, roughness=rough, metallic=np.full((n, n), 0.95) - line * 0.6,
                normal=normal_from_height(-line, 2.0)), tile_m


def nozzle_metal(n, seed, colour, tile_m=0.3, rough0=0.4, bands=0):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    ox = pnoise(n, n / 6, seed, octaves=4)
    st = streaks(n, seed + 1, along=0, length_px=1200)
    ribs = 0.5 + 0.5 * np.cos(2 * math.pi * x / (n / max(bands, 1))) if bands else np.zeros((n, n))
    base = tint(ox, colour, 0.18) * (0.9 + 0.15 * st[..., None])
    rough = np.clip(rough0 + (ox - 0.5) * 0.3, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.full((n, n), 0.95),
                normal=normal_from_height(ribs * 0.4 + st * 0.4, 1.5)), tile_m


def composite(n, seed, colour, tile_m=0.15, rough0=0.35):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    k = 24
    a = np.sin(2 * math.pi * k * (x + y) / n)
    b = np.sin(2 * math.pi * k * (x - y) / n)
    band = (np.floor(2 * k * x / n) + np.floor(2 * k * y / n)) % 2
    h = np.where(band > 0, a, b) * 0.5 + 0.5
    var = pnoise(n, n / 5, seed)
    base = tint(var, colour, 0.08) * (0.85 + 0.2 * h[..., None])
    rough = np.clip(rough0 + (h - 0.5) * 0.15, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)), normal=normal_from_height(h, 1.2)), tile_m


def cloth(n, seed, colour, tile_m=0.1, rough0=0.85, threads=120):
    y, x = np.mgrid[0:n, 0:n]
    p = n / threads
    u, v = x / p, y / p
    warp = np.abs(np.sin(math.pi * u)) * (0.6 + 0.4 * np.cos(math.pi * v) * np.sign(np.sin(math.pi * u)))
    weft = np.abs(np.sin(math.pi * v)) * (0.6 - 0.4 * np.cos(math.pi * u) * np.sign(np.sin(math.pi * v)))
    h = np.maximum(warp, weft)
    var = pnoise(n, n / 5, seed + 1)
    base = tint(var, colour, 0.05) * (0.86 + 0.14 * h[..., None])
    rough = np.clip(rough0 + (0.5 - h) * 0.1, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)), normal=normal_from_height(h, 0.9)), tile_m


def regolith(n, seed, colour=(0.13, 0.125, 0.12), tile_m=4.0):
    fine = pnoise(n, 3, seed, octaves=3)
    mid = pnoise(n, 30, seed + 1, octaves=4)
    big = pnoise(n, n / 4, seed + 2, octaves=3)
    peb, dome = _dots(n, n / 37.0, n / 600, stagger=True)
    jitter = pnoise(n, 20, seed + 3) > 0.62
    h = fine * 0.4 + mid * 1.0 + big * 1.5 + dome * jitter * 2.0
    base = tint(big * 0.6 + mid * 0.4, colour, 0.25) * (0.9 + 0.2 * fine[..., None])
    rough = np.clip(0.92 + (fine - 0.5) * 0.1, 0, 1)
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)), normal=normal_from_height(h, 3.0)), tile_m


def _star_mask(h, w, cx, cy, r_out):
    r_in = r_out * 0.382
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    inside = np.zeros((h, w), bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        cond = (ay > ys) != (by > ys)
        xint = ax + (ys - ay) * (bx - ax) / np.where(by - ay == 0, 1e-9, by - ay)
        inside ^= cond & (xint > xs)
    return inside


def flag(n, seed, tile_m=1.0):
    H, W = n, int(n * 1.9)
    red, white, blue = np.array([0.45, 0.02, 0.04]), np.array([0.80, 0.80, 0.78]), np.array([0.03, 0.04, 0.16])
    rows = (np.arange(H) // (H / 13)).astype(int)
    img = np.empty((H, W, 3))
    img[:] = white
    img[rows % 2 == 0] = red
    ch, cw = int(round(H * 7 / 13)), int(round(H * 0.76))
    img[:ch, :cw] = blue
    E = F = 0.054 * H
    G = 0.063 * H
    K = 0.0616 * H
    stars = np.zeros((ch, cw), bool)
    for r in range(9):
        for c in range(6 if r % 2 == 0 else 5):
            stars |= _star_mask(ch, cw, G + (2 * c + (r % 2)) * G, E + r * F, K / 2)
    img[:ch, :cw][stars] = white
    idx = (np.arange(n) * W / n).astype(int)
    img = img[:, idx]
    var = pnoise(n, n / 6, seed)
    base = img * (0.96 + 0.08 * var[..., None])
    rough = np.full((n, n), 0.55) + (var - 0.5) * 0.1
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)),
                normal=normal_from_height(var, 0.5)), tile_m



def _blur(a, sigma):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma, mode="wrap")


def _wrapd(n, cx, cy):
    y, x = np.mgrid[0:n, 0:n] + 0.5
    dx = (x - cx + n / 2) % n - n / 2
    dy = (y - cy + n / 2) % n - n / 2
    return dx, dy


def _stamp(acc, cx, cy, half, fn):
    n = acc.shape[0]
    h = int(math.ceil(half)) + 2
    xs = (np.arange(int(cx) - h, int(cx) + h + 1)) % n
    ys = (np.arange(int(cy) - h, int(cy) + h + 1)) % n
    lx = np.arange(int(cx) - h, int(cx) + h + 1) + 0.5 - cx
    ly = np.arange(int(cy) - h, int(cy) + h + 1) + 0.5 - cy
    gx, gy = np.meshgrid(lx, ly)
    acc[np.ix_(ys, xs)] = np.maximum(acc[np.ix_(ys, xs)], fn(gx, gy))


def _rect_fn(hw, hh, ang, soft=0.7):
    c, s_ = math.cos(ang), math.sin(ang)

    def f(gx, gy):
        u, v = gx * c + gy * s_, -gx * s_ + gy * c
        return np.clip(np.minimum(hw - np.abs(u), hh - np.abs(v)) / soft + 0.5, 0, 1)
    return f


def defects(n, seed, tile_m, dust=1.0, smudge=1.0, prints=1.0, scratch=1.0, scuff=1.0):
    rng = _rng(seed)
    px_m = n / tile_m
    specks = (rng.random((n, n)) < dust * 4e-5).astype(float) * (0.3 + 0.7 * rng.random((n, n)))
    fine = _blur(specks, max(0.5, 0.00015 * px_m))
    fine = np.clip(fine / (fine.max() + 1e-9) * 2.0, 0, 1)
    film = np.clip((pnoise(n, n / 3, seed + 1, octaves=4) - 0.5) * 4 * dust, 0, 1) * 0.5
    sm = np.clip((pnoise(n, 0.07 * px_m, seed + 2, octaves=4) - 0.62) * 5, 0, 1) * smudge
    fp = np.zeros((n, n))
    count = int(round(prints * tile_m * tile_m * 6))
    for i in range(count):
        cx, cy = rng.random(2) * n
        a, b = (0.008 + rng.random() * 0.004) * px_m, (0.011 + rng.random() * 0.005) * px_m
        ang = rng.random() * math.pi
        freq = 2 * math.pi / max(1.2, 0.00045 * px_m)
        c, s_ = math.cos(ang), math.sin(ang)

        def f(gx, gy, a=a, b=b, c=c, s_=s_, freq=freq):
            u, v = gx * c + gy * s_, -gx * s_ + gy * c
            r = np.sqrt((u / a) ** 2 + (v / b) ** 2)
            ridge = 0.5 + 0.5 * np.sin(np.sqrt(u * u + (v * 0.8) ** 2) * freq)
            return np.clip(1.2 - r, 0, 1) * ridge
        _stamp(fp, cx, cy, max(a, b) * 1.3, f)
    sc = -scratches(n, seed + 3, count=int(30 * scratch * max(tile_m, 0.2)), max_len=0.12, depth=0.7)
    sc = np.clip(sc, 0, 1)
    scf = np.clip((pnoise(n, 0.06 * px_m, seed + 4, octaves=4) - 0.64) * 4, 0, 1) * scuff
    return {"dust": np.clip(fine + film * 0.2, 0, 1), "smudge": sm, "prints": fp, "scratch": sc, "scuff": scf}


def _apply(base, rough, d, dust_colour=(0.16, 0.15, 0.14), dust_amt=0.35, rough_dust=0.25, rough_smudge=0.10, rough_print=0.12,
           scratch_colour=None, scratch_rough=-0.1):
    dc = np.array(dust_colour)[None, None, :]
    w = (d["dust"] * dust_amt)[..., None]
    base = base * (1 - w) + dc * w
    rough = rough + d["dust"] * rough_dust + d["smudge"] * rough_smudge * 0.5 + d["prints"] * rough_print + d["scuff"] * 0.04
    if scratch_colour is not None:
        sw = d["scratch"][..., None]
        base = base * (1 - sw) + np.array(scratch_colour)[None, None, :] * sw
    rough = rough + d["scratch"] * scratch_rough
    return base, np.clip(rough, 0.02, 1.0)


def mli_flight(n, seed, colour, tile_m=1.2, quilt=0.15, tape=(0.86, 0.84, 0.78), grime=1.0, gloss=0.36, stitch=False, metal=0.7):
    rng = _rng(seed)
    px_m = n / tile_m
    folds = crumple(n, seed, folds=40, kmax=max(2, int(tile_m / 0.25)), sharp=0.8, warp_px=0.05 * px_m)
    pillow = pnoise(n, 0.12 * px_m, seed + 1, octaves=3)
    big, cid, e1 = facets(n, seed + 2, int((tile_m / 0.16) ** 2 * 1.2), 5, stretch=1.6)
    fine, _, _ = facets(n, seed + 3, int((tile_m / 0.022) ** 2), 4, stretch=1.2)
    ridges = crumple(n, seed + 8, folds=120, kmax=max(6, int(tile_m / 0.06)), sharp=1.3, warp_px=0.03 * px_m)
    dimple = np.zeros((n, n))
    tabs = np.zeros((n, n))
    k = max(1, int(round(tile_m / quilt)))
    pitch = n / k
    for i in range(k):
        for j in range(k):
            cx = (i + 0.5 + rng.normal(0, 0.06)) * pitch
            cy = (j + 0.5 + rng.normal(0, 0.06)) * pitch
            r = 0.03 * px_m
            _stamp(dimple, cx, cy, r * 2.5, lambda gx, gy, r=r: np.exp(-(gx * gx + gy * gy) / (r * r)))
            if rng.random() < 0.55:
                hw = (0.012 + rng.random() * 0.008) * px_m
                _stamp(tabs, cx, cy, hw * 1.5, _rect_fn(hw, hw * (0.8 + rng.random() * 0.4), rng.normal(0, 0.15)))
    h = folds * 3.0 + pillow * 2.0 - dimple * 1.5 + ridges * 1.2
    nrm = normal_from_height(h, 9.0 * n / 2048) * 2 - 1
    nrm = nrm + (big - [0, 0, 1]) * 0.35 + (fine - [0, 0, 1]) * 0.3
    lap = np.abs(4 * ridges - np.roll(ridges, 1, 0) - np.roll(ridges, -1, 0) - np.roll(ridges, 1, 1) - np.roll(ridges, -1, 1))
    crease = np.clip(lap / (np.percentile(lap, 99.5) + 1e-9), 0, 1) ** 1.5
    y, x = np.mgrid[0:n, 0:n] + 0.5
    tw = 0.048 * px_m
    ox, oy = rng.random(2) * n
    seam = ((np.abs((x - ox + n / 2) % n - n / 2) < tw / 2) | (np.abs((y - oy + n / 2) % n - n / 2) < tw / 2)).astype(float)
    tape_wr = pnoise(n, 0.01 * px_m, seed + 5, octaves=2)
    t = (x * 0.7 + y * 0.3) / n
    zz = np.abs(((x * 0.3 - y * 0.7) / (0.015 * px_m)) % 1.0 - 0.5) * 2 - 0.5
    stitch_line = np.abs(((y - 0.7 * x - oy * 0.5) % n) - n / 2 + zz * 0.004 * px_m) < 0.0008 * px_m
    stitch = stitch_line.astype(float) * (np.mod(t * n / (0.006 * px_m), 1.0) < 0.6) * float(stitch)
    var = pnoise(n, n / 4, seed + 6, octaves=3)
    fvar = (np.sin(cid * 12.9898) * 43758.5453) % 1.0
    base = tint(var * 0.85 + fvar * 0.15, colour, 0.03) * (1 - 0.06 * crease[..., None])
    rough = gloss + (fvar - 0.5) * 0.03 + crease * 0.06 + (var - 0.5) * 0.08
    tc = np.array(tape)[None, None, :]
    base = base * (1 - seam[..., None]) + tc * (0.97 + 0.06 * tape_wr[..., None]) * seam[..., None]
    rough = rough * (1 - seam) + (0.22 + 0.1 * tape_wr) * seam
    nrm = nrm * (1 - 0.7 * seam[..., None]) + np.array([0, 0, 1.0]) * 0.7 * seam[..., None]
    base = base * (1 - tabs[..., None]) + np.array([0.80, 0.78, 0.70])[None, None, :] * tabs[..., None]
    rough = rough * (1 - tabs) + 0.6 * tabs
    nrm = nrm * (1 - 0.8 * tabs[..., None]) + np.array([0, 0, 1.0]) * 0.8 * tabs[..., None]
    base = base * (1 - 0.85 * stitch[..., None])
    d = defects(n, seed + 7, tile_m, dust=0.5 * grime, smudge=grime, prints=0.4 * grime, scratch=0.0, scuff=grime)
    base, rough = _apply(base, rough, d, dust_amt=0.25, rough_dust=0.15)
    met = np.clip(metal - tabs * metal - d["dust"] * 0.3, 0, 1)
    nrm[..., 2] = np.abs(nrm[..., 2]) + 0.25
    return dict(basecolor=base, roughness=rough, metallic=met, normal=_encode_normal(nrm)), tile_m


def solar_array_flight(n, seed, tile_m=0.40, cell=(0.08, 0.04), gap=0.0015, string_every=4, string_gap=0.004,
                       cell_colour=(0.010, 0.012, 0.032), substrate=(0.16, 0.14, 0.11)):
    rng = _rng(seed)
    px_m = n / tile_m
    y, x = np.mgrid[0:n, 0:n] + 0.5
    cw, ch = cell[0] * px_m, cell[1] * px_m
    col = np.floor(x / cw)
    row = np.floor(y / ch)
    u, v = x - col * cw, y - row * ch
    g = gap * px_m * 0.7
    gl = np.where(np.mod(col, string_every) == 0, string_gap * px_m, g)
    in_cell = (u > gl) & (u < cw - g) & (v > g) & (v < ch - g)
    cc = 0.006 * px_m
    corner = ((u - gl) + (v - g) < cc) | ((cw - g - u) + (ch - g - v) < cc)
    in_cell &= ~corner
    fingers = (np.abs(np.mod(v, 0.0016 * px_m) - 0.0008 * px_m) < 0.35) & in_cell
    bus = (u > gl) & (u < gl + 0.0022 * px_m) & in_cell
    tabs = (~in_cell) & (u < gl + 0.002 * px_m) & (np.abs(np.mod(v, ch / 3) - ch / 6) < 0.0025 * px_m)
    cid = col * 7.13 + row * 13.7
    cvar = (np.sin(cid * 12.9898) * 43758.5453) % 1.0
    ar = pnoise(n, 0.3 * px_m, seed + 1, octaves=2)
    cellc = np.array(cell_colour)[None, None, :] * (0.8 + 0.4 * cvar[..., None])
    cellc = cellc + np.array([0.006, 0.0, 0.010])[None, None, :] * (ar[..., None] - 0.4)
    base = np.where(in_cell[..., None], cellc, np.array(substrate)[None, None, :])
    base = np.where(fingers[..., None], base * 1.6 + 0.01, base)
    base = np.where((bus | tabs)[..., None], np.array([0.62, 0.62, 0.64])[None, None, :], base)
    rough = np.where(in_cell, 0.05, 0.45) + 0.0 * x
    met = np.where(bus | tabs, 1.0, 0.0) + 0.0 * x
    tilt = np.stack([np.sin(cid * 3.1) * 0.02, np.cos(cid * 5.7) * 0.02, np.ones_like(cid)], -1)
    edge = normal_from_height(in_cell.astype(float) * 0.6 + (bus | tabs) * 0.4, 1.2) * 2 - 1
    nrm = np.where(in_cell[..., None], tilt, edge)
    crack = np.zeros((n, n))
    for _ in range(max(1, int(tile_m * tile_m * 8))):
        cx, cy = rng.random(2) * n
        ang = rng.random() * math.pi
        L = (0.01 + rng.random() * 0.02) * px_m
        c, s_ = math.cos(ang), math.sin(ang)
        _stamp(crack, cx, cy, L, lambda gx, gy, c=c, s_=s_, L=L:
               np.clip(0.7 - np.abs(-gx * s_ + gy * c), 0, 1) * (np.abs(gx * c + gy * s_) < L))
    crack *= in_cell
    base = base * (1 - crack[..., None]) + np.array([0.12, 0.12, 0.14])[None, None, :] * crack[..., None]
    d = defects(n, seed + 2, tile_m, dust=0.8, smudge=1.0, prints=1.5, scratch=0.4, scuff=0.5)
    base, rough = _apply(base, rough, d, dust_colour=(0.20, 0.19, 0.18), dust_amt=0.25, rough_dust=0.3, rough_smudge=0.12, rough_print=0.2)
    return dict(basecolor=base, roughness=rough, metallic=met, normal=_encode_normal(nrm)), tile_m


def osr_flight(n, seed, tile_m=0.40, tile=0.05, grout=0.0007):
    rng = _rng(seed)
    px_m = n / tile_m
    k = int(round(tile_m / tile))
    line, x, y = _grid_lines(n, k, grout * px_m)
    tid = np.floor(x / (n / k)) * 3.3 + np.floor(y / (n / k)) * 17.1
    var = (np.sin(tid * 78.233) * 43758.5453) % 1.0
    var2 = (np.sin(tid * 12.9898) * 43758.5453) % 1.0
    base = np.array([0.87, 0.875, 0.89])[None, None, :] * (0.95 + 0.06 * var[..., None])
    base = base * (1 - line[..., None]) + np.array([0.06, 0.06, 0.065])[None, None, :] * line[..., None]
    rough = 0.025 + 0.03 * var2 + line * 0.6
    met = 0.95 - line * 0.9
    tilt = np.stack([(var - 0.5) * 0.03, (var2 - 0.5) * 0.03, np.ones_like(var)], -1)
    nrm = tilt + (normal_from_height(-line, 2.0) * 2 - 1) * [1, 1, 0]
    chip = np.zeros((n, n))
    cell = n / k
    for _ in range(max(2, int(k * k * 0.04))):
        i, j = rng.integers(0, k, 2)
        cx, cy = (i + rng.choice([0.03, 0.97])) * cell, (j + rng.choice([0.03, 0.97])) * cell
        r = (0.002 + rng.random() * 0.004) * px_m
        _stamp(chip, cx, cy, r, lambda gx, gy, r=r: np.clip(r - np.abs(gx) - np.abs(gy), 0, 1))
    base = base * (1 - chip[..., None]) + np.array([0.35, 0.36, 0.38])[None, None, :] * chip[..., None]
    rough = rough + chip * 0.4
    d = defects(n, seed + 3, tile_m, dust=1.0, smudge=1.2, prints=2.0, scratch=0.6, scuff=0.6)
    base, rough = _apply(base, rough, d, dust_amt=0.3, rough_dust=0.35, rough_smudge=0.15, rough_print=0.25, scratch_rough=0.15)
    return dict(basecolor=base, roughness=rough, metallic=np.clip(met, 0, 1), normal=_encode_normal(nrm)), tile_m


def sheet_metal(n, seed, colour, tile_m=0.5, rivet_pitch=0.03, iridite=0.0, rough0=0.45):
    rng = _rng(seed)
    px_m = n / tile_m
    pit = pnoise(n, max(1.5, 0.0004 * px_m), seed, octaves=2)
    var = pnoise(n, 0.15 * px_m, seed + 1, octaves=4)
    mott = pnoise(n, 0.04 * px_m, seed + 2, octaves=4)
    base = tint(var, colour, 0.05) * (0.96 + 0.08 * pit[..., None])
    if iridite:
        shift = (mott[..., None] - 0.5) * iridite * np.array([0.25, 0.05, -0.35])[None, None, :]
        streak = streaks(n, seed + 3, along=0, length_px=0.3 * px_m, width_px=4)
        base = base * (1 + shift) * (1 + (streak[..., None] - 0.5) * 0.15 * iridite)
    rough = rough0 + (pit - 0.5) * 0.12 + (var - 0.5) * 0.08
    h = pit * 0.4
    if rivet_pitch:
        y, x = np.mgrid[0:n, 0:n] + 0.5
        sx = rng.random() * n
        seam = np.abs((x - sx + n / 2) % n - n / 2)
        r = 0.0025 * px_m
        pitch = rivet_pitch * px_m
        dv = np.mod(y, pitch) - pitch / 2
        dd = np.sqrt((seam - 0.008 * px_m) ** 2 + dv ** 2)
        head = np.clip(r - dd + 0.5, 0, 1)
        dome = np.sqrt(np.clip(1 - (dd / r) ** 2, 0, 1))
        joint = np.clip(0.0008 * px_m - seam + 0.5, 0, 1)
        base = base * (1 - head[..., None]) + np.array([0.62, 0.62, 0.63])[None, None, :] * head[..., None]
        base = base * (1 - 0.5 * joint[..., None])
        rough = rough * (1 - head) + 0.3 * head + joint * 0.2
        h = h + dome * 1.5 - joint * 1.0
    d = defects(n, seed + 4, tile_m, dust=0.6, smudge=0.8, prints=0.6, scratch=0.6, scuff=0.8)
    base, rough = _apply(base, rough, d, scratch_colour=(0.80, 0.80, 0.80) if iridite else None, scratch_rough=-0.12)
    h = h - d["scratch"] * 0.8
    return dict(basecolor=base, roughness=rough, metallic=np.full((n, n), 0.9) - d["dust"] * 0.4,
                normal=normal_from_height(h, 1.8)), tile_m


def fabric_boot(n, seed, colour, tile_m=0.3, rough0=0.42):
    px_m = n / tile_m
    y, x = np.mgrid[0:n, 0:n] + 0.5
    warp = (pnoise(n, 0.08 * px_m, seed, octaves=2) - 0.5) * 0.03 * px_m
    k = max(1, int(round(tile_m / 0.045)))
    ph = (y + warp) / n * k
    pleat = np.abs(np.sin(math.pi * ph)) ** 0.6
    cr = crumple(n, seed + 1, folds=70, kmax=8, sharp=1.0, warp_px=0.02 * px_m)
    fine, cid, _ = facets(n, seed + 2, int((tile_m / 0.012) ** 2), 10, stretch=1.3)
    h = pleat * 2.5 + cr * 1.2
    nrm = normal_from_height(h, 7.0 * n / 2048) * 2 - 1 + (fine - [0, 0, 1]) * 0.5
    nrm[..., 2] = np.abs(nrm[..., 2]) + 0.25
    fvar = (np.sin(cid * 12.9898) * 43758.5453) % 1.0
    valley = 1 - pleat
    cvar = pnoise(n, 0.05 * px_m, seed + 4, octaves=3)
    base = tint(cvar * 0.8 + fvar * 0.2, colour, 0.08) * (1 - 0.35 * valley[..., None])
    rough = rough0 + (fvar - 0.5) * 0.06 + valley * 0.1
    d = defects(n, seed + 3, tile_m, dust=1.5, smudge=0.8, prints=0.0, scratch=0.0, scuff=1.0)
    base, rough = _apply(base, rough, d, dust_colour=(0.20, 0.19, 0.18), dust_amt=0.5, rough_dust=0.3)
    return dict(basecolor=base, roughness=rough, metallic=np.full((n, n), 0.55) - d["dust"] * 0.4, normal=_encode_normal(nrm)), tile_m


def worn_coating(n, seed, colour, tile_m=0.3, metallic=0.0, rough0=0.5, bare=(0.75, 0.75, 0.76)):
    px_m = n / tile_m
    peel = pnoise(n, max(2.0, 0.0012 * px_m), seed, octaves=3)
    var = pnoise(n, 0.1 * px_m, seed + 1, octaves=3)
    chips_n = pnoise(n, 0.006 * px_m, seed + 2, octaves=3)
    region = pnoise(n, 0.08 * px_m, seed + 3, octaves=2)
    chips = np.clip((chips_n - 0.74) * 12, 0, 1) * np.clip((region - 0.62) * 8, 0, 1)
    base = tint(var, colour, 0.04) * (0.97 + 0.06 * peel[..., None])
    base = base * (1 - chips[..., None]) + np.array(bare)[None, None, :] * chips[..., None]
    rough = rough0 + (peel - 0.5) * 0.12 + (var - 0.5) * 0.06
    rough = rough * (1 - chips) + 0.3 * chips
    met = metallic * (1 - chips) + chips
    d = defects(n, seed + 4, tile_m, dust=1.0, smudge=1.0, prints=1.2, scratch=1.0, scuff=1.0)
    base, rough = _apply(base, rough, d, scratch_colour=bare, scratch_rough=-0.15)
    met = np.clip(met + d["scratch"] * (1 - metallic), 0, 1)
    h = peel * 0.3 - chips * 1.0 - d["scratch"] * 0.7
    return dict(basecolor=base, roughness=rough, metallic=met, normal=normal_from_height(h, 1.8)), tile_m


def checkerboard(n, seed, tile_m=0.16, squares=12, border=0.08):
    px_m = n / tile_m
    y, x = np.mgrid[0:n, 0:n] + 0.5
    b = border * n
    inner = (x > b) & (x < n - b) & (y > b) & (y < n - b)
    sq = (n - 2 * b) / squares
    chk = ((np.floor((x - b) / sq) + np.floor((y - b) / sq)) % 2 == 0) & inner
    fuzz = pnoise(n, 1.5, seed, octaves=2)
    base = np.where(chk[..., None], np.array([0.035, 0.035, 0.037]), np.array([0.82, 0.82, 0.80]))
    base = base * (0.97 + 0.06 * fuzz[..., None])
    rough = np.where(chk, 0.6, 0.75) + 0.0 * x
    d = defects(n, seed + 1, tile_m, dust=0.5, smudge=0.6, prints=0.8, scratch=0.3, scuff=0.3)
    base, rough = _apply(base, rough, d, dust_amt=0.2)
    return dict(basecolor=base, roughness=rough, metallic=np.zeros((n, n)), normal=normal_from_height(fuzz * 0.2, 1.0)), tile_m


GENERATORS = {f.__name__: f for f in (flag, mli, beta_cloth, panel, brushed, anodised, perforated, solar_cells, osr,
                                      nozzle_metal, composite, cloth, regolith, mli_flight, solar_array_flight, osr_flight,
                                      sheet_metal, fabric_boot, worn_coating, checkerboard)}


def generate(out, sets, res=2048, only=None):
    os.makedirs(out, exist_ok=True)
    tiles = {}
    for i, (name, (gen, kw)) in enumerate(sorted(sets.items())):
        kw = dict(kw)
        n = kw.pop("res", res)
        seed = kw.pop("seed", 1000 + i * 37)
        spec = json.dumps([gen, n, seed, kw], sort_keys=True, default=list)
        stamp = os.path.join(out, name, "spec.json")
        if (only is None or name in only) and not (os.path.exists(stamp) and open(stamp).read() == spec):
            maps, tile_m = GENERATORS[gen](n, seed, **kw)
            save_set(out, name, tile_m, **maps)
            with open(stamp, "w") as f:
                f.write(spec)
            print(f"  {name:24s} {gen:12s} {n}px  tile {tile_m} m")
        with open(os.path.join(out, name, "set.json")) as f:
            tiles[name] = json.load(f)
    with open(os.path.join(out, "tiles.json"), "w") as f:
        json.dump(tiles, f, indent=1)
    return tiles
