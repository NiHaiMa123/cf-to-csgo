import bpy, json
from mathutils import Vector
arm = bpy.data.objects["R1A_VIEW_ARM"]
aw = arm.matrix_world
out = {}
for b in ["v_weapon.M4A1_Parent","v_weapon.M4A1_Clip","v_weapon.M4A1_Bolt","v_weapon.Bip01_R_Hand"]:
    rb = arm.data.bones[b]
    rl = rb.matrix_local
    head = (aw @ rl).translation
    tail = (aw @ Matrix()).translation if False else None
    # bone rest direction: tail - head in armature space
    hd = rl.translation; tl = rb.matrix_local @ Vector((0, rb.length, 0))
    out[b] = {"rest_head_arm": [round(v,2) for v in rl.translation],
              "rest_y_dir": [round(v,2) for v in (rl.to_3x3() @ Vector((0,1,0)))],
              "rest_x_dir": [round(v,2) for v in (rl.to_3x3() @ Vector((1,0,0)))],
              "rest_z_dir": [round(v,2) for v in (rl.to_3x3() @ Vector((0,0,1)))],
              "len": round(rb.length,2),
              "parent": rb.parent.name if rb.parent else None}
# gun mesh local bbox (undeformed)
gm = bpy.data.objects["R1A_VIEW_GUN"].data
xs=[v.co.x for v in gm.vertices]; ys=[v.co.y for v in gm.vertices]; zs=[v.co.z for v in gm.vertices]
out["gun_mesh_local_bbox"] = [[round(min(xs),1),round(min(ys),1),round(min(zs),1)],[round(max(xs),1),round(max(ys),1),round(max(zs),1)]]
print(json.dumps(out, ensure_ascii=False, indent=1))
