# N01 Phase 1 — Consumer search report

Schema: `cf2.p4m01.n01.consumer-candidate.v3`

## Executor provenance

```text
executor_model                = MiniMax-M3
executor_harness             = Claude Code
executor_family              = MiniMax
model_id_source              = CLI flag / N01_EXECUTOR_MODEL env var
commit_footer_model_provenance = NON_AUTHORITATIVE
```

If a field shows `unspecified`, the generator received neither a
`--executor-*` CLI flag nor a `N01_EXECUTOR_*` environment variable
for that field. The generator MUST NOT default to any specific model
identity. The `Co-Authored-By:` trailer of any commit is NEVER
authoritative for actual executor identity.

## Scope

Reproduce the call/data paths of the repo's own texture/config/mapping/
index/resolver stack on the local `data/` corpus, focused on the four
weapons `M4A1_S_BornBeast`, `M4A1_S_Transformers`, `M4A1_S_Jewelry`,
and the simpler control `M4A1_S_BlueDiamond`.

Scan roots: `data/`. Include extensions for raw-needle scan:
`['.cfg', '.dat', '.ini', '.lta', '.txt']`.

Excluded from native-binding accounting (reported separately as
`DERIVED_OUTPUT_HIT`): `data/out/`, `out/`, `work/`, `reports/`, `logs/`.
Also excluded: low-value/UI/radio/lobbynotice paths.

## Scan scope summary (per M2 cleanup: three independent counters)

- **all_files_seen_post_low_value_filter**: **102382** — every file
  (any extension) that survived the low-value/UI/radio path filter
  during `os.walk(data/)`. Includes models, textures, audio banks,
  voice files, etc.
- **config_candidates_seen**: **261** — subset whose
  extension is in CONFIG_EXT (`.cfg/.ini/.txt`) AND
  `is_likely_model_texture_config(rel, ext)` returned True.
- **config_candidates_decoded**: **18** — subset of
  config_candidates_seen whose content decoded as text AND produced
  at least one real `(model_key, [texture_refs])` mapping.
- config_index keys (cfg files with real parsed mappings): 18
- config_index total mapping tuples: 72
- **raw_needle_scope**: **355** files seen, **355** decoded
  (text-decodeable subset).

Each count above is the literal output of one of the three
independent counters in `build_consumer_index()` / `build_corpus()`;
no count is hand-derived.

Regression guards (assertions) executed before reporting:

- no legacy `_ALL_` key in `config_index`;
- no 1-char texture ref under any config entry;
- schema/type guard in `look_up_texture` (string cannot be iterated
  as a texture list);
- `DERIVED_OUTPUT_HIT` rows are reported separately from native
  consumer hits and never count as binding evidence;
- raw-needle scan splits hits into `hits_by_extension`,
  `hits_by_resource_family`, and `hits_by_consumer`;
- three independent scope counters with explicit legend (M2 cleanup);
- `is_config_candidate` is the SINGLE structural predicate that
  gates `config_candidates_seen`, `config_candidates_decoded`,
  and `config_index` (F3 cleanup);
- `len(config_index_keys) == config_candidates_decoded` and
  `config_candidates_decoded <= config_candidates_seen` both
  hold by structural invariant.

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
   .dat world files. Hits reported under `hits_by_consumer.`
4. `CfgTextDecoder.TryDecode` — WeaponShader/*.CFG route. Tries structured
   text -> Rez-phase -> enc-text -> CfgBinaryStripDecoder.TryDetect. The
   weapon strips all match the binary-strip heuristic, so this path yields
   no text sections.
5. `LithTechModelDecoder.FindTexturePath + FindMaterialHints` — mesh-level
   parser, but only consumes .lta; BornBeast PV is .ltb binary, so this
   consumer cannot resolve weapon material on it.

## Text-config resolver hits per weapon

Hits resolved from real parsed mappings only. Each hit is a tuple
`(cfg_path, texture_ref)` where `texture_ref` is a full resource path
of length > 3. The legacy 1-char pseudo-hits produced by the
`_ALL_ -> "scanned"` schema bug have been removed.

### BornBeast (M4A1_S_BornBeast)
keys tried: `['M4A1_S_BornBeast']`
text-config hits: 0

### Transformers (M4A1_S_Transformers)
keys tried: `['M4A1_S_Transformers']`
text-config hits: 0

### Jewelry (M4A1_S_Jewelry)
keys tried: `['M4A1_S_Jewelry']`
text-config hits: 0

### M4A1_S_BlueDiamond (M4A1_S_BlueDiamond)
keys tried: `['M4A1_S_BlueDiamond']`
text-config hits: 0

## Raw-needle scan

Scanned every `.cfg/.dat/.ini/.lta/.txt` in local `data/`
(excluding low-value/UI/radio/lobbynotice paths **and** derived
outputs) for the literal weapon stems.

### Hits by extension (excludes derived outputs)

| target | .cfg | .dat | .ini | .lta | .txt |
|---|---|---|---|---|---|
| BornBeast | 0 | 0 | 0 | 0 | 0 |
| Transformers | 0 | 0 | 0 | 0 | 0 |
| Jewelry | 0 | 0 | 0 | 0 | 0 |
| M4A1_S_BlueDiamond | 0 | 0 | 0 | 0 | 0 |

### Hits by resource family

| target | config_text | model_binary | model_text | world_dat |
|---|---|---|---|---|
| BornBeast | 0 | 0 | 0 | 0 |
| Transformers | 0 | 0 | 0 | 0 |
| Jewelry | 0 | 0 | 0 | 0 |
| M4A1_S_BlueDiamond | 0 | 0 | 0 | 0 |

### Hits by consumer

| target | LithTechDatTextureReferenceIndex | LithTechModelTextureConfigIndex |
|---|---|---|
| BornBeast | 0 | 0 |
| Transformers | 0 | 0 |
| Jewelry | 0 | 0 |
| M4A1_S_BlueDiamond | 0 | 0 |

### Per-target examples (first 5 hits per extension)

#### BornBeast
- `.cfg`: 0 hits
- `.dat`: 0 hits
- `.ini`: 0 hits
- `.lta`: 0 hits
- `.txt`: 0 hits

#### Transformers
- `.cfg`: 0 hits
- `.dat`: 0 hits
- `.ini`: 0 hits
- `.lta`: 0 hits
- `.txt`: 0 hits

#### Jewelry
- `.cfg`: 0 hits
- `.dat`: 0 hits
- `.ini`: 0 hits
- `.lta`: 0 hits
- `.txt`: 0 hits

#### M4A1_S_BlueDiamond
- `.cfg`: 0 hits
- `.dat`: 0 hits
- `.ini`: 0 hits
- `.lta`: 0 hits
- `.txt`: 0 hits

### DERIVED_OUTPUT_HIT (reported separately, NOT a binding evidence)

Hits found in derived outputs (`data/out/`, `out/`, `work/`,
`reports/`, `logs/`). These cannot be used as native-binding
evidence because they are generated by our own tooling / earlier
runs and merely echo file paths back.

#### BornBeast: 4 derived-output hits
- `out/PV-M4A1_S_BornBeast_Classic_BL_mapping_candidates.txt` — `urces - Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic_BL.LTB  Most Likely Mapping Files - score 150: M`
- `out/PV-M4A1_S_BornBeast_Classic_BL_texture_report.txt` — ` Source: Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic_BL.LTB Mesh: Fview-hand2   Reference: <none>   I`
- `out/PV-M4A1_S_BornBeast_Classic_mapping_candidates.txt` — `urces - Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic.LTB  Most Likely Mapping Files - score 150: Mode`
- `out/PV-M4A1_S_BornBeast_Classic_texture_report.txt` — ` Source: Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic.LTB Mesh: Fview-hand2   Reference: <none>   Infe`

#### Transformers: 0 derived-output hits
- (none)

#### Jewelry: 0 derived-output hits
- (none)

#### M4A1_S_BlueDiamond: 0 derived-output hits
- (none)

## Findings (high-level)

- The repo's consumer stack is **basename/name-driven**: every index/scanner
  resolves textures by stem + extension + token match, never by mesh
  post-mesh digit or by WeaponShader CFG contents.
- On .lta meshes the mesh-level `FindTexturePath` consumer fires, but
  BornBeast weapon is .ltb binary which the LTB parser doesn't expose
  texture bindings from.
- On .dat worlds the `ExtractTextureReferences` consumer can name textures,
  but we found 0 BornBeast/Transformers/Jewelry/BlueDiamond needle hits
  inside the local dat corpus (only 67 .dat files; CTY/world tables, not
  weapon binding tables).
- On .cfg side, all 237 WeaponShader/*.CFG files match the binary-strip
  heuristic and never reach the structured-text path. No file in the local
  corpus (config-like scanned by R1 stage-2 binding: 355 files) explicitly
  mentions BornBeast/Transformers/Jewelry/BlueDiamond weapon paths or CFG
  stems as a binding key. The structured-text resolvers produced 0 hits
  for any of the four targets.
- Derived outputs (`data/out/`, `work/`, etc.) that happen to mention the
  weapon stems are now reported as `DERIVED_OUTPUT_HIT` and are NOT
  counted as native-binding evidence.

## Implication for Phase 2

Because no in-corpus config-side key was found, Phase 2 must rely on
structural/differential evidence from the four weapon families (BornBeast,
Transformers, Jewelry, BlueDiamond) — same LTB geometry (when SHA matches)
different DTX/TGA/CFG; same skin name, different DTX/TGA bytes — to surface
the binding chain from the *engine-resource direction* (mesh → texture file)
that the repo's exporter pipeline assumes (see `LithTechObjExporter.
EnumerateTextureCandidates`).
