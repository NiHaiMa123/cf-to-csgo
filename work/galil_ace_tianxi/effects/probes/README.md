# effects/probes — E2 三条路线最小探针（待用户 MIGI REBUILD 后实测）

## 修复记录（第 2 次部署，A↔B 32 文件一致）

1. **贴图回退事故**：`build_galilace_vm.py` 的 `build_materials()` 曾覆盖 `build_textures_v2.py`(v7) 拥有的 `cf_galilace_pb.vmt/vtf`（selfillum+mask 版 → 简化版、2048 BGRA → dxt1）。已改：模型构建不再写 v7 文件（arm VMT 与 v7 同模板、仅缺时补写），并清理 isolated 残留后重跑 v7 恢复。
2. **fx 网格不可见**：`fx_galilace_parts_blue.vmt` 原带 `$vertexcolor/$vertexalpha`，而 SMD 三角面无顶点色 → additive 输出为 0。已移除。
3. **粒子材质缺失**：PCF 引用的 `cf_fx_glow02.vmt` 不存在（只有 .vtf）。已补（粒子材质**需要** vertexcolor/vertexalpha——粒子渲染器按粒子写顶点色）。
4. **fx 网格错位 ~100 单位**：漏掉了节点的 `Sk` 对象缩放。上游 `BaseFx.cpp`：`PV_SocketAttach` 用 `GetSocketTransform(bWorldSpace=FALSE)`（模型空间 socket 变换）+ 父对象位置补偿；`Sk` 曲线经 `SetObjectScale` 直接作对象缩放。blue-parts Sk=0.15（FX LTB 比 PV 模型大约 3×）。修正后 PARTS_BLUE 落位在枪身中后段，与参考视频一致。

本轮部署到 `p_cf_tianxi_galilar_p1` 的增量：

| 路线 | 内容 | 文件/改动 |
|---|---|---|
| B 呼吸材质 | `fx_galilace_parts_blue` 用 `Sine` 代理驱动 `$alpha`（2s 周期 0.35→1.0），加性混合 | `materials/.../cf_tianxi/fx_galilace_parts_blue.vmt` + `cf_fx_glow02.vtf` |
| C 单光片 | 原始 LTBModel 层 `PARTS_BLUE`（68v/34t），按 `fix_effect_5` socket（挂 Box001）经 B×socket×MXH 链落位，蒙皮到新增 `fx_fix_effect_5` 骨骼 | 模型内新增 tris + 15 个 `fx_fix_effect_*` 骨骼（全部 idle 组引用 socket）|
| D 单粒子 | 自制 `cf_tianxi_probe`（持续发射蓝色 glow 精灵，约 12/s）经 `AE_CL_CREATE_PARTICLE_EFFECT` 挂 `fx3` 挂点，`draw` 序列第 5 帧触发 | `particles/cf_tianxi_fx.pcf`（dmxconvert 从 text 制作）+ `particles/particles_manifest.txt`（全量 stock 清单 + `!particles/cf_tianxi_fx.pcf`） |

## 进游戏后请检查（验收标准）

1. **B（呼吸）**：枪身上的蓝色部件薄层是否以 ~2s 周期明暗呼吸？（若常亮/不可见 → $alpha 代理在 additive 下不生效，记为 B 路线失败模式）
2. **C（光片）**：蓝色薄层是否贴合在枪身正确位置、随枪运动（转动/开火/换弹不脱节）？若位置错乱 → socket 链路需修（证据在 `sockets.json`）。
3. **D（粒子）**：切枪(draw)时枪口前方 `fx3` 处是否出现蓝色光点并跟随枪口移动？切走武器后是否消失无残留？控制台若出现 `Attempted to create unknown particle system cf_tianxi_probe` → manifest/PCF 未生效，报回来。

已知不确定项：MIGI 是否把 addon 的 `particles_manifest.txt` 按 `// MIGI ADDONS` 合并；本探针 manifest 含全量 stock 条目，merge/替换两种行为下结果一致。

## 修复记录（第 3 次部署，A↔B 31 文件一致）

5. **pcf 命名不符合 MIGI 约定**（关键修复）：MIGI 的粒子 manifest 合并按
   "pcf 文件名 == addon 目录名去 `p_`/`m_` 前缀" 约定扫描（见其
   `addonTemplate/particles/particle.pcf` 与官方文档 "named
   `yourfoldername.pcf` without the addon type prefix"）。`cf_tianxi_fx.pcf`
   被静默跳过——打进 VPK 的 manifest 尾部只有 `// MIGI ADDONS` 无任何条目。
   已改名 `particles/cf_tianxi_galilar_p1.pcf`，并删除自供 manifest
   （MIGI 重新生成 manifest 并自动追加 `!particles/cf_tianxi_galilar_p1.pcf`）。
   证据：反编译 migi.exe（PyInstaller）拿到 `buildParticlesManifest` 字节码与
   常量串 `.pcf` / `!particles/` / `// MIGI ADDONS`。
6. **fx 网格仍埋在枪体内部**（关键修复）：原 socket 变换链
   `B[p]×socket_local` 含旋转，把壳旋转错位到枪体内部。用 Blender MCP
   渲染确认（Plate 只露出一个小角）。改用 **ICP 实证变换**：
   用 `BODY_01`（特效组内完整特效枪体 11186v）对 PV 枪身顶点做相似变换
   拟合 → 解得 `v_pv = B[parent].pos + 0.15·v_fx`（纯位移 + 缩放，
   旋转恒等，rmse=0.033 机器精度）。即 socket 只提供位置锚点，
   Facing=ParentAlign 使旋转跟随父对象（模型空间恒等）。
   Blender 复渲确认蓝甲片现贴合枪身表面。

## Blender 验证（MCP socket 9876）

- `blender_check.py` + `blender_send.py`：经 blender-mcp 导入 SMD 三角形、
  Workbench 渲染侧视/顶视图，fx 网格高亮蓝色。
- 渲染产物：`render_side.png` / `render_top.png` / `render_fxonly_*.png`。

## 修复记录（第 4 次部署，A↔B 35 文件一致）—— 龙眼专项

7. **fx 骨骼原点偏出枪身 ~5 单位**（本轮关键修复）：socket 骨骼的世界矩阵
   经 `anim_world(w)=MX·H·w·H⁻¹·MX` 共轭得到，但其 translation ≠
   `MXH @ socket_cf_pos`——因为 `(MXH)⁻¹·0 = H⁻¹·MX·0 ≠ 0`（MX 镜像绕
   x=-5.223 而非原点）。骨骼原点 = `MXH·(SW·q0)` 而非 `MXH·SW.trans`，
   误差随每个 socket 的旋转不同（fx15 实测偏 (4.75,0.58,4.36)）。
   网格蒙皮不受影响（W·bindW⁻¹ 消去），但 attachment 原点悬空——
   **这很可能就是之前枪口探针"等于没有"的原因之一：粒子在枪外发射**。
   修复：`fx_local` 保持 anim_world 旋转，translation 替换为
   `MXH @ socket_world_cf.trans`。修正后 fx15 骨骼 runtime 原点 =
   (3.166,20.814,-4.522)，在枪面（该 Y 处枪身 X 2.78-5.5, Z -6.6..-3.2）。
8. **龙眼 PCF**：`cf_tianxi_fx.txt` 新增 `cf_tianxi_eye`（SHINE_06 软光斑，
   蓝 (1,107,237)~(49,151,253)，rate 5，半径 1.6-2.2）+ 顶层子系统
   `cf_tianxi_eye_core`（JY_SHINE_03 亮核，淡蓝白，rate 8，半径 0.55-0.85）。
   注意 DMX 文本数组元素间**必须有逗号**，且子系统用
   `DmeParticleChild{"child" "element" "<guid>"}` 引用顶层定义——
   内嵌 `DmeParticleSystemDefinition` 会让 dmxconvert 段错误。
   `draw` 第 5 帧 `follow_attachment fx15` 创建（每次装备触发一次，
   常驻到切枪为止）。挂点 `fx15`/`fx16` 已加入 QC `$attachment`。
9. **龙眼贴图**：`cf_fx_shine06.vtf` / `cf_fx_jyshine03.vtf`（DXT5）+
   粒子用 VMT（additive + vertexcolor/vertexalpha）。

## Blender 验证产物（龙眼）

- `render_eye_fp.png`（持枪视角）、`render_eye_close.png`（特写）、
  `render_eye_left.png`、`render_eye.mp4`（48 帧呼吸循环）。
- `blender_eye.py`：eye socket 用 `MXH @ socket_cf_pos`（验证后的正确点），
  三层 sprite 片（rbw 大晕/main 主斑/core 亮核）朝相机。
- 位置实测：CF 空间 socket (-1.75,-4.24,-12.68) 距最近枪面顶点 0.078
  （在枪身上 ✓）；模型空间 (3.17,20.8,-4.5) = 枪口前段左侧 ✓。

## 复现

- PCF 源：`effects/probes/cf_tianxi_fx.txt`（DMX keyvalues2 文本）→ `dmxconvert -oe binary` 生成 `.pcf`（文件名按需改为 addon 约定名）。
- 构建：`python work/galil_ace_tianxi/native_vm/build_galilace_vm.py`（含 fx 骨骼/网格/材质/事件/部署全链）。

## 原始 L-flow-front 隔离样例（2026-09-16）

根据 `effects/review/failure_analysis_20260916.md` 的最小验收建议，当前构建已切换为：

- 仅加载原 `SGFX_BD_PLANE_02_4.LTB` 的 8 顶点/6 三角形和原 UV；按 `fix_effect_9`、`Offset=[0,1,0]`、`Sk=0.026000000536441803` 绑定。
- 原 AURA_54 24 帧封装为 `cf_fx_aura54.vtf`，VTF 7.2 / BGRA8888 / 256×128 / 24 帧 / 1 mip；材质 `fx_galilace_l_flow_front.vmt` 以 `AnimatedTexture` 11 fps 播放。
- 首轮使用节点原 Ck `[80,168,255]` 作为 additive 颜色乘数，不增强原始帧。游戏确认 24 帧螺旋能显示，但偏淡且位置偏上。
- 第二轮根据游戏画面下移 1.8 Source Z；加入原组的 `L-flow-front-COPY` 第二层，使用其原 Ck `[0,84,170]` additive 叠加。原 AURA_54 帧保持不变。用户确认略有改善，但仍偏淡、偏后；该轮 B↔C 40/40 SHA-256 一致。
- 第三轮整体前移 +4.0 Source Y，并加入原 `L-flow-back`：`PLANE_02_5` / Sk=0.037 / AURA_55 24 帧 10 fps / Ck `[89,70,249]`，不修改原帧。
- 手工龙眼交叉面片仍禁用；第三轮 eye/core PCF 各补零位置初始化器，并恢复 draw@5 的 `cf_tianxi_eye follow_attachment fx16`。游戏确认粒子显示，但未锁定到移动 CP，形成世界空间拖影，且增强 VTF + 高 rate/radius 严重过亮；第三轮 B↔C 42/42。
- 第四轮 main/core 均加入 `Movement Lock to Control Point` CP0；使用未增强的原始 SHINE_06/JY_SHINE_03。main=rate3/radius2.6–3.4/alpha120–170/life0.7–0.9，core=rate4/radius0.75–1.1/alpha160–210/life0.5–0.7。
- 第四轮游戏确认 Movement Lock 消除拖影、亮度回落，但位置偏离且 draw 事件创建的粒子切枪/换状态后消失；该轮 B↔C 42/42。
- 第五轮移除 fx15/fx16 的 `0 0 -0.9` 人工 attachment 偏移；删除 draw 事件，改为 QC `$keyvalues/particles/effect` 的 `follow_attachment fx16` 模型常驻声明。
- studiomdl 接受 236 bytes model keyvalues；三层流光不变，A↔B 42/42 SHA-256 一致。第五轮为 `PACK_VERIFY_PENDING / GAME_VERIFY_PENDING`。
