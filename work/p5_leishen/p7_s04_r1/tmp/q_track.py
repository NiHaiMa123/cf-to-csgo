import bpy, json
dg = bpy.context.evaluated_depsgraph_get()
arm = bpy.data.objects["R1A_VIEW_ARM"].evaluated_get(dg)
aw = bpy.data.objects["R1A_VIEW_ARM"].matrix_world
import json as _j
p = _j.load(open(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json", encoding="utf-8"))
idx = {n["name"]: n["index"] for n in p["nodes"]}
pairs = [
 ("FvARM-bone","v_weapon.Bip01"),("FvARM-bone Pelvis","v_weapon.Bip01_Pelvis"),
 ("FvARM-bone Spine","v_weapon.Bip01_Spine"),("FvARM-bone Spine1","v_weapon.Bip01_Spine1"),
 ("FvARM-bone Neck","v_weapon.Bip01_Neck"),
 ("FvARM-bone L Clavicle","v_weapon.Bip01_L_Clavicle"),("FvARM-bone L UpperArm","v_weapon.Bip01_L_UpperArm"),
 ("FvARM-bone L ForeArm","v_weapon.Bip01_L_Forearm"),("FvARM-bone L Hand","v_weapon.Bip01_L_Hand"),
 ("FvARM-bone R Clavicle","v_weapon.Bip01_R_Clavicle"),("FvARM-bone R UpperArm","v_weapon.Bip01_R_UpperArm"),
 ("FvARM-bone R ForeArm","v_weapon.Bip01_R_Forearm"),("FvARM-bone R Hand","v_weapon.Bip01_R_Hand"),
 ("FvARM-bone Prop1","v_weapon.M4A1_Parent"),("Bone06","v_weapon.M4A1_Clip"),("Bone04","v_weapon.M4A1_Bolt"),
]
scn = bpy.context.scene
clip = scn.r1a_source_clip; fr = scn.frame_current
samples = p["clips"][clip]["samples"]
sample = samples[min(fr, len(samples)-1)]
out = {}
for cf, cs in pairs:
    pb = arm.pose.bones.get(cs)
    if pb is None:
        out[cs] = "MISSING"; continue
    vw = (aw @ pb.matrix).translation
    cfpos = sample["pos"][idx[cf]]
    err = (vw - __import__("mathutils").Vector(cfpos)).length
    out[cs] = {"view": [round(v,2) for v in vw], "cf": [round(v,2) for v in cfpos], "err": round(err,3)}
print(json.dumps({"clip": clip, "frame": fr, "bones": out}, ensure_ascii=False, indent=1))
