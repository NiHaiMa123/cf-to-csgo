# P6 — M4A1-雷神 identity replacement

Result: **P6_IDENTITY_REPLACEMENT_DEPLOYED**. `final_target_identity=true`. `final_cf_material=false`. P4-M01 remains **INCOMPLETE**.

Addon: `p_cf_leishen_m4a4_p6`
Deploy: `D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_leishen_m4a4_p6` (created)
Previous N05-J: `moved_outside_addons`
Frozen parked: `True` (not modified)

Local identity is base `PV-M4A1_S_Transformers` (user 是雷神 + Bute WeaponName M4A1-雷神). Mesh is compiled from the verified PV LTB, not the P4 BornBeast prototype mesh.

Left/right: LTB X scale −1 + reverse faces, then the frozen C3 M4A4 matrix. User already confirmed the Blender preview 「对了」.

Materials reuse the N05-J formula: AlphaMap.b → `$envmapmask`. `$phongexponent 16` is still a placeholder. Cube is face0 only. CFG scalars were not copied.

Compiled MDL internal name `weapons\v_rif_m4a1.mdl`, bones `57`, sequences `9`.

This is not P4-M01 PASS and not a lighting match. In-game look still needs a user Gate.

