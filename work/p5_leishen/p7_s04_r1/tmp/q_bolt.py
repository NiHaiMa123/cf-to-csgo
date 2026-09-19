import bpy, json
from mathutils import Vector
gun = bpy.data.objects["R1A_VIEW_GUN"]
dg = bpy.context.evaluated_depsgraph_get()
gev = gun.evaluated_get(dg)
me = gev.to_mesh()
vg = {g.name: g.index for g in gun.vertex_groups}
out = {}
for grp in ["v_weapon.M4A1_Clip","v_weapon.M4A1_Bolt"]:
    gi = vg[grp]
    pts = [gev.matrix_world @ v.co for v in me.vertices if any(g.group==gi for g in v.groups)]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    out[grp] = {"min":[round(min(xs),1),round(min(ys),1),round(min(zs),1)],
                "max":[round(max(xs),1),round(max(ys),1),round(max(zs),1)]}
gev.to_mesh_clear()
print(json.dumps(out, ensure_ascii=False))
