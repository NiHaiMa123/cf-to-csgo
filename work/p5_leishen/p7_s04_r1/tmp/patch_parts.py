import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()

# 1) re-add bolt mapping
old_map = '    "Bone06": "v_weapon.M4A1_Clip",\n'
assert old_map in s, "clip map line"
s = s.replace(old_map, old_map + '    "Bone04": "v_weapon.M4A1_Bolt",\n')

# 2) POS_ONLY covers both small parts
old_set = 'POS_ONLY_BONES = {"v_weapon.M4A1_Clip"}'
new_set = 'POS_ONLY_BONES = {"v_weapon.M4A1_Clip", "v_weapon.M4A1_Bolt"}'
assert old_set in s, "posonly set"
s = s.replace(old_set, new_set)

# 3) pos-only branch: head at CF pos, orientation = rigid-follow-gun
old_b = """                elif bone.name in POS_ONLY_BONES:
                    pose = (Matrix.Translation((T @ M).translation)
                            @ rest.to_3x3().to_4x4())"""
new_b = """                elif bone.name in POS_ONLY_BONES:
                    follow = (desired[bone.parent.name]
                              @ bone.parent.matrix_local.inverted() @ rest)
                    pose = (Matrix.Translation((T @ M).translation)
                            @ follow.to_3x3().to_4x4())"""
assert old_b in s, "posonly branch"
s = s.replace(old_b, new_b)
text.from_string(s)
ns = {"bpy": bpy}
exec(compile(s, "r1a_source_switcher", "exec"), ns)
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_SIDE"]
scn.camera = cam
for clip, frame, name in [("idle_0", 10, "p3_idle_side"), ("reload", 72, "p3_reload718_side"), ("select", 0, "p3_select0_side")]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
