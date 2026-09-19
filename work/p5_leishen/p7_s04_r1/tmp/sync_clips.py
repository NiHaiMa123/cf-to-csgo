import bpy, json
scn = bpy.context.scene
# align the keyed-armature dropdown with the payload-driven CF clip the user picked
cur = scn.r1a_source_clip  # "prefire"
scn.r1a_clip = "R1A_CF_" + cur   # triggers apply_clip -> sets matching action + frame range
bpy.ops.wm.save_mainfile()
print(json.dumps({
  "r1a_source_clip": scn.r1a_source_clip,
  "r1a_clip": scn.r1a_clip,
  "frame_range": [scn.frame_start, scn.frame_end],
  "saved": bpy.data.filepath,
}, ensure_ascii=False))
