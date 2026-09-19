import json
import bpy

out = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_view_query.json"

def obj_info(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return None
    mods = []
    for m in obj.modifiers:
        item = {"name": m.name, "type": m.type, "show_viewport": bool(m.show_viewport)}
        if hasattr(m, "object") and m.object:
            item["object"] = m.object.name
        mods.append(item)
    mats = []
    for slot in obj.material_slots:
        mats.append(slot.material.name if slot.material else None)
    ad = obj.animation_data
    action = ad.action.name if ad and ad.action else None
    return {
        "type": obj.type,
        "hide_viewport": bool(obj.hide_viewport),
        "hide_render": bool(obj.hide_render),
        "hide_get": bool(obj.hide_get()),
        "location": list(obj.location),
        "parent": obj.parent.name if obj.parent else None,
        "users_collection": [c.name for c in obj.users_collection],
        "modifiers": mods,
        "materials": mats,
        "action": action,
        "visible_in_scene": obj.name in bpy.context.scene.objects,
    }

scene = bpy.context.scene
result = {
    "filepath": bpy.data.filepath,
    "scene": scene.name,
    "scenes": [s.name for s in bpy.data.scenes],
    "fps": scene.render.fps,
    "frame": scene.frame_current,
    "clip": getattr(scene, "r1a_source_clip", None),
    "objects_in_current": sorted(o.name for o in scene.objects),
    "all_objects": sorted(o.name for o in bpy.data.objects),
    "focus": {name: obj_info(name) for name in [
        "CF_GUN_P6", "CS_GLOVE", "CS_SLEEVE", "CS_M4A4_Armature",
        "CS_GLOVE_Armature", "CS_SLEEVE_Armature",
        "R1A_CF_ANIM", "R1A_CF_BIND", "R1A_CAM_SIDE",
    ]},
}
arm = bpy.data.objects.get("CS_M4A4_Armature")
if arm:
    names = [b.name for b in arm.pose.bones]
    result["cs_bones_sample"] = names[:20]
    result["cs_bones_weapon"] = [n for n in names if "M4A1" in n or "weapon" in n.lower()]
    for want in ("v_weapon.M4A1_Parent", "v_weapon.M4A1_Clip", "v_weapon.M4A1_Bolt",
                 "v_weapon.Bip01_R_Hand", "v_weapon.Bip01_L_Hand"):
        pb = arm.pose.bones.get(want)
        if pb:
            result.setdefault("cs_pose", {})[want] = list(pb.matrix.to_translation())

with open(out, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
