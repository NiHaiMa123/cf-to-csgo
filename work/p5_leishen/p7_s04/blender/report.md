# P7-S04 current viewmodel in Blender

Result: **P7_CF_ANIM_IN_BLENDER**. Not in-game. Not accepted.

The live Blender scene is `work/p5_leishen/p7_s04/blender/p7_s04_current.blend`.

- `CF_GUN_P6`: P6 雷神 gun on the CS M4A4 57-bone armature
- `CS_GLOVE` / `CS_SLEEVE`: CS:GO bonemerge arms (same path as in-game hands)
- **Frame 0 / action `1_idle_hold` = CS hold.**
- Switch clip in **Dope Sheet → Action Editor** (or NLA), armature selected, pick:
  - `1_idle_hold`
  - `2_shoot`
  - `3_draw`
  - `4_reload`
  - `5_lookat`
- Pose Position, not Rest Position. Glove/sleeve Copy Transforms follow the weapon bones.

Do not compile or deploy until this scene is used to fix and verify.
