import bpy, bmesh
from math import radians
from mathutils import Matrix

sc = bpy.context.scene
# collect CF objects (armatures + meshes)
targets = [o for o in bpy.data.objects if o.name.startswith("CF_") or o.name.startswith("R1A_CF")]
root = bpy.data.objects.new("CF_ROOT", None)
sc.collection.objects.link(root)
for o in targets:
    if o.parent is None:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
# verified convention: X90 + Z-20 orientation fix, then world-X mirror
root.rotation_euler = (radians(90), 0.0, radians(-20))
root.scale.x = -1.0
bpy.context.view_layer.update()
# mirror -> flip winding on every CF mesh
for o in targets:
    if o.type != "MESH": continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free(); o.data.update()
print("mirrored", len(targets), "objects")

# re-frame camera on evaluated content
deps = bpy.context.evaluated_depsgraph_get()
import mathutils
lo=[1e9]*3; hi=[-1e9]*3
for o in targets:
    if o.type!="MESH" or o.hide_get(): continue
    oe=o.evaluated_get(deps)
    me=oe.to_mesh()
    mw=oe.matrix_world
    for v in me.vertices:
        w=mw @ v.co
        for i in range(3):
            lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    oe.to_mesh_clear()
print("bounds",lo,hi)
ctr=[(lo[i]+hi[i])/2 for i in range(3)]
span=max(hi[i]-lo[i] for i in range(3))
cam=bpy.data.objects.get("P5T02_Camera") or bpy.data.objects.get("Camera")
if cam is None:
    cam=bpy.data.objects.new("P5T02_Camera", bpy.data.cameras.new("P5T02_Camera"))
    sc.collection.objects.link(cam)
cam.location=(ctr[0]+span*0.9, ctr[1]-span*1.6, ctr[2]+span*0.5)
d=(mathutils.Vector(ctr)-cam.location)
cam.rotation_euler=d.to_track_quat('Z','Y').to_euler()
cam.data.clip_start=0.1; cam.data.clip_end=10000
sc.camera=cam
sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\mirrored_idle10.png"
bpy.ops.render.render(write_still=True)
print("done")
