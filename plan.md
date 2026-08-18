# CF → CS:GO Legacy 武器移植重建计划

> 最后更新：2026-08-18
> 当前主目标：把 **CF M4A1-S-BornBeast（雷神 / Classic）源模型** 替换到 CS:GO Legacy **M4A4 槽位**。2026-08-18 起取消 M4A1-S 消音器状态/装卸路线；运行时内部模型固定为 `weapons/v_rif_m4a1.mdl`。
> 本文是执行计划，不是成果宣传。所有“完成”必须有仓库产物、自动校验结果和实机证据三者之一或多者支撑。

### 当前执行位置（2026-08-18）

- **A1/A2/A3：`[~]`（PASS WITH RISK）** — 官方 M4A1-S 已完成 decompile → compile → MIGI → 实机闭环，58 骨骼、序列、附件、材质和 bodygroup 结构保留；同一 Crowbar 路线和一个额外修正动画仍构成工具同源风险。
- **B1：`[!]`（REWORK）** — 57-node 层级、蒙皮 mesh 的 packed bone indices/weights 已读出，但 PC LTB v25 rigid mesh header 中的单骨骼索引尚未进入正式 decoder/report；当前 9 个枪体 mesh 的 `BoneWeightCount=0` 是错误报告。
- **B2：`[!]`（REWORK）** — bind matrix 已独立确认是 row-major、column-vector、model/global-space bone-to-model bind，packed index/weight 顺序也正确；现有 `M^-1` 后再乘 `M` 的 validator 会自证任何可逆矩阵，不能作为语义证明。
- **B2 动画子目标：`[~]`** — 目标 LTB 已确认含 8 个 clip，但正式 decoder 尚未输出关键帧。它只阻塞 R3/CF 原动作，不阻塞使用官方动画的 R1/R2、C2/C3。
- **B3：`[~]`（PASS WITH RISK）** — raw position/normal、`V -> 1-V`、原始 winding 和 9 个枪体 group 已独立复核；材质仍只是 11 个 placeholder slot，rigid bone 报告继承 B1 错误。
- **C1：`[~]`（PASS WITH RISK）** — Blender 已复核 9 个枪体 mesh：主体、01 弹匣、02 枪机/拉机柄；03–08 的几何外观已记录但精确机械语义仍 unresolved。CF 动画关键帧尚未解码，不能再把 03–08 的动态角色写成已证明结论。
- **C2：`[!]`（REWORK，但不阻塞 C3）** — 官方 58-bone skeleton 正确；01→Clip 可锁定，02→Bolt 高置信；整块 main→Parent 会错误固定其中的内置枪口/消音器（以及可能的扳机），03–08→Parent 只能作为 R1 静态降级方案。
- **C3：`[~]`（PASS WITH REQUIRED QC OVERRIDE）** — 9 个枪体 mesh 的唯一共享变换已固化，Blender 官方 reference 叠加与四标志点通过；官方 `muzzle_flash2 9.5` 偏移不适配 CF 内置枪口，D 阶段必须改为约 `1.613`，首次编译后仍需实机 Idle/FOV 确认。
- **C3-M4A4：`[~]`（PASS WITH PROVISIONAL ATTACHMENTS）** — 已拒绝复用旧 M4A1-S transform，并针对官方 M4A4 网格独立重拟合：scale `1.784443884`、轴向修正 `2.4516°`，双向 P90 均约 `1.0` Source unit。SMD 顶点域与 skeleton-global 域不能混合作附件自动证据，枪口/抛壳/FOV 保留到 D3 实机门。
- **D1：`[~]`（PASS WITH UV AND BOUNDARY ADVISORY）** — 可复现 Blender 场景已保存，官方 SMD 导入的 58-bone armature 与 C2 manifest 完全一致；9 个 EXPORT mesh 无 CF 手臂、变换已应用、法线有效。主枪身 16 个零面积 UV 面和 2,834 条开放边被保留并显式记录，未通过删真实枪面伪造 clean。
- **D2：`[~]`（旧 M4A1-S preflight，运行目标已废止）** — 几何/UV/拓扑结论仍有效，但 58-bone skeleton、`rif_m4a1_s` 与消音器 blocker 不再是 M4A4 发布门。M4A4 使用独立 57-bone reference。
- **D3：`[~]`（M4A4 R1 MAIN PASS）** — 官方 M4A4 已从本地 VPK 独立提取/反编译；主枪身已按 57-bone M4A4 QC 编译为 `v_rif_m4a1.mdl`，回环保持 57 骨、9 序列、2 附件、3,407 三角面和 `rif_m4a1`。临时 addon `p_cf_bornbeast_m4a4_d3_main_tmp` 已由用户实机确认“没有问题”。
- **D3-Clip：`[x]`（PASS）** — 01 弹匣已作为唯一新增变量绑定到 `v_weapon.M4A1_Clip`：44 个位置、36 三角面；回环 108 corners 全部保持 bone 4。官方 Idle 中 Clip 不漂移，Reload 最大分量变化 `14.908203`；用户实机确认“弹夹正常”。
- **掉落模型：`[ ]`（独立范围）** — 截图确认掉枪后仍显示官方 M4A4。这不是 D3-Clip 回归：当前仅覆盖 `v_rif_m4a1`；M4A4 掉落物实际使用独立的 `w_rif_m4a1_dropped.*`，另有 `w_rif_m4a1.*` 第三人称和 `w_rif_m4a1_mag.*` 掉落弹匣，禁止用 viewmodel 或 AK 模型改名代替。
- **D3-Bolt：`[x]`（PASS）** — 02 枪机/拉机柄组已绑定到 `v_weapon.M4A1_Bolt`：133 个位置、121 三角面；回环 363 corners 全部保持 bone 29。官方动作表明 Bolt 在 Idle/Fire/Reload 中静止，只在 Draw 中运动（最大分量 `2.261719`）；用户实机确认没有问题。
- **D3-Part03：`[x]`（PASS WITH MATERIAL ADVISORY）** — 03 已 rigid 到 Parent，用户实机确认无动作/位置问题；但官方 `rif_m4a1` 占位材质过黑，几何完整性的人工置信度有限，最终 CF 材质接入后必须复核。
- **D3-Part04：`[x]`（PASS WITH MATERIAL ADVISORY）** — 04 已 rigid 到 Parent，自动检查和用户实机确认均通过；最终表面完整性仍待 CF 材质复核。
- **D3-Part05：`[x]`（PASS WITH LOW VISUAL SENSITIVITY）** — 05 自动检查通过，用户观察无明显区别；黑色占位材质降低了逐件判断价值，因此按用户要求合并剩余静态件测试。
- **D3-Full：`[x]`（PASS WITH MATERIAL ADVISORY）** — 全部 9 个枪体 mesh 共 3,646 个位置、4,008 三角面；01→Clip、02→Bolt，03–08→Parent 静态降级，回环骨骼分布为 Parent 11,553 corners、Clip 108、Bolt 363。用户已确认整体没有问题，记录为 `d3_full_manual_game_check.json`；旧 addon 已可恢复地移入 `mods_temp`。
- **F1：`[x]`（CORRECTED DEBUG MATERIAL ACCEPTED / ARCHIVED）** — 用户对首版调试材质确认“正常”，但 F2 交叉验证发现三张辅助 TGA 的 footer/header 插在像素流中间；首版视觉结论保留、解码语义作废。修正输出与 CFRezManager 逐像素一致，用户确认黑白显示符合预期；F1 addon 已移入 `mods_temp`。
- **F2：`[~]`（PASS WITH PROVISIONAL SHADER MAPPING）** — PV DTX 的 512×256 BGR24 完整 mip 链已用跨级相关性验证；Alpha/Normal/Specular 分别只有 G/B/R 单通道携带信号；CFG 是 164 像素、B 通道变化的一维 RGB lookup strip，不是文本参数。官方本地 UI 图标确认经典雷神为黑/枪灰、银边和红色能量点缀。具体 blend/动画/查表语义仍未证明。
- **F1 修正版：`[x]`（PASS WITH GRAYSCALE LIMIT）** — 用户确认黑白显示属于预期且没有问题；因缺少颜色方向线索，不能把本次确认扩张为最终材质方向证明，但足以关闭灰度可见性门。
- **F3-Base/Phong：`[!]`（REJECTED AS RECOGNIZABLE BASE）** — 技术闭包虽通过，但实机仍是不可识别的黑白拼块。回看 atlas 后确认 Alpha-G 是带 `ACCURACY INTERNATIONAL` 字样的另一把常规武器贴图，不能继续作为雷神底色；F3 addon 已移入 `mods_temp`。
- **F4-Recognizable：`[~]`（MIGI STAGED）** — 从公开 GoldSrc 移植包的 v10 MDL 内审计并提取 `PV-M4A1_S_BORNBEAST.bmp`：完整 512² 黑/枪灰/银/红经典 atlas。当前模型和动画保持 D3 不变；底色用 DXT1，红色优势像素派生独立 self-illum mask，另加低强度 Phong。当前唯一活动 addon 为 `p_cf_bornbeast_m4a4_f4_recognizable_tmp`。
- **下一步：F4 可识别性实机门** — 只确认 atlas 是否正确贴合当前 CF 模型，以及是否能一眼认出经典黑骑士（黑枪体、银色机械件、红色纹路）；若通过，再处理红光呼吸动画和更精确高光。

---

## 0. 状态标记与完成规则

本文统一使用以下标记，避免再次把目标误写成已实现：

- `[x]`：仓库中已有可检查的产物，并已通过对应层级验证。
- `[~]`：已有候选产物，但来源、正确性或游戏内效果尚未验证。
- `[ ]`：尚未实施。
- `[!]`：已有实现已被证实错误、占位或不可作为成品继续使用。
- `[?]`：需要技术实验或人工选择后才能定方案。

任何阶段只有同时满足以下条件，才允许改为 `[x]`：

1. 有明确输入、命令、输出路径，能从干净的工作目录复现；
2. 命令失败时返回非零退出码，不能仅依赖脚本打印的 `[OK]` / `[SUCCESS]`；
3. 自动校验器验证模型、骨骼、序列、材质、音频或包结构；
4. 涉及最终游戏效果的任务，必须有 CS:GO Legacy 实机截图/视频和控制台日志；
5. 不能通过复制其他武器模型并改名来满足验收；参考 Mod 只能作为结构和技术参考。

---

## 1. 项目最终目标与分阶段交付

### 1.1 最终目标

建立一条可复用的 CF 武器移植流水线，支持：

- 从 CF REZ/LTB/DTX/WAV 资源中定位并提取目标武器；
- 保留正确的网格分件、UV、法线、骨骼权重、绑定姿态和可用的原始动作数据；
- 适配 CS:GO Legacy 目标武器自己的 Source 1 骨架、序列、事件和附件点；
- 支持 CS:GO 手臂、手套、袖子与目标武器动画；
- 将 CF 原始材质信息转换为 Source 1 可表达的 VTF/VMT，不把 Source 1 材质误称为真正 PBR；
- 将 CF 音效映射到正确的 CS:GO 音效事件并与动作对齐；
- 生成独立 MIGI addon，可安装、更新、卸载和回滚；
- 用自动检查阻止“改名复制”“空骨架”“单材质误绑”“缺序列”“材质未引用”等问题进入发布包。

### 1.2 交付顺序

不再同时推进 AK、M4A1-S、M4A4 三个槽位。先完成一个最小但真实的纵向闭环，再扩展：

1. **R0：诊断与基线**  
   固化当前失败样本，提取官方 M4A1-S 基线，建立模型/材质/动作检查器。
2. **R1：M4A1-S 静态可见 MVP**  
   雷神真实网格在官方 M4A1-S 骨架和官方基础动作上可见，比例、朝向、材质正确；先不承诺 CF 原版动作。
3. **R2：M4A1-S 功能完整的一人称版本**  
   Idle、Draw、Fire、Reload、Inspect、消音器装卸等目标槽位必需序列齐全，手套/袖子正常。
4. **R3：CF 原版动作版**  
   在确认 LTB 动画可提取后，逐条重定向 CF 动作，保留 CS:GO 必需事件与状态机兼容性。
5. **R4：材质、特效、音频与性能定稿**  
   完成 Source 1 材质翻译、音效映射、性能档位与实机回归。
6. **R5：第三人称/掉落模型与 M4A4 独立适配**  
   不再把 AK 世界模型重命名为 M4。
7. **R6：火麒麟复核与批量化**  
   用同一流水线重新审计火麒麟，之后才抽象成通用批处理。

---

## 2. 2026-08-17 仓库真实基线

### 2.1 已确认可用的基础能力

- `[x]` CF REZ 已解包到 `data/rf*/`，仓库中存在大量 LTB、DTX、WAV 等资源。
- `[x]` `CFRezManager` 能读取目标 LTB 的静态网格，并导出 OBJ/MTL。
- `[x]` DTX 解码和 PNG 输出路径已存在，目标武器的候选 PNG/VTF 也已生成。
- `[x]` 仓库有 `studiomdl.exe`、Crowbar/CrowbarDecompiler、Blender Source Tools 压缩包、VTFCmd、vgmstream、ffmpeg 和 MIGI 环境。
- `[x]` 用户 Blender MCP `127.0.0.1:9876` 可连通并接受 `get_scene_info`/`execute_code`；连接只依赖用户当前 Blender 会话，不把 Blender executable vendoring 到仓库。
- `[x]` 旧音频清洗、VPK 解析、语音分发、Blender MCP 客户端、C2 骨架计划和当前脚本语法 smoke 测试可运行；最新日志为 `logs/20260817_235528_smoke.log`，结果为 44/44 通过。
- `[~]` 火麒麟参考 Mod 的反编译文件、90 骨骼模型和动作文件可用作格式研究样本，但不能视为 CF → CS:GO 自动移植已经完成。

### 2.2 雷神源资产现状

首个目标固定为：

```text
CF 源模型：data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB
CF 主贴图：data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX
CF 高光图：data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA
CF Shader：data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG
CS:GO 目标槽位：M4A4，内部模型名 weapons/v_rif_m4a1.mdl
消音器策略：取消可拆卸消音器功能，不引入 M4A1-S Silencer 骨/附件/装卸序列
首轮不包含：M4A1-S 运行时覆盖、第三人称世界模型、掉落弹匣、其他雷神变体
```

旧失败包的静态导出基线（保留用于对照）：

| 项目 | 当前结果 | 结论 |
|---|---:|---|
| LTB 文件大小 | 166,113 bytes | 源文件存在 |
| OBJ 网格组 | 11 | 包含 `Fview-hand2`、`Fview-arm2` 和 9 个 `M4A1S_BornBeast*` 子网格 |
| OBJ 顶点 | 4,926 | 静态几何可读取 |
| OBJ 三角面 | 5,342 | 面数适合先做功能验证 |
| OBJ UV | 4,926 | 当前导出有逐顶点 UV |
| OBJ 法线 | 0 | 当前导出器没有写 `vn`，不能直接作为最终模型 |
| OBJ 材质 | 1 | 11 个网格全被错误归到 `Fview-hand2`，材质映射未完成 |
| OBJ 最大边 | 4.5 | 导出器强制居中、归一化；这不是 Source 1 的已标定尺寸 |
| M4 高光 TGA | 3,145,772 bytes | 文件存在，需验证通道含义 |
| M4 候选 4K PNG/VTF | 已存在 | 只能标记为候选，尚未证明模型实际引用或游戏效果正确 |

B3 raw-transform 导出已生成到 `work/m4a1_s_bornbeast/source_dump/b3_raw/`，统计与回环报告为 `PV-M4A1_S_BornBeast_Classic_export_report.json`：4,926 个 `v`、4,926 个 `vt`、4,926 个 `vn`、5,342 个三角面、11 个 group 和 11 个独立 material slot。旧表中的“法线 0 / 材质 1 / 最大边 4.5”只描述失败包，不再描述 B3 产物。

### 2.3 当前雷神实现已证实的问题

以下内容必须视为失败样本，不能继续标记为已完成：

- `[!]` `scripts/csgo_pack/deploy_cf_m4a1_bornbeast_migi.py` 会从 AK Mod 或 AK 编译目录取模型，再改名成 `v_rif_m4a1_s.*` / `v_rif_m4a1.*`。
- `[!]` 同一脚本把 AK 音效目录作为 M4 音效来源；这不是雷神音效映射。
- `[!]` 当前 M4 世界模型与 AK 世界模型 SHA-256 完全相同，只是文件名不同。
- `[!]` 当前 M4 动画目录直接复制自 AK；至少 `ak47_idle.smd` 与 AK 参考文件 SHA-256 完全相同。
- `[!]` `data/out/decompiled_m4a1_bornbeast/bones_define.qci` 为 0 字节。
- `[!]` 当前 M4 QC 只含 6 条 AK 风格序列，且没有 `lookat`/Inspect，也没有 M4A1-S 消音器装卸相关完整序列集。
- `[!]` `convert_obj_to_smd.py` 把全部雷神顶点刚性绑定到 bone 2，并从 AK 参考 SMD 复制节点和静态 skeleton 块。
- `[!]` 当前 M4 SMD 虽声明 90 个节点，但所有雷神顶点都只使用 bone 2；编译后的 M4 MDL 实际只保留 5 根骨骼。
- `[!]` 当前 AK 参考 MDL 为 90 根骨骼，而部署后的 `v_rif_m4a1_s.mdl` 和 `v_rif_m4a1.mdl` 都只有 5 根。
- `[!]` `csgo_hands.smd` 只有节点和 skeleton，没有三角面，不能单凭该文件声称手套/袖子已经可用。
- `[!]` 旧失败包 OBJ 不含法线；旧转换脚本在缺法线时给所有顶点写入同一个 `(0, 1, 0)` 默认法线，最终光照必然错误。B3 raw exporter 已输出真实 `vn`，旧转换脚本仍禁止作为正式入口。
- `[!]` 旧失败包 OBJ 只引用 `Fview-hand2` 材质；部署脚本生成的 `pv-m4a1_s_bornbeast.vmt` 并未被旧 M4 SMD 引用。B3 已保留独立 OBJ material slot，但真实 DTX/Shader 绑定仍待 F 阶段。
- `[!]` 旧失败包 OBJ 被居中并缩放到最大边 4.5，旧转换脚本原样写入 SMD，没有与官方 M4A1-S 的坐标、比例和握持点做标定。B3 raw 产物已保留原始坐标，标定仍属于 C3。
- `[!]` 部署/编译过程吞掉 `studiomdl` 标准输出和错误输出，之后无条件打印成功，无法证明编译过程没有警告或缺失。
- `[!]` 当前 smoke 测试仅对新武器脚本做 Python 语法检查；`convert_obj_to_smd.py`、自定义 Inspect、AK/M4 部署脚本均没有进入模型流水线 L2/L3 测试。

### 2.4 对“隐形”的正确表述

目前不能把隐形归结为一个未经隔离验证的原因。已知同时存在：骨骼被裁剪、骨架来源错误、比例过小、坐标未标定、材质名未解析、材质文件未被引用、动画和目标槽位不匹配等问题。

因此后续诊断必须逐层隔离：

1. 先用官方 M4A1-S 原模型完成反编译 → 重编译 → MIGI 回环；
2. 再只替换一个简单测试网格，保持官方骨架/材质/动作；
3. 再替换雷神主枪身，不带手臂、不带动作重定向；
4. 再添加分件、材质、动作、音频；
5. 每层都保存实机证据，哪一层首次失败就在哪一层排查。

---

## 3. 目标目录和可复现构建结构

当前脚本大量硬编码 `D:\project`、Steam 和 MIGI 绝对路径，且会直接写游戏目录。重建时建议新增以下结构；大体积中间产物应由 `.gitignore` 排除，小型清单、脚本和配置应纳入版本控制：

```text
assets/weapons/m4a1_s_bornbeast/
├── manifest.yaml             # 输入、哈希、目标槽位和构建参数
├── mesh_map.yaml             # CF 分件 → Source 骨骼/材质
├── material_map.yaml         # CF 贴图/Shader → Source 材质
├── animation_map.yaml        # CF clip → CS:GO sequence/activity/event
└── audio_map.yaml            # CF WAV → CS:GO sound event/path
work/m4a1_s_bornbeast/
├── source_dump/              # LTB 骨骼、权重、动作调试导出
├── reference_m4a1_s/         # 官方 M4A1-S 反编译基线
├── blender/                  # .blend 与 Blender 自动化脚本
├── source1/                  # SMD/DMX/QC/QCI/VMT/VTF/WAV
├── reports/                  # 差异、编译、材质、校验报告
└── evidence/                 # 实机截图、视频、控制台日志
build/m4a1_s_bornbeast/
├── game_root/                # 隔离的 studiomdl 输出根
└── addon/                    # MIGI staging
dist/p_cf_m4a1_s_bornbeast/   # 通过发布校验后的最终包
scripts/weapon_port/
├── inventory.py
├── extract_reference.py
├── inspect_ltb.py
├── build_blender_scene.py
├── export_source1.py
├── build_materials.py
├── build_audio.py
├── generate_qc.py
├── compile_model.py
├── validate_source_assets.py
├── validate_mdl.py
├── package_migi.py
└── pipeline.py
```

`manifest.yaml` 至少包含：

```yaml
id: m4a1_s_bornbeast_classic
source:
  model: data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB
  diffuse: data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX
  specular: data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA
  shader: data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG
  sha256: {}
target:
  engine: source1
  game: csgo_legacy
  weapon_slot: m4a1_s
  modelname: weapons/v_rif_m4a1_s.mdl
reference:
  kind: official_csgo_m4a1_s
  source_vpk: csgo/pak01_dir.vpk
quality:
  texture_tiers: [2048, 4096]
  preserve_original_uv: true
  require_normals: true
  require_dynamic_gloves: true
outputs:
  staging_addon: build/m4a1_s_bornbeast/addon
  release_addon: dist/p_cf_m4a1_s_bornbeast
```

规则：

- 所有脚本使用 `scripts/_paths.py` 或新的统一配置层，不再散落绝对路径；
- 所有改变游戏目录的操作拆成显式 `--deploy`；默认只写 `build/`；
- 提供 `--dry-run`、`--clean-build`、`--verbose`，清理只能作用于校验后的 `build/<weapon-id>`；
- 每次构建输出 `build_manifest.json`，记录工具版本、输入哈希、命令、产物哈希和时间；
- 当前目录执行 `git status` 返回“不是 Git 仓库”，正式重构前应建立 Git 或等价不可变快照，避免后续无法恢复和追踪。

---

## 4. 阶段 A：冻结失败样本与建立官方基线（P0）

### A1. 冻结当前失败样本

- `[x]` 将当前 `data/out/decompiled_m4a1_bornbeast`、已部署 addon 清单、MDL 头信息和关键文件哈希记录到 `work/m4a1_s_bornbeast/reports/legacy_attempt_20260817.json`。
- `[x]` 不删除当前失败文件；后续构建一律写新目录，防止新旧产物混用。
- `[x]` 标记现有 M4 部署脚本为 legacy/unsafe，禁止作为正式发布入口。
- `[x]` 把根目录误生成的 `--out`、`--out.mtl` 纳入清理清单；实际删除前确认是否需要保留。

验收：报告已明确列出当前 M4 MDL 的 5 根骨骼、6 个序列、文件哈希，以及与 AK 样本相同的文件；报告中的 `deletion_performed` 和 `game_files_modified` 均为 `false`。

### A2. 提取官方 M4A1-S 参考模型

- `[x]` 从当前 CS:GO Legacy VPK 提取官方 M4A1-S 一人称 `.mdl/.vvd/.vtx/.ani`（如有）。清单和 SHA-256 见 `work/m4a1_s_bornbeast/reference_m4a1_s/extraction_manifest.json`；原始文件保存在该目录的 `source_vpk/`。
- `[x]` 固化一键可复现入口 `scripts/csgo_pack/build_m4a1_s_reference.py`，按“VPK 提取 → 固定 CrowbarDecompiler → 报告”顺序执行。
- `[x]` 用固定版本 `tools/CrowbarDecompiler/CrowbarDecompiler(1.1).exe`（CrowbarDecompiler 0.71 CMD edition）反编译到 `work/m4a1_s_bornbeast/reference_m4a1_s/decompiled/`。
- `[x]` 保存完整 QC、reference SMD、动画 SMD、材质名、附件点和 bodygroup/skin。当前固定命令版输出格式是 QC+SMD；没有生成 DMX，报告明确记录 `dmx_files: []`，官方 `.ani` 仍由 `source_vpk/` 保留。
- `[x]` 生成机器可读报告 `work/m4a1_s_bornbeast/reference_m4a1_s/reference_report.json`，包含 58 根骨骼及层级、13 个序列、activity、事件、帧数、fps、3 个附件点、材质槽、bodygroup 和 QC/SMD bounds。
- `[x]` 不再以 AK 参考 Mod 作为 M4A1-S 的骨架和动画模板；提取清单写入 `ak_reference_used: false`，报告验证 `unexplained_ak_references: []`。

验收：目标内部名必须是 M4A1-S；不得出现未经解释的 AK 专用 parent、clip、bolt、声音事件或路径。

### A3. 官方模型回环编译

- `[x]` 不修改官方反编译资源，使用其副本在 `build/m4a1_s_bornbeast/source1/` 原样重编译。
- `[x]` `studiomdl` stdout/stderr 完整保存在 `work/m4a1_s_bornbeast/reports/a3_studiomdl.stdout.log`、`a3_studiomdl.stderr.log` 和合并日志 `a3_studiomdl.log`，退出码记录为 `0`。
- `[x]` 在隔离 `build/m4a1_s_bornbeast/game_root/` 输出，未直接覆盖 `csgo/models`；编译模型、VVD、VTX、ANI 均进入 `build/m4a1_s_bornbeast/addon/`。
- `[x]` 用同一 CrowbarDecompiler 反编译回环产物，并在 `work/m4a1_s_bornbeast/reports/a3_roundtrip_report.json` 比较骨骼/层级、序列、附件、材质、bodygroup 和 bounds，全部结构检查通过。
- `[x]` 已将独立产物部署到全新临时 MIGI addon `p_cf_m4a1_s_bornbeast_a3_tmp`；旧 addon 已移至 `migi/csgo/mods_temp`，用户实机确认模型与动作无问题，报告的 `manual_game_check.status` 为 `passed_user_confirmed`。

停止条件：官方模型原样回环无法正确显示时，先修工具链和 QC，不进入雷神网格替换。

---

## 5. 阶段 B：补齐 LTB 导出能力（P0，最高技术风险）

### B1. 当前解码器缺口

在 B1 改动前，`LithTechModelDecoder` 只保留网格名、顶点位置、三角索引、UV、候选贴图路径；二进制布局虽然会根据 `IncludeWeights` 识别 skinned stride，却把权重/法线字段丢弃。当前仍没有把以下完整信息输出到模型文档：

- 顶点法线与切线；
- 顶点骨骼索引和权重；
- LTB 节点/骨骼名与层级；
- 绑定姿态和骨骼变换；
- 动画 clip、帧率、关键帧；
- 每个网格真正的材质/Shader 关联；
- 原始坐标到导出坐标的可逆变换。

所以 README 中“动作/动画位于 LTB 内”只能说明源格式可能有数据，不能说明仓库已经能导出这些数据。

本轮 B1 已完成可验证的第一步：

- `[x]` LTB 二进制顶点流现在保留法线和最多三个显式权重值，并在存在第四个有效骨骼槽位时用残差权重恢复总和；原始坐标不做居中、缩放或旋转。
- `[x]` 新增 `CFRezManager.exe --inspect-ltb`，输出字段级 JSON 诊断，明确区分 `available`、`partial` 和 `missing`，禁止把未解析的骨骼/动作称为已支持。
- `[x]` 目标雷神 LTB 报告已生成到 `work/m4a1_s_bornbeast/source_dump/PV-M4A1_S_BornBeast_Classic_b1_report.json`：11 个网格、4,926 顶点、5,342 三角面、4,926 个有效非零法线；1,090 个顶点权重样本中 4 个权重和偏离 1.0。
- `[~]` B1 报告当时仍把骨骼索引/节点层级、绑定姿态标为未支持；B2 已补上这些字段的原生解析和验证。切线、动画 clip/帧率/关键帧和直接材质绑定仍未完成。

### B2. 两条技术路线的验证

- `[x]` 路线 1：已检查项目 `tools/` 和 PATH，没有可用的 LTB2X、Noesis 或 Model Unpacker；稳定性与许可评估因此不能假设通过。
- `[x]` 路线 2：已扩展 `LithTechModelDecoder` 原生读取法线、显式权重、残差第四权重、packed bone indices、节点名称/父子层级和 4x4 bind 矩阵；动画块仍未解析，报告明确标为 `missing`。
- `[x]` 用较小的 `PV-M4A1_BL.LTB` 和雷神目标 LTB 对照，输出字段级 dump 与矩阵报告：`work/m4a1_s_bornbeast/reports/b2_route_evaluation.json`。
- `[x]` 已验证顶点位置/法线有限且非零；两个样本的 packed bone indices 均通过节点数范围校验。雷神目标报告 1,280 个蒙皮样本、57 个节点；4 个原始显式权重和为 `0.60606098` 的样本均由有效第四骨骼槽位的残差权重修复。
- `[x]` 已验证 bind-pose 蒙皮回环：两份样本均通过，雷神目标最大位置误差约 `7.4e-15`，平均误差约 `1.5e-15`。
- `[ ]` 验证至少一个 CF 动作从首帧到末帧无 NaN、爆点和跳变。

决策门 G-B：

- `[x]` 当前工作区没有可封装的外部转换器，路线 1 暂不作为主路径。
- `[x]` 当前决策：路线 2 已足以承载真实网格、骨骼索引和 bind pose；继续解析动画块。R1/R2 使用官方 M4A1-S 动作，不能宣称已获得 CF 原版动作。
- `[x]` 在拿到真实 CF clip 前，任何动作不得标记为“CF 原版动作”。

B2 当前缺口与组件边界：

- `[x]` 原生路线已经是可复现主路径，不依赖外部转换器。
- `[ ]` CF 动画 clip、关键帧、帧率/采样率、参与骨骼和连续性校验仍未完成；这正是进入 E2 前的技术缺口。
- `[ ]` LTB 切线、直接 mesh→Shader 材质绑定仍未完成，不能把材质提示当作完整材质映射。
- `[~]` 已检索公开 LTB→LTA 工具，但没有把未验证、不可复现的二进制放入项目；`tools/third_party/ltb2lta_v2.4/` 只保留组件登记位置。若后续取得合法包，须补版本/来源/SHA-256/许可和独立回归报告。

### B3. 重做静态导出接口

- `[x]` 给 OBJ 导出增加 `--raw-transform`；raw 模式保留 LTB 原始坐标，旧的居中/4.5 缩放模式仍可复现。
- `[x]` 将两种变换模式、中心、scale、位置/UV 逆变换公式写入 `*_export_report.json`。
- `[x]` 输出真实顶点法线 `vn`；源无有效法线时报告计数为 0，不写统一 `(0,1,0)`。
- `[x]` 保留每个源 mesh 的 group 和独立 material slot；雷神目标为 11/11，材质文件不再把所有网格折叠到 `Fview-hand2`。
- `[x]` 输出统计 JSON：顶点/三角面/UV/法线/材质/骨骼影响/bounds、每 mesh checksum 和来源信息。
- `[x]` 新增 `scripts/cf_ltb/validate_b3_obj_roundtrip.py`；雷神 raw 导出回环通过：4,926/4,926/4,926、5,342 面、11 groups、无失败引用。

验收：已满足 B3 静态导出接口条件；这仍不是最终 SMD/Source 骨架验收，进入 C3 前不得部署到游戏目录。

---

## 6. 阶段 C：网格分件与 Source 骨架映射（P0）

### C1. 分离 CF 手臂与枪体

当前 11 组为：

```text
Fview-hand2
Fview-arm2
M4A1S_BornBeast
M4A1S_BornBeast01
M4A1S_BornBeast02
M4A1S_BornBeast03
M4A1S_BornBeast04
M4A1S_BornBeast05
M4A1S_BornBeast06
M4A1S_BornBeast07
M4A1S_BornBeast08
```

- `[x]` C1 已生成 11 个 mesh 的 bounds/顶点/法线/材质统计；通过 Blender MCP `127.0.0.1:9876` 以 `use_split_objects=true`、`use_split_groups=true` 导入 weapon-only staging，并生成总览图与逐件预览。
- `[~]` `M4A1S_BornBeast` 已确认主枪身，`M4A1S_BornBeast01` 为高置信弹匣，`M4A1S_BornBeast02` 为中高置信枪机/拉机柄；03–08 的几何外观已记录，但 LTB clip 关键帧尚未解码，不能宣称其动态角色已经得到动画证明。
- `[x]` 首版排除 CF `Fview-hand2`/`Fview-arm2`，采用官方 M4A1-S 手臂/手套兼容方案；校验报告记录 2 个 excluded mesh。
- `[x]` CF 特殊手部作为 `cf_arms_optional` 独立 staging bodygroup，不进入默认枪体路径。
- `[x]` 保存 `assets/weapons/m4a1_s_bornbeast/mesh_map.yaml`，为每个网格指定 group、角色、Source 骨骼候选、材质槽和是否导出；`work/m4a1_s_bornbeast/reports/c1_mesh_map_validation.json` 已通过。
- `[x]` 生成 `work/m4a1_s_bornbeast/source_dump/c1_split/weapon_only/` 与 `cf_arms_optional/`，分别包含 9 个枪体 mesh 和 2 个 CF 手臂 mesh。
- `[x]` 保存 `work/m4a1_s_bornbeast/reports/c1_blender_mcp_review.json`、`c1_blender_overview.png` 和 `c1_blender_previews/`；报告记录对象数、顶点/面数、尺寸和语义判断。

C1 当前停止条件：`mesh_map.yaml` 继续保持 `status: provisional_c1`；官方动作可以检查 Source 候选骨，但 CF LTB 的 8 个 clip 尚未解码关键帧，不能提供 01–08 的相对运动证明。01 已由 D3 实机锁定 Clip，02 已由 D3 实机锁定 Bolt；03–08 若在 R1 绑 Parent，必须明确写成静态降级而不是最终语义。

### C2. 骨架不是“凑够 90 根”

目标是匹配**当前版本官方 M4A1-S**的骨骼集合、名称、层级和动画。90 是现有 AK 样本的实测数，不应直接套用。

- `[x]` 从官方 M4A1-S 生成 58 骨骼 canonical skeleton 清单，保存为 `assets/weapons/m4a1_s_bornbeast/c2_skeleton_manifest.json`。
- `[x]` 校验并保留双手、手指、前臂、武器 parent、弹匣、枪机、枪口、抛壳口、消音器等必需骨骼；构建脚本缺骨骼即失败。
- `[x]` 生成 `work/m4a1_s_bornbeast/reports/c2_binding_plan.json`：主枪身 parent、01 Clip 候选、02 Bolt 候选、03–08 parent fallback 均明确记录。
- `[x]` 通过 Blender MCP 创建隐藏的 `CF_C2_SKELETON/CF_C2_M4A1S_Armature`，含 58 根 canonical bones；不改变当前 03–08 仅显示的视图。
- `[!]` 旧的“主枪身无原始权重”依据已失效：PC LTB rigid mesh 的 header bone index 未被 decoder 读取。main 的 CF rigid node 是 `Bone02`；R1 可将静态主体临时映射 Parent，但内置枪口/消音器和可能的扳机不能随整块 main 永久固定。
- `[x]` `M4A1S_BornBeast01` provisional 验收为 Clip 候选：C1 预览形状/位置与弹匣一致，官方 skeleton 有 `v_weapon.M4A1_Clip`；最终运动仍需 C2 动画检查。
- `[~]` R1 静态降级可让枪身刚性件使用 100% 单骨骼权重；正式 R2 仍需从 main 分离枪口/消音器和可能的扳机。手臂/手指继续使用官方模型，不从 CF 权重重建。
- `[ ]` 不用自动权重处理机械枪体；对弹匣、枪机、消音器做显式分配。
- `[ ]` reference mesh、animation SMD 和 QC `$definebone/$bonemerge` 使用一致骨骼名与层级。
- `[ ]` 编译后对比骨骼集合，必需骨骼被裁剪时立即失败。

### C3. 坐标、比例和握持姿态

- `[x]` 从官方 `v_rif_m4a1_s.smd` 与 `v_rif_m4a1_s_silencer.smd` 生成 weapon-only reference，作为唯一空间基准。
- `[x]` 直接读取 B3 `--raw-transform` OBJ；9 个枪体 mesh 共用同一变换，不做逐件 normalize/scale/hand tuning。
- `[x]` 用右手握把、左手护木、弹匣接口、裸枪口四个标志点做数值校验；误差分别约 `1.389 / 0.397 / 0.802 / 1.656` Source 单位，均在 C3 阈值内。
- `[x]` 将变换固化到 `assets/weapons/m4a1_s_bornbeast/c3_alignment_manifest.json`：轴向为 `Source X=CF X, Source Y=-CF Z, Source Z=CF Y`，统一 scale `1.863360763`，再含约 `2.9456°` 的小姿态修正和平移；矩阵使用 column-vector 约定。
- `[~]` 附件校验：官方 `flash` 距 CF 表面约 `1.656`、`shelleject` 约 `0.181`，可用；官方 silenced `muzzle_flash2` 距 CF 实际枪口约 `7.896`，D 阶段 QC 必须把 local-X offset 从 `9.5` 改为约 `1.613`。
- `[~]` CF 对齐后 XYZ bounds 完全位于官方带消音器 reference bounds 内，静态 FOV envelope 风险通过；默认 FOV/常用 viewmodel offset 的最终画面仍需 D 首次编译后的实机截图确认。
- `[x]` Blender MCP 已生成 `work/m4a1_s_bornbeast/reports/c3/c3_alignment_review.blend`、三向 overlay、附件标志图和 `c3_blender_overlay_report.json`；CF 为橙红、官方 reference 为透明蓝。

验收结论：**PASS WITH REQUIRED QC OVERRIDE**。坐标、hand-contact envelope、弹匣/枪机位置和朝向足以进入 D；不得沿用官方 `muzzle_flash2 9.5`，也不得把 C3 通过解释为 C2 的消音器拆分已经完成。Idle/FOV 实机确认属于 D 首次编译 gate，不用极端 `$bbox` 掩盖问题。

---

## 7. 阶段 D：Blender 场景和 Source 1 导出（P0）

### D1. 工具版本与场景生成

- `[x]` 已记录 Blender `4.5.12 LTS`、Blender Source Tools `3.4.3` 和加载方式：从仓库 `tools/bst_extracted/BlenderSourceTools-master` 仅在当前 session 注册，不写入 Blender 用户插件目录。
- `[x]` `build_d1_blender_scene.py` 每次从空场景建立 `REFERENCE`、`CF_WEAPON`、`CSGO_ARMS`、`EXPORT`、`GUIDES` Collection；重复执行不会叠加旧对象。
- `[x]` 场景使用 unitless Source units、`scale_length=1.0`、Z-up；OBJ 以 forward Y/up Z 导入，SMD 导入和后续导出契约均为 `Z_UP_SMD`，EXPORT object location/rotation/scale 已应用为 identity。
- `[x]` 保存 `work/m4a1_s_bornbeast/d1/d1_m4a1_s_bornbeast.blend`、预览和 `d1_scene_report.json`；`validate_d1_scene.py` 可在不启动 Blender 时校验版本、集合、骨架、几何统计和产物 SHA-256。
- `[~]` 安全清理合并 13 个精确重复顶点，未发现几何退化面和 complex non-manifold edge。主枪身仍有 16 个几何有效但 UV 面积为零的面；全体有 2,834 条开放边。二者均保留并作为 D2 advisory/blocker，不自动删面或补洞。
- `[x]` 有效 decoded LTB loop normals 在拓扑不变时原样恢复；所有 9 mesh 零长度法线为 0，机械硬边按 45° 标记。没有叠加 Weighted Normal modifier，因为真实源法线优先。

D1 验收结论：**PASS WITH UV AND BOUNDARY ADVISORY**。场景结构、工具版本、官方 58-bone armature、轴向、应用变换和法线已可复现；可以进入 D2 编写强制检查，但在 D2 明确处置 16 个零面积 UV 前不得进入正式 Source 导出。开放边是原 CF 多壳/机械结构的一部分，D2 应区分 boundary 与 complex non-manifold，不能盲目封口。

### D2. 导出前强制检查

以下任一不满足就失败：

- 分组没有受控 `mesh_map`；
- 枪体仍含 CF 手臂且目标要求动态手套；
- 存在无材质面；
- 存在统一默认法线或零长度法线；
- 权重未归一、骨骼索引无效或影响数超限；
- 可动件错误绑到主枪身；
- Source 材质名在 `material_map` 无定义；
- skeleton 与官方 M4A1-S canonical skeleton 不兼容。

D2 已实现为实际场景 preflight，而不是只检查计划文件：

- `[x]` D1 builder 每次先 purge orphan datablock，重复运行后 EXPORT/material 名称保持稳定，不再出现 `.002/.010` 后缀。
- `[x]` 9 个 EXPORT object 均有真实 vertex group 和指向 `CSGO_M4A1S_Canonical_Armature` 的 Armature modifier；逐顶点检查 weight sum=`1.0`、骨骼存在、影响数不超限。
- `[x]` R1 绑定实际落入场景：main→Parent、01→Clip、02→Bolt、03–08→Parent；03–08 和 main 明确标记 static downgrade，不视为 R2 final。
- `[x]` `material_map.json` 覆盖 9 个源 material slot，并确认目标 `rif_m4a1_s` 存在于官方 reference；其状态是 `r1_reference_placeholder`，所以只允许 R1 首次可见性编译。
- `[x]` 所有 face 有材质、法线有限且非零、方向不统一、与 face winding 一致；无几何退化面和 complex non-manifold edge。2,834 条 boundary edge 作为原始多壳结构保留并报告。
- `[x]` 16 个 collapsed UV face 已定位在 main 的两个 8-triangle 圆形端盖/环面，约位于 Source Y=`-9.1` 与 `-13.8`；它们不是几何退化面。R1 占位材质允许保留，R2 必须结合 CF 贴图确认应保留定点采样还是重新展开。
- `[x]` `build_d2_preflight_report.py` 写出逐 mesh/逐异常 face 报告；`validate_d2_report.py --profile r1_static|r2_full` 对选定 profile 返回真实退出码。

D2 gate：

- **R1：GO — `PASS WITH EXPLICIT DOWNGRADES`**。允许进入 D3 的仅是首次 Source 可见性/官方动画编译。
- **R2：NO-GO**。当前 blocker 仅有：main 内置消音器未拆、02→Bolt 尚未最终动画 overlay、03–08 仍 Parent fallback、缺最终 CF Source 1 material、collapsed UV caps 尚未结合 CF 贴图确认。CF 动画 decoder 不在此列表，因为 R2 使用官方动作。

### D3. 逐层导出

- `[x]` 独立提取并反编译官方 M4A4 `v_rif_m4a1` 基线：57 骨、9 序列、2 附件、`rif_m4a1`，不含 Silencer 骨或装卸序列。
- `[x]` 先只导出主枪身，rigid 到 `v_weapon.M4A1_Parent`，使用官方 Idle/Draw/Fire/Reload/Inspect；隔离编译与回环结构检查通过。
- `[x]` `build/m4a1_s_bornbeast_m4a4/d3_r1_main/addon/` 已部署为 `p_cf_bornbeast_m4a4_d3_main_tmp`；自动逐文件一致性通过，用户已实机确认主枪身及基础动作没有问题。
- `[x]` 01 弹匣增量已编译到 `build/m4a1_s_bornbeast_m4a4/d3_r1_clip/` 并部署为 `p_cf_bornbeast_m4a4_d3_clip_tmp`；自动绑定/动作/回环检查及用户实机确认均通过。
- `[x]` 02 枪机增量已编译到 `build/m4a1_s_bornbeast_m4a4/d3_r1_bolt/`；自动绑定/动作/回环检查通过，历史测试 addon 已移入 `mods_temp`。
- `[x]` 02 枪机层已由用户实机确认没有问题；确认记录为 `d3_bolt_manual_game_check.json`。
- `[x]` 03 已按 Parent 静态降级加入 `build/m4a1_s_bornbeast_m4a4/d3_r1_part03/`；自动检查通过，历史测试 addon 已移入 `mods_temp`。
- `[x]` 03 用户实机确认没有动作/位置问题；黑色占位材质导致完整性判断置信度有限，已记入 `d3_part03_manual_game_check.json`。
- `[x]` 04 已按 Parent 静态降级加入 `build/m4a1_s_bornbeast_m4a4/d3_r1_part04/`；自动检查通过，历史测试 addon 已移入 `mods_temp`。
- `[x]` 04 已由用户实机确认没有问题；确认记录为 `d3_part04_manual_game_check.json`，历史测试 addon 已移入 `mods_temp`。
- `[x]` 05 已按 Parent 静态降级加入 `build/m4a1_s_bornbeast_m4a4/d3_r1_part05/`；自动检查通过，历史测试 addon 已移入 `mods_temp`。
- `[x]` 05 已由用户确认无明显回归；记录为 `d3_part05_manual_game_check.json`，历史测试 addon 已移入 `mods_temp`。
- `[~]` 06–08 已按用户要求一次加入；`d3_r1_full` 包含全部 9 个枪体 mesh 并部署为 `p_cf_bornbeast_m4a4_d3_full_tmp`，待整体实机确认。
- `[ ]` 再加入手臂/手套 bodygroup。
- `[ ]` 每次只增加一个变量，保存编译报告和实机截图。

停止条件：主枪身静态版未显示前，不做自定义 Inspect、AI 材质调参或音频包装。

---

## 8. 阶段 E：动画策略与序列完整性（P0/P1）

### E1. R1/R2 先用官方 M4A4 动作

- `[ ]` 从官方 QC 自动提取完整序列清单，不手写猜测。
- `[ ]` 逐条保留 sequence、activity、fps、loop、fade、snap、事件和状态差异。
- `[x]` D3 主枪身编译已保留官方 M4A4 的 Idle、3 条 Primary Fire、Reload、Draw 和 3 条 Inspect/Lookat 序列。
- `[ ]` 把雷神弹匣、枪机绑定到官方对应武器骨骼；不实现消音器装卸状态。
- `[ ]` 验证弹匣取出/插入、枪机运动与游戏一致。
- `[ ]` Inspect 第一版使用官方 M4A4 Inspect；功能通过后再定制。

验收：序列集合与官方目标兼容，不能再用 AK 的 6 条序列代替。

### E2. CF 原版动作提取和重定向

- `[ ]` 列出 LTB 全部 clip 名、帧数、时长、fps/采样率和参与骨骼。
- `[ ]` 识别 Idle、Draw、Fire、Reload、特殊动作；不按文件顺序猜测。
- `[ ]` 建 `animation_map.yaml`，每条 CF clip 对应 CS:GO sequence，并注明官方 fallback。
- `[ ]` 建 CF 手骨 → CS:GO 手骨显式映射，记录轴向和 rest-pose 修正。
- `[ ]` 先重定向右手和武器根，再做左手 IK/接触，最后处理手指。
- `[ ]` 对弹匣、枪机、消音器保持刚性运动。
- `[ ]` 每条动作检查首尾连续、循环缝、手穿模、枪体漂移和镜头裁剪。
- `[ ]` 将 CS:GO 换弹完成、抛壳、枪口、音效事件重新对齐到 CF 动作帧。
- `[ ]` CF 无法覆盖的 M4A1-S 状态使用官方动作，并明确标注混合来源。

### E3. 雷神定制 Inspect

现有 `build_custom_inspect.py` 对 AK 动画按固定骨骼编号做正弦旋转，既没有目标 M4 骨架语义，也没接入 QC，不能作为正式实现。

- `[ ]` 以已通过实机的 M4A1-S Inspect 为基线。
- `[ ]` 按骨骼名称而非固定编号控制。
- `[ ]` 设计抬枪、展示机匣/雷电纹、停留、翻看、回 Idle 等可读关键姿态。
- `[ ]` 左手接触用 IK/约束修正，避免漂浮。
- `[ ]` 避免遮挡屏幕中心和穿近裁剪面。
- `[ ]` QC 实际加入对应 sequence/activity/event，并由校验器验证。
- `[ ]` 实机连续触发 20 次，确认无姿态累计、卡循环或回 Idle 跳帧。

---

## 9. 阶段 F：材质与贴图重建（P1）

### F1. 先解决材质引用

- `[~]` 9 个枪体 mesh 已脱离 `Fview-hand2`；F1 暂共用一个 CF atlas 调试材质，最终是否需要拆槽仍取决于 Shader/mesh 语义。
- `[x]` SMD 的 `rif_m4a1` 能在 `$cdmaterials` 下解析到唯一 VMT。
- `[x]` VMT 的 `$basetexture` 已解析到唯一存在的 VTF；路径闭环报告通过。
- `[x]` 新增 `scripts/weapon_port/validate_materials.py`，验证 SMD → QC → VMT → VTF 全链路。
- `[x]` 先用 1024² 原始辅助贴图派生的调试材质完成可见性；来源不明的旧 4K 候选明确禁用。

### F2. CF 材质审计

- `[x]` `M4A1_S_BornBeast.CFG` 已确认是 492 字节、164 像素的一维 RGB lookup strip：R/G 恒白、B 有 19 个值；它不是文本 Shader 参数。lookup 在 CF shader 中的具体采样方式仍 provisional。
- `[~]` PV DTX 容器布局、尺寸、mip 链和 BGR 顺序已闭合；它呈粉色流动/能量纹理，颜色空间、自发光和动画用途仍待实机/Shader 证据。
- `[x]` 三张辅助 TGA 已按“像素流中间插入 TRUEVISION footer/header”修复，并与 CFRezManager 输出逐像素一致：Alpha=G scalar、Normal=B scalar、Specular=R scalar；Normal-B 不是可直接提交给 Source `$bumpmap` 的 RGB 切线法线。
- `[~]` 已对照本地官方 `BUYWEAPON_INFO_M4A1_S_BornBeast.DTX` 图标确认黑/枪灰、银边、红色能量配色；Alpha-G/Specular-R/PV-DTX/CFG 的具体混合、高光、自发光和动画职责仍需 Source 分层实测。
- `[x]` `material_decode_report.json` 保存原始、解码和派生调试图的布局、哈希与被排除候选。

### F3. Source 1 材质翻译

Source 1 `VertexLitGeneric` 不是金属度/粗糙度 PBR。使用 Source 1 能表达的近似：

- `$basetexture`：漫反射；
- `$bumpmap`：可信来源的切线空间法线；
- `$phong`/`$phongexponent`/`$phongboost`：高光近似；
- `$phongmask` 或纹理 alpha：按实测选择 mask；
- `$envmap`/Fresnel：谨慎模拟金属反射；
- `$selfillum`/additive：只用于真实发光区；
- detail/scroll/proxy：CF 原效果和 Source 实机均验证后再加。

任务：

- `[ ]` 不把 AI normal/roughness/metallic 直接视为正确；与 DTX/TGA 和参考图比较。
- `[x]` 第一层只使用已验证的 Alpha-G RGB 底色与 Specular-R basemap-alpha Phong mask；Normal-B、CFG、PV DTX 全部保持关闭。
- `[ ]` 统一法线切线方向/绿色通道，游戏内用斜光验证凹凸方向。
- `[ ]` 生成 mipmap，检查远距闪烁、边缘渗色和 alpha halo。
- `[ ]` 提供 2K 默认和 4K 可选；实测后再决定是否保留 8K。
- `[ ]` 记录 VTF 格式、压缩、尺寸、mipmap、flags；法线图带正确 normal flag。
- `[ ]` 准备纯灰、纯色分件、最终三套调试材质。

验收：无紫黑格、整枪透明、错误自发光和反向法线；不同地图光照不过曝；材质全部可解析。

---

## 10. 阶段 G：音效与动画事件（P1）

### G1. 当前状态

- `[x]` `data/rf018/SND/WEAPON/M4A1-S-BornBeast/` 有 `M4A1-S-BornBeast_GasEjection.WAV`。
- `[~]` `data/out/m4a1_audio/` 有 `M4A1_BR_*`、`M4A1IronBeast_*` 候选，但文件名不足以证明都是雷神原版。
- `[!]` 现有 M4 部署从 AK 音效目录复制，必须废弃。

### G2. 来源验证

- `[ ]` 为候选 WAV 生成 ffprobe 报告：编码、采样率、位深、声道、时长、峰值。
- `[ ]` 人工试听标注：开火、消音开火、远距、Draw、MagOut、MagIn、Bolt、Gas、特殊。
- `[ ]` 记录来源 REZ/路径/哈希；无法确认的标为 unknown。
- `[ ]` 缺失事件先用官方 M4A1-S fallback，不用 AK 冒充。

### G3. Source 1 适配

- `[ ]` 从官方 M4A1-S QC/sound script 确认事件名与文件路径。
- `[ ]` 建 `audio_map.yaml`，区分模型动画事件和武器开火 sound script。
- `[ ]` 统一为已验证可用的 WAV 规格，保留原始文件，不原地覆盖。
- `[ ]` 调响度时保存测量报告并限制 true peak，不凭听感批量增益。
- `[ ]` 按目标动作帧同步 ClipOut/ClipIn/Bolt/Draw/Gas，不沿用 AK 帧号。
- `[ ]` 分别测试第一人称、第三人称/远距（若覆盖）、消音器状态。

验收：语义、时间和状态正确；无 AK 残留、尾音截断、错误定位或明显削波。

---

## 11. 阶段 H：QC 生成、编译与静态校验（P0）

### H1. QC/QCI 原则

- `[ ]` 以官方 M4A1-S QC 为模板，不从 AK QC 改名。
- `[ ]` `$modelname`、`$cdmaterials`、bodygroup、skin、attachment、sequence、event 来自 manifest/reference report。
- `[ ]` 禁止空 `$include`；检查所有 include 非空可解析。
- `[ ]` 不写死未经验证的 `$bbox/$cbox/$illumposition`；根据模型/官方基线生成并复核。
- `[ ]` 保留枪口/抛壳附件的正确骨骼和旋转。
- `[ ]` M4A4 使用另一份 manifest/QC，禁止改名 M4A1-S 编译结果。

### H2. 编译器封装

- `[ ]` `compile_model.py` 接受 manifest/staging root，不接受散落全局常量。
- `[ ]` 记录命令、cwd、工具版本、stdout、stderr、退出码、耗时。
- `[ ]` 非零退出码或缺 `.mdl/.vvd/.dx90.vtx` 立即失败。
- `[ ]` 骨骼、材质、sequence、vertex、attachment warning 默认视为失败。
- `[ ]` 先输出 `build/`，校验后才进入 addon staging。

### H3. 编译后 MDL 校验器

`validate_mdl.py` 至少验证：

- MDL magic/version 与 CS:GO Legacy 匹配；
- internal name 是 `weapons/v_rif_m4a1_s.mdl`；
- `.mdl/.vvd/.vtx` checksum 一致；
- 骨骼数量/名称满足官方 M4A1-S canonical skeleton；
- 必需手/指/前臂/武器/弹匣/枪机/消音器/附件骨骼存在；
- sequence 名、数量、activity、fps、帧数符合映射；
- Inspect 和消音器相关序列存在；
- attachment 绑定正确；
- material 列表与 addon VMT 完整对应；
- bounds 非零且不过小/大，vertex/triangle 非空；
- 不含未经允许的 `ak47` 路径、骨骼、材质、音效事件；
- 编译产物不是参考文件的改名副本。

验收：当前 5 骨骼、6 序列的失败模型必须被自动拒绝。

---

## 12. 阶段 I：自动化测试体系（P0/P1）

### L0：环境

- `[ ]` 检查 Blender、BST、Crowbar、studiomdl、VTFCmd、ffmpeg、vgmstream、MIGI 并打印版本。
- `[ ]` 检查 CS:GO Legacy build/reference VPK 与 manifest 目标一致。

### L1：语法和配置

- `[x]` Python 语法检查已有基础。
- `[ ]` 校验 YAML/JSON schema、路径和输入哈希。
- `[ ]` 禁止正式脚本包含目标机器绝对路径；默认值集中到配置层。

### L2：单元测试

- `[ ]` LTB：网格、UV、法线、权重、骨骼、动画 fixture。
- `[ ]` OBJ/SMD：索引、三角化、材质切换、法线、权重、bounds。
- `[ ]` QC：include、sequence、activity、event、attachment、material path。
- `[ ]` VMT/VTF：引用闭包、尺寸、格式、flags、mipmap。
- `[ ]` MDL：header、骨骼、序列、附件、材质、checksum。
- `[ ]` WAV：PCM/声道/采样率/峰值/时长。

### L3：集成测试

- `[ ]` fixture 一键生成 SMD/QC/VMT/VTF/WAV、编译 MDL、组 addon。
- `[ ]` 雷神完整构建只在 staging 运行，不写 Steam/MIGI。
- `[ ]` 执行所有静态校验并归档 studiomdl/validator 报告。
- `[ ]` 负例：空 QCI、单材质误绑、统一法线、全顶点单骨骼、缺 Inspect、含 AK 文件必须失败。

### L4：实机测试

- `[ ]` 用独立测试 addon，不覆盖稳定版。
- `[ ]` 自动生成测试清单/控制台命令；人工步骤填写结果和证据路径。
- `[ ]` 只有 L0-L4 满足发布条件才输出 `release_ready: true`。

---

## 13. 阶段 J：MIGI 打包、部署与回滚（P1）

### J1. Staging 结构

```text
build/m4a1_s_bornbeast/addon/
├── materials/...             # 仅实际引用的 VMT/VTF
├── models/weapons/
│   ├── v_rif_m4a1_s.mdl
│   ├── v_rif_m4a1_s.vvd
│   └── v_rif_m4a1_s.dx90.vtx
├── sound/...                 # 仅 audio_map 启用的覆盖
├── build_manifest.json
└── README.txt
```

### J2. 规则

- `[ ]` 第一版只覆盖 `v_rif_m4a1_s`，不生成假 M4A4/世界模型。
- `[ ]` 从 `build/` 的真实雷神结果复制，不从其他已安装 addon 取模型。
- `[ ]` 打包前扫描孤儿、重复材质、AK 残留和未引用大贴图。
- `[ ]` 输出清单、大小、SHA-256、总包体积。
- `[ ]` 默认只生成 staging；`--deploy` 才复制到 MIGI。
- `[ ]` 部署前备份同名旧 addon；不修改原版 VPK/模型。
- `[ ]` 提供 `--rollback <build-id>` 或手工回滚说明。
- `[ ]` 由 MIGI 负责生成/挂载和 sound cache，不盲删缓存。

验收：从空 staging 一条命令构建；移走旧 AK/M4 addon 后仍独立工作。

---

## 14. 阶段 K：实机验收矩阵（P0/P1）

### K1. 可见性和空间

- `[ ]` 首次装备可见，无紫黑、透明、极小、极大或位于相机后方。
- `[ ]` 默认 FOV 下枪身/枪口/枪托不异常裁剪。
- `[ ]` 常用 viewmodel offsets 下仍可用。
- `[ ]` Idle 无漂移，双手握持正确。

### K2. 动作

- `[ ]` Draw、Idle loop、带/不带消音器 Fire、Reload、Inspect。
- `[ ]` 装/卸消音器状态与外观一致。
- `[ ]` 切枪、死亡、回合切换后无 bind pose 或错误序列。

### K3. 手套与袖子

- `[ ]` 至少两套手套和两个不同袖子角色。
- `[ ]` 手腕无明显断裂，手指无严重穿模。
- `[ ]` 手臂材质不被雷神材质覆盖。

### K4. 附件和材质

- `[ ]` 枪口火焰位置随消音器状态正确。
- `[ ]` 弹壳从抛壳口出现且方向合理。
- `[ ]` 发光/反射在明暗地图不过曝。
- `[ ]` mipmap、法线、高光运动中无严重闪烁。

### K5. 音效

- `[ ]` 开火、换弹、拉机柄、Draw、Gas 语义正确且与帧同步。
- `[ ]` 无削波和错误 2D 全图广播。
- `[ ]` 消音器状态音效正确。

### K6. 错误、性能与证据

- `[ ]` 控制台无 missing model/material/sound、bad sequence、bone 错误。
- `[ ]` 首次加载和切枪卡顿可接受。
- `[ ]` 记录 2K/4K 显存、包体和体验差异。
- `[ ]` 保存完整视频：装备 → 开火 → 换弹 → Inspect → 卸/装消音器 → 切枪。

只有 K1-K6 通过才可称为“游戏内完成”。

---

## 15. 阶段 L：世界模型、M4A4 与火麒麟（首个闭环后）

### L1. 第三人称/掉落模型

- `[ ]` 从雷神 QV/WEAPONS 或简化 PV 建真实世界模型。
- `[ ]` 从本地 VPK 独立提取 M4A4 的 `w_rif_m4a1.*`、`w_rif_m4a1_dropped.*`、`w_rif_m4a1_mag.*`，分别确认第三人称、落地武器和掉落弹匣用途。
- `[ ]` 使用官方 M4A4 世界模型骨架、碰撞、附件、LOD 和朝向基线，不复用第一人称 57-bone viewmodel。
- `[ ]` 独立制作掉落武器/弹匣，不能复制 AK 改名。
- `[ ]` 检查持枪姿态、掉落朝向、碰撞和 LOD。

### L2. M4A4

- `[ ]` 新建独立 manifest 和官方 M4A4 reference。
- `[ ]` 重做骨架、序列、附件、材质和声音映射。
- `[ ]` 通过 M4A4 自己的回环/实机矩阵后才发布 `v_rif_m4a1.mdl`。

### L3. 火麒麟复核

- `[ ]` 证明最终枪体来自 CF LTB，不是参考 Mod 原模型。
- `[ ]` 区分 CF、CS:GO 官方、参考 Mod 动作来源。
- `[ ]` 当前 QC 实际仅 6 序列，定制 Inspect 未接入；修正后重验。
- `[ ]` 检查材质、龙眼、法线、8K 性能和 Source 1 表现。
- `[ ]` 重建世界模型和音效来源清单。
- `[ ]` 通过与雷神相同的 L0-L4、K1-K6。

---

## 16. 自动化流水线最终形态

```powershell
# 环境和输入检查
python scripts/weapon_port/pipeline.py check `
  --manifest assets/weapons/m4a1_s_bornbeast/manifest.yaml

# 在 work/build 内构建，不碰游戏目录
python scripts/weapon_port/pipeline.py build `
  --manifest assets/weapons/m4a1_s_bornbeast/manifest.yaml `
  --clean-build --verbose

# 静态验证
python scripts/weapon_port/pipeline.py validate `
  --manifest assets/weapons/m4a1_s_bornbeast/manifest.yaml

# 生成 MIGI staging
python scripts/weapon_port/pipeline.py package `
  --manifest assets/weapons/m4a1_s_bornbeast/manifest.yaml

# 用户确认后部署
python scripts/weapon_port/pipeline.py deploy `
  --manifest assets/weapons/m4a1_s_bornbeast/manifest.yaml
```

依赖关系：

```text
输入清单/哈希
  → LTB/DTX/WAV 检查
  → 官方目标模型基线
  → Blender 网格/骨架映射
  → SMD/DMX + QC/QCI
  → VMT/VTF + WAV
  → 隔离 studiomdl 编译
  → MDL/材质/音频静态校验
  → MIGI staging
  → 实机验收
  → dist 发布
```

任何上游失败，下游不得继续或打印成功。

---

## 17. 风险、决策点与降级

| 风险 | 影响 | 当前判断 | 缓解 |
|---|---|---|---|
| LTB 骨架/动画未解析 | 无法立即做 CF 原版动作 | 最高 | R1/R2 先用官方动作，R3 单独攻克 |
| OBJ 归一化且无法线 | 比例、位置、光照错 | 已证实 | raw export、法线、变换报告 |
| 材质映射丢失 | 紫黑/透明/错误材质 | 已证实 | mesh/material map + 引用闭包 |
| 目标骨架被裁剪 | 动画、手套、附件失效 | 已证实 | 官方 M4 skeleton 编译后差异检查 |
| M4A1-S/M4A4 状态不同 | 改名模型功能缺失 | 高 | 首轮只做 M4A1-S，M4A4 独立 |
| AI 4K/8K 不可信或过重 | 失真/显存/加载问题 | 中高 | 原图/2K 先验收，4K 可选，8K 实测 |
| 音效来源混杂 | 其他武器冒充原版 | 已证实 | 逐条溯源，缺失用明确 fallback |
| 脚本直接写 Steam/MIGI | 污染、难回滚 | 高 | staging、显式 deploy、备份 |
| 无 Git 历史 | 无法追踪恢复 | 高 | 开工前 Git 或不可变快照 |
| Legacy 版本差异 | 骨架/序列变化 | 中 | 记录游戏 build/VPK/reference 哈希 |

---

## 18. 实际执行顺序

### 第一批：先自动判定真假

1. `[ ]` 冻结失败样本并生成哈希/结构报告。
2. `[ ]` 创建雷神 manifest 和目录结构。
3. `[ ]` 提取、反编译、报告官方 M4A1-S。
4. `[ ]` 完成官方 M4A1-S 回环编译和实机验证。
5. `[ ]` 写 SMD/QC/MDL/material validator，让当前失败样本必定被拒绝。

### 第二批：真实雷神静态闭环

6. `[ ]` LTB/OBJ 导出补 raw transform、法线、分组、材质槽。
7. `[x]` 通过 Blender MCP 分离 CF 手臂和 9 个枪体子件，输出 C1 staging 与预览；未决件进入后续语义复核。
8. `[ ]` 用官方 rig 标定比例、轴向、握持点、附件点。
9. `[ ]` 只导出主枪身，用纯色材质/官方 Idle 编译并实机显示。
10. `[ ]` 逐个加入弹匣、枪机、消音器、手臂/手套。

### 第三批：补齐目标槽位功能

11. `[ ]` 接入官方 M4A1-S 完整序列/事件。
12. `[ ]` 完成 Draw/Fire/Reload/Inspect/消音器状态矩阵。
13. `[ ]` 解决骨骼裁剪、手穿模和附件错位。

### 第四批：还原 CF 特色

14. `[ ]` 完成 LTB 骨骼/权重/动画技术验证。
15. `[ ]` 逐条重定向 CF 动作并保留官方 fallback。
16. `[ ]` 重建雷神定制 Inspect。
17. `[ ]` 解码 CF Shader，完成材质/特效翻译。
18. `[ ]` 完成音频溯源、转换和事件同步。

### 第五批：发布与扩展

19. `[ ]` 生成独立 MIGI staging 并跑静态校验。
20. `[ ]` 跑完 K1-K6 并归档证据。
21. `[ ]` 发布雷神包，更新 README 的真实能力/限制。
22. `[ ]` 再做世界模型、M4A4、火麒麟复核和通用批处理。

---

## 19. 雷神最终 Definition of Done

只有全部满足才算完成：

- `[ ]` 枪体可追溯到目标 CF LTB，不是参考 Mod/AK 改名副本；
- `[ ]` 分件、UV、法线、材质槽、Source 坐标正确；
- `[ ]` 编译后骨骼满足官方 M4A1-S 要求，手套/袖子实机正常；
- `[ ]` 完整必需序列、activity、event、消音器状态工作；
- `[ ]` 声称 CF 原版的动作可追溯到 LTB clip；其余明确为官方 fallback；
- `[ ]` SMD 材质、QC 路径、VMT、VTF 全链路解析；
- `[ ]` 材质经 Source 1 实机验证，不用“PBR/4K/8K”标签代替正确性；
- `[ ]` 音效逐条有来源/用途，与动画同步，无 AK 冒充；
- `[ ]` studiomdl 日志无未处理的模型/骨骼/材质/序列问题；
- `[ ]` `.mdl/.vvd/.vtx` 和 addon 通过自动检查；
- `[ ]` 移除旧参考 addon 后仍独立运行；
- `[ ]` K1-K6 全通过，并保存截图、视频、控制台日志；
- `[ ]` 有从 manifest 到 dist 的可复现命令和回滚说明；
- `[ ]` README 已同步真实完成度、用法和限制。

在此之前，项目状态应描述为：

> CF 资源解包、静态网格/贴图候选提取和部分 Source 工具链已经具备；雷神与火麒麟的完整 CS:GO 武器移植仍在重建中，当前已部署包不作为有效成品。
