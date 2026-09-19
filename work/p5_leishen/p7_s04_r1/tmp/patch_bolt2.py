import bpy, json
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()

old1 = 'SLAM_BONES = {"v_weapon.M4A1_Parent"}'
new1 = ('SLAM_BONES = {"v_weapon.M4A1_Parent"}\n'
        'POS_ONLY_BONES = {"v_weapon.M4A1_Bolt"}')
assert s.count(old1) == 1, "slam line"
s = s.replace(old1, new1)

old2 = """                if bone.name in SLAM_BONES:
                    pose = T @ M
                else:
                    Dt = T @ (M @ bi) @ T_inv
                    pose = (Matrix.Translation((T @ M).translation)
                            @ Dt.to_3x3().to_4x4()
                            @ rest.to_3x3().to_4x4())"""
new2 = """                if bone.name in SLAM_BONES:
                    pose = T @ M
                elif bone.name in POS_ONLY_BONES:
                    pose = (Matrix.Translation((T @ M).translation)
                            @ rest.to_3x3().to_4x4())
                else:
                    Dt = T @ (M @ bi) @ T_inv
                    pose = (Matrix.Translation((T @ M).translation)
                            @ Dt.to_3x3().to_4x4()
                            @ rest.to_3x3().to_4x4())"""
assert s.count(old2) == 1, "pose block"
s = s.replace(old2, new2)
text.from_string(s)

ns = {"bpy": bpy}
exec(compile(text.as_string(), "r1a_source_switcher", "exec"), ns)
# ensure handler is the fresh one
for h in list(bpy.app.handlers.frame_change_post):
    if getattr(h, "__name__", "") == "r1a_apply":
        bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(ns["r1a_apply"])
scn = bpy.context.scene
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/bolt_posonly.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"patched": True}))
