# N05-J — Formula-backed AlphaMap.b envmask

Result: **FORMULA_CHANNEL_DIAGNOSTIC_DEPLOYED**. P4-M01 remains **INCOMPLETE**. `final_cf_material=false`.

Addon: `p_cf_bornbeast_m4a4_n05j_formula_diag`
Deploy: `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_n05j_formula_diag` (created)
Previous N05-H addon: `removed`
Frozen parked: `True`

N05-I compiled PS uses AlphaMap.r as opacity, .g as spec mix, .b as cube mix. This BornBeast TGA has R=G=255 everywhere; only B varies (mean ~10.8 / 255). The diagnostic VMT therefore wires `$envmapmask` from B and drops `$normalmapalphaenvmapmask`.

`$phongexponent 16` is still a placeholder. CFG `SpecularPower*0.25` was not copied. Cube is still face0.

Restore frozen: `move D:\steam\steamapps\common\csgo legacy\migi\csgo\_parked_addons\p_cf_bornbeast_m4a4_p4_frozen_noop_01 back to D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_p4_frozen_noop_01 and remove D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_n05j_formula_diag`

