import bpy
import os

OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"
OUT_PNG = r"D:\project\cf_to_csgo\work\tulong_chuntao\texture\up\kukri_beast_baked.png"
IMG_DIF = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
IMG_S = r"D:\project\cf_to_csgo\work\tulong_chuntao\acquire\verified_root\ModelTextures\SpecularMap\Kukri_Beast_s.PNG"

knife = bpy.data.objects.get([o.name for o in bpy.data.objects if 'kukri' in o.name][0])
assert knife, "knife object missing"

# target image (UV-space bake, 2048^2 like pipeline diffuse)
img = bpy.data.images.new('baked_kukri', 2048, 2048, alpha=False)

mt = bpy.data.materials.new('bake_add')
mt.use_nodes = True
nt = mt.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
t1 = nt.nodes.new('ShaderNodeTexImage')
t1.image = bpy.data.images.load(IMG_DIF)
t2 = nt.nodes.new('ShaderNodeTexImage')
t2.image = bpy.data.images.load(IMG_S)
m = nt.nodes.new('ShaderNodeMixRGB')
m.blend_type = 'ADD'
m.inputs['Fac'].default_value = 1.0
nt.links.new(t1.outputs['Color'], m.inputs[1])
nt.links.new(t2.outputs['Color'], m.inputs[2])
nt.links.new(m.outputs[0], em.inputs['Color'])
nt.links.new(em.outputs[0], out.inputs['Surface'])
# bake target: active image node
tb = nt.nodes.new('ShaderNodeTexImage')
tb.image = img
tb.select = True
nt.nodes.active = tb

knife.data.materials.clear()
knife.data.materials.append(mt)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'  # bake requires Cycles
sc.cycles.samples = 1
sc.cycles.device = 'CPU'
sc.render.bake.use_clear = True

bpy.ops.object.select_all(action='DESELECT')
knife.select_set(True)
bpy.context.view_layer.objects.active = knife
sc.render.bake.margin = 4
bpy.ops.object.bake(type='EMIT')

img.filepath_raw = OUT_PNG
img.file_format = 'PNG'
img.save()
print("baked ->", OUT_PNG)

# quick verify render: apply baked image back to knife
img2 = bpy.data.images.load(OUT_PNG)
mt2 = bpy.data.materials.new('baked_show')
mt2.use_nodes = True
nt2 = mt2.node_tree
nt2.nodes.clear()
o2 = nt2.nodes.new('ShaderNodeOutputMaterial')
e2 = nt2.nodes.new('ShaderNodeEmission')
x2 = nt2.nodes.new('ShaderNodeTexImage')
x2.image = img2
nt2.links.new(x2.outputs['Color'], e2.inputs['Color'])
nt2.links.new(e2.outputs[0], o2.inputs['Surface'])
knife.data.materials.clear()
knife.data.materials.append(mt2)
sc.render.filepath = os.path.join(OUTDIR, 'baked_verify.png')
bpy.ops.render.render(write_still=True)
print("verify rendered")
