# M2_env_off 运行时结果

日期：2026-09-19  
加载身份：pak C **等于** A/B（r1/r4 为 M2）  
视觉：**NO_MATERIAL_CHANGE**

## 对照

关掉 r1/r4 的 `$envmap env_cubemap` 后，徽章、金框、枪管金件亮度与基线同类，转向也没有少掉一层环境反射。不是洗白，也不是“更好看”。

## 结论

当前 `env_cubemap` 路径没有可见贡献。M2 不是改善候选，已滚回冻结基线。

不把这当成“金属不需要环境反射”。也不做 M3（改强度计算）：强度作用在一条没有可见输出的路径上没有意义。

## 下一实验（已同步 A/B，等 REBUILD）

**M6_r1_env_unmask**：只改 r1，删 `$normalmapalphaenvmapmask`，保留 `$envmap` 和 `$envmaptint`。

- 若徽章／亮金出现天空或地图色、并随视角变：envmap 能采样，是遮罩在挡。
- 若仍无变化：这条 viewmodel 上 `env_cubemap` 基本不工作；不绑 LobbyCube；下一轮改已有效的 Phong（指数／颜色）。
