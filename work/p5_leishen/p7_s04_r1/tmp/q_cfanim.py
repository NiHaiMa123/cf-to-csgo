import bpy, json
from mathutils import Vector
cf = bpy.data.objects["R1A_CF_ANIM"]
scn = bpy.context.scene
print("actions:", [a.name for a in bpy.data.actions if "CF" in a.name or "R1A" in a.name][:15])
print("cf anim action:", cf.animation_data.action.name if cf.animation_data and cf.animation_data.action else None)
print("scene clip prop:", getattr(scn, "r1a_clip", None), "| r1a_source_clip:", getattr(scn, "r1a_source_clip", None))
# pose check: does a pose bone world == CF pos? try current frame
pb = cf.pose.bones["FvARM-bone Prop1"]
w = cf.matrix_world @ pb.matrix.translation
print("Prop1 pose world:", [round(v,2) for v in w])
pb2 = cf.pose.bones["FvARM-bone L Hand"]
w2 = cf.matrix_world @ pb2.matrix.translation
print("L_Hand pose world:", [round(v,2) for v in w2])
# payload reference
import json as j
p = j.load(open(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"))
names = [n["name"] for n in p["nodes"]]
clip = p["clips"]["idle_0"]
s = clip["samples"][10]
i = names.index("FvARM-bone Prop1")
print("payload Prop1 idle f10:", [round(v,2) for v in s["pos"][i]])
i2 = names.index("FvARM-bone L Hand")
print("payload L_Hand idle f10:", [round(v,2) for v in s["pos"][i2]])
