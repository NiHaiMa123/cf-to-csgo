# M4b_phong_boost 运行时结果

日期：2026-09-19  
加载身份：pak C **等于** A/B（r0 boost 3.14，r1/r4 5.02，指数 48）  
视觉：**NO_CLEAR_ENERGY_CHANGE**（无洗白）

## 对照

Phong 增益 ×2 后，徽章／金框没有明显变亮，墙影处也没有抬起来，黑色主体仍暗。不是过曝失败。

## 结论

在带 `$basemapalphaphongmask` 的当前路径上，加倍增益几乎看不出。限制因素更像是遮罩或 Phong 根本没在第一人称上出光，而不是能量不够。

下一实验 **M6_r1_phong_unmask**（父本=M4b）：只去掉 r1 的 `$basemapalphaphongmask`，指数／增益／颜色保留。已同步 A/B，等 REBUILD。
