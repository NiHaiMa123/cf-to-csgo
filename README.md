# CF to CS:GO Modding Toolkit (穿越火线转 CS:GO 资源解包与 Mod 工具库)

本项目是将 **穿越火线 (CrossFire)** 的音频/模型等游戏资源提取、清洗并转换为 **Counter-Strike: Global Offensive (CS:GO)** 兼容 Mod 的全套一站式工具集合。

包含：CF REZ 解密解包、假 WAV 音频修复、CS:GO VPK 结构解析、MIGI 自动化封包部署及 GSI 游戏联动工具。

## 当前项目方向

项目当前优先目标不是立刻证明某一套候选资产就是最终雷神，而是先建立稳定、可重复的 **CF 武器 → CS:GO Legacy Source 1** 转换流水线。唯一权威进度、当前阶段和后续顺序见 [`plan.md`](plan.md)；README 以下内容主要是工具用法、历史实验和证据索引，不再单独维护另一套阶段状态。

- Active runtime 已统一为 **M4A4**：`weapons/v_rif_m4a1.mdl`、官方 M4A4 57-bone skeleton 和 9 个 sequence。
- 当前可运行版本是 `Prototype`：本地 CF 候选 LTB + 官方 M4A4 动作 + 参考材质，已经跑通编译、MIGI 和实机闭环。
- 当前网络下载材质只允许用于 `REFERENCE/PROTOTYPE`；`final_cf_material=false`，不能视为最终 F 阶段完成。
- 最终模型、材质、动画和声音必须来自本地 CF 原始资源；“真正雷神是哪套 LTB/DTX”是流水线稳定后独立执行的资产定位任务。
- M4A1-S skeleton、C2/D2 和 silencer 相关内容均为历史研究证据，不是当前 M4A4 路线的 blocker，也不得重新成为 active route。

Prototype 的权威构建输入/输出由 [`assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`](assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json) 和 [`P4_TASKS.md`](P4_TASKS.md) 定义；MIGI 现场状态只在 `plan.md` 记录。

### P4 证据索引（不重复维护阶段状态）

- 流水线入口：`scripts/weapon_port/pipeline.py`；P4 安全 Inspect：`--inspect-policy frozen_noop_safe`（`safe_idle_fallback` 兼容别名）。
- 自动闭环报告：`work/m4a1_s_bornbeast/p4_prototype_01/{check_report,build_report,validation_report,upstream_trace_report}.json`。
- 当前 package/staging：`work/m4a1_s_bornbeast/p4_prototype_01/{package,staging}/`；当前唯一 BornBeast addon 为 `p_cf_bornbeast_m4a4_p4_frozen_noop_01`，部署记录和用户 Gate 见 `deploy_report.json`、`prototype_01_game_regression.json`。
- 用户实机记录：`prototype_01_game_regression.json`；Inspect 可见动作/手部 retarget 已明确移入 P7，P4 只验收触发后的安全状态。

---

## 📁 目录结构与组件说明

```text
D:\project\cf_to_csgo\
├── CFRezManager\              # C# WPF 原生 CF REZ 资源管理器工程（可视化解包/预览）
├── scripts\                   # 各阶段处理脚本库
│   ├── _paths.py              # 共享路径解析（默认项目内路径，支持环境变量覆盖供沙盒测试）
│   ├── cf_extract\            # 阶段① CF 资源解包（REZ / FMOD bank）
│   │   ├── extract_all.py     # Python 版 REZ 自动 XOR 解包脚本
│   │   └── extract_fmod.py    # FMOD / FSB 音频格式解包脚本
│   ├── audio_clean\           # 阶段② 音频清洗与分类
│   │   ├── clean_wavs.py      # 假 WAV 头部修复与标准 PCM WAV 洗白脚本
│   │   └── categorize_voices.py  # 语音分类统计脚本
│   ├── csgo_pack\             # 阶段③ CS:GO VPK 解析与 Mod 打包部署
│   │   ├── parse_vpk.py       # CS:GO pak01_dir.vpk 快速目录解析器
│   │   ├── unpack_vpk_voices.py   # CS:GO 全阵营 1.8 万语音 VPK 批量解包提取器
│   │   ├── package_tts_migi.py    # 自动分发并打包至 MIGI addons 的部署脚本
│   │   ├── convert_audio.py   # CS:GO 音频标准格式重采样脚本
│   │   └── fix_planting_voices.py # 炸弹与无线电语音修复脚本
│   ├── cf_ltb\                # 阶段 B/C：LTB 诊断、OBJ 分件与 Blender MCP 复核
│   │   ├── evaluate_b2_routes.py # 原生解码器/外部转换器决策门报告
│   │   └── blender_mcp_call.py   # 127.0.0.1:9876 JSON-TCP 最小客户端
│   └── gsi\                   # 阶段④ CS:GO GSI 游戏状态实时联动
│       ├── gsi_voice_bot.py   # GSI 游戏状态实时联动播报机器人
│       ├── gsi_voice_bot_debug.py # GSI 调试脚本
│       └── start_bot.vbs      # GSI 后台静默启动脚本
├── migi_tools\                # MIGI 工具与底层逆向工程库
│   ├── migi.exe               # MIGI 原版执行程序备用包
│   ├── migi.exe_extracted\    # MIGI 逆向工程包（内置 Valve 官方 vpk.exe 打包工具）
│   └── pyinstxtractor.py      # PyInstaller 逆向提取工具
├── assets\weapons\            # 目标武器的可审计映射与 manifest
│   └── m4a1_s_bornbeast\mesh_map.yaml # C1：CF mesh → 导出策略/Source 候选骨骼/材质槽
├── tools\                     # 第三方音视频与游戏解码工具链
│   ├── vgmstream\             # 万能游戏音频解码器（支持 FSB/假 WAV 转标准 WAV）
│   └── third_party\           # 按版本隔离的可选组件登记区（当前不 vendoring LTB 转换器）
├── data\                      # 存放解包与清洗后的中间数据
│   ├── Snd2_Cleaned\          # 修复后的 CF 标准 PCM WAV 语音库
│   ├── FMOD_Voices\           # FMOD bank 解包出的语音
│   ├── rvc\tts\               # RVC TTS 稳定输入目录（外部生成后复制至此）
│   ├── rvc\tts_processed\     # TTS 标准化处理输出
│   └── tmp\                   # 测试沙盒（每次测试自动清理，不保留）
├── logs\                      # 测试日志（沙盒测试的唯一保留物）
└── tests\                     # 沙盒测试模块
    ├── run_smoke.py           # 主入口：python tests\run_smoke.py
    ├── checks.py              # 环境自检 / 语法 / 沙盒冒烟检查逻辑
    └── logger.py              # 日志工具（控制台 + logs/ 文件）
```

---

## 🛠️ 核心模块与使用指南

### 一、 CF 资源解包与音频修复 (`scripts/cf_extract/` & `CFRezManager/`)

#### 1. 可视化解包（推荐）
* 打开 [`CFRezManager/CFRezManager.sln`](file:///D:/project/cf_to_csgo/CFRezManager)，直接编译运行 WPF 工具；
* 支持直接加载 CF 安装目录下的 `.rez` 文件（如 `rez/Snd2.rez`、`rez/RF016.REZ`），具备内置 XOR 解密、文件树查看与 FMOD 音频预览。

#### 2. Python 批量解包
* 运行 `python scripts/cf_extract/extract_all.py`，内置 256 字节 XOR 解密密钥表，可全自动将 REZ 提取为散文件。

#### 3. 为什么 CF 解包出的 WAV 很多“是假的/读不了”？（核心修复）
* **原因**：CF 的 `Snd2.rez` 中提取的很多 `.wav` 文件实质上并非标准 RIFF PCM 格式，而是包裹了非标准头部、ADPCM 压缩或 FMOD/FSB 音频流，导致常规播放器或代码报错；
* **修复方法**：
  * 运行 `python scripts/audio_clean/clean_wavs.py`，脚本会自动去除脏数据头并重构标准 PCM WAV 头部，输出到 `data/Snd2_Cleaned/`；
  * 或使用 `tools/vgmstream/vgmstream-cli.exe -o output.wav input.wav` 进行通用无损转码。

#### 4. CF 枪模 / 模型解包（CFRezManager 命令行）

已用 `extract_all.py` 将 CF 的 REZ 解包为散文件，存放在 `data/rf*/`（96 个 REZ 包）。其中模型与贴图资源概况：

| 资源 | 数量 | 说明 |
|------|------|------|
| `.ltb` 模型 | 21,216 | LithTech Jupiter 二进制模型（**LZMA 压缩**） |
| `.dtx` 贴图 | 20,218 | CF 专用纹理，解码为 PNG |
| `.wav` 音频 | 3,765 | 角色/武器语音等 |
| `.spr` / `.lta` / `.dat` | 少量 | 精灵 / 地图 / 世界模型 |

**目录结构**（`data/rf016/Models/`）：
- `PLAYERVIEW/` — 第一人称手+枪模型（约 1.2 万，含大量皮肤变体）
- `WEAPONS/` — 武器展示模型（约 2,650，含皮肤变体）
- `CHARACTER/` — 角色模型（约 2,044，**87/150 含蒙皮骨骼**，动画基础）
- `ModelTextures/WEAPONS` — 武器贴图（在 `rf017`）

**枪种可识别**：文件名与 mesh 名直接对应枪种（AK47、M4A1、AWM、M200、P90、MP5、GLOCK-18、SVD 等 20+ 种，含大量皮肤变体）。注：部分皮肤（如 AK47-火麒麟）在文件内**无独立命名**，为共用基础枪模 + 专属贴图。

**完整导出 OBJ/MTL/贴图**（需 .NET 8 SDK）：

```powershell
# 先构建（一次）
dotnet build .\CFRezManager.csproj
# 导出枪模为 OBJ + MTL + 贴图
.\CFRezManager\bin\Debug\net8.0-windows7.0\CFRezManager.exe `
  --export-obj --root "D:\project\cf_to_csgo\data\rf016" `
  --model "Models/WEAPONS/AK47.LTB" --output ".\out\AK47.obj"
```

已实测 `AK47.LTB`（1609 顶点 / 798 面）成功导出 `AK47.obj + AK47.mtl + AK47_textures\AK47.png`。动作/动画数据位于 LTB 骨架内，当前导出聚焦静态网格 OBJ。

**LTB 字段诊断（阶段 B1）**：先构建 `CFRezManager`，再对目标 LTB 运行：

```powershell
dotnet build .\CFRezManager\CFRezManager.csproj --no-restore
& ".\CFRezManager\bin\Debug\net8.0-windows7.0\CFRezManager.exe" `
  --inspect-ltb `
  --input ".\data\rf016\Models\PLAYERVIEW\PV-M4A1_S_BornBeast_Classic.LTB" `
  --output ".\work\m4a1_s_bornbeast\source_dump\PV-M4A1_S_BornBeast_Classic_b1_report.json"
```

该报告会保留原始坐标，并逐网格记录法线、UV、权重值、bounds、材质提示和校验结果；当前可解析蒙皮 mesh 的 packed bone indices、LTB 节点名称/父子层级和绑定矩阵。审计已确认 PC LTB v25 rigid mesh header 另有单骨骼索引，现有正式 decoder 尚未写入该字段，因此 9 个枪体 mesh 的 `BoneWeightCount=0` **不是事实**，不得作为 C2 绑定依据。现有 bind-pose 回环又是同一矩阵先逆后正乘，只能证明矩阵可逆，不能独立证明 local/model space、矩阵顺序或骨骼索引语义。

**两条路线评估（阶段 B2）**：

```powershell
python scripts/cf_ltb/evaluate_b2_routes.py
```

该命令对 `PV-M4A1_BL.LTB` 与候选 LTB 做字段级对照，并记录外部转换器可用性；结果写入 `work/m4a1_s_bornbeast/reports/b2_route_evaluation.json`。审计后的可信结论是：57-node hierarchy 真实存在；蒙皮记录中的 packed bone bytes 是直接 node index（`255` sentinel），显式 weights 在前、残差 weight 在后；bind matrix 是 row-major、column-vector、model/global-space bone-to-model bind，子级 local 应按 `inverse(parentGlobal) * childGlobal` 计算。报告中的 `7.4e-15` 回环误差是自验证结果，不能继续写成这些语义“已经被 validator 证明”。目标 LTB 实际含 8 个 CF clip，但正式 decoder 尚未输出关键帧；它只阻塞未来 CF 原动作，不阻塞当前使用官方 M4A4 动作的 Prototype。

项目没有把外部 LTB 转换器二进制混进源码树。`tools/third_party/ltb2lta_v2.4/` 仅作为组件登记目录；如果以后取得合法、可复现的工具包，应连同版本、来源、SHA-256 和许可说明放入该目录，再由报告记录，不要直接放到 `data/` 或游戏目录。

**组件盘点**：当前 smoke 已确认 Python、ffmpeg、vgmstream、`vpk`、CF 目录、CS:GO Legacy 目录和 .NET 构建链可用；没有会阻塞当前 B2 原生路线的必需组件。缺少的是可选的外部 `LTB2X`/`LTB2LTA`/`Model_Unpacker` 转换器，以及仓库内尚未实现的 CF 动画块解析器。仓库仍只有 Blender Source Tools 压缩包、没有 Blender executable；本轮由用户启动的 Blender MCP `127.0.0.1:9876` 完成 C1 可视化复核，因此不把 Blender 二进制或插件缓存复制进项目。

**静态导出（阶段 B3）**：

```powershell
dotnet build .\CFRezManager\CFRezManager.csproj --no-restore
dotnet run --project .\CFRezManager\CFRezManager.csproj --no-build -- `
  --export-obj --raw-transform `
  --root ".\data\rf016" `
  --model "Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB" `
  --output ".\work\m4a1_s_bornbeast\source_dump\b3_raw\PV-M4A1_S_BornBeast_Classic.obj"
python scripts/cf_ltb/validate_b3_obj_roundtrip.py `
  --report ".\work\m4a1_s_bornbeast\source_dump\b3_raw\PV-M4A1_S_BornBeast_Classic_export_report.json"
```

`--raw-transform` 保留原始坐标并写出 `vn`、独立 mesh group/material、MTL、纹理诊断和 `*_export_report.json`。报告记录可逆变换、bounds、骨骼影响计数和 checksum；round-trip 校验失败时返回非零退出码。该产物只位于 `work/`，不会写入 Steam 或 MIGI。

**网格分件（阶段 C1）**：

```powershell
python scripts/cf_ltb/validate_c1_mesh_map.py `
  --map ".\assets\weapons\m4a1_s_bornbeast\mesh_map.yaml" `
  --b3-report ".\work\m4a1_s_bornbeast\source_dump\b3_raw\PV-M4A1_S_BornBeast_Classic_export_report.json" `
  --reference-report ".\work\m4a1_s_bornbeast\reference_m4a1_s\reference_report.json" `
  --output ".\work\m4a1_s_bornbeast\reports\c1_mesh_map_validation.json"

python scripts/cf_ltb/split_c1_meshes.py `
  --obj ".\work\m4a1_s_bornbeast\source_dump\b3_raw\PV-M4A1_S_BornBeast_Classic.obj" `
  --map ".\assets\weapons\m4a1_s_bornbeast\mesh_map.yaml" `
  --output-dir ".\work\m4a1_s_bornbeast\source_dump\c1_split"
```

C1 默认只保留 9 个 CF 枪体 mesh；`Fview-hand2` 与 `Fview-arm2` 输出到独立的 `cf_arms_optional` staging，当前 M4A4 Prototype 不把 CF 手臂并入 weapon mesh。编号件中 01 已作为弹匣、02 已作为枪机/拉机柄；03–08 在 Prototype 中使用 Parent fallback，最终语义留到目标资产确认后处理。

用户已启动 Blender MCP 时，可用下面的最小客户端确认端口并执行 Blender Python：

```powershell
python scripts/cf_ltb/blender_mcp_call.py get_scene_info
python scripts/cf_ltb/blender_mcp_call.py execute_code `
  --params '{"code":"import bpy\nprint(len(bpy.data.objects))"}'
```

本次 C1 复核使用 `use_split_objects=true`、`use_split_groups=true` 导入 weapon-only staging，并整理到 Blender 的 `CF_C1_REVIEW` collection；生成 `work/m4a1_s_bornbeast/reports/c1_blender_overview.png`、逐件预览目录和 `c1_blender_mcp_review.json`。结果确认主体、`M4A1S_BornBeast01`（弹匣）以及 `M4A1S_BornBeast02`（枪机/拉机柄）；03–08 的几何已单独检查，但 CF 动画关键帧尚未解码，因此其动态角色保持 unresolved，不能用尚未实现的 clip decoder 作为绑定证据。

**历史骨架研究（旧阶段 C2；非 active runtime）**：

```powershell
python scripts/cf_ltb/build_c2_skeleton_plan.py `
  --reference-report ".\work\m4a1_s_bornbeast\reference_m4a1_s\reference_report.json" `
  --mesh-map ".\assets\weapons\m4a1_s_bornbeast\mesh_map.yaml" `
  --skeleton-output ".\assets\weapons\m4a1_s_bornbeast\c2_skeleton_manifest.json" `
  --binding-output ".\work\m4a1_s_bornbeast\reports\c2_binding_plan.json"
```

该步骤曾以官方 M4A1-S 的 58 根骨骼研究主枪身、弹匣、枪机及未决件的候选绑定。`c2_binding_plan.json` 不是当前 M4A4 权重文件，也不是 active gate；可复用的网格语义结论已转入 M4A4 D3，silencer 相关结论只作为历史证据保留。

**历史 M4A1-S 坐标标定（旧阶段 C3）**：

```powershell
python scripts/cf_ltb/build_c3_alignment.py `
  --raw-obj ".\work\m4a1_s_bornbeast\source_dump\b3_raw\PV-M4A1_S_BornBeast_Classic.obj" `
  --weapon-only-obj ".\work\m4a1_s_bornbeast\source_dump\c1_split\weapon_only\PV-M4A1_S_BornBeast_Classic_weapon_only.obj" `
  --reference-smd ".\work\m4a1_s_bornbeast\reference_m4a1_s\decompiled\v_rif_m4a1_s.smd" `
  --silencer-smd ".\work\m4a1_s_bornbeast\reference_m4a1_s\decompiled\v_rif_m4a1_s_silencer.smd" `
  --output-dir ".\work\m4a1_s_bornbeast\source_dump\c3_alignment" `
  --manifest-output ".\assets\weapons\m4a1_s_bornbeast\c3_alignment_manifest.json"

# Blender MCP 在线时生成可复现 overlay、附件图和 .blend
python scripts/cf_ltb/blender_mcp_call.py execute_code --timeout 120 `
  --params '{"code":"exec(compile(open(r\"D:\\project\\cf_to_csgo\\scripts\\cf_ltb\\build_c3_blender_scene.py\", encoding=\"utf-8\").read(), \"build_c3_blender_scene.py\", \"exec\"))"}'
```

C3 只接受 B3 raw OBJ，并把同一个相似变换应用到全部 9 个枪体 mesh。固化轴向是 `Source X=CF X, Source Y=-CF Z, Source Z=CF Y`，统一 scale 为 `1.863360763`，再含约 `2.9456°` 的小修正；完整 column-vector 4×4 矩阵在 `assets/weapons/m4a1_s_bornbeast/c3_alignment_manifest.json`。自动报告位于 `work/m4a1_s_bornbeast/source_dump/c3_alignment/c3_alignment_report.json`，Blender 叠加证据位于 `work/m4a1_s_bornbeast/reports/c3/`。

四标志点与包围盒 gate 已通过，但该变换属于旧 M4A1-S reference。当前 M4A4 已使用独立的 `c3_alignment_m4a4_manifest.json`，不得复用这里的 scale、attachment offset 或 silencer 假设。

**历史 Blender 构建场景（旧阶段 D1）**：

Blender MCP `127.0.0.1:9876` 在线时运行：

```powershell
python scripts/cf_ltb/blender_mcp_call.py execute_code --timeout 120 `
  --params '{"code":"exec(compile(open(r\"D:\\project\\cf_to_csgo\\scripts\\cf_ltb\\build_d1_blender_scene.py\", encoding=\"utf-8\").read(), \"build_d1_blender_scene.py\", \"exec\"))"}'

python scripts/cf_ltb/validate_d1_scene.py `
  --report ".\work\m4a1_s_bornbeast\d1\d1_scene_report.json"
```

构建脚本固定使用 Blender `4.5.12 LTS` 和仓库内 Blender Source Tools `3.4.3`；插件只在当前 Blender session 从 `tools/bst_extracted/BlenderSourceTools-master` 注册，不复制到用户插件目录。场景从空白状态重建 `REFERENCE`、`CF_WEAPON`、`CSGO_ARMS`、`EXPORT`、`GUIDES` 五个 Collection，使用 unitless Source units、Z-up 和 `Z_UP_SMD` 导出契约。官方 SMD 实际导入的 58 根骨骼已与 C2 canonical manifest 逐名、逐父节点完全匹配。

最终 D1 EXPORT 含 9 个 CF 枪体 mesh、3,633 顶点和 4,008 面；不含 CF 手臂，object transform 已应用，零长度法线、几何退化面和 complex non-manifold edge 均为 0。清理安全合并 13 个精确重复顶点，但保留了 16 个几何有效、UV 面积为零的主枪体面和 2,834 条开放边：删除这些面或自动封口会改变真实枪体，因此它们被写入 D1 report，留给 D2 结合材质/部件语义强制处理。

产物位于 `work/m4a1_s_bornbeast/d1/`：可打开的 `d1_m4a1_s_bornbeast.blend`、`d1_export_scene.png` 和带 SHA-256 的 `d1_scene_report.json`。

**历史 M4A1-S 导出前检查（旧阶段 D2）**：

```powershell
# Blender 当前打开 D1 场景时，生成不修改场景的 preflight report
python scripts/cf_ltb/blender_mcp_call.py execute_code --timeout 120 `
  --params '{"code":"exec(compile(open(r\"D:\\project\\cf_to_csgo\\scripts\\cf_ltb\\build_d2_preflight_report.py\", encoding=\"utf-8\").read(), \"build_d2_preflight_report.py\", \"exec\"))"}'

# R1 必须返回 0
python scripts/cf_ltb/validate_d2_report.py `
  --report ".\work\m4a1_s_bornbeast\d2\d2_preflight_report.json" `
  --profile r1_static

# 历史 r2_full 结果仅供研究；不再是当前 M4A4 gate
python scripts/cf_ltb/validate_d2_report.py `
  --report ".\work\m4a1_s_bornbeast\d2\d2_preflight_report.json" `
  --profile r2_full
```

D2 直接读取 Blender 中的实际 EXPORT object，而不是信任 C2 JSON 候选：逐顶点验证 vertex group、weight sum、骨骼名、影响数和 Armature modifier；同时检查 mesh map、CF 手臂泄漏、材质面、`material_map.json`、法线/翻面、UV、退化/非流形、object transform、58-bone canonical skeleton 及 C3 `muzzle_flash2` override。

当前 `r1_static` 为 `PASS_WITH_EXPLICIT_DOWNGRADES`：main→Parent、01→Clip、02→Bolt、03–08→Parent 均已实际写进场景，所有顶点为 100% 单骨骼权重；官方 `rif_m4a1_s` 只是明示的首次编译占位材质。16 个零面积 UV 面已定位为 main 上两个各 8 面的 collapsed circular caps，并非几何退化；R1 可保留定点采样，不能声称 CF 材质已经正确。

这份 D2 报告属于旧 M4A1-S 运行目标。2026-08-18 已按用户决定切换到 M4A4，并取消可拆卸消音器/装卸序列；D2 的几何、UV、法线和拓扑结论继续有效，58-bone M4A1-S skeleton、`rif_m4a1_s` 以及“必须拆消音器”的 blocker 不再直接作为 M4A4 gate。

### D3：M4A4 主枪身 R1

官方 M4A4 基线从本地 CS:GO Legacy VPK 独立提取到 `work/m4a1_s_bornbeast/reference_m4a4/`。它的真实内部名是 `weapons/v_rif_m4a1.mdl`，含 57 骨、9 序列、2 附件和 `rif_m4a1` 材质；不存在 M4A1-S 的 Silencer 骨、消音器 bodygroup 或装卸序列。

```powershell
# 需要带 vpk 包的 Python；只读取游戏 VPK
python scripts/csgo_pack/extract_m4a4_reference.py

# 固定 CrowbarDecompiler 反编译后生成通用报告
python scripts/csgo_pack/report_m4a1_s_reference.py `
  --reference-dir work/m4a1_s_bornbeast/reference_m4a4 `
  --weapon M4A4 --expected-modelname 'weapons\v_rif_m4a1.mdl' `
  --schema cf2.m4a4.reference-report.v1

# 隔离编译主枪身并自动回环反编译；不写游戏/MIGI
python scripts/csgo_pack/build_d3_m4a4_r1.py

# 显式部署到全新的临时 MIGI addon（已部署目标可重复校验，但不会覆盖不同内容）
python scripts/csgo_pack/build_d3_m4a4_r1.py --deploy-migi

# D3 下一层：在已通过的主枪身上只增加 01 弹匣
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer clip --deploy-migi

# D3 Bolt 层：在已通过的主枪身+弹匣上只增加 02
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer bolt --deploy-migi

# D3 03 层：静态绑定 Parent，仅作 R1 可见性补全
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer part03 --deploy-migi

# D3 04 层：继续只增加一个 Parent-bound 静态件
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer part04 --deploy-migi

# D3 05 层
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer part05 --deploy-migi

# D3 Full：加入全部 9 个枪体 mesh；03-08 均为明示静态降级
python scripts/csgo_pack/build_d3_m4a4_r1.py --layer full --deploy-migi
```

D3 主枪身自动检查通过：`M4A1S_BornBeast` 共 3,407 三角面，100% rigid 到 M4A4 的 `v_weapon.M4A1_Parent`；编译和回环均为 57 骨、9 序列、2 附件、3,407 面及 `rif_m4a1`。旧 M4A1-S C3 transform 已明确拒绝，因为两种官方模型的 Parent bind 不同；新 M4A4 独立拟合固化于 `c3_alignment_m4a4_manifest.json`。`p_cf_bornbeast_m4a4_d3_main_tmp` 是当时的分层测试 addon，现已归档；用户确认记录为 `d3_manual_game_check.json`。

01 弹匣增量位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_clip/`，报告为 `d3_r1_clip_report.json`。该层新增 44 个位置、36 个三角面并 rigid 到 `v_weapon.M4A1_Clip`；回环 SMD 中主枪身 10,221 corners 保持 bone 3，弹匣 108 corners 保持 bone 4。官方 Idle 的 Clip 最大变化为 `0`，Reload 为 `14.908203`。该分层 addon 已归档；用户实机证据在 `d3_clip_manual_game_check.json`。

截图中掉枪后仍是原版 M4A4 属于预期的未覆盖范围，而不是弹匣层失败：当前 addon 只有第一人称 `v_rif_m4a1.*`。本地官方 VPK 确认 M4A4 另有 `w_rif_m4a1.*`、落地武器 `w_rif_m4a1_dropped.*` 以及掉落弹匣 `w_rif_m4a1_mag.*`；世界模型必须单独提取、反编译、对齐并保留自己的碰撞/LOD，不能把 viewmodel 或 AK 模型直接改名。

02 Bolt 增量位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_bolt/`，报告为 `d3_r1_bolt_report.json`。该层新增 133 个位置、121 个三角面并 rigid 到 `v_weapon.M4A1_Bolt`；回环 SMD 中 363 个 02 corners 全部保持 bone 29。官方 M4A4 的 Bolt 骨在 Idle、三条 Fire 和 Reload 中最大变化均为 `0`，只在 Draw 中变化 `2.261719`；因此实机正确预期是 Draw 联动而不是开火往复。用户已确认本层没有问题，记录为 `d3_bolt_manual_game_check.json`。

03 增量位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_part03/`，报告为 `d3_r1_part03_report.json`。该层新增 165 个位置、184 个三角面并 rigid 到 `v_weapon.M4A1_Parent`。这是明确的 `r1_static_visibility_only` 降级：CF 动画关键帧尚未解码，也没有证明 03 对应某个官方 M4A4 动态骨。用户已确认没有动作/位置问题，但指出官方占位贴图过黑、难以判断枪体是否完整；该限制已写入 `d3_part03_manual_game_check.json`，最终 CF 材质阶段必须重做完整性检查。

04 增量位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_part04/`，报告为 `d3_r1_part04_report.json`。该层新增 46 个位置、52 个三角面并 rigid 到 Parent；回环后 bone 3 共 10,929 corners，bone 4/29 分布保持不变。用户实机确认没有问题，记录为 `d3_part04_manual_game_check.json`。

05 增量位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_part05/`，报告为 `d3_r1_part05_report.json`。该层同样新增 46 个位置、52 个三角面并 rigid 到 Parent，累计 3,852 三角面；自动检查通过，用户观察无明显区别。逐件测试受黑色占位材质限制，剩余 06–08 按用户要求合并。

Full 层位于 `build/m4a1_s_bornbeast_m4a4/d3_r1_full/`，报告为 `d3_r1_full_report.json`。它包含全部 9 个枪体 mesh，共 3,646 个位置、4,008 三角面；01 rigid 到 Clip、02 rigid 到 Bolt，03–08 共 6 件均逐项记录为 Parent-bound `r1_static_visibility_only`。回环骨骼 corners 为 Parent 11,553、Clip 108、Bolt 363，所有自动检查通过。用户已确认 Full 整体没有问题，记录为 `d3_full_manual_game_check.json`；因官方占位材质过暗，表面完整性保留到 F1 复核。旧 Full addon 已移入 `mods_temp`。

### F1：材质引用与表面可见性调试

原始纹理不是标准容器：`PV-M4A1_S_BornBeast.DTX` 实际由 512×256 BGR24 主级、完整 mip 链和 163 字节尾部组成；Alpha/Normal/Specular 三张伪 `.TGA` 则把 TRUEVISION footer 和 18 字节 TGA header 插在 1024×1024 BGR24 像素流中间，必须拆出后重组，不能简单裁掉文件尾。修正输出与 CFRezManager 逐像素一致：Alpha 仅 G 通道、Normal 仅 B 通道、Specular 仅 R 通道携带标量信号。492 字节 Shader CFG 是 164 像素的一维 RGB lookup strip（R/G 恒白，B 变化），不是可按文本翻译的 VMT 参数。可复现解码器为 `scripts/weapon_port/decode_bornbeast_materials.py`，布局、源哈希、输出哈希和被排除的旧 Raw/UltraHD 候选写入 `work/m4a1_s_bornbeast/materials/material_decode_report.json`。

第一版只为检查 UV 和表面：从 AlphaMap G 标量生成灰度 atlas，并用 gamma 0.55 提亮阴影；没有启用法线、高光、envmap、自发光、动态 PV DTX 或 CFG。用户曾确认首版“正常”，但随后发现其中置 header 未修复，因此该确认只证明没有明显视觉/动作回归，不能证明旧解码语义。修正版通过 `scripts/weapon_port/validate_materials.py` 的 `rif_m4a1` SMD → M4A4 QC `$cdmaterials` → 唯一 VMT → 存在 VTF 闭环，并由用户确认黑白显示符合预期、没有问题；灰度缺少颜色方向线索的限制已单独记录。F1 两版均已移入 `mods_temp`。

F2 审计脚本为 `scripts/weapon_port/audit_bornbeast_materials.py`，报告为 `f2_material_audit_report.json`。本地官方 UI 图标 `BUYWEAPON_INFO_M4A1_S_BornBeast.DTX` 已由 CFRezManager 新增的 `--decode-image` 命令解出，确认经典雷神基准配色是黑/枪灰主体、银色机械边缘与红色能量点缀。当前只允许把 Alpha-G 当灰度可见性/底色候选、Specular-R 当保守高光 mask 候选；Normal-B 是单通道标量，禁止直接当切线空间 `$bumpmap`，CFG 与 PV DTX 的查表、混合和动画方式仍是 provisional。

F3 第一层由 `scripts/weapon_port/build_f3_m4a4_base_phong.py` 构建：修正后的 Alpha-G 经 gamma 0.55 提亮作为灰度 RGB，Specular-R 写入同一 RGBA 贴图的 alpha，Source VMT 用 `$basemapalphaphongmask`、`$phongboost 0.6`、`$phongexponent 18` 做低强度金属高光。输出为 1024² DXT5/11 mip，报告和闭包分别为 `f3_base_phong_report.json`、`f3_material_closure_report.json`；红色能量、Normal-B、CFG lookup、envmap、自发光和动画 proxy 均未启用。

F3 的引用闭包虽然通过，但实机只能看到不可识别的黑白拼块；复核纹理内容后确认 Alpha-G 实际是带 `ACCURACY INTERNATIONAL` 字样的另一把常规武器 atlas。因此 F3 被判定为“技术链路有效、外观语义错误”，不能继续作为雷神底色，addon 已移入 `mods_temp`。

F4 改用可独立核验的网络参考来源：公开页面 `https://www.gamemodd.com/cs/skinsweapons/ak47/1082-m4a1-s-born-beast.html` 发布的 CS 1.6 包（页面署名 Smilegate、Nexon）。下载 RAR 的 SHA-256 为 `9820df6ffafc5a49051e7e64560118d399bbda6a65717f2120a89ccae5b91d85`；仓库新增 `scripts/weapon_port/extract_goldsrc_mdl_textures.py`，从 GoldSrc v10 MDL 的内嵌 8-bit palette 中提取 6 张纹理，报告为 `external/cs16_texture_extract_report.json`。其中 `PV-M4A1_S_BORNBEAST.bmp` 只用于 Prototype 可识别性与材质链验证；它不得进入最终 F 阶段，外部模型与动画也未进入项目构建。

`scripts/weapon_port/build_f4_m4a4_recognizable_classic.py` 及其 `f4_*_report.json` 仅作为 Prototype 历史视觉证据；不把某个外部 addon 名称写入 README 的静态状态。MIGI 当前启用项以 `plan.md` 为准，不使用的 addon 放入 `mods_temp`。

---

### 二、 CS:GO VPK 解析与 Mod 打包 (`scripts/csgo_pack/` & `migi_tools/`)

#### 1. CS:GO 原版语音提取与比对
* 运行 `python scripts/csgo_pack/unpack_vpk_voices.py`（基于 Python `vpk` 库，需先 `pip install vpk`），从游戏官方 `csgo/pak01_dir.vpk` 中批量提取所有 341 种语音指令（共 1.8 万个音频），输出到 `data/csgo_voices_unpacked`。
* 运行 `python scripts/csgo_pack/parse_vpk.py`，可快速搜索特定人物或路径的内部文件名（如 `sound/player/vo/...`）。

#### 2. 历史官方 M4A1-S 参考基线（旧阶段 A2）

下面的流程只读取 CS:GO Legacy 官方 `pak01_dir.vpk`，输出到项目 `work/`，不会改写游戏目录，也不会使用 AK 参考 Mod：

```powershell
# 一键运行：提取 VPK、固定 CrowbarDecompiler 反编译并生成报告
python scripts/csgo_pack/build_m4a1_s_reference.py

# 也可以拆开执行（需要安装 vpk 的项目 Python）
python scripts/csgo_pack/extract_m4a1_s_reference.py

# 固定 CrowbarDecompiler 0.71 CMD edition
& ".\tools\CrowbarDecompiler\CrowbarDecompiler(1.1).exe" `
  ".\work\m4a1_s_bornbeast\reference_m4a1_s\source_vpk\models\weapons\v_rif_m4a1_s.mdl" `
  ".\work\m4a1_s_bornbeast\reference_m4a1_s\decompiled"

python scripts/csgo_pack/report_m4a1_s_reference.py
```

提取清单位于 `work/m4a1_s_bornbeast/reference_m4a1_s/extraction_manifest.json`，QC/SMD、动作和机器可读骨骼/序列/事件/附件/材质/bounds 报告位于同目录；官方 `.ani` 与 `.mdl/.vvd/.vtx` 原文件保存在 `source_vpk/`。

#### 3. 官方模型隔离回环（阶段 A3）

```powershell
# 输出到 build/m4a1_s_bornbeast，不改写 csgo/models；同时保留完整编译日志
python scripts/csgo_pack/compile_m4a1_s_roundtrip.py

# 如需准备一个新的临时 MIGI addon（不会覆盖已有目录）
python scripts/csgo_pack/compile_m4a1_s_roundtrip.py --deploy-migi
```

回环结果和结构比较见 `work/m4a1_s_bornbeast/reports/a3_roundtrip_report.json`；临时 addon 需要启动游戏后再人工确认画面与动作行为。

#### 4. 自动打包部署到 MIGI
* 运行 `python scripts/csgo_pack/package_tts_migi.py`，可将制作好的语音按照 CS:GO 各阵营的映射规则，自动分发并写入 MIGI 的 `migi\csgo\addons\` 文件夹。

---

### 三、 CS:GO 实机 Mod 生效流程（MIGI 极简操作）

在实际进入游戏游玩时，**只需要操作 CS:GO 目录下的 `migi.exe` 和 `migi\csgo\addons` 文件夹**：

1. **放置 Mod 资源**：
   将转换好的语音/模型放入 MIGI 的 addons 目录，例如：
   ```text
   D:\steam\steamapps\common\csgo legacy\
   └── migi\
       └── csgo\
           └── addons\
               └── My_Custom_Voice\
                   └── sound\
                       └── player\
                           └── vo\
                               ├── anarchist\*.wav
                               ├── balkan\*.wav
                               └── separatist\*.wav
   ```
2. **运行生效**：
   * 打开 `D:\steam\steamapps\common\csgo legacy\migi.exe`；
   * 在列表中勾选你的 Mod；
   * 点击 **Generate** 或 **Launch** 启动游戏，MIGI 会自动生成 `.vpk`、重建 `sound.cache` 并通过 `gameinfo.txt` 挂载，不破坏原版文件。

---

## 🔊 四、 CS:GO 游戏音频规范与硬性要求 (Audio Specifications)

为确保自定义语音在 Source 1 / CS:GO 引擎中完美触发 3D 空间定位、不破音且不被枪炮声掩盖，所有打进 Mod 的音频必须符合以下**硬性技术规范**：

| 规范项目 | 引擎硬性要求 | 最佳推荐配置 | 为什么必须这样设置？ |
| :--- | :--- | :--- | :--- |
| **封装格式** | 标准 `.wav` (RIFF 容器) | `.wav` | 游戏引擎原生直读，禁止使用 mp3/ogg/flac 等格式。 |
| **编码格式** | **16-bit PCM** (`pcm_s16le`) | `pcm_s16le` | 必须为未压缩的 16 位有符号整型 PCM，否则报格式错误。 |
| **声道配置** | **单声道 Mono (1 channel)** | **1 channel** | **核心重点**：CS:GO 的人物报点与 3D 空间声学定位（HRTF/距离衰减）**必须要求单声道**！双声道立体声（Stereo）会导致声音全图无衰减广播或引擎定位失效。 |
| **采样率** | **44,100 Hz** (44.1 kHz) | `44100` | 48kHz 在部分 Source 1 语音系统中可能引起微卡顿或音调变异，44.1kHz 为引擎官方黄金标准。 |
| **目标响度** | **`-9 ~ -11 LUFS`** | `-10.0 LUFS` (RMS -7~-10dB) | 相比常规 -14~-16 LUFS **提高约 5dB**，用于补偿游戏内语音混音衰减；在激烈交火中清晰可辨且不易爆音（实测 +10dB 过大，+5dB 合适）。 |
| **真实峰值** | **`≤ -0.5 dBTP`** | `-0.8 dBTP` | 预留防爆音安全余量，防止游戏内部混音器爆音削波。 |
| **尾端缓冲** | **`200ms ~ 450ms`** 释放区 | 450ms 静音缓冲 | 避免自回归/声码器在句尾硬切导致最后一个字残缺吞字。 |

---

## 🧪 五、测试与日志（沙盒冒烟）

运行 `python tests\run_smoke.py` 可一键验证工具链与各脚本是否就绪：

- **L0 环境自检**：Python / ffmpeg / vgmstream-cli / vpk 库 / CF 目录 / CS:GO 游戏目录。
- **L1 语法检查**：`py_compile` 编译 `scripts/` 下全部脚本。
- **L2 沙盒冒烟**：在临时沙盒 `data/tmp/<run-id>` 内用样例输入真跑脚本（clean_wavs、categorize_voices 等），并验证其余脚本在空输入下不崩溃。

测试结束**自动删除沙盒目录**，只保留 `logs/<时间戳>_smoke.log` 日志；有失败项时退出码非 0，便于自动化判断。调试时可加 `--keep-tmp` 保留沙盒：

```powershell
python tests\run_smoke.py            # 跑全部，测完自动清理沙盒
python tests\run_smoke.py --keep-tmp # 保留沙盒目录便于排查
```

> 所有脚本的输入/输出路径统一由 `scripts/_paths.py` 解析，默认指向项目内路径；测试时通过 `CF2_DATA_DIR` / `CF2_GAME_DIR` / `CF2_CF_DIR` / `CF2_LOG_DIR` 等环境变量重定向到沙盒，不会污染真实 `data/` 与游戏目录。
