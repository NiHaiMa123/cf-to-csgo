"""G0: Save unsaved live scene to a new copy, then switch session to a working copy.

Does not overwrite the frozen original filepath. Does not delete objects/actions.
Does not change animation, frame, or selection except as required by save_as.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import bpy

ROOT = r"D:\project\cf_to_csgo"
BASELINE = os.path.join(ROOT, "work", "p5_leishen", "p7_s04_r1", "baseline")
PRE_HASHES = os.path.join(BASELINE, "pre_hashes.json")
RESULT = os.path.join(BASELINE, "g0_save_result.json")
FROZEN_BLEND = os.path.join(ROOT, "work", "p5_leishen", "p7_s04", "blender", "p7_s04_current.blend")

FROZEN_RELS = [
    "work/p5_leishen/p7_s04/blender/p7_s04_current.blend",
    "work/p5_leishen/p7_s04/smd/draw.smd",
    "work/p5_leishen/p7_s04/smd/idle.smd",
    "work/p5_leishen/p7_s04/smd/reload.smd",
    "work/p5_leishen/p7_s04/smd/shoot1.smd",
    "scripts/p5/p5_p7_s04_cf_animation.py",
    "scripts/p5/p5_p7_s04_fix_retarget.py",
    "work/p5_leishen/p7_s04/source1/cf_leishen_m4a4.smd",
    "work/p5_leishen/p6/verified_root/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB",
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def unique_path(prefix):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BASELINE, "%s_%s.blend" % (prefix, stamp))
    if os.path.exists(path):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(BASELINE, "%s_%s.blend" % (prefix, stamp))
    return os.path.abspath(path), stamp


def action_slot(obj):
    ad = obj.animation_data if obj else None
    if ad is None:
        return None, None
    action = ad.action.name if ad.action else None
    slot = None
    if getattr(ad, "action_slot", None) is not None:
        try:
            slot = ad.action_slot.identifier
        except Exception:
            slot = str(ad.action_slot)
    return action, slot


def live_state():
    scene = bpy.context.scene
    obj = bpy.data.objects.get("CS_M4A4_Armature")
    action, slot = action_slot(obj)
    selected = [o.name for o in bpy.context.selected_objects]
    active = bpy.context.view_layer.objects.active
    return {
        "filepath": bpy.data.filepath,
        "is_dirty": bool(bpy.data.is_dirty),
        "frame": int(scene.frame_current),
        "frame_start": int(scene.frame_start),
        "frame_end": int(scene.frame_end),
        "fps": int(scene.render.fps),
        "fps_base": float(scene.render.fps_base),
        "scene": scene.name,
        "mode": bpy.context.mode,
        "selected": selected,
        "active": active.name if active else None,
        "cs_m4a4_action": action,
        "cs_m4a4_slot": slot,
        "object_names": [o.name for o in bpy.data.objects],
        "action_names": [a.name for a in bpy.data.actions],
        "object_count": len(bpy.data.objects),
        "action_count": len(bpy.data.actions),
    }


def hash_frozen():
    expected = {}
    if os.path.isfile(PRE_HASHES):
        expected = json.loads(open(PRE_HASHES, "r", encoding="utf-8").read()).get("files", {})
    out = {}
    for rel in FROZEN_RELS:
        path = os.path.join(ROOT, *rel.split("/"))
        item = {"path": path, "exists": os.path.isfile(path)}
        if item["exists"]:
            item["size"] = os.path.getsize(path)
            item["sha256"] = sha256_file(path)
        else:
            item["size"] = None
            item["sha256"] = None
        prev = expected.get(rel, {})
        item["expected_sha256"] = prev.get("sha256")
        item["sha_matches_pre_hashes"] = (
            item["sha256"] is not None
            and item["expected_sha256"] is not None
            and item["sha256"] == item["expected_sha256"]
        )
        out[rel] = item
    return out


os.makedirs(BASELINE, exist_ok=True)

before = live_state()
hashes_before = hash_frozen()
live_unsaved, stamp = unique_path("live_unsaved")
working, _ = unique_path("working")

ops_copy = bpy.ops.wm.save_as_mainfile(filepath=live_unsaved, copy=True, check_existing=False)
after_copy = live_state()
copy_exists = os.path.isfile(live_unsaved)
copy_size = os.path.getsize(live_unsaved) if copy_exists else 0
copy_sha = sha256_file(live_unsaved) if copy_exists and copy_size > 0 else None

ops_working = bpy.ops.wm.save_as_mainfile(filepath=working, copy=False, check_existing=False)
after_working = live_state()
working_exists = os.path.isfile(working)
working_size = os.path.getsize(working) if working_exists else 0
working_sha = sha256_file(working) if working_exists and working_size > 0 else None
hashes_after = hash_frozen()

frozen_unchanged = all(
    hashes_before[rel].get("sha256") == hashes_after[rel].get("sha256")
    and hashes_after[rel].get("sha_matches_pre_hashes")
    for rel in FROZEN_RELS
)

payload = {
    "captured_utc": datetime.now(timezone.utc).isoformat(),
    "blender_version": bpy.app.version_string,
    "stamp": stamp,
    "frozen_original_path": os.path.abspath(FROZEN_BLEND),
    "before": before,
    "after_copy": after_copy,
    "after_working": after_working,
    "live_unsaved": {
        "path": os.path.abspath(live_unsaved),
        "ops_result": list(ops_copy),
        "finished": "FINISHED" in set(ops_copy),
        "exists": copy_exists,
        "size": copy_size,
        "sha256": copy_sha,
        "filepath_still_original": after_copy["filepath"] == before["filepath"],
        "is_dirty_after": after_copy["is_dirty"],
    },
    "working": {
        "path": os.path.abspath(working),
        "ops_result": list(ops_working),
        "finished": "FINISHED" in set(ops_working),
        "exists": working_exists,
        "size": working_size,
        "sha256": working_sha,
        "filepath_is_working": after_working["filepath"] == os.path.abspath(working),
        "is_dirty_after": after_working["is_dirty"],
    },
    "objects_actions_preserved": (
        before["object_names"] == after_working["object_names"]
        and before["action_names"] == after_working["action_names"]
        and before["frame"] == after_working["frame"]
        and before["selected"] == after_working["selected"]
        and before["active"] == after_working["active"]
        and before["cs_m4a4_action"] == after_working["cs_m4a4_action"]
        and before["cs_m4a4_slot"] == after_working["cs_m4a4_slot"]
    ),
    "frozen_hashes_before": hashes_before,
    "frozen_hashes_after": hashes_after,
    "frozen_sha_unchanged": frozen_unchanged,
    "original_not_overwritten": (
        os.path.abspath(live_unsaved) != os.path.abspath(FROZEN_BLEND)
        and os.path.abspath(working) != os.path.abspath(FROZEN_BLEND)
        and before["filepath"] == os.path.abspath(FROZEN_BLEND)
    ),
}

with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")

print(json.dumps({
    "wrote": RESULT,
    "live_unsaved": payload["live_unsaved"]["path"],
    "copy_finished": payload["live_unsaved"]["finished"],
    "copy_size": copy_size,
    "filepath_after_copy": after_copy["filepath"],
    "working": payload["working"]["path"],
    "working_finished": payload["working"]["finished"],
    "filepath_after_working": after_working["filepath"],
    "dirty_before": before["is_dirty"],
    "dirty_after_copy": after_copy["is_dirty"],
    "dirty_after_working": after_working["is_dirty"],
    "frozen_sha_unchanged": frozen_unchanged,
    "objects_actions_preserved": payload["objects_actions_preserved"],
}, ensure_ascii=False))
