import bpy
import os
from mathutils import Matrix
import numpy as np

OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"
IMG_DIF = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
IMG_S = r"D:\project\cf_to_csgo\work\tulong_chuntao\acquire\verified_root\ModelTextures\SpecularMap\Kukri_Beast_s.PNG"

knife = bpy.data.objects.get('cf_kukri_beast')
assert knife, "knife object missing - run _blender_gr_check.py first"

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1024
sc.render.resolution_y = 595
sc.view_settings.view_transform = 'Standard'

cam = bpy.data.objects.get('cam')
# reuse the +X face camera position from gr check
import math
kvs = np.array([v.co[:] for v in knife.data.vertices])
cen = (kvs.min(0) + kvs.max(0)) / 2
d = float(np.linalg.norm(kvs.max(0) - kvs.min(0))) * 0.8 + 15
cam.matrix_world = Matrix([[0, 0, 1, cen[0] + d], [1, 0, 0, cen[1]],
                           [0, 1, 0, cen[2]], [0, 0, 0, 1]])
sc.camera = cam


def mix_mat(mode, k):
    mt = bpy.data.materials.new('bake_%s' % mode)
    mt.use_nodes = True
    nt = mt.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    t1 = nt.nodes.new('ShaderNodeTexImage')
    t1.image = bpy.data.images.load(IMG_DIF)
    if mode == 'dif' or mode == 'difx':
        src = t1.outputs['Color']
        if mode == 'difx':
            gm = nt.nodes.new('ShaderNodeGamma')
            gm.inputs[1].default_value = k
            nt.links.new(src, gm.inputs[0])
            src = gm.outputs[0]
        nt.links.new(src, em.inputs['Color'])
    else:
        t2 = nt.nodes.new('ShaderNodeTexImage')
        t2.image = bpy.data.images.load(IMG_S)
        m = nt.nodes.new('ShaderNodeMixRGB')
        m.blend_type = mode  # 'ADD' or 'SCREEN' or 'MIX'
        m.inputs['Fac'].default_value = k
        nt.links.new(t1.outputs['Color'], m.inputs[1])
        nt.links.new(t2.outputs['Color'], m.inputs[2])
        nt.links.new(m.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return mt


variants = [
    ('dif', 'dif', 1.0),
    ('difx_g06', 'difx', 0.6),      # gamma brighten
    ('difx_g05', 'difx', 0.5),
    ('add07', 'ADD', 0.7),
    ('add10', 'ADD', 1.0),
    ('screen', 'SCREEN', 1.0),
    ('mix50', 'MIX', 0.5),
]
for tag, mode, k in variants:
    knife.data.materials.clear()
    knife.data.materials.append(mix_mat(mode, k))
    sc.render.filepath = os.path.join(OUTDIR, 'bake_%s.png' % tag)
    bpy.ops.render.render(write_still=True)
    print('rendered', tag)

print("DONE")
