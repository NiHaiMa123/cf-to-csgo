import bpy, json
from mathutils import Vector
scn = bpy.context.scene
# hide all skeleton stick/joint meshes to test
hid = 0
for o in bpy.data.objects:
    if o.name.startswith(("R1A_ANIM_J_","R1A_ANIM_S_","R1A_ANIM_AX_","R1A_BIND")):
        if not o.hide_viewport:
            o.hide_viewport = True; hid += 1
        o.hide_render = True
cam = bpy.data.objects["R1A_CAM_STUDIO"]
def aim(pos, look, lens=35):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(look)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    cam.data.lens = lens
aim((2.5, -12.0, 3.5), (1.0, 4.0, -1.5), 30)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\eye_b2.png"
bpy.ops.render.render(write_still=True)
# a wider "held weapon" 3/4 view from front-right slightly below
aim((14.0, -16.0, 6.0), (1.5, -2.0, -0.5), 32)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\eye_c.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"hid": hid}))
