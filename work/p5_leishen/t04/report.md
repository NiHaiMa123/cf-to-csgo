# P5-T04 — Identity review

Result: **IDENTITY_CONFIRMED**.

Local identity is base `M4A1_S_Transformers` / `PV-M4A1_S_Transformers`. Official name is **M4A1-雷神** (item `2010044601`, `C0457.png`).

This is not P6 and not P4-M01 PASS.

## Why confirmed

| Gate | Evidence |
|---|---|
| Official 图鉴 | T01: item `2010044601`, SHA `ffa14d6a…` |
| User visual | T02: 「是雷神」 on Blender base Transformers |
| L/R | T02 mirror X −1; user 「对了」 |
| Packed Bute | T03: `rez/Butes/BF005.LTC` record 856, WeaponName `M4A1-雷神`, StandardName `M4A1_S_Transformers` |
| PV bytes | Bute `PViewModelFileName` / `PViewSkinFileName` match SHA-verified LTB `a0ccef5deed7…` and DTX `7ca69f66d229…` |
| QV bytes | Bute `ModelFileName` / `SkinFileName` match SHA-verified QV LTB/DTX |

`_PC` copies are same-bytes aliases, not a second skin.

## Explicitly not 雷神

- BornBeast / 黑骑士
- Classic, DS, FD, BB, GR/BL, and event Transformers skins
- Filename `Transformers` by itself (the Bute + user visual are what close it)

## Open, but not identity blockers

- WeaponShader CFG / TGA / `Black_Shader02.dds` are CFG Name2, not Bute fields
- Bute fire event is `ShootM4A1-S-Beast`; no `SND/WEAPON/M4A1_S_Transformers/*.WAV`
- Lobby preview in Bute is `QV-M4A1_S_IronBeast_PreView.ltb`
- English BigIconName is `M4A1-S-Iron Beast`
- LTB clip names are not fully decoded (`nParentAnims=8`)
- Source 1 import needs LTB X scale −1
- P4-M01 still INCOMPLETE; lighting deferred; N05-J stays as-is

## Next

P6 replacement is now allowed by identity, **not started**. Do not deploy over N05-J or the parked frozen addon until a separate P6 task.
