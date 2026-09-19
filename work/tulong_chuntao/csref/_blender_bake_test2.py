import bpy
import os
import numpy as np
from mathutils import Matrix

OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"
IMG_DIF = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast_spring.png"
IMG_S = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\maps\Kukri_Beast_Spring_S.PNG"

knife = bpy.data.objects.get([o.name for o in bpy.data.objects if 'kukri' in o.name][0])
assert knife, "knife object missing"

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1024
sc.render.resolution_y = 595
sc.view_settings.view_transform = 'Standard'

cam = bpy.data.objects.get('cam')
kvs = np.array([v.co[:] for v in knife.data.vertices])
cen = (kvs.min(0) + kvs.max(0)) / 2
d = float(np.linalg.norm(kvs.max(0) - kvs.min(0))) * 0.8 + 15
cam.matrix_world = Matrix([[0, 0, 1, cen[0] + d], [1, 0, 0, cen[1]],
                           [0, 1, 0, cen[2]], [0, 0, 0, 1]])
sc.camera = cam


def spec_node(nt, mode):
    """return socket carrying (possibly powered) spec color"""
    t2 = nt.nodes.new('ShaderNodeTexImage')
    t2.image = bpy.data.images.load(IMG_S)
    if mode == 'pow2':
        pw = nt.nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.inputs[1].default_value = 2.0
        nt.links.new(t2.outputs['Color'], pw.inputs[0])
        return pw.outputs[0]
    if mode == 'pow3':
        pw = nt.nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.inputs[1].default_value = 3.0
        nt.links.new(t2.outputs['Color'], pw.inputs[0])
        return pw.outputs[0]
    return t2.outputs['Color']


def mix_mat(tag):
    mt = bpy.data.materials.new('bt_%s' % tag)
    mt.use_nodes = True
    nt = mt.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    t1 = nt.nodes.new('ShaderNodeTexImage')
    t1.image = bpy.data.images.load(IMG_DIF)
    m = nt.nodes.new('ShaderNodeMixRGB')
    nt.links.new(t1.outputs['Color'], m.inputs[1])
    if tag == 'add10':
        m.blend_type = 'ADD'; m.inputs['Fac'].default_value = 1.0
        nt.links.new(spec_node(nt, 'flat'), m.inputs[2])
    elif tag == 'add07':
        m.blend_type = 'ADD'; m.inputs['Fac'].default_value = 0.7
        nt.links.new(spec_node(nt, 'flat'), m.inputs[2])
    elif tag == 'pow2_a09':
        m.blend_type = 'ADD'; m.inputs['Fac'].default_value = 0.9
        nt.links.new(spec_node(nt, 'pow2'), m.inputs[2])
    elif tag == 'pow3_a10':
        m.blend_type = 'ADD'; m.inputs['Fac'].default_value = 1.0
        nt.links.new(spec_node(nt, 'pow3'), m.inputs[2])
    elif tag == 'screen':
        m.blend_type = 'SCREEN'; m.inputs['Fac'].default_value = 1.0
        nt.links.new(spec_node(nt, 'flat'), m.inputs[2])
    nt.links.new(m.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return mt


for tag in ('add10', 'add07', 'pow2_a09', 'pow3_a10', 'screen'):
    knife.data.materials.clear()
    knife.data.materials.append(mix_mat(tag))
    sc.render.filepath = os.path.join(OUTDIR, 'bt_%s.png' % tag)
    bpy.ops.render.render(write_still=True)
    print('rendered', tag)

print("DONE")
