# P5-T01 Scan Report — 官方身份锚点与本地候选召回

- status: `EXECUTION_PASS`
- task_id: `P5-T01`
- target identity: `M4A1-雷神`
- official reference: https://cf.qq.com/cp/a20250701wqbk/index.html
- scan root: `data/**` (read-only)
- inventory: 165082 files / 16913021491 bytes
- recalled candidates: 2856; LTB candidates: 1281; canonical LTB inspected: 441

## Search and parser boundary

Keywords were used for recall only: `M4`, `M4A1`, `M4A1-S`, `M4A1S`, `雷神`, `LEISHEN`, `LEI_SHEN`, `THOR`, `THUNDER`. Text configuration was searched with literal basename references. Binary `.BIN` resources were not decoded and are marked unresolved by their path/extension. The existing CFRezManager inspect route was used only for canonical LTB light summaries; no Blender, OBJ export, or Source/MIGI changes were performed.

## Top 30 candidates (priority only, not identity proof)

| Rank | Type | Score | Path | Light summary | Identity boundary |
|---:|---|---:|---|---|---|
| 1 | model | 220 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 2 | model | 220 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 3 | model | 210 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_BL.LTB` | non-canonical _BL/_GR/_WOMAN presentation variant not inspected in bounded T01 pass | `CANDIDATE_ONLY` |
| 4 | model | 210 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic_BL.LTB` | non-canonical _BL/_GR/_WOMAN presentation variant not inspected in bounded T01 pass | `CANDIDATE_ONLY` |
| 5 | model | 170 | `data/rf016/Models/WEAPONS/QV-M4A1_S_BornBeast.LTB` | inspect report not produced:  be written as valid JSON. To make it work when using 'JsonSerializer', consider specifying 'JsonNumberHandling.AllowNamedFloatingPointLiterals' (see https://learn.microsoft.com/dotnet/api/system.text.json.serialization.jsonnumberhandling). | `CANDIDATE_ONLY` |
| 6 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-EliteMOS_M4A1_IronBeast.LTB` | 5 meshes/5958 tris | `CANDIDATE_ONLY` |
| 7 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-GunNiang_B_M4A1_S_IronBeast.LTB` | 5 meshes/8579 tris | `CANDIDATE_ONLY` |
| 8 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_BORNBEAST_NG_WIND.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 9 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_AngelicBeast.LTB` | 7 meshes/11168 tris | `CANDIDATE_ONLY` |
| 10 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_AngelicBeast_Sprint.LTB` | 7 meshes/11168 tris | `CANDIDATE_ONLY` |
| 11 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 12 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_Champion.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 13 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_Medusa.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 14 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_NG_GoldenWind.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 15 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_QingLong.LTB` | 9 meshes/12013 tris | `CANDIDATE_ONLY` |
| 16 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_QingLong2_NG.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |
| 17 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_QingLong_Darken.LTB` | 9 meshes/12013 tris | `CANDIDATE_ONLY` |
| 18 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_TianShen.LTB` | 4 meshes/8150 tris | `CANDIDATE_ONLY` |
| 19 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_TianShen_Nano.LTB` | 9 meshes/16022 tris | `CANDIDATE_ONLY` |
| 20 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Beast_TianShen_Nano_test.LTB` | 9 meshes/16022 tris | `CANDIDATE_ONLY` |
| 21 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast2.LTB` | 7 meshes/8905 tris | `CANDIDATE_ONLY` |
| 22 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast2_sprint.LTB` | 7 meshes/8905 tris | `CANDIDATE_ONLY` |
| 23 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_13thCarnival.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 24 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_CFS21.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 25 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_FuXi.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 26 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_HHUD.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 27 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_IceSoul.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 28 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_ImperialGold.LTB` | 11 meshes/5420 tris | `CANDIDATE_ONLY` |
| 29 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Legend18.LTB` | 11 meshes/5342 tris | `CANDIDATE_ONLY` |
| 30 | model | 120 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_MJXW.LTB` | 5 meshes/3183 tris | `CANDIDATE_ONLY` |

## Exclusions and limitations

- 161 recalled entries are derived/unclassified local outputs or non-weapon/hand-only summaries; they remain recorded for exclusion traceability.
- 246 LTB inspect attempts did not yield a usable report; these candidates remain `not_available` and are not silently promoted.
- 0 candidate hashes failed; details are recorded in `execution.json`.
- `data/**` was not changed and no raw LTB/DTX/TGA/WAV/BIN was copied into the repository outputs.
- The existing Prototype-01 BornBeast paths are retained as comparison/negative-control candidates with `prototype_only_not_finally_proven`; they are not declared final Leishen.

## Recommended next action

Chat/Sol should select a small set of model/texture pairs from this matrix for P5-T02 geometry and atlas comparison. T01 does not enter T02 automatically.
