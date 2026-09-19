import json
import bpy

gun = bpy.data.objects["CF_GUN_P6"]
vgs = [g.name for g in gun.vertex_groups]
arm = bpy.data.objects["CS_M4A4_Armature"]
out = {
    "vgroups": vgs,
    "n_verts": len(gun.data.vertices),
    "n_vgroups": len(vgs),
    "weapon_groups": [n for n in vgs if "M4A1" in n or "Clip" in n or "Bolt" in n or "Parent" in n],
    "arm_bone_count": len(arm.pose.bones),
    "gun_bound_box": [list(c) for c in gun.bound_box],
    "gun_dims": list(gun.dimensions),
}
path = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_gun_mesh.json"
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
