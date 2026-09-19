"""Frame a studio camera on the actual gun mesh and take a preview."""
import json
import os

import bpy
from mathutils import Vector

DEST = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\source_reference.blend"
WORKING = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend"
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
SHOT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model.png"
SHOT2 = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model_reload.png"
RESULT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_reframe_studio.json"


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
deps = bpy.context.evaluated_depsgraph_get()
gun_ev = gun.evaluated_get(deps)
pts = [gun_ev.matrix_world @ v.co for v in gun_ev.data.vertices]
center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)
minc = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
maxc = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
extent = maxc - minc
dist = max(extent.length * 0.9, 8.0)

cam.data.lens = 50
cam.data.clip_start = 0.05
cam.data.clip_end = 200.0
# three-quarter from front-right-above in CF space (Y is the long axis)
look_at(cam, center + Vector((extent.x * 1.6 + 3.0, -dist, extent.z * 0.55 + 1.5)), center)
scene.camera = cam

hud = bpy.data.objects.get("R1A_HUD")
if hud:
    hud.parent = cam
    hud.location = (-1.15, -0.68, -2.8)
    hud.scale = (0.06, 0.06, 0.06)

key = bpy.data.objects.get("R1A_Key")
fill = bpy.data.objects.get("R1A_Fill")
if key:
    key.location = center + Vector((6.0, -8.0, 7.0))
    key.data.energy = 1200
if fill:
    fill.location = center + Vector((-7.0, -3.0, 4.0))
    fill.data.energy = 500

# keep P6 material
if gun.data.materials:
    mat = gun.data.materials[0]
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if "Specular IOR Level" in node.inputs:
                    node.inputs["Specular IOR Level"].default_value = 0.3
                node.inputs["Roughness"].default_value = 0.45

scene.render.engine = "BLENDER_EEVEE"
for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "MATERIAL"
    space.overlay.show_bones = False
    space.overlay.show_relationship_lines = False
    space.region_3d.view_perspective = "CAMERA"

scene.r1a_source_clip = "select"
scene.frame_start = 0
scene.frame_end = 64
scene.frame_set(0)
bpy.context.view_layer.update()
scene.render.filepath = SHOT
bpy.ops.render.opengl(write_still=True, view_context=False)

scene.r1a_source_clip = "reload"
scene.frame_end = 160
scene.frame_set(72)
bpy.context.view_layer.update()
scene.render.filepath = SHOT2
bpy.ops.render.opengl(write_still=True, view_context=False)

scene.r1a_source_clip = "select"
scene.frame_end = 64
scene.frame_set(0)
scene.camera = cam
bpy.ops.wm.save_mainfile()

out = {
    "center": list(center),
    "min": list(minc),
    "max": list(maxc),
    "cam": list(cam.location),
    "working_ok": sha256_file(WORKING) == WORKING_SHA,
    "shots": [SHOT, SHOT2],
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
