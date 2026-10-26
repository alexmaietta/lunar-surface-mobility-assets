import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

import assetcfg
import geo as G

VIEWS = {
    "front_three_quarter": ((17.0, -12.0, 4.0), (0, 0, 4.1), 45),
    "side": ((0.0, -21.0, 3.2), (0, 0, 4.1), 45),
    "low_engine": ((5.2, -3.6, 0.35), (0, 0, 1.9), 24),
    "top_deck": ((6.5, -5.5, 12.0), (0, 0, 7.6), 35),
    "thumb": ((16.0, -11.0, 4.6), (0, 0, 4.1), 40),
}


def setup_render(samples, res):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == dev_type
            sc.cycles.device = "GPU"
            break
        except Exception:
            continue
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = "PNG" if res[0] <= 256 else "JPEG"
    sc.render.image_settings.quality = 92
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.35


def _clear_env():
    for ob in [o for o in bpy.data.objects if o.type in ("LIGHT", "CAMERA") or o.name.startswith(("ground", "rock_", "env_"))]:
        if ob.type == "CAMERA" and ob.name.startswith("scalpss"):
            continue
        bpy.data.objects.remove(ob)


def _ground_material(tex_dir):
    m = bpy.data.materials.get("env_regolith")
    if m:
        return m
    m = bpy.data.materials.new("env_regolith")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    for kind, inp, col in (("basecolor", "Base Color", True), ("roughness", "Roughness", False)):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(tex_dir, "regolith", f"regolith_{kind}.png"), check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if col else "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], b.inputs[inp])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(tex_dir, "regolith", "regolith_normal.png"), check_existing=True)
    t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(t.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def _world(color, strength, camera_black=False):
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    if isinstance(color, tuple):
        bg.inputs["Color"].default_value = (*color, 1)
    else:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.26, 1)
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.02, 1)
        ramp.color_ramp.elements[0].position = 0.40
        ramp.color_ramp.elements[1].position = 0.62
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    if camera_black:
        lp, black, mix = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeMixShader")
        black.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        nt.links.new(bg.outputs[0], mix.inputs[1])
        nt.links.new(black.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(bg.outputs[0], out.inputs["Surface"])


def _plane(name, size, z, mat):
    me = bpy.data.meshes.new(name)
    s = size / 2
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def lunar(tex_dir):
    _clear_env()
    _world((0.02, 0.02, 0.025), 0.6, camera_black=True)
    g = _plane("ground", 400, 0.0, _ground_material(tex_dir))
    g.data.uv_layers.new()
    sun = bpy.data.objects.new("env_sun", bpy.data.lights.new("env_sun", "SUN"))
    sun.data.energy = 6.0
    sun.data.angle = math.radians(0.53)
    sun.rotation_euler = (math.radians(68), 0, math.radians(-35))
    bpy.context.scene.collection.objects.link(sun)
    fill = bpy.data.objects.new("env_fill", bpy.data.lights.new("env_fill", "SUN"))
    fill.data.energy = 0.15
    fill.rotation_euler = (math.radians(60), 0, math.radians(150))
    bpy.context.scene.collection.objects.link(fill)


def camera(pos, target, lens):
    cam = bpy.data.objects.new("env_cam", bpy.data.cameras.new("env_cam"))
    cam.data.lens = lens
    cam.data.clip_end = 2000
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def attach(cfg, dep, mount_site, dep_site):
    mount = bpy.data.objects[f"site:{mount_site}"].matrix_world.translation.copy()
    path = os.path.join(assetcfg.ROOT, "build", dep, f"{dep}.blend")
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = list(src.objects)
    for ob in dst.objects:
        if ob is None:
            continue
        bpy.context.scene.collection.objects.link(ob)
    for ob in dst.objects:
        if ob is not None and ob.parent is None:
            ob.location = ob.location + mount
    print(f"attached {dep} at {tuple(round(c, 3) for c in mount)}")


def add_lights(scale=1.0):
    import json
    from mathutils import Matrix
    n = 0
    for rec in json.loads(bpy.context.scene.get("sites", "[]")):
        if rec["kind"] != "light":
            continue
        ob = bpy.data.objects.get(f"site:{rec['name']}")
        if ob is None:
            continue
        a = rec.get("attrs", {})
        r = float(a.get("radius_m", 0.05))
        ld = bpy.data.lights.new(f"lamp_{rec['name']}", "SPOT")
        ld.energy = float(a.get("intensity", 30000.0)) * r * r * 0.25 * scale
        ld.shadow_soft_size = r
        ld.spot_size = math.radians(float(a.get("cone_deg", 60.0)) * 2)
        ld.spot_blend = 0.6
        k = float(a.get("colour_k", 5600.0))
        ld.color = (1.0, min(1.0, 0.55 + k / 12000), min(1.0, 0.25 + k / 8000))
        lo = bpy.data.objects.new(f"lamp_{rec['name']}", ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.parent = ob
        lo.matrix_parent_inverse = Matrix.Identity(4)
        lo.matrix_basis = Matrix.Rotation(math.pi, 4, "X")
        n += 1
    print(f"added {n} lights")


def pose(items):
    import json
    for kv in items:
        name, val = kv.split("=")
        ob = bpy.data.objects[f"link:{name}"]
        j = json.loads(ob["joint"])
        if j["type"] == "revolute":
            ob.rotation_mode = "AXIS_ANGLE"
            ob.rotation_axis_angle = (float(val), *j["axis"])
        elif j["type"] == "prismatic":
            ob.location = ob.location + Vector(j["axis"]) * float(val)
    bpy.context.view_layer.update()


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    asset = assetcfg.arg(a, "--asset")
    cfg = assetcfg.load(asset)
    views = getattr(cfg, "RENDER_VIEWS", VIEWS)
    only = [v for v in assetcfg.arg(a, "--views", "").split(",") if v]
    out = os.path.abspath(assetcfg.arg(a, "--out", os.path.join(assetcfg.ROOT, "build", asset, "renders")))
    os.makedirs(out, exist_ok=True)
    tex_dir = assetcfg.build_dir(asset, "textures")
    sel = dict(kv.split(":") for kv in assetcfg.arg(a, "--variant", "").split(",") if kv)
    G.prune_variants(cfg, sel)
    vj = [f"{j}={q}" for st, o in sel.items() for j, q in getattr(cfg, "GEOMETRY_VARIANT_JOINTS", {}).get(st, {}).get(o, {}).items()]
    pose(vj + [kv for kv in assetcfg.arg(a, "--pose", "").split(",") if kv])
    if "--lights" in a:
        add_lights(float(assetcfg.arg(a, "--light-scale", "1.0")))
    for spec in [x for x in assetcfg.arg(a, "--attach", "").split(",") if x]:
        set_name, opt = spec.split(":")
        attach(cfg, *cfg.ATTACHMENTS[set_name][opt])
    setup_render(int(assetcfg.arg(a, "--samples", "128")), tuple(int(x) for x in assetcfg.arg(a, "--res", "1600x1200").split("x")))
    lunar(tex_dir)
    if assetcfg.arg(a, "--sun"):
        az, el = (math.radians(float(v)) for v in assetcfg.arg(a, "--sun").split(","))
        sun = bpy.data.objects["env_sun"]
        sun.rotation_mode = "QUATERNION"
        sun.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(
            Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))))
    if "--night" in a:
        bpy.data.objects["env_sun"].data.energy = 0.0
        bpy.data.objects["env_fill"].data.energy = 0.004
    for name, (pos, tgt, lens) in views.items():
        if only and name not in only:
            continue
        for ob in [o for o in bpy.data.objects if o.name == "env_cam"]:
            bpy.data.objects.remove(ob)
        camera(pos, tgt, lens)
        ext = "png" if bpy.context.scene.render.image_settings.file_format == "PNG" else "jpg"
        bpy.context.scene.render.filepath = os.path.join(out, f"{name}.{ext}")
        bpy.ops.render.render(write_still=True)
        print("rendered", name)


if __name__ == "__main__":
    main()
