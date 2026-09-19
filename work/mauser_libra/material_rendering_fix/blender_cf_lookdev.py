"""Headless Blender look-dev: CF additive formula on the real Mauser mesh.

Not Source ground truth. Answers whether CF maps can look like the target
before more CS:GO VMT experiments.

  D:\\software\\blender\\5.2.1\\blender.exe --background --factory-startup --python this.py
"""
from __future__ import annotations

import json
import os

import bpy
from mathutils import Vector

PROJECT = r"D:\project\cf_to_csgo"
WORK = os.path.join(PROJECT, "work", "mauser_libra")
SKIN = os.path.join(WORK, "decode", "cf_skin_m1896_libra.json")
DIFFUSE = os.path.join(WORK, "material_v2", "upscale", "diffuse_2048.png")
SPECULAR = os.path.join(WORK, "material_v2", "upscale", "specular_2048.png")
NORMAL = os.path.join(WORK, "material_v2", "upscale", "normal_2048.png")
ALPHA = os.path.join(WORK, "material_v2", "upscale", "alpha_2048.png")
EQUIRECT = os.path.join(WORK, "material_rendering_fix", "blender_lookdev", "lobbycube_equirect.png")
OUT = os.path.join(WORK, "material_rendering_fix", "blender_lookdev")
BLEND = os.path.join(OUT, "cf_lookdev.blend")
REPORT = os.path.join(OUT, "blender_report.json")

os.makedirs(OUT, exist_ok=True)

# CFG Properties (M1896_Libra.CFG)
LIGHT_BRIGHTNESS = 0.2
AMBIENT = 0.01
DIFFUSE_BOOST = 0.01
SPEC_EXP = 0.25          # SpecularPower * 0.25
ENV_BRIGHT = 3.0
LIGHT_DIR = Vector((-0.2, -0.9, 0.4)).normalized()


def load_image(path, colorspace):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def new_tex(nodes, img, non_color=False):
    n = nodes.new("ShaderNodeTexImage")
    n.image = img
    if non_color:
        n.interpolation = "Linear"
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def mix_color(nodes, nt, blend, col_a, col_b, fac=1.0):
    n = nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    if isinstance(fac, float):
        n.inputs["Factor"].default_value = fac
    else:
        link(nt, fac, n.inputs["Factor"])
    link(nt, col_a, n.inputs["A"])
    link(nt, col_b, n.inputs["B"])
    return n.outputs["Result"]


def combine_color(nodes, nt, value):
    n = nodes.new("ShaderNodeCombineColor")
    link(nt, value, n.inputs["Red"])
    link(nt, value, n.inputs["Green"])
    link(nt, value, n.inputs["Blue"])
    return n.outputs["Color"]


def separate_g_b(nodes, nt, color):
    n = nodes.new("ShaderNodeSeparateColor")
    link(nt, color, n.inputs["Color"])
    return n.outputs["Green"], n.outputs["Blue"]


FRAME_MESHES = {"PV-Mauser_Libra", "reload", "reload02", "coin", "Line"}


def build_meshes(mat):
    skin = json.loads(open(SKIN, encoding="utf-8").read())
    meshes = [m for m in skin["meshes"]
              if not m["name"].lower().startswith(("fview", "fview-"))]
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    built = []
    for m in meshes:
        verts = [tuple(m["vertices"][i:i + 3]) for i in range(0, len(m["vertices"]), 3)]
        tris = [tuple(m["triangles"][i:i + 3]) for i in range(0, len(m["triangles"]), 3)]
        uvs = m["uvs"]
        me = bpy.data.meshes.new(m["name"])
        me.from_pydata(verts, [], tris)
        me.update()
        uv_layer = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uv_layer.data[li].uv = (uvs[2 * vi], 1.0 - uvs[2 * vi + 1])
        me.materials.append(mat)
        obj = bpy.data.objects.new(m["name"], me)
        bpy.context.scene.collection.objects.link(obj)
        hide = m["name"] not in FRAME_MESHES
        obj.hide_render = hide
        obj.hide_viewport = hide
        built.append({"name": m["name"], "verts": len(verts), "tris": len(tris), "framed": not hide})
        if hide:
            continue
        for v in verts:
            lo = Vector(map(min, lo, v))
            hi = Vector(map(max, hi, v))
    return built, lo, hi


def make_unlit_mat(diff_img):
    mat = bpy.data.materials.new("unlit_diffuse")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    tex = new_tex(nodes, diff_img)
    link(nt, tex.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    link(nt, em.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_cf_mat(diff_img, spec_img, nrm_img, alpha_img, env_img):
    """Additive CF: albedo*(ambient+Lb*N.L+boost) + spec*N.H^e*alpha.g + cube*3*alpha.b."""
    mat = bpy.data.materials.new("cf_additive")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")

    tex_d = new_tex(nodes, diff_img)
    tex_s = new_tex(nodes, spec_img)
    tex_n = new_tex(nodes, nrm_img, True)
    tex_a = new_tex(nodes, alpha_img, True)
    tex_e = nodes.new("ShaderNodeTexEnvironment")
    tex_e.image = env_img

    geom = nodes.new("ShaderNodeNewGeometry")
    nrm = nodes.new("ShaderNodeNormalMap")
    nrm.space = "TANGENT"
    link(nt, tex_n.outputs["Color"], nrm.inputs["Color"])

    # L as world vector
    lvec = nodes.new("ShaderNodeCombineXYZ")
    lvec.inputs["X"].default_value = LIGHT_DIR.x
    lvec.inputs["Y"].default_value = LIGHT_DIR.y
    lvec.inputs["Z"].default_value = LIGHT_DIR.z

    n_out = nrm.outputs["Normal"]
    v_out = geom.outputs["Incoming"]

    ndotl = nodes.new("ShaderNodeVectorMath")
    ndotl.operation = "DOT_PRODUCT"
    link(nt, n_out, ndotl.inputs[0])
    link(nt, lvec.outputs["Vector"], ndotl.inputs[1])
    ndotl_max = nodes.new("ShaderNodeMath")
    ndotl_max.operation = "MAXIMUM"
    ndotl_max.inputs[1].default_value = 0.0
    link(nt, ndotl.outputs["Value"], ndotl_max.inputs[0])

    # H = normalize(L+V)
    hadd = nodes.new("ShaderNodeVectorMath")
    hadd.operation = "ADD"
    link(nt, lvec.outputs["Vector"], hadd.inputs[0])
    link(nt, v_out, hadd.inputs[1])
    hnorm = nodes.new("ShaderNodeVectorMath")
    hnorm.operation = "NORMALIZE"
    link(nt, hadd.outputs["Vector"], hnorm.inputs[0])
    ndoth = nodes.new("ShaderNodeVectorMath")
    ndoth.operation = "DOT_PRODUCT"
    link(nt, n_out, ndoth.inputs[0])
    link(nt, hnorm.outputs["Vector"], ndoth.inputs[1])
    ndoth_max = nodes.new("ShaderNodeMath")
    ndoth_max.operation = "MAXIMUM"
    ndoth_max.inputs[1].default_value = 0.0
    link(nt, ndoth.outputs["Value"], ndoth_max.inputs[0])
    spec_term = nodes.new("ShaderNodeMath")
    spec_term.operation = "POWER"
    spec_term.inputs[1].default_value = SPEC_EXP
    link(nt, ndoth_max.outputs["Value"], spec_term.inputs[0])

    # diffuse_scale = ambient + Lb*N.L + boost
    lb = nodes.new("ShaderNodeMath")
    lb.operation = "MULTIPLY"
    lb.inputs[1].default_value = LIGHT_BRIGHTNESS
    link(nt, ndotl_max.outputs["Value"], lb.inputs[0])
    dscale = nodes.new("ShaderNodeMath")
    dscale.operation = "ADD"
    dscale.inputs[1].default_value = AMBIENT + DIFFUSE_BOOST
    link(nt, lb.outputs["Value"], dscale.inputs[0])
    diff_col = mix_color(nodes, nt, "MULTIPLY", tex_d.outputs["Color"],
                         combine_color(nodes, nt, dscale.outputs["Value"]))

    a_g, a_b = separate_g_b(nodes, nt, tex_a.outputs["Color"])

    spec_mul1 = nodes.new("ShaderNodeMath")
    spec_mul1.operation = "MULTIPLY"
    link(nt, spec_term.outputs["Value"], spec_mul1.inputs[0])
    link(nt, a_g, spec_mul1.inputs[1])
    spec_out = mix_color(nodes, nt, "MULTIPLY", tex_s.outputs["Color"],
                         combine_color(nodes, nt, spec_mul1.outputs["Value"]))

    inv_v = nodes.new("ShaderNodeVectorMath")
    inv_v.operation = "SCALE"
    inv_v.inputs["Scale"].default_value = -1.0
    link(nt, v_out, inv_v.inputs[0])
    refl = nodes.new("ShaderNodeVectorMath")
    refl.operation = "REFLECT"
    link(nt, inv_v.outputs["Vector"], refl.inputs[0])
    link(nt, n_out, refl.inputs[1])
    link(nt, refl.outputs["Vector"], tex_e.inputs["Vector"])

    env_mul = nodes.new("ShaderNodeMath")
    env_mul.operation = "MULTIPLY"
    env_mul.inputs[1].default_value = ENV_BRIGHT
    link(nt, a_b, env_mul.inputs[0])
    env_out = mix_color(nodes, nt, "MULTIPLY", tex_e.outputs["Color"],
                        combine_color(nodes, nt, env_mul.outputs["Value"]))

    sum1 = mix_color(nodes, nt, "ADD", diff_col, spec_out)
    final_col = mix_color(nodes, nt, "ADD", sum1, env_out)

    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    link(nt, final_col, em.inputs["Color"])
    link(nt, em.outputs["Emission"], out.inputs["Surface"])
    return mat


def setup_cycles(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    world = bpy.data.worlds.new("dark")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.04, 0.04, 0.045, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        scene.cycles.device = "GPU"
    except Exception:
        scene.cycles.device = "CPU"


def point_camera(cam, center, direction, dist):
    cam.location = center + Vector(direction).normalized() * dist
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()


def assign_mat(mat):
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.data.materials:
            obj.data.materials[0] = mat


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)

    scene = bpy.context.scene
    setup_cycles(scene)

    diff_img = load_image(DIFFUSE, "sRGB")
    spec_img = load_image(SPECULAR, "sRGB")
    nrm_img = load_image(NORMAL, "Non-Color")
    alpha_img = load_image(ALPHA, "Non-Color")
    env_img = load_image(EQUIRECT, "sRGB")

    unlit = make_unlit_mat(diff_img)
    cfmat = make_cf_mat(diff_img, spec_img, nrm_img, alpha_img, env_img)

    built, lo, hi = build_meshes(unlit)
    center = (lo + hi) / 2.0
    diag = max((hi - lo).length, 1.0)
    dist = diag * 1.85

    cam_data = bpy.data.cameras.new("LookCam")
    cam = bpy.data.objects.new("LookCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.lens = 70
    cam_data.clip_start = 0.01
    cam_data.clip_end = dist * 20

    views = {
        "front": (0.0, -1.0, 0.35),
        "three_quarter": (0.85, -1.0, 0.45),
    }
    jobs = (("unlit", unlit), ("cf_additive", cfmat))
    written = []
    for shader_name, mat in jobs:
        assign_mat(mat)
        for view_name, direction in views.items():
            point_camera(cam, center, direction, dist)
            path = os.path.join(OUT, f"{shader_name}_{view_name}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            written.append(path)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    json.dump({
        "engine": scene.render.engine,
        "samples": scene.cycles.samples,
        "device": scene.cycles.device,
        "formula": "albedo*(ambient+Lb*N.L+boost) + spec*(N.H^0.25)*alpha.g + cube*3*alpha.b",
        "cfg": {
            "LightBrightness": LIGHT_BRIGHTNESS,
            "AmbientLightColor": AMBIENT,
            "DiffuseBoost": DIFFUSE_BOOST,
            "SpecularPower_x_0.25": SPEC_EXP,
            "EnvCubeMapBrightness": ENV_BRIGHT,
        },
        "meshes": built,
        "bbox_min": list(lo),
        "bbox_max": list(hi),
        "outputs": written,
        "note": "Blender look-dev of recovered CF additive formula. Not CS:GO runtime truth.",
    }, open(REPORT, "w", encoding="utf-8"), indent=1)
    print("lookdev done", written)


if __name__ == "__main__":
    main()
