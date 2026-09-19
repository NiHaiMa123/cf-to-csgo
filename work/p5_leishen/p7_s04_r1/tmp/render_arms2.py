import bpy, json
scn = bpy.context.scene
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\fullarms_v2.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"clip": scn.r1a_source_clip, "frame": scn.frame_current}))
