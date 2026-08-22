# P4-M01-N02-D — M4A1 Runtime Binding -> REZ Asset Existence Verification

- status: **M4A1_RUNTIME_ARTIFACT_CONFIRMED**
- script: `scripts/material_recovery/n02d_rez_asset_lookup.py`

## 1. Scope

- only existing N02-C M4A1 binding paths were re-evaluated
- only the **REZ directory index** was read (no payload extraction)
- the REZ reader is a 1:1 port of
  `CFRezManager/Archives/RezArchiveReader.cs` +
  `CFRezManager/Archives/RezCrypto.cs`
- REZ files indexed: **475** under `rez/ rez2-6/`
- unique basenames in the union index: **225863**
- total file entries across all REZ: **252505**
- index build time: 17.7s

## 2. Verdict counts

| verdict | count |
|---|---|
| `DIRECT_RUNTIME_ARTIFACT` | 60 |
| `ARCHIVE_INDEX_ONLY` | 0 |
| `NOT_FOUND_IN_SCOPED_RUNTIME` | 0 |

## 3. Per-binding lookup table

| WeaponName | field | runtime_path | verdict | rez_path | name | size | id | md5 |
|---|---|---|---|---|---|---|---|---|
| `M4A1` | `ModelFileName` | `Models\weapons\m4a1.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1.LTB` | 16,558 | 0 | `A23982936F54BC95399359F4FEF6BBCC` |
| `M4A1` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `L-M4A1.DTX` | 32,932 | 0 | `5DAE6B278CBDDF6B8BD80429FBD7E3CF` |
| `M4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `M4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `M4A1-B` | `ModelFileName` | `Models\weapons\m4a1.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1.LTB` | 16,558 | 0 | `A23982936F54BC95399359F4FEF6BBCC` |
| `M4A1-B` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `L-M4A1.DTX` | 32,932 | 0 | `5DAE6B278CBDDF6B8BD80429FBD7E3CF` |
| `M4A1-B` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `M4A1-B` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1-B` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1-B` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-B` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-B` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `M4A1-A` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `L-M4A1_SILENCER.DTX` | 32,932 | 0 | `BF0E80517626F05CE9A21F4BF9066E86` |
| `M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `M4A1-S` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `M4A1-S` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | 0 | `56498E817DA6ED661D6D3B5098974F79` |
| `M4A1-S` | `SkinFileName` | `ModelTextures\weapons\L-M4A1_Silencer_camo.DTX` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | 0 | `92A6162F9381436C72320E4874B3E104` |
| `M4A1-S` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `M4A1-S` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-S` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-S` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1-camo.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1-CAMO.DTX` | 524,452 | 0 | `1AEB11A4CC8B21D2A7DE05DCEA919D3D` |
| `M4A1-S` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-S` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-S` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `M4A1-QQ»áÔ±` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `M4A1-QQ»áÔ±` | `SkinFileName` | `ModelTextures\weapons\m4a1_qq.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `M4A1_QQ.DTX` | 41,124 | 0 | `BAE2E92D4AC646354EF784B25E7AF22B` |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-m4a1_qq.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_QQ.DTX` | 164,004 | 0 | `6B3B91852C8237B17F2AB655F18EE2AE` |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-QQ»áÔ±` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `M4A1-Custom` | `ModelFileName` | `Models\weapons\M4A1-CUSTOM.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1-CUSTOM.LTB` | 29,576 | 0 | `19A34256C538D38066C7FC1D8C9B19F7` |
| `M4A1-Custom` | `SkinFileName` | `ModelTextures\weapons\l-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `L-M4A1.DTX` | 32,932 | 0 | `5DAE6B278CBDDF6B8BD80429FBD7E3CF` |
| `M4A1-Custom` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1-CUSTOM` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1-CUSTOM.LTB` | 64,927 | 0 | `F28DDAB62708572ABC5DA88F7DA2D24C` |
| `M4A1-Custom` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1-CUSTOM` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1-CUSTOM.DTX` | 131,236 | 0 | `8AE7E66D9658810A4420483269EC9751` |
| `M4A1-Custom` | `PViewModelFileName` | `Models\PlayerView\PV-M4A1-CUSTOM` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1-CUSTOM.DTX` | 131,236 | 0 | `8AE7E66D9658810A4420483269EC9751` |
| `M4A1-Custom` | `PViewSkinFileName` | `ModelTextures\PlayerView\pv-m4a1.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `M4A1-Custom` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-Custom` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `M4A1-Custom` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `»Æ½ðM4A1` | `ModelFileName` | `Models\weapons\m4a1.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1.LTB` | 16,558 | 0 | `A23982936F54BC95399359F4FEF6BBCC` |
| `»Æ½ðM4A1` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_gold.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `QV-RI_M4A1_GOLD.DTX` | 82,084 | 0 | `FA1801AB9D3FD0F3F236A17699DAB10C` |
| `»Æ½ðM4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `»Æ½ðM4A1` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1.DTX` | 524,452 | 0 | `35DD8FFDC846ACFD17E4BFF57B98B832` |
| `»Æ½ðM4A1` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_gold.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-RI_M4A1_GOLD.DTX` | 262,308 | 0 | `E2FDB69324BDCE61AB92FF4EC158FF93` |
| `»Æ½ðM4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `»Æ½ðM4A1` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `»Æ½ðM4A1` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `ÇàÍ­M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `ÇàÍ­M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_bronze.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `QV-RI_M4A1_SILENCER_BRONZE.DTX` | 65,700 | 0 | `F7778D04AA8541EF2432B743B7929F39` |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_bronze.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-RI_M4A1_SILENCER_BRONZE.DTX` | 327,844 | 0 | `E8FD2627C5BE9D4E50544BB3FAE7B7A9` |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `ÇàÍ­M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `ÒøÉ«M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `ÒøÉ«M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_silver.dtx` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `QV-RI_M4A1_SILENCER_SILVER.DTX` | 65,700 | 0 | `8AD3934D9E0E2D9138E7C41063E1EF6F` |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_silver.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-RI_M4A1_SILENCER_SILVER.DTX` | 327,844 | 0 | `74B37FEE7A865C83FEB49CF3D1CE46D6` |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `ÒøÉ«M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |
| `Ë®¾§M4A1-A` | `ModelFileName` | `Models\weapons\M4A1_Silencer.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `M4A1_SILENCER.LTB` | 16,926 | 0 | `848703A34A2A8B50028D217D8D270FB9` |
| `Ë®¾§M4A1-A` | `SkinFileName` | `ModelTextures\weapons\QV-RI_m4a1_silencer_crystal.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `QV-RI_M4A1_SILENCER_CRYSTAL.DTX` | 65,700 | 0 | `5B8FA5E97DA1A9073C11A403560E52CD` |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `PV-M4A1_SILENCER.LTB` | 64,777 | 0 | `941ADE9EE197F60A2E04FA12B2F29FD7` |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | `Models\PlayerView\pv-m4a1_silencer` | DIRECT_RUNTIME_ARTIFACT | `RF017.REZ` | `PV-M4A1_SILENCER.DTX` | 32,932 | 0 | `589B86B4462F861C5DFDAD7A5A70FBAF` |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | `ModelTextures\PlayerView\PV-RI_m4a1_silencer_crystal.DTX` | DIRECT_RUNTIME_ARTIFACT | `rf017.rez` | `PV-RI_M4A1_SILENCER_CRYSTAL.DTX` | 327,844 | 0 | `F89155D2AF2C033BACBB40E39807DA3B` |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | `RS\\NinjaTranslucent.ltb` | DIRECT_RUNTIME_ARTIFACT | `RF016.REZ` | `NINJATRANSLUCENT.LTB` | 111 | 0 | `A6FB0DE9DAD327990799DD0D89E3B5D9` |
| `Ë®¾§M4A1-A` | `PViewRenderStyleFileName` | `RS\\PVModelDefault.ltb` | DIRECT_RUNTIME_ARTIFACT | `rf002.rez` | `PVMODELDEFAULT.LTB` | 119 | 0 | `9B86A40416C4B63A68C6CB829CADFA34` |

## 4. Per-WeaponName rollup

| WeaponName | field | most-severe verdict |
|---|---|---|
| `M4A1` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-A` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-B` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-Custom` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-QQ»áÔ±` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `M4A1-S` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `»Æ½ðM4A1` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÇàÍ­M4A1-A` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `Ë®¾§M4A1-A` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `ModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `PViewModelFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `PViewRenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `PViewSkinFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `RenderStyleFileName` | DIRECT_RUNTIME_ARTIFACT |
| `ÒøÉ«M4A1-A` | `SkinFileName` | DIRECT_RUNTIME_ARTIFACT |

## 5. Status & next investigation

**status**: `M4A1_RUNTIME_ARTIFACT_CONFIRMED`

- at least one M4A1 binding path is confirmed to exist
  inside the CF runtime REZ archives by name + extension +
  non-zero size. This is the strongest non-decompile evidence
  that the runtime Bute bind maps to a real CF artifact.
- The next single highest-value consumer is **bounded payload
  SHA collection** for the matching entry: read just the bytes
  at `data_offset` for `size` bytes, hash them, and compare to
  any P4 / N01 extracted artifact. The full file is not
  needed; the on-disk MD5 in the REZ directory is already
  recorded in the lookup table above.

## 6. Scope guard

- did NOT extract any REZ payload bytes
- did NOT decompile or strings/xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT modify `plan.md`
- did NOT re-do LTC format reverse
- did NOT treat filename similarity as binding proof
- P4-M01 PASS NOT announced; P5 identity confirmation NOT entered
