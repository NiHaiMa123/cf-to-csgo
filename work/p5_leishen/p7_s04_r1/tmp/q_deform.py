import bpy, json
cf = bpy.data.objects["R1A_CF_ANIM"]
nd = sum(1 for b in cf.data.bones if b.use_deform)
print("deform bones:", nd, "/", len(cf.data.bones))
names = [b.name for b in cf.data.bones]
print("has gun nodes:", [n for n in ["FvARM-bone Prop1","Dummy01","Bone02","Box001","Box002","Box003","Box004","Box005","Box006","Bone04","Bone06"] if n in names])
# check the reload action has fcurves for gun nodes
act = bpy.data.actions.get("R1A_CF_reload")
if act:
    fcbones = set()
    for fc in act.fcurves:
        if fc.data_path.startswith('pose.bones["'):
            fcbones.add(fc.data_path.split('"')[1])
    print("reload action keyed bones:", len(fcbones))
    print("gun nodes keyed:", sorted(fcbones & {"Dummy01","Bone02","Box001","Box002","Box003","Box004","Box005","Box006","Bone04","Bone06"}))
