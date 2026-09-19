import bpy, json
from mathutils import Vector, Quaternion, Matrix
cf = bpy.data.objects["R1A_CF_ANIM"]
p = json.load(open(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"))
names = [n["name"] for n in p["nodes"]]
clip = p["clips"]["idle_0"]; s = clip["samples"][10]
out = {}
for nm in ["FvARM-bone Prop1","Dummy01","Bone02","Box001","Bone04","Bone06","FvARM-bone L Hand"]:
    i = names.index(nm)
    pb = cf.pose.bones.get(nm)
    if not pb: out[nm] = "MISSING"; continue
    pw = (cf.matrix_world @ pb.matrix).translation
    out[nm] = {"pose": [round(v,2) for v in pw], "cf": [round(v,2) for v in s["pos"][i]],
               "err": round((pw - Vector(s["pos"][i])).length, 4)}
print(json.dumps(out, indent=1))
