import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_SIDE"]
cam.location = Vector((26.0, -6.4, 6.0))
d = (Vector((0.5, -6.0, 2.0)) - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 35
scn.camera = cam
scn.frame_set(0)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/final_side4.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
