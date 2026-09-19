import bpy, json
scn = bpy.context.scene
for clip, frame, name in [("idle_0", 10, "chk_idle"), ("select", 32, "chk_select_mid"), ("reload", 72, "chk_reload_718")]:
    scn.r1a_source_clip = clip
    scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\%s.png" % name
    bpy.ops.render.render(write_still=True)
scn.r1a_source_clip = "idle_0"
scn.frame_set(0)
print(json.dumps({"done": True}))
