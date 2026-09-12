# P5-T03 — 雷神 Resource Graph

Result: **RESOURCE_GRAPH_RECORDED**. Identity remains **not** `IDENTITY_CONFIRMED`.

User 2026-09-13: base `PV-M4A1_S_Transformers` is 雷神 (`USER_VISUAL_MATCH_CONFIRMED`).
Left/right swap: confirmed fixed in Blender by LTB X scale −1 + reverse faces.

## Identity root

- Official: M4A1-雷神 / item `2010044601`
- PV LTB: `Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB` SHA256 `a0ccef5deed745f1731eb93295c630f531123288055f3c3790531b99b6e401b8`
- PV DTX: `ModelTextures/PLAYERVIEW/PV-M4A1_S_Transformers.DTX` SHA256 `7ca69f66d229a942752edd327fde145e45c2c00d65b570f5e5a6b6ac68d52555`
- `_PC` copies of DTX/CFG are same-bytes aliases, not a second skin.

## Graph

```text
Bute Weapon  M4A1-雷神 / StandardName M4A1_S_Transformers
  PViewModelFileName -> PV-M4A1_S_Transformers.LTB
  PViewSkinFileName  -> PV-M4A1_S_Transformers.DTX  (== _PC bytes)
  ModelFileName      -> QV-M4A1_S_Transformers.LTB
  SkinFileName       -> QV-M4A1_S_Transformers.DTX
  CFG Name2          -> M4A1_S_Transformers_{S,N,alpha}.tga
  CFG Name2          -> Black_Shader02.dds  (shared cube)
  RS                 -> NinjaTranslucent / PVModelDefault
  PreView            -> QV-M4A1_S_IronBeast_PreView.ltb  (Bute; shared, not Transformers_Preview)
```

## Nodes

| id | role | path | sha256[:12] | size | relation | confidence |
|---|---|---|---|---|---|---|
| `pv_ltb` | pv_ltb | `Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB` | `a0ccef5deed7` | 152923 | user_visual_match | OBSERVED |
| `pv_dtx` | pv_dtx | `ModelTextures/PLAYERVIEW/PV-M4A1_S_Transformers.DTX` | `7ca69f66d229` | 524452 | user_visual_match + same_stem_or_same_bytes | OBSERVED |
| `weapon_shader_cfg` | weapon_shader_cfg | `ModelTextures/Shader/WeaponShader/M4A1_S_Transformers.CFG` | `75c6b29a369c` | 506 | same_stem_filename_not_bute | STRONG_HYPOTHESIS |
| `specular` | specular | `ModelTextures/SpecularMap/M4A1_S_Transformers_S.TGA` | `84694eb4f6df` | 3145772 | cfg_name2 | STRONG_HYPOTHESIS |
| `normal` | normal | `ModelTextures/NormalMap/M4A1_S_Transformers_N.TGA` | `882c4561f55e` | 3145772 | cfg_name2 | STRONG_HYPOTHESIS |
| `alpha` | alpha | `ModelTextures/AlphaMap/M4A1_S_Transformers_Alpha.TGA` | `9b66c835a190` | 3145772 | cfg_name2 | STRONG_HYPOTHESIS |
| `env_cube` | env_cube | `ModelTextures/EnvCubeMap/Black_Shader02.DDS` | `c64014afe4b3` | 786560 | cfg_name2_shared | STRONG_HYPOTHESIS |
| `qv_ltb` | qv_ltb | `Models/WEAPONS/QV-M4A1_S_Transformers.LTB` | `3e8479d64e75` | 20186 | packed_bute_ModelFileName | OBSERVED |
| `qv_dtx` | qv_dtx | `ModelTextures/WEAPONS/QV-M4A1_S_Transformers.DTX` | `f883496782df` | 524452 | packed_bute_SkinFileName | OBSERVED |
| `qv_transformers_preview_ltb` | qv_ltb | `Models/WEAPONS/QV-M4A1_S_Transformers_Preview.LTB` | `2dedbd7f3e7a` | 102812 | same_stem_preview_filename_not_bute | HYPOTHESIS |
| `rs_ninjatranslucent` | other_ltb | `RS/NINJATRANSLUCENT.LTB` | `85a8c47e4cfa` | 111 | packed_bute_RenderStyle | OBSERVED |
| `rs_pvmodeldefault` | other_ltb | `RS/PVMODELDEFAULT.LTB` | `7aac491cdd91` | 119 | packed_bute_RenderStyle | OBSERVED |
| `ui_0` | ui_icon | `TEX/UI/WEAPONICON/WEAPON_SELECT_FD_M4A1_S_Transformers.DTX` | `81aeed6e8388` | 4651 | ui_name_convention | HYPOTHESIS |
| `ui_1` | ui_icon | `TEX/UI/WEAPONICON/WEAPON_SELECT_BB_M4A1_S_Transformers.DTX` | `6e6400395d3e` | 3870 | ui_name_convention | HYPOTHESIS |
| `ui_2` | ui_icon | `TEX/UI/KILLMSG/SHOT_WEAPON_FD_M4A1_S_Transformers.DTX` | `6d35c8af5e6c` | 236 | ui_name_convention | HYPOTHESIS |
| `ui_3` | ui_icon | `TEX/UI/KILLMSG/SHOT_WEAPON_BB_M4A1_S_Transformers.DTX` | `9b676f4750ce` | 204 | ui_name_convention | HYPOTHESIS |
| `ui_4` | ui_icon | `TEX/UI/WEAPONICON/BUYWEAPON_INFO_M4A1_S_Transformers.DTX` | `380439a5d048` | 24498 | ui_name_convention | HYPOTHESIS |
| `ui_5` | ui_icon | `TEX/UI/KILLMSG/SHOT_WEAPON_M4A1_S_Transformers.DTX` | `ff988242a1dd` | 256 | ui_name_convention | HYPOTHESIS |

## Binding grades

- PV LTB + PV DTX are OBSERVED and user-matched. That is USER_VISUAL_MATCH_CONFIRMED, not IDENTITY_CONFIRMED.
- CFG Name2 filenames exist as MD5-verified TGA/DDS. That is a config reference, not FXO technique proof. Bute does not name the TGA/CFG.
- QV LTB/DTX are Bute ModelFileName / SkinFileName when the canonical Weapon record is present.
- UI icons remain name convention only (HYPOTHESIS).
- Packed Bute / TABLE search: OBSERVED.
- Identity-core audio: NEGATIVE_RESULT_SCOPED.
- LTB animation clip names are not decoded by P5T02ModelReader; header allocs are STRUCTURALLY_VERIFIED counts.
- Do not treat related_variant (Classic, DS, FD, BB, GR/BL, event skins) as 雷神.

## Audio

- Identity-core WAV/OGG/MP3/BANK: **0**
- Related variant audio (other Transformers skins): **9**
- Family-other (Thunder hammer/scepter etc.): **25**
- Loose FMOD bank token hits: **0**
- Status: `NEGATIVE_RESULT_SCOPED`
- Canonical Bute `M4A1-雷神` has no dedicated SND/WEAPON/M4A1_S_Transformers/*.WAV in REZ. Variant skins (Qingchun/BB/Zeekr) have their own clips; those are not identity-core.

## Animation / config

- PV LTB file type: `LTB_D3D_MODEL_FILE`
- alloc nParentAnims=8 nKeyFrames=256 nAnimData=408576 nNodes=57 nPieces=11
- decoder mesh names: Fview-hand2, Fview-arm2, M4A1_transformers_Body, M4A1_transformers_MAG, M4A1_transformers_part05, M4A1_transformers_Reload02, M4A1_transformers_part02, M4A1_transformers_part04, M4A1_transformers_part01, M4A1_transformers_part03, M4A1_transformers_Reload01
- ASCII anim-like strings in LTB: reload, WeaponReload, select, WeaponReload*, idle_0, postfire, fire!, fire, prefire, gunfire

- Packed Bute / TABLE files recovered: **1235**
- Token hits: **1** files / **106** hits
- Canonical packed Bute Weapon (GBK-decoded):
  - WeaponName `M4A1-雷神`
  - StandardName `M4A1_S_Transformers`
  - PViewModelFileName `Models\PlayerView\PV-M4A1_S_Transformers`
  - PViewSkinFileName `ModelTextures\PlayerView\PV-M4A1_S_Transformers.dtx`
  - ModelFileName `Models\Weapons\QV-M4A1_S_Transformers.ltb`
  - SkinFileName `ModelTextures\Weapons\QV-M4A1_S_Transformers.dtx`
  - PreViewModelFileName `Models\Weapons\QV-M4A1_S_IronBeast_PreView.ltb`
  - RenderStyle `RS\\NinjaTranslucent.ltb` / `RS\\PVModelDefault.ltb`
  - ShotSoundName `ShootM4A1-S-Beast` (event name, not a REZ WAV path)
  - GViewAnimName `M4A1`
  - source `['rez/Butes/BF005.LTC']`
- Related Bute rows share the same StandardName (源-雷神 LV2–6, 高校特权) or only the Transformers token (IronBeast 雷神 skins). Those are **not** identity-core.

## Conversion notes (not identity)

- Raw CF LTB import is left/right swapped vs 图鉴. Blender / Source 1 path must apply LTB X scale −1 and reverse faces. User confirmed 2026-09-13: 「对了」.
- Native PV DTX albedo is dark; 图鉴 is lit art. Do not rewrite native pixels.
- Decoder V is already image-top-left. Do not apply a second `v→1-v` on LithTechModelDecoder JSON.

## Not written

- `IDENTITY_CONFIRMED`
- P6 deploy
- N05-J / frozen addon changes

Reproduce:

```powershell
python -B scripts/p5/p5_t03_resource_graph.py
```

