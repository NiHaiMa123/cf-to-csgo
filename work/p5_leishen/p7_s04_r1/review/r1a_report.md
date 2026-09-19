# P7-S04-R1-A G1 report

Status: **SOURCE_REFERENCE_READY_FOR_REVIEW**. Not ANIM_FIXED. Not user-accepted. G2 is not open.

## What this is

A source-only CF skeleton reference on a new blend, with a real millisecond timeline. It is the missing G1 overlay after Planner rejected the v1 audit method. Old rejected P7-S04 files were not overwritten.

## Convention used (not auto-picked)

- Quaternion file order **xyzw**
- Translation in **column 3**
- World = **parent @ local**
- Bind matrices are row-major 4×4 with last row `0001`

Taken from public LithTech SDK (`LTRotation`, `TransformMaker`) plus local affine checks. The public mirror is **not** the current CF runtime. `interpolation_ms` is 0 on these clips and is not treated as a runtime rule.

v1 `source_audit.json` is kept as failed-method evidence. v3 does **not** rank conventions by bind-vs-clip0, does **not** force bind = clip0, and does **not** add pelvis/root compensation.

## Numeric checks that passed

| Check | Result |
|---|---|
| Body SHA / 57 nodes / 8 clips / flags=0 | match existing P6 input |
| Every keyframe world vs `cf_worlds` | max abs 5.3e-15 |
| Planner raw-vs-unit world delta | reload 0.04845 @ key96 `L Finger12`; select 3.59e-5; idle 3.35e-5 |
| reload L Hand key96 raw R | det 0.9276306731, RᵀR err 0.0723688076; angles only on unit/polar rotations |
| select gun first vs idle | 4.98188 CF units (entry motion kept) |
| select/reload last vs idle | position < 1e-4 for gun and both hands |
| reload0 parent-relative pos vs bind | 53/57 match; gun subtree 11/11 world pos. Recorded, **not** a decoder gate |
| Diagnostic sampler at source keys | matches unit composition |
| Component-LINEAR vs SLERP at midpoints | < 3e-6 deg on this file; still not claimed equivalent |

Visible mesh gun at select 0ms and 640ms matches the sampler to 0 Source/CF units.

## Visible reference

File: `work/p5_leishen/p7_s04_r1/source/source_reference.blend`

- Scene `CF_SOURCE_REFERENCE` at **100 FPS**, `frame = time_ms / 10`
- Orange `R1A_ANIM_*` joints/sticks = diagnostic sampler (linear pos, unit shortest-arc SLERP)
- Cyan `R1A_BIND_*` = static `node.matrix`; **not** compensated onto clip0
- RGB axes on `Prop1` / `Bone06` / `Bone04`
- N-panel **R1A** switches clips
- Original CS scene is still in the same file
- `SKELETON_ONLY_REFERENCE`: no LTB weights / inverse bind

Fixed cameras: `R1A_CAM_SIDE` / `_TOP` / `_FRONT`. Stills in `source/shots/`. Slow (4×) videos: `select_side_100fps.mp4`, `reload_side_100fps.mp4`.

First armature `pose.matrix` bake was **not** used for display: child bones (e.g. `Box004`) drifted. Joint meshes are driven from sampler world translations.

## Protected

Working copy `baseline/working_20260913_113051.blend` SHA unchanged. Frozen old blend/SMD/scripts/LTB hashes unchanged. No compile, no deploy.

## Open / not claimed

- CF runtime interpolator still OPEN
- 100 FPS is diagnostic, not native sampling
- No skinned CF hands
- G2 control rig / contact / IK not started
- Old in-game and Blender retargets remain REJECTED
