import bpy, math, os
from mathutils import Vector

SMD = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\native_vm\source1\cf_native_vm.smd'
TEX = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_assets'
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

lines = open(SMD).read().splitlines()
i = lines.index('triangles') + 1
tris = []
while i < len(lines):
    ln = lines[i]
    if ln.strip() == 'end':
        break
    if not ln.startswith((' ', '\t')):
        cur = ln.strip()
        vs = []
        for k in range(3):
            p = lines[i + 1 + k].split()
            vs.append(((float(p[1]), float(p[2]), float(p[3])),
                       (float(p[7]), float(p[8]))))
        tris.append((cur, vs))
        i += 4
    else:
        i += 1

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

from collections import defaultdict
groups = defaultdict(lambda: ([], []))
for mat, vs in tris:
    vlist, flist = groups[mat]
    base = len(vlist)
    for v in vs:
        vlist.append(v[0])
    flist.append((base, base + 1, base + 2))

def load_img(name):
    img = bpy.data.images.get(name)
    if not img:
        img = bpy.data.images.load(os.path.join(TEX, name + '.png'))
    return img

def mat_basic(name, img_name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = load_img(img_name)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Metallic'].default_value = 0.35
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m

def mat_eye(name, img_name):
    # additive-ish: emission modulated by texture color+alpha, blue tint
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = load_img(img_name)
    mixn = nt.nodes.new('ShaderNodeMix'); mixn.data_type = 'RGBA'
    mixn.blend_type = 'MULTIPLY'; mixn.inputs[0].default_value = 1.0
    tint = nt.nodes.new('ShaderNodeRGB')
    tint.outputs[0].default_value = (0.15, 0.45, 1.0, 1)
    nt.links.new(tex.outputs['Color'], mixn.inputs[6])
    nt.links.new(tint.outputs[0], mixn.inputs[7])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(mixn.outputs[2], em.inputs['Color'])
    em.inputs['Strength'].default_value = 4.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mixs = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tex.outputs['Alpha'], mixs.inputs[0])
    nt.links.new(tr.outputs[0], mixs.inputs[1])
    nt.links.new(em.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    return m

mat_map = {
    'cf_galilace_pb': mat_basic('cf_galilace_pb', 'cf_galilace_pb'),
    'cf_foxarm_bl': mat_basic('cf_foxarm_bl', 'cf_foxarm_bl'),
    'cf_foxhand_bl': mat_basic('cf_foxhand_bl', 'cf_foxhand_bl'),
    'fx_galilace_parts_blue': mat_basic('fx_galilace_parts_blue', 'cf_fx_glow02'),
    'fx_galilace_eye': mat_eye('fx_galilace_eye', 'cf_fx_shine06_b'),
    'fx_galilace_eye_core': mat_eye('fx_galilace_eye_core', 'cf_fx_jyshine03_b'),
}

for mat, (vlist, flist) in groups.items():
    me = bpy.data.meshes.new(mat)
    me.from_pydata(vlist, [], flist)
    me.update()
    uvs = []
    for m2, vs in tris:
        if m2 == mat:
            for v in vs:
                uvs.append(v[1])
    uvl = me.uv_layers.new(name='UVMap')
    for li, uv in enumerate(uvs):
        uvl.data[li].uv = uv
    ob = bpy.data.objects.new(mat, me)
    bpy.context.collection.objects.link(ob)
    mm = mat_map.get(mat)
    if mm:
        me.materials.append(mm)

cam = bpy.data.cameras.new('cam')
camob = bpy.data.objects.new('cam', cam)
bpy.context.collection.objects.link(camob)
bpy.context.scene.camera = camob
cam.lens = 50; cam.clip_end = 2000

def look_at(obj, pt):
    obj.rotation_euler = (obj.location - Vector(pt)).to_track_quat('Z', 'Y').to_euler()

sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4
sunob = bpy.data.objects.new('sun', sun)
bpy.context.collection.objects.link(sunob)
sunob.rotation_euler = (math.radians(55), 0, math.radians(25))
pt = bpy.data.lights.new('pt', 'POINT'); pt.energy = 300
ptob = bpy.data.objects.new('pt', pt)
bpy.context.collection.objects.link(ptob)
ptob.location = (12, 10, 6)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value = (0.03, 0.04, 0.06, 1)

cnt = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
sc.compositing_node_group = cnt
cnt.interface.new_socket('Image', in_out='INPUT', socket_type='NodeSocketColor')
cnt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = cnt.nodes.new('CompositorNodeRLayers')
gl = cnt.nodes.new('CompositorNodeGlare')
try:
    gl.glare_type = 'FOG_GLOW'; gl.threshold = 0.8; gl.size = 7
except Exception:
    pass
grp_out = cnt.nodes.new('NodeGroupOutput')
cnt.links.new(rl.outputs['Image'], gl.inputs['Image'])
cnt.links.new(gl.outputs['Image'], grp_out.inputs['Image'])

# fp view
camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
sc.render.filepath = OUT + 'eyeq_fp.png'
bpy.ops.render.render(write_still=True)

# close-up on eye area
camob.location = (-3, 13, -5.5)
look_at(camob, (2.7, 20.8, -4.5))
sc.render.filepath = OUT + 'eyeq_close.png'
bpy.ops.render.render(write_still=True)
print('EYEQ DONE')
