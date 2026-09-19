import bpy, json
from mathutils import Matrix, Vector
arm = bpy.data.objects["R1A_VIEW_ARM"]
print("r1a_T:", arm.get("r1a_T"))
print("arm world:", arm.matrix_world)
cf = bpy.data.objects.get("R1A_CF_ANIM")
if cf:
    print("CF_ANIM world:", cf.matrix_world)
    print("CF_ANIM n bones:", len(cf.data.bones))
    b0 = cf.data.bones[0]
    print("bone0:", b0.name, "matrix_local:", [round(v,2) for v in b0.matrix_local.translation])
    for bn in ["FvARM-bone Prop1","FvARM-bone L Hand","Scene Root"]:
        bb = cf.data.bones.get(bn)
        if bb: print(bn, "rest head:", [round(v,2) for v in bb.matrix_local.translation])
