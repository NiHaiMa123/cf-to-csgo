# Blender 5.x — build GALILACE_PREVIEW: CF-native GalilACE_PhantomBeast preview.
# Runs inside the live Blender via blender_mcp_exec execute_code.
# Creates prefixed objects only; does NOT touch existing scene objects;
# saves via wm.save_copy (current file untouched).
import bpy, json, math, os
from mathutils import Matrix, Quaternion, Vector

REPO = r"D:\project\cf_to_csgo"
WORK = REPO + r"\work\galil_ace_tianxi"
PAYLOAD = WORK + r"\decode\reference_payload.json"
SKIN = WORK + r"\decode\cf_skin_galilace.json"
GUNTEX = WORK + r"\decode\PV-GalilACE_PhantomBeast.png"
BLEND_OUT = WORK + r"\preview\cf_native_preview_galilace.blend"
SHOT_DIR = WORK + r"\preview\shots"
os.makedirs(SHOT_DIR, exist_ok=True)

p = json.load(open(PAYLOAD, "r", encoding="utf-8"))
sk = json.load(open(SKIN, "r", encoding="utf-8"))
pnodes = p["nodes"]
parents = [n["parent"] for n in pnodes]
bindw = [Matrix(n["bind_world"]) for n in pnodes]
bindwi = [m.inverted() for m in bindw]

PIECE_NODE = {  # optimal mean-distance bijection (p1 decode)
    "Body": 46, "Mag": 49, "Core01": 55, "Core02": 53, "Core03": 54,
    "Object489": 50, "Object490": 51, "Object491": 52,
    "Stock": 47, "Object492": 48,
}

def q2m(q):
    return Quaternion((q[3], q[0], q[1], q[2])).to_matrix().to_4x4()

# ---------- cleanup previous run ----------
for nm in ["GALIL_ROOT", "GALIL_ARM"]:
    o = bpy.data.objects.get(nm)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if o.name.startswith("GA_"):
        bpy.data.objects.remove(o, do_unlink=True)
for a_ in list(bpy.data.actions):
    if a_.name.startswith("GA_"):
        bpy.data.actions.remove(a_)
col = bpy.data.collections.get("GALILACE_PREVIEW") or bpy.data.collections.new("GALILACE_PREVIEW")
if col.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(col)

# ---------- armature ----------
arm_data = bpy.data.armatures.new("GALIL_ARM")
arm = bpy.data.objects.new("GALIL_ARM", arm_data)
col.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
order = []
def walk(i):
    order.append(i)
    for j, pn in enumerate(parents):
        if pn == i:
            walk(j)
for i in range(len(pnodes)):
    if parents[i] < 0:
        walk(i)
eb = {}
for i in order:
    n = pnodes[i]
    b = arm_data.edit_bones.new(n["name"])
    head = Vector((bindw[i][0][3], bindw[i][1][3], bindw[i][2][3]))
    kids = n["children"]
    if kids:
        tail = Vector((bindw[kids[0]][0][3], bindw[kids[0]][1][3], bindw[kids[0]][2][3]))
    else:
        tail = head + Vector((0, 0.6, 0))
    if (tail - head).length < 0.05:
        tail = head + Vector((0, 0.6, 0))
    b.head = head
    b.tail = tail
    eb[i] = b
for i in order:
    if parents[i] >= 0:
        eb[i].parent = eb[parents[i]]
bpy.ops.object.mode_set(mode="OBJECT")
ML = {b.name: b.matrix_local.copy() for b in arm.data.bones}
MLI = {n: m.inverted() for n, m in ML.items()}

# ---------- meshes ----------
def build_mesh(mname, rec):
    me = bpy.data.meshes.new(mname)
    nv = rec["vertex_count"]
    verts = rec["vertices"]
    tris = rec["triangles"]
    me.from_pydata([tuple(verts[i*3:i*3+3]) for i in range(nv)], [],
                   [tuple(tris[i:i+3]) for i in range(0, len(tris), 3)])
    me.update()
    ob = bpy.data.objects.new(mname, me)
    col.objects.link(ob)
    if rec.get("uvs"):
        uv = me.uv_layers.new(name="UVMap")
        uvd = rec["uvs"]
        for li, lp in enumerate(me.loops):
            vi = lp.vertex_index
            uv.data[li].uv = (uvd[2*vi], 1.0 - uvd[2*vi+1])
    return ob, me

gun_meshes = []
skin_meshes = []
for rec in sk["meshes"]:
    ob, me = build_mesh("GA_" + rec["name"], rec)
    if rec["name"] in PIECE_NODE:
        ni = PIECE_NODE[rec["name"]]
        bn = pnodes[ni]["name"]
        g = ob.vertex_groups.new(name=bn)
        g.add(list(range(rec["vertex_count"])), 1.0, 'REPLACE')
        gun_meshes.append(ob)
    else:
        bw = rec["bone_weights"]; bi = rec["bone_indices"]
        anames = [n["name"] for n in sk["skeleton"]]
        groups = {}
        for vi in range(rec["vertex_count"]):
            ids = bi[4*vi:4*vi+4]
            w0, w1, w2 = bw[3*vi:3*vi+3]
            w3 = max(0.0, 1.0-w0-w1-w2)
            for nii, w in zip(ids, (w0, w1, w2, w3)):
                if nii == 255 or nii >= len(anames) or w <= 1e-6:
                    continue
                bn = anames[nii]
                gp = groups.get(bn)
                if gp is None:
                    gp = groups[bn] = ob.vertex_groups.new(name=bn)
                gp.add([vi], w, 'REPLACE')
        skin_meshes.append(ob)
    mod = ob.modifiers.new("arm", "ARMATURE")
    mod.object = arm

# flip winding for the X-mirror at root (keeps normals outward)
import bmesh
for ob in gun_meshes + skin_meshes:
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()

# ---------- root mirror ----------
root = bpy.data.objects.new("GALIL_ROOT", None)
col.objects.link(root)
root.scale.x = -1.0
root.rotation_euler = (math.radians(90), 0, math.radians(-20))
for o in [arm] + gun_meshes + skin_meshes:
    o.parent = root

# ---------- texture ----------
img = bpy.data.images.load(GUNTEX)
mat = bpy.data.materials.new("GA_gun")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.45
bsdf.inputs["Metallic"].default_value = 0.35
for ob in gun_meshes:
    ob.data.materials.append(mat)
mat2 = bpy.data.materials.new("GA_arm")
mat2.use_nodes = True
mat2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.28, 0.22, 0.18, 1)
for ob in skin_meshes:
    ob.data.materials.append(mat2)

# ---------- bake clips ----------
name2idx = {n["name"]: i for i, n in enumerate(pnodes)}
bname_of = {i: pnodes[i]["name"] for i in range(len(pnodes))}
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'

def bake(clip_name):
    samples = p["clips"][clip_name]["samples"]
    act = bpy.data.actions.new("GA_" + clip_name)
    fcs = {}
    for bn in ML:
        for k in range(3):
            fcs[(bn, "l", k)] = act.fcurves.new('pose.bones["%s"].location' % bn, index=k)
        for k in range(4):
            fcs[(bn, "q", k)] = act.fcurves.new('pose.bones["%s"].rotation_quaternion' % bn, index=k)
    nfr = len(samples)
    for fc in fcs.values():
        fc.keyframe_points.add(nfr)
    prevq = {bn: None for bn in ML}
    pts = {k: [0.0]*(2*nfr) for k in fcs}
    for fi, s in enumerate(samples):
        fnum = int(round(s.get("frame_100", fi)))
        D = {}
        for i in order:
            A = q2m(s["quat_xyzw_world"][i]); A.translation = s["pos"][i]
            D[bname_of[i]] = A @ bindwi[i] @ ML[bname_of[i]]
        for i in order:
            bn = bname_of[i]
            pi = parents[i]
            if pi < 0:
                basis = MLI[bn] @ D[bn]
            else:
                basis = MLI[bn] @ ML[bname_of[pi]] @ D[bname_of[pi]].inverted() @ D[bn]
            loc = basis.to_translation(); q = basis.to_quaternion()
            if prevq[bn] is not None and prevq[bn].dot(q) < 0:
                q.negate()
            prevq[bn] = q.copy()
            for k in range(3):
                pts[(bn, "l", k)][2*fi] = fnum; pts[(bn, "l", k)][2*fi+1] = loc[k]
            for k in range(4):
                pts[(bn, "q", k)][2*fi] = fnum; pts[(bn, "q", k)][2*fi+1] = q[k]
    for k, fc in fcs.items():
        fc.keyframe_points.foreach_set('co', pts[k])
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()
    return nfr

results = {}
for cn in ["idle_0", "select", "reload", "observe", "fire"]:
    if cn in p["clips"]:
        results[cn] = bake(cn)
        print("baked", cn, results[cn])

arm.animation_data_create()
act = bpy.data.actions["GA_idle_0"]
arm.animation_data.action = act
arm.animation_data.action_slot = act.slots[0]

# ---------- light + camera ----------
w = bpy.data.worlds.new("GA_W") if not bpy.data.worlds.get("GA_W") else bpy.data.worlds["GA_W"]
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.4, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
bpy.context.scene.world = w
sun = bpy.data.objects.new("GA_SUN", bpy.data.lights.new("GA_SUN", 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
col.objects.link(sun)

cam = bpy.data.objects.new("GA_CAM", bpy.data.cameras.new("GA_CAM"))
col.objects.link(cam)
bpy.context.scene.camera = cam
def aim(cam, pos, target):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# gun sits near origin after root xform; compute its world bbox center
bpy.context.view_layer.update()
allv = []
for ob in gun_meshes:
    for v in ob.bound_box:
        allv.append(ob.matrix_world @ Vector(v))
ctr = sum(allv, Vector()) / len(allv)
print("gun world center", tuple(round(c, 2) for c in ctr))

scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE_NEXT'
scn.render.resolution_x = 900
scn.render.resolution_y = 700
scn.render.fps = 100

def shot(name, campos, frame):
    aim(cam, campos, ctr)
    scn.frame_set(frame)
    scn.render.filepath = os.path.join(SHOT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("shot", name)

# select a frame inside each clip's range for review
shot("idle_f10_side", (ctr.x + 12, ctr.y - 6, ctr.z + 3), 10)
shot("idle_f10_front", (ctr.x + 2, ctr.y - 14, ctr.z + 4), 10)
arm.animation_data.action = bpy.data.actions["GA_reload"]
arm.animation_data.action_slot = bpy.data.actions["GA_reload"].slots[0]
shot("reload_f50_side", (ctr.x + 12, ctr.y - 6, ctr.z + 3), 50)
shot("reload_f100_front", (ctr.x + 2, ctr.y - 14, ctr.z + 4), 100)
arm.animation_data.action = bpy.data.actions["GA_observe"]
arm.animation_data.action_slot = bpy.data.actions["GA_observe"].slots[0]
shot("observe_f200_side", (ctr.x + 12, ctr.y - 6, ctr.z + 3), 200)
arm.animation_data.action = bpy.data.actions["GA_select"]
arm.animation_data.action_slot = bpy.data.actions["GA_select"].slots[0]
shot("select_f30_front", (ctr.x + 2, ctr.y - 14, ctr.z + 4), 30)
arm.animation_data.action = bpy.data.actions["GA_idle_0"]
arm.animation_data.action_slot = bpy.data.actions["GA_idle_0"].slots[0]

bpy.ops.wm.save_copy(filepath=BLEND_OUT)
print("SAVED", BLEND_OUT)
print("DONE", json.dumps(results))
