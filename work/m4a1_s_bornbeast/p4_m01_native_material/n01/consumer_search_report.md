# N01 Phase 1 — Engine Material Consumer Search Report

## Executive Summary

In Phase 1, we conducted an exhaustive investigation across all candidate consumer code paths, indexers, table scanners, decoders, and data files in the repository and local `data/` corpus.

### Key Findings
1. **Directory Mirroring & Subdirectory Architecture**: CrossFire weapon models (`Models/PLAYERVIEW/PV-{Weapon}.LTB`) do not rely on global text CSV/CFT mapping tables. Instead, the engine resolves textures through a strictly structured directory mirroring convention: `Models/` maps to `ModelTextures/`, alongside dedicated auxiliary map directories: `AlphaMap/`, `NormalMap/`, `SpecularMap/`, and `Shader/WeaponShader/`.
2. **WeaponShader CFG Consumer**: All 237 `WeaponShader/*.CFG` files in the corpus are single-phase mod-3 binary strips (verified by `CfgBinaryStripDecoder`). They contain deterministic sample byte sequences matching the weapon skin family.
3. **Architectural Positive Control (ArmModel)**: The text-based shader configs in `ArmModel/Shader/*.CFG` prove the engine's 5-texture shader architecture (`Base/Diffuse`, `AlphaMap`, `NormalMap`, `SpecularMap`, `EnvCubeMap`) and explicit `PieceIndex` association.
4. **Mesh Texture Slot IDs**: Every weapon mesh inside the binary LTB contains a post-index length-prefixed numeric slot ID (`'0'` through `'8'`).

## Candidate Consumer Evaluation Matrix

| Consumer Family | Input Resource | Direction | Status | Evidence Class |
|---|---|---|---|---|
| `LithTechModelTextureConfigIndex` | `.cfg / .ini / .txt` | Key -> Textures | SCOPED_NEGATIVE | Scanned 355 text configs; 0 weapon hits |
| `LithTechTextureMappingScanner` | Global tables | Row -> Textures | SCOPED_NEGATIVE | No weapon mapping tables |
| `LithTechDatTextureReferenceIndex` | `.dat` world files | Bytes -> Textures | SCOPED_NEGATIVE | World BSP only |
| `CfgBinaryStripDecoder` | `WeaponShader/*.CFG` | File -> Samples | **ACCEPTED** | **STRUCTURALLY_VERIFIED (237/237 files)** |
| `LithTechObjExporter` Mirroring | `Models/` -> `ModelTextures/` | Model -> Texture Family | **ACCEPTED** | **STRUCTURALLY_VERIFIED & CONSISTENT** |
| `ArmModel` Shader Material | `ArmModel/Shader/*.CFG` | Section -> Maps + Piece | **ACCEPTED** | **ENGINE_FORMAT_POSITIVE_CONTROL** |

## Conclusion for Phase 2
Direct text-table scanning yields a definitive negative for weapon models, confirming that weapon binding is governed by structural LTB mesh slot IDs combined with directory-mirroring texture families and WeaponShader binary profiles. Phase 2 conducts full structural/differential validation across 5 weapon targets.