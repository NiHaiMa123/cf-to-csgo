import bpy
import math
import os
from mathutils import Matrix

OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"
IMG_DIF = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
IMG_S = r"D:\project\cf_to_csgo\work\tulong_chuntao\acquire\verified_root\ModelTextures\SpecularMap\Kukri_Beast_s.PNG"

knife = bpy.data.objects.get('cf_kukri_beast')
assert knife, "knife object missing"

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1024
sc.render.resolution_y = 595
sc.view_settings.view_transform = 'Standard'

cam = bpy.data.objects.get('cam')
cam.matrix_world = Matrix([[0, 0, 1, 27], [1, 0, 0, -9], [0, 1, 0, 4.7],
                           [0, 0, 0, 1]])
sc.camera = cam


def mix_mat(dif_w, s_w, add):
    mt = bpy.data.materials.new('probe')
    mt.use_nodes = True
    nt = mt.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    t1 = nt.nodes.new('ShaderNodeTexImage')
    t1.image = bpy.data.images.load(IMG_DIF)
    t2 = nt.nodes.new('ShaderNodeTexImage')
    t2.image = bpy.data.images.load(IMG_S)
    if add:
        m = nt.nodes.new('ShaderNodeMixRGB')
        m.blend_type = 'ADD'
        m.inputs['Fac'].default_value = 1.0
        nt.links.new(t1.outputs['Color'], m.inputs[1])
        nt.links.new(t2.outputs['Color'], m.inputs[2])
        nt.links.new(m.outputs[0], em.inputs['Color'])
    else:
        m = nt.nodes.new('ShaderNodeMixRGB')
        m.blend_type = 'MIX'
        m.inputs['Fac'].default_value = s_w
        nt.links.new(t1.outputs['Color'], m.inputs[1])
        nt.links.new(t2.outputs['Color'], m.inputs[2])
        nt.links.new(m.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return mt


# variants: (name, dif_w, s_w, add)
variants = [
    ('dif', 1, 0, False),
    ('spec', 0, 1, False),
    ('mix50', 0.5, 0.5, False),
    ('add', 1, 1, True),
]
for tag, dw, sw, add in variants:
    mt = mix_mat(dw, sw, add)
    knife.data.materials.clear()
    knife.data.materials.append(mt)
    sc.render.filepath = os.path.join(OUTDIR, 'blender_mix_%s.png' % tag)
    bpy.ops.render.render(write_still=True)
    print('rendered', tag)

print("DONE")
