# P4-M01-N03-F — WeaponShader / AlphaMap exact-path lookup

- status: **CANDIDATE_ONLY**
- confidence: **MEDIUM**
- script: `scripts/material_recovery/n03f_shader_alphamap_lookup.py`
- packed BF005 records: 8205
- elapsed: 11.89s

Tokens **exclude** the StandardName stem `M4A1_S_BornBeast`.

## 1. Exact path hits

count: **0**

**None** in any packed BF005 field value.

## 2. Directory-prefix hits (`WeaponShader/` `AlphaMap/` `NormalMap/` `SpecularMap/`)

count: **32**

| record | head | identity | field | prefix | value |
|---|---|---|---|---|---|
| 469 | `Weapon` | `M14EBR` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 542 | `Weapon` | `M4A1-隐袭` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M4A1-S_s.dtx` |
| 542 | `Weapon` | `M4A1-隐袭` | `SpecularMapName2` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M4A1-S_Bandage_s.dtx` |
| 545 | `Weapon` | `MK5-S` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-krissSuperV_Silver_S.DTX` |
| 560 | `Weapon` | `M4A1-隐袭` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M4A1-S_s.dtx` |
| 560 | `Weapon` | `M4A1-隐袭` | `SpecularMapName2` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M4A1-S_Bandage_s.dtx` |
| 579 | `Weapon` | `M14EBR-圣诞` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 585 | `Weapon` | `M4A1-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-M4A1_RoyalDragon_s.DTX` |
| 586 | `Weapon` | `Barrett-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |
| 587 | `Weapon` | `尼泊尔军刀-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-kukri_RoyalDragon_S.dtx` |
| 588 | `Weapon` | `MG3-银色杀手` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-MG3_PerfectSilever_s.dtx` |
| 589 | `Weapon` | `双枪沙鹰-幽灵` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-DualDE_GreenVein_S.dtx` |
| 591 | `Weapon` | `FN F2000-绿魔` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-FN F2000_GreenSkull_s.dtx` |
| 592 | `Weapon` | `毛瑟手枪-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Mauser_RoyalDragon_S.dtx` |
| 598 | `Weapon` | `M4A1-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-M4A1_RoyalDragon_s.DTX` |
| 599 | `Weapon` | `Barrett-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |
| 600 | `Weapon` | `毛瑟手枪-战龙` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Mauser_RoyalDragon_S.dtx` |
| 612 | `Weapon` | `DSR-1 老兵` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\DSR-2_S.dtx` |
| 612 | `Weapon` | `DSR-1 老兵` | `SpecularMapName3` | `SpecularMap` | `ModelTextures\SpecularMap\DSR-1_Scope_S.dtx` |
| 735 | `Weapon` | `M14EBR-雪夜奇缘` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 740 | `Weapon` | `M14EBR-圣诞` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 883 | `Weapon` | `M14EBR-迷彩` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 1036 | `Weapon` | `M14EBR-蓝海` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 1172 | `Weapon` | `M14EBR-天羽` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 1216 | `Weapon` | `M14EBR-天羽` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-RI_M14EBR_s.dtx` |
| 3594 | `Weapon` | `MG3-银色杀手` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-MG3_PerfectSilever_s.dtx` |
| 4497 | `Weapon` | `强化M82A1` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |
| 5811 | `Weapon` | `强化M82A1` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |
| 6552 | `Weapon` | `强化M82A1` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |
| 6580 | `Weapon` | `MG3-银色杀手` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-MG3_PerfectSilever_s.dtx` |
| 6582 | `Weapon` | `双枪沙鹰-幽灵` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-DualDE_GreenVein_S.dtx` |
| 7587 | `Weapon` | `强化M82A1` | `SpecularMapName` | `SpecularMap` | `ModelTextures\SpecularMap\PV-Barret M99_RoyalDragon_S.dtx` |

## 3. FileName-key union vs 黑骑士

| key | records | on canonical 黑骑士 |
|---|---|---|
| `ChangeModelFileName` | 127 | False |
| `ChangeSkinFileName` | 33 | False |
| `CrossHairFileName` | 56 | False |
| `LeftHandChangeModelFileName` | 38 | False |
| `LeftHandModelFileName` | 529 | False |
| `ModelFileName` | 6067 | True |
| `MotionFileName` | 1 | False |
| `MountedStandModelFileName` | 6 | False |
| `PViewModelFileName` | 6052 | True |
| `PViewRenderStyleFileName` | 6097 | True |
| `PViewSkinFileName` | 5955 | True |
| `PreViewModelFileName` | 1110 | True |
| `ProjectileModelFileName` | 146 | False |
| `ProjectileSkinFileName` | 141 | False |
| `RenderStyleFileName` | 6057 | True |
| `SkinFileName` | 6041 | True |
| `ThrowModelFileName` | 48 | False |
| `ThrowSkinFileName` | 48 | False |
| `WChangeModelFileName` | 100 | False |
| `WLeftHandChangeModelFileName` | 22 | False |
| `WLeftHandModelFileName` | 250 | False |
| `WModelFileName` | 1781 | False |

Projectile/left-hand `*FileName` extras are other weapon types,
not Alpha/Shader path fields.

## 3b. Material-ish keys (`*MapName*` / Shader / Alpha / Normal / Specular)

| key | records | on canonical 黑骑士 |
|---|---|---|
| `LightCorrectionLegacyShader` | 18 | False |
| `SpecularMapName` | 29 | False |
| `SpecularMapName2` | 2 | False |
| `SpecularMapName3` | 1 | False |
| `SpecularPower` | 46 | False |

These keys exist on **other** weapons but not on 黑骑士:
`['LightCorrectionLegacyShader', 'SpecularMapName', 'SpecularMapName2', 'SpecularMapName3', 'SpecularPower']`

Observed `SpecularMapName` values are `.dtx` under
`ModelTextures\SpecularMap\`, not the BornBeast `.TGA` inventory files.

## 4. REZ existence (not consumer)

| logical path | present |
|---|---|
| `WEAPONSHADER/M4A1_S_BORNBEAST.CFG` | WeaponShader/M4A1_S_BornBeast.CFG |
| `ALPHAMAP/M4A1_S_BORNBEAST_ALPHA.TGA` | AlphaMap/M4A1_S_BornBeast_alpha.TGA |
| `NORMALMAP/M4A1_S_BORNBEAST_N.TGA` | NormalMap/M4A1_S_BornBeast_N.TGA |
| `SPECULARMAP/M4A1_S_BORNBEAST_S.TGA` | SpecularMap/M4A1_S_BornBeast_S.TGA |

## 5. Remaining ambiguity

- Exact BornBeast `WeaponShader/` and `AlphaMap/` / `NormalMap/` /
  `SpecularMap/*.TGA` paths: **0** in 8205 BF005 records.
- Some later weapons have `SpecularMapName` → `SpecularMap\*.dtx`,
  not TGA, and 黑骑士 does not have that field.
- No `WeaponShader` / `AlphaMapName` field exists in this table.
- CFG/render semantic closure still `OPEN_UNRESOLVED`.
- P4-M01 is not PASS. This is not P5 雷神.

### Confidence: `MEDIUM`

## 6. Status

**status**: `CANDIDATE_ONLY`

## 7. Scope guard

- did NOT announce P4-M01 PASS
- did NOT use StandardName stem as CFG proof
- did NOT scan all `.cfg` payloads or non-BUTES `.ltc`
- did NOT reverse DLL / EXE / FXO
- did NOT freeze CFG shader semantics
- did NOT modify historical accepted evidence or `plan.md`

