# P7-S04 current viewmodel in Blender

Result: **P7_CF_ANIM_IN_BLENDER**. Not in-game. Not accepted.

The live Blender scene is `work/p5_leishen/p7_s04/blender/p7_s04_current.blend`.

- `CF_GUN_P6`: P6 雷神 gun on the CS M4A4 57-bone armature
- `CS_GLOVE` / `CS_SLEEVE`: CS:GO bonemerge arms (same path as in-game hands)
- Action `P7S04_CURRENT` slots: `idle` `shoot1` `draw` `reload` `lookat01`
- **Frame 0 / slot `idle` = CS hold.** Glove/sleeve use their own bind armature and Copy Transforms onto the weapon bones (game bonemerge). Do not use Armature Rest Position; that is `$definebone`, not the hold.

Switch clip: Action Editor → action `P7S04_CURRENT` → Slot.

Do not compile or deploy until this scene is used to fix and verify.
