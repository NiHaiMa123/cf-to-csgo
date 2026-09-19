"""Textured gun, hide deformed gloves, tighter studio camera."""
import json
import os

import bpy
from mathutils import Vector

DEST = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\source_reference.blend"
WORKING = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend"
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
DIFF = r"D:\project\cf_to_csgo\work\p5_leishen\p6\_png\diffuse.png"
NORM = r"D:\project\cf_to_csgo\work\p5_leishen\p6\_png\normal_src.png"
SHOT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model.png"
SHOT_RELOAD = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model_reload.png"
RESULT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_gun_view.json"


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

for name in ("R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE", "R1A_VIEW_GLOVE_ARM", "R1A_VIEW_SLEEVE_ARM"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_viewport = True
        obj.hide_render = True

# Rebuild a simple textured material so the atlas actually shows.
mat = bpy.data.materials.get("R1A_GUN_VIEW") or bpy.data.materials.new("R1A_GUN_VIEW")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
tex = nt.nodes.new("ShaderNodeTexImage")
img = bpy.data.images.load(DIFF, check_existing=True)
img.colorspace_settings.name = "sRGB"
tex.image = img
tex.location = (-400, 0)
bsdf.location = (0, 0)
out.location = (300, 0)
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
if "Specular IOR Level" in bsdf.inputs:
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
bsdf.inputs["Roughness"].default_value = 0.4
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
# Object-level override so the shared P6 mesh keeps its original material.
if len(gun.material_slots) == 0:
    gun.data.materials.append(mat)
gun.material_slots[0].link = "OBJECT"
gun.material_slots[0].material = mat

scene.r1a_source_clip = "idle_0"
scene.frame_set(0)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
gun_ev = gun.evaluated_get(deps)
pts = [gun_ev.matrix_world @ v.co for v in gun_ev.data.vertices]
center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)
minc = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
maxc = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
extent = maxc - minc

cam.data.lens = 55
look_at(
    cam,
    Vector((center.x + 2.8, center.y - 11.5, center.z + 3.2)),
    Vector((center.x + 0.4, center.y, center.z + 0.2)),
)
scene.camera = cam

key = bpy.data.objects.get("R1A_Key")
fill = bpy.data.objects.get("R1A_Fill")
if key:
    key.location = center + Vector((4.0, -6.0, 5.0))
    key.data.energy = 1400
    key.data.size = 6
if fill:
    fill.location = center + Vector((-5.0, -2.0, 3.0))
    fill.data.energy = 600
    fill.data.size = 8

hud = bpy.data.objects.get("R1A_HUD")
if hud:
    hud.hide_viewport = True
    hud.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.3
for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "MATERIAL"
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = True
    space.overlay.show_bones = False
    space.overlay.show_relationship_lines = False
    space.overlay.show_motion_paths = False
    space.overlay.show_extras = False
    space.overlay.show_floor = False
    space.overlay.show_axis_x = False
    space.overlay.show_axis_y = False
    space.overlay.show_ortho_grid = False
    space.region_3d.view_perspective = "CAMERA"

def render_clip(clip, frame, path):
    scene.r1a_source_clip = clip
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    scene.render.filepath = path
    bpy.ops.render.opengl(write_still=True, view_context=False)

render_clip("select", 0, SHOT)
render_clip("idle_0", 0, os.path.join(os.path.dirname(SHOT), "view_model_idle.png"))
render_clip("reload", 72, SHOT_RELOAD)
render_clip("select", 0, SHOT)

scene.frame_start = 0
scene.frame_end = 64
scene.r1a_source_clip = "select"
scene.frame_set(0)
bpy.ops.wm.save_mainfile()

out = {
    "center": list(center),
    "extent": list(extent),
    "cam": list(cam.location),
    "mat": gun.material_slots[0].material.name if gun.material_slots else None,
    "image": img.filepath if img else None,
    "working_ok": sha256_file(WORKING) == WORKING_SHA,
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
