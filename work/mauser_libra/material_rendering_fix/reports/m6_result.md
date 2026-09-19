# M6_r1_env_unmask 运行时结果

日期：2026-09-19  
加载身份：pak C **等于** A/B（r1 已去掉 `$normalmapalphaenvmapmask`，仍保留 `$envmap env_cubemap`）  
视觉：**NO_MATERIAL_CHANGE**

## 对照

徽章和亮金没有出现天空或地图立方体贴图颜色，转向也没有环境洗色。和基线、M2 同类。

## 结论

在这套第一人称 viewmodel 上，`env_cubemap` 即使去掉遮罩也不采样。M2+M6 一起说明：当前环境反射路径没有可见输出。

- 不做 M3（改区域强度）
- 不绑定 LobbyCube（历史白噪点）
- 金属观感应走已确认有效的 Phong 路径

M6 已滚回。下一实验 **M4_phong_exponent**：r0–r4 的 `$phongexponent` 4→48（天袭 A.8.1 金属指数），boost/tint/envmap/r5 不动。
