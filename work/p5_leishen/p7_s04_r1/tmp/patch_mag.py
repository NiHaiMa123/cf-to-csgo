import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()
old = 'POS_ONLY_BONES = {"v_weapon.M4A1_Bolt"}'
new = 'POS_ONLY_BONES = {"v_weapon.M4A1_Clip"}'
assert old in s, "posonly set"
s = s.replace(old, new)
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
for clip, frame, name in [("idle_0", 10, "m2_idle"), ("reload", 72, "m2_reload718"), ("select", 32, "m2_select32"), ("reload", 0, "m2_reload0")]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
