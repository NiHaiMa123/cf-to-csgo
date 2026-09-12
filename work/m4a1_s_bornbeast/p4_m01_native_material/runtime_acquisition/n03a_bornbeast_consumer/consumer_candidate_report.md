# P4-M01-N03-A — BornBeast Consumer Path Discovery

- status: **CANDIDATE_ONLY**
- confidence: **MEDIUM**
- script: `scripts/material_recovery/n03a_bornbeast_consumer.py`
- consumes: `evidence/native_material_inventory.json` + N02-B-R1 LTC decoder + N02-D-R1 REZ index + N02-A config inventory
- elapsed: 21.66s

## 1. Question

```text
BornBeast inventory asset
  -> runtime/config consumer
  -> REZ/resource path
  -> payload identity
```

Reverse lookup uses **exact** filename / path / hash tokens from the
P4 native inventory.  Bounded-token matching rejects a token that is
only a prefix of a longer identifier.  Filename similarity is not proof.

## 2. Inventory tokens

| asset_role | relative_path | rez_logical_path | sha256 | local_md5 |
|---|---|---|---|---|
| `geometry` | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` | `PLAYERVIEW/PV-M4A1_S_BORNBEAST.LTB` | `5dbcee45c4565b20…` | `DD6FEDDA6821F4A2…` |
| `base_dtx` | `data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` | `PLAYERVIEW/PV-M4A1_S_BORNBEAST.DTX` | `c419a5fb164db608…` | `8C340529FA3E942E…` |
| `alpha` | `data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA` | `ALPHAMAP/M4A1_S_BORNBEAST_ALPHA.TGA` | `40b2c94361b5db58…` | `BE831ACCA67173E3…` |
| `normal` | `data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA` | `NORMALMAP/M4A1_S_BORNBEAST_N.TGA` | `4b9d3eb4c5d71b6b…` | `9D82476E4BA1E3EA…` |
| `specular` | `data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA` | `SPECULARMAP/M4A1_S_BORNBEAST_S.TGA` | `c0815faec0d55307…` | `BE5F854A9BE39438…` |
| `shader_cfg` | `data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG` | `SHADER/WEAPONSHADER/M4A1_S_BORNBEAST.CFG` | `78f0bd5024f70624…` | `F179D3739F62E254…` |

- exact tokens emitted: **36** (basename/stem/rez_path/source_path/sha256/md5 per item)
- family-name substring `BornBeast` is **not** used as consumer proof

## 3. Config search scope

| metric | count |
|---|---|
| config files searched | 107 |
| skipped | 0 |
| .ltc decode OK | 73 |
| .ltc decode fail | 0 |
| parsed lisp records | 7337 |
| DIRECT_CONFIG_FIELD hits | 0 |
| decoded-text path/stem hits | 0 |
| hash-hex text hits | 0 |

### 3.1 Direct config field hits

**None.** No parsed Bute/LTC field value exact-matches a BornBeast
inventory basename, stem, or logical path.  This includes every
key (not only N02-B BINDING_FIELDS) across every successfully
decoded `rez/Butes/*.ltc`.

### 3.2 Bounded text-token hits

**None** in decoded LTC text or string-scanned `.lta/.ini/.cfg`.
This reconfirms N02-B-R1's family-substring negative, now at
exact inventory-token granularity, and extends it to the rest
of the N02-A config-role set plus `rez/Butes/` directory files.

## 4. Runtime REZ reverse lookup

| metric | count |
|---|---|
| REZ archives indexed | 475 |
| total REZ file entries | 252505 |
| unique full paths | 243508 |
| exact-path hits (all assets) | 7 |
| payload SHA256 matches | 8 |

| asset_role | rez_logical_path | exact_path | basename_only | sha_match |
|---|---|---|---|---|
| `geometry` | `PLAYERVIEW/PV-M4A1_S_BORNBEAST.LTB` | 3 | 0 | 3 |
| `base_dtx` | `PLAYERVIEW/PV-M4A1_S_BORNBEAST.DTX` | 1 | 0 | 1 |
| `alpha` | `ALPHAMAP/M4A1_S_BORNBEAST_ALPHA.TGA` | 1 | 0 | 1 |
| `normal` | `NORMALMAP/M4A1_S_BORNBEAST_N.TGA` | 1 | 0 | 1 |
| `specular` | `SPECULARMAP/M4A1_S_BORNBEAST_S.TGA` | 1 | 0 | 1 |
| `shader_cfg` | `SHADER/WEAPONSHADER/M4A1_S_BORNBEAST.CFG` | 0 | 1 | 1 |

### 4.1 Payload SHA256 checks

| asset_role | query | archive | full_path | size | sha_match | note |
|---|---|---|---|---|---|---|
| `geometry` | `EXACT_PATH` | `rez/RF016.REZ` | `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` | 166113 | YES | `payload SHA256 == inventory SHA256` |
| `geometry` | `EXACT_PATH` | `rez2/RF016.REZ` | `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` | 166113 | YES | `payload SHA256 == inventory SHA256` |
| `geometry` | `EXACT_PATH` | `rez4/RF016.REZ` | `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` | 166113 | YES | `payload SHA256 == inventory SHA256` |
| `base_dtx` | `EXACT_PATH` | `rez/rf017.rez` | `PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` | 524452 | YES | `payload SHA256 == inventory SHA256` |
| `alpha` | `EXACT_PATH` | `rez/rf017.rez` | `AlphaMap/M4A1_S_BornBeast_alpha.TGA` | 3145772 | YES | `payload SHA256 == inventory SHA256` |
| `normal` | `EXACT_PATH` | `rez/rf017.rez` | `NormalMap/M4A1_S_BornBeast_N.TGA` | 3145772 | YES | `payload SHA256 == inventory SHA256` |
| `specular` | `EXACT_PATH` | `rez/rf017.rez` | `SpecularMap/M4A1_S_BornBeast_S.TGA` | 3145772 | YES | `payload SHA256 == inventory SHA256` |
| `shader_cfg` | `BASENAME_SIZE_FILTER` | `rez/rf017.rez` | `WeaponShader/M4A1_S_BornBeast.CFG` | 492 | YES | `payload SHA256 == inventory SHA256` |

Basename-only REZ hits are **existence candidates**, not consumer
proof, and are not treated as BornBeast identity.

The `shader_cfg` inventory path normalises to
`SHADER/WEAPONSHADER/M4A1_S_BORNBEAST.CFG` after stripping the
`ModelTextures/` virtual root.  The runtime copy lives at
`WeaponShader/M4A1_S_BornBeast.CFG` (no `Shader/` prefix).
That is a **path-normalisation miss**, not a missing file: the
basename+size filter hashed it and SHA256 still matches.

## 5. Confirmed relations / remaining ambiguity

### Confirmed

- `bf005` M4A1 runtime family is **not** BornBeast
  (`SCOPED_NEGATIVE_ACCEPTED`, N02-E-R2).
- 8 runtime REZ payload(s) byte-equal the BornBeast inventory SHA256 (`PAYLOAD_IDENTITY`).

### Remaining ambiguity

- LTB piece → DTX/TGA binding is still `OPEN_UNRESOLVED`
  (N02-E-R1; this round did not re-open LTB internals).
- CFG / render-style semantic closure is still `OPEN_UNRESOLVED`.
- No decoded `rez/Butes/*.ltc` (or other N02-A config-role file)
  names a BornBeast inventory asset.  The consumer table for
  this skin is **not** in the currently decoded Bute layer.
  Remaining places it could live, in rising cost:
  1. a config packed *inside* a REZ (not the loose `rez/Butes` files);
  2. a non-text item/skin catalog (CFT/CSV/DAT) not in N02-A config scope;
  3. a server-side or numeric-ID bind with no filename on disk;
  4. PE/strings consumer tracing (explicitly out of this task).

### Confidence: `MEDIUM`

Exact-token reverse lookup over the declared config set and the
path-aware REZ index.  A miss in this set is a scoped negative,
not a global 'BornBeast has no runtime entry' claim.

## 6. Status

**status**: `CANDIDATE_ONLY`

## 7. Scope guard

- did NOT announce P4-M01 PASS
- did NOT treat bf005 M4A1 bindings as BornBeast identity
- did NOT reverse DLL / EXE / FXO
- did NOT run a full-disk scan; config set = N02-A config-role
  files ∪ `rez/Butes/` directory listing
- did NOT use filename similarity as proof
- did NOT freeze CFG shader semantics
- did NOT modify historical accepted evidence or `plan.md`

