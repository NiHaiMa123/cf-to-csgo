import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_STUDIO"]

def aim(pos, look, lens=35):
    cam.location = Vector(pos)
    d = (Vector(look) - Vector(pos))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens

# eye-ish: behind stock (-Y end), slightly above gun line, looking down the barrel (+Y)
aim((3.5, -15.5, 5.5), (1.5, 2.0, -1.0), 35)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\eye_a.png"
bpy.ops.render.render(write_still=True)
# closer / higher
aim((2.5, -12.0, 3.5), (1.0, 4.0, -1.5), 30)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\eye_b.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
