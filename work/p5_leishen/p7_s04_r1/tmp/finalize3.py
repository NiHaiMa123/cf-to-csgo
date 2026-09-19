import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_SIDE"]
cam.location = Vector((18.99, -6.38, 3.37))
d = (Vector((0.8, -5.6, 0.6)) - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
scn.camera = cam
scn.frame_set(0)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/final_side2.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
