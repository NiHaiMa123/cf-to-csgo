import bpy, json
from mathutils import Vector
scn = bpy.context.scene
cam = bpy.data.objects["R1A_CAM_STUDIO"]
# keep the eye_c framing
cam.location = Vector((14.0,-16.0,6.0))
cam.rotation_euler = (Vector((1.5,-2.0,-0.5))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens = 32
# hide arms -> gun only
bpy.data.objects["R1A_VIEW_GLOVE"].hide_render = True
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_render = True
bpy.data.objects["R1A_VIEW_GLOVE"].hide_viewport = True
bpy.data.objects["R1A_VIEW_SLEEVE"].hide_viewport = True
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\iso_gun.png"
bpy.ops.render.render(write_still=True)
# list all visible-render meshes with world bbox, find tall/thin ones
dg = bpy.context.evaluated_depsgraph_get()
res = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.hide_render or o.hide_viewport:
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    if not me.vertices: continue
    ws = [ev.matrix_world @ v.co for v in me.vertices]
    xs=[v.x for v in ws]; ys=[v.y for v in ws]; zs=[v.z for v in ws]
    res.append({"name": o.name, "min":[round(min(xs),1),round(min(ys),1),round(min(zs),1)],
                "max":[round(max(xs),1),round(max(ys),1),round(max(zs),1)]})
    ev.to_mesh_clear()
print(json.dumps(res, ensure_ascii=False))
