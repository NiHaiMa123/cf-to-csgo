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
| `ReloadM4A1-S-Beast (拉栓)` | `M4A1-S-Beast_Reload+M4A1_S_Reload_03` | `Weapon_M4A1.ClipHit` | `m4a1_cliphit.wav` | STRONG_HYPOTHESIS |
| `ReloadM4A1-S-Beast (拉栓 on draw)` | `M4A1-S-Beast_Reload+M4A1_S_Reload_03` | `Weapon_M4A1.Draw` | `m4a1_draw.wav` | STRONG_HYPOTHESIS |
| `silence (kill vanilla CS bolt)` | `silence` | `Weapon_M4A1.BoltForward` | `m4a1_boltforward.wav` | SOURCE1_DESIGN_CANDIDATE |
| `silence (kill GasEjection on draw)` | `silence` | `Weapon_M4A1.BoltBack` | `m4a1_boltback.wav` | SOURCE1_DESIGN_CANDIDATE |

User 2026-09-13: fire is correct; draw played a truncated reload and missed 拉栓; reload still sounded CS and should be 拉栓.

拉栓 is `M4A1-S-Beast_Reload` mixed with bank-local `M4A1_S_Reload_03`. It is wired to reload `ClipHit` and to draw via `Weapon_M4A1.Draw` (CHAN_STATIC, delayed to the bolt frames, volume-compensated). `BoltForward` / `BoltBack` are silenced so vanilla CS bolt and `GasEjection` cannot steal CHAN_ITEM or cut the bolt.

`M4A1-S-Beast_GasEjection` is a hiss, not 拉栓; it is no longer wired. Qingchun / BB / Zeekr / BornBeast unused.

Not done: Inspect, CF animation, world model, knife foley, lighting.

This is not P4-M01 PASS and not release-quality audio mastering.
