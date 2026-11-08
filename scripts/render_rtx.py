import math
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assetcfg

FILM = 36.0
GROUND = 2000.0
SUN = (-70.0, 20.0)


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def look_at(eye, target):
    f = norm(tuple(t - e for t, e in zip(target, eye)))
    x = norm(cross(f, (0.0, 0.0, 1.0)))
    y = cross(x, f)
    rows = (x, y, tuple(-c for c in f), eye)
    return "( " + ", ".join("(%s, %s)" % (", ".join("%.6f" % c for c in r), "1" if i == 3 else "0") for i, r in enumerate(rows)) + " )"


def parse_variants(s):
    return dict(kv.split("=", 1) for kv in s.split(",") if kv) if s else {}


def ground_material(asset_id):
    tex = os.path.join(assetcfg.ROOT, "build", asset_id, "textures", "regolith")
    if not os.path.exists(os.path.join(tex, "regolith_basecolor.png")):
        return """
        def Shader "Surface" {
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.30, 0.29, 0.28)
            float inputs:roughness = 0.95
            token outputs:surface
        }
        token outputs:surface.connect = </World/Looks/Regolith/Surface.outputs:surface>"""
    tex_node = lambda name, kind, out, cs: f"""
        def Shader "{name}" {{
            uniform token info:id = "UsdUVTexture"
            asset inputs:file = @{tex}/regolith_{kind}.png@
            token inputs:sourceColorSpace = "{cs}"
            token inputs:wrapS = "repeat"
            token inputs:wrapT = "repeat"
            float2 inputs:st.connect = </World/Looks/Regolith/St.outputs:result>
            {out}
        }}"""
    return f"""
        def Shader "St" {{
            uniform token info:id = "UsdPrimvarReader_float2"
            token inputs:varname = "st"
            float2 outputs:result
        }}
        {tex_node("Base", "basecolor", "float3 outputs:rgb", "sRGB")}
        {tex_node("Rough", "roughness", "float outputs:r", "raw")}
        {tex_node("Normal", "normal", "float3 outputs:rgb", "raw").replace('token inputs:wrapS', 'float4 inputs:scale = (2, 2, 2, 1)\n            float4 inputs:bias = (-1, -1, -1, 0)\n            token inputs:wrapS')}
        def Shader "Surface" {{
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor.connect = </World/Looks/Regolith/Base.outputs:rgb>
            float inputs:roughness.connect = </World/Looks/Regolith/Rough.outputs:r>
            normal3f inputs:normal.connect = </World/Looks/Regolith/Normal.outputs:rgb>
            float inputs:metallic = 0
            token outputs:surface
        }}
        token outputs:surface.connect = </World/Looks/Regolith/Surface.outputs:surface>"""


def camera(name, view, res, ev):
    eye, target, lens = view
    return f"""
    def Camera "{name}" {{
        matrix4d xformOp:transform = {look_at(eye, target)}
        uniform token[] xformOpOrder = ["xformOp:transform"]
        float focalLength = {lens}
        float horizontalAperture = {FILM}
        float verticalAperture = {FILM * res[1] / res[0]:.4f}
        float2 clippingRange = (0.05, 2000)
        float exposure = {ev}
    }}"""


def product(name, res, spp, mode="PathTracing", spectral=False, cam=None):
    spec = ""
    if mode == "PathTracing":
        spec = f"""
        uint omni:rtx:pt:samplesPerPixel = {spp}
        uint omni:rtx:pt:limits:maxBounces = 6
        bool omni:rtx:pt:ris:meshLights = 1
        custom bool omni:rtx:pathtracing:spectral:enabled = {str(spectral).lower()}
        custom float omni:rtx:pathtracing:spectral:wavelengthMin = 360
        custom float omni:rtx:pathtracing:spectral:wavelengthMax = 830"""
    return f"""
    def RenderProduct "{name}" {{
        int2 resolution = ({res[0]}, {res[1]})
        rel camera = <{cam or f"/World/Cameras/{name}"}>
        rel orderedVars = [<LdrColor>]
        token omni:rtx:rendermode = "{mode}"{spec}
        def RenderVar "LdrColor" {{
            string sourceName = "LdrColor"
        }}
    }}"""


def lamp_overs(usd, offset):
    from pxr import Gf, Usd, UsdLux
    if offset <= 0:
        return ""
    st = Usd.Stage.Open(usd)
    root = st.GetDefaultPrim().GetPath()
    tree = {}
    for prim in st.Traverse():
        if not prim.HasAPI(UsdLux.LightAPI) or prim.IsA(UsdLux.DomeLight) or prim.IsA(UsdLux.DistantLight):
            continue
        orient = prim.GetAttribute("xformOp:orient").Get()
        beam = Gf.Rotation(Gf.Quatd(orient)).TransformDir(Gf.Vec3d(0, 0, -1)) if orient is not None else Gf.Vec3d(0, 0, -1)
        pos = Gf.Vec3d(prim.GetAttribute("xformOp:translate").Get() or (0, 0, 0)) + beam * offset
        node = tree
        for name in prim.GetPath().MakeRelativePath(root).pathString.split("/"):
            node = node.setdefault(name, {})
        node[None] = "double3 xformOp:translate = (%.5f, %.5f, %.5f)" % tuple(pos)

    def emit(node, depth):
        pad = "    " * depth
        out = [pad + node[None]] if None in node else []
        for k, v in node.items():
            if k is not None:
                out += [f'{pad}over "{k}"', pad + "{", emit(v, depth + 1), pad + "}"]
        return "\n".join(out)

    return emit(tree, 2)


def lights(night, sun, dome):
    if night:
        return ""
    az, el = (math.radians(a) for a in sun)
    pos = (math.cos(el) * math.cos(az) * 100, math.cos(el) * math.sin(az) * 100, math.sin(el) * 100)
    fill = "" if dome <= 0 else f"""
    def DomeLight "Fill"
    {{
        float inputs:intensity = {dome}
        color3f inputs:color = (0.85, 0.88, 0.95)
        bool visibleInPrimaryRay = false
    }}
"""
    return f"""
    def DistantLight "Sun"
    {{
        matrix4d xformOp:transform = {look_at(pos, (0, 0, 0))}
        uniform token[] xformOpOrder = ["xformOp:transform"]
        float inputs:intensity = 3000
        float inputs:angle = 0.53
        color3f inputs:color = (1, 0.98, 0.95)
    }}
{fill}"""


def pose_layer(usd, poses, out):
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    if not poses:
        return usd
    st = Usd.Stage.Open(usd)
    joints = {p.GetName(): p for p in st.Traverse() if p.IsA(UsdPhysics.RevoluteJoint) or p.IsA(UsdPhysics.PrismaticJoint)}
    layer = Sdf.Layer.CreateNew(os.path.join(out, "posed.usda"))
    layer.subLayerPaths.append(usd)
    layer.defaultPrim = st.GetDefaultPrim().GetName()
    edit = Usd.Stage.Open(layer)
    unit = {"X": Gf.Vec3d(1, 0, 0), "Y": Gf.Vec3d(0, 1, 0), "Z": Gf.Vec3d(0, 0, 1)}
    for name, value in poses.items():
        if name not in joints:
            raise SystemExit(f"no joint {name} in {usd}")
        j = joints[name]
        child = st.GetPrimAtPath(j.GetRelationship("physics:body1").GetTargets()[0])
        rot0 = Gf.Rotation(Gf.Quatd(j.GetAttribute("physics:localRot0").Get()))
        axis = rot0.TransformDir(unit[j.GetAttribute("physics:axis").Get()])
        pivot = Gf.Vec3d(j.GetAttribute("physics:localPos0").Get())
        local = UsdGeom.Xformable(child).GetLocalTransformation()
        if j.IsA(UsdPhysics.RevoluteJoint):
            move = Gf.Matrix4d().SetTranslate(-pivot) * Gf.Matrix4d().SetRotate(Gf.Rotation(axis, value)) * Gf.Matrix4d().SetTranslate(pivot)
        else:
            move = Gf.Matrix4d().SetTranslate(axis * value)
        m = local * move
        prim = edit.OverridePrim(child.GetPath())
        prim.GetAttribute("xformOp:translate").Set(m.ExtractTranslation())
        prim.GetAttribute("xformOp:orient").Set(Gf.Quatd(m.ExtractRotationQuat()))
    layer.Save()
    return layer.realPath


def sensor_paths(usd, names):
    from pxr import Usd, UsdGeom
    st = Usd.Stage.Open(usd)
    root = st.GetDefaultPrim().GetPath()
    found = {p.GetName(): p.GetPath() for p in st.Traverse() if p.IsA(UsdGeom.Camera) and p.GetName() in names}
    missing = [n for n in names if n not in found]
    if missing:
        raise SystemExit(f"cameras not found in {usd}: {missing}")
    return {n: "/World/" + os.path.basename(usd).rsplit(".", 1)[0] + "/" + found[n].MakeRelativePath(root).pathString for n in names}


def scene(asset_id, usd, views, variants, night, res, spp, sun, dome, offset, ev, mode="PathTracing", spectral=False, sensors=None):
    root = os.path.basename(usd).rsplit(".", 1)[0]
    sel = "".join(f'\n            string {k} = "{v}"' for k, v in variants.items())
    g = GROUND / 2
    cams = "".join(camera(n, v, res, ev) for n, v in views.items())
    prods = "".join(product(n, res, spp, mode, spectral) for n in views)
    prods += "".join(product(n, res, spp, mode, spectral, cam=p) for n, p in (sensors or {}).items())
    lit = lights(night, sun, dome)
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{root}" (
        prepend references = @{usd}@
        variants = {{{sel}
        }}
    )
    {{
{lamp_overs(usd, offset)}
    }}

    def Mesh "Ground" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        int[] faceVertexCounts = [4]
        int[] faceVertexIndices = [0, 1, 2, 3]
        point3f[] points = [(-{g}, -{g}, 0), ({g}, -{g}, 0), ({g}, {g}, 0), (-{g}, {g}, 0)]
        normal3f[] normals = [(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)] (interpolation = "vertex")
        texCoord2f[] primvars:st = [(0, 0), ({GROUND / 4}, 0), ({GROUND / 4}, {GROUND / 4}), (0, {GROUND / 4})] (interpolation = "vertex")
        float3[] extent = [(-{g}, -{g}, 0), ({g}, {g}, 0)]
        uniform token subdivisionScheme = "none"
        rel material:binding = </World/Looks/Regolith>
    }}

    def Scope "Looks"
    {{
        def Material "Regolith"
        {{{ground_material(asset_id)}
        }}
    }}

{lit}
    def Scope "Cameras"
    {{{cams}
    }}
}}

def Scope "Render"
{{{prods}
}}
"""


def main(argv):
    import ovrtx
    import ovstage
    asset_id = assetcfg.arg(argv, "--asset", "lunar_cruiser")
    cfg = assetcfg.load(asset_id)
    usd = os.path.abspath(assetcfg.arg(argv, "--usd", os.path.join(assetcfg.ROOT, "build", asset_id, "usd", asset_id, f"{asset_id}.usda")))
    names = assetcfg.arg(argv, "--views", "rear_patio,front_three_quarter").split(",")
    views = {n: cfg.RENDER_VIEWS[n] for n in names}
    variants = parse_variants(assetcfg.arg(argv, "--variant", ""))
    night = "--night" in argv
    if night:
        variants.setdefault("Lights", "on")
    res = tuple(int(v) for v in assetcfg.arg(argv, "--res", "1600x1200").split("x"))
    spp = int(assetcfg.arg(argv, "--spp", "256"))
    sun = tuple(float(v) for v in assetcfg.arg(argv, "--sun", "%g,%g" % SUN).split(","))
    dome = float(assetcfg.arg(argv, "--dome", "40"))
    offset = float(assetcfg.arg(argv, "--lamp-offset", "0.0"))
    ev = float(assetcfg.arg(argv, "--exposure", "3" if night else "0"))
    out = assetcfg.arg(argv, "--out", os.path.join(assetcfg.ROOT, "build", asset_id, "rtx"))
    mode = assetcfg.arg(argv, "--mode", "PathTracing")
    spectral = "--spectral" in argv
    frames = int(assetcfg.arg(argv, "--frames", "2" if mode == "PathTracing" else "48"))
    os.makedirs(out, exist_ok=True)
    poses = {k: float(v) for k, v in (kv.split("=") for kv in assetcfg.arg(argv, "--pose", "").split(",") if kv)}
    usd = pose_layer(usd, poses, out)
    sensors = sensor_paths(usd, [n for n in assetcfg.arg(argv, "--sensors", "").split(",") if n])
    usda = scene(asset_id, usd, views, variants, night, res, spp, sun, dome, offset, ev, mode, spectral, sensors)
    names = names + list(sensors)
    with open(os.path.join(out, "render_stage.usda"), "w") as f:
        f.write(usda)
    t = time.time()
    renderer = ovrtx.Renderer(ovrtx.RendererConfig(enable_spectral_rendering=spectral, log_file_path=os.path.join(out, "ovrtx.log")))
    stage = ovstage.Stage("render_rtx")
    renderer.attach_ovstage(stage)
    ovstage.population.open_usd_from_string(stage, usda, ordinal=1)
    stage.advance_write_floor(1, ovstage.Scope.ALL).wait()
    print(f"loaded in {time.time() - t:.1f}s")
    suffix = ("_night" if night else "") + ("_spectral" if spectral else "") + ("_rt" if mode != "PathTracing" else "")
    for i, n in enumerate(names):
        t = time.time()
        for _ in range(frames):
            products = renderer.step(render_products={f"/Render/{n}"}, delta_time=1.0 / 60, ordinal=1)
        for _, p in products.items():
            for fr in p.frames:
                var = fr.render_vars[f"/Render/{n}/LdrColor"].map(device=ovrtx.Device.CPU)
                px = np.from_dlpack(var).copy()
                var.unmap()
                del var
        del products
        img = Image.fromarray(px[..., :3])
        path = os.path.join(out, f"{n}{suffix}.png" if res[0] <= 256 else f"{n}{suffix}.jpg")
        img.save(path, quality=92) if path.endswith(".jpg") else img.save(path)
        print(f"{path} {time.time() - t:.1f}s")
    renderer.detach_ovstage()
    stage.destroy()
    renderer.destroy()


if __name__ == "__main__":
    main(sys.argv[1:])
