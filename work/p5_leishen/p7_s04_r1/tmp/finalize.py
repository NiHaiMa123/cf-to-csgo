import bpy, json
scn = bpy.context.scene
# default state: idle clip, frame 0, studio overview camera
scn.r1a_source_clip = "idle_0"
scn.frame_start = 0
scn.frame_end = 300
scn.frame_set(0)
scn.camera = bpy.data.objects["R1A_CAM_STUDIO"]
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/final_studio.png"
bpy.ops.render.render(write_still=True)
# persist
bpy.ops.wm.save_as_mainfile()
print(json.dumps({"saved": bpy.data.filepath}))
