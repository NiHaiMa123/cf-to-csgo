# P4-M01-N02-E-R1 — LTB Material Resource Binding Evidence Recovery

- status: **MATERIAL_BINDING_PARTIAL**
- script: `scripts/material_recovery/n02e_r1_material_binding.py`
- consumes: `n02d_r1_path_binding/runtime_path_binding.json`

## 1. LTB extraction

For each (WeaponName, field, full_path) LTB hit from
N02-D-R1, this round:

1. read the LTB bytes from `rez_path` at `data_offset` for
   `size` bytes (REZ directory → payload; same access as the
   LZMA-Alone header expects);
2. verified the LZMA-alone magic (`0x5D` first byte) and
   decompressed with `lzma.decompress(..., FORMAT_ALONE)`;
3. parsed the LTB header using the same offsets as
   `CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs`
   (LtbCommandLineLengthOffset=84, LtbFirstMeshOffset=86+12);
4. scanned the decompressed body for `(lt-model`, `(piece`,
   `(texture`, `(renderstyle`, `(material`, `(string`, `.dtx`,
   `.tga` substrings;
5. extracted every (uint16 length + ASCII name) record
   that satisfies the Jupiter mesh/bone/animation name
   convention (3-64 chars, alnum + `-_/\. `, at least one
   uppercase letter).

## 2. Per-LTB result table

| WeaponName | field | ltb_class | rez_path | name | size | LZMA ok | header.cmdline | mesh | bone | anim | inline material |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `M4A1` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1.LTB` | 16,558 | True | 0 | 0 | 1 | 0 | NO |
| `M4A1` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `M4A1-B` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1.LTB` | 16,558 | True | 0 | 0 | 1 | 0 | NO |
| `M4A1-B` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1-B` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1-B` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `M4A1-A` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `M4A1-A` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1-A` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1-A` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `M4A1-S` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `M4A1-S` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1-S` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1-S` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `M4A1-QQ»áÔ±` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1-QQ»áÔ±` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `M4A1-Custom` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1-CUSTOM.LTB` | 29,576 | True | 0 | 0 | 1 | 0 | NO |
| `M4A1-Custom` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1-CUSTOM.LTB` | 64,927 | True | 0 | 3 | 51 | 4 | NO |
| `M4A1-Custom` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `M4A1-Custom` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `»Æ½ðM4A1` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1.LTB` | 16,558 | True | 0 | 0 | 1 | 0 | NO |
| `»Æ½ðM4A1` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `»Æ½ðM4A1` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `»Æ½ðM4A1` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `ÇàÍ­M4A1-A` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `ÇàÍ­M4A1-A` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `ÒøÉ«M4A1-A` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `ÒøÉ«M4A1-A` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |
| `Ë®¾§M4A1-A` | `ModelFileName` | weapon | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | True | 0 | 1 | 1 | 0 | NO |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | weapon | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | True | 0 | 3 | 51 | 4 | NO |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | render_style | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | True | None | 0 | 0 | 0 | NO |
| `Ë®¾§M4A1-A` | `PViewRenderStyleFileName` | render_style | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | True | None | 0 | 0 | 0 | NO |

## 3. Per-LTB inline-keyword scan (decompressed body)

### 3.1 `WEAPONS/M4A1.LTB`

- size (compressed): 16,558 bytes
- lzma_decompress: `lzma-alone ok (16558 -> 34174 bytes)`
- decompressed byte count: 34,174
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 33823 | 10 | other | `Scene Root` |
| 33906 | 6 | bone_candidate | `Bone09` |
| 34009 | 7 | other | `Swat_BL` |

### 3.2 `PLAYERVIEW/PV-M4A1.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.3 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.4 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.5 `WEAPONS/M4A1.LTB`

- size (compressed): 16,558 bytes
- lzma_decompress: `lzma-alone ok (16558 -> 34174 bytes)`
- decompressed byte count: 34,174
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 33823 | 10 | other | `Scene Root` |
| 33906 | 6 | bone_candidate | `Bone09` |
| 34009 | 7 | other | `Swat_BL` |

### 3.6 `PLAYERVIEW/PV-M4A1.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.7 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.8 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.9 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.10 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.11 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.12 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.13 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.14 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.15 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.16 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.17 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.18 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.19 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.20 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.21 `WEAPONS/M4A1-CUSTOM.LTB`

- size (compressed): 29,576 bytes
- lzma_decompress: `lzma-alone ok (29576 -> 78625 bytes)`
- decompressed byte count: 78,625
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 2, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 10 | other | `Cylinder01` |
| 51605 | 8 | other | `L-M4-A02` |
| 78272 | 10 | other | `Scene Root` |
| 78355 | 6 | bone_candidate | `Bone01` |
| 78458 | 8 | other | `baseAnim` |

### 3.22 `PLAYERVIEW/PV-M4A1-CUSTOM.LTB`

- size (compressed): 64,927 bytes
- lzma_decompress: `lzma-alone ok (64927 -> 238249 bytes)`
- decompressed byte count: 238,249
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.23 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.24 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.25 `WEAPONS/M4A1.LTB`

- size (compressed): 16,558 bytes
- lzma_decompress: `lzma-alone ok (16558 -> 34174 bytes)`
- decompressed byte count: 34,174
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 33823 | 10 | other | `Scene Root` |
| 33906 | 6 | bone_candidate | `Bone09` |
| 34009 | 7 | other | `Swat_BL` |

### 3.26 `PLAYERVIEW/PV-M4A1.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.27 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.28 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.29 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.30 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.31 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.32 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.33 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.34 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.35 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.36 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.37 `WEAPONS/M4A1_SILENCER.LTB`

- size (compressed): 16,926 bytes
- lzma_decompress: `lzma-alone ok (16926 -> 35330 bytes)`
- decompressed byte count: 35,330
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 1, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 8 | other | `L-M4-A02` |
| 34967 | 10 | other | `Scene Root` |
| 35050 | 6 | bone_candidate | `Bone09` |
| 35153 | 13 | mesh_candidate | `M4A1_SILENCER` |

### 3.38 `PLAYERVIEW/PV-M4A1_SILENCER.LTB`

- size (compressed): 64,777 bytes
- lzma_decompress: `lzma-alone ok (64777 -> 236863 bytes)`
- decompressed byte count: 236,863
- header: {'ltb_class': 'weapon', 'command_line_length': 0, 'command_line_text': '', 'mesh_count_offset': 94, 'first_mesh_offset': 98, 'mesh_count': 5, 'header_grade': 'STRUCTURALLY_VERIFIED'}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

Mesh/bone/anim names (first 20):

| offset | length | kind | name |
|---|---|---|---|
| 98 | 11 | mesh_candidate | `Fview-hand2` |
| 68459 | 10 | mesh_candidate | `Fview-arm2` |
| 78975 | 5 | mesh_candidate | `M4-A1` |
| 171955 | 10 | other | `Scene Root` |
| 172038 | 10 | bone_candidate | `FvARM-bone` |
| 172121 | 17 | bone_candidate | `FvARM-bone Pelvis` |
| 172211 | 16 | bone_candidate | `FvARM-bone Spine` |
| 172300 | 17 | bone_candidate | `FvARM-bone Spine1` |
| 172390 | 15 | bone_candidate | `FvARM-bone Neck` |
| 172478 | 21 | bone_candidate | `FvARM-bone L Clavicle` |
| 172572 | 21 | bone_candidate | `FvARM-bone L UpperArm` |
| 172666 | 20 | bone_candidate | `FvARM-bone L ForeArm` |
| 172759 | 17 | bone_candidate | `FvARM-bone L Hand` |
| 172849 | 20 | bone_candidate | `FvARM-bone L Finger0` |
| 172942 | 21 | bone_candidate | `FvARM-bone L Finger01` |
| 173036 | 21 | bone_candidate | `FvARM-bone L Finger02` |
| 173130 | 20 | bone_candidate | `FvARM-bone L Finger1` |
| 173223 | 21 | bone_candidate | `FvARM-bone L Finger11` |
| 173317 | 21 | bone_candidate | `FvARM-bone L Finger12` |
| 173411 | 20 | bone_candidate | `FvARM-bone L Finger2` |

### 3.39 `RS/NINJATRANSLUCENT.LTB`

- size (compressed): 111 bytes
- lzma_decompress: `lzma-alone ok (111 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

### 3.40 `RS/PVMODELDEFAULT.LTB`

- size (compressed): 119 bytes
- lzma_decompress: `lzma-alone ok (119 -> 645 bytes)`
- decompressed byte count: 645
- header: {'ltb_class': 'render_style', 'command_line_length': None, 'command_line_text': '', 'mesh_count_offset': None, 'first_mesh_offset': None, 'mesh_count': None, 'header_grade': 'N/A_RENDER_STYLE_BLOCK', 'note': "RS/*.LTB is a render-style / shader config block, not a Jupiter mesh model.  CFRezManager's LithTechModelDecoder mesh-count header offsets do not apply; the 645-byte decompressed body is opaque shader data without ASCII mesh/bone/animation names."}
- inline_binding_evidence: NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — Jupiter LTB standard has no LTA piece/material atoms; any material binding must be reconstructed from external evidence
- inline_keyword_hits: none

## 4. Status & next investigation

**status**: `MATERIAL_BINDING_PARTIAL`

- LTB internal piece / material / texture / renderstyle
  atoms are **not present** in any of the 8 LTB hits.
  This is consistent with the Jupiter LTB standard
  (LTB = compressed binary model file; the LTA piece
  table is a separate consumer artefact, not a section
  of the LTB).
- The closest runtime semantic for the LTB-internal
  mesh is the (uint16 length, ASCII name) record set
  we extracted.  Examples: `Fview-hand2`, `Fview-arm2`,
  `M4-A1` (meshes), `Bone02`..`Bone06`, `BaseTracker`
  (bones), `WeaponReload`, `WeaponClipOut`,
  `WeaponClipIn`, `WeaponFinish` (animations).
- LTB-internal piece->DTX/TGA material binding is
  **OPEN_UNRESOLVED** in scope: the LTB does not name
  any DTX/TGA inline, and the runtime-side
  reconstruction is consumer-inferred from the bf005
  (ModelFileName, SkinFileName) / (PViewModelFileName,
  PViewSkinFileName) pairing.
- The next single highest-value target is to verify
  the consumer-inferred material pairing by reading
  the BF005 weapon record's `RenderStyleFileName`
  payload (RS/*.LTB) and correlating it with the LTB
  render-style block, which would be the smallest
  step that converts a consumer inference into a
  decoded evidence.  Out of scope for this round.

## 5. Scope guard

- did read LTB bytes (5-byte LZMA props + compressed
  payload) for the 8 N02-D-R1 hits; this is the same
  payload that `studiomdl` / runtime consumer would
  read; no other REZ bytes were read.
- did NOT decompile / strings / xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT modify `plan.md`
- did NOT enter P5 identity confirmation
- did NOT announce P4-M01 PASS
- did NOT freeze CFG shader semantics
- did NOT treat filename similarity as proof
