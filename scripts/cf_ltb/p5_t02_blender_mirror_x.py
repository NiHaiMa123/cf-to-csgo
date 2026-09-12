"""Live Blender: mirror Transformers gun on LTB X (weapon left/right).

User confirmed identity as 雷神 and that left/right is swapped.
"""
from __future__ import annotations

import json
import os

import bmesh
import bpy
from mathutils import Vector

OUT_DIR = r"D:\project\cf_to_csgo\work\p5_leishen\t02_native\blender"
PREVIEW = os.path.join(OUT_DIR, "viewport_gun_mirrored.png")
BLEND = os.path.join(OUT_DIR, "p5_t02_transformers_base.blend")
REPORT = os.path.join(OUT_DIR, "mirror_report.json")

root = bpy.data.objects.get("P5T02_Root")
if root is None:
    raise RuntimeError("P5T02_Root missing")

# LTB X is weapon left/right (side-view depth). Negative parent scale mirrors L/R.
root.scale.x = -abs(float(root.scale.x)) if root.scale.x >= 0 else root.scale.x
if root.scale.x >= 0:
    root.scale.x = -1.0
bpy.context.view_layer.update()

meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
for obj in meshes:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

gun = [
    obj
    for obj in meshes
    if "Fview" not in obj.name and "hand" not in obj.name.lower() and "arm" not in obj.name.lower()
]
hands = [obj for obj in meshes if obj not in gun]
for obj in meshes:
    hidden = obj in hands
    obj.hide_set(hidden)
    obj.hide_render = hidden
    obj.select_set(obj in gun)

scene = bpy.context.scene
cam = scene.camera


def mesh_bbox(objects):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
    return mins, maxs, (mins + maxs) * 0.5, maxs - mins


_, _, mid, size = mesh_bbox(gun)
span = max(size.x, size.y, size.z, 1.0)
cam.location = mid + Vector((span * 0.85, -span * 1.35, span * 0.42))
cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.objects.active = gun[0]
for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "RENDERED"
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = True
    space.overlay.show_overlays = False
    region = next((item for item in area.regions if item.type == "WINDOW"), None)
    if region is None:
        continue
    with bpy.context.temp_override(
        window=bpy.context.window,
        screen=bpy.context.screen,
        area=area,
        region=region,
        scene=scene,
    ):
        bpy.ops.view3d.view_camera()
        try:
            bpy.ops.view3d.camera_to_view_selected()
        except Exception as exc:
            print("camera_to_view_selected failed:", exc)

for obj in bpy.data.objects:
    obj.select_set(False)
scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

report = {
    "identity_status": "USER_VISUAL_MATCH_CONFIRMED",
    "candidate": "PV-M4A1_S_Transformers",
    "mirror": "root.scale.x = -1 (LTB X / weapon left-right), mesh normals flipped",
    "preview": PREVIEW,
    "root_scale": list(root.scale),
}
with open(REPORT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
