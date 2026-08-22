# P4-M01-N02-A — Runtime Root Discovery & Candidate Inventory

- generated_at: `2026-08-22T13:40:17.488168+00:00`
- script: `scripts\material_recovery\n02_runtime_artifact_acquire.py`
- status: **RUNTIME_INVENTORY_READY_FOR_REVIEW**

## 1. Root discovery

| root_id | path | exists | trustworthy | reason |
|---|---|---|---|---|
| `cf_default` | `D:\Program Files\CF(2)` | yes | **yes** | present: cf-exe=True rez=True rez_dir=True link.ini=True |
| `cf_legacy_d_game` | `D:\game\7launch\Counter-Strike 2` | no | no |  |
| `wegame_default` | `D:\WeGame` | no | no |  |
| `wegame_program` | `C:\Program Files\WeGame` | no | no |  |
| `tgp_default` | `D:\TGP` | no | no |  |
| `qqgame_default` | `D:\QQGame` | no | no |  |
| `cf_alt_pf86` | `C:\Program Files (x86)\CrossFire` | no | no |  |
| `cf_alt_pf` | `C:\Program Files\CrossFire` | no | no |  |
| `cf_alt_root` | `C:\CrossFire` | no | no |  |
| `cf_alt_d` | `D:\CrossFire` | no | no |  |

**Selected root**: `cf_default` at `D:\Program Files\CF(2)`

Trust reason: present: cf-exe=True rez=True rez_dir=True link.ini=True

## 2. Candidate counts

- **total_candidates**: 2273

### By extension

| ext | count |
|---|---|
| `.bin` | 1291 |
| `.rez` | 476 |
| `.dll` | 272 |
| `.ltc` | 73 |
| `.pak` | 58 |
| `.dat` | 44 |
| `.exe` | 27 |
| `.fxo` | 14 |
| `.ini` | 8 |
| `.lta` | 5 |
| `.fx` | 3 |
| `.lto` | 2 |

### By candidate role

| role | count |
|---|---|
| `binary` | 1291 |
| `archive` | 476 |
| `library` | 272 |
| `config` | 107 |
| `packed` | 58 |
| `process` | 27 |
| `generic` | 23 |
| `shader` | 17 |
| `LithTech` | 2 |

## 3. Top 20 candidates (priority, then size)

| rank | role | ext | path_alias | size | sha256 | why |
|---|---|---|---|---|---|---|
| 1 | `shader` | `.fx` | `rez/InGameUI/Shader/UIShader.fx` | 17,992 | `9fe7829a95ede12e` | shader candidate (.fx) under rez/Shader/ or matching shader ext |
| 2 | `shader` | `.fx` | `rez/Shader/CustomColor.fx` | 0 | `e3b0c44298fc1c14` | shader candidate (.fx) under rez/Shader/ or matching shader ext |
| 3 | `shader` | `.fx` | `rez/Shader/shader.fx` | 0 | `e3b0c44298fc1c14` | shader candidate (.fx) under rez/Shader/ or matching shader ext |
| 4 | `shader` | `.fxo` | `rez/Shader/playerviewmesh.fxo` | 1,193,704 | `d227961370c480ba` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 5 | `shader` | `.fxo` | `rez/Shader/AdvancedShader.fxo` | 188,608 | `6853c15a56d3d0bb` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 6 | `shader` | `.fxo` | `rez/Shader/playermesh.fxo` | 118,048 | `a5eb55e876a779ba` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 7 | `shader` | `.fxo` | `rez/Shader/CustomColor.fxo` | 113,616 | `7222e7824e9a2229` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 8 | `shader` | `.fxo` | `rez/Shader/QuarterViewEffect.fxo` | 101,388 | `cc37126db2d6d3a0` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 9 | `shader` | `.fxo` | `rez/Shader/RefractionComponent.fxo` | 69,268 | `4d54aca58abf1e97` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 10 | `shader` | `.fxo` | `rez/Shader/HousingSystemMeshShader.fxo` | 64,376 | `79383e537f6fb5ef` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 11 | `shader` | `.fxo` | `rez/Shader/MRTShader.fxo` | 36,944 | `2ceb82f345e12e3d` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 12 | `shader` | `.fxo` | `rez/InGameUI/Shader/UIShader.fxo` | 35,528 | `9b3017c97a68ae9c` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 13 | `shader` | `.fxo` | `rez/Shader/legacyshader.fxo` | 11,732 | `17f76f2e504210c5` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 14 | `shader` | `.fxo` | `rez/Shader/PostProcess.fxo` | 11,376 | `b07d545b0f90db04` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 15 | `shader` | `.fxo` | `rez/Shader/FXShader.fxo` | 4,468 | `7dac5f6fa813d835` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 16 | `shader` | `.fxo` | `rez/Shader/Instancing.fxo` | 4,324 | `4ca7dbd93460737d` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 17 | `shader` | `.fxo` | `rez/Shader/RenderStyleEffect_RigidMesh.fxo` | 0 | `e3b0c44298fc1c14` | shader candidate (.fxo) under rez/Shader/ or matching shader ext |
| 18 | `archive` | `.rez` | `rez4/RF017.REZ` | 2,090,174,576 | `n/a` | LithTech REZ archive — needs unpacking to expose inner DTX/LTB/Config |
| 19 | `archive` | `.rez` | `rez/rf192.rez` | 1,994,583,320 | `n/a` | LithTech REZ archive — needs unpacking to expose inner DTX/LTB/Config |
| 20 | `archive` | `.rez` | `rez2/RF017.REZ` | 1,940,536,776 | `n/a` | LithTech REZ archive — needs unpacking to expose inner DTX/LTB/Config |

## 3.5 Key observations

- `.ltc` count = 73; all live under `rez/Butes/`. plan.md §4.7 previously reported `BornBeast text-config hits = 0` on the unpacked `data/**` corpus — these are **packed-binary sibling** configs that the unpack pipeline did not surface. They are the most direct follow-up target for N01 reopen.
- `bf*.ltc` family count = 35 (e.g. `bf001.ltc`, `bf002.ltc`, `bf003.ltc`, `bf004.ltc`, `bf005.ltc`, …). Naming pattern strongly suggests weapon / bdf family — cross-check with N01 family list (BornBeast / Transformers / Jewelry / BlueDiamond).
- `rez/bf000.lta` is the only `bf`-prefixed archive-shaped config: size = 30,002 bytes. Compare with the LTB post-mesh short ASCII field identified in plan.md §4.6.
- Shader-bearing files: 17 total. The 14 `rez/Shader/*.fxo` (compiled) and 3 `rez/Shader/*.fx` (source) are the natural N02-B `archive/shader triage` target.
- Largest REZ archives: `rez4/RF017.REZ` (2,090,174,576 B), `rez/rf192.rez` (1,994,583,320 B), `rez2/RF017.REZ` (1,940,536,776 B), `rez3/RF017.REZ` (1,931,848,826 B), `rez5/RF017.REZ` (1,928,543,492 B). Top archive unpacking is the most expensive N02-B branch.
- `.dat` under `rez/` count = 28; includes `rez/Butes/*_zoneman.dat` and `rez/Camera/Opening_*.dat` — candidate for follow-up only if a concrete zone / camera binding question emerges.

## 4. Scope guard

Bounded to ARTIFACT_EXTS only. No audio corpus, no derived outputs.
Skipped auxiliary Tencent/anti-cheat subtrees: AntiCheatExpert, Chroma, D3D, FeedBack, GPUCache, GVoiceLog, GVoiceTQos, NTCLS, PCMLoader, QQBrowser, Report, TCLS, TGuard, TenioCS, UpdateCenter, WeGameLauncher, WeGameLauncher2, components, rail_files, tiny_cache.
Scan depth limit: 6.
SHA256 captured only for files <= 512 MiB.

What this round did NOT do:

- no strings / xref / decompilation;
- no execution of any CF binary;
- no launcher patch or update;
- no `data/**` re-scan, no derived-output re-baseline;
- no `plan.md` modification.

Recommended follow-up tasks (in priority order):

1. `N02-B PE / strings static triage` on Top shader/model EXE/DLL;
2. `N02-B archive/shader triage` on Top REZ + Shader;
3. `N02-B launcher/runtime-root expansion` if x64 / new sub-roots matter.
