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
| `ShootM4A1-S-Beast (distant uses same shoot sample)` | `M4A1-S-Beast_SHOOT_1` | `Weapon_M4A4.SingleDistant` | `m4a1_distant_01.wav` | OBSERVED |
| `CF reload 喷气+退弹 together, then 上弹, then 拉栓` | `M4A1-S-Beast_GasEjection|M4A1-S-Beast_ClipOut then M4A1-S-Beast_ClipIn then M4A1-S-Beast_Reload` | `Weapon_M4A1.Clipout` | `m4a1_clipout.wav` | OBSERVED |
| `silence (do not follow CS clipin)` | `silence` | `Weapon_M4A1.Clipin` | `m4a1_clipin.wav` | SOURCE1_DESIGN_CANDIDATE |
| `silence (do not follow CS cliphit)` | `silence` | `Weapon_M4A1.ClipHit` | `m4a1_cliphit.wav` | SOURCE1_DESIGN_CANDIDATE |
| `拉栓 on 切枪 (listen 03)` | `M4A1-S-Beast_Reload` | `Weapon_M4A1.Draw` | `m4a1_draw.wav` | OBSERVED |
| `silence (kill vanilla CS bolt)` | `silence` | `Weapon_M4A1.BoltForward` | `m4a1_boltforward.wav` | SOURCE1_DESIGN_CANDIDATE |
| `silence (do not play 换弹 on 切枪)` | `silence` | `Weapon_M4A1.BoltBack` | `m4a1_boltback.wav` | SOURCE1_DESIGN_CANDIDATE |

User listen: 01-06 match filenames. 07 BeastAir is wrong. 08-13 unknown, unused.

换弹: 喷气(02) and 退弹(04) start together, then 上弹(05), then 拉栓(03). One clip on the first reload event. Clipin/ClipHit silenced. 切枪 still 拉栓(03). Fire=01. CF animation still later P7.

`BoltForward` / `BoltBack` stay silent. Qingchun / BB / Zeekr / BornBeast unused.

Not done: Inspect, CF animation, world model, knife foley, lighting.

This is not P4-M01 PASS and not release-quality audio mastering.
