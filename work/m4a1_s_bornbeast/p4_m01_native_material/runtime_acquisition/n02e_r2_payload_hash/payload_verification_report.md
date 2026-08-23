# P4-M01-N02-E-R2 — Bounded REZ Payload SHA256 Verification

- status: **MATERIAL_BINDING_PARTIAL**
- script: `scripts/material_recovery/n02e_r2_payload_hash.py`
- consumes: `n02d_r1_path_binding/runtime_path_binding.json` + `evidence/native_material_inventory.json`

## 1. Scope

For every (rez_path, full_path, size, md5) hit in
N02-D-R1's binding closure, this round:

1. recovered `data_offset` from a fresh REZ directory
   walk via `n02d_r1_path_aware_rez_binding.read_rez_index` (cached, one walk per archive);
2. read **bounded bytes** at `data_offset` for `size`
   bytes via `fp.seek + fp.read` — the rest of the REZ
   is never read into memory;
3. computed SHA256 and standard MD5 of the bounded bytes;
4. compared the SHA256 (uppercase hex) against the BornBeast
   P4 baseline inventory by byte equality (not basename);
5. compared standard MD5 against the REZ directory catalog
   MD5 (`directory_md5_sanity`) — informational, not
   interpreted as engine fact, retained to preserve N02-E's
   directory-honesty chain;
6. for multi-archive entries (M4A1-S `SkinFileName` has
   two RF017.REZ copies), recorded whether the distinct
   archive copies byte-match (`duplicate_archive_sha_equal`).

## 2. Verdict counts

| metric | count | meaning |
|---|---|---|
| `binding_total` | 61 | raw (WeaponName, field, hit) triples from N02-D-R1 |
| `unique_payloads` | 24 | unique (rez_path, full_path) after dedup |
| `READ_OK_BORN_BEAST_MATCH` | 0 | runtime payload SHA256 == BornBeast P4 baseline |
| `READ_OK_NO_BORN_BEAST_MATCH` | 24 | runtime payload SHA256 != BornBeast P4 baseline |
| `READ_SKIPPED` | 0 | data_offset missing or read failed |
| `directory_md5_sanity_match` | 9 | standard MD5 of payload == REZ catalog MD5 |
| `directory_md5_sanity_mismatch` | 15 | standard MD5 of payload != REZ catalog MD5 |
| `skipped_oversized_rez` | 0 | skipped due to --skip-oversized-rez (0 if not used) |

- elapsed: 1.13s

## 3. BornBeast inventory snapshot (P4 baseline)

| asset_role | sha256 | size | relative_path |
|---|---|---|---|
| `geometry` | `5dbcee45c4565b2026a4e4d2d639a4b7022b4f4fc1c5ef69bc8f49fd5a6c54f7` | 166,113 | `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB` |
| `base_dtx` | `c419a5fb164db6085878ff2efe21d318a85186b4e3c1fd6baba920311f6ea1d9` | 524,452 | `data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` |
| `alpha` | `40b2c94361b5db58edffb27b8b8aa457667eceb9eb27848135cfee0c17992a37` | 3,145,772 | `data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA` |
| `normal` | `4b9d3eb4c5d71b6bd129f88f108c567251ce260f37dfff4bae2c90073974c28e` | 3,145,772 | `data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA` |
| `specular` | `c0815faec0d553079b38072118ab089f4fe5df79f7db8491fd391d029c3894c6` | 3,145,772 | `data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA` |
| `shader_cfg` | `78f0bd5024f70624594c6b7ebd470094a3642fce8cf7df596407d40dae0ebc87` | 492 | `data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG` |

## 4. Per-payload bounded SHA256 + BornBeast match

| rez | full_path | name | size | sha256 | bb_match | dir_md5 |
|---|---|---|---|---|---|---|
| `RF016.REZ` | `WEAPONS/M4A1.LTB` | `M4A1.LTB` | 16,558 | `F7BFD6FD5FBFB0573F113BFDD5D0C30C7E72C42D6E8C5F84A74B7649AF8B0975` | — | match |
| `rf017.rez` | `WEAPONS/L-M4A1.DTX` | `L-M4A1.DTX` | 32,932 | `38D566ADB963417955B79C37BBACC0DEFB43BE69A307D00D3DE37176A4A84AD8` | — | mismatch |
| `RF016.REZ` | `PLAYERVIEW/PV-M4A1.LTB` | `PV-M4A1.LTB` | 64,777 | `46835DCE53BDDD02FA9C183C3DDE2B515DB60694897DB98322BFF3519B2028DF` | — | match |
| `rf017.rez` | `PLAYERVIEW/PV-M4A1.DTX` | `PV-M4A1.DTX` | 524,452 | `6AE0B7DE74B6DBB016E8999AB478A81BAC462021780899709007F4B516325D13` | — | mismatch |
| `rf002.rez` | `RS/NINJATRANSLUCENT.LTB` | `NINJATRANSLUCENT.LTB` | 111 | `85A8C47E4CFAE2EDF92E921F428DBE78ADAAC87EA295304DFD0860921F98187E` | — | match |
| `rf002.rez` | `RS/PVMODELDEFAULT.LTB` | `PVMODELDEFAULT.LTB` | 119 | `7AAC491CDD91DF513C1B8ED58B0B4FC385039EAF026CC4A18E4A160E91D7F57E` | — | match |
| `RF016.REZ` | `WEAPONS/M4A1_SILENCER.LTB` | `M4A1_SILENCER.LTB` | 16,926 | `F7669417139F7F64C7999BD8D71F632C6C410F48C9ABBAA198A9860B5918F8E3` | — | match |
| `rf017.rez` | `WEAPONS/L-M4A1_SILENCER.DTX` | `L-M4A1_SILENCER.DTX` | 32,932 | `001DF1A187F62BBDACC745376B1780B147C4469DDD8F3B3F24561FC8C0C10799` | — | mismatch |
| `RF016.REZ` | `PLAYERVIEW/PV-M4A1_SILENCER.LTB` | `PV-M4A1_SILENCER.LTB` | 64,777 | `46835DCE53BDDD02FA9C183C3DDE2B515DB60694897DB98322BFF3519B2028DF` | — | match |
| `rf017.rez` | `WEAPONS/L-M4A1_SILENCER_CAMO.DTX` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `48A3BD237592264F8DA4FA913452A64659C514C50DC85EE009E48DE73232F2FC` | — | mismatch |
| `RF017.REZ` | `WEAPONS/L-M4A1_SILENCER_CAMO.DTX` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `20588B4AADA29CE1408CCDA8F547942D41B1E95FA489283CDC5275586D1C16B0` | — | match |
| `rf017.rez` | `PLAYERVIEW/PV-M4A1-CAMO.DTX` | `PV-M4A1-CAMO.DTX` | 524,452 | `BC2DD5691E3D8152B81798A05921D6611855C5B559EC1666EE724779CAC21267` | — | mismatch |
| `rf017.rez` | `WEAPONS/M4A1_QQ.DTX` | `M4A1_QQ.DTX` | 41,124 | `4BC7C5FAA5D84BD1C9370BE454F9F193D98915335C654D12DBD77EDF4A018424` | — | mismatch |
| `rf017.rez` | `PLAYERVIEW/PV-M4A1_QQ.DTX` | `PV-M4A1_QQ.DTX` | 164,004 | `DA4281CE35944DEF3ECE80E45CB3344463D2319EE09C6867459B7B008C1AA9DB` | — | mismatch |
| `RF016.REZ` | `WEAPONS/M4A1-CUSTOM.LTB` | `M4A1-CUSTOM.LTB` | 29,576 | `D81DE88A7F1EEA355C7A7383D16BA2F9DE40D2AFDF065CFEB4AAC1771BF91F10` | — | match |
| `RF016.REZ` | `PLAYERVIEW/PV-M4A1-CUSTOM.LTB` | `PV-M4A1-CUSTOM.LTB` | 64,927 | `CBA7B85BD0E620F5838097E87C7F314BF10B94220C12A2417151F5C04D0F37AE` | — | match |
| `rf017.rez` | `WEAPONS/QV-RI_M4A1_GOLD.DTX` | `QV-RI_M4A1_GOLD.DTX` | 82,084 | `7AC5A024F3B0C7C7C4FD7FCBA8589FF178D7BD9BC38C169E3934FB58DA2F0F83` | — | mismatch |
| `rf017.rez` | `PLAYERVIEW/PV-RI_M4A1_GOLD.DTX` | `PV-RI_M4A1_GOLD.DTX` | 262,308 | `4DAD3D6CDDA5F880C45AFCF137B676556617CB68AF46BDE8517E81EBEA0E8ACE` | — | mismatch |
| `rf017.rez` | `WEAPONS/QV-RI_M4A1_SILENCER_BRONZE.DTX` | `QV-RI_M4A1_SILENCER_BRONZE.DTX` | 65,700 | `6971CF9FE4379EFF49795F47AC8E6CC5AB6C4C831C6AFA51A447D73807F71B94` | — | mismatch |
| `rf017.rez` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_BRONZE.DTX` | `PV-RI_M4A1_SILENCER_BRONZE.DTX` | 327,844 | `1931C1448492573910E4CD1C63161487C2F5A7F648F418150890BA349CE445A4` | — | mismatch |
| `rf017.rez` | `WEAPONS/QV-RI_M4A1_SILENCER_SILVER.DTX` | `QV-RI_M4A1_SILENCER_SILVER.DTX` | 65,700 | `15F02E10B424F71004A766A5DDD6D0833CF08049030BA966A7A60EE13A8D9DE8` | — | mismatch |
| `rf017.rez` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_SILVER.DTX` | `PV-RI_M4A1_SILENCER_SILVER.DTX` | 327,844 | `9137315708C8187782B8EFF73A06DDF5617E165714936E2615F76B03FA5F2EEC` | — | mismatch |
| `rf017.rez` | `WEAPONS/QV-RI_M4A1_SILENCER_CRYSTAL.DTX` | `QV-RI_M4A1_SILENCER_CRYSTAL.DTX` | 65,700 | `FFD56334FCC32215CF7C65ADD7D8E34A230D4F17523F824F3DD272ABD9D69EB2` | — | mismatch |
| `rf017.rez` | `PLAYERVIEW/PV-RI_M4A1_SILENCER_CRYSTAL.DTX` | `PV-RI_M4A1_SILENCER_CRYSTAL.DTX` | 327,844 | `C640EDF3B2B443E191EF0DE5E319F5013E18BFD368EDFE72A543BB80C3805A46` | — | mismatch |

## 5. Per-weapon BornBeast match summary

| WeaponName | unique_payloads | bornbeast_payload_hits |
|---|---|---|
| `M4A1` | 6 | 0 |
| `M4A1-A` | 6 | 0 |
| `M4A1-B` | 6 | 0 |
| `M4A1-Custom` | 6 | 0 |
| `M4A1-QQ»áÔ±` | 6 | 0 |
| `M4A1-S` | 7 | 0 |
| `»Æ½ðM4A1` | 6 | 0 |
| `ÇàÍ­M4A1-A` | 6 | 0 |
| `Ë®¾§M4A1-A` | 6 | 0 |
| `ÒøÉ«M4A1-A` | 6 | 0 |

## 6. Status & next investigation

**status**: `MATERIAL_BINDING_PARTIAL`

- All unique (rez_path, full_path) payloads have a bounded SHA256; every binding_ref is byte-verified.
- **No runtime payload SHA256 matches a BornBeast P4 baseline asset** — bf005's M4A1 family resolves to the base/silencer/camo/QQ/gold/silver/bronze/crystal M4A1 skin family, not BornBeast.
- This is a bounded negative: N02-C had already established that BornBeast is absent from bf005's decoded Bute records; this round promotes that conclusion to byte-level payload identity for every reachable bf005 (WeaponName, field) hit.
- BornBeast native material closure for P4-M01 therefore requires a different `bf*.ltc` layer (bf001-*.ltc, bf000.lta) or a runtime-resident inventory scan; this round closed the bf005 layer only.

## 7. Scope guard

- read only `data_offset .. data_offset + size` bytes from each (rez_path) — no full-archive load, no in-memory payload cache beyond the per-payload bounded block;
- did NOT decompile / strings / xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT modify `plan.md`
- did NOT enter P5 identity confirmation
- did NOT announce P4-M01 PASS
- did NOT freeze CFG shader semantics
- did NOT promote REZ catalog MD5 mismatch to an engine-format fact (informational only)
- used SHA256 for BornBeast comparison (not basename similarity)
