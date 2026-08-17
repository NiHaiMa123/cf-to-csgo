# CF to CS:GO Modding Toolkit (穿越火线转 CS:GO 资源解包与 Mod 工具库)

本项目是将 **穿越火线 (CrossFire)** 的音频/模型等游戏资源提取、清洗并转换为 **Counter-Strike: Global Offensive (CS:GO)** 兼容 Mod 的全套一站式工具集合。

包含：CF REZ 解密解包、假 WAV 音频修复、CS:GO VPK 结构解析、MIGI 自动化封包部署及 GSI 游戏联动工具。

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

该报告会保留原始坐标，并逐网格记录法线、UV、权重值、bounds、材质提示和校验结果；当前还会解析蒙皮网格的 packed bone indices、LTB 节点名称/父子层级和绑定矩阵，并执行 bind-pose 蒙皮回环校验。切线、直接 Shader 材质绑定和 CF 动画 clip 仍会明确标为 `partial`/`missing`，不会伪造 CF 动作支持。

**两条路线评估（阶段 B2）**：

```powershell
python scripts/cf_ltb/evaluate_b2_routes.py
```

该命令对 `PV-M4A1_BL.LTB` 与雷神目标 LTB 做字段级对照，并记录外部转换器可用性；结果写入 `work/m4a1_s_bornbeast/reports/b2_route_evaluation.json`。当前已证明：两份 LTB 的静态几何/法线/权重、packed bone indices、节点层级和 bind-pose skinning 均可由原生路线复现；雷神目标为 57 个节点、1,280 个蒙皮样本，bind-pose 最大回环误差约 `7.4e-15`。CF 动画 clip/关键帧尚未解码，所以 R1/R2 继续使用官方 CS:GO 动作，不能声称拥有 CF 原版动作。

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

C1 默认只保留 9 个 CF 枪体 mesh；`Fview-hand2` 与 `Fview-arm2` 输出到独立的 `cf_arms_optional` staging，正式路径使用官方 M4A1-S 手臂/手套。当前编号枪体件的语义仍是 provisional，待 Blender/mesh inspection 后在 C2 固化弹匣、枪机、消音器和附件骨骼绑定。

用户已启动 Blender MCP 时，可用下面的最小客户端确认端口并执行 Blender Python：

```powershell
python scripts/cf_ltb/blender_mcp_call.py get_scene_info
python scripts/cf_ltb/blender_mcp_call.py execute_code `
  --params '{"code":"import bpy\nprint(len(bpy.data.objects))"}'
```

本次 C1 复核使用 `use_split_objects=true`、`use_split_groups=true` 导入 weapon-only staging，并整理到 Blender 的 `CF_C1_REVIEW` collection；生成 `work/m4a1_s_bornbeast/reports/c1_blender_overview.png`、逐件预览目录和 `c1_blender_mcp_review.json`。结果确认主体与 `M4A1S_BornBeast01`（弹匣候选）以及 `M4A1S_BornBeast02`（枪机候选）；03–08 保持未分类，所有 C2 骨骼仍需动画验证。

**骨架映射（阶段 C2，当前为 provisional）**：

```powershell
python scripts/cf_ltb/build_c2_skeleton_plan.py `
  --reference-report ".\work\m4a1_s_bornbeast\reference_m4a1_s\reference_report.json" `
  --mesh-map ".\assets\weapons\m4a1_s_bornbeast\mesh_map.yaml" `
  --skeleton-output ".\assets\weapons\m4a1_s_bornbeast\c2_skeleton_manifest.json" `
  --binding-output ".\work\m4a1_s_bornbeast\reports\c2_binding_plan.json"
```

该步骤锁定官方 M4A1-S 的 58 根骨骼和必需机械骨骼集合，建立主枪身、弹匣、枪机及未决件的候选绑定；当前 Blender 会话中另有隐藏的 `CF_C2_SKELETON/CF_C2_M4A1S_Armature`，用于后续权重检查。`c2_binding_plan.json` 不是最终权重文件：在 CF 动画未解析、03–08 仍是开放片段的情况下，所有绑定都保持 `finalized: false`。

---

### 二、 CS:GO VPK 解析与 Mod 打包 (`scripts/csgo_pack/` & `migi_tools/`)

#### 1. CS:GO 原版语音提取与比对
* 运行 `python scripts/csgo_pack/unpack_vpk_voices.py`（基于 Python `vpk` 库，需先 `pip install vpk`），从游戏官方 `csgo/pak01_dir.vpk` 中批量提取所有 341 种语音指令（共 1.8 万个音频），输出到 `data/csgo_voices_unpacked`。
* 运行 `python scripts/csgo_pack/parse_vpk.py`，可快速搜索特定人物或路径的内部文件名（如 `sound/player/vo/...`）。

#### 2. 官方 M4A1-S 参考基线（阶段 A2）

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
