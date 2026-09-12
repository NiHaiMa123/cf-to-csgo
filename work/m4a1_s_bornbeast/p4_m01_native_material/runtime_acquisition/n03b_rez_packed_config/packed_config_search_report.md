# P4-M01-N03-B — REZ-resident table/config BornBeast search

- status: **BORNBEAST_CONSUMER_CONFIRMED**
- confidence: **HIGH**
- script: `scripts/material_recovery/n03b_rez_packed_config.py`
- consumes: N03-A inventory tokens + N02-D-R1 REZ index + N02-B-R1 LTC decoder
- elapsed: 113.42s

## 1. Question

```text
BornBeast inventory token
  -> REZ-resident table/config payload
  -> record / field context
  -> consumer relation grade
```

## 2. Selection

| rule | value |
|---|---|
| extensions | `.cft` `.lta` `.txt` |
| extra .ltc | `full_path` starts with `BUTES/` |
| unique full_path | yes, preferred archive `rez/` |
| payload size cap | 8388608 bytes |
| excluded | `.dat` `.dtx` `.bin` `.ltb` `.cfg` non-BUTES `.ltc` |

| ext | selected | skipped | read_ok | files_with_hits |
|---|---|---|---|---|
| `.cft` | 548 | 0 | 548 | 0 |
| `.lta` | 20 | 0 | 20 | 0 |
| `.ltc` | 928 | 0 | 928 | 1 |
| `.txt` | 63 | 4 | 59 | 0 |

- REZ archives indexed: 475
- REZ file entries: 252505
- tokens: 36

### Priority tables

| full_path | present | size | hits |
|---|---|---|---|
| `Table/ITEM.CFT` | yes | 1333487 | 0 |
| `Table/ModelBute.CFT` | yes | 40923 | 0 |
| `Table/WeaponPoint.CFT` | yes | 50386 | 0 |

## 3. Hits

| metric | count |
|---|---|
| DIRECT_CONFIG_FIELD | 82 |
| CFT text-token | 0 |
| any path/stem text-token | 70 |
| hash-hex text-token | 0 |
| files with any hit | 1 |

### 3.1 Per-file hits

| archive | full_path | ext | size | field_hits | unique_weapons |
|---|---|---|---|---|---|
| `rez/RB001.REZ` | `Butes/BF005.LTC` | `.ltc` | 5892359 | 82 | 22 |

The packed `Butes/BF005.LTC` inside `rez/RB001.REZ` is a **different
payload** from the loose `rez/Butes/bf005.ltc` that N02-C / N03-A
decoded (loose file is tens of KB; packed copy is multi-MB).
That is why BornBeast was absent from the loose Bute layer.

### 3.2 Unique Weapon records that bind BornBeast

| WeaponName (GBK) | StandardName | PViewModelFileName | PViewSkinFileName |
|---|---|---|---|
| `M4A1-黑骑士` | `M4A1_S_BornBeast` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `王者之势` | `M4A1_BornBeast_NobleGold` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_BornBeast_NobleGold.dtx` |
| `源·黑骑士` | `M4A1_S_BornBeast` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `M4A1-仙界-黑骑士` | `M4A1_S_BornBeast_BeijingOpera` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_BeijingOpera.dtx` |
| `黑骑士-网吧专属` | `M4A1_S_BornBeast_Prime_PCCafe` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_Prime_PCCafe.dtx` |
| `黑骑士-摸金校尉` | `M4A1_S_BornBeast_LongLingMiKu` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_LongLingMiKu.dtx` |
| `御·黑骑士·哪吒闹海` | `M4A1_S_BornBeast_Nezha` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_Nezha.dtx` |
| `M4A1-黑骑士-网吧特权` | `M4A1_S_BornBeast_PC` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_PC.dtx` |
| `步枪6` | `²½Ç¹6` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `步枪Max` | `²½Ç¹Max` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_BornBeast_NobleGold.dtx` |
| `魂·黑骑士-现代金属` | `M4A1_S_BornBeast_Modern` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_Modern.dtx` |
| `魂·黑骑士-幻能朋克` | `M4A1_S_BornBeast_PurplePunk` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast_PurplePunk.dtx` |
| `M4A1-黑骑士-高校特权` | `M4A1_S_BornBeast` | `Models\PlayerView\PV-M4A1_S_BornBeast` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |

Deduped exact field binds (role collapsed):

| identity (GBK) | field | value |
|---|---|---|
| `M4A1-黑骑士` | `StandardName` | `M4A1_S_BornBeast` |
| `M4A1-黑骑士` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `M4A1-黑骑士` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `M4A1-黑骑士` | `BigIconName` | `M4A1_S_BornBeast` |
| `王者之势` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `源·黑骑士` | `StandardName` | `M4A1_S_BornBeast` |
| `源·黑骑士` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `源·黑骑士` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `M4A1-仙界-黑骑士` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `黑骑士-网吧专属` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `黑骑士-摸金校尉` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `御·黑骑士·哪吒闹海` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `M4A1-黑骑士-网吧特权` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `步枪6` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `步枪6` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `步枪6` | `BigIconName` | `M4A1_S_BornBeast` |
| `步枪Max` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `魂·黑骑士-现代金属` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `魂·黑骑士-幻能朋克` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `M4A1-黑骑士-高校特权` | `StandardName` | `M4A1_S_BornBeast` |
| `M4A1-黑骑士-高校特权` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1_S_BornBeast` |
| `M4A1-黑骑士-高校特权` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx` |
| `M4A1-黑骑士-高校特权` | `BigIconName` | `M4A1_S_BornBeast` |

### 3.3 Text-token context (cap 40)

| file | token_kind | token | role | context |
|---|---|---|---|---|
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `geometry` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `basename` | `PV-M4A1_S_BornBeast.DTX` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\PVMo` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | `wSkinFileName "ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx" )  (PViewRenderStyleFileName "RS\\` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |
| `Butes/BF005.LTC` | `stem` | `PV-M4A1_S_BornBeast` | `base_dtx` | ` (PViewModelFileName "Models\PlayerView\PV-M4A1_S_BornBeast" )  (PViewSkinFileName "ModelTextures\P` |

## 4. Remaining ambiguity

- Loose `rez/Butes/bf005.ltc` miss remains (N03-A); the consumer lives
  in the **packed** `RB001.REZ` copy, which is a different payload.
- Canonical bind is `M4A1-黑骑士` / `StandardName=M4A1_S_BornBeast`
  → `PViewModelFileName=PV-M4A1_S_BornBeast`
  → `PViewSkinFileName=PV-M4A1_S_BornBeast.dtx`.
  Those two paths are the N03-A SHA-verified inventory geometry + base_dtx.
- Family variants reuse the same LTB with **other** DTX names;
  those DTX are not the P4 inventory `base_dtx`.
- Alpha / Normal / Specular TGA and WeaponShader CFG are **not**
  file-path fields on these Weapon records. `StandardName` /
  `BigIconName` equal the CFG stem, which is an alias, not a CFG path.
- LTB piece → DTX/TGA still `OPEN_UNRESOLVED`.
- CFG/render semantic closure still `OPEN_UNRESOLVED`.
- This does **not** identify P5 雷神 and is **not** P4-M01 PASS.

### Confidence: `HIGH`

## 5. Status

**status**: `BORNBEAST_CONSUMER_CONFIRMED`

## 6. Scope guard

- did NOT announce P4-M01 PASS
- did NOT treat WeaponShader `.cfg` as consumer
- did NOT scan `.dat` / `.dtx` / `.bin` / `.ltb` / non-BUTES `.ltc`
- did NOT reverse DLL / EXE / FXO
- did NOT use filename similarity as proof
- did NOT freeze CFG shader semantics
- did NOT modify historical accepted evidence or `plan.md`

