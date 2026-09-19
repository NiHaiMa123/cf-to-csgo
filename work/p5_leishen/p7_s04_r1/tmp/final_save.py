import bpy, json
scn = bpy.context.scene
scn.r1a_source_clip = "idle_0"; scn.frame_start = 0; scn.frame_end = 300
scn.frame_set(0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile()
print(json.dumps({"saved": bpy.data.filepath, "dirty": bpy.data.is_dirty}))
