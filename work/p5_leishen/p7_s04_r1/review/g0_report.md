# P7-S04-R1-A G0 checkpoint

Status: **G0_BACKUP_READY_FOR_REVIEW**. G1 is still pending. Not ANIM_FIXED. Not user-accepted.

## What was done

Live Blender 5.2.1 LTS was queried, then the in-memory dirty scene was saved to new unique paths under `work/p5_leishen/p7_s04_r1/baseline/`. The frozen original file was not overwritten. Objects, Actions, frame, selection, and `3_draw` / `OBdraw` were left unchanged. No retarget, compile, or deploy.

## Live state (refreshed at save)

| moment | filepath | dirty | frame | FPS | action / slot |
|---|---|---|---|---|---|
| before | `.../p7_s04/blender/p7_s04_current.blend` | true | 25 | 30 | `3_draw` / `OBdraw` |
| after `copy=True` | same original path | true | 25 | 30 | `3_draw` / `OBdraw` |
| after `copy=False` | `.../p7_s04_r1/baseline/working_20260913_113051.blend` | true | 25 | 30 | `3_draw` / `OBdraw` |

`is_dirty` stayed **true** after both saves. That is the observed Blender return, not an assumption.

Topology, constraints, NLA, modifiers, and deform-rig lists: see `baseline/live_query.json` (read-only dump before save).

## New copies

- Unsaved memory backup: `D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\live_unsaved_20260913_113051.blend`
  ops=`FINISHED`, exists, size=17471964, SHA256=`3f2da3f5f3fd6fe0e06aee0123e9ce4902dd4985c42fd8e2e02daf419919597c`
- Working session: `D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend`
  ops=`FINISHED`, exists, size=17471964, SHA256=`3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1`
  Current `bpy.data.filepath` is this working path.

The backup is larger than the frozen disk blend (17471836) and has a different SHA. That is expected: it is a Save Copy of dirty memory, not a byte copy of the old file.

## Frozen inputs unchanged

All compared SHA values still match `baseline/pre_hashes.json` after the saves: original blend, draw/idle/reload/shoot1 SMD, both old retarget scripts, `cf_leishen_m4a4.smd`, and the verified PV LTB body.

## Not done

G1 source reference, quaternion study, retarget, compile, deploy, git commit/push, and edits to root `plan.md` / `task.md`.
