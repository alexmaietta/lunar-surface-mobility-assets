import json
import math
import os

import numpy as np

K_M = 683.002
_CIE = None
XYZ_TO_REC709 = np.array([[3.2404542, -1.5371385, -0.4985314],
                          [-0.9692660, 1.8760108, 0.0415560],
                          [0.0556434, -0.2040259, 1.0572252]])


def cie():
    global _CIE
    if _CIE is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cie1931_2deg.json")) as f:
            d = json.load(f)
        _CIE = {k: np.asarray(d[k], float) for k in ("nm", "x", "y", "z")}
    return _CIE


def led_spectrum(peak_nm, fwhm_nm, step_nm=1.0, span_sigma=4.0):
    s = fwhm_nm / (2 * math.sqrt(2 * math.log(2)))
    lo, hi = peak_nm - span_sigma * s, peak_nm + span_sigma * s
    nm = np.arange(math.floor(lo), math.ceil(hi) + step_nm, step_nm)
    v = np.exp(-0.5 * ((nm - peak_nm) / s) ** 2)
    v[0] = v[-1] = 0.0
    return [(float(a), float(round(b, 6))) for a, b in zip(nm, v)]


def spectrum_from_bands(bands, step_nm=1.0):
    lo = min(p - 4 * f for p, f, _ in bands)
    hi = max(p + 4 * f for p, f, _ in bands)
    nm = np.arange(math.floor(lo), math.ceil(hi) + step_nm, step_nm)
    v = np.zeros_like(nm, float)
    for p, f, w in bands:
        s = f / (2 * math.sqrt(2 * math.log(2)))
        v += w * np.exp(-0.5 * ((nm - p) / s) ** 2)
    v /= v.max()
    v[0] = v[-1] = 0.0
    return [(float(a), float(round(b, 6))) for a, b in zip(nm, v)]


def _sample(spectrum):
    c = cie()
    nm = c["nm"]
    a = np.asarray(spectrum, float)
    s = np.interp(nm, a[:, 0], a[:, 1], left=0.0, right=0.0)
    return nm, s


def luminous_efficacy(spectrum):
    a = np.asarray(spectrum, float)
    total = np.trapezoid(a[:, 1], a[:, 0])
    if total <= 0:
        return 0.0
    nm, s = _sample(spectrum)
    return float(K_M * np.trapezoid(s * cie()["y"], nm) / total)


def lumens(radiant_w, spectrum):
    return radiant_w * luminous_efficacy(spectrum)


def xyz(spectrum):
    nm, s = _sample(spectrum)
    c = cie()
    return np.array([np.trapezoid(s * c[k], nm) for k in ("x", "y", "z")])


def linear_rgb(spectrum):
    X = xyz(spectrum)
    if X[1] <= 0 and X.sum() <= 0:
        return (1.0, 1.0, 1.0), 1.0
    rgb = XYZ_TO_REC709 @ X
    rgb = np.clip(rgb, 0, None)
    rgb = rgb / max(rgb.max(), 1e-9)
    lum = float(0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2])
    return tuple(float(round(c, 5)) for c in rgb), lum


def blackbody_rgb(kelvin):
    nm = cie()["nm"]
    lam = nm * 1e-9
    h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
    s = 1.0 / (lam ** 5 * (np.exp(h * c / (lam * k * kelvin)) - 1.0))
    return linear_rgb(list(zip(nm, s / s.max())))


def beam_profile(theta, phi, fwhm_h_deg, fwhm_v_deg, shape=2.0, cutoff_deg=90.0):
    a, b = math.radians(fwhm_h_deg) / 2, math.radians(fwhm_v_deg) / 2
    half = 1.0 / np.sqrt((np.cos(phi) / a) ** 2 + (np.sin(phi) / b) ** 2)
    i = np.exp(-math.log(2) * (theta / half) ** shape)
    return np.where(theta <= math.radians(cutoff_deg), i, 0.0)


def write_ies(path, lumens_total, fwhm_h_deg, fwhm_v_deg, shape=2.0, cutoff_deg=90.0, size_m=(0.1, 0.1), label="", notes=()):
    va = np.arange(0.0, 180.01, 2.5)
    ha = np.arange(0.0, 360.01, 5.0)
    th, ph = np.meshgrid(np.radians(va), np.radians(ha))
    rel = beam_profile(th, ph, fwhm_h_deg, fwhm_v_deg, shape, cutoff_deg)

    dth, dph = math.radians(2.5), math.radians(5.0)
    w_th = np.full(va.shape, dth)
    w_th[0] = w_th[-1] = dth / 2
    w_ph = np.full(ha.shape, dph)
    w_ph[0] = w_ph[-1] = dph / 2
    flux_per_cd = float((rel * np.sin(th) * w_th[None, :] * w_ph[:, None]).sum())
    cd = rel * (lumens_total / flux_per_cd)
    lines = ["IESNA:LM-63-2002",
             "[TEST] synthetic profile, lunar-surface-mobility-assets scripts/photometry.py",
             "[MANUFAC] lunar-surface-mobility-assets (not a measured luminaire)",
             f"[LUMINAIRE] {label}",
             f"[OTHER] elliptical super-Gaussian beam, FWHM {fwhm_h_deg:g} x {fwhm_v_deg:g} deg, shape {shape:g}, cutoff {cutoff_deg:g} deg"]
    lines += [f"[OTHER] {n}" for n in notes]
    lines += ["TILT=NONE",
              f"1 {lumens_total:.3f} 1.0 {len(va)} {len(ha)} 1 2 {size_m[0]:.4f} {size_m[1]:.4f} 0.0",
              "1.0 1.0 0.0"]

    def block(vals, per=10):
        vals = [f"{v:.4g}" for v in vals]
        return [" ".join(vals[i:i + per]) for i in range(0, len(vals), per)]

    lines += block(va) + block(ha)
    for row in cd:
        lines += block(row)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\r\n".join(lines) + "\r\n")
    return float(cd.max())


def light_spec(attrs):
    out = {"shape": attrs.get("shape", "disk")}
    if "peak_nm" in attrs:
        spec = led_spectrum(float(attrs["peak_nm"]), float(attrs.get("fwhm_nm", 20.0)))
        out["spectrum"] = spec
        out["rgb"], out["rgb_luminance"] = linear_rgb(spec)
        out["efficacy"] = luminous_efficacy(spec)
    else:
        out["spectrum"] = None
        out["rgb"], out["rgb_luminance"] = blackbody_rgb(float(attrs.get("colour_k", 5600.0)))
        out["efficacy"] = 300.0
    if "lumens" in attrs:
        out["lumens"] = float(attrs["lumens"])
    elif "radiant_w" in attrs:
        out["lumens"] = float(attrs["radiant_w"]) * out["efficacy"]
    else:
        out["lumens"] = None
    if out["shape"] == "rect":
        out["area"] = float(attrs["width_m"]) * float(attrs["height_m"])
    else:
        out["area"] = math.pi * float(attrs.get("radius_m", 0.05)) ** 2
    if out["spectrum"] is not None and out["efficacy"] < 0.5:
        out["rgb"], out["rgb_luminance"], out["lumens"], out["intensity"] = (0.0, 0.0, 0.0), 0.0, 0.0, 0.0
        return out
    if out["lumens"] is not None:


        out["intensity"] = out["lumens"] / (math.pi * out["area"] * max(out["rgb_luminance"], 1e-4))
    else:
        out["intensity"] = float(attrs.get("intensity", 30000.0))
    return out
