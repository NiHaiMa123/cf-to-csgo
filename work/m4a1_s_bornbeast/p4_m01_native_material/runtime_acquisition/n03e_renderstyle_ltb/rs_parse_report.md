# P4-M01-N03-E — RenderStyle LTB parse

- status: **RENDERSTYLE_STRUCTURAL**
- confidence: **HIGH**
- script: `scripts/material_recovery/n03e_renderstyle_ltb.py`
- reference: `jsj2008/lithtech/.../d3d_renderstyle.cpp` Load_LTBData
- elapsed: 0.00s

## `RS/NINJATRANSLUCENT.LTB`

- archive: `rez/rf002.rez`
- compressed 111 → decompressed 645
- parse status: **RENDERSTYLE_STRUCTURAL**

| field | value |
|---|---|
| fileType | 5 (want 5) ok=True |
| version @2 | 3 (want 3) ok=True |
| byte1 | 0xf3 |
| iTotalSize | 605 |
| iRenStyleCnt | 1 |
| iSize | 605 |
| iRenderPasses | 1 |

LightingMaterial (Ambient/Diffuse/Emissive/Specular rgb):

| channel | r | g | b | a |
|---|---|---|---|---|
| Ambient | 0.3922 | 0.3922 | 0.3922 | 1.0000 |
| Diffuse | 0.3922 | 0.3922 | 0.3922 | 1.0000 |
| Emissive | 0.1176 | 0.1176 | 0.1176 | 1.0000 |
| Specular | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| SpecularPower | 0.0000 | | | |

Best stage layout: packed=False score=7 leftover=8

| pass | stage | TextureParam | ColorOp | BlendMode |
|---|---|---|---|---|
| 0 | 0 | `RENDERSTYLE_USE_TEXTURE1` | 4 | `BLEND_MOD_SRCALPHA` |
| 0 | 1 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |
| 0 | 2 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |
| 0 | 3 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |

TextureParam is a **slot selector**, not a filename.

### String scan

**No** `.cfg` / `.fx` / `.tga` / `.dtx` / `WeaponShader` strings.

## `RS/PVMODELDEFAULT.LTB`

- archive: `rez/rf002.rez`
- compressed 119 → decompressed 645
- parse status: **RENDERSTYLE_STRUCTURAL**

| field | value |
|---|---|
| fileType | 5 (want 5) ok=True |
| version @2 | 3 (want 3) ok=True |
| byte1 | 0x76 |
| iTotalSize | 605 |
| iRenStyleCnt | 1 |
| iSize | 605 |
| iRenderPasses | 1 |

LightingMaterial (Ambient/Diffuse/Emissive/Specular rgb):

| channel | r | g | b | a |
|---|---|---|---|---|
| Ambient | 0.2745 | 0.2745 | 0.2745 | 1.0000 |
| Diffuse | 0.6275 | 0.6275 | 0.6275 | 1.0000 |
| Emissive | 0.0196 | 0.0196 | 0.0196 | 1.0000 |
| Specular | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| SpecularPower | 255.0000 | | | |

Best stage layout: packed=False score=7 leftover=8

| pass | stage | TextureParam | ColorOp | BlendMode |
|---|---|---|---|---|
| 0 | 0 | `RENDERSTYLE_USE_TEXTURE1` | 4 | `BLEND_MOD_SRCALPHA` |
| 0 | 1 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |
| 0 | 2 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |
| 0 | 3 | `RENDERSTYLE_NOTEXTURE` | 0 | `BLEND_MOD_SRCALPHA` |

TextureParam is a **slot selector**, not a filename.

### String scan

**No** `.cfg` / `.fx` / `.tga` / `.dtx` / `WeaponShader` strings.

## Jupiter vs CF delta

- Outer wrapper is LZMA-alone (`5d`), same as model LTB.
- Header is the 20-byte aligned `LTB_Header` used on the PV model:
  `fileType` at 0, `uint16 version` at 2. For RS, `fileType=5` and
  version=3 (`RENDERSTYLE_D3D_VERSION`). Byte 1 is non-zero on these
  files (CF reserved); model LTB had 0 pad there.
- No filename table in the RS body.

## Remaining ambiguity

- TextureParam slots are not DTX/TGA paths.
- Both RS files use **one** pass, stage0=`USE_TEXTURE1`, stages 1–3
  `NOTEXTURE`. That matches a single Bute skin DTX, not Alpha/Normal/
  Specular TGA or WeaponShader CFG.
- CFG/render semantic closure still `OPEN_UNRESOLVED`.
- P4-M01 is not PASS. This is not P5 雷神.

### Confidence: `HIGH`

## Status

**status**: `RENDERSTYLE_STRUCTURAL`

## Scope guard

- did NOT announce P4-M01 PASS
- did NOT map TextureParam to DTX/TGA path
- did NOT freeze CFG shader semantics
- did NOT reverse DLL / EXE / FXO
- did NOT scan all RS LTB files
- did NOT modify historical accepted evidence or `plan.md`

