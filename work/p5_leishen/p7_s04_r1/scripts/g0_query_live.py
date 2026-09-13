"""G0 step 1: read-only dump of the live Blender session. Does not save or mutate."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import bpy

OUT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\live_query.json"


def mat4(m):
    return [[float(m[i][j]) for j in range(4)] for i in range(4)]


def bone_info(pose_bone):
    parent = pose_bone.parent.name if pose_bone.parent else None
    constraints = []
    for c in pose_bone.constraints:
        item = {
            "name": c.name,
            "type": c.type,
            "mute": bool(c.mute),
            "influence": float(getattr(c, "influence", 1.0)),
        }
        if hasattr(c, "target") and c.target:
            item["target"] = c.target.name
        if hasattr(c, "subtarget"):
            item["subtarget"] = c.subtarget
        if hasattr(c, "chain_count"):
            item["chain_count"] = int(c.chain_count)
        if hasattr(c, "use_stretch"):
            item["use_stretch"] = bool(c.use_stretch)
        constraints.append(item)
    return {
        "name": pose_bone.name,
        "parent": parent,
        "constraints": constraints,
        "head": list(pose_bone.head),
        "tail": list(pose_bone.tail),
        "length": float(pose_bone.length),
    }


def action_slot(obj):
    ad = obj.animation_data
    if ad is None:
        return {"action": None, "action_slot": None, "nla_tracks": []}
    slot = None
    if getattr(ad, "action_slot", None) is not None:
        try:
            slot = ad.action_slot.identifier
        except Exception:
            slot = str(ad.action_slot)
    tracks = []
    for track in ad.nla_tracks:
        strips = []
        for strip in track.strips:
            strips.append({
                "name": strip.name,
                "action": strip.action.name if strip.action else None,
                "frame_start": float(strip.frame_start),
                "frame_end": float(strip.frame_end),
                "mute": bool(strip.mute),
            })
        tracks.append({"name": track.name, "mute": bool(track.mute), "strips": strips})
    return {
        "action": ad.action.name if ad.action else None,
        "action_slot": slot,
        "nla_tracks": tracks,
    }


def mesh_deform(obj):
    mods = []
    unique = []
    for mod in obj.modifiers:
        item = {"name": mod.name, "type": mod.type, "show_viewport": bool(mod.show_viewport)}
        if mod.type == "ARMATURE" and getattr(mod, "object", None):
            item["object"] = mod.object.name
            unique.append(mod.object.name)
        mods.append(item)
    return mods, sorted(set(unique))


scene = bpy.context.scene
view = bpy.context.scene.view_layers[0] if bpy.context.scene.view_layers else None
selected = [o.name for o in bpy.context.selected_objects]
active = bpy.context.view_layer.objects.active
screen = bpy.context.screen

objects = []
for obj in bpy.data.objects:
    mods, deform = mesh_deform(obj)
    item = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "collection": [c.name for c in obj.users_collection],
        "hidden": bool(obj.hide_get()),
        "hide_viewport": bool(obj.hide_viewport),
        "hide_render": bool(obj.hide_render),
        "matrix_world": mat4(obj.matrix_world),
        "modifiers": mods,
        "deform_rigs": deform,
        **action_slot(obj),
    }
    if obj.type == "ARMATURE":
        item["pose_position"] = obj.data.pose_position
        item["bones"] = [bone_info(pb) for pb in obj.pose.bones]
        item["bone_count"] = len(obj.pose.bones)
        roots = [b.name for b in obj.data.bones if b.parent is None]
        item["root_bones"] = roots
    objects.append(item)

actions = []
for act in bpy.data.actions:
    slots = []
    if hasattr(act, "slots"):
        for sl in act.slots:
            ident = getattr(sl, "identifier", None) or sl.name
            slots.append(ident)
    actions.append({
        "name": act.name,
        "slots": slots,
        "fcurves": len(act.fcurves) if hasattr(act, "fcurves") else None,
        "frame_range": [float(act.frame_range[0]), float(act.frame_range[1])],
    })

result = {
    "captured_utc": datetime.now(timezone.utc).isoformat(),
    "blender_version": bpy.app.version_string,
    "filepath": bpy.data.filepath,
    "is_dirty": bool(bpy.data.is_dirty),
    "scene": scene.name,
    "scenes": [s.name for s in bpy.data.scenes],
    "frame": int(scene.frame_current),
    "frame_float": float(getattr(scene, "frame_current_final", scene.frame_current)),
    "frame_range": [int(scene.frame_start), int(scene.frame_end)],
    "fps": int(scene.render.fps),
    "fps_base": float(scene.render.fps_base),
    "scene_clip": scene.get("p7_clip") if hasattr(scene, "get") else None,
    "mode": bpy.context.mode,
    "selected": selected,
    "active": active.name if active else None,
    "is_animation_playing": bool(getattr(screen, "is_animation_playing", False)) if screen else None,
    "objects": objects,
    "actions": actions,
    "collections": [c.name for c in bpy.data.collections],
}

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")

print(json.dumps({
    "wrote": OUT,
    "filepath": result["filepath"],
    "is_dirty": result["is_dirty"],
    "frame": result["frame"],
    "fps": result["fps"],
    "version": result["blender_version"],
    "object_count": len(objects),
    "action_count": len(actions),
    "selected": selected,
    "active": result["active"],
    "playing": result["is_animation_playing"],
}, ensure_ascii=False))
