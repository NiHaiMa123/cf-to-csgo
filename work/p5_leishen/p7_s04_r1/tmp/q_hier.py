import bpy, json
view_arm = bpy.data.objects["R1A_VIEW_ARM"]
gun = bpy.data.objects["R1A_VIEW_GUN"]
# hierarchy of weapon bones
hier = {}
for b in view_arm.data.bones:
    hier[b.name] = b.parent.name if b.parent else None
# which bones have weights in gun mesh
weighted = {}
for v in gun.data.vertices:
    for g in v.groups:
        weighted[g.group] = weighted.get(g.group, 0) + 1
vg_names = {i: g.name for i, g in enumerate(gun.vertex_groups)}
weighted_named = {vg_names[k]: c for k, c in weighted.items()}
# text blocks (clip switcher script?)
texts = [t.name for t in bpy.data.texts]
# scene frame range
scn = bpy.context.scene
print(json.dumps({
 "weapon_bone_hier": {k:v for k,v in hier.items() if "M4A1" in k or k=="v_weapon"},
 "gun_vertex_groups": weighted_named,
 "texts": texts,
 "frame_start": scn.frame_start, "frame_end": scn.frame_end,
}, ensure_ascii=False, indent=1))
