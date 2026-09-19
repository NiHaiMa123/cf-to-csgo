# P7-S05 — 纯 CF 第一人称 viewmodel mod（CF 手膜显示 / CS 手臂隐藏）

日期：2026-09-13（**R3 修复版**：对齐已验证 P6 空间 + CS 手臂远处塌陷）
结果：BUILD_DEPLOYED_PENDING_RUNTIME_GATE（等待游戏内确认）
构建脚本：`scripts/p5/p5_p7_s05_cf_native_vm.py`
部署目标：`migi/csgo/addons/p_cf_leishen_m4a4_p6`（只改 `models/weapons/v_rif_m4a1.*` + 新增手臂材质）

## R1 → R2 → R3：三次定位

- **R1** `M = MirrorX@C3`：C3 是对齐 CS bind 姿态的拟合，非相机空间约定 → 模型巨大错位。
- **R2** 以 `decompiled_stock/`（BornBeast build）为参照：数学自洽但参照物本身顶点只有 ±2 的紧凑尺度、posed 网格仅 ~4.5 单位 —— 枪在眼前缩成小球；且 **identity 塌陷导致 bonemerge 手臂顶点落在 bind 相对空间（±10）即相机原点 → 满屏迷彩碎片**。
- **R3**（当前）：
  - **变换 H**：ICP 拟合 `CF idle-posed 枪身顶点 → P6（已验证可玩 build）idle-posed 顶点`：`s=1.785575`，`R≈Rx(-90°)`（det=+1，无镜像），`t=(-8.06,-13.62,3.47)`，med 残差 0.017。整个模型（顶点/rest/anim 世界矩阵）= CF 场景经 H 映射：`v'=H·v`、`R'=H·B·H⁻¹`、`W'(t)=H·W·H⁻¹`。
  - **CS 手臂隐藏**：47 根 `Bip01*` 骨全帧钉在 `(0,-500,0)` —— bonemerge 的 sleeve/glove 顶点整体沉到相机下 500 单位，彻底不可见（identity 塌陷是错的：顶点落 bind 相对空间 = 相机原点）。
  - **挂点**：4 attachment 骨挂 Dummy01 下，偏移取 P6 idle f0 官方位（flash −4.97,−35.7,−3.54；shell −5.79,−19.0,−3.31；stattrack/uid 同法）。
  - 开火序列名对齐 P6：`fire1/2/3`。

验证（生成 SMD 蒙皮仿真）：枪身 idle posed `x(-6.2..-3.5) y(-40.4..-4.7) z(-11.4..-0.3)` ≈ P6 posed `x(-6.6..-3.9) y(-40.4..-4.7) z(-11.4..-0.3)`；FoxHowl 手 `x(-7.7..-2.7) y(-26.7..-11.3)` = 枪身中段握持区；reload Bone06 弹匣骨位移正常（y −32.5→−31.3→−33.9→−32.5）；挂点与 P6 逐值一致；编译后 MDL 反编译 108 骨齐；`w_rif_*` 未动。

参考：`work/p5_leishen/p7_s05/viewmodel_transform.json`（H + P6 挂点世界矩阵）、`decompiled_new/`。

## 架构

`weapons/v_rif_m4a1.mdl` 整体重编，不再是"CF 网格贴 CS 骨骼"：

| 部分 | 内容 |
|---|---|
| 骨骼 108 | `v_weapon`(root) + 47 个 CS Bip01 塌陷骨 + 56 CF 骨 + 4 attachment 骨 |
| CS 手臂隐藏 | 47 个 `v_weapon.Bip01*` 骨全帧钉在 `(0,-500,0)` → bonemerge 的 sleeve/glove 顶点整体沉到相机下 500 单位 → 不可见 |
| CF 手膜 | FoxHowl Renewal **BL**（潜伏者）：`fox_bl_HAND` 3721v + `Arm_W` 801v，顶点经 LBS 重摆 `Σw·B_gun@inv(B_arm)` 摆进枪 bind 位（等价 Blender `R1A_CF_DEFORM_ARMS` 烘法） |
| 枪 | 9 个刚性件按已验证归属绑 CF 节点（Body→Dummy01、MAG→Bone06、Reload01→Bone04、Reload02→Box001、part01–05→Box003/004/005/006/002） |
| 动画 | 8 条 CF clip 原生数据：`idle_0`(301f)/`fire`/`reload`(161f)/`select`(65f) → 9 条 sequence，fps 100 |
| 坐标（R3 修正） | 整模型相似变换 `H`（s=1.7856，R≈Rx(-90°)，det+1）：`v'=H·v`、`R'=H·B·H⁻¹`、`W'=H·W·H⁻¹`。H 由 CF idle-posed → P6 posed 顶点 ICP 拟合（残差 0.017）。**不镜像、不用 C3、不用 BornBeast 紧凑参照**。 |

## 契约保持

- `$attachment 1/2`（flash/shelleject）+ `stattrack`/`uid` 骨挂在 CF `Dummy01` 下，偏移由 P6 idle SMD 世界变换解算
- 换弹事件按 CF 时序：ClipOut@19(194ms)、ClipIn@72(718ms)、ClipHit/CompleteReload@121(1211ms)
- draw: Draw@0；shoot: 5001+brass@0
- lookat01×3 = 冻结 idle（CF 无 inspect 动画；CS lookat 无法在 CF 骨架播放 —— 检视时枪保持持枪位，为已知回退）

## 材质

- 枪：沿用 P6 `v_models/rif_m4a1/*`（未动）
- 手臂：`v_models/cf_leishen/cf_foxhand_bl` / `cf_foxarm_bl` —— 4x 超分 diffuse + 原生 normal，VertexLitGeneric+phong

## 验证

- 编译：studiomdl OK，108 骨全保留（stattrack/uid 经 attachment 保住），9 序列
- 静态：枪件 rest bounds 与 P6 已知正确 SMD **逐值一致**（x −1.50..1.14 / y −41.43..−5.77 / z 4.59..15.70）
- 动态数值：idle f0 手臂蒙皮落点 x −2.3..2.7 / y −27.6..−12.8 / z 7.5..13.3 —— 与枪身相交，即"握枪"位
- Bone06（弹匣）reload t0→t40 Y 位移 −12.6→−3.2：拔弹匣运动真实写入
- 第三人称：`w_rif_m4a1*`/`w_rif_m4a1_dropped*` 文件未改（时间戳/哈希旧值）

## 待用户 runtime Gate

- 第一人称：CF 手膜可见、CS 手套/袖子消失、切枪/换弹/开火/run 动作时序
- 弹匣交接连续、结束回统一持枪位、握持不滑脱
- F 检视 = 静态持枪（预期内回退）
- 声音：CF 原声事件现在按 CF 时序触发（`SOUND_RETIME_REQUIRED_ON_CF_ANIM` 已自然满足——事件帧按 CF ms 换算）

## 已知限制

- inspect 无 CF 动画 → 冻结 idle（可后续把 CS lookat 重定向到 CF 骨架，或保留 CS 骨架仅驱动 lookat）
- CS 手臂隐藏靠"塌陷到 −500"；若个别 sleeve 模型含未 bonemerge 的额外骨（非标准），可能残留小块网格 —— 需 runtime 确认
- 手臂贴图为 BL 4x 超分 diffuse + 512² normal；spec/env 通道未接
