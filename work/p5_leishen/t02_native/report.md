# P5-T02 — Transformers native inventory (user visual gate)

Result: **NATIVE_TRANSFORMERS_INVENTORY_READY_FOR_USER_GATE**.  
Identity remains **CANDIDATE_ONLY**. This pass does **not** write `USER_VISUAL_MATCH_CONFIRMED` or `IDENTITY_CONFIRMED`.

Official 图鉴 (T01 user-confirmed): **M4A1-雷神** / item `2010044601` / `C0457.png` — silver M4A1, mechanical dragon head, blue energy.

Look at [`gate/gate_sheet.png`](gate/gate_sheet.png) first. Do not use the 77-tile `contact_sheet.png`.

## UV wrap (fixed 2026-09-13)

The first gate meshes looked randomly textured. That was **not** a wrong atlas. Historical T02 always sampled decoder UVs with `v → 1-v`. CFRezManager OBJ export already writes `vt (u, 1-decoderV)`, so applying `1-v` again to LithTechModelDecoder JSON puts the mag-well island on the stock.

Decoder V is already image-top-left. After removing the extra flip:

- stock carries the Autobot-like mark
- magazine is a magazine
- barrel dragon is a single piece
- Classic shows L1/L2 blue strips on the carry handle

Before/after: `uv_repair/base_decoder_vflip.png` vs `uv_repair/base_decoder_v_as_is.png`. Orthographic unlit wrap is still darker than 图鉴; that is albedo + no CF lighting, not another UV scramble.

## What I looked at before asking

| Image | What it actually shows |
|---|---|
| [`gate/official_C0457.png`](gate/official_C0457.png) | Official 图鉴: silver body, dragon barrel, blue glow, Autobot-like stock mark |
| [`gate/buyweapon_M4A1_S_TRANSFORMERS.png`](gate/buyweapon_M4A1_S_TRANSFORMERS.png) | CF buy-menu icon labelled `M4A1.S.TRANSFORMERS` / `T 英雄`. Same silhouette as 图鉴. **UI art, not PV diffuse** |
| [`gate/pv_dtx_base_Transformers.png`](gate/pv_dtx_base_Transformers.png) | Verified PV DTX, 1024×1024 DXT1. Dark silver mechanical atlas, dragon head with blue eye, serial `M4A1SSQ00083`, L1/L2. Native albedo is dark (empty atlas space is near-black) |
| [`gate/mesh_base_Transformers.png`](gate/mesh_base_Transformers.png) | Same DTX UV-wrapped on verified `PV-M4A1_S_Transformers.LTB`. Dragon barrel is visible; unlit wrap is much darker than 图鉴 |
| [`gate/pv_dtx_Classic.png`](gate/pv_dtx_Classic.png) | Classic PV DTX: same layout, brighter silver/blue. Closer to 图鉴 value range |
| [`gate/mesh_Classic.png`](gate/mesh_Classic.png) | Classic DTX on the Classic/TLand LTB SHA family |
| [`gate/neg_bornbeast_NOT_leishen.png`](gate/neg_bornbeast_NOT_leishen.png) | **NEG** BornBeast / 黑骑士: red-black, different mesh language. Not 雷神 |

The DS mesh wrap produced in the first dump is a **red** skin. It is not the 图鉴 and was left out of the gate sheet.

## Recovered facts (not identity)

- 464 REZ indexes scanned with the N05-C MD5-verified reader. 973 Transformers/Thunder family hits, 793 unique payloads, 77 unique PV DTX, 0 recover failures.
- `ModelTextures/PLAYERVIEW/PV-M4A1_S_Transformers.DTX` (`rez/rf017.rez` part 8) and `PV-M4A1_S_Transformers_PC.DTX` (`rez3/RF017.REZ`) share directory MD5 `baa25436eb34a5ac91412e9c099c8604` and SHA256 `7ca69f66d229a942…`. Same bytes.
- Base PV LTB SHA256 `a0ccef5deed745f1…` (14 filename copies, including historical C029 IronBeast_Gilt cluster). Geometry sharing is not skin identity.
- Classic LTB SHA256 `620778d78577ed10…` is shared with the TLand filename cluster. Classic **DTX** is a distinct brighter atlas.
- Base WeaponShader CFG (same bytes as `_PC`) names `M4A1_S_Transformers_S.tga` / `_N.tga` / `_alpha.tga` and `Black_Shader02.dds`. CFG `Name2` is a config reference, not Bute `PViewSkinFileName` and not runtime technique proof.
- Historical T02 gray geometry + headerless BGR24 `data/rf017` probe is obsolete for these pixels.

## Binding grade

- Same-stem LTB↔DTX and CFG `Name2` = filename/config convention.
- Packed Bute still has no Transformers `PViewSkinFileName` from the earlier bounded search; this pass does not invent that binding.
- CF buy-menu / kill icons support the **name** Transformers ↔ 图鉴 look. They are not the first-person atlas.

## User gate

Please say which local candidate is M4A1-雷神, or none:

1. **Base** `PV-M4A1_S_Transformers` (same bytes as `_PC`) — dark native albedo, dragon head present.
2. **Classic** `PV-M4A1_S_Transformers_Classic` — same language, brighter silver/blue.
3. Neither / need another variant from the 77 PV DTX dump.

Do not treat BornBeast as 雷神. Filename `Transformers` is not identity by itself.

User 2026-09-13: `mesh_base_Transformers` looks like it, but too dark to confirm. Preview-only exposure is in [`gate/expose/`](gate/expose/) (`gain 3.2x`, native DTX unchanged). Live Blender MCP 9876 now shows the same base LTB+DTX in EEVEE (`work/p5_leishen/t02_native/blender/`). Hands hidden.

**USER_VISUAL_MATCH_CONFIRMED** — user: 「是雷神」. Local candidate is base `PV-M4A1_S_Transformers` (DTX same bytes as `_PC`). Not `IDENTITY_CONFIRMED`.

User also: raw import is left/right swapped. Fix: LTB X scale −1 and flip normals. Live Blender already mirrored; preview [`blender/viewport_gun_mirrored.png`](blender/viewport_gun_mirrored.png).

N05-J diagnostic addon and the parked P4 frozen addon were not touched. P4-M01 remains INCOMPLETE.

Reproduce:

```powershell
python -B scripts/p5/p5_t02_native_inventory.py
python -B scripts/p5/p5_t02_native_gate.py
```
