import bpy, json
from mathutils import Vector
scn = bpy.context.scene
out = {}
for clip, frame in [("idle_0", 10), ("reload", 72), ("select", 32)]:
    scn.r1a_source_clip = clip; scn.frame_set(frame)
    bpy.context.view_layer.update()
    gun = bpy.data.objects["R1A_VIEW_GUN"]
    dg = bpy.context.evaluated_depsgraph_get()
    gev = gun.evaluated_get(dg); me = gev.to_mesh()
    vg = {g.name: g.index for g in gun.vertex_groups}
    res = {}
    for grp in ["v_weapon.M4A1_Clip", "v_weapon.M4A1_Bolt"]:
        gi = vg[grp]
        pts = [gev.matrix_world @ v.co for v in me.vertices if any(g.group==gi for g in v.groups)]
        ctr = Vector((0,0,0))
        for p in pts: ctr += p
        ctr /= max(len(pts),1)
        res[grp.split(".")[-1]] = [round(v,2) for v in ctr]
    gev.to_mesh_clear()
    arm = bpy.data.objects["R1A_VIEW_ARM"]
    ph = arm.matrix_world @ arm.pose.bones["v_weapon.M4A1_Parent"].head
    res["gun_root"] = [round(v,2) for v in ph]
    out["%s_f%d" % (clip, frame)] = res
print(json.dumps(out, indent=1))
