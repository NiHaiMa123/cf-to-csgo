import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_SIDE"]
# pull side cam back a bit to fit arms+gun
cam.location = Vector((21.5, -6.4, 4.6))
d = (Vector((0.8, -5.6, 0.8)) - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scn.camera = cam
scn.frame_set(0)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/final_side.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile()
print(json.dumps({"saved": True}))
