import bpy, json
from mathutils import Vector
scn = bpy.context.scene
# hide arm meshes, render gun only
for n in ["R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_render = True
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
scn.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/tmp/gun_only.png"
bpy.ops.render.render(write_still=True)
for n in ["R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_render = False
# identify which vertex group owns verts near the pole: pole ~ x 1-2, y -4..-3, z up to 3.4
gun = bpy.data.objects["R1A_VIEW_GUN"]
dg = bpy.context.evaluated_depsgraph_get()
gev = gun.evaluated_get(dg); me = gev.to_mesh()
vg = {g.index: g.name for g in gun.vertex_groups}
hits = {}
for v in me.vertices:
    wp = gev.matrix_world @ v.co
    if 0.8 < wp.x < 2.5 and -5.0 < wp.y < -3.0 and wp.z > 1.6:
        for g in v.groups:
            nm = vg.get(g.group, "?")
            hits[nm] = hits.get(nm, 0) + 1
gev.to_mesh_clear()
print(json.dumps(hits))
