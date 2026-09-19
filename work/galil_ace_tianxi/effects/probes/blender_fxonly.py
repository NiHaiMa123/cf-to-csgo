import bpy, math
from mathutils import Vector

OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

# hide everything except fx mesh
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.hide_render = not ('fx_' in ob.name or 'parts_blue' in ob.name)

camob = bpy.context.scene.camera
def look_at(obj, pt):
    d = obj.location - Vector(pt)
    obj.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

sc = bpy.context.scene
# fx mesh bbox: X 2.7-5.2, Y -11.9..7.3, Z -5.5..-2.4 -> center ~(4,-2.3,-4)
camob.location = (30, -2, -4)
look_at(camob, (4, -2, -4))
sc.render.filepath = OUT + 'fxonly_side.png'
bpy.ops.render.render(write_still=True)

camob.location = (4, -2, 25)
look_at(camob, (4, -2, -4))
sc.render.filepath = OUT + 'fxonly_top.png'
bpy.ops.render.render(write_still=True)

# and along the gun axis (from muzzle direction)
camob.location = (4, -2, -40)
look_at(camob, (4, -2, -4))
sc.render.filepath = OUT + 'fxonly_back.png'
bpy.ops.render.render(write_still=True)

# restore visibility for later renders
for ob in bpy.data.objects:
    ob.hide_render = False
print('DONE')
