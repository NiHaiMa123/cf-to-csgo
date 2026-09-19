import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()
assert 'SLAM_ALL = True' in s
s = s.replace('SLAM_ALL = True', 'SLAM_ALL = False')
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
scn.camera = bpy.data.objects["R1A_CAM_SIDE"]
for clip, frame, name in [("idle_0", 10, "v_idle"), ("reload", 72, "v_reload718"), ("select", 32, "v_select32")]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
