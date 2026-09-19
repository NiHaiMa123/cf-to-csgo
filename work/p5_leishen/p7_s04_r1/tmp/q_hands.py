import bpy, json
from mathutils import Vector
scn = bpy.context.scene
scn.r1a_source_clip = "idle_0"; scn.frame_set(10)
bpy.context.view_layer.update()
arm = bpy.data.objects["R1A_VIEW_ARM"]
out = {}
for b in ["v_weapon.M4A1_Parent", "v_weapon.Bip01_L_Hand", "v_weapon.Bip01_R_Hand",
          "v_weapon.Bip01_L_Forearm", "v_weapon.Bip01_R_Forearm",
          "v_weapon.Bip01_L_UpperArm", "v_weapon.Bip01_R_UpperArm"]:
    pb = arm.pose.bones.get(b)
    if pb:
        h = arm.matrix_world @ pb.head
        out[b] = [round(v,2) for v in h]
print(json.dumps(out, indent=1))
