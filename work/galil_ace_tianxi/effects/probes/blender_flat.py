import bpy, math
from mathutils import Vector

OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

# flat blue unlit-ish material for fx plates — placement check only
m = bpy.data.materials.new('fx_flat_blue')
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
bs.inputs['Base Color'].default_value = (0.1, 0.35, 1.0, 1)
bs.inputs['Roughness'].default_value = 0.9
bs.inputs['Metallic'].default_value = 0.0
nt.links.new(bs.outputs[0], out.inputs['Surface'])

ob = bpy.data.objects['fx_galilace_parts_blue']
ob.data.materials.clear()
ob.data.materials.append(m)
# hide marker/halo for a clean placement check
for o in bpy.data.objects:
    if 'marker' in o.name or 'halo' in o.name:
        o.hide_render = True

camob = bpy.context.scene.camera
def look_at(obj, pt):
    obj.rotation_euler = (obj.location - Vector(pt)).to_track_quat('Z', 'Y').to_euler()
sc = bpy.context.scene

camob.location = (30, 8, -5)
look_at(camob, (4, 12, -5))
sc.render.filepath = OUT + 'flat_side.png'
bpy.ops.render.render(write_still=True)

camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
sc.render.filepath = OUT + 'flat_fp.png'
bpy.ops.render.render(write_still=True)
print('done')
