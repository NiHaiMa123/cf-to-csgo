"""Side view + real EEVEE render so the diffuse atlas shows."""
import json
import os

import bpy
from mathutils import Vector

DEST = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\source_reference.blend"
WORKING = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend"
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
SHOT_DIR = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots"
RESULT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_eevee_view.json"


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

uv = gun.data.uv_layers.get("Float2") or gun.data.uv_layers.active
if uv:
    uv.active = True
    uv.active_render = True
    sample_uv = [list(uv.data[i].uv) for i in range(0, min(len(uv.data), 12))]
else:
    sample_uv = []

scene.r1a_source_clip = "idle_0"
scene.frame_set(0)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
gun_ev = gun.evaluated_get(deps)
pts = [gun_ev.matrix_world @ v.co for v in gun_ev.data.vertices]
center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)

# Side three-quarter: rifle runs along Y.
cam.data.lens = 45
look_at(cam, Vector((center.x + 16.0, center.y - 4.0, center.z + 5.5)), center)
scene.camera = cam

key = bpy.data.objects.get("R1A_Key")
fill = bpy.data.objects.get("R1A_Fill")
if key:
    key.location = center + Vector((10.0, -8.0, 12.0))
    key.data.energy = 1800
if fill:
    fill.location = center + Vector((-10.0, 2.0, 6.0))
    fill.data.energy = 800

scene.render.engine = "BLENDER_EEVEE"
scene.render.film_transparent = False
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.2
if hasattr(scene, "eevee"):
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16

for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "RENDERED"
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = True
    space.overlay.show_overlays = False
    space.region_3d.view_perspective = "CAMERA"


def grab(clip, frame, filename):
    scene.r1a_source_clip = clip
    scene.frame_end = {"select": 64, "reload": 160, "idle_0": 300}.get(clip, 64)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    path = os.path.join(SHOT_DIR, filename)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


p1 = grab("idle_0", 0, "view_model_idle.png")
p2 = grab("select", 0, "view_model.png")
p3 = grab("reload", 48, "view_model_reload.png")

scene.r1a_source_clip = "select"
scene.frame_end = 64
scene.frame_set(0)
bpy.ops.wm.save_mainfile()

out = {
    "center": list(center),
    "cam": list(cam.location),
    "sample_uv": sample_uv,
    "n_uv": len(uv.data) if uv else 0,
    "working_ok": sha256_file(WORKING) == WORKING_SHA,
    "shots": [p1, p2, p3],
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
