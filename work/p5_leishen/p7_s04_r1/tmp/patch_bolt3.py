import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()
# Remove the bolt mapping so it rigidly follows M4A1_Parent (flush like CS bind)
old = '"Bone04": "v_weapon.M4A1_Bolt",'
assert old in s, "bolt map line"
s = s.replace(old, '')
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/bolt_unmapped.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
