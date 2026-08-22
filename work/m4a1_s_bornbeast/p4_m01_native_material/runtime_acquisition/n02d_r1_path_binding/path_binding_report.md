# P4-M01-N02-D-R1 — Path-Aware REZ Runtime Binding Revalidation

- status: **M4A1_RUNTIME_PATH_BINDING_CONFIRMED**
- script: `scripts/material_recovery/n02d_r1_path_aware_rez_binding.py`
- runtime source: `rez/Butes/bf005.ltc` (decoded via N02-B-R1 pipeline)

## 1. Scope & path-normalisation rule

This is a rework of N02-D per plan.md §4.10.  The previous
N02-D built a basename-only index and could not distinguish
e.g. `Models/PlayerView/PV-M4A1.LTB` from
`ModelTextures/PlayerView/PV-M4A1.DTX`.  This rework
preserves the full REZ directory hierarchy and binds the
bf005 runtime path to an **archive-relative logical path**
by exact match.

Normalisation rules (in order):

1. backslash -> forward slash
2. strip a **single** leading virtual root if it is one of:
   - `Models/` — LithTech engine `Models` virtual root
   - `ModelTextures/` — LithTech engine `ModelTextures` virtual root
   Both are confirmed absent as top-level REZ directories in
   the RF016 / RF017 / rf002 inventory.
3. `RS/` is **kept** (it is a literal REZ subdir in rf002.rez).
4. uppercase for REZ-side comparison (REZ entries are upper-case).
5. extensionless `ModelFileName` / `PViewModelFileName` ->
   only `.LTB` is attempted as suffix.  No `.dtx/.tga/.lto/
.ltc/.rez/.dat` fallback (forbidden per task.md §4.3).

Multi-archive hits are reported explicitly; no archive is
declared authoritative without explicit load-order evidence.

## 2. REZ index scope

- REZ directories: `rez/ rez2/ rez3/ rez4/ rez5/ rez6/`
- REZ files indexed: **475**
- total file entries: **252,505**
- unique full paths: **243,508**
- unique basenames: **225,863**
- index build time: 16.6s

## 3. Verdict counts

| verdict | count | meaning |
|---|---|---|
| `EXACT_PATH_BINDING` | 49 | single full-path match after normalisation |
| `EXTENSIONLESS_LTB_RESOLVED` | 10 | extensionless model value -> .LTB single full-path match |
| `EXACT_PATH_MULTIPLE_ARCHIVES` | 1 | full path exists in >=2 distinct REZ |

## 4. Distinct (WeaponName, field) coverage

- total unique (WeaponName, field) pairs: **60**
- full-path bound (after virtual-root strip): **60**
- basename-only (not full-path): **0**
- missing entirely: **0**
- archive-ambiguity cases: **1**

## 5. Per-binding path-aware lookup

| WeaponName | field | runtime_path | normalised | verdict | archive_count |
|---|---|---|---|---|---|
| `M4A1` | `ModelFileName` | `Models\weapons\m4a1.ltb` | `WEAPONS/M4A1.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | `WEAPONS/L-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | `PLAYERVIEW/PV-M4A1` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `PLAYERVIEW/PV-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-B` | `ModelFileName` | `Models\weapons\m4a1.ltb` | `WEAPONS/M4A1.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-B` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | `WEAPONS/L-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-B` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | `PLAYERVIEW/PV-M4A1` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1-B` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `PLAYERVIEW/PV-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-B` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-B` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-A` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer.DTX` | `WEAPONS/L-M4A1_SILENCER.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `PLAYERVIEW/PV-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-S` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-S` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | `WEAPONS/L-M4A1_SILENCER_CAMO.DTX` | EXACT_PATH_MULTIPLE_ARCHIVES | 2 |
| `M4A1-S` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1-S` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1-camo.dtx` | `PLAYERVIEW/PV-M4A1-CAMO.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-S` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-S` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-QQ»áÔ±` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-QQ»áÔ±` | `SkinFileName` | `ModelTextures\weapons\m4a1_qq.DTX` | `WEAPONS/M4A1_QQ.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-m4a1_qq.dtx` | `PLAYERVIEW/PV-M4A1_QQ.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-QQ»áÔ±` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-Custom` | `ModelFileName` | `Models\weapons\M4A1-CUSTOM.ltb` | `WEAPONS/M4A1-CUSTOM.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-Custom` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | `WEAPONS/L-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-Custom` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1-CUSTOM` | `PLAYERVIEW/PV-M4A1-CUSTOM` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `M4A1-Custom` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `PLAYERVIEW/PV-M4A1.DTX` | EXACT_PATH_BINDING | 1 |
| `M4A1-Custom` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `M4A1-Custom` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `»Æ½ðM4A1` | `ModelFileName` | `Models\weapons\m4a1.ltb` | `WEAPONS/M4A1.LTB` | EXACT_PATH_BINDING | 1 |
| `»Æ½ðM4A1` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_gold.dtx` | `WEAPONS/QV-RI_M4A1_GOLD.DTX` | EXACT_PATH_BINDING | 1 |
| `»Æ½ðM4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | `PLAYERVIEW/PV-M4A1` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `»Æ½ðM4A1` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_gold.dtx` | `PLAYERVIEW/PV-RI_M4A1_GOLD.DTX` | EXACT_PATH_BINDING | 1 |
| `»Æ½ðM4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `»Æ½ðM4A1` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `ÇàÍ­M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `ÇàÍ­M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_bronze.dtx` | `WEAPONS/QV-RI_M4A1_SILENCER_BRONZE.DTX` | EXACT_PATH_BINDING | 1 |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_bronze.dtx` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_BRONZE.DTX` | EXACT_PATH_BINDING | 1 |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `ÇàÍ­M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `ÒøÉ«M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `ÒøÉ«M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_silver.dtx` | `WEAPONS/QV-RI_M4A1_SILENCER_SILVER.DTX` | EXACT_PATH_BINDING | 1 |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_silver.DTX` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_SILVER.DTX` | EXACT_PATH_BINDING | 1 |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `ÒøÉ«M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |
| `Ë®¾§M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | `WEAPONS/M4A1_SILENCER.LTB` | EXACT_PATH_BINDING | 1 |
| `Ë®¾§M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_crystal.DTX` | `WEAPONS/QV-RI_M4A1_SILENCER_CRYSTAL.DTX` | EXACT_PATH_BINDING | 1 |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `PLAYERVIEW/PV-M4A1_SILENCER` | EXTENSIONLESS_LTB_RESOLVED | 1 |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_crystal.DTX` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_CRYSTAL.DTX` | EXACT_PATH_BINDING | 1 |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | `RS/NINJATRANSLUCENT.LTB` | EXACT_PATH_BINDING | 1 |
| `Ë®¾§M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | `RS/PVMODELDEFAULT.LTB` | EXACT_PATH_BINDING | 1 |

## 6. Archive ambiguity (same full path in multiple REZ)

| WeaponName | field | runtime_path | normalised | distinct REZ |
|---|---|---|---|---|
| `M4A1-S` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | `WEAPONS/L-M4A1_SILENCER_CAMO.DTX` | RF017.REZ, rf017.rez |

## 7. Per-(WeaponName, field) verdict rollup

| WeaponName | field | best verdict |
|---|---|---|
| `M4A1` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1` | `SkinFileName` | EXACT_PATH_BINDING |
| `M4A1-A` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1-A` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1-A` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-A` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1-A` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-A` | `SkinFileName` | EXACT_PATH_BINDING |
| `M4A1-B` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1-B` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1-B` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-B` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1-B` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-B` | `SkinFileName` | EXACT_PATH_BINDING |
| `M4A1-Custom` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1-Custom` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1-Custom` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-Custom` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1-Custom` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-Custom` | `SkinFileName` | EXACT_PATH_BINDING |
| `M4A1-QQ»áÔ±` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1-QQ»áÔ±` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-QQ»áÔ±` | `SkinFileName` | EXACT_PATH_BINDING |
| `M4A1-S` | `ModelFileName` | EXACT_PATH_BINDING |
| `M4A1-S` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `M4A1-S` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-S` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `M4A1-S` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `M4A1-S` | `SkinFileName` | EXACT_PATH_MULTIPLE_ARCHIVES |
| `»Æ½ðM4A1` | `ModelFileName` | EXACT_PATH_BINDING |
| `»Æ½ðM4A1` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `»Æ½ðM4A1` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `»Æ½ðM4A1` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `»Æ½ðM4A1` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `»Æ½ðM4A1` | `SkinFileName` | EXACT_PATH_BINDING |
| `ÇàÍ­M4A1-A` | `ModelFileName` | EXACT_PATH_BINDING |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `ÇàÍ­M4A1-A` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `ÇàÍ­M4A1-A` | `SkinFileName` | EXACT_PATH_BINDING |
| `Ë®¾§M4A1-A` | `ModelFileName` | EXACT_PATH_BINDING |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `Ë®¾§M4A1-A` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `Ë®¾§M4A1-A` | `SkinFileName` | EXACT_PATH_BINDING |
| `ÒøÉ«M4A1-A` | `ModelFileName` | EXACT_PATH_BINDING |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | EXTENSIONLESS_LTB_RESOLVED |
| `ÒøÉ«M4A1-A` | `PViewRenderStyleFileName` | EXACT_PATH_BINDING |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | EXACT_PATH_BINDING |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | EXACT_PATH_BINDING |
| `ÒøÉ«M4A1-A` | `SkinFileName` | EXACT_PATH_BINDING |

## 8. Status & next investigation

**status**: `M4A1_RUNTIME_PATH_BINDING_CONFIRMED`

- every M4A1 binding path used in N02-C resolves to a
  full archive-relative logical path in the current CF
  runtime REZ set after the documented virtual-root strip.
- The next single highest-value consumer is **bounded
  payload SHA collection** for the matching entry: read
  just the bytes at `data_offset` for `size` bytes,
  hash them, and compare to any P4 / N01 extracted
  artifact. The full file is not needed.

## 9. Scope guard

- did NOT extract any REZ payload bytes
- did NOT decompile or strings/xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT modify `plan.md`
- did NOT re-do LTC format reverse
- did NOT explain or reverse LZX
- did NOT treat basename similarity as path binding proof
- did NOT announce P4-M01 PASS; did NOT enter P5 identity
  confirmation
