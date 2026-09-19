# M1_r5_phong 运行时结果

日期：2026-09-19  
加载身份：pak C **等于** A/B，r5 SHA-256 `58c40b9c…`（M1）  
视觉：**NO_MATERIAL_CHANGE**（不是 PASS，也不是洗白拒绝）

## 加载

用户 REBUILD 后，C 中 `cf_mauser_libra_r5.vmt` 已是 M1 文本（`$phong 1` + r0 遮罩 Phong）。本次“没变化”不是旧包。

截图：`runtime/M1_r5_phong/scenes/{lit_front,lit_turn,dark}.jpg`

## 对照

与基线三张同位置比较：黑色主体没有出现新的金纹／亮边；徽章和准星金件亮度与基线同类；转向后高光形状没有新的金属走光；墙影处仍整块偏暗。没有洗白或噪点。

## 结论

“r5 被当成无高光表面”不是当前画面差的主因。r0 那套 Phong 接到 r5 上，游戏内看不出效果。

不提高 boost。r5 区域 `specular_lum=0.078`（r0=0.197，r1=0.295），`$basemapalphaphongmask` 在这块 UV 上本身就弱，暗底 albedo 更压掉高光。

## 已做的下一步

已把 r5 滚回冻结基线，并只同步 **M2_env_off**（关 r1/r4 `$envmap`）到 A/B。A/B 29/29。pak 仍是 M1，需再次 REBUILD。
