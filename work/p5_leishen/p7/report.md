# P7-S01 — CF original sound (M4A1-雷神)

Result: **P7_ORIGINAL_SOUND_DEPLOYED**. P6 mesh addon `p_cf_leishen_m4a4_p6` is unchanged. Frozen addon not modified. P4-M01 remains **INCOMPLETE**.

Addon: `p_cf_leishen_m4a4_p7_sound`
Deploy: `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_leishen_m4a4_p7_sound` (created)

P6 only replaced the M4A4 viewmodel and textures. Vanilla `Weapon_M4A1.Single` still pointed at `weapons/m4a1/m4a1_01.wav`. Identity-core has no REZ WAV; Bute `ShotSoundName` is the FMOD event `ShootM4A1-S-Beast`.

Source bank: `rez/FMODStudio/Weapons/M4A1IronBeast.bank` SHA256 `5bd92625c7fecc28…`. Extractor: vgmstream. Qingchun / BB / Zeekr / BornBeast streams were not used.

Wired:

| Bute / CF | FSB stream | CS:GO event | wave | grade |
|---|---|---|---|---|
| `ShootM4A1-S-Beast` | `M4A1-S-Beast_SHOOT_1` | `Weapon_M4A1.Single` | `m4a1_01.wav`, `m4a1_02.wav` | OBSERVED |
| `ShootM4A1-S-Beast (air/tail layer)` | `M4A1SBeastAir` | `Weapon_M4A4.SingleDistant` | `m4a1_distant_01.wav` | STRONG_HYPOTHESIS |
| `ClipOutM4A1-S-Beast` | `M4A1-S-Beast_ClipOut` | `Weapon_M4A1.Clipout` | `m4a1_clipout.wav` | OBSERVED |
| `ClipInM4A1-S-Beast` | `M4A1-S-Beast_ClipIn` | `Weapon_M4A1.Clipin` | `m4a1_clipin.wav` | OBSERVED |
| `ReloadM4A1-S-Beast` | `M4A1-S-Beast_Reload` | `Weapon_M4A1.ClipHit` | `m4a1_cliphit.wav` | STRONG_HYPOTHESIS |
| `Extra01M4A1-S-IronBeast / GasEjection` | `M4A1-S-Beast_GasEjection` | `Weapon_M4A1.BoltBack` | `m4a1_boltback.wav` | HYPOTHESIS |

Close fire is the named `M4A1-S-Beast_SHOOT_1` sample only. FMOD may layer extra voices in CF; that graph was not reconstructed. `M4A1SBeastAir` is the distant layer only.

Vanilla `Weapon_M4A1.Single` has pitch 120. The close-fire WAV is pitch-compensated so in-game playback matches the CF sample.

Not done: Inspect, CF animation, world model, knife foley, lighting. Reload uses CS:GO clipout/clipin/cliphit timing, not the CF reload clip as a single one-shot.

This is not P4-M01 PASS and not release-quality audio mastering.
