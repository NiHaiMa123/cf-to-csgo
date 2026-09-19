import bpy, json
# 1) revert: hide glove/sleeve view meshes again (blob in bind pose)
for n in ["R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    o = bpy.data.objects.get(n)
    if o: o.hide_viewport = True; o.hide_render = True
# 2) unhide the orange source-skeleton joints/sticks for review context
nshow = 0
for o in bpy.data.objects:
    if o.name.startswith(("R1A_ANIM_J_","R1A_ANIM_S_")):
        o.hide_viewport = False; o.hide_render = False; nshow += 1
scn = bpy.context.scene
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\probe_model_skeleton.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"unhidden_sticks": nshow, "clip": scn.r1a_source_clip, "frame": scn.frame_current}))
