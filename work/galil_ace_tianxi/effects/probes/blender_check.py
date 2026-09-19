import bpy, math
from mathutils import Vector

SMD = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\native_vm\source1\cf_native_vm.smd'
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

# ---- parse SMD ----
lines = open(SMD).read().splitlines()
tris = []          # (mat, [(x,y,z),x3])
i = lines.index('triangles') + 1
cur = None
while i < len(lines):
    ln = lines[i]
    if ln.strip() == 'end':
        break
    if not ln.startswith((' ', '\t')):
        cur = ln.strip()
        vs = []
        for k in range(3):
            p = lines[i + 1 + k].split()
            vs.append((float(p[1]), float(p[2]), float(p[3]),
                       float(p[7]), float(p[8])))
        tris.append((cur, vs))
        i += 4
    else:
        i += 1

# ---- clear scene ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in bpy.data.meshes: bpy.data.meshes.remove(c)
for m in bpy.data.materials: bpy.data.materials.remove(m)

# ---- group verts/faces by material ----
from collections import defaultdict
groups = defaultdict(lambda: ([], []))
for mat, vs in tris:
    vlist, flist = groups[mat]
    base = len(vlist)
    for v in vs:
        vlist.append((v[0], v[1], v[2]))
    flist.append((base, base + 1, base + 2))

mat_objs = {}
for mat, (vlist, flist) in groups.items():
    me = bpy.data.meshes.new(mat)
    me.from_pydata(vlist, [], flist)
    me.update()
    ob = bpy.data.objects.new(mat, me)
    bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new(mat)
    if 'fx_' in mat or 'parts_blue' in mat:
        m.diffuse_color = (0.0, 0.4, 1.0, 1)   # bright blue for fx mesh
    elif 'fox' in mat:
        m.diffuse_color = (0.5, 0.42, 0.35, 1)
    else:
        m.diffuse_color = (0.2, 0.2, 0.2, 1)
    me.materials.append(m)
    mat_objs[mat] = ob

# ---- camera: gun sits around x 2.7-5.5, y -4..33, z -13.6..-1.9 ----
cam = bpy.data.cameras.new('cam')
camob = bpy.data.objects.new('cam', cam)
bpy.context.collection.objects.link(camob)
bpy.context.scene.camera = camob
camob.location = (30, 8, -6)
def look_at(obj, pt):
    d = obj.location - Vector(pt)
    obj.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
look_at(camob, (4, 14, -7))
cam.clip_end = 2000

sun = bpy.data.lights.new('sun', 'SUN')
sun.energy = 3
sunob = bpy.data.objects.new('sun', sun)
bpy.context.collection.objects.link(sunob)
sunob.rotation_euler = (math.radians(50), 0, math.radians(30))

pt = bpy.data.lights.new('pt', 'POINT')
pt.energy = 400
ptob = bpy.data.objects.new('pt', pt)
bpy.context.collection.objects.link(ptob)
ptob.location = (10, 15, 5)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = 1600
sc.render.resolution_y = 700
sc.render.film_transparent = False
sc.render.filepath = OUT + 'side.png'
bpy.ops.render.render(write_still=True)

# second view: top-down on the gun
camob.location = (4, 14, 25)
look_at(camob, (4, 14, -8))
sc.render.filepath = OUT + 'top.png'
bpy.ops.render.render(write_still=True)

# report fx mesh bounds
fx = groups.get('fx_galilace_parts_blue')
if fx:
    vs = fx[0]
    print('FX', min(v[0] for v in vs), max(v[0] for v in vs),
          min(v[1] for v in vs), max(v[1] for v in vs),
          min(v[2] for v in vs), max(v[2] for v in vs))
print('objects:', list(mat_objs))
print('DONE')
