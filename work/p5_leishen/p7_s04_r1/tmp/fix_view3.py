import bpy, json
scn = bpy.context.scene
# sanity before save: confirm filepath is the r1 source_reference.blend
assert scn and bpy.data.filepath.endswith(r"source\source_reference.blend"), bpy.data.filepath
# final state check
scn.r1a_source_clip = "idle_0"
scn.frame_set(0)
scn.frame_start = 0
scn.frame_end = 300
# visibility summary for the record
vis = {o.name: (not o.hide_viewport and not o.hide_get()) for o in bpy.data.objects
       if o.name.startswith(("R1A_VIEW","R1A_CF","R1A_ANIM_J_00","R1A_ANIM_S_00","R1A_CAM"))}
bpy.ops.wm.save_mainfile()
print(json.dumps({"saved": bpy.data.filepath, "dirty_after": bpy.data.is_dirty,
                  "clip": scn.r1a_source_clip, "vis_sample": vis}, ensure_ascii=False, indent=1))
