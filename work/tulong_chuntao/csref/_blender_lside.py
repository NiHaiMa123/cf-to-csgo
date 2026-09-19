import bpy
import math
from mathutils import Matrix

OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1024
sc.render.resolution_y = 595
sc.view_settings.view_transform = 'Standard'

cam = bpy.data.objects['cam']
knife = bpy.data.objects['cf_kukri_beast']

# restore diffuse emission material on knife
IMG_DIF = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
mt = bpy.data.materials.new('probe_dif')
mt.use_nodes = True
nt = mt.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(IMG_DIF)
nt.links.new(tex.outputs['Color'], em.inputs['Color'])
nt.links.new(em.outputs[0], out.inputs['Surface'])
knife.data.materials.clear()
knife.data.materials.append(mt)

# both sides: -X view then +X view, also try opposite winding visibility
cam.matrix_world = Matrix([[0, 0, -1, -33], [-1, 0, 0, -9], [0, 1, 0, 4.7],
                           [0, 0, 0, 1]])
sc.render.filepath = OUTDIR + r"\lside_check.png"
bpy.ops.render.render(write_still=True)
print("done L")
