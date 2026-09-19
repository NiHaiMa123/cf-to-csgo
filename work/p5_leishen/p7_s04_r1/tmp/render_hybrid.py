import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_STUDIO"]
cam.location = Vector((27.0, -7.65, 7.87))
cam.rotation_euler = (Vector((4.0,-6.0,0.5)) - cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens = 35
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\hybrid.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"ok": True, "clip": scn.r1a_source_clip, "frame": scn.frame_current}))
