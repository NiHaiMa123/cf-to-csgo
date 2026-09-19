import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()
# unmap both small parts: they ride the gun rigidly like CS bind
for line in ['    "Bone06": "v_weapon.M4A1_Clip",\n',
             '    "Bone04": "v_weapon.M4A1_Bolt",\n']:
    if line in s:
        s = s.replace(line, '')
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
scn.camera = bpy.data.objects["R1A_CAM_SIDE"]
for clip, frame, name in [("idle_0", 10, "u_idle"), ("reload", 72, "u_reload718"), ("select", 32, "u_select32"), ("idle_0", 150, "u_idle150")]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
