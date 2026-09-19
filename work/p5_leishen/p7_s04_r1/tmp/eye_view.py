import bpy, json
from mathutils import Vector
scn = bpy.context.scene
# try the FRONT and STUDIO cams
for n in ["R1A_CAM_FRONT", "R1A_CAM_STUDIO", "R1A_CAM_TOP"]:
    c = bpy.data.objects.get(n)
    print(n, "loc", [round(v,1) for v in c.location] if c else None)
# place an eye cam behind gun stock looking along -Y
cam = bpy.data.objects["R1A_CAM_STUDIO"]
arm = bpy.data.objects["R1A_VIEW_ARM"]
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
gun_head = (arm.matrix_world @ arm.pose.bones["v_weapon.M4A1_Parent"].head)
# gun muzzle direction ~ -Y world; eye behind = +Y
eye = Vector((gun_head.x + 0.8, gun_head.y + 7.0, gun_head.z + 1.2))
tgt = Vector((gun_head.x - 0.3, gun_head.y - 8.0, gun_head.z + 0.2))
d = (tgt - eye).normalized()
cam.location = eye
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
scn.camera = cam
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/eye_idle.png"
bpy.ops.render.render(write_still=True)
scn.r1a_source_clip = "reload"; scn.frame_set(72)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/eye_reload72.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
