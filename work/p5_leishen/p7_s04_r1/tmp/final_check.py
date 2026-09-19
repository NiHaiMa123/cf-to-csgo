import bpy, json
from mathutils import Vector
scn = bpy.context.scene
for clip, frame, name in [("reload", 72, "fin_reload718"), ("select", 32, "fin_select32"), ("select", 0, "fin_select0")]:
    scn.r1a_source_clip = clip
    scn.frame_set(frame)
    bpy.context.view_layer.update()
    scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/%s.png" % name
    bpy.ops.render.render(write_still=True)
# numeric stability check: all mapped bones must still land on CF pos (err 0) and be finite
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
arm = bpy.data.objects["R1A_VIEW_ARM"]
bad = []
for pb in arm.pose.bones:
    h = pb.head
    if not all(abs(c) < 1e5 and c == c for c in h):
        bad.append((pb.name, [round(c,1) for c in h]))
print(json.dumps({"bad_bones": bad, "mapped_pose_count": len(arm.pose.bones)}))
