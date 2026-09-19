"""Whole-gun studio view with original P6 texture. Gloves stay hidden."""
import json
import os

import bpy
from mathutils import Vector

DEST = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\source_reference.blend"
WORKING = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend"
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
SHOT_DIR = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots"
RESULT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_view_final.json"


def sha256_file(path):
    import hashlib
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def look_at(obj, location, target):
    obj.location = Vector(location)
    obj.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


if os.path.abspath(bpy.data.filepath) != os.path.abspath(DEST):
    raise RuntimeError(bpy.data.filepath)
if sha256_file(WORKING) != WORKING_SHA:
    raise RuntimeError("working hash changed")

scene = bpy.data.scenes["CF_SOURCE_REFERENCE"]
bpy.context.window.scene = scene
gun = bpy.data.objects["R1A_VIEW_GUN"]
cam = bpy.data.objects["R1A_CAM_STUDIO"]

for name in ("R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE", "R1A_VIEW_GLOVE_ARM", "R1A_VIEW_SLEEVE_ARM", "R1A_HUD"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_viewport = True
        obj.hide_render = True

orig = bpy.data.materials.get("rif_m4a1_p6")
if orig is None:
    raise RuntimeError("missing rif_m4a1_p6")
if len(gun.material_slots) == 0:
    gun.data.materials.append(orig)
gun.material_slots[0].link = "OBJECT"
gun.material_slots[0].material = orig

uv_names = [uv.name for uv in gun.data.uv_layers]
info_tex = None
for node in orig.node_tree.nodes:
    if node.type == "TEX_IMAGE" and node.image:
        info_tex = node.image.filepath

scene.r1a_source_clip = "idle_0"
scene.frame_set(0)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
gun_ev = gun.evaluated_get(deps)
pts = [gun_ev.matrix_world @ v.co for v in gun_ev.data.vertices]
center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)

cam.data.lens = 40
cam.data.clip_start = 0.1
cam.data.clip_end = 250.0
look_at(cam, center + Vector((9.0, -20.0, 7.0)), center + Vector((0.0, 2.0, 0.0)))
scene.camera = cam

key = bpy.data.objects.get("R1A_Key")
fill = bpy.data.objects.get("R1A_Fill")
if key:
    key.location = center + Vector((8.0, -10.0, 10.0))
    key.data.energy = 1600
if fill:
    fill.location = center + Vector((-8.0, -4.0, 5.0))
    fill.data.energy = 700

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.15
if scene.world and scene.world.use_nodes:
    for node in scene.world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Color"].default_value = (0.15, 0.16, 0.18, 1.0)
            node.inputs["Strength"].default_value = 0.6

for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "MATERIAL"
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = False
    space.overlay.show_overlays = False
    space.region_3d.view_perspective = "CAMERA"

def grab(clip, frame, filename):
    scene.r1a_source_clip = clip
    dur = {"select": 64, "reload": 160, "idle_0": 300}.get(clip, 64)
    scene.frame_end = dur
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    path = os.path.join(SHOT_DIR, filename)
    scene.render.filepath = path
    bpy.ops.render.opengl(write_still=True, view_context=False)
    return path

p_idle = grab("idle_0", 0, "view_model_idle.png")
p_sel0 = grab("select", 0, "view_model.png")
p_sel1 = grab("select", 64, "view_model_select_end.png")
p_rel = grab("reload", 72, "view_model_reload.png")

scene.r1a_source_clip = "select"
scene.frame_end = 64
scene.frame_set(0)
bpy.ops.wm.save_mainfile()

out = {
    "center": list(center),
    "cam": list(cam.location),
    "uv": uv_names,
    "material": orig.name,
    "tex": info_tex,
    "working_ok": sha256_file(WORKING) == WORKING_SHA,
    "shots": [p_idle, p_sel0, p_sel1, p_rel],
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
