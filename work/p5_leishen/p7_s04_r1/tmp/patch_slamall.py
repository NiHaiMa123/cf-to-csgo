import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()
# slam everything that's still mapped (arm chain + gun root); clip/bolt already unmapped
old = 'SLAM_BONES = {"v_weapon.M4A1_Parent"}'
assert old in s
s = s.replace(old, 'SLAM_ALL = True\nSLAM_BONES = {"v_weapon.M4A1_Parent"}')
old2 = '                if bone.name in SLAM_BONES:'
assert old2 in s
s = s.replace(old2, '                if SLAM_ALL or bone.name in SLAM_BONES:')
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
scn.camera = bpy.data.objects["R1A_CAM_SIDE"]
for clip, frame, name in [("idle_0", 10, "sa_idle"), ("reload", 72, "sa_reload718")]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
