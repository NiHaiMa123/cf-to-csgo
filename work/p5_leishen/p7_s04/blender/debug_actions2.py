import json
import bpy

arm = bpy.data.objects["CS_M4A4_Armature"]
arm2 = bpy.data.objects.get("CS_M4A4_Armature.001")
gun = bpy.data.objects["CF_GUN_P6"]
mod = gun.modifiers[0]
info = {
    "gun_parent": gun.parent.name if gun.parent else None,
    "mod_object": mod.object.name if mod.object else None,
    "mod_type": mod.type,
}

def sample_action(name):
    act = bpy.data.actions[name]
    # pick a location curve
    rows = []
    curves = list(act.fcurves)
    if not curves and hasattr(act, "layers"):
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(list(bag.fcurves))
    for fc in curves:
        dp = fc.data_path
        if "Bip01_R_Hand" in dp and "location" in dp and fc.array_index == 0:
            rows.append({
                "path": dp,
                "index": fc.array_index,
                "keys": len(fc.keyframe_points),
                "v0": fc.evaluate(0),
                "v13": fc.evaluate(13),
                "v81": fc.evaluate(81),
            })
            if len(rows) >= 3:
                break
    return {"n_curves": len(curves), "samples": rows}

info["idle_curves"] = sample_action("1_idle_hold")
info["reload_curves"] = sample_action("4_reload")

def pose_both(action_name, frame):
    act = bpy.data.actions[action_name]
    out = {}
    for obj in (arm, arm2):
        if obj is None:
            continue
        obj.hide_viewport = False
        obj.data.pose_position = "POSE"
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = act
        if getattr(act, "slots", None) and act.slots:
            # try matching slot by name
            wanted = action_name
            picked = act.slots[0]
            for slot in act.slots:
                label = slot.name_display if hasattr(slot, "name_display") else slot.name
                if label in action_name or action_name.endswith(label):
                    picked = slot
            obj.animation_data.action_slot = picked
        bpy.context.scene.frame_set(int(frame))
        bpy.context.view_layer.update()
        pb = obj.pose.bones["v_weapon.Bip01_R_Hand"]
        out[obj.name] = {
            "slot": (obj.animation_data.action_slot.name_display if obj.animation_data.action_slot else None),
            "hand": list((obj.matrix_world @ pb.matrix).to_translation()),
            "pose_pos": obj.data.pose_position,
        }
    return out

info["reload13_both"] = pose_both("4_reload", 13)
info["idle0_both"] = pose_both("1_idle_hold", 0)
print(json.dumps(info, ensure_ascii=False))
