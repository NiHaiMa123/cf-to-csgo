import bpy, json
scn = bpy.context.scene
for n in ["R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_render = True
cam = bpy.data.objects["R1A_CAM_SIDE"]
scn.camera = cam
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/gun_side_idle.png"
bpy.ops.render.render(write_still=True)
scn.r1a_source_clip = "reload"; scn.frame_set(72)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/gun_side_reload.png"
bpy.ops.render.render(write_still=True)
for n in ["R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_render = False
print(json.dumps({"done": True, "cam": cam.location[:]}))
