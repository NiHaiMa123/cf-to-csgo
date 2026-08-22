# P4-M01-N02-C — M4A1 Weapon Record -> Runtime Asset Correlation

- status: **M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN**
- script: `scripts/material_recovery/n02c_m4a1_weapon_correlation.py`
- runtime source: `rez/Butes/bf005.ltc` (CF weapon table)

## 1. Scope

- only existing N01 / P4 / P5 evidence was re-read
- only `rez/Butes/bf005.ltc` was decoded (the CF weapon table)
- no `data/**` re-scan, no DLL/EXE decompile, no FXO shader reverse
- known P4/N01 asset basenames: 51

## 2. M4A1 family records extracted from bf005.ltc

- M4-family Weapon records: **10**
- M4A1 family present: **True**
- 'BornBeast' substring in any binding value: **False**
- direct config reference to a BornBeast-named asset: **False**

| # | WeaponName | ModelFileName | SkinFileName | PViewModelFileName | PViewSkinFileName | RenderStyleFileName |
|---|---|---|---|---|---|---|
| 1 | `M4A1` | `Models\weapons\m4a1.ltb` | `ModelTextures\weapons\l-m4a1.dtx` | `Models\PlayerView\pv-m4a1` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `RS\\NinjaTranslucent.ltb` |
| 2 | `M4A1-B` | `Models\weapons\m4a1.ltb` | `ModelTextures\weapons\l-m4a1.dtx` | `Models\PlayerView\pv-m4a1` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `RS\\NinjaTranslucent.ltb` |
| 3 | `M4A1-A` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\L-M4A1_Silencer.DTX` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `RS\\NinjaTranslucent.ltb` |
| 4 | `M4A1-S` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\pv-m4a1-camo.dtx` | `RS\\NinjaTranslucent.ltb` |
| 5 | `M4A1-QQ»áÔ±` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\m4a1_qq.DTX` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\PV-m4a1_qq.dtx` | `RS\\NinjaTranslucent.ltb` |
| 6 | `M4A1-Custom` | `Models\weapons\M4A1-CUSTOM.ltb` | `ModelTextures\weapons\l-m4a1.dtx` | `Models\PlayerView\PV-M4A1-CUSTOM` | `ModelTextures\PlayerView\pv-m4a1.dtx` | `RS\\NinjaTranslucent.ltb` |
| 7 | `»Æ½ðM4A1` | `Models\weapons\m4a1.ltb` | `ModelTextures\weapons\QV-RI_m4a1_gold.dtx` | `Models\PlayerView\pv-m4a1` | `ModelTextures\PlayerView\PV-RI_m4a1_gold.dtx` | `RS\\NinjaTranslucent.ltb` |
| 8 | `ÇàÍ­M4A1-A` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\QV-RI_m4a1_silencer_bronze.dtx` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_bronze.dtx` | `RS\\NinjaTranslucent.ltb` |
| 9 | `ÒøÉ«M4A1-A` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\QV-RI_m4a1_silencer_silver.dtx` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_silver.DTX` | `RS\\NinjaTranslucent.ltb` |
| 10 | `Ë®¾§M4A1-A` | `Models\weapons\M4A1_Silencer.ltb` | `ModelTextures\weapons\QV-RI_m4a1_silencer_crystal.DTX` | `Models\PlayerView\pv-m4a1_silencer` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_crystal.DTX` | `RS\\NinjaTranslucent.ltb` |

## 3. Per-field correlation verdict

For each binding field of each M4 record, classify the runtime
value against the known P4/N01 asset basenames. Evidence grades:

- `DIRECT_CONFIG_REFERENCE` — the runtime Bute binds a path whose
  basename matches a known P4/N01 asset exactly. **Counts as binding.**
- `BASENAME_MATCH` — basename string overlap without direct bind.
  Treated as PARTIAL evidence, not a direct binding proof.
- `PARTIAL_BASENAME` — substring overlap (e.g. `m4a1` in
  `pv-m4a1_s_bornbeast_classic`). WEAK signal only.
- `NO_MATCH` — no basename or substring overlap.

## 4. P4 evidence — BornBeast source LTB / derived assets

- BornBeast **LTB** (canonical): `D:\project\cf_to_csgo\data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB`
  - source label: `p4_baseline_inventory`
  - field path: `.repository_p4_inputs.files.cf_ltb_source.path`

All BornBeast-named assets in existing evidence (basename contains 'bornbeast'):

| source_label | value | ext |
|---|---|---|
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB` | `.ltb` |
| `p4_baseline_inventory` | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB` | `.ltb` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work/m4a1_s_bornbeast/source_dump/b3_raw/PV-M4A1_S_BornBeast_Classic.obj` | `.obj` |
| `p4_baseline_inventory` | `work/m4a1_s_bornbeast/source_dump/b3_raw/PV-M4A1_S_BornBeast_Classic.obj` | `.obj` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work/m4a1_s_bornbeast/source_dump/c3_alignment_m4a4/PV-M4A1_S_BornBeast_Classic_c3_aligned.obj` | `.obj` |
| `p4_baseline_inventory` | `work/m4a1_s_bornbeast/source_dump/c3_alignment_m4a4/PV-M4A1_S_BornBeast_Classic_c3_aligned.obj` | `.obj` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png` | `.png` |
| `p4_baseline_inventory` | `work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png` | `.png` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vmt` | `.vmt` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1_selfillum.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\models\weapons\v_rif_m4a1.mdl` | `.mdl` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_prototype_01\staging\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vmt` | `.vmt` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_prototype_01\staging\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_prototype_01\staging\materials\models\weapons\v_models\rif_m4a1\rif_m4a1_selfillum.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_prototype_01\staging\models\weapons\v_rif_m4a1.mdl` | `.mdl` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vmt` | `.vmt` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1_selfillum.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp\models\weapons\v_rif_m4a1.mdl` | `.mdl` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vmt` | `.vmt` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp\materials\models\weapons\v_models\rif_m4a1\rif_m4a1_selfillum.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp\models\weapons\v_rif_m4a1.mdl` | `.mdl` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vmt` | `.vmt` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final\materials\models\weapons\v_models\rif_m4a1\rif_m4a1.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final\materials\models\weapons\v_models\rif_m4a1\rif_m4a1_selfillum.vtf` | `.vtf` |
| `p4_baseline_inventory` | `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final\models\weapons\v_rif_m4a1.mdl` | `.mdl` |
| `prototype_01_manifest` | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB` | `.ltb` |
| `prototype_01_manifest` | `work/m4a1_s_bornbeast/source_dump/c3_alignment_m4a4/PV-M4A1_S_BornBeast_Classic_c3_aligned.obj` | `.obj` |
| `prototype_01_manifest` | `work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png` | `.png` |
| `m4a4_final_bornbeast_manifest` | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB` | `.ltb` |
| `m4a4_final_bornbeast_manifest` | `work/m4a1_s_bornbeast/source_dump/b3_raw/PV-M4A1_S_BornBeast_Classic.obj` | `.obj` |
| `m4a4_final_bornbeast_manifest` | `work/m4a1_s_bornbeast/source_dump/c3_alignment_m4a4/PV-M4A1_S_BornBeast_Classic_c3_aligned.obj` | `.obj` |
| `m4a4_final_bornbeast_manifest` | `data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` | `.dtx` |
| `m4a4_final_bornbeast_manifest` | `data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA` | `.tga` |
| `m4a4_final_bornbeast_manifest` | `data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA` | `.tga` |
| `m4a4_final_bornbeast_manifest` | `data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA` | `.tga` |
| `material_map` | `build/m4a1_s_bornbeast_m4a4/f4_recognizable_classic/addon/materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vmt` | `.vmt` |
| `material_map` | `build/m4a1_s_bornbeast_m4a4/f4_recognizable_classic/addon/materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vtf` | `.vtf` |

Sources read:
- ✓ `p4_baseline_inventory` (D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_prototype_01\baseline_inventory.json)
- ✓ `prototype_01_manifest` (D:\project\cf_to_csgo\assets\weapons\m4a1_s_bornbeast\prototype_01_manifest.json)
- ✓ `m4a4_target_manifest` (D:\project\cf_to_csgo\assets\weapons\m4a1_s_bornbeast\m4a4_target_manifest.json)
- ✓ `m4a4_final_bornbeast_manifest` (D:\project\cf_to_csgo\assets\weapons\m4a1_s_bornbeast\m4a4_final_bornbeast_manifest.json)
- ✓ `c3_alignment_manifest` (D:\project\cf_to_csgo\assets\weapons\m4a1_s_bornbeast\c3_alignment_m4a4_manifest.json)
- ✓ `material_map` (D:\project\cf_to_csgo\assets\weapons\m4a1_s_bornbeast\material_map.json)
- ✓ `m4a4_reference_report` (D:\project\cf_to_csgo\work\m4a1_s_bornbeast\reference_m4a4\reference_report.json)

## 5. Verdict

**status**: `M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN`

- bf005.ltc binds M4A1 family records to runtime paths
  (`Models\weapons\m4a1.ltb`, `Models\PlayerView\pv-m4a1`,
  `M4A1_Silencer.ltb`, `pv-m4a1_silencer`, …).
- The P4/N01 BornBeast source LTB is a **DERIVED** asset
  (`data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB`),
  not present in the runtime Bute text layer.
- 'BornBeast' substring: 0 hits across all 73 decoded
  `rez/Butes/*.ltc`.
- Therefore **no DIRECT_CONFIG_REFERENCE** to a BornBeast-named
  resource exists; the gap between runtime Bute and P4 derived
  asset is open.

## 6. Next single highest-value investigation target

The single highest-value next target is a **bounded REZ-side check**:
confirm that one of the runtime paths bound by bf005.ltc's M4A1
family records (`Models\weapons\m4a1.ltb`,
`ModelTextures\weapons\l-m4a1.dtx`,
`Models\PlayerView\pv-m4a1`,
`ModelTextures\PlayerView\pv-m4a1.dtx`,
`Models\weapons\M4A1_Silencer.ltb`,
`Models\PlayerView\pv-m4a1_silencer`, …) actually exists
as a payload inside the CF runtime REZ archives (without unpacking
the full 2 GiB REZ as the main task). That would either:
  1. directly show the runtime path matches a real CF artifact, or
  2. reveal that the BornBeast variant lives in a different REZ
     (and therefore the gap between Bute bind and P4 derived asset
     is structural, not a path mismatch).

Wide DLL/EXE decompile, FXO shader reverse, and large-REZ
unpacking remain out of scope per task.md §8.

## 7. Scope guard

- did not re-scan `data/**`
- did not decompile or strings/xref any EXE / DLL
- did not reverse any FXO shader
- did not run any CF client / runtime binary
- did not modify `plan.md`
- did not re-do LTC format reverse
- did not treat filename similarity as binding proof
