# P4-M01-N05-A — decoder / provenance audit

- result: **DECODE_RECOVERED_BINDING_OPEN**
- P4-M01: still **INCOMPLETE**
- generated_at_utc: 2026-09-12T09:17:54.024+00:00
- parent_git_head: `08a4f3cd166b527518bc36521ae28bab13d3603f`
- script: `scripts/material_recovery/n05a_decoder_provenance_audit.py`

## Repro

```text
python scripts/material_recovery/n05a_decoder_provenance_audit.py
```

## 1. Tool control

Synthetic Jupiter DTX (16×16 RGBA32 + 16×16 DXT1) **PASS**.
This only proves the standard header/pixel path in this repo's decoder
and the shared lithtech `dtx_Create` gates. LTB2FBX and Vortigaunt are
one loader lineage, not two independent CF proofs.

- `synthetic_rgba32_16x16`: python=True cfrez=True dtx_Create=True quadrants_python=True
- `synthetic_dxt1_16x16`: python=True cfrez=True dtx_Create=True quadrants_python=True

Local client DTX with a legal Jupiter header: **NO_CURRENT_CLIENT_CONTROL** (scanned 3258 ModelTextures DTX, kept 0).

No current-client positive DTX was found in `data/rf017/ModelTextures` outside the seven targets.

## 2. Input table

| id | loose SHA256 | copies | raw==loose | directory MD5 vs computed |
|---|---|---:|---|---|
| `bornbeast_pv_dtx` | `c419a5fb164d` | 1 | True | rez/rf017.rez:DIFF |
| `bornbeast_qv_dtx` | `ea99c7101708` | 2 | False | rez/rf017.rez:DIFF; rez2/RF017.REZ:match |
| `royaldragon_pv_dtx` | `03e163bc7384` | 1 | True | rez/rf017.rez:DIFF |
| `royaldragon_s_dtx` | `0151b3de34ef` | 1 | True | rez/rf017.rez:DIFF |
| `greenvain_s_dtx` | `df719d20d996` | 1 | True | rez/rf017.rez:DIFF |
| `bornbeast_cfg` | `78f0bd5024f7` | 1 | True | rez/rf017.rez:DIFF |
| `bornbeast_alpha_tga` | `40b2c94361b5` | 1 | True | rez/rf017.rez:DIFF |

Directory MD5 and computed MD5 are recorded separately. A mismatch is not treated as a codec.
`rez/` is not assumed more authoritative than `rez2/` / `rez3/` / `rez4/`.

## 3. Sourced transforms

### bornbeast_pv_dtx

- kind: `dtx`
- logical: `PLAYERVIEW/PV-M4A1_S_BornBeast.DTX`
- loose: `data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX`
- `raw_read`: **FAIL**
- `lzma_alone`: **FAIL** precondition not met; not decompressed
- `crossfire_ltc_wrapper`: **FAIL** precondition not met
- `rezextract_offset4_8_swap`: **FAIL** after swap, offset4=-14977025 offset8=460783386 still not -2/-3/-5
- size-fit combinations (not a codec):
  - leftover 164: payload 524288 could be 512x256x4 BGRA no mip / 1024x512 RGB16 / DXT1 1024x1024 / DXT5 1024x512 / BGR24 512x256 full mip (geometric series = 524288)

### bornbeast_qv_dtx

- kind: `dtx`
- logical: `WEAPONS/QV-M4A1_S_BornBeast.DTX`
- loose: `data/rf017/ModelTextures/WEAPONS/QV-M4A1_S_BornBeast.DTX`
- `raw_read`: **FAIL**
- `lzma_alone`: **FAIL** precondition not met; not decompressed
- `crossfire_ltc_wrapper`: **FAIL** precondition not met
- `rezextract_offset4_8_swap`: **FAIL** after swap, offset4=-61697 offset8=-15794177 still not -2/-3/-5
- size-fit combinations (not a codec):
  - leftover 164: payload 32768 could be DXT1 256x256 / RGB565 128x128 / 8-bit 256x128
- divergent copy `rez2/RF017.REZ` size=524452 sha256=`73a954f8540c`
  - `raw_read`: **OK**
    header: 1024x1024 ver=-5 bpp=4 flags=8 data_offset=164
    pixels python=True cfrez=True preview=`work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05a_decoder_audit/previews/bornbeast_qv_dtx_rez2_RF017_REZ_raw_python.png`
  - `lzma_alone`: **FAIL** precondition not met; not decompressed
  - `crossfire_ltc_wrapper`: **FAIL** precondition not met
  - `rezextract_offset4_8_swap`: **OK**
    header: 1024x1024 ver=-5 bpp=4 flags=8 data_offset=164
    pixels python=True cfrez=True preview=`work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05a_decoder_audit/previews/bornbeast_qv_dtx_rez2_RF017_REZ_raw_python.png`

### royaldragon_pv_dtx

- kind: `dtx`
- logical: `PLAYERVIEW/PV-M4A1_RoyalDragon.DTX`
- loose: `data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_RoyalDragon.DTX`
- `raw_read`: **FAIL**
- `lzma_alone`: **FAIL** precondition not met; not decompressed
- `crossfire_ltc_wrapper`: **FAIL** precondition not met
- `rezextract_offset4_8_swap`: **FAIL** after swap, offset4=-59905 offset8=-15335425 still not -2/-3/-5
- size-fit combinations (not a codec):
  - leftover 164: payload 524288 could be 512x256x4 BGRA no mip / 1024x512 RGB16 / DXT1 1024x1024 / DXT5 1024x512 / BGR24 512x256 full mip (geometric series = 524288)

### royaldragon_s_dtx

- kind: `dtx`
- logical: `SpecularMap/PV-M4A1_RoyalDragon_s.DTX`
- loose: `data/rf017/ModelTextures/SpecularMap/PV-M4A1_RoyalDragon_s.DTX`
- `raw_read`: **FAIL**
- `lzma_alone`: **FAIL** precondition not met; not decompressed
- `crossfire_ltc_wrapper`: **FAIL** precondition not met
- `rezextract_offset4_8_swap`: **FAIL** after swap, offset4=1507072 offset8=385810454 still not -2/-3/-5
- size-fit combinations (not a codec):
  - leftover 164: payload 524288 could be 512x256x4 BGRA no mip / 1024x512 RGB16 / DXT1 1024x1024 / DXT5 1024x512 / BGR24 512x256 full mip (geometric series = 524288)

### greenvain_s_dtx

- kind: `dtx`
- logical: `SpecularMap/PV-DualDE_GreenVein_S.DTX`
- loose: `data/rf017/ModelTextures/SpecularMap/PV-DualDE_GreenVein_S.DTX`
- `raw_read`: **FAIL**
- `lzma_alone`: **FAIL** precondition not met; not decompressed
- `crossfire_ltc_wrapper`: **FAIL** precondition not met
- `rezextract_offset4_8_swap`: **FAIL** after swap, offset4=-15449601 offset8=339869460 still not -2/-3/-5
- size-fit combinations (not a codec):
  - leftover 164: payload 131072 could be DXT1 512x512 / BGRA 256x128 / BGR24 256x170 leftover-ish

### bornbeast_cfg

- kind: `cfg`
- logical: `WeaponShader/M4A1_S_BornBeast.CFG`
- loose: `data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG`
- `raw_read`: **OK** 492-byte / 164 non-FF measurement is structure only; not a LUT or constant-table proof

### bornbeast_alpha_tga

- kind: `tga`
- logical: `AlphaMap/M4A1_S_BornBeast_alpha.TGA`
- loose: `data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA`
- `raw_read`: **FAIL** implausible type fields (cmap=0 type=255)
- `inserted_footer_header_repair`: **OK** repair success is TGA container evidence, not DTX albedo and not shader-role proof

## 4. Failure layers

- provenance copies: QV DTX logical path has distinct copies: rez/rf017.rez 32932B sha=ea99c7101708; rez2/RF017.REZ 524452B sha=73a954f8540c
- wrapper / LZMA: LZMA/LTC preconditions not met on the five DTX
- Jupiter / RezExtract header: inventory/`rez/` copies of the five DTX still fail -2/-3/-5; rez2 QV is already a legal Jupiter header (version -5, 1024×1024, DXT1, payload 524288)
- DTX pixels: rez2 `WEAPONS/QV-M4A1_S_BornBeast.DTX` decoded as DXT1 1024×1024 gun-piece atlas (python and CFRezManager agree). PV DTX and `rez/` QV 32932 still unsupported
- TGA repair: inserted-header repair recovered a legal TGA
- CFG semantics: phase structure recorded; semantics OPEN

No extra CF variant codec was invented. The new fact is a **copy difference** on the QV logical path: `rez/` 32932 headerless vs `rez2/` 524452 standard DTX. Offset 4/8 swap still cannot repair the inventory/`rez/` PV or QV samples.
CFG 492/164 remains structure-only.

## 5. Result

**DECODE_RECOVERED_BINDING_OPEN**

Recovered pixels are from `rez2/RF017.REZ` `WEAPONS/QV-M4A1_S_BornBeast.DTX`
(sha256 `73a954f8540cd7660c1a6cc1b65dc240c2421c37909e7a8f35d4e6f789b59965`):
Jupiter DTX version -5, DXT1, 1024×1024, header 164 + payload 524288.
The atlas is a recognizable dark metal / red-energy M4A1-S gun-piece sheet
(serial `M4A1SSQ00083` visible). That is an intermediate visual observation,
not mesh binding and not shader semantics.

Still open:

- runtime load order among `rez/` vs `rez2/` (QV copies are not byte-identical)
- first-person `PViewSkinFileName` PV DTX remains headerless
- piece → sampler bind
- WeaponShader CFG consumer

The available local OBJ is first-person PV. This file is `SkinFileName` / QV,
so it was not UV-wrapped onto the PV mesh. P4-M01 remains INCOMPLETE.
No N05-B and no process dump from this round.

