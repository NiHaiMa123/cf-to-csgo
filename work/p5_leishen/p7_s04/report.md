# P7-S04 — CF original animation on the viewmodel

Result: **P7_CF_ANIM_REJECTED_IN_GAME** then **P7_CF_ANIM_IN_BLENDER**.

User 2026-09-13: in-game 完全不行，全部动作手都会变形. Automatic world-space retarget is rejected. Current viewmodel is in Blender (`work/p5_leishen/p7_s04/blender/p7_s04_current.blend`). Do not compile again until that scene is fixed and verified.

Reload / 切枪 / idle / fire use CF PV LTB clips retargeted in world space onto the P6 CS M4A4 skeleton. Sound QC events follow CF labels (`WeaponClipOut` / `ClipIn` / `WeaponReload`). P7-S01 WAV files are unchanged.

- `reload`: 108 keys, 1600 ms, NONE, ~66.9 fps. smoke@0ms/f0, begin@15ms/f1, Extra01SoundName@30ms/f2, WeaponClipOut@194ms/f13, WeaponClipIn@718ms/f48, WeaponReload@1211ms/f81, end@1585ms/f106
- `select`: 31 keys, 640 ms, NONE, ~46.9 fps. WeaponReload@277ms/f13
- `idle_0`: 55 keys, 3000 ms, NONE, ~18.0 fps. 
- `knife-attack`: 19 keys, 666 ms, NONE, ~27.0 fps. GunKnifeSound@0ms/f0, end@33ms/f1, GunKnifeAttack@166ms/f5
- `postfire`: 13 keys, 500 ms, NONE, ~24.0 fps. fire@0ms/f0
- `run`: 10 keys, 650 ms, NONE, ~13.8 fps. 
- `fire`: 5 keys, 90 ms, NONE, ~44.4 fps. fire@0ms/f0
- `prefire`: 15 keys, 500 ms, NONE, ~28.0 fps. fire@0ms/f0

- reload Clipout@f13 Clipin@f48 ClipHit@f81 fps `66.875`
- draw BoltBack@f13 fps `46.875`
- mag bone `Bone06`, bolt bone `Bone04`, gun root `FvARM-bone Prop1`
- inspect stays official CS lookat; world/dropped untouched; frozen untouched

Not a P4-M01 PASS.
