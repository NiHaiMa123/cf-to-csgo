import bpy, math, os
from mathutils import Vector

SMD = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\native_vm\source1\cf_native_vm.smd'
TEX = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_assets'
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

# eye sockets in SMD model space — MXH @ CF-space socket world translation
# (the visually-correct surface point; fx bone origins are offset by the
#  anim_world conjugation and sit off the gun — known issue)
EYE_MAIN = (3.167, 21.304, -4.546)   # fix_effect_16: EYE-main + rbw + prism
EYE_CORE = (3.166, 20.814, -4.529)   # fix_effect_15: EYE-CORE

# ---- parse SMD (same as blender_render.py) ----
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
groups = defaultdict(lambda: ([], [], []))
for mat, vs in tris:
    vlist, flist, uvlist = groups[mat]
    base = len(vlist)
    for v in vs:
        vlist.append(v[0])
    flist.append((base, base + 1, base + 2))

def load_img(name):
    img = bpy.data.images.get(name)
    if not img:
        img = bpy.data.images.load(os.path.join(TEX, name + '.png'))
    return img

def principled_mat(name, img_name, emission=False, emit_strength=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = load_img(img_name)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Metallic'].default_value = 0.35
    if not emission:
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Emission Color'].default_value = (0.08, 0.3, 1.0, 1)
        bsdf.inputs['Base Color'].default_value = (0.005, 0.02, 0.08, 1)
        bsdf.inputs['Roughness'].default_value = 1.0
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        bsdf.inputs['Emission Strength'].default_value = emit_strength
        bsdf.inputs['Metallic'].default_value = 0.0
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m

mat_map = {
    'cf_galilace_pb': principled_mat('cf_galilace_pb', 'cf_galilace_pb'),
    'cf_foxarm_bl': principled_mat('cf_foxarm_bl', 'cf_foxarm_bl'),
    'cf_foxhand_bl': principled_mat('cf_foxhand_bl', 'cf_foxhand_bl'),
    'fx_galilace_parts_blue': principled_mat('fx_galilace_parts_blue', 'cf_fx_glow02', emission=True, emit_strength=0.9),
}

for mat, (vlist, flist, uvlist) in groups.items():
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
    me.materials.append(mat_map.get(mat))

# ---- dragon-eye: camera-facing additive sprite planes at the sockets ----
def sprite_plane(name, img_name, pos, size, tint, strength):
    """One additive glow quad, always rotated to face the camera."""
    me = bpy.data.meshes.new(name)
    s = size / 2.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)],
                   [], [(0, 1, 2, 3)])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for li, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uvl.data[li].uv = uv
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.location = pos
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = load_img(img_name)
    # texture color * tint -> emission color; texture alpha -> mix transparency
    mult = nt.nodes.new('ShaderNodeMath'); mult.operation = 'MULTIPLY'
    tintn = nt.nodes.new('ShaderNodeRGB'); tintn.outputs[0].default_value = (*tint, 1)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex.outputs['Color'], sep.inputs['Color'])
    # tint via vector math multiply
    vmul = nt.nodes.new('ShaderNodeVectorMath'); vmul.operation = 'SCALE'
    # simpler: use Mix to tint
    mixn = nt.nodes.new('ShaderNodeMix'); mixn.data_type = 'RGBA'
    mixn.blend_type = 'MULTIPLY'; mixn.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs['Color'], mixn.inputs[6])
    nt.links.new(tintn.outputs[0], mixn.inputs[7])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(mixn.outputs[2], em.inputs['Color'])
    em.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mixs = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tex.outputs['Alpha'], mixs.inputs[0])
    nt.links.new(tr.outputs[0], mixs.inputs[1])
    nt.links.new(em.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    me.materials.append(m)
    return ob

# EYE-rbw: wide dark blue halo (SHINE06 tinted darker, larger)
rbw = sprite_plane('eye_rbw', 'cf_fx_shine06', EYE_MAIN, 5.2,
                   (0.10, 0.33, 0.53), 0.9)
# EYE-main: breathing blue flare
eye = sprite_plane('eye_main', 'cf_fx_shine06', EYE_MAIN, 3.4,
                   (0.13, 0.42, 0.99), 1.6)
# EYE-CORE: small bright pale core
core = sprite_plane('eye_core', 'cf_fx_jyshine03', EYE_CORE, 1.3,
                    (0.72, 0.67, 0.96), 2.2)

cam = bpy.data.cameras.new('cam')
camob = bpy.data.objects.new('cam', cam)
bpy.context.collection.objects.link(camob)
bpy.context.scene.camera = camob
cam.lens = 50
cam.clip_end = 2000

def look_at(obj, pt):
    obj.rotation_euler = (obj.location - Vector(pt)).to_track_quat('Z', 'Y').to_euler()

def face_sprites():
    for ob in (rbw, eye, core):
        ob.rotation_euler = (camob.location - ob.location).to_track_quat('Z', 'Y').to_euler()

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
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.world = bpy.data.worlds.new('w')
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value = (0.03, 0.04, 0.06, 1)

cnt = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
sc.compositing_node_group = cnt
cnt.interface.new_socket('Image', in_out='INPUT', socket_type='NodeSocketColor')
cnt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = cnt.nodes.new('CompositorNodeRLayers')
gl = cnt.nodes.new('CompositorNodeGlare')
try:
    gl.glare_type = 'FOG_GLOW'
    gl.threshold = 1.0
    gl.size = 7
except Exception:
    pass
grp_out = cnt.nodes.new('NodeGroupOutput')
cnt.links.new(rl.outputs['Image'], gl.inputs['Image'])
cnt.links.new(gl.outputs['Image'], grp_out.inputs['Image'])

# ---- still 1: held/first-person view (same as previous fp render) ----
camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
face_sprites()
sc.render.filepath = OUT + 'eye_fp.png'
bpy.ops.render.render(write_still=True)

# ---- still 2: right side profile ----
camob.location = (30, 12, -6)
look_at(camob, (4, 13, -6))
face_sprites()
sc.render.filepath = OUT + 'eye_side.png'
bpy.ops.render.render(write_still=True)

# ---- still 3: close-up of the eye area ----
camob.location = (-1, 16, -5.5)
look_at(camob, EYE_MAIN)
face_sprites()
sc.render.filepath = OUT + 'eye_close.png'
bpy.ops.render.render(write_still=True)

# ---- short breathing loop at fp view (48 frames @30fps = 1.6s, half breath) ----
sc.render.resolution_x = 960
sc.render.resolution_y = 540
frames = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\eye_frames'
os.makedirs(frames, exist_ok=True)
camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
face_sprites()
eye_bs = None
for m in (eye.data.materials[0],):
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeEmission':
            eye_bs = n
for f in range(48):
    # EYE-main breathes between Ck (1,107,237) and (49,151,253): modulate strength
    eye_bs.inputs['Strength'].default_value = 1.2 + 0.7 * (0.5 - 0.5 * math.cos(2 * math.pi * f / 48))
    sc.render.filepath = os.path.join(frames, f'f{f:03d}.png')
    bpy.ops.render.render(write_still=True)

print('EYE RENDERS DONE')
