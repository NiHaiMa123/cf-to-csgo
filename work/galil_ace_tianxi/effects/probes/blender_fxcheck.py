import bpy, math
from mathutils import Vector

OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.hide_render = not ('fx_' in ob.name or 'parts_blue' in ob.name or 'marker' in ob.name or 'halo' in ob.name)
camob = bpy.context.scene.camera

def look_at(obj, pt):
    obj.rotation_euler = (obj.location - Vector(pt)).to_track_quat('Z', 'Y').to_euler()

sc = bpy.context.scene
camob.location = (30, 8, -5)
look_at(camob, (4, 12, -5))
sc.render.filepath = OUT + 'fxcheck.png'
bpy.ops.render.render(write_still=True)

# fp angle too
camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
sc.render.filepath = OUT + 'fxcheck_fp.png'
bpy.ops.render.render(write_still=True)

for ob in bpy.data.objects:
    ob.hide_render = False
print('ok')
