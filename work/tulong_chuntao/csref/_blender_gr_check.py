import bpy
import math
import os
from mathutils import Matrix

SMD = r"D:\project\cf_to_csgo\work\tulong_chuntao\native_vm\source1\cf_native_vm.smd"
IMG_KNIFE = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
IMG_HAND = r"D:\project\cf_to_csgo\work\galil_ace_tianxi\decode\nini_gr\FVIEW_HAND_Nini_GR.PNG"
IMG_ARM = r"D:\project\cf_to_csgo\work\galil_ace_tianxi\decode\nini_gr\FVIEW_ARM_Nini_GR.PNG"
OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tris = []
mode = None
cur_mat = None
buf = []
for ln in open(SMD, encoding='utf-8', errors='replace'):
    s = ln.strip()
    if s == 'triangles':
        mode = 't'
        continue
    if not s:
        continue
    if mode == 't':
        if s == 'end':
            mode = None
            continue
        p = s.split()
        try:
            float(p[1])
            int(p[0])
        except (ValueError, IndexError):
            cur_mat = s
            buf = []
            continue
        pos = [float(x) for x in p[1:4]]
        uv = [float(p[7]), float(p[8])]
        buf.append((pos, uv))
        if len(buf) == 3:
            tris.append((cur_mat, buf))
            buf = []

print("parsed tris:", len(tris))

mats = {}
for m, b in tris:
    mats.setdefault(m, []).append(b)

objs = {}
for m, tlist in mats.items():
    vs, fs, uvs = [], [], []
    for b in tlist:
        n = len(vs)
        for pos, uv in b:
            vs.append(pos)
            uvs.append(uv)
        fs.append((n, n + 1, n + 2))
    me = bpy.data.meshes.new('m_' + m)
    me.from_pydata(vs, [], fs)
    uvl = me.uv_layers.new(name='UVMap')
    for i, poly in enumerate(me.polygons):
        for j, li in enumerate(poly.loop_indices):
            uvl.data[li].uv = uvs[i * 3 + j]
    ob = bpy.data.objects.new(m, me)
    bpy.context.collection.objects.link(ob)
    objs[m] = ob


def make_mat(name, imgpath):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    nt = mt.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(imgpath)
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return mt


matmap = {'cf_kukri_beast': IMG_KNIFE,
          'cf_nini_hand_gr': IMG_HAND,
          'cf_nini_arm_gr': IMG_ARM}
for m, ob in objs.items():
    ob.data.materials.append(make_mat(m, matmap.get(m, IMG_KNIFE)))

cd = bpy.data.cameras.new('cam')
cd.sensor_fit = 'VERTICAL'
cd.angle = math.radians(40)
cd.clip_start = 0.05
cd.clip_end = 1000
cam = bpy.data.objects.new('cam', cd)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1024
sc.render.resolution_y = 595
sc.view_settings.view_transform = 'Standard'

# knife bbox
import numpy as np
kvs = np.array([v.co[:] for v in objs[[m for m in objs if 'kukri' in m][0]].data.vertices])
print('knife bbox min', kvs.min(0), 'max', kvs.max(0))
cen = (kvs.min(0) + kvs.max(0)) / 2
d = float(np.linalg.norm(kvs.max(0) - kvs.min(0))) * 0.8 + 15

# view the +X face and -X face straight on
for tag, mw in {
    'gr_Rside': Matrix([[0, 0, 1, cen[0] + d], [1, 0, 0, cen[1]],
                        [0, 1, 0, cen[2]], [0, 0, 0, 1]]),
    'gr_Lside': Matrix([[0, 0, -1, cen[0] - d], [-1, 0, 0, cen[1]],
                        [0, 1, 0, cen[2]], [0, 0, 0, 1]]),
}.items():
    cam.matrix_world = mw
    sc.render.filepath = os.path.join(OUTDIR, tag + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', tag)

print("DONE")
