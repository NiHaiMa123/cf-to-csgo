import bpy, json
tb = bpy.data.texts["r1a_source_switcher.py"]
src = "\n".join(l.body for l in tb.lines)

old = '''                Dt = T @ (M @ bi) @ T_inv
                pose = (Matrix.Translation((T @ M).translation)
                        @ Dt.to_3x3().to_4x4()
                        @ rest.to_3x3().to_4x4())'''

new = '''                if bone.name in SLAM_BONES:
                    pose = T @ M
                else:
                    Dt = T @ (M @ bi) @ T_inv
                    pose = (Matrix.Translation((T @ M).translation)
                            @ Dt.to_3x3().to_4x4()
                            @ rest.to_3x3().to_4x4())'''
assert old in src
src = src.replace(old, new)
# add SLAM_BONES const after BONE_MAP dict
marker2 = "    \"FvARM-bone R UpperArm\": \"v_weapon.Bip01_R_UpperArm\",\n}"
assert marker2 in src
src = src.replace(marker2, marker2 + "\n\n\nSLAM_BONES = {\"v_weapon.M4A1_Parent\"}")
tb.clear(); tb.write(src)
tb.use_module = True
g = {"bpy": bpy, "__name__": "r1a_source_switcher"}
exec(tb.as_string(), g)
scn = bpy.context.scene
scn.frame_set(scn.frame_current)
bpy.context.view_layer.update()
# unhide arms again for the check render
for n in ["R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_viewport = False
    bpy.data.objects[n].hide_render = False
# restore the wide studio framing (was moved by eye-cam experiments)
cam = bpy.data.objects["R1A_CAM_STUDIO"]
from mathutils import Vector
cam.location = Vector((27.0, -7.65, 7.87))
cam.rotation_euler = Vector((1.216,0,1.190)).to_quaternion().to_euler()  # placeholder; recompute aim below
d = Vector((4.0,-6.0,0.5)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
cam.data.lens = 35
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\hybrid.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"ok": True}))
