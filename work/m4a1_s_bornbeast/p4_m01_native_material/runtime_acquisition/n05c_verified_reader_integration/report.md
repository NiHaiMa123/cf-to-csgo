# N05-C — Verified REZ reader integration

Result: **VERIFIED_READER_INTEGRATED**. P4-M01 remains **INCOMPLETE**.

Official extract/preview entries now share `rez_verified_payload.py` / `RezVerifiedPayloadReader`. Directory `time` is only a candidate numbered-part hint; bounds, length and MD5 are checked per candidate. Missing parts, truncated parts, wrong hashes and two matching candidates error. Archives without a complete directory MD5 cannot claim verification or guess a part.

## Official entries

- `scripts/cf_extract/extract_all.py extract_archive`
- `CFRezManager --extract-file (RezArchiveReader.ExtractFile)`
- `CFRezManager --read-hash (RezVerifiedPayloadReader.Read)`
- `n02e_r2_payload_hash.read_payload_bytes(..., entry=entry) used by N05-A`

N05-B helper `n05b_shard_material_recovery.py` was **not** used as proof that the official entries work.

## 9/9 SHA256 vs N05-B freeze

| Target | extract_all | CFRez extract-file | CFRez read-hash | N05-A n02e | Match |
|---|---|---|---|---|---|
| `PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` | `a30c9a271612…` | `a30c9a271612…` | `a30c9a271612…` | `a30c9a271612…` | yes |
| `PLAYERVIEW/PV-M4A1_RoyalDragon.DTX` | `7fcdd31bf6ec…` | `7fcdd31bf6ec…` | `7fcdd31bf6ec…` | `7fcdd31bf6ec…` | yes |
| `SpecularMap/PV-M4A1_RoyalDragon_s.DTX` | `56e7c35fbfb4…` | `56e7c35fbfb4…` | `56e7c35fbfb4…` | `56e7c35fbfb4…` | yes |
| `SpecularMap/PV-DualDE_GreenVein_S.DTX` | `16264274baaa…` | `16264274baaa…` | `16264274baaa…` | `16264274baaa…` | yes |
| `SpecularMap/M4A1_S_BornBeast_S.TGA` | `0f8807caa0aa…` | `0f8807caa0aa…` | `0f8807caa0aa…` | `0f8807caa0aa…` | yes |
| `WeaponShader/M4A1_S_BornBeast.CFG` | `ceb52671c5c1…` | `ceb52671c5c1…` | `ceb52671c5c1…` | `ceb52671c5c1…` | yes |
| `WEAPONS/QV-M4A1_S_BornBeast.DTX` | `b927ce642242…` | `b927ce642242…` | `b927ce642242…` | `b927ce642242…` | yes |
| `AlphaMap/M4A1_S_BornBeast_alpha.TGA` | `80b887618b82…` | `80b887618b82…` | `80b887618b82…` | `80b887618b82…` | yes |
| `NormalMap/M4A1_S_BornBeast_N.TGA` | `5f971097856b…` | `5f971097856b…` | `5f971097856b…` | `5f971097856b…` | yes |

BornBeast PV DTX decodes as 1024×1024. CFG sections: Textures, Techniques, Properties. TGA files parse without inserted-header repair.

## Cache

CFRezManager.Tests directory cold/hot plus thumbnail key change after numbered-part mutation. Directory cache is v2; thumbnail cache is v2 and includes numbered-part path/length/mtime so changing a part cannot reuse the old image.

## Staging

Raw bytes for this round: `D:\project\cf_to_csgo\data\n05c_verified_extract` (local `data/**`, not committed). Diagnostic PNGs and this report: `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05c_verified_reader_integration`. Historical `data/rf017` was not overwritten.

## Still deprecated

- `n02e_r2_payload_hash.read_payload_bytes(path, offset, size) without entry` — Unauthenticated main-file slice; no numbered-part routing; must not claim verified recovery
- `scripts/material_recovery/n03a_bornbeast_consumer.py and n03b–n03g payload reads` — Still call the unauthenticated n02e helper; historical reports were not rewritten
- `scripts/material_recovery/n02d_rez_asset_lookup.py` — Basename-oriented historical index helper; not a payload resolver
- `pre-N05-C CFRezManager ArchiveFile.DataOffset seeks` — Replaced by RezVerifiedPayloadReader; leftover seeks are writer/cache metadata only
- `data/rf017 and other historical extract trees` — Old main-file extracts; this round writes only data/n05c_verified_extract

## Reproduce

```powershell
python -B -m unittest discover -s tests -p test_rez_verified_payload.py -v; python -B -m unittest discover -s tests -p test_extract_all_verified.py -v
dotnet test CFRezManager.Tests/CFRezManager.Tests.csproj -c Debug
python scripts/material_recovery/n05c_verified_reader_integration.py
```

P4 frozen build, deploy and shader tuning were not touched.
