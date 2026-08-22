# CF 武器 -> CS:GO Legacy Source 1 — 项目计划与唯一执行入口

> 最后更新：2026-08-22  
> **本文件是项目唯一 authoritative progress / workflow / task state。**  
> 所有 Agent 先读 `AGENTS.md`，再读本文件。  
> 历史 Task Spec / Continuation / Review 已合并到本文；需要逐轮细节时查 Git history 和 `work/**` evidence。

---

## 0. 30 秒读懂现在做到哪了

已经解决：

```text
CF LTB / 模型基础解析
-> M4A4 Source 1 skeleton / sequence / attachment contract
-> SMD / QC / VMT / VTF build
-> studiomdl / Crowbar roundtrip / validation
-> package / staging / MIGI deploy
-> changed-runtime user Gate
```

这条 **CF 武器 -> CS:GO Legacy Source 1** 技术链已经 `PASS / FROZEN`。

当前真正没解决的是：

```text
CF weapon piece / mesh
-> 原游戏 material / shader binding key
-> local DTX/TGA texture family
-> WeaponShader CFG 的真实 consumer / semantic
```

现有 repo + 已解包静态 corpus 已经分析到证据边界：

```text
P4-M01-N01 evidence cleanup = COMPLETE / FROZEN
P4-M01-N01 substantive      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

但这不等于“下一步为空”。**当前正式下一任务是主动获取新的 runtime/client 输入：**

```text
P4-M01-N02 = ACTIVE / RUNTIME_ARTIFACT_ACQUISITION
```

N02 不允许继续重复扫描旧 `data/**`；它负责从本机 CF 安装环境、原始 runtime 包、客户端模块和 shader 包中找到可供静态逆向的新证据，并做第一轮 bounded static triage。

---

# 1. 唯一权威状态

| 阶段 / Task | 当前状态 | 说明 |
|---|---|---|
| P0-P3 | `DONE / HISTORICAL` | 资源处理、模型研究、Source 1 前置基础 |
| P4 baseline | **`PASS / FROZEN`** | 模型 -> Source 1 -> package -> MIGI 技术链冻结 |
| P4-M01 | **`ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`** | BornBeast 原生 CF 材质尚未闭合 |
| P4-M01-R1 | `ACCEPTED / COMPLETE` | 早期材质 evidence 纠错已完成 |
| P4-M01-N01 Phase 0 | `ACCEPT / FROZEN` | consistency cleanup 已接受 |
| P4-M01-N01 evidence | **`COMPLETE / FROZEN`** | scanner/provenance/scope/closure 文档与代码清理完成 |
| P4-M01-N01 substantive | **`BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS`** | 旧 corpus 缺原 CF engine/client consumer code |
| **P4-M01-N02** | **`ACTIVE / RUNTIME_ARTIFACT_ACQUISITION`** | **CURRENT：主动寻找新 runtime/client/shader 输入并做静态分流** |
| P5-T01 | `PASS / USER_REFERENCE_CONFIRMED` | M4A1-雷神官方目标图已由用户确认 |
| P5 LEGACY PRE-SCAN | `EXECUTION_PASS / PRESERVED_FOR_REUSE` | 本地候选广召回结果保留 |
| P5-T02 | **`PAUSED_BY_P4_M01`** | 等可信 native material method 后恢复 |
| P5-T03 | `BLOCKED_BY_T02` | Resource Graph / provenance closure |
| P5-T04 | `BLOCKED_BY_T03` | 最终 identity Review |
| P6 | `BLOCKED_BY_P5` | 最终替换 / 发布质量 |
| P7 | `FUTURE` | visible Inspect、IK/retarget、CF 原动画/声音等增强 |

### 当前执行决策

```text
CURRENT -> 执行 P4-M01-N02 (§6)

N02 找到 credible runtime consumer candidate
    -> 返回 Chat/Sol Review
    -> 重新打开 N01 substantive static consumer tracing

N02 找到 runtime artifact，但直接字符串无命中
    -> 不停止；继续 imports/xref/archive/shader/旁路模块等 N02 分支

N02 证明本机范围内确实无可用 runtime artifact
    -> N02 = BLOCKED / NO_RUNTIME_ARTIFACT_FOUND_LOCALLY
    -> 明确告诉用户需要另一安装版本/目录/原始客户端输入

未来 P4-M01 被 Review 为 NATIVE_MATERIAL_RECOVERED
    -> 恢复 P5-T02
```

---

# 2. 整体流程

```text
Track A — 资源与转换
CF REZ / local assets
-> LTB / DTX / TGA / CFG / audio extraction
-> model / UV / skeleton / animation evidence
-> Source 1 conversion
-> compile / validate / package / MIGI
-> P4 baseline PASS / FROZEN

Track B — 原生材质
BornBeast local material family
-> container/storage evidence
-> real material binding
-> CFG/render semantics
-> native-only composition
-> P4-M01 PASS / NATIVE_MATERIAL_RECOVERED

Track B2 — 当前新输入获取
Windows/local CF installation
-> locate client/runtime/modules/archives/shaders
-> hash/inventory
-> static strings/imports/resources triage
-> credible consumer candidate
-> reopen N01 consumer tracing

Track C — 最终雷神识别
official reference
+ preserved local candidate pool
+ validated native material method
-> Transformers/native finalists
-> user candidate Gate
-> Resource Graph
-> final identity Review
-> P6 release

Track D — 后续增强
visible Inspect / hand-finger IK / retarget
CF original animation / sound / world model
-> P7
```

---

# 3. P4 baseline — PASS / FROZEN

## 3.1 冻结身份

```text
Implementation baseline : 10aa99b770e575300ca3c28324ef3de3d5b70c6b
Frozen build run        : run_20260819_170013_270792
RV-04 evidence commit   : fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
Frozen addon            : p_cf_bornbeast_m4a4_p4_frozen_noop_01
Runtime slot            : M4A4
Internal model          : weapons/v_rif_m4a1.mdl
Inspect policy          : frozen_noop_safe
final_target_identity   : false
final_cf_material       : false
```

## 3.2 已证明的链

```text
local CF LTB
-> B3
-> C1
-> C3
-> Source build / Crowbar roundtrip
-> validation
-> package / staging
-> deploy
-> user changed-runtime Gate
```

P4 baseline 证明 conversion/build/package/MIGI/runtime contract 能稳定工作。

## 3.3 RV-04 独立反例

4/4 高风险 mutation 都被预定 Gate 拒绝：

```text
unsafe output root                 -> manifest_contract
same sequence count, wrong name    -> sequence_names_and_count
Parent/Clip bone semantic swap     -> smd_manifest_bone_corners
missing critical VTF               -> material_closure
```

注意：`material_closure` 只证明 Source material reference 对缺失 VTF 有 Gate，**不证明 VTF 像素来自正确 CF 原生材质语义**。

## 3.4 User Gate 与保留风险

用户历史确认 frozen/no-op addon：

```text
no crash / obvious runtime error
no visible Inspect motion (符合 frozen_noop 设计)
weapon state returned normally
Fire / Reload / Switch remained usable
```

仍未测试或未闭合：

```text
console_errors                  not_tested
rollback_after_disable          not_tested
visible Inspect / hand IK       -> P7
CLI inspect-policy override     non-blocking risk
fully manifest-driven toolchain non-blocking risk
working-tree SHA / Git blob EOL portability provenance risk
```

P4-M01 不得为了解材质而重写这条 frozen conversion contract。

---

# 4. P4-M01 — BornBeast 原生材质恢复

## 4.1 为什么必须补做

历史 Prototype 可辨识材质曾使用：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此“枪能进 CSGO”已经成立，但“CF 原版材质被正确恢复”并没有成立。

## 4.2 最终目标

只使用本地 CF：

```text
BornBeast LTB / UV
+ DTX
+ Alpha / Normal / Specular TGA
+ WeaponShader CFG
+ same-family variants
-> decode/container evidence
-> real material binding
-> CFG/render semantics
-> native-only composition
-> reproducible closure
```

最终可见材质输入只允许：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

外部 MOD texture、官网图、网络图、AI 生成/补全 texture 只能 `reference_only / differential_control`，不能贡献 final pixels。

## 4.3 P4-M01 PASS Gate

只有同时满足下列核心要求，Chat/Sol 才能判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

要求：

1. geometry / UV 来自 local CF LTB；
2. 实际使用的 base/lookup/alpha/normal/specular/emissive/detail 等都有 path + SHA；
3. mesh/piece -> material/texture binding 有结构或 direct consumer evidence；
4. CFG/render semantics 足够支持重建，而不是“能画成彩条”；
5. visible color 全部 local CF / verified semantics；
6. 0 external pixels；
7. clean output 可重复；
8. BornBeast 主要颜色分区、图案、UV、高光/能量区域稳定可辨认；
9. 外部图只参与对照。

当前 Gate 仍未满足；N02 的目的就是主动寻找第 3/4 项缺失的 engine-side 输入。

---

# 5. P4-M01-N01 — 已冻结的旧 corpus 结论

最新完整 cleanup executor commit：

```text
65292c742d545459974c56aec494d1d9c44039a8
P4-M01-N01: F3 scope guard - unified is_config_candidate predicate
```

## 5.1 N01 scanner / scope 已冻结

统一 config candidate predicate：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

以下三个输出都只在同一个 predicate 内产生：

```text
config_candidates_seen
config_candidates_decoded
config_index
```

并保留 invariant：

```text
config_candidates_decoded <= config_candidates_seen
len(config_index_keys) == config_candidates_decoded
```

当前 measured scope：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
config_index_keys                    = 18
config_index mapping tuples          = 72
raw_scan_files_seen                  = 355
raw_scan_files_decoded               = 355
```

18 个真实 mapping config 都是 ArmModel CFG。

Scoped negative：

```text
BornBeast      text-config hits = 0
Transformers   text-config hits = 0
Jewelry        text-config hits = 0
BlueDiamond    text-config hits = 0
.dat consumer hits             = 0
BornBeast derived-output hits  = 4 (DERIVED_OUTPUT_HIT only)
```

这些只是声明 scope 内的 negative，不是“整个游戏绝对不存在”的 universal negative。

## 5.2 DTX / TGA 当前证据等级

DTX：

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC / NOT universal
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

TGA inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular formal repair 已接受为 structural evidence；map 的 shader role 仍不能仅由文件名推导。

## 5.3 WeaponShader CFG 当前证据等级

237/237 WeaponShader CFG：

```text
non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

这是 `STRUCTURALLY_VERIFIED`。

已接受 measured samples：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

语义仍是：

```text
CFG = 1D LUT                    HYPOTHESIS
CFG = packed shader constants   HYPOTHESIS
actual CF semantic consumer     OPEN_UNRESOLVED
Source1 Phong/selfillum mapping SOURCE1_DESIGN_CANDIDATE
```

不能把 Source 1 设计映射倒推成 CF 原引擎事实。

## 5.4 ArmModel positive control 与 weapon binding

ArmModel LZMA text material CFG 已证明 CF engine-format 能存在：

```text
[Textures] named texture references
[Techniques]
[Properties] PieceIndex
```

但这只是 **ArmModel positive control**，不能推出 weapon 使用同一 contract。

Weapon 侧当前：

```text
LTB post-mesh short ASCII field exists        STRUCTURALLY_VERIFIED
short id == texture/material slot             NOT PROVEN
repo parser semantically consumes short id    NO / TOOL-CODE OBSERVATION
repo ObjExporter Models->ModelTextures mirror TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
original CF piece->texture binding            OPEN_UNRESOLVED
```

Repo exporter 的 filename/path mirroring **不是**原 CF runtime binding proof。

## 5.5 N01 substantive blocker

`engine_binding_closure.json` 当前核心状态：

```text
closure_path        = Path B - Incomplete
status              = OPEN_UNRESOLVED
substantive_blocker = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

旧 repo/corpus 没有可用于 engine-side consumer tracing 的 client/runtime code，所以还不能证明：

```text
post_mesh_short_id / piece identity
-> original CF material/shader resolver
-> texture family binding
-> WeaponShader CFG semantic consumer
```

**禁止继续用旧 corpus 重复 basename/config/curve-fitting 搜索。**

这条禁止只针对“重复分析旧输入”，**不禁止 N02 主动从本机安装环境获取新的 runtime/client 输入**。

---

# 6. CURRENT TASK — P4-M01-N02 Runtime Artifact Acquisition & Static Triage

> task_id: `P4-M01-N02`  
> parent: `P4-M01`  
> state: **`ACTIVE / RUNTIME_ARTIFACT_ACQUISITION`**  
> purpose: **主动找到能解除 N01 blocker 的新输入，而不是等待用户手工猜文件。**

## 6.1 任务目标

N02 必须尽可能自动完成：

```text
locate CF install/runtime roots
-> inventory candidate executables/modules/archives/shaders
-> record path/size/SHA256/type/version metadata
-> bounded static strings/imports/resources triage
-> rank consumer candidates
-> choose next static-analysis route
```

最终至少输出之一：

```text
RUNTIME_CONSUMER_CANDIDATE_FOUND
RUNTIME_ARTIFACT_FOUND_NEEDS_DEEPER_STATIC_ANALYSIS
NO_RUNTIME_ARTIFACT_FOUND_LOCALLY
```

不得因为第一条路径没有命中就直接问用户“下一步选什么”。下面分支必须按顺序尽可能尝试。

## 6.2 Step A — 找 CF 安装根目录，不要求用户先给路径

按优先级寻找，找到后仍继续记录其他可信 roots：

### A1. 已知/现有路径线索

检查：

```text
repo scripts/config/report 中记录过的 CF source/install path
环境变量
当前命令历史可见配置（若本地 harness 能访问）
```

只用于定位，不把旧 `data/**` 当 runtime artifact。

### A2. Windows 注册表

只读检查：

```text
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
App Paths
```

关注 display name / install location / executable path 中的：

```text
CrossFire
穿越火线
Tencent / 腾讯
WeGame
CF
```

不要把仅 launcher 的目录误当完整 game root；记录 relation。

### A3. 快捷方式 / 启动入口

只读解析：

```text
Desktop *.lnk
Start Menu *.lnk
WeGame/launcher 配置或 manifest
```

目标是得到真实 target / working directory / game path，不启动程序。

### A4. 有界文件系统搜索

如果仍未知，搜索固定盘符下常见安装目录，先目录名再文件名，不做无界全文扫描：

```text
Program Files
Program Files (x86)
Tencent
WeGame
CrossFire
穿越火线
CF
```

如果用户机器有多个盘，可枚举 fixed drives 后按上述目录/token 搜索。

### A5. 已运行进程旁路（可选）

如果 CF/WeGame **本来已经在运行**，允许只读查询进程 executable path / loaded module paths。

**禁止为了获取路径而启动未知客户端或关闭/注入进程。**

## 6.3 Step B — Runtime artifact inventory

对每个可信 install/runtime root 建 inventory，至少覆盖：

```text
*.exe
*.dll
*.rez
*.pak
*.pck
*.bin
*.dat               only when near runtime/config/shader roots
*.fx *.fxc *.shader *.shd *.cso
renderstyle / shader / effect related files or directories
```

不要把全部音频/贴图再次纳入 inventory。

每个候选记录：

```text
relative_or_local_path
root_id
size_bytes
sha256
extension
PE_magic / archive_magic if applicable
file_version / product_name / description if available
signer if available
last_write_time
candidate_role
why_candidate
```

建议输出：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/artifact_inventory.json
```

原始 binary/archive 继续留本地；**不得 commit。**

## 6.4 Step C — PE / module 静态初筛

对 `.exe/.dll` 只做静态读取。

### C1. PE 基础信息

优先复用本机已有工具：

```text
PowerShell Get-Item / Get-FileHash / Get-AuthenticodeSignature
Visual Studio dumpbin
llvm-readobj / llvm-objdump
objdump
Python pefile（若环境已有）
```

不要为了这一阶段下载来历不明的二进制工具。

记录：

```text
architecture
imports
exports
sections
resource/version metadata
entrypoint/RVA metadata
```

### C2. 目标 strings

同时检查 ASCII / UTF-16LE，至少搜索：

```text
WeaponShader
ModelTextures
AlphaMap
NormalMap
SpecularMap
PieceIndex
RenderStyle
Shader
.DTX / .dtx
.LTB / .ltb
.CFG / .cfg
PLAYERVIEW
```

扩展辅助 needles：

```text
CreateFile / fopen / ReadFile
Direct3D / D3D9 / D3D11
texture / material / render / resource
```

命中必须记录：

```text
artifact_sha256
needle
encoding
offset/RVA if available
surrounding_string/context
```

输出：

```text
runtime_acquisition/string_hits.json
```

### C3. Candidate ranking

建议优先级：

```text
P0 direct WeaponShader/ModelTextures/PieceIndex/DTX/LTB strings
P1 direct resource-loader/render imports + relevant string family
P2 engine/render/resource named module adjacent to game client
P3 client module with archive/resource parsing evidence
P4 large generic launcher/patcher with no game-resource evidence
```

不能只凭文件名判定；ranking 必须说明证据。

输出：

```text
runtime_acquisition/candidate_rank.json
```

## 6.5 Step D — 如果 strings 直接命中：静态 xref 路线

若存在 P0/P1 candidate，不等待用户，继续使用**本机已有**静态分析工具中的任一种：

```text
Ghidra
IDA
radare2 / rizin
Binary Ninja
objdump/llvm + manual RVA tracing
```

目标不是完整反编译客户端，而是 bounded tracing：

```text
relevant string
-> xref function
-> caller/callee
-> file/resource loader
-> model/material resolver
-> key/index/short-id use
```

优先回答：

```text
谁打开 .LTB/.DTX/.CFG？
谁拼 ModelTextures/Shader/WeaponShader 路径？
piece/material index 从哪里进入 resolver？
WeaponShader CFG bytes 被当作什么数据类型/长度消费？
```

只要得到 credible consumer chain，就输出：

```text
RUNTIME_CONSUMER_CANDIDATE_FOUND
```

并写：

```text
runtime_acquisition/static_xref_report.json
```

然后停止扩大逆向范围，交回 Chat/Sol Review 决定如何重新打开 N01 substantive。

## 6.6 Step E — 如果 PE strings 没命中，不准立即停止

依次尝试：

### E1. Imports / loader 旁路

即使字符串被压缩/混淆，也检查：

```text
CreateFileA/W
ReadFile
fopen/fread
FindFirstFile
resource/archive APIs
Direct3D texture/shader APIs
```

从资源加载/渲染相关函数周边寻找 extension compare、hash lookup、路径拼接或 resource ID table。

### E2. 旁路 DLL/module

如果主 EXE 很薄、像 launcher/packer：

```text
优先扫描同目录和 bin/system/client/engine/render/resource 子目录 DLL
按 imports 找被主程序加载的模块
按 ProductName/FileDescription 判断 engine/render/resource 角色
```

不要因为主 EXE 没字符串就判定失败。

### E3. Archive/container route

对 `.rez/.pak/.pck/.bin`：

```text
先 list / magic / table-of-contents
-> 找 embedded PE / shader / config / renderstyle
-> 必要时解到本地临时目录或 data/runtime_local_only/
-> hash
-> 重复 Step C/D
```

可优先复用 `CFRezManager` 已有只读/解包能力。

**提取出的 raw runtime binary 仍 local-only，不提交。**

### E4. Shader route

寻找：

```text
compiled shader bytecode
FX/FXC/CSO/effect packages
render-style files
constant tables / parameter names
```

如果是可识别 DXBC/CTAB/Direct3D shader container，优先使用本机已有 shader dump/disassembly 工具读取 constant/resource names。

重点关联：

```text
specular
normal
alpha
emissive
texture slots
constant register count
CFG sample/count relation
```

即使拿不到 model binding，也可能先闭合 CFG consumer 语义的一部分。

### E5. Launcher / patch manifest route

如果本地只有 launcher 或安装目录不完整：

```text
检查 launcher config
patch/version manifest
download list
module list
relative game executable path
```

目的仅是定位实际客户端/runtime 文件，不访问账号秘密，不执行 patcher。

### E6. Packed/protected client route

如果主 EXE 明显 packed/protected、静态 strings 很少：

```text
记录 pack/protection evidence
不要执行脱壳器、不要注入/内存 dump、不要绕过 anti-cheat
优先转向未保护的 engine/render/resource DLL、shader 包、archive、旧版本/备份客户端
```

若用户本机存在旧版/备份安装，可以把它作为独立 root 做相同静态 inventory；版本差异必须记录。

## 6.7 Step F — 如果当前安装仍找不到 consumer

Agent 必须先完成有边界的 negative evidence，再返回 blocker，不能只说“没找到”。

至少记录：

```text
searched roots
root discovery method
candidate counts by extension/type
PE count
archive count
shader/renderstyle count
strings needles searched
artifacts with/without hits
excluded directories + reason
```

最终状态：

```text
NO_RUNTIME_ARTIFACT_FOUND_LOCALLY
```

仅在以下条件成立时使用：

```text
安装 root 已可靠定位或明确不存在
+ Step B inventory 完成
+ Step C static triage 完成
+ E1-E5 合理分支均已检查或有明确不可用原因
```

然后向用户请求的不是“你想做什么”，而是明确的缺口之一：

```text
另一台/另一版本 CF 完整客户端路径
旧版客户端备份
原始安装包/完整 REZ/runtime 包的位置
可访问的 engine/render/resource module
可信外部 documented/reverse-engineered binding contract
```

## 6.8 N02 输出与允许修改范围

建议实现一个可重复的 inventory/triage 脚本：

```text
scripts/material_recovery/n02_runtime_artifact_acquire.py
```

允许提交：

```text
scripts/material_recovery/n02_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/*.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/*.md
```

禁止提交：

```text
*.exe / *.dll / raw runtime binaries
raw REZ/PAK/PCK
raw shader package if proprietary client data
absolute-path secrets/user account data
data/**
```

报告可记录本机 absolute path 供本地继续，但提交版优先做 root alias/relative path；若绝对路径包含用户名等个人信息，提交前归一化。

## 6.9 N02 Completion Gate

### PASS A — 最优

```text
P4-M01-N02 = PASS / RUNTIME_CONSUMER_CANDIDATE_FOUND
```

至少具备：

```text
artifact path alias + SHA256 + size
relevant string/import/resource evidence
至少一个 static xref / loader-resolver candidate
为什么它可能消费 weapon material/CFG
```

然后停止 N02 扩张，交回 Chat/Sol；下一任务应重新打开 N01 substantive consumer tracing。

### PASS B — 有新输入但还没 direct consumer

```text
P4-M01-N02 = PARTIAL / RUNTIME_ARTIFACT_FOUND_NEEDS_DEEPER_STATIC_ANALYSIS
```

只有当所有 N02 bounded triage 已完成、但需要更深反编译才能判断时使用。报告必须给出明确的 top candidates 和下一条静态 tracing 点，不能只说“需要逆向”。

### BLOCKED

```text
P4-M01-N02 = BLOCKED / NO_RUNTIME_ARTIFACT_FOUND_LOCALLY
```

必须满足 §6.7 的 bounded-negative 要求。

---

# 7. P5 — 最终 M4A1-雷神识别

## 7.1 P5-T01 — 已完成

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
Target = M4A1-雷神
```

Ground truth evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

除非用户明确否决、evidence 丢失或 page/image relation 被证明错误，否则不重跑 T01。

## 7.2 Legacy pre-scan — 保留复用

历史执行 commit：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

结果：

```text
data inventory       165082 files
recalled candidates    2856
LTB candidates         1281
canonical inspected     441
```

主要 evidence：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

旧 score 只是召回优先级，不是 identity confidence。没有 evidence 损坏就不重新扫描全部 16 万文件。

## 7.3 P5-T02 — 当前暂停

已经完成：

```text
official reference
-> legacy candidate reuse
-> M4/M4A1 PLAYERVIEW narrowing
-> exact SHA dedup
-> geometry clusters
-> C029 / C103 finalist diagnostics
```

以下仍只允许 diagnostic：

```text
C029/C103 gray geometry                       diagnostic_only
Transformers DTX headerless-BGR24             unvalidated hypothesis
raw PV DTX + UV                               diagnostic_only
Alpha/Specular scalar approximation           diagnostic_only
raw RGB strip CFG preview                     not semantic decoding
```

因此当前禁止要求用户在灰模/伪材质之间强选。

只有：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

后才恢复 T02。

恢复后的固定路线：

```text
validated P4-M01 material method
-> M4A1_S_Transformers family inventory
-> revalidate Transformers-specific DTX/TGA/CFG
-> recover Transformers material binding
-> minimal evidence-backed semantic extension if needed
-> native material acceptance Gate
-> fixed-view native-material finalist renders
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

`USER_VISUAL_MATCH_CONFIRMED` 仍不是最终 `IDENTITY_CONFIRMED`。

## 7.4 P5-T03 / T04

T03 在 T02 后建立完整 Resource Graph；T04 由 Chat/Sol 最终 identity Review。只有 `IDENTITY_CONFIRMED` 才进入 P6。

---

# 8. P6 / P7

## P6 — Final replacement / release

P5 final identity 成立后才做最终资产替换、clean build/package/deploy、发布质量验证。

## P7 — Enhancement

不阻塞当前 material / identity closure：

```text
visible Inspect
hand / finger IK
Blender retarget / penetration avoidance
CF original animation
CF original sound
world model / extra polish
```

---

# 9. Agent 执行决策树

每个新 Agent：

```text
1. git status --short --branch
2. read AGENTS.md
3. read plan.md
4. confirm master
5. use current task below; do not invent a different lane
```

当前必须执行：

```text
Q0: P4-M01-N02 是否已 PASS/BLOCKED？
  NO -> 执行 §6 Runtime Artifact Acquisition & Static Triage。
  YES -> 按最新 Chat/Sol Review 状态继续。
```

N02 内部：

```text
Q1: 已定位可信 CF install/runtime root？
  NO -> A1 -> A2 -> A3 -> A4 -> A5，直到定位或形成 bounded negative。
  YES -> Step B inventory。

Q2: 有 EXE/DLL/runtime archive/shader candidates？
  NO -> Step E5/其他 roots/旧版备份线索，再按 §6.7 收口。
  YES -> Step C static triage。

Q3: direct relevant strings / resource evidence 命中？
  YES -> Step D static xref。
  NO -> E1 imports -> E2 modules -> E3 archives -> E4 shaders -> E5 launcher manifests -> E6 protected-client alternate route。

Q4: 得到 credible loader/resolver/consumer candidate？
  YES -> N02 PASS A，停止扩大，交回 Chat/Sol。
  NO -> 若有明确 top candidate 但需 deeper disassembly，N02 PASS B；否则按 §6.7 bounded blocker。
```

P5 决策仍是：

```text
P4-M01 未被 Chat/Sol Review 为 NATIVE_MATERIAL_RECOVERED
    -> P5-T02 保持 PAUSED

P4-M01 = NATIVE_MATERIAL_RECOVERED
    -> 恢复 Transformers/native finalist flow
```

Local Executor 可以更换模型/Agent，但 acceptance criteria 不随模型改变。实际 executor provenance 来自 harness/runtime 显示；commit `Co-Authored-By` footer 不是权威模型身份。

---

# 10. Evidence 索引

## P4 frozen baseline

```text
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
work/m4a1_s_bornbeast/p4_prototype_01/build_report.json
work/m4a1_s_bornbeast/p4_prototype_01/validation_report.json
work/m4a1_s_bornbeast/p4_prototype_01/upstream_trace_report.json
work/m4a1_s_bornbeast/p4_prototype_01/deploy_report.json
work/m4a1_s_bornbeast/p4_prototype_01/prototype_01_game_regression.json
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json
```

## P4-M01 / N01

```text
work/m4a1_s_bornbeast/p4_m01_native_material/
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
work/m4a1_s_bornbeast/p4_m01_native_material/n01/weapon_material_differential.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/cfg_consumer_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/channel_semantics_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/engine_binding_closure.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json
```

## P4-M01-N02

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/artifact_inventory.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/string_hits.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/candidate_rank.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/static_xref_report.json   if applicable
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/acquisition_report.md
```

## P5

```text
work/p5_leishen/t01_reference/
work/p5_leishen/t01/
work/p5_leishen/t02/
```

`work/**` 中的 Markdown/JSON 是 evidence，可以保留；它们不是项目流程 authority。

---

# 11. 关键历史提交

```text
10aa99b770e575300ca3c28324ef3de3d5b70c6b  P4 frozen implementation baseline
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d  RV-04 evidence
632ede449578f688cea7e6b5f40cbf03700aaaa5  P4-M01 initial material exploration
bded9e8a6f7f95997d9717eb8f35beb02619f153  R1 correction start
0dc5793b6e47cb20da9e44aebcec2195194bd6f2  R1 narrow correction
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19  N01 Phase-0 cleanup
69c03d8769db2107cd94cae11accc750716466ae  scanner / lineage / binding-key repair
ea11ba143d859193213f24ab92248ff8a576b135  bounded runtime-consumer search
46fcacebbc631fc05e0d491470b5e5482bca4533  JSON/scope/provenance cleanup
95b6bb363a5f00daf01193f53e2a27cff9cea3f8  provenance parameterization / closure wording
65292c742d545459974c56aec494d1d9c44039a8  final unified config-scope guard
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2  P5 legacy candidate pre-scan
```

旧根目录 Task/Review Markdown 的有效结论已合并到本文件。逐轮细节查 Git history。

---

# 12. Evidence grade 约定

| Grade | 含义 |
|---|---|
| `OBSERVED` | 当前样本直接观测值 |
| `STRUCTURALLY_VERIFIED` | 二进制/格式结构已机械验证 |
| `VERIFIED_CORPUS_STATISTIC` | 在声明 corpus/scope 内可复现统计 |
| `DIFFERENTIAL_SUPPORTED` | 多个相关样本差分支持，但未必等于 engine semantic proof |
| `STRONG_HYPOTHESIS` | 强结构线索，仍有替代解释 |
| `HYPOTHESIS` | 待验证解释 |
| `TOOL_BEHAVIOR` | 本仓库工具实际行为，不等于原 CF runtime 行为 |
| `SOURCE1_DESIGN_CANDIDATE` | 为 Source 1 实现提出的映射，不是恢复出的 CF 原事实 |
| `NEGATIVE_RESULT_SCOPED` | 只在明确扫描范围内的 negative |
| `OPEN_UNRESOLVED` | 当前证据不足，保持未决 |
| `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` | 旧 corpus 缺能继续证明 engine consumer 的新输入 |

禁止为了推动进度把 `HYPOTHESIS`、filename convention、视觉相似或单一统计相关升级成 `VERIFIED`。

---

# 13. Git / data / handoff

所有 Agent 严格遵守 `AGENTS.md`。核心底线：

```text
master only
never upload data/**
no git add . / -A / --all
no force push
no destructive reset/clean
no raw CF client/runtime binaries in Git
```

N02 特别规则：

```text
未知 CF binary 不执行
不做进程注入/内存 dump/anti-cheat bypass
只做 static/read-only
raw runtime files 只留本机
报告只提交 metadata/hash/offset/xref/call-chain evidence
```

推荐同步：

```bash
git status --short --branch
git fetch origin
git pull --rebase origin master
```

项目状态只有本文件是 authority；`README.md` 是入口说明，`AGENTS.md` 是安全合同，`work/**` 是 evidence。