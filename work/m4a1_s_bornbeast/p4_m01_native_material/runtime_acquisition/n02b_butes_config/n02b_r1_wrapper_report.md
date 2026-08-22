# P4-M01-N02-B-R1 — CrossFire LTC Wrapper Validation & Bute Semantic Correlation

- generated_at: `2026-08-22T14:32:37.797707+00:00`
- script: `scripts\material_recovery\n02_butes_config_triage.py`
- 73-sample target: `rez/Butes/*.ltc` under `D:\Program Files\CF(2)`

Reworks commit `539ae93` — previous `CF_LTC_VARIANT_CONFIRMED` is no longer accepted because the previous round fed raw 54 83 B2 E1 bytes directly into the native decoder instead of running the existing `CrossFireLtcDecoder` wrapper first.

## 1. Wrapper under test

- source: `CFRezManager/Decoders/CrossFire/CrossFireLtcDecoder.cs`
- magic: `5483b2e1` (54 83 B2 E1)
- XOR key (16 bytes repeating): `5483b2e1103f6e9dccfb2a5988b7e615`
- the wrapper applies `data[i] ^ key[i & 15]` over the **entire** payload

## 2. Raw-magic verdict (73 rez/Butes/*.ltc)

| magic | count |
|---|---|
| `5483b2e1` | 73 |

## 3. Wrapper unlock verdict

- samples evaluated: **73**
- wrapper unlock success: **73**
- unlocked header == `00 00 00 00`: **73**

| unlocked header (first-4-hex) | count |
|---|---|
| `00000000` | 73 |

## 4. Post-unlock native decoder verdict

- decoder: 1:1 Python port of `LithTechLtcNativeDecoder`, applied to **unlocked** payload
- native decode success: **73**
- native decode failure: **0**

- (no failure cluster)

## 5. Bute/LTA semantic parse verdict

- total decoded: `73`
- total parsed as Bute grammar: `73`

## 6. Target / resource correlation

Scope reused from existing evidence only (BornBeast / Transformers / Jewelry / BlueDiamond).

- direct binding_evidence_count: **50**

| path_alias | head | ModelFileName | SkinFileName | PViewModelFileName | PViewSkinFileName | evidence_grade |
|---|---|---|---|---|---|---|
| `rez/Butes/bf002.ltc` | `Debris` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf002.ltc` | `Debris` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf003.ltc` | `Breakable` | `Models\M-motion.ltb` | `ModelTextures\ak47.dtx` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf003.ltc` | `Breakable` | `Model\Breakable\GenBottle.ltc` | `ModelTextures\Breakable\SiBottle1.dtx` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_BL_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_BL_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_BL_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_BL_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_GR_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_GR_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_GR_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf004.ltc` | `Character` | `Models\Character\M_GR_001.ltb` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\xm.ltb` | `ModelTextures\weapons\xm1014.dtx` | `Models\PlayerView\pv-xm` | `ModelTextures\PlayerView\pv-xm.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\colt.ltb` | `ModelTextures\weapons\l-colt.dtx` | `Models\PlayerView\pv-colt` | `ModelTextures\PlayerView\pv-colt.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\mp5.ltb` | `ModelTextures\weapons\l-mp5.dtx` | `Models\PlayerView\pv-mp5` | `ModelTextures\PlayerView\pv-mp5.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\p90.ltb` | `ModelTextures\weapons\p90.dtx` | `Models\PlayerView\pv-p90` | `ModelTextures\PlayerView\pv-p90.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\m9.ltb` | `ModelTextures\weapons\l-m9.dtx` | `Models\PlayerView\pv-m9` | `ModelTextures\PlayerView\pv-m9.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\KNIFE.ltb` | `ModelTextures\weapons\l-knife.dtx` | `Models\PlayerView\pv-Knife` | `ModelTextures\PlayerView\pv-knife.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\HEGRENADE.ltb` | `ModelTextures\weapons\l-hegrenade.dtx` | `Models\PlayerView\pv-hegrenade` | `ModelTextures\PlayerView\pv-hegrenade.dtx` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf005.ltc` | `Weapon` | `Models\weapons\FLASHBANG.ltb` | `ModelTextures\weapons\l-flashbang.dtx` | `Models\PlayerView\pv-flashbang` | `ModelTextures\PlayerView\pv-flashbang.DTX` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf007.ltc` | `Sound` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf009.ltc` | `Map` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |
| `rez/Butes/bf009.ltc` | `Map` | `` | `` | `` | `` | DIRECT_BINDING_RELATION |

### Family correlation (substring match in decoded text)

| family | hit_count | sample_paths |
|---|---|---|
| `BornBeast` | 0 |  |
| `Transformers` | 0 |  |
| `Jewelry` | 0 |  |
| `BlueDiamond` | 0 |  |

### Binding field aggregate (unique values across all .ltc)

- `LoadingTexFileNameGR`: 41 unique values; sample = `tex/ui/loading/LOADINGBANLIEUE13.DTX`, `tex/ui/loading/LOADINGDESERTSTORM_GR.DTX`, `tex/ui/loading/LOADINGESTATE.DTX`
- `FileName`: 472 unique values; sample = `message/Bomb_Plant_BL_A_1.wav`, `message/Bomb_Plant_BL_A_1_C.wav`, `message/Bomb_Plant_BL_A_2.wav`
- `WeaponName`: 101 unique values; sample = `AK-47`, `AK-47-A`, `AK-47-B`
- `DebrisSkinFileName`: 2 unique values; sample = `ModelTextures\Debris\SiBottle1.dtx`, `ModelTextures\ak47.dtx`
- `MinimapFileNameGR`: 19 unique values; sample = `TEX/UI/LOADING/MINIMAP_LAYER/BLACKWIDOW/TD_GR.dtx`, `TEX/UI/LOADING/MINIMAP_LAYER/BLACKWIDOW/TM_GR.dtx`, `TEX/UI/LOADING/MINIMAP_LAYER/CEYHAN/TD_GR.dtx`
- `DebrisModelFileName4`: 1 unique values; sample = `Models\Debris\DBottle1d.ltc`
- `PViewRenderStyleFileName`: 1 unique values; sample = `RS\\PVModelDefault.ltb`
- `ArmorName`: 2 unique values; sample = `Helmet`, `Kevlar`
- `DebrisModelFileName5`: 1 unique values; sample = `Models\Debris\DBottle1e.ltc`
- `MapRezFileAndCheckSum`: 32 unique values; sample = `rez\rf001.rez`, `rez\rf003.rez`, `rez\rf006.rez`
- `DebrisModelFileName2`: 2 unique values; sample = `Models\Debris\DBottle1b.ltc`, `Models\M-motion.ltb`
- `LoadingTexFileNameBL`: 41 unique values; sample = `tex/ui/loading/LOADINGBANLIEUE13.DTX`, `tex/ui/loading/LOADINGDESERTSTORM_BL.DTX`, `tex/ui/loading/LOADINGESTATE.DTX`
- `CharacterName`: 72 unique values; sample = `µ¿¾çÀÎ´ëÅ×·¯SAS`, `µ¿¾çÀÎ´ëÅ×·¯°¡À»½Å»óÇ°`, `µ¿¾çÀÎ´ëÅ×·¯±âº»`
- `TexRezFileAndCheckSum`: 16 unique values; sample = `rez\rf007.rez`, `rez\rf009.rez`, `rez\rf010.rez`
- `PViewModelFileName`: 63 unique values; sample = `MODELS\PLAYERVIEW\PV_Nano_knife`, `Models\PlayerView\PV-AK47_Dagger`, `Models\PlayerView\PV-HULK`
- `MapRoomIcon`: 48 unique values; sample = `UI/MapIcon/RoomMap0.TGA`, `UI/MapIcon/RoomMap1.TGA`, `UI/MapIcon/RoomMap11.TGA`
- `SoundName`: 497 unique values; sample = `AxeDeploy`, `AxeHit`, `AxeMetal_1`
- `MapLobbyIcon`: 48 unique values; sample = `UI/MapIcon/LobbyMap0.TGA`, `UI/MapIcon/LobbyMap1.TGA`, `UI/MapIcon/LobbyMap11.TGA`
- `DebrisModelFileName1`: 2 unique values; sample = `Models\Debris\DBottle1a.ltc`, `Models\M-motion.ltb`
- `DebrisModelFileName3`: 2 unique values; sample = `Models\Debris\DBottle1c.ltc`, `Models\M-motion.ltb`
- `PViewSkinFileName`: 83 unique values; sample = `MODELTEXTURES\PLAYERVIEW\PV_NANO_UP_KNIFE.DTX`, `MODELTEXTURES\PLAYERVIEW\PV_Nano_knife.dtx`, `ModelTextures\PlayerView\PV-CSMOKEgrenade_Blue.dtx`
- `MinimapFileNameBL`: 19 unique values; sample = `TEX/UI/LOADING/MINIMAP_LAYER/BLACKWIDOW/TD_BL.dtx`, `TEX/UI/LOADING/MINIMAP_LAYER/BLACKWIDOW/TM_BL.dtx`, `TEX/UI/LOADING/MINIMAP_LAYER/CEYHAN/TD_BL.dtx`
- `ModelFileName`: 67 unique values; sample = `MODELS\CHARACTER\NANOHULK\NANOHULK.ltb`, `MODELS\CHARACTER\NANOHULK\NANOHULK_UP.ltb`, `Model\Breakable\GenBottle.ltc`
- `BreakableName`: 2 unique values; sample = `Bottle`, `BreakLightTest`
- `MapFileName`: 42 unique values; sample = `Banlieue13.dat`, `BlackWidow.dat`, `CH_Spring.dat`
- `SkinFileName`: 89 unique values; sample = `MODELTEXTURES\CHARACTER\NANOHULK\NANOHULK.dtx`, `MODELTEXTURES\CHARACTER\NANOHULK\NANOHULK_UP.dtx`, `MODELTEXTURES\WEAPONS\QV_NANO_UP_KNIFE.DTX`
- `RenderStyleFileName`: 3 unique values; sample = `RS\\GoldWeapon.LTB`, `RS\\NinjaTranslucent.ltb`, `RS\\PVModelDefault.ltb`
- `DebrisName`: 2 unique values; sample = `Bottle`, `BreakLightDebris`

## 7. bf000.lta vs bf*.ltc relationship

- `rez/bf000.lta` (control): size=30,002 bytes, first 16 hex = `c7004400ffff00000000000000000000`
- **NOT** fed into the LTC decoder (not a .ltc). Held as control for downstream grammar comparison only.

## 8. Verdict

- **status**: `RUNTIME_BUTE_PARSED_NO_TARGET_BINDING`

- next single highest-value consumer: RUNTIME_BUTE_PARSED_NO_TARGET_BINDING: wrapper + native decoder both work end-to-end and bf005.ltc carries the full CF weapon table (101 unique WeaponName, 67 ModelFileName, 89 SkinFileName). However, none of the 73 decoded .ltc mentions any of the four N01 family basenames (BornBeast / Transformers / Jewelry / BlueDiamond) — those basenames live in the CFG-file family phase numbering recorded in plan.md §4.4, not in the runtime Bute text. The single next highest-value consumer is therefore **bf005.ltc's weapon table** itself: cross-check each WeaponName's ModelFileName / SkinFileName path against the BornBeast (M4A1-family) and Transformers (variant) baselines, and confirm those paths exist in the CF runtime REZ. Wide EXE/DLL decompile is out of scope per task.md §6.

## 9. Scope guard

- only `rez/Butes/*.ltc` enumerated — no `.lta` fed to LTC decoder;
- `.lta` (rez/bf000.lta) is held as control only, **not** decoded;
- no `data/**` re-scan;
- no DLL/EXE decompile or strings/xref as main task;
- no FXO shader reverse;
- no execution of any CF binary;
- no anti-cheat bypass, no memory dump;
- no large-REZ unpacking as main task;
- did not modify `plan.md`;
- did not rewrite or fork the C# decoder / wrapper.
