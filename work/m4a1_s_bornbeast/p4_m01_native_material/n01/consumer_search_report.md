# N01 Phase 1 — Consumer search report

## Scope

Reproduce the call/data paths of the repo's own texture/config/mapping/
index/resolver stack on the local `data/` corpus, focused on the four
weapons `M4A1_S_BornBeast`, `M4A1_S_Transformers`, `M4A1_S_Jewelry`,
and the simpler control `M4A1_S_BlueDiamond`.

## Consumer candidates examined

1. `LithTechModelTextureConfigIndex.CreateResolver` — builds a config
   index from .cfg/.ini/.txt and resolves a model-name query to a list
   of textures by the per-line scorer (base/diffuse +100, aux -80,
   lobbycube/gold_map/black_shader -120, name-overlap +25).
2. `LithTechTextureMappingScanner.FindGlobalMappingTableCandidates` —
   scans for files containing both texture extension references and
   binding keywords with formula `model*8 + texture*3 + keyword*10` plus
   path bonuses.
3. `LithTechDatTextureReferenceIndex.ExtractTextureReferences` —
   raw-byte LZMA-or-direct scan for texture-extension anchors within
   .dat world files.
4. `CfgTextDecoder.TryDecode` — WeaponShader/*.CFG route. Tries structured
   text -> Rez-phase -> enc-text -> CfgBinaryStripDecoder.TryDetect. The
   weapon strips all match the binary-strip heuristic, so this path yields
   no text sections.
5. `LithTechModelDecoder.FindTexturePath + FindMaterialHints` — mesh-level
   parser, but only consumes .lta; BornBeast PV is .ltb binary, so this
   consumer cannot resolve weapon material on it.

## Text-config resolver hits per weapon

### BornBeast (M4A1_S_BornBeast)
keys tried: `['M4A1_S_BornBeast']`
text-config hits: 6
- `_ALL_` -> `s`
- `_ALL_` -> `c`
- `_ALL_` -> `a`
- `_ALL_` -> `n`
- `_ALL_` -> `e`
- `_ALL_` -> `d`

### Transformers (M4A1_S_Transformers)
keys tried: `['M4A1_S_Transformers']`
text-config hits: 6
- `_ALL_` -> `s`
- `_ALL_` -> `c`
- `_ALL_` -> `a`
- `_ALL_` -> `n`
- `_ALL_` -> `e`
- `_ALL_` -> `d`

### Jewelry (M4A1_S_Jewelry)
keys tried: `['M4A1_S_Jewelry']`
text-config hits: 6
- `_ALL_` -> `s`
- `_ALL_` -> `c`
- `_ALL_` -> `a`
- `_ALL_` -> `n`
- `_ALL_` -> `e`
- `_ALL_` -> `d`

### M4A1_S_BlueDiamond (M4A1_S_BlueDiamond)
keys tried: `['M4A1_S_BlueDiamond']`
text-config hits: 6
- `_ALL_` -> `s`
- `_ALL_` -> `c`
- `_ALL_` -> `a`
- `_ALL_` -> `n`
- `_ALL_` -> `e`
- `_ALL_` -> `d`

## Raw-needle scan

Scanned every .cfg/.ini/.txt/.dat/.lta in local `data/` (excluding
low-value/UI/radio paths) for the literal weapon stems.

### BornBeast: 4 files
- `out/PV-M4A1_S_BornBeast_Classic_BL_mapping_candidates.txt` — `urces - Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic_BL.LTB  Most Likely Mapping Files - score 150: M`
- `out/PV-M4A1_S_BornBeast_Classic_BL_texture_report.txt` — ` Source: Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic_BL.LTB Mesh: Fview-hand2   Reference: <none>   I`
- `out/PV-M4A1_S_BornBeast_Classic_mapping_candidates.txt` — `urces - Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic.LTB  Most Likely Mapping Files - score 150: Mode`
- `out/PV-M4A1_S_BornBeast_Classic_texture_report.txt` — ` Source: Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic.LTB Mesh: Fview-hand2   Reference: <none>   Infe`

## Findings (high-level)

- The repo's consumer stack is **basename/name-driven**: every index/scanner
  resolves textures by stem + extension + token match, never by mesh
  post-mesh digit or by WeaponShader CFG contents.
- On .lta meshes the mesh-level `FindTexturePath` consumer fires, but
  BornBeast weapon is .ltb binary which the LTB parser doesn't expose
  texture bindings from.
- On .dat worlds the `ExtractTextureReferences` consumer can name textures,
  but we found 0 BornBeast/Transformers/Jewelry needle hits inside
  local dat corpus (only 67 .dat files; CTY/world tables, not weapon
  binding tables).
- On .cfg side, all 237 WeaponShader/*.CFG files match the binary-strip
  heuristic and never reach the structured-text path. No file in the local
  corpus (config-like scanned by R1 stage-2 binding: 355 files) explicitly
  mentions BornBeast/Transformers/Jewelry weapon paths or CFG stems as a
  binding key. The structured-text resolvers produced 0 hits for any of the
  four targets.

## Implication for Phase 2

Because no in-corpus config-side key was found, Phase 2 must rely on
structural/differential evidence from the four weapon families (BornBeast,
Transformers, Jewelry, BlueDiamond) — same LTB geometry (when SHA matches)
different DTX/TGA/CFG; same skin name, different DTX/TGA bytes — to surface
the binding chain from the *engine-resource direction* (mesh → texture file)
that the repo's exporter pipeline assumes (see `LithTechObjExporter.
EnumerateTextureCandidates`).