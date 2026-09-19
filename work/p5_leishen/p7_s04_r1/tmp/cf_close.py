import bpy, json
from mathutils import Vector
scn = bpy.context.scene
# find world bbox of all CF_ objects at idle f10
scn.r1a_clip = "R1A_CF_idle_0"; scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
allmin = Vector((1e9,)*3); allmax = Vector((-1e9,)*3)
per = {}
for o in bpy.data.objects:
    if not o.name.startswith("CF_"): continue
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    if not me.vertices: ev.to_mesh_clear(); continue
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    per[o.name] = [list(mn), list(mx)]
    for i in range(3):
        allmin[i] = min(allmin[i], mn[i]); allmax[i] = max(allmax[i], mx[i])
    ev.to_mesh_clear()
print("all bbox:", [round(v,1) for v in allmin], [round(v,1) for v in allmax])
for k,v in per.items():
    print(k, [round(x,1) for x in v[0]], "..", [round(x,1) for x in v[1]])
