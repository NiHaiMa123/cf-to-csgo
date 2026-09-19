import bpy, json, math
from mathutils import Matrix, Quaternion, Vector

PAYLOAD = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"
ARMDUMP = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\cf_skin_foxhowl_renewal_bl.json"
p = json.load(open(PAYLOAD,"r",encoding="utf-8"))
a = json.load(open(ARMDUMP,"r",encoding="utf-8"))
pnodes = p["nodes"]; nidx = {n["name"]:i for i,n in enumerate(pnodes)}
parents = [n["parent"] for n in pnodes]
anames = [n["name"] for n in a["skeleton"]]

def _m16(flat):
    return Matrix((flat[0:4], flat[4:8], flat[8:12], flat[12:16]))

abind = {n["name"]: _m16(n["bind_matrix"]) for n in a["skeleton"]}
AINV = {n: B.inverted() for n,B in abind.items()}

def q2m(q):
    return Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4()

order=[]
def walk(i):
    order.append(i)
    for j,pn in enumerate(parents):
        if pn==i: walk(j)
for i in range(len(pnodes)):
    if parents[i]<0: walk(i)

src = bpy.data.objects["R1A_CF_ANIM"]
old = bpy.data.objects.get("R1A_CF_DEFORM_ARMS")
if old: bpy.data.objects.remove(old, do_unlink=True)
darms = src.copy()
darms.name = "R1A_CF_DEFORM_ARMS"
darms.matrix_world = Matrix.Identity(4)
darms.animation_data_clear()
darms.hide_set(False); darms.hide_render=True
src.users_collection[0].objects.link(darms)
for pb in darms.pose.bones: pb.rotation_mode='QUATERNION'

ML = {b.name: b.matrix_local.copy() for b in darms.data.bones}
MLI = {n:m.inverted() for n,m in ML.items()}
bname_of = {i: pnodes[i]["name"] for i in range(len(pnodes))}

for act in list(bpy.data.actions):
    if act.name.startswith("R1A_CFDA_"): bpy.data.actions.remove(act)

def bake(clip_name):
    samples = p["clips"][clip_name]["samples"]
    act = bpy.data.actions.new("R1A_CFDA_"+clip_name)
    fcs={}
    for bn in ML:
        if bn not in abind: continue
        for k in range(3): fcs[(bn,"l",k)] = act.fcurves.new('pose.bones["%s"].location'%bn,index=k)
        for k in range(4): fcs[(bn,"q",k)] = act.fcurves.new('pose.bones["%s"].rotation_quaternion'%bn,index=k)
    nfr=len(samples)
    for fc in fcs.values(): fc.keyframe_points.add(nfr)
    prevq={bn:None for bn in abind}
    pts={k:[0.0]*(2*nfr) for k in fcs}
    for fi,s in enumerate(samples):
        fnum=int(round(s.get("frame_100",fi)))
        D={}
        for bn in abind:
            i=nidx[bn]
            A=q2m(s["quat_xyzw_world"][i]); A.translation=s["pos"][i]
            D[bn]=A@AINV[bn]@ML[bn]
        for i in order:
            bn=bname_of[i]
            if bn not in abind: continue
            pi=parents[i]
            if pi<0 or bname_of[pi] not in abind:
                basis = MLI[bn] @ D[bn]
            else:
                basis = MLI[bn] @ ML[bname_of[pi]] @ D[bname_of[pi]].inverted() @ D[bn]
            loc=basis.to_translation(); q=basis.to_quaternion()
            if prevq[bn] is not None and prevq[bn].dot(q)<0: q.negate()
            prevq[bn]=q.copy()
            for k in range(3):
                pts[(bn,"l",k)][2*fi]=fnum; pts[(bn,"l",k)][2*fi+1]=loc[k]
            for k in range(4):
                pts[(bn,"q",k)][2*fi]=fnum; pts[(bn,"q",k)][2*fi+1]=q[k]
    for k,fc in fcs.items():
        arr=pts[k]
        for j,kp in enumerate(fc.keyframe_points):
            kp.co=(arr[2*j],arr[2*j+1]); kp.interpolation='LINEAR'
        fc.update()
    return nfr

res={}
for cn in ["idle_0","select","reload","fire","prefire","postfire","run","knife-attack"]:
    res[cn]=bake(cn); print("baked arms",cn,res[cn])

col = bpy.data.collections.get("CF_NATIVE")
for o in list(bpy.data.objects):
    if o.name.startswith("CF_FVIEW_"):
        bpy.data.objects.remove(o, do_unlink=True)
def build_mesh(mname, rec):
    me = bpy.data.meshes.new(mname)
    nv = rec["vertex_count"]
    verts = rec["vertices"]; tris = rec["triangles"]
    faces=[tuple(tris[i:i+3]) for i in range(0,len(tris),3)]
    me.from_pydata([tuple(verts[i*3:i*3+3]) for i in range(nv)],[],faces)
    me.update()
    ob = bpy.data.objects.new(mname, me)
    col.objects.link(ob)
    if rec.get("uvs"):
        uv = me.uv_layers.new(name="UVMap")
        uvdata=rec["uvs"]
        for li,loop in enumerate(me.loops):
            vi=loop.vertex_index
            uv.data[li].uv = (uvdata[2*vi], 1.0-uvdata[2*vi+1])
    bw=rec["bone_weights"]; bi=rec["bone_indices"]
    groups={}
    for vi in range(nv):
        ids=bi[4*vi:4*vi+4]; w0,w1,w2=bw[3*vi:3*vi+3]
        w3=max(0.0,1.0-w0-w1-w2)
        for ni,w in zip(ids,(w0,w1,w2,w3)):
            if ni==255 or ni>=len(anames) or w<=1e-6: continue
            bn=anames[ni]
            g=groups.get(bn)
            if g is None: g=groups[bn]=ob.vertex_groups.new(name=bn)
            g.add([vi], w, 'REPLACE')
    mod=ob.modifiers.new("arm","ARMATURE"); mod.object=darms
    return ob

for rec in a["meshes"]:
    ob = build_mesh("CF_"+rec["name"], rec)
    print("built",ob.name,rec["vertex_count"],"v")

for nm in ("CF_Fview-hand2","CF_Fview-arm2"):
    o=bpy.data.objects.get(nm)
    if o:
        try: o.hide_set(True); o.hide_render=True
        except Exception: pass

darms.animation_data_create()
act=bpy.data.actions["R1A_CFDA_idle_0"]
darms.animation_data.action=act; darms.animation_data.action_slot=act.slots[0]
darms.hide_set(True)
print("DONE",json.dumps(res))
