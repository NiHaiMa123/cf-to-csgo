import bpy, json
dg = bpy.context.evaluated_depsgraph_get()
def wbbox(name):
    o = bpy.data.objects[name].evaluated_get(dg)
    me = o.to_mesh()
    from mathutils import Vector
    ws = [o.matrix_world @ v.co for v in me.vertices]
    xs=[v.x for v in ws]; ys=[v.y for v in ws]; zs=[v.z for v in ws]
    o.to_mesh_clear()
    return {"min":[round(min(xs),1),round(min(ys),1),round(min(zs),1)],
            "max":[round(max(xs),1),round(max(ys),1),round(max(zs),1)],
            "cx": round((min(xs)+max(xs))/2,1), "cy": round((min(ys)+max(ys))/2,1), "cz": round((min(zs)+max(zs))/2,1),
            "sx": round(max(xs)-min(xs),1), "sy": round(max(ys)-min(ys),1), "sz": round(max(zs)-min(zs),1)}
out = {}
for n in ["R1A_VIEW_GUN","R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    try: out[n] = wbbox(n)
    except Exception as e: out[n] = str(e)
# hand bones world (evaluated)
arm = bpy.data.objects["R1A_VIEW_ARM"].evaluated_get(dg)
aw = arm.matrix_world
for b in ["v_weapon.Bip01_R_Hand","v_weapon.Bip01_L_Hand","v_weapon.Bip01_R_Forearm","v_weapon.Bip01_L_Forearm","v_weapon.Bip01_R_UpperArm","v_weapon.Bip01_L_UpperArm"]:
    pb = arm.pose.bones.get(b)
    out[b] = [round(v,2) for v in (aw @ pb.matrix).translation] if pb else None
# glove/sleeve armature bone check: do their bones match view arm worlds?
ga = bpy.data.objects["R1A_VIEW_GLOVE_ARM"].evaluated_get(dg)
gaw = ga.matrix_world
pb = ga.pose.bones.get("v_weapon.Bip01_R_Hand")
out["glove_R_Hand_world"] = [round(v,2) for v in (gaw @ pb.matrix).translation] if pb else None
pb = ga.pose.bones.get("v_weapon.Bip01_L_Hand")
out["glove_L_Hand_world"] = [round(v,2) for v in (gaw @ pb.matrix).translation] if pb else None
print(json.dumps(out, ensure_ascii=False, indent=1))
