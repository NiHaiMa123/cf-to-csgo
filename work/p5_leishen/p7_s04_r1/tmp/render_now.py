import bpy, json
scn = bpy.context.scene
# confirm live handler is the patched one and both flags exist
import re
src = bpy.data.texts["r1a_source_switcher.py"].as_string()
ok_pos = "POS_ONLY_BONES" in src and "elif bone.name in POS_ONLY_BONES" in src
ok_slam = 'SLAM_BONES = {"v_weapon.M4A1_Parent"}' in src
for clip, frame, name in [("idle_0", 10, "bolt_idle"), ("reload", 72, "bolt_reload718"), ("select", 32, "bolt_select32")]:
    scn.r1a_source_clip = clip
    scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
print(json.dumps({"pos_only": ok_pos, "slam": ok_slam}))
