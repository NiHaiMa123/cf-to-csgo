import bpy, math, os
from mathutils import Vector

SMD = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\native_vm\source1\cf_native_vm.smd'
TEX = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_assets'
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'
FRAMES_DIR = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\frames'
os.makedirs(FRAMES_DIR, exist_ok=True)

# fx3 attachment in SMD space (from sockets.json * MXH)
FX3 = (4.08, 8.89, -4.32)

# ---- parse SMD ----
lines = open(SMD).read().splitlines()
i = lines.index('triangles') + 1
tris = []   # (mat, [v0,v1,v2]) v=(pos,norm,uv)
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

# ---- clear scene ----
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
    if emission:
        # fx plate: blue emission tinted by Ck color (0.075,0.376,1.0)
        # boosted so the mostly-dark glow tex still reads as blue glow
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
    # rebuild uv layer from per-corner data
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

# ---- fx3 marker: small emissive sphere where particle spawns ----
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=FX3)
mk = bpy.context.object
mk.name = 'fx3_marker'
mm = bpy.data.materials.new('fx3_marker')
mm.use_nodes = True
nt = mm.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
bs.inputs['Base Color'].default_value = (0.05, 0.35, 1.0, 1)
for n in bs.inputs:
    if n.name.startswith('Emission') and 'Strength' in n.name:
        n.default_value = 20.0
    elif n.name.startswith('Emission'):
        n.default_value = (0.1, 0.5, 1.0, 1)
nt.links.new(bs.outputs[0], out.inputs['Surface'])
mk.data.materials.append(mm)

# bigger soft glow halo around fx3: transparent emission shell
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=FX3)
halo = bpy.context.object
halo.name = 'fx3_halo'
hm = bpy.data.materials.new('fx3_halo')
hm.use_nodes = True
nt = hm.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.02, 0.15, 0.7, 1)
em.inputs['Strength'].default_value = 0.6
nt.links.new(em.outputs[0], out.inputs['Surface'])
hm.surface_render_method = 'BLENDED'
halo.data.materials.append(hm)

# ---- camera & lights ----
cam = bpy.data.cameras.new('cam')
camob = bpy.data.objects.new('cam', cam)
bpy.context.collection.objects.link(camob)
bpy.context.scene.camera = camob
cam.lens = 50
cam.clip_end = 2000

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
pt2 = bpy.data.lights.new('pt2', 'POINT'); pt2.energy = 150
pt2ob = bpy.data.objects.new('pt2', pt2)
bpy.context.collection.objects.link(pt2ob)
pt2ob.location = (-8, 20, -10)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new('w')
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value = (0.03, 0.04, 0.06, 1)

# compositor bloom (Blender 5.x: compositing_node_group)
cnt = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
sc.compositing_node_group = cnt
cnt.interface.new_socket('Image', in_out='INPUT', socket_type='NodeSocketColor')
cnt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = cnt.nodes.new('CompositorNodeRLayers')
gl = cnt.nodes.new('CompositorNodeGlare')
try:
    gl.glare_type = 'FOG_GLOW'
    gl.threshold = 1.2
    gl.size = 6
except Exception:
    pass
grp_out = cnt.nodes.new('NodeGroupOutput')
grp_out.location = (600, 0)
cnt.links.new(rl.outputs['Image'], gl.inputs['Image'])
cnt.links.new(gl.outputs['Image'], grp_out.inputs['Image'])

# ---- still 1: first-person-ish view (camera behind gun looking along +Y) ----
camob.location = (-2, -6, -3.0)
look_at(camob, (4.5, 20, -6.5))
sc.render.filepath = OUT + 'fp.png'
bpy.ops.render.render(write_still=True)

# ---- still 2: side profile ----
camob.location = (30, 12, -6)
look_at(camob, (4, 13, -6))
sc.render.filepath = OUT + 'side_tex.png'
bpy.ops.render.render(write_still=True)

# ---- still 3: left side ----
camob.location = (-20, 12, -4)
look_at(camob, (4, 13, -6))
sc.render.filepath = OUT + 'side_left.png'
bpy.ops.render.render(write_still=True)

# ---- turntable video: orbit gun centre ----
sc.render.resolution_x = 960
sc.render.resolution_y = 540
centre = Vector((4.1, 12, -6))
r = 34
nfr = 90
for f in range(nfr):
    a = 2 * math.pi * f / nfr
    camob.location = centre + Vector((r * math.sin(a), 0, r * 0.35 * math.cos(a) + 4))
    look_at(camob, centre)
    # breathing: modulate fx emission strength (2s cycle @30fps -> 60f period)
    fxmat = mat_map['fx_galilace_parts_blue']
    for n in fxmat.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            n.inputs['Emission Strength'].default_value = 0.6 + 0.5 * math.sin(2 * math.pi * f / 60)
    sc.render.filepath = os.path.join(FRAMES_DIR, f'f{f:03d}.png')
    bpy.ops.render.render(write_still=True)

print('RENDERS DONE')
