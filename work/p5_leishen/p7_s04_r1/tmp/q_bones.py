import bpy, json
anim = bpy.data.objects["R1A_CF_ANIM"]
view_arm = bpy.data.objects["R1A_VIEW_ARM"]
gun = bpy.data.objects["R1A_VIEW_GUN"]
scn = bpy.context.scene

# bone names containing prop/gun/mag/bolt-ish
names = [b.name for b in anim.data.bones]
key_bones = [n for n in names if any(k in n.lower() for k in ["prop","bone0","arm","hand","root"])]
# world pos of a few key bones at current frame
dg = bpy.context.evaluated_depsgraph_get()
ev = anim.evaluated_get(dg)
def bw(obj, bone):
    pb = obj.pose.bones.get(bone)
    if not pb: return None
    m = obj.matrix_world @ pb.matrix
    return [round(v,3) for v in m.translation]
frame = scn.frame_current
sample = {}
for b in ["FvARM-bone","FvARM-bone Prop1","Prop1","Bone06","Bone04","Bone01","Bip01","L Hand","R Hand"]:
    w = bw(ev, b)
    if w: sample[b] = w
# all bone names first 20
# gun mesh world bbox center
import mathutils
bb = [gun.matrix_world @ mathutils.Vector(c) for c in gun.bound_box]
cx = sum(v.x for v in bb)/8; cy=sum(v.y for v in bb)/8; cz=sum(v.z for v in bb)/8
# view arm bone world sample
vnames = [b.name for b in view_arm.data.bones][:10]
vw = {}
evv = view_arm.evaluated_get(dg)
for b in ["v_weapon.M4A1_Parent","v_weapon","v_weapon.Bip01","v_weapon.M4A1_Clip","v_weapon.M4A1_Bolt","v_weapon.Bip01_R_Hand","v_weapon.Bip01_L_Hand"]:
    w = bw(evv, b)
    if w: vw[b] = w
print(json.dumps({
 "frame": frame,
 "anim_action": anim.animation_data.action.name if anim.animation_data and anim.animation_data.action else None,
 "anim_bones": names,
 "key_bones": key_bones,
 "anim_bone_world": sample,
 "view_bones_sample": vnames,
 "view_bone_world": vw,
 "gun_bbox_center": [round(cx,2),round(cy,2),round(cz,2)],
}, ensure_ascii=False, indent=1))
