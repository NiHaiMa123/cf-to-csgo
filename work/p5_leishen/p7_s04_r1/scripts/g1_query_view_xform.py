import json
import bpy
from mathutils import Vector

arm = bpy.data.objects["R1A_VIEW_ARM"]
gun = bpy.data.objects["R1A_VIEW_GUN"]
empty = bpy.data.objects["R1A_VIEW_ROOT"]
cam = bpy.data.objects["R1A_CAM_STUDIO"]
deps = bpy.context.evaluated_depsgraph_get()
pb = arm.pose.bones["v_weapon.M4A1_Parent"]
gun_ev = gun.evaluated_get(deps)
verts = [gun_ev.matrix_world @ gun_ev.data.vertices[i].co for i in range(0, len(gun_ev.data.vertices), 200)]
bb = [Vector(c) for c in gun_ev.bound_box]
out = {
    "empty_world": [list(r) for r in empty.matrix_world],
    "arm_world": [list(r) for r in arm.matrix_world],
    "gun_world": [list(r) for r in gun.matrix_world],
    "gun_parent": gun.parent.name if gun.parent else None,
    "parent_pose_trans": list(pb.matrix.to_translation()),
    "parent_head_pose": list(pb.head),
    "parent_head_world": list((arm.matrix_world @ pb.matrix).to_translation()),
    "cam_loc": list(cam.location),
    "n_verts": len(gun.data.vertices),
    "sample_vert_world": [list(v) for v in verts[:8]],
    "eval_bbox_local": [list(c) for c in bb],
    "hide_gun": gun.hide_viewport,
    "mod": [(m.type, m.object.name if m.object else None, m.show_viewport) for m in gun.modifiers],
}
path = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_view_xform.json"
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
