# P7-S04 current viewmodel in Blender

Result: **P7_CF_ANIM_RETARGET_FIXED_IN_BLENDER**. Not in-game. Not accepted.

The live Blender scene is `work/p5_leishen/p7_s04/blender/p7_s04_current.blend`.

Gun-driven relative retarget (not the rejected independent world-space pass):

- CF `Prop1` drives `M4A1_Parent`
- Hands keep the CS hold grip plus CF hand-vs-gun relative change
- Mag / bolt keep CF motion relative to the gun
- Wrist / finger bone lengths stay at rest (no stretch)
- Frame 0 of every clip is the P6 hold

Verified in Blender (pose bones on the deform armature):

| clip | gun–hand | wrist | mag note |
|---|---|---|---|
| idle f0 | 4.69 | 10.30 | hold |
| shoot f2 | 4.69 | 10.30 | small recoil, hands stay |
| reload f0 | 4.69 | 10.30 | same hold |
| reload f13 clipout | 4.69 | 10.30 | gun tilts, mag starts |
| reload f40 | 4.91 | 10.30 | mag is out |
| reload f81 bolt | 12.10 | 10.30 | CF's own grip change during bolt, not the old 32-unit explode |
| reload f106 | 4.44 | 10.30 | back to hold |

Old independent retarget on reload: gun–hand **3.8 → 32.5**. New: **4.2 → 12.1**.

Shots: `work/p5_leishen/p7_s04/blender/shots/side_*.png`

Switch clip: 3D View **N** → tab **P7**. Pose Position, frame 0, Space.

Still open in Blender (not a reason to compile yet):

- Sleeve ghost on the right during big motions (CS spine stays at rest; sleeve is also weighted there)
- Left hand vs mag is not a tight grab at every reload frame
- Draw camera framing is messy; look in the 3D View
- Inspect is still official CS lookat

Do not compile or deploy until the user accepts this scene.
