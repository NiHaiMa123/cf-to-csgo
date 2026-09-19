"""Blender review stills for user approval. Do not deploy to the game.

Side view matches the user Blender screenshot composition.
Shading uses CF spec energy (clip(diff*0.25+spec)) plus studio lights,
aiming at the CF in-game champagne metal. Approve these stills before
any CS:GO transfer.
"""
from __future__ import annotations

import json
import math
import os

import bpy
from mathutils import Euler, Vector

PROJECT = r"D:\project\cf_to_csgo"
WORK = os.path.join(PROJECT, "work", "mauser_libra")
SKIN = os.path.join(WORK, "decode", "cf_skin_m1896_libra.json")
DIFFUSE = os.path.join(WORK, "material_v2", "upscale", "diffuse_2048.png")
SPECULAR = os.path.join(WORK, "material_v2", "upscale", "specular_2048.png")
NORMAL = os.path.join(WORK, "material_v2", "upscale", "normal_2048.png")
BAKED = os.path.join(WORK, "material_rendering_fix", "bake_spec_to_base", "cf_mauser_libra_baked_rgb.png")
OUT = os.path.join(WORK, "material_rendering_fix", "blender_review")
BLEND = os.path.join(OUT, "review.blend")
REPORT = os.path.join(OUT, "review_report.json")
FRAME_MESHES = {"PV-Mauser_Libra", "reload", "reload02", "coin", "Line"}

os.makedirs(OUT, exist_ok=True)


def load_img(path, space):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = space
    return img


def link(nt, a, b):
    nt.links.new(a, b)


def make_metal_mat(baked, nrm):
    mat = bpy.data.materials.new("cf_review_metal")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = baked
    ntex = nodes.new("ShaderNodeTexImage")
    ntex.image = nrm
    nmap = nodes.new("ShaderNodeNormalMap")
    nmap.space = "TANGENT"
    nmap.inputs["Strength"].default_value = 0.6
    link(nt, ntex.outputs["Color"], nmap.inputs["Color"])
    link(nt, nmap.outputs["Normal"], bsdf.inputs["Normal"])
    link(nt, tex.outputs["Color"], bsdf.inputs["Base Color"])
    sep = nodes.new("ShaderNodeSeparateColor")
    link(nt, tex.outputs["Color"], sep.inputs["Color"])
    lum = nodes.new("ShaderNodeMath")
    lum.operation = "MULTIPLY_ADD"
    # approx luma
    # use Greater/roughness from inverse brightness of baked gold
    rgb2bw = nodes.new("ShaderNodeRGBToBW")
    link(nt, tex.outputs["Color"], rgb2bw.inputs["Color"])
    met = nodes.new("ShaderNodeMath")
    met.operation = "MULTIPLY"
    met.inputs[1].default_value = 0.9
    link(nt, rgb2bw.outputs["Val"], met.inputs[0])
    met2 = nodes.new("ShaderNodeMath")
    met2.operation = "ADD"
    met2.inputs[1].default_value = 0.08
    link(nt, met.outputs["Value"], met2.inputs[0])
    link(nt, met2.outputs["Value"], bsdf.inputs["Metallic"])
    rough = nodes.new("ShaderNodeMath")
    rough.operation = "SUBTRACT"
    rough.inputs[0].default_value = 0.55
    link(nt, rgb2bw.outputs["Val"], rough.inputs[1])
    roughc = nodes.new("ShaderNodeMath")
    roughc.operation = "MAXIMUM"
    roughc.inputs[1].default_value = 0.12
    link(nt, rough.outputs["Value"], roughc.inputs[0])
    link(nt, roughc.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.15
    link(nt, bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def build_meshes(mat):
    skin = json.loads(open(SKIN, encoding="utf-8").read())
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    built = []
    for m in skin["meshes"]:
        if m["name"].lower().startswith("fview"):
            continue
        verts = [tuple(m["vertices"][i:i + 3]) for i in range(0, len(m["vertices"]), 3)]
        tris = [tuple(m["triangles"][i:i + 3]) for i in range(0, len(m["triangles"]), 3)]
        uvs = m["uvs"]
        me = bpy.data.meshes.new(m["name"])
        me.from_pydata(verts, [], tris)
        me.update()
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uv.data[li].uv = (uvs[2 * vi], 1.0 - uvs[2 * vi + 1])
        me.materials.append(mat)
        obj = bpy.data.objects.new(m["name"], me)
        bpy.context.scene.collection.objects.link(obj)
        hide = m["name"] not in FRAME_MESHES
        obj.hide_render = hide
        if hide:
            continue
        built.append(m["name"])
        for v in verts:
            lo = Vector(map(min, lo, v))
            hi = Vector(map(max, hi, v))
    return built, lo, hi


def add_area(name, loc, rot, size, energy, color):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size * 0.6
    data.energy = energy
    data.color = color
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    return obj


def point_cam(cam, center, offset, up="Y", roll_deg=0.0):
    cam.location = center + Vector(offset)
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", up).to_euler()
    if roll_deg:
        cam.rotation_euler.rotate_axis("Z", math.radians(roll_deg))


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.85
    world = bpy.data.worlds.new("studio_gray")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.18, 0.18, 0.185, 1)
    bg.inputs["Strength"].default_value = 0.35
    scene.world = world
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        scene.cycles.device = "GPU"
    except Exception:
        scene.cycles.device = "CPU"
    return scene


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = setup_scene()
    spec = load_img(SPECULAR, "sRGB")
    nrm = load_img(NORMAL, "Non-Color")
    mat = make_metal_mat(spec, nrm)
    built, lo, hi = build_meshes(mat)
    center = (lo + hi) / 2.0
    diag = max((hi - lo).length, 1.0)
    dist = diag * 2.6

    cam_data = bpy.data.cameras.new("ReviewCam")
    cam_data.lens = 60
    cam_data.clip_start = 0.01
    cam_data.clip_end = dist * 20
    cam = bpy.data.objects.new("ReviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # Studio lights relative to gun center (world).
    add_area("key", center + Vector((diag * 0.9, -diag * 1.1, diag * 1.2)),
             Euler((math.radians(55), 0, math.radians(35))), diag * 1.4, 650, (1.0, 0.97, 0.9))
    add_area("fill", center + Vector((-diag * 1.2, -diag * 0.4, diag * 0.3)),
             Euler((math.radians(80), 0, math.radians(-70))), diag * 2.0, 80, (0.75, 0.82, 1.0))
    add_area("rim", center + Vector((0.0, diag * 1.3, diag * 0.6)),
             Euler((math.radians(-20), 0, math.radians(180))), diag * 1.2, 180, (1.0, 0.95, 0.85))

    views = {
        # panel side, barrel left — same layout as the user Blender still
        "side_panel": ((dist, 0.0, 0.0), "Y", -90.0),
        # coin side
        "side_coin": ((-dist, 0.12 * diag, 0.04 * diag), "Y", 90.0),
        # first-person-like 3/4 from coin side
        "fp_three_quarter": ((-dist * 0.7, -dist * 0.85, dist * 0.22), "Y", 55.0),
    }
    written = []
    for name, (offset, up, roll) in views.items():
        point_cam(cam, center, offset, up, roll)
        path = os.path.join(OUT, f"{name}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        written.append(path)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    json.dump({
        "purpose": "User review only. Not deployed to CS:GO.",
        "shading": "baked CF spec albedo (diff*0.25+spec) + Principled metallic + studio area lights",
        "target": "CF in-game champagne metal (user reference screenshot)",
        "meshes": built,
        "outputs": written,
        "blend": BLEND,
    }, open(REPORT, "w", encoding="utf-8"), indent=1)
    print("review stills", written)


if __name__ == "__main__":
    main()
