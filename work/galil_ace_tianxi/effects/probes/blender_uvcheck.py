import bpy
from mathutils import Vector

ob = bpy.data.objects.get('fx_galilace_parts_blue')
me = ob.data
print('uv layers:', [l.name for l in me.uv_layers])
uvl = me.uv_layers.active
if uvl:
    us = [tuple(round(c, 3) for c in d.uv) for d in uvl.data[:12]]
    print('first uvs:', us)
print('polys:', len(me.polygons), 'loops:', len(me.loops))

# also print material emission links
m = bpy.data.materials.get('fx_galilace_parts_blue')
for l in m.node_tree.links:
    print('link:', l.from_node.bl_idname, l.from_socket.name, '->', l.to_node.bl_idname, l.to_socket.name)
for n in m.node_tree.nodes:
    if n.bl_idname == 'ShaderNodeBsdfPrincipled':
        print('basecol', n.inputs['Base Color'].default_value, 'emitS', n.inputs['Emission Strength'].default_value)
    if n.bl_idname == 'ShaderNodeTexImage':
        print('tex img:', n.image.name if n.image else None)

# render fx only
import math
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = not ('fx_' in o.name or 'marker' in o.name or 'halo' in o.name)
camob = bpy.context.scene.camera
camob.location = (30, 8, -5)
camob.rotation_euler = (camob.location - Vector((4, 12, -5))).to_track_quat('Z', 'Y').to_euler()
bpy.context.scene.render.filepath = OUT + 'fxcheck2.png'
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    o.hide_render = False
print('done')
