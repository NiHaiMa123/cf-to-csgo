import bpy, json
from mathutils import Vector, Matrix
text = bpy.data.texts["r1a_source_switcher.py"]
s = text.as_string()

old = 'SLAM_BONES = {"v_weapon.M4A1_Parent"}'
new = ('SLAM_BONES = {"v_weapon.M4A1_Parent"}\n'
       'POS_ONLY_BONES = {"v_weapon.M4A1_Bolt"}')
assert s.count(old) == 1
s = s.replace(old, new)

old2 = """                if bname in SLAM_BONES:
                    desired = w
                else:
                    desired = Matrix.LocRotScale(w.translation, rest_delta.rotation, w.to_scale())"""
new2 = """                if bname in SLAM_BONES:
                    desired = w
                elif bname in POS_ONLY_BONES:
                    desired = Matrix.LocRotScale(w.translation, rest_delta.rotation, None)
                else:
                    desired = Matrix.LocRotScale(w.translation, rest_delta.rotation, w.to_scale())"""
assert s.count(old2) == 1
s = s.replace(old2, new2)
text.from_string(s)
bpy.ops.wm.save_as_mainfile()
scn = bpy.context.scene
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\bolt_posonly.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"patched": True}))
