import bpy
import math
import os
from mathutils import Matrix

SMD = r"D:\project\cf_to_csgo\work\tulong_chuntao\native_vm\source1\cf_native_vm.smd"
IMG_KNIFE = r"D:\project\cf_to_csgo\work\tulong_chuntao\decode\PV-Kukri_Beast.png"
IMG_HAND = r"D:\project\cf_to_csgo\work\galil_ace_tianxi\decode\nini_gr\FVIEW_HAND_Nini_GR.PNG"
IMG_ARM = r"D:\project\cf_to_csgo\work\galil_ace_tianxi\decode\nini_gr\FVIEW_ARM_Nini_GR.PNG"
OUTDIR = r"D:\project\cf_to_csgo\work\tulong_chuntao\csref\_diag"

# --- clean scene ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# --- parse smd triangles ---
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


import traceback
try:
    # --- build one mesh per material ---
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
                uvl.data[li].uv = uvs[i][j]
        ob = bpy.data.objects.new(m, me)
        bpy.context.collection.objects.link(ob)
        objs[m] = ob
    
    
except Exception:
    print("TRACEBACK:", traceback.format_exc())
