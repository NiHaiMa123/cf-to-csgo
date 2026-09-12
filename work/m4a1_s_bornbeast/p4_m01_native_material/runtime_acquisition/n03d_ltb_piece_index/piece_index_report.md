# P4-M01-N03-D — Jupiter vs CF LTB piece/texture indices

- status: **PIECE_TEXTURE_INDEX_STRUCTURAL**
- confidence: **HIGH**
- script: `scripts/material_recovery/n03d_ltb_piece_index.py`
- reference: `jsj2008/lithtech/runtime/model/src/model_load.cpp` (REFERENCE_IMPLEMENTATION, not CF proof)
- elapsed: 0.37s

## 1. Canonical PV LTB

- archive: `rez/RF016.REZ`
- path: `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB`
- compressed: 166113  decompressed: 725544
- raw magic: `5d000000` (LZMA-alone `5d`)

### 1.1 Jupiter header

| field | value |
|---|---|
| fileType | 1 `LTB_D3D_MODEL_FILE` |
| LTB_Header.version | 9 |
| model fileVersion | 25 |
| header_layout | `aligned_20B_fileType@0_uint16_version@2_fileVersion@20` |
| alloc.nKeyFrames | 320 |
| alloc.nParentAnims | 8 |
| alloc.nNodes | 57 |
| alloc.nPieces | 11 |
| alloc.nChildModels | 1 |
| alloc.nTris | 5342 |
| alloc.nVerts | 3116 |
| alloc.nVertexWeights | 3526 |
| alloc.nLODs | 11 |
| alloc.nSockets | 5 |
| alloc.nWeightSets | 1 |
| alloc.nStrings | 88 |
| alloc.StringLengths | 1339 |
| alloc.VertAnimDataSize | 0 |
| alloc.nAnimData | 510720 |
| command_string | `` |
| vis_radius | 96.0 |
| num_obb | 0 |
| nPieces (stream) | 11 |
| alloc.nPieces match | True |

### 1.2 Best piece-LOD layout (scored CF delta)

- layout: `jupiter_fixed4`  skip_unused=False
- pieces_parsed: 11 / 11
- score: 99

| trial | skip_unused | pieces | score |
|---|---|---|---|
| `jupiter_fixed4` | False | 11 | 99 |
| `counted` | True | 11 | 99 |
| `counted` | False | 11 | 99 |
| `jupiter_fixed4` | True | 11 | 55 |

### 1.3 Pieces

| i | name | nLODs | nNumTextures | iTextures | iRenderStyle | robj_type |
|---|---|---|---|---|---|---|
| 0 | `Fview-hand2` | 1 | 0 | `[0, 1, 0, 1]` | 2 | 0 |
| 1 | `Fview-arm2` | 1 | 0 | `[0, 1, 1, 1]` | 2 | 0 |
| 2 | `M4A1S_BornBeast` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 3 | `M4A1S_BornBeast04` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 4 | `M4A1S_BornBeast02` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 5 | `M4A1S_BornBeast03` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 6 | `M4A1S_BornBeast07` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 7 | `M4A1S_BornBeast08` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 8 | `M4A1S_BornBeast05` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 9 | `M4A1S_BornBeast06` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |
| 10 | `M4A1S_BornBeast01` | 1 | 0 | `[0, 1, 2, 1]` | 2 | 0 |

Texture indices are **slot numbers**, not DTX/TGA paths.
`nNumTextures=0` on every piece: this LTB does not carry extra
texture filenames. The repeating `iTextures` pattern is the fixed
Jupiter array of 4 ints (always written). Runtime PV DTX still
comes from the Bute `PViewSkinFileName` (N03-C), not from these slots.

Winning layout omits Jupiter's deprecated min/max LOD offset
uint32 pair (`skip_unused=False` scores higher). That is a
fileVersion-25 CF delta against `ModelPiece::Load` as written.

## 2. QV LTB differential (rez2 copy, optional)

- archive: `rez2/RF016.REZ` `WEAPONS/QV-M4A1_S_BornBeast.LTB`
- status: **PIECE_TEXTURE_INDEX_STRUCTURAL**
- nPieces: 1
- pieces_parsed: 1

| i | name | nNumTextures | iTextures | iRenderStyle |
|---|---|---|---|---|
| 0 | `QV-M4A1_S_BornBeast` | 0 | `[0, 1, 0, 1]` | 2 |

## 3. Jupiter vs CF delta

- Header: CF matches Jupiter D3D model (`fileType=1`, header version 9)
  with **aligned 20-byte** `LTB_Header` (uint16 version at offset 2),
  then `fileVersion` at 20, then 15 allocation uint32s.
- Outer compression: CF wraps the Jupiter body in LZMA-alone (`5d`).
  Jupiter `Model::Load` does not mention this wrapper.
- Piece names / nPieces match the stream after visRadius/obb.
- `CDIModelDrawable::Load` mesh payload is **not** walked this round;
  subsequent pieces are found by scanning the next uint16 name with
  a plausible `nLODs`. That scan is a CF recovery method, not Jupiter.
- `m_iTextures[i]` is not a filename. No name table was parsed.

## 4. Remaining ambiguity

- Index → DTX/TGA/CFG path still `OPEN_UNRESOLVED`.
- `nNumTextures=0`: LTB piece table does not name Alpha/Normal/
  Specular TGA or WeaponShader CFG.
- CFG/render semantic closure still `OPEN_UNRESOLVED`.
- P4-M01 is not PASS. This is not P5 雷神.

### Confidence: `HIGH`

## 5. Status

**status**: `PIECE_TEXTURE_INDEX_STRUCTURAL`

## 6. Scope guard

- did NOT announce P4-M01 PASS
- did NOT map texture index to DTX/TGA path
- did NOT reverse DLL / EXE / FXO
- did NOT scan all LTB / all REZ
- did NOT freeze CFG shader semantics
- did NOT modify historical accepted evidence or `plan.md`

