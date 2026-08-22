# P4-M01-N02-E — M4A1 Runtime Artifact Payload SHA Verification

- status: **M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN**
- script: `scripts/material_recovery/n02e_payload_hash.py`

## 1. Scope

- only N02-D confirmed REZ entries are read
- only the bytes at the REZ `data_offset` for exactly `size`
  bytes are loaded — never the full REZ
- SHA256 of the bounded payload is compared to:
  1. the REZ directory MD5 (the value CF itself wrote at
     archive-build time), and
  2. the P4 known BornBeast source LTB SHA256, recorded in
     `assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`
     under `inputs.cf_ltb_source.sha256`.

## 2. P4 known BornBeast source SHAs

- `inputs.cf_ltb_source`: `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB`  
  sha256: `5dbcee45c4565b2026a4e4d2d639a4b7022b4f4fc1c5ef69bc8f49fd5a6c54f7`
- `inputs.cf_ltb_source`: `data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB`  
  sha256: `5dbcee45c4565b2026a4e4d2d639a4b7022b4f4fc1c5ef69bc8f49fd5a6c54f7`

## 3. Verdict counts

| metric | count |
|---|---|
| verified entries | 29 |
| REZ MD5 MATCH | 12 |
| REZ MD5 MISMATCH | 17 |
| P4 BornBeast MATCH | 0 |
| P4 BornBeast NO_MATCH | 29 |
| skipped (empty/oversize/read-error) | 0 |

## 4. Per-extension rollup

| ext | count | rez_md5_match | rez_md5_mismatch | p4_match | p4_no_match |
|---|---|---|---|---|---|
| `.dtx` | 15 | 1 | 14 | 0 | 15 |
| `(no-ext)` | 8 | 5 | 3 | 0 | 8 |
| `.ltb` | 6 | 6 | 0 | 0 | 6 |

## 5. Per-entry detail

### 5.2 Entries whose SHA256 disagrees with the REZ directory MD5

| WeaponName | field | runtime_path | REZ | name | rez_md5 | payload_sha256 |
|---|---|---|---|---|---|---|
| `M4A1` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | `rf017.rez` | `L-M4A1.DTX` | `5DAE6B278CBDDF6B8BD80429FBD7E3CF` | `38d566adb963417955b79c37bbacc0defb43be69a307d00d3de37176a4a84ad8` |
| `M4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | `rf017.rez` | `PV-M4A1.DTX` | `35DD8FFDC846ACFD17E4BFF57B98B832` | `6ae0b7de74b6dbb016e8999ab478a81bac462021780899709007f4b516325d13` |
| `M4A1-A` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer.DTX` | `rf017.rez` | `L-M4A1_SILENCER.DTX` | `BF0E80517626F05CE9A21F4BF9066E86` | `001df1a187f62bbdacc745376b1780b147c4469ddd8f3b3f24561fc8c0c10799` |
| `M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | `589B86B4462F861C5DFDAD7A5A70FBAF` | `e4ad3d4389aab24b0c2c969546392c61cfa0a3dba03c1782676f82b3977098fa` |
| `M4A1-S` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | `rf017.rez` | `L-M4A1_SILENCER_CAMO.DTX` | `56498E817DA6ED661D6D3B5098974F79` | `48a3bd237592264f8da4fa913452a64659c514c50dc85ee009e48de73232f2fc` |
| `M4A1-S` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1-camo.dtx` | `rf017.rez` | `PV-M4A1-CAMO.DTX` | `1AEB11A4CC8B21D2A7DE05DCEA919D3D` | `bc2dd5691e3d8152b81798a05921d6611855c5b559ec1666ee724779cac21267` |
| `M4A1-QQ»áÔ±` | `SkinFileName` | `ModelTextures\weapons\m4a1_qq.DTX` | `rf017.rez` | `M4A1_QQ.DTX` | `BAE2E92D4AC646354EF784B25E7AF22B` | `4bc7c5faa5d84bd1c9370be454f9f193d98915335c654d12dbd77edf4a018424` |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-m4a1_qq.dtx` | `rf017.rez` | `PV-M4A1_QQ.DTX` | `6B3B91852C8237B17F2AB655F18EE2AE` | `da4281ce35944def3ece80e45cb3344463d2319ee09c6867459b7b008c1aa9db` |
| `M4A1-Custom` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1-CUSTOM` | `rf017.rez` | `PV-M4A1-CUSTOM.DTX` | `8AE7E66D9658810A4420483269EC9751` | `b145fdf510880b80bddd4e947dfd21244eeafddc70064a9f5997a3b326253869` |
| `»Æ½ðM4A1` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_gold.dtx` | `rf017.rez` | `QV-RI_M4A1_GOLD.DTX` | `FA1801AB9D3FD0F3F236A17699DAB10C` | `7ac5a024f3b0c7c7c4fd7fcba8589ff178d7bd9bc38c169e3934fb58da2f0f83` |
| `»Æ½ðM4A1` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_gold.dtx` | `rf017.rez` | `PV-RI_M4A1_GOLD.DTX` | `E2FDB69324BDCE61AB92FF4EC158FF93` | `4dad3d6cdda5f880c45afcf137b676556617cb68af46bde8517e81ebea0e8ace` |
| `ÇàÍ­M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_bronze.dtx` | `rf017.rez` | `QV-RI_M4A1_SILENCER_BRONZE.DTX` | `F7778D04AA8541EF2432B743B7929F39` | `6971cf9fe4379eff49795f47ac8e6cc5ab6c4c831c6afa51a447d73807f71b94` |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_bronze.dtx` | `rf017.rez` | `PV-RI_M4A1_SILENCER_BRONZE.DTX` | `E8FD2627C5BE9D4E50544BB3FAE7B7A9` | `1931c1448492573910e4cd1c63161487c2f5a7f648f418150890ba349ce445a4` |
| `ÒøÉ«M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_silver.dtx` | `rf017.rez` | `QV-RI_M4A1_SILENCER_SILVER.DTX` | `8AD3934D9E0E2D9138E7C41063E1EF6F` | `15f02e10b424f71004a766a5ddd6d0833cf08049030ba966a7a60ee13a8d9de8` |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_silver.DTX` | `rf017.rez` | `PV-RI_M4A1_SILENCER_SILVER.DTX` | `74B37FEE7A865C83FEB49CF3D1CE46D6` | `9137315708c8187782b8eff73a06ddf5617e165714936e2615f76b03fa5f2eec` |
| `Ë®¾§M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_crystal.DTX` | `rf017.rez` | `QV-RI_M4A1_SILENCER_CRYSTAL.DTX` | `5B8FA5E97DA1A9073C11A403560E52CD` | `ffd56334fcc32215cf7c65add7d8e34a230d4f17523f824f3dd272abd9d69eb2` |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_crystal.DTX` | `rf017.rez` | `PV-RI_M4A1_SILENCER_CRYSTAL.DTX` | `F89155D2AF2C033BACBB40E39807DA3B` | `c640edf3b2b443e191ef0de5e319f5013e18bfd368edfe72a543bb80c3805a46` |

### 5.3 Per-WeaponName/field rollup

| WeaponName | field | count | rez_md5_match | p4_match |
|---|---|---|---|---|
| `M4A1` | `ModelFileName` | 1 | 1 | 0 |
| `M4A1` | `PViewModelFileName` | 2 | 1 | 0 |
| `M4A1` | `PViewRenderStyleFileName` | 1 | 1 | 0 |
| `M4A1` | `RenderStyleFileName` | 2 | 2 | 0 |
| `M4A1` | `SkinFileName` | 1 | 0 | 0 |
| `M4A1-A` | `ModelFileName` | 1 | 1 | 0 |
| `M4A1-A` | `PViewModelFileName` | 3 | 2 | 0 |
| `M4A1-A` | `SkinFileName` | 1 | 0 | 0 |
| `M4A1-Custom` | `ModelFileName` | 1 | 1 | 0 |
| `M4A1-Custom` | `PViewModelFileName` | 3 | 2 | 0 |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | 1 | 0 | 0 |
| `M4A1-QQ»áÔ±` | `SkinFileName` | 1 | 0 | 0 |
| `M4A1-S` | `PViewSkinFileName` | 1 | 0 | 0 |
| `M4A1-S` | `SkinFileName` | 2 | 1 | 0 |
| `»Æ½ðM4A1` | `PViewSkinFileName` | 1 | 0 | 0 |
| `»Æ½ðM4A1` | `SkinFileName` | 1 | 0 | 0 |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | 1 | 0 | 0 |
| `ÇàÍ­M4A1-A` | `SkinFileName` | 1 | 0 | 0 |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | 1 | 0 | 0 |
| `Ë®¾§M4A1-A` | `SkinFileName` | 1 | 0 | 0 |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | 1 | 0 | 0 |
| `ÒøÉ«M4A1-A` | `SkinFileName` | 1 | 0 | 0 |

## 6. Verdict

**status**: `M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN`

- All bounded payload reads either match the REZ
  directory MD5 (proving the index is honest) or were
  skipped; **none** matches a P4 BornBeast source SHA.
- Therefore the BornBeast source LTB (the P4-derived
  custom asset) is **not byte-identical** to any of the
  runtime Bute bind targets in the CF REZ archives. The
  P4 frozen BornBeast mod is built from a custom LTB
  outside the CF runtime REZ layer, as the P4 baseline
  inventory already recorded.

## 7. Next single highest-value investigation target

- the runtime Bute binds to the BASE M4A1 family and
  the BornBeast custom LTB is a separate asset outside
  the CF runtime REZ layer. The next step is to
  acknowledge that the runtime REZ layer cannot, by
  itself, prove BornBeast identity; that requires the
  P4 / P5 stage that consumes the runtime artifact and
  the BornBeast source together.

## 8. Scope guard

- read at most `size` bytes per REZ entry — never the full REZ
- did not decompile or strings/xref any EXE / DLL
- did not reverse any FXO shader
- did not run any CF client / runtime binary
- did not modify `plan.md`
- did not re-do LTC format reverse
- did not treat filename similarity as hash evidence
- P4-M01 PASS NOT announced; P5 identity confirmation NOT entered
