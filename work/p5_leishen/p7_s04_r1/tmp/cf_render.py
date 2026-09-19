import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_SIDE"]
cam.location = Vector((34.0, 4.0, 8.0))
d = (Vector((0.0, 4.0, 0.5)) - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 32
scn.camera = cam
scn.render.resolution_x = 960; scn.render.resolution_y = 540
# hide CS view meshes + diagnostic sticks for clean CF look
for n in ["R1A_VIEW_GUN","R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    o = bpy.data.objects.get(n)
    if o: o.hide_render = True
import re
for o in bpy.data.objects:
    if re.match(r"R1A_ANIM_[JSAX]_", o.name):
        o.hide_render = True
for clip, frame, name in [("reload",0,"cf_reload0"),("reload",72,"cf_reload72"),("select",32,"cf_select32"),("idle_0",10,"cf_idle10")]:
    scn.r1a_clip = "R1A_CF_" + clip
    scn.r1a_source_clip = clip
    scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
print(json.dumps({"done": True}))
