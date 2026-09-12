# P7-S04 — CF original animation decode

Result: **P7_CF_ANIM_CLIPS_DECODED**.

Nodes `57`, clips `8`, weight sets `1`.

- `reload`: 108 keys, 1600 ms, NONE, ~66.9 fps. smoke@0ms/f0, begin@15ms/f1, Extra01SoundName@30ms/f2, WeaponClipOut@194ms/f13, WeaponClipIn@718ms/f48, WeaponReload@1211ms/f81, end@1585ms/f106
- `select`: 31 keys, 640 ms, NONE, ~46.9 fps. WeaponReload@277ms/f13
- `idle_0`: 55 keys, 3000 ms, NONE, ~18.0 fps. 
- `knife-attack`: 19 keys, 666 ms, NONE, ~27.0 fps. GunKnifeSound@0ms/f0, end@33ms/f1, GunKnifeAttack@166ms/f5
- `postfire`: 13 keys, 500 ms, NONE, ~24.0 fps. fire@0ms/f0
- `run`: 10 keys, 650 ms, NONE, ~13.8 fps. 
- `fire`: 5 keys, 90 ms, NONE, ~44.4 fps. fire@0ms/f0
- `prefire`: 15 keys, 500 ms, NONE, ~28.0 fps. fire@0ms/f0

Not deployed onto the live first-person model yet (P6 mesh is still weighted to the CS M4A4 skeleton). Next: retarget these clips onto that skeleton and retime P7-S01 sound to the reload/select labels above.

Not a P4-M01 PASS. Frozen addon untouched.
