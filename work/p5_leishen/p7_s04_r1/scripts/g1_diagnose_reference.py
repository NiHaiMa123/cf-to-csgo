import json
import bpy

out = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_diag.json"
anim = bpy.data.objects.get("R1A_CF_ANIM")
bind = bpy.data.objects.get("R1A_CF_BIND")
scene = bpy.context.scene
ad = anim.animation_data if anim else None
action = ad.action if ad else None
slot = None
if ad is not None and getattr(ad, "action_slot", None) is not None:
    try:
        slot = ad.action_slot.identifier
    except Exception as exc:
        slot = str(exc)

def bone_sample(obj, names):
    rows = []
    if obj is None:
        return rows
    for name in names:
        pb = obj.pose.bones.get(name)
        if pb is None:
            rows.append({"name": name, "missing": True})
            continue
        rows.append({
            "name": name,
            "head": list(pb.head),
            "tail": list(pb.tail),
            "matrix_trans": list(pb.matrix.to_translation()),
            "length": float(pb.length),
        })
    return rows

names = [
    "Scene Root", "FvARM-bone", "FvARM-bone Prop1", "FvARM-bone L Hand",
    "FvARM-bone R Hand", "Box004", "Bone06", "Bone04",
]
result = {
    "filepath": bpy.data.filepath,
    "scene": scene.name,
    "fps": scene.render.fps,
    "frame": scene.frame_current,
    "objects": sorted(o.name for o in bpy.data.objects),
    "scenes": [s.name for s in bpy.data.scenes],
    "anim_exists": anim is not None,
    "bind_exists": bind is not None,
    "anim_hide": None if anim is None else {"viewport": bool(anim.hide_viewport), "render": bool(anim.hide_render)},
    "action": None if action is None else action.name,
    "slot": slot,
    "n_fcurves": 0 if action is None else len(action.fcurves),
    "n_pose_bones": 0 if anim is None else len(anim.pose.bones),
    "anim_bones_frame": bone_sample(anim, names),
    "bind_bones": bone_sample(bind, names),
    "cameras": {},
}
for cam_name in ("R1A_CAM_SIDE", "R1A_CAM_TOP", "R1A_CAM_FRONT"):
    cam = bpy.data.objects.get(cam_name)
    if cam:
        result["cameras"][cam_name] = {
            "location": list(cam.location),
            "rotation_euler": list(cam.rotation_euler),
        }
if action is not None and action.fcurves:
    fc = action.fcurves[0]
    result["fcurve0"] = {
        "data_path": fc.data_path,
        "array_index": fc.array_index,
        "n_keys": len(fc.keyframe_points),
        "first_last": [fc.keyframe_points[0].co[:], fc.keyframe_points[-1].co[:]] if fc.keyframe_points else None,
    }
with open(out, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
result
