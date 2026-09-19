import json
import bpy

arm = bpy.data.objects["CS_M4A4_Armature"]
arm.hide_viewport = False
arm.hide_render = True
arm.data.pose_position = "POSE"
scene = bpy.context.scene

info = {
    "objects": [o.name for o in bpy.data.objects if o.type == "ARMATURE"],
    "actions": [],
    "arm_action": None,
    "pose_position": arm.data.pose_position,
    "modifiers_gun": [m.name + ":" + m.type for m in bpy.data.objects["CF_GUN_P6"].modifiers],
    "gun_parent": bpy.data.objects["CF_GUN_P6"].parent.name if bpy.data.objects["CF_GUN_P6"].parent else None,
}

for act in bpy.data.actions:
    slots = []
    if getattr(act, "slots", None):
        slots = [s.name_display if hasattr(s, "name_display") else s.name for s in act.slots]
    nfc = len(act.fcurves)
    layered = 0
    if hasattr(act, "layers"):
        try:
            layered = sum(len(bag.fcurves) for layer in act.layers for strip in layer.strips for bag in strip.channelbags)
        except Exception as exc:
            layered = str(exc)
    info["actions"].append({
        "name": act.name,
        "users": act.users,
        "fcurves": nfc,
        "layered": layered,
        "slots": slots,
        "range": [float(act.frame_range[0]), float(act.frame_range[1])],
    })

if arm.animation_data:
    act = arm.animation_data.action
    slot = getattr(arm.animation_data, "action_slot", None)
    info["arm_action"] = {
        "action": act.name if act else None,
        "slot": (slot.name_display if slot and hasattr(slot, "name_display") else (slot.name if slot else None)),
    }

def w(name):
    return list((arm.matrix_world @ arm.pose.bones[name].matrix).to_translation())

def try_set(name, frame):
    act = bpy.data.actions.get(name)
    if act is None:
        return {"error": "missing " + name}
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = None
    bpy.context.view_layer.update()
    arm.animation_data.action = act
    assigned_slot = None
    if getattr(act, "slots", None) and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
        assigned_slot = act.slots[0].name_display if hasattr(act.slots[0], "name_display") else act.slots[0].name
    scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    return {
        "action": arm.animation_data.action.name if arm.animation_data.action else None,
        "slot": assigned_slot,
        "frame": scene.frame_current,
        "r_hand": w("v_weapon.Bip01_R_Hand"),
        "gun": w("v_weapon.M4A1_Parent"),
        "clip": w("v_weapon.M4A1_Clip"),
    }

info["idle0"] = try_set("1_idle_hold", 0)
info["reload0"] = try_set("4_reload", 0)
info["reload13"] = try_set("4_reload", 13)
info["reload81"] = try_set("4_reload", 81)
print(json.dumps(info, ensure_ascii=False))
