# P7-S04 current viewmodel in Blender

Result: **P7_CF_ANIM_IN_BLENDER**. Not in-game. Not accepted.

The live Blender scene is `work/p5_leishen/p7_s04/blender/p7_s04_current.blend`.

- `CF_GUN_P6`: P6 雷神 gun on the CS M4A4 57-bone armature
- `CS_GLOVE` / `CS_SLEEVE`: CS:GO bonemerge arms (same path as in-game hands)
- **Frame 0 / action `1_idle_hold` = CS hold.**
- Switch clip: select `CS_M4A4_Armature`, press **N** in the 3D View, tab **P7**, pick:
  - `1 持枪 idle`
  - `2 射击`
  - `3 切枪 draw`
  - `4 换弹 reload`
  - `5 检视 lookat`
  Then Space to play from frame 0. Blender 5 needs the Action **Slot**; the panel sets it. Action Editor dropdown alone looks frozen.

Do not compile or deploy until this scene is used to fix and verify.
