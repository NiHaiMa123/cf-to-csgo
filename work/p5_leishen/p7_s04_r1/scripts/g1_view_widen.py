"""Widen studio camera so the whole rifle fits. Default clip idle."""
import bpy
from mathutils import Vector

scene = bpy.data.scenes["CF_SOURCE_REFERENCE"]
bpy.context.window.scene = scene
gun = bpy.data.objects["R1A_VIEW_GUN"]
cam = bpy.data.objects["R1A_CAM_STUDIO"]

scene.r1a_source_clip = "idle_0"
scene.frame_start = 0
scene.frame_end = 300
scene.frame_set(0)
bpy.context.view_layer.update()

deps = bpy.context.evaluated_depsgraph_get()
gun_ev = gun.evaluated_get(deps)
pts = [gun_ev.matrix_world @ v.co for v in gun_ev.data.vertices]
center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)

cam.data.lens = 35
cam.location = center + Vector((20.0, -8.0, 8.0))
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "RENDERED"
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = True
    space.overlay.show_overlays = False
    space.region_3d.view_perspective = "CAMERA"

scene.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model_idle.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile()
