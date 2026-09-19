import bpy, json
scn = bpy.context.scene
# glove only
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_viewport = True
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_render = True
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\glove_only.png"
bpy.ops.render.render(write_still=True)
# sleeve only
bpy.data.objects["R1A_VIEW_GLOVE"].hide_viewport = True
bpy.data.objects["R1A_VIEW_GLOVE"].hide_render = True
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_viewport = False
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_render = False
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\sleeve_only.png"
bpy.ops.render.render(write_still=True)
# both back on? leave as: sleeve on, glove off - will decide after viewing
print(json.dumps({"clip": scn.r1a_source_clip, "frame": scn.frame_current}))
