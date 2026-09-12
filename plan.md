# CF 武器 -> CS:GO Legacy Source 1 — 蓝图与当前任务

> 本文件同时是 **长期 pipeline / Gate / 冻结事实** 和 **当前状态与当前任务**。  
> 原独立 `task.md` 已并入 **§0**。Git 规则看 [`AGENTS.md`](AGENTS.md)，角色看 [`README.md`](README.md)。

---

# 0. 现在的情况

```text
Date captured                 : 2026-09-12
P4 Source 1 / MIGI baseline   : PASS / FROZEN
P4-M01 native material        : INCOMPLETE
P5 雷神 identity              : T01 图鉴已确认；T02 等原生材质方法
Current executor task         : NONE
Last completed task           : P4-M01-N05-A
Last executor evidence commit : pending this push
State                         : WAITING_REVIEW / DECODE_RECOVERED_BINDING_OPEN
```

## 0.1 已钉死

- P4 证明 CF LTB 能进 Source 1 / MIGI（M4A4 槽）。Prototype **不是**最终雷神，也 **不是**原生材质。
- 黑骑士 Bute 只绑 PV LTB + PV DTX + 共用 RS（TEXTURE1）。TGA/CFG 路径在 packed BF005 上是 0。
- 已尝试的解码没有恢复出原生枪身 atlas。PV DTX 的“能量/标量层”仅是猜测布局后的视觉分类，真实 codec / shader role 未闭合；不能据此认定本机没有 albedo。N03-H 的适用范围见 §4.19、§4.26。
- 网格 UV 按 512×512 枪件 atlas 排。CS1.6 / ComfyUI 只能当视觉对照，禁止当 P4-M01 final 像素。
- `playerviewmesh.fxo` 有 Alpha/Normal/Specular/Emissive **槽名**，没有文件路径。
- CShell 有 `modeltextures\SpecularMap\%s`（12 LEA，后期 `.dtx` 路线）。黑骑士没有 `SpecularMapName`。
- `crossfire.exe` 明文岛：`MODELTEXTURES\Shader\WeaponShader\` + `.cfg`，**0 代码引用**。它是 stub，只导入 packed `crossfirebase.dll`（`.tvm0`）。
- 磁盘 `crossfirebase.dll` 无 WeaponShader 明文。N04-F 当时的 PID 33100 = `x64/crossfire.exe`，`OpenProcess(VM_READ)` = Win32 **5**。这是历史观测，不是当前进程状态；未绕过 ACE。

## 0.2 当前任务

```text
Task ID : NONE
State   : WAITING_REVIEW
Last    : P4-M01-N05-A
Result  : DECODE_RECOVERED_BINDING_OPEN
```

Executor 已完成 N05-A，**尚未 Review / 尚未写入 §4 冻结**。没有下一轮执行单。

N05-A 证据：

- `scripts/material_recovery/n05a_decoder_provenance_audit.py`
- `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05a_decoder_audit/`

要点（待 Review 接受后才能升格冻结）：

- 合成 Jupiter DTX（RGBA32 / DXT1 16×16）正例通过；`data/rf017/ModelTextures` 3258 个本机 DTX 无合法头对照 → `NO_CURRENT_CLIENT_CONTROL`。
- inventory / `rez/` 的 BornBeast PV、QV 以及 RoyalDragon / GreenVein 对照仍不是 -2/-3/-5；LZMA/LTC 前置不满足；RezExtract 4/8 交换不能修好这些副本。
- **同一 QV logical path 有两份副本**：`rez/rf017.rez` `WEAPONS/QV-M4A1_S_BornBeast.DTX` = 32932 B，SHA `ea99c710…`，等于 loose；`rez2/RF017.REZ` 同路径 = 524452 B，SHA `73a954f8…`，标准 Jupiter DTX version -5，DXT1 1024×1024，header 164 + payload 524288。python 与 CFRezManager 都能解出枪件 atlas。
- 这是 `SkinFileName` / QV，不是 `PViewSkinFileName` / PV。PV DTX 仍未解。runtime 是否加载 `rez2` 副本未证。未把 QV 图套到 PV mesh。P4-M01 仍为 INCOMPLETE。

N04-F 进程读取路线继续暂停。不自动开 N05-B。

N05-A 结果表（Review 用）：

| 结果 | 验收含义 | Review 后可考虑的下一步 |
|---|---|---|
| `DECODE_RECOVERED_BINDING_OPEN` | 有结构验证的 deterministic decode + 原生像素；绑定仍待证 | §0.4 路线 B，结合 FXO 与 Bute 闭合 |
| `PROVENANCE_OR_VARIANT_MISMATCH` | 找到可复现的副本/提取/格式差异，明确哪一层不一致 | 精确修复输入选择或 adapter，再 Review |
| `REFERENCE_DECODERS_UNSUPPORTED` | 正例通过，但声明的真实样本/变换未通过 | 转路线 B；需要新副本时再用 C |
| `CONTROL_OR_TOOLCHAIN_BLOCKED` | 未能建立可信对照或源码工具不可构建 | 记录具体依赖，不能把工具失败算资源不存在 |

本轮已选 `DECODE_RECOVERED_BINDING_OPEN`。P4-M01 仍为 INCOMPLETE。等待 Review。

## 0.3 禁止

- 不宣布 P4-M01 PASS
- 不把 CS1.6 / ComfyUI / 图鉴当 native final
- 不注入、不补丁、不驱动、不 NtRead 绕过 ACE
- 不 git add `data/**`、CF `.exe/.dll/.fxo/.dmp`

## 0.4 2026-09-12 联网复盘：可尝试路径与顺序

**判断**：现在缺的是三层不同证据：①正确字节/codec，②资源到 mesh/piece/sampler 的绑定，③渲染语义。N04-F 只堵住 packed consumer 的进程读取；N03-H 没有排除所有 CF 解码方式；N04-C 只读了 FXO 名称，没有分析指令。不能把三层问题都压到“先取得内存 dump”上。

以下为规划候选，不是已验证的当前 CF 行为。N05-A 已执行，§0.2 现为 WAITING_REVIEW。

| 优先级 / 路线 | 新依据与要回答的问题 | 最小实验 / 成功标准 | 边界与停止条件 |
|---|---|---|---|
| 1 / A：decoder 与 provenance 复核 | 标准 decoder 0/16 失败意味着对照未建立；外部源码存在 CF 头字段差异 | N05-A：7 个真实样本 + 标准正例，分离 raw/normalized/decoded；得到合法结构或明确不支持的层级 | 不以“导出成功/颜色像能量”证明语义；无新线索不继续全库排列组合 |
| 2 / B：FXO 离线语义分析 | `playerviewmesh.fxo` 是 D3D9 effect；微软提供二进制 effect 加载、参数枚举和反汇编接口 | 候选 N05-B：在自建工具的 D3D9 device 中载入本地 effect，先枚举 parameter/technique/pass/default，再提取普通/Alpha/Emissive 路径的采样、通道运算、混色和常量；`playermesh.fxo` 作对照 | 读到代码不等于该 technique 被黑骑士选中；默认值不等于运行值。解析失败记录 HRESULT/依赖，不转为附加 CF |
| 3 / C：资源副本与版本差分 | 已有 `rez/`、`rez2/` 的 QV LTB 不同，loose Bute 与 packed BF005 也曾不一致 | 仅围绕已绑定的 BornBeast/Transformers logical paths 建副本矩阵，记录版本/哈希/相应 Bute 与 RS；有新合法输入时对比头、binding、shader slot | 当前载入优先级未知就保持候选；不按文件夹名或视觉选择“真副本”，不重复无差别扫描 25 万 entry |
| 4 / D：可合法取得的兼容旧版本作参考 | Jupiter / CF 工具可解释标准路径，较早版本或不同地区 variant 可能暴露更少的格式差异 | 只有已获得可信版本与相关资源后，做旧/新 loader 或资源格式差分，提炼规则回验当前本机样本 | 尚无这样的新输入，不承诺能取得；旧版本行为/像素不自动成为当前 CF final，也不采用私服/脱壳工具包补缺口 |
| 产品备选 / E：可用外观版本 | P4 已具备构建/部署能力，CS1.6 atlas 可作已有视觉演示 | 用户选择此交付目标后单独生成可看版本，`final_cf_material=false` | 不计为 native PASS，不借此跳过 P5 身份 Gate；此次仅规划，不部署 |

**B 的具体可行性**：[`D3DXCreateEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxcreateeffect) 接受 ASCII 或 binary effect；[`ID3DXBaseEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/id3dxbaseeffect) 可枚举参数、technique/pass 和取值；[`D3DXDisassembleEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxdisassembleeffect) 可反汇编已加载 effect。需要自建 D3D9 device、匹配的 D3DX9 依赖及 effect 成功解析，**不是对 `.fxo` 跑 DXBC 工具，也不是执行 CF 客户端**。先得到明确公式，再决定是否值得做一次只换单个通道/常量的离线验证；不靠调参把外部参考“拟合”成原生。

**没有默认启用的路径**：继续扫同一 packed PE 的 strings/xref、重复 VM_READ、换权限/驱动/注入抓取，都没有本轮新证据支持。RenderDoc 官方[支持表](https://github.com/baldurk/renderdoc/blob/v1.x/README.md#api-support) 明确不支持 D3D9；[apitrace](https://github.com/apitrace/apitrace/blob/master/docs/USAGE.markdown) 支持 D3D9，但 Windows 跟踪需要 wrapper/插入，不能当成无侵入方案。只有未来自有离线 harness 才考虑图形跟踪；不用于本次 ACE 保护进程。用户已有合法 dump 时可保留原 C 分叉，但它不再是所有离线工作的前置条件。

**源码与参考入口（联网核查日期 2026-09-12）**：

| 来源 / 固定版本 | 已核实的具体内容 | 对当前任务的限制 |
|---|---|---|
| [no-lith/RezExtract `src/rez.cpp`](https://github.com/no-lith/RezExtract/blob/b3f87a9c731c0bbc1900da2fd37e41b9a02e1e63/src/rez.cpp#L338-L369) | `b3f87a9`：DTX 提取选项会交换 offset 4/8 的四字节字段以恢复版本位置 | 只解决某类头换位；本次 PV/QV 头不符合，不能据此宣称已有新 decoder |
| [YoungFine0825/LTB2FBX `DtxConverter.cpp`](https://github.com/YoungFine0825/LTB2FBX/blob/06d749d56d6c929ba6c538cc26aa11cc1f7f1566/Source/DtxConverter.cpp)、[底层 `dtxmgr.cpp`](https://github.com/YoungFine0825/LTB2FBX/blob/06d749d56d6c929ba6c538cc26aa11cc1f7f1566/ThirdParty/lithtech/runtime/shared/dtxmgr.cpp) | `06d749d`：尝试 LZMA 后走 LithTech texture loader；`dtx_Create` 检查 resource type/version/mip 范围 | 是可审计参考与工具对照，不能承诺支持 2026 本机 variant；不用其测试资源当 final |
| [iQuitt/Vortigaunt `DtxConverter.cpp`](https://github.com/iQuitt/Vortigaunt/blob/d739d1f900c261fc1ae67e11b436410084dda1aa/src/core/converters/DtxConverter.cpp)、[底层 `dtxmgr.cpp`](https://github.com/iQuitt/Vortigaunt/blob/d739d1f900c261fc1ae67e11b436410084dda1aa/ThirdParty/lithtech/runtime/shared/dtxmgr.cpp) | `d739d1f`：也使用 LZMA/同源 LithTech loader | 两工具都失败/成功不是两份独立的 CF runtime 证明 |
| [no-lith/Jupiter](https://github.com/no-lith/Jupiter)、[jsj2008/lithtech](https://github.com/jsj2008/lithtech) | 标准 engine/render/resource contract 的源码参考入口，沿用 §4.9 | 公开仓库不是当前 CF 或官方授权来源证明；具体采用函数时再固定 commit |

推进规则：**A 完成并 Review → 选择 B 或修复明确的输入差异 → 确有新版本证据再 C/D**。像素、绑定、公式分别验收；只有 §3 的全部条件成立才能 native PASS。P5-T02 仍待原生方法，不能用这次规划提前宣告恢复。

---

# 1. 总体目标

把 CrossFire 本地资源可靠转换为 CS:GO Legacy Source 1 / MIGI 可用武器 Mod，并最终完成目标武器身份、原生材质、发布质量与后续动画/IK增强。

完整主链：

```text
CF 原始资源
-> REZ / LTB / DTX / TGA / CFG / audio 提取与解析
-> 武器模型 / UV / 骨骼 / 动作关系
-> Source 1 SMD / QC / VMT / VTF
-> compile / validate / package / MIGI
-> CF 原生材质恢复
-> 最终目标资产确认
-> release-quality replacement
-> Inspect / IK / CF 原动画/声音等增强
```

---

# 2. 阶段 Pipeline

## P0-P3 — 前置基础

包含资源解包、音频工具、LTB 基础研究、Source 1 兼容性与 M4A4 映射等历史基础工作。

状态：`DONE / HISTORICAL`。

## P4 — Source 1 conversion baseline

目标：证明 CF 第一人称武器能稳定进入 Source 1 构建与 MIGI runtime。

固定链：

```text
local CF LTB
-> mesh / UV / normal / bone mapping
-> SMD / QC
-> Source 1 material references
-> studiomdl
-> Crowbar roundtrip
-> validation
-> package / staging
-> MIGI deploy
-> user runtime Gate
```

### P4 冻结结论

```text
P4 baseline = PASS / FROZEN
```

冻结身份：

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

已证明：

- fresh local CF LTB 能进入完整 Source 1 构建；
- M4A4 skeleton / sequence / attachment contract 可工作；
- mesh-to-bone、SMD/QC、studiomdl、roundtrip、validation、package、deploy 可闭环；
- runtime changed-state 用户 Gate 通过。

P4 从未证明：

- Prototype 就是最终雷神；
- CF 原生材质已经正确恢复；
- external texture 可作为 final；
- visible Inspect / hand-finger IK 已完成；
- CF 原动画、声音、world model 已最终化。

### RV-04 冻结反例

4/4 高风险 mutation 被预定 Gate 拒绝：

```text
unsafe output root              -> manifest_contract
same sequence count/wrong name -> sequence_names_and_count
bone semantic swap             -> smd_manifest_bone_corners
missing critical VTF           -> material_closure
```

`material_closure` 只证明 Source 1 引用闭合，不证明上游 CF 像素语义正确。

---

# 3. P4-M01 — Native Material Recovery

目的：补齐 P4 从未证明的 CF 原生材质 fidelity。

历史 Prototype 曾使用 external CS1.6 BornBeast texture，因此必须把原生材质作为独立 hard requirement。

目标链：

```text
BornBeast local LTB / UV
+ DTX
+ Alpha / Normal / Specular TGA
+ WeaponShader CFG
+ same-family variants
-> container / storage evidence
-> real mesh/piece material binding
-> CFG / render semantics
-> native-only composition
-> reproducible Source 1 mapping
```

最终可见材质只能来自：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

禁止 final pixels 来自：

- external MOD texture；
- 官网/网络图片；
- AI 生成/补全贴图；
- 从 reference 反采样后回写的颜色。

### P4-M01 PASS Gate

只有同时满足：

1. geometry / UV 来自 local CF；
2. 实际材质资源都有 path + SHA；
3. mesh/piece -> material/texture binding 有结构或 direct consumer evidence；
4. CFG/render semantics 足够解释真实消费方式；
5. visible color 100% local CF / verified semantics；
6. 0 external pixels；
7. clean output 可重复；
8. BornBeast native result 可稳定辨认；

才能判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

---

# 4. P4-M01-R1 / N01 / N02 — 冻结技术结论

## 4.1 R1

R1 已完成早期材质 evidence 纠错，状态：

```text
P4-M01-R1 = ACCEPTED / COMPLETE
```

## 4.2 DTX

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

## 4.3 TGA

Formal inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular repair 已结构验证；文件名不等于 shader role 证明。

## 4.4 WeaponShader CFG

237/237 文件满足：

```text
non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

已接受测量：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

证据等级：

```text
single-mod3 structure          STRUCTURALLY_VERIFIED
per-file measured sequence     OBSERVED
cross-skin differences         DIFFERENTIAL_SUPPORTED
CFG = 1D LUT                   HYPOTHESIS
CFG = packed shader constants  HYPOTHESIS
actual semantic consumer       OPEN_UNRESOLVED
Source1 mapping                SOURCE1_DESIGN_CANDIDATE
```

## 4.5 ArmModel positive control

ArmModel text CFG 已证明 engine-format 中存在：

```text
[Textures]
[Techniques]
[Properties] PieceIndex
```

但不能直接推出 weapon 使用相同 contract。

## 4.6 Weapon binding

```text
LTB post-mesh short ASCII field exists        STRUCTURALLY_VERIFIED
short id == texture/material slot             NOT PROVEN
repo parser semantic material use             NOT PROVEN
ObjExporter Models->ModelTextures mirroring   TOOL_BEHAVIOR
original CF piece->texture binding            OPEN_UNRESOLVED
```

Repo exporter 的路径镜像不是原 CF runtime proof。

## 4.7 N01 scope freeze

最终 scanner scope：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
config_index_keys                    = 18
config_index mapping tuples          = 72
raw_scan_files_seen                  = 355
raw_scan_files_decoded               = 355
```

统一 predicate：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

Scoped negative：

```text
BornBeast      text-config hits = 0
Transformers   text-config hits = 0
Jewelry        text-config hits = 0
BlueDiamond    text-config hits = 0
.dat consumer hits             = 0
BornBeast derived-output hits  = 4 / DERIVED_OUTPUT_HIT only
```

N01 在关闭当时的状态：

```text
P4-M01-N01 evidence      = COMPLETE / FROZEN
N01 old-corpus search    = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
engine binding closure   = OPEN_UNRESOLVED
```

这只描述 **旧 `data/**` corpus 的证据边界**；N02-A 后已取得新的本机 runtime 输入，不能再把整个 P4-M01 路线概括为“没有 runtime artifact”。

## 4.8 N02-A runtime acquisition freeze

Review 接受提交：

```text
a561924a9c0795932f328de929bee510f6e2719a
P4-M01-N02-A = ACCEPTED / COMPLETE
```

可信 runtime root：

```text
D:\Program Files\CF(2)
```

选择依据为本机只读观测同时存在：

```text
CF executable signal
REZ signal
rez/ directory
link.ini
```

N02-A 在该 root 建立 depth<=6、限定扩展名的 runtime artifact inventory：

```text
total candidates = 2273
.bin             = 1291
.rez             = 476
.dll             = 272
.ltc             = 73
.pak             = 58
.dat             = 44
.exe             = 27
.fxo             = 14
.ini             = 8
.lta             = 5
.fx              = 3
.lto             = 2
```

SHA256：

```text
2262 / 2273 captured
11 omitted = files >512 MiB, recorded explicitly as null
```

对 P4-M01 信息增益最高的新输入：

```text
73 x rez/Butes/*.ltc
35 x bf-prefixed .ltc within that set
rez/bf000.lta = 30,002 bytes
17 shader-bearing files (.fx/.fxo)
272 DLL + 27 EXE available for later static consumer tracing
476 REZ available for later bounded archive work
```

接受的边界：

- `rez/Butes/*.ltc` 的存在是 **真实 runtime artifact evidence**；
- 它们此前未被 N01 的 unpacked `data/**` config scope 覆盖，因此重新打开 config 路线；
- `bf` 文件名族只构成候选排序信号，**尚不能**证明 BornBeast / bdf / weapon binding；
- shader/EXE/DLL/REZ 目前只是 inventory candidate，尚无 strings/xref/decompile consumer proof；
- 其余 9 个硬编码候选 root 不存在只形成该探测集合内的 bounded negative，不代表对整机所有可能安装位置的穷尽证明。

当前状态更新为：

```text
runtime artifact acquisition blocker = CLEARED_FOR_STATIC_TRIAGE
engine binding closure               = OPEN_UNRESOLVED
CFG/render semantic closure          = OPEN_UNRESOLVED
P4-M01                                = INCOMPLETE
```

后续应优先从低成本、直接相关的 runtime config 证据开始；只有 config 路线不足时，再升级到 PE / shader / archive consumer tracing。

## 4.9 LithTech / CrossFire reference hierarchy

后续格式研究不再默认从 raw bytes 独立逆向。固定采用以下 reference hierarchy：

```text
1. public LithTech/Jupiter source
   -> 标准 engine/file/runtime semantics 的第一参考

2. CF-specific community tools
   -> CrossFire variant 的 positive control / differential clue

3. this repo CFRezManager
   -> 本项目资源入口、浏览、提取、快速 decode/preview implementation

4. current local CF runtime evidence
   -> 对当前 CrossFire 客户端实际行为的最终验真来源
```

核心原则：

```text
standard Jupiter behavior
-> compare existing CF tools / repo implementation
-> validate against current CF runtime artifacts
-> reverse only the remaining CF-specific delta
```

### 4.9.1 已确认的 public reference implementations

长期参考：

```text
https://github.com/no-lith/Jupiter
https://github.com/jsj2008/lithtech
```

已确认公开 Jupiter 源码包含或可追踪：

```text
LIB-ButeMgr
LIB-LTAMgr
LIB-DTXMgr
LIB-RezMgr
runtime/model
runtime/render / render_a / render_b
clientfx
controlfilemgr
```

`jsj2008/lithtech/runtime/model/src/model_load.cpp` 还直接暴露标准 Jupiter LTB 的 piece texture indices、render style、bone/node、animation compression/load contract，因此后续 LTB 研究应先做 Jupiter-vs-CF differential，而不是重复从零猜标准字段。

这些源码是 **REFERENCE_IMPLEMENTATION**，不是当前 CF client behavior 的自动证明；版本差异必须由本机 artifact 验证。

### 4.9.2 已确认的 CF-specific community references

可作为 positive control / differential reference：

```text
https://github.com/iQuitt/Vortigaunt
  LTB -> SMD with bones/animations
  DTX support
  REZ extraction explicitly tested with CrossFire

https://github.com/bxclip/Tool-Crossfire
  project declares LTB -> LTA / CFT -> CSV / LTC -> LTA
```

社区工具结论等级默认：

```text
EXTERNAL_TOOL_BEHAVIOR / POSITIVE_CONTROL
```

除非源码可审计并被当前 CF artifact 复现，否则不能直接升级为 runtime fact。尤其只提供 binary/rar 的工具不应作为 production dependency，也不应未经审计执行未知二进制。

### 4.9.3 CFRezManager role freeze

`CFRezManager` 的长期角色冻结为：

```text
REZ browse / inventory / extract / repack
format preview
DTX / image / audio / config / model quick decode
local deterministic conversion helpers
reference-adapter implementation
```

它 **不是** 整个 CF engine semantics 的唯一 authority。

当前 repo 已存在：

```text
CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs
```

该实现已经给出 LTC 的 deterministic native decode path；因此后续 N02-B 不应再把“LTC 是什么压缩/编码格式”作为首要逆向问题，而应先：

```text
validate existing LTC decoder on current runtime samples
-> recover decoded LTA/Bute-form content where possible
-> parse semantics using Jupiter Bute/LTA reference
-> correlate resource bindings
```

只有现有 decoder 与真实 runtime sample 不一致时，才进入 LTC format differential reverse。

## 4.10 N02-B-R1 / N02-C Review freeze 与 N02-D/E rework boundary

Review 接受：

```text
4d7c8b64d44c7d1848f1abb5182f511e5a91107f  P4-M01-N02-B-R1
2a4054dba6cc03bedb43201aa89692c6e0a36e88  P4-M01-N02-C
```

N02-B-R1 已确认当前 runtime `rez/Butes/*.ltc` 的真实 decode chain：

```text
raw magic 54 83 B2 E1
-> CrossFire wrapper XOR unlock
-> unlocked 00 00 00 00 header
-> LithTechLtcNativeDecoder
-> readable LTA/Bute-style text
```

当前样本：

```text
73 / 73 wrapper unlock success
73 / 73 native decode success
73 / 73 Bute/LTA-style parse success
```

因此以下长期事实可以冻结：

```text
current CF runtime Bute config layer exists                    VERIFIED_RUNTIME_INPUT
repo CrossFire LTC wrapper + native decoder works on 73/73    STRUCTURALLY_VERIFIED
weapon/resource relations exist in decoded Bute records        DIRECT_CONFIG_RELATION
```

N02-C 在 `bf005.ltc` 中找到 10 个 M4A1-family Weapon records，并直接读取：

```text
ModelFileName
SkinFileName
PViewModelFileName
PViewSkinFileName
RenderStyleFileName
PViewRenderStyleFileName
```

因此可以冻结：

```text
M4A1-family runtime config records found     ACCEPTED / COMPLETE
M4A1 config -> resource-path relation        DIRECT_CONFIG_RELATION
BornBeast direct config reference            NOT FOUND IN THIS SCOPED LAYER
```

注意：`BornBeast / Transformers / Jewelry / BlueDiamond` 在该 decoded Bute layer 中未命中，只是对声明 scope 的 bounded negative；不能推出这些 family 不存在于其他 config/material/runtime layer。

### N02-D / N02-E Review 结论

以下提交 **不冻结**：

```text
be1b150b0cc4e67e4861779079887f1cf243d9a1  P4-M01-N02-D
2f94db91099814523d9137f2c67f3ebfed7de869  P4-M01-N02-E
```

状态统一为：

```text
P4-M01-N02-D = REVIEW_REWORK_REQUIRED
P4-M01-N02-E = REVIEW_REWORK_REQUIRED
```

原因 1：N02-D 的 REZ recursion 没有把 directory parent path 写入 file entry，最终 index 实际为：

```text
lowercase basename -> REZ entries
```

而不是：

```text
archive-relative full logical path -> REZ entries
```

因此它不能区分例如：

```text
Models/PlayerView/PV-M4A1.LTB
ModelTextures/PlayerView/PV-M4A1.DTX
```

只按 basename 命中的结果不能升级为 exact runtime path binding。

原因 2：对没有扩展名的 `ModelFileName / PViewModelFileName`，N02-D 使用：

```text
.ltb / .dtx / .tga / .lto / .ltc / .rez / .dat
```

宽泛 fallback。该策略会把 model path 引向非 model artifact；在没有 consumer semantics 证据时不成立。返工后 extensionless model path 默认只允许按 field semantics 尝试 exact logical path + `.ltb`，其他扩展名必须另有证据。

原因 3：N02-E 直接继承 N02-D 的候选 entry，因此其 payload hash 虽然是对选中 offset/size 的真实机械测量，但 **不能反向修复错误或过宽的 path selector**。

N02-E 当前可保留为未冻结观测：

```text
29 selected unique REZ entries
12 catalog-MD5 matches
17 catalog-MD5 mismatches
0 skipped
0 selected payload SHA256 matches known P4 BornBeast source LTB SHA256
```

但不能把这组数字解释为：

```text
M4A1 exact runtime artifact closure
BornBeast runtime non-identity closure
```

直到 N02-D-R1 通过 full-path revalidation。

另外 N02-E 报告存在内部文字不一致：统计为 `12 MATCH / 17 MISMATCH / 0 skipped`，verdict 段却写成“全部 match 或 skipped”；该结论文本不得引用为冻结事实。

对 DTX MD5 mismatch 的 `LZX` 解释当前仅为：

```text
HYPOTHESIS / NEEDS_FORMAT_OR_CONSUMER_EVIDENCE
```

不能冻结为“REZ directory MD5 一定计算在某个 pre/post compression representation”之类的 engine fact。

原始 N02-D / N02-E 提交仍不冻结。后续 D-R1 / D-R2 / E-R1 / E-R2 已在 §4.11 接受。

## 4.11 N02-D-R1 / D-R2 / E-R1 / E-R2 freeze

Review 接受：

```text
f468e96f2d956ee82f69f8372c9c7c36423897ec  P4-M01-N02-D-R1
e6204b46e841b19386e82f4f103883981ae2ee07  P4-M01-N02-D-R2 review 6/6
c3e8872369aad29285cbf4ddb4a821a66eb127ba  P4-M01-N02-D-R2 refined checklist ACCEPTED
dc3ac1b69843141b54b2ae97b868aa4a7a242d01  P4-M01-N02-E-R1
2e0c750624832e28a5292a488b4bad81b3934c15  P4-M01-N02-E-R2
```

N02-D-R1 以 archive-relative full logical path 重做 REZ binding，60/60 `(WeaponName, field)` 命中。接受的规则：

```text
backslash -> slash, uppercase
strip one leading virtual root in {Models/, ModelTextures/}
keep RS/ (literal rf002.rez directory)
extensionless ModelFileName / PViewModelFileName -> only .LTB
multi-archive hits reported, no load-order authority claimed
```

因此：

```text
bf005 M4A1 exact REZ full-path binding    ACCEPTED / COMPLETE
```

N02-E-R1：8 个 N02-D-R1 LTB 解压后均无 Jupiter LTA `(piece` / `(texture` / `(renderstyle` / `(material` 原子，也无 `.dtx` / `.tga` 内嵌引用。LTB 内 piece→DTX/TGA 不能从该 binary 直接读出。

```text
LTB-internal piece -> texture/material    OPEN_UNRESOLVED
MATERIAL_BINDING_PARTIAL                  ACCEPTED as round status
```

N02-E-R2：24 个 unique `(rez_path, full_path)` payload 全部 bounded SHA256 成功，**0** 个等于 BornBeast P4 inventory。该结论把 N02-C 的 bf005 文本 negative 提升到 byte identity：

```text
bf005 M4A1 runtime family
!=
BornBeast native asset
SCOPED_NEGATIVE_ACCEPTED
```

N02-E 原始提交的 basename index / 过宽 extension fallback 仍不得引用。

## 4.12 N03-A freeze

Review 接受提交：

```text
23e275a4be0eed8fd90132095ed0c283b36a39d9  P4-M01-N03-A
P4-M01-N03-A = ACCEPTED / CANDIDATE_ONLY
```

从 BornBeast inventory 做 exact-token 反向查找（basename / stem / logical path / SHA256 / MD5；拒绝更长 ident 前缀）。

Loose config 范围：N02-A config-role ∪ `rez/Butes/` 目录，107 文件，73/73 LTC decode，7337 lisp records：

```text
DIRECT_CONFIG_FIELD hits     0
bounded text-token hits      0
```

因此：

```text
loose rez/Butes Bute+config layer
does not name BornBeast inventory assets
SCOPED_NEGATIVE_ACCEPTED
```

同一轮在当前客户端 REZ 中用 exact path（CFG 为 basename+size 过滤器）做 bounded payload SHA256，6/6 inventory 角色均命中：

```text
geometry   PLAYERVIEW/PV-M4A1_S_BornBeast.LTB
           rez/RF016.REZ, rez2/RF016.REZ, rez4/RF016.REZ
           SHA256 == inventory                          PAYLOAD_IDENTITY
base_dtx   PLAYERVIEW/PV-M4A1_S_BornBeast.DTX
           rez/rf017.rez                                PAYLOAD_IDENTITY
alpha      AlphaMap/M4A1_S_BornBeast_alpha.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
normal     NormalMap/M4A1_S_BornBeast_N.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
specular   SpecularMap/M4A1_S_BornBeast_S.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
shader_cfg WeaponShader/M4A1_S_BornBeast.CFG
           rez/rf017.rez                                PAYLOAD_IDENTITY
```

`shader_cfg` 的 inventory 路径在 strip `ModelTextures/` 后变成 `SHADER/WEAPONSHADER/...`，runtime 实际为 `WeaponShader/...`（无 `Shader/` 前缀）。这是 normalisation miss，不是缺文件。

不能从 N03-A 推出：

```text
BornBeast has no runtime consumer anywhere
WeaponShader CFG is the consumer table
piece -> DTX/TGA binding
P4-M01 PASS
```

当前有效 closure 边界见 §4.13 更新后的表。N03-A 的 loose-config negative 仍然成立。

## 4.13 N03-B freeze

Review 接受提交：

```text
f839bdb2f572ad5269a263a62ed2b3e5f87cd947  P4-M01-N03-B
P4-M01-N03-B = ACCEPTED / BORNBEAST_CONSUMER_CONFIRMED
```

REZ-resident 扩展名选择：`.cft` `.lta` `.txt` + `BUTES/*.ltc`，1559 unique payloads。

```text
TABLE/*.CFT exact BornBeast tokens     0   SCOPED_NEGATIVE
.lta / .txt                            0   SCOPED_NEGATIVE
packed Butes/BF005.LTC hits            1 file
```

Consumer 不在 loose `rez/Butes/bf005.ltc`，而在：

```text
rez/RB001.REZ
  -> Butes/BF005.LTC
  size 5,892,359
  decode 8205 lisp records
```

该 packed payload 与 loose `rez/Butes/bf005.ltc`（N02-C / N03-A 用的那份）**不是同一文件**。

Canonical Weapon 记录：

```text
WeaponName     M4A1-黑骑士
StandardName   M4A1_S_BornBeast
PViewModelFileName  Models\PlayerView\PV-M4A1_S_BornBeast
PViewSkinFileName   ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx
```

`PViewModelFileName` / `PViewSkinFileName` 精确对应 N03-A 已 SHA 验证的 inventory geometry + base_dtx。

同一 packed 表里还有一批变体，共用 `PV-M4A1_S_BornBeast` LTB，但 DTX 不同（NobleGold / BeijingOpera / PCCafe 等）。变体 DTX **不是** P4 inventory `base_dtx`。

N03-B 快照字段还包括：

```text
ModelFileName  Models\Weapons\QV-M4A1_S_BornBeast.ltb
SkinFileName   ModelTextures\Weapons\QV-M4A1_S_BornBeast.dtx
RenderStyleFileName        RS\NinjaTranslucent.ltb
PViewRenderStyleFileName   RS\PVModelDefault.ltb
BigIconName                M4A1_S_BornBeast
```

QV / RS 路径在 N03-B **未**做 payload SHA。Alpha / Normal / Specular TGA 与 WeaponShader CFG **没有**出现在已快照的文件路径字段里；`StandardName`/`BigIconName` 等于 CFG stem 只是 alias，不是 CFG 路径绑定。

不能从 N03-B 推出：

```text
P4-M01 PASS
TGA/CFG engine consumption contract
piece -> DTX/TGA
M4A1-黑骑士 == P5 雷神
```

当前有效 closure 边界：

```text
runtime root acquisition                 ACCEPTED
LTC wrapper/native decode                ACCEPTED
runtime Bute config parse                ACCEPTED
M4A1 config -> resource path             ACCEPTED
bf005 M4A1 exact REZ full-path binding   ACCEPTED
loose bf005 M4A1 != BornBeast payload    SCOPED_NEGATIVE_ACCEPTED
BornBeast runtime REZ payload identity   ACCEPTED
loose Bute/config BornBeast consumer     SCOPED_NEGATIVE_ACCEPTED
packed BF005 BornBeast consumer          ACCEPTED
  WeaponName M4A1-黑骑士
  -> PV LTB + PV DTX (inventory SHA)
QV / RS payload identity                 see §4.14
mesh/piece -> material binding           OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
TGA/CFG file-path on Weapon record       see §4.14
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

## 4.14 N03-C freeze

Review 接受提交：

```text
0e3c1e9130ea61cc2ed11c788cb33a1c6ba7d782  P4-M01-N03-C
P4-M01-N03-C = ACCEPTED / BUTE_MATERIAL_GRAPH_EXPANDED
```

Canonical packed Weapon 1002（`M4A1-黑骑士` / `StandardName=M4A1_S_BornBeast`）已 dump 105 keys + raw s-expression。7 个 `*FileName` 全部 REZ exact-path bind：

```text
PViewModelFileName   PLAYERVIEW/PV-M4A1_S_BornBeast.LTB     inventory SHA
PViewSkinFileName    PLAYERVIEW/PV-M4A1_S_BornBeast.DTX     inventory SHA
ModelFileName        WEAPONS/QV-M4A1_S_BornBeast.LTB        rez2 copy == local data
                                                            rez/ copy differs by 2 bytes
SkinFileName         WEAPONS/QV-M4A1_S_BornBeast.DTX        local data SHA
PreViewModelFileName WEAPONS/QV-M4A1_S_BornBeast_preview.LTB  bound, no local SHA
RenderStyleFileName  RS/NINJATRANSLUCENT.LTB (111 B)        bound
PViewRenderStyleFileName RS/PVMODELDEFAULT.LTB (119 B)      bound
```

`rez/` vs `rez2/` 的 QV LTB 字节不等；无 load-order authority，不得挑选“官方”副本。

Weapon raw 块内 inventory TGA/CFG exact path：**0**。`StandardName` / `BigIconName` = CFG stem 仅为 alias。RS LTB 与 WeaponShader CFG 无可打印 `.tga/.dtx/.cfg` 路径。

```text
Bute record binds LTB+DTX+RS only
TGA/CFG file-path on canonical Weapon     SCOPED_NEGATIVE_ACCEPTED
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
mesh/piece -> material binding           OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.15 更新。

## 4.15 N03-D freeze

Review 接受提交：

```text
04e8b425b32a6db24b24acea3f4c129c2f80f38b  P4-M01-N03-D
P4-M01-N03-D = ACCEPTED / PIECE_TEXTURE_INDEX_STRUCTURAL
```

Canonical `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB`（`rez/RF016.REZ`，N03-C SHA）LZMA-alone 解压后是 Jupiter D3D 模型：

```text
LTB_Header fileType = 1 (LTB_D3D_MODEL_FILE)
LTB_Header version  = 9  (uint16 at offset 2, aligned 20-byte header)
model fileVersion   = 25
alloc.nPieces       = 11
stream nPieces      = 11
```

CF 相对 `ModelPiece::Load` 的 delta：fileVersion 25 **省略** 源码中已废弃的 min/max LOD offset 那对 uint32。后续 piece 用“下一个 uint16 名 + 合理 nLODs”扫描接上，不是完整 `CDIModelDrawable::Load`。

11 个 piece 全部 `nNumTextures = 0`。`m_iTextures[4]` 仍按 Jupiter 固定数组写出（手/QV `[0,1,0,1]`，枪身 `[0,1,2,1]`），**不是** DTX/TGA 路径。可见 PV 皮肤仍来自 Bute `PViewSkinFileName`。

QV LTB（`rez2` 副本）1 piece，同样 `nNumTextures=0`。

```text
LTB piece names + nPieces              STRUCTURALLY_VERIFIED
LTB extra texture filenames            SCOPED_NEGATIVE (nNumTextures=0)
index -> DTX/TGA path                  OPEN_UNRESOLVED
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
Jupiter LTB piece table on PV model      ACCEPTED
LTB extra texture filenames              SCOPED_NEGATIVE_ACCEPTED
index -> DTX/TGA path                    OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.16 更新。

## 4.16 N03-E freeze

Review 接受提交：

```text
043935f4ac948bcf30d6fa5d68371190569ac298  P4-M01-N03-E
P4-M01-N03-E = ACCEPTED / RENDERSTYLE_STRUCTURAL
```

`RS/NINJATRANSLUCENT.LTB` 与 `RS/PVMODELDEFAULT.LTB`（`rez/rf002.rez`）LZMA-alone 解压后是 Jupiter renderstyle：

```text
LTB_Header fileType = 5 (LTB_D3D_RENDERSTYLE_FILE)
LTB_Header version  = 3 (RENDERSTYLE_D3D_VERSION, uint16 at offset 2)
iRenStyleCnt        = 1
iRenderPasses       = 1
```

CF delta：byte 1 of the 20-byte aligned header is non-zero（model LTB 该位为 0）。

两文件均为单 pass：

```text
stage 0 TextureParam = RENDERSTYLE_USE_TEXTURE1
stage 1..3           = RENDERSTYLE_NOTEXTURE
BlendMode            = BLEND_MOD_SRCALPHA
```

解压体内无 `.cfg` / `.fx` / `.tga` / `.dtx` / `WeaponShader` 字符串。`USE_TEXTURE1` 与 Bute 单张 `PViewSkinFileName` DTX 一致；这两条共用 RS **不能** 选择 BornBeast TGA/CFG。

```text
shared RS samples TEXTURE1 only           STRUCTURALLY_VERIFIED
RS body names TGA/CFG                     SCOPED_NEGATIVE
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
Jupiter LTB piece table on PV model      ACCEPTED
LTB extra texture filenames              SCOPED_NEGATIVE_ACCEPTED
shared RS TEXTURE1-only                  ACCEPTED
RS body TGA/CFG strings                  SCOPED_NEGATIVE_ACCEPTED
index -> DTX/TGA path                    OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.17 更新。

## 4.17 N03-F freeze

Review 接受提交：

```text
62bcce21aa2f808a230c040c58802a999f645295  P4-M01-N03-F
P4-M01-N03-F = ACCEPTED / CANDIDATE_ONLY
```

packed `Butes/BF005.LTC` 全部 8205 条记录：

```text
exact WeaponShader/M4A1_S_BornBeast.CFG     0
exact Alpha/Normal/Specular TGA paths       0
path segment WeaponShader/ or AlphaMap/     0
path segment SpecularMap/                   32 (other weapons only)
```

后期武器有 `SpecularMapName` → `ModelTextures\SpecularMap\*.dtx`（DTX，不是 TGA）。黑骑士没有该字段，也没有 `AlphaMapName` / `WeaponShader*`。四份 inventory 文件仍在 `rf017.rez`（存在 ≠ consumer）。

公开社区没有把 2013 年 WeaponShader CFG + Alpha/Normal TGA 的 **runtime 路径消费** 做成可审计 closure。已有成功仅限于：REZ/LTB/DTX 提取、OBJ/SMD 移植、CLIENTFX 特效、以及 Bute `SpecularMapName` 双贴图时代。

当前有效 closure 边界：

```text
packed BF005 exact TGA/CFG paths             SCOPED_NEGATIVE_ACCEPTED
SpecularMapName on later weapons (.dtx)      OBSERVED (not 黑骑士)
WeaponShader CFG runtime bind                OPEN_UNRESOLVED
P4-M01                                       INCOMPLETE
```

## 4.18 N03-G freeze

Review 接受提交：

```text
8386de1a852b0b726504ca7ca32b21def741e710  P4-M01-N03-G
P4-M01-N03-G = ACCEPTED / SCOPED_NEGATIVE
```

packed BF005 含 `LightCorrectionLegacyShader` / `SpecularMapName*` / `SpecularPower` 的记录 49 条：

```text
LightCorrectionLegacyShader values     18, all integer `1`
exact WeaponShader/*.CFG stem match    0
SpecularMapName                        SpecularMap\*.dtx only (later weapons)
M4A1-黑骑士 / M4A1_S_BornBeast         不在 dump 中（字段缺失）
```

`LightCorrectionLegacyShader` 是数值 flag，不是 CFG 名或路径。缺字段不是 StandardName 约定的证明。

当前有效 closure 边界：

```text
packed BF005 exact TGA/CFG paths             SCOPED_NEGATIVE_ACCEPTED
LightCorrectionLegacyShader                  SCOPED_NEGATIVE_ACCEPTED (int 1)
SpecularMapName on later weapons (.dtx)      OBSERVED (not 黑骑士)
WeaponShader CFG runtime bind                OPEN_UNRESOLVED
QV/PV DTX pixel role                         see N03-H
BornBeast native material closure            OPEN_UNRESOLVED
P4-M01                                       INCOMPLETE
```

## 4.19 N03-H freeze

> 2026-09-12 Review 收窄：保留下述实验与 scoped negative；撤回将 size-fit 视觉分类视为真实 DTX/shader 语义的表述。审计依据见 §4.26。

Review 接受提交：

```text
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  P4-M01-N03-H
P4-M01-N03-H = ACCEPTED / SCOPED_NEGATIVE
```

```text
repo standard Jupiter decoder       0/16 weapon DTX
BornBeast *DTX size classes          524452 / 32932 / empty only
524452 guessed-layout preview       visually scalar_or_energy
actual codec / shader role          OPEN_UNRESOLVED
QV 32932 size-fit                    not a gun atlas
```

用户已授权后续 PE **静态** strings/xref。不附加调试器，不提交 CF binary。

当前有效 closure 边界：

```text
native gun-atlas via tested decodes  SCOPED_NEGATIVE_ACCEPTED
native albedo existence / codec      OPEN_UNRESOLVED
WeaponShader CFG runtime bind        OPEN_UNRESOLVED (N04 PE)
P4-M01                               INCOMPLETE
```

## 4.20 N04-A freeze

Review 接受提交：

```text
d770a0a2c46a3c02f910fb28034635adac95b458  P4-M01-N04-A
P4-M01-N04-A = ACCEPTED / FORMAT_STRING_HIT
```

```text
CShell_x64.dll   modeltextures\SpecularMap\%s
crossfire.exe    MODELTEXTURES\Shader\WeaponShader\
CShell Bute keys PViewSkinFileName / SpecularMapName / LightCorrectionLegacyShader
WeaponShader\%s.CFG                  NOT found
M4A1_S_BornBeast token               CLIENTFX particle, not material bind
crossfirebase.dll                    packed .tvm0, 0 token
```

当前有效 closure 边界：

```text
SpecularMap path sprintf             OBSERVED in CShell
WeaponShader directory prefix        OBSERVED in crossfire.exe
code xref / consumer function        OPEN (N04-B)
P4-M01                               INCOMPLETE
```

## 4.21 N04-B freeze

Review 接受提交：

```text
ca8c2209541bb60f7b8cc6b7cfb4cca4715475f2  P4-M01-N04-B
P4-M01-N04-B = ACCEPTED / XREF_FOUND_UNRELATED
```

```text
CShell_x64.dll  modeltextures\SpecularMap\%s   12 LEA
                nearby: modeltextures\playerview\
                not near Bute field names
crossfire.exe   WeaponShader\ prefix           0 RIP xref (packed .std)
```

这是后期 SpecularMap `.dtx` 拼接，不是黑骑士 TGA/CFG。

当前有效 closure 边界：

```text
SpecularMap\%s code xref             STRUCTURALLY_VERIFIED (later-era .dtx)
WeaponShader CFG code consumer       OPEN (packed exe, 0 xref)
P4-M01                               INCOMPLETE
```

## 4.22 N04-C freeze

Review 接受提交：

```text
ee092c317e3cbd42fedd130f864d022b270ab0bd  P4-M01-N04-C
P4-M01-N04-C = ACCEPTED / FXO_NAMES_GENERIC
```

```text
playerviewmesh.fxo   D3D9 effect, not DXBC
samplers             Diffuse/Specular/Normal/Alpha/Overlay/Mask/Noise
techniques           tPlayerViewMesh / tPlayerViewMeshEmsv
WeaponShader/CFG/TGA paths           none
```

用户已授权 packed `crossfire.exe` **额外静态**（不脱壳、不附加进程）。

当前有效 closure 边界：

```text
FXO sampler slots                    OBSERVED
WeaponShader CFG code consumer       OPEN (N04-D packed exe static)
P4-M01                               INCOMPLETE
```

## 4.23 N04-D freeze

Review 接受提交：

```text
d36bde10d3611c862fa49843cb28854fb4b75694  P4-M01-N04-D
P4-M01-N04-D = ACCEPTED / STRING_ISLAND_ONLY
```

```text
x64/crossfire.exe     stub, sole import crossfireBase.dll
WeaponShader island   dir prefix + adjacent .cfg, 0 xref
```

用户已授权 `.tvm0` 静态 + 若进程已运行则模块 dump。不启动游戏，不对抗 ACE。

当前有效 closure 边界：

```text
WeaponShader CFG code consumer       OPEN (N04-E)
P4-M01                               INCOMPLETE
```

## 4.24 N04-E freeze

Review 接受提交：

```text
be3edd98f236ef3263b3f37af0d4e3809753c0b2  P4-M01-N04-E
P4-M01-N04-E = ACCEPTED / STATIC_ONLY_NO_PROCESS
```

磁盘 `crossfirebase.dll` / `crossfire_x64base.dll` 为 `.tvm0`，0 WeaponShader token。当时无进程。

## 4.25 N04-F freeze

Review 接受提交：

```text
729c3a3dd8d31ccbc2fc2503c386b6d9a3fdbef0  P4-M01-N04-F
P4-M01-N04-F = ACCEPTED / DUMP_ACCESS_DENIED
```

```text
PID 33100 = D:\Program Files\CF(2)\x64\crossfire.exe
PROCESS_QUERY_LIMITED_INFORMATION  ok
PROCESS_VM_READ / SNAPMODULE       last_error 5
no dump files
```

当前有效 closure 边界：

```text
native gun-atlas via tested decodes  SCOPED_NEGATIVE (scope clarified in §4.26)
SpecularMap\%s (later-era .dtx)      STRUCTURALLY_VERIFIED in CShell
WeaponShader CFG code consumer       BLOCKED (packed .tvm0 + ACE denies VM_READ)
P4-M01                               INCOMPLETE
```

活状态以 **§0** 为准。

---

## 4.26 2026-09-12 Planner 证据边界审计

本节冻结的是代码与证据的适用范围修正，不是新的 decode / native PASS。此次没有重跑 N03-H，也没有更改其历史 report、JSON、预览或本地用户修改。

1. N03-H 的 `official_decode()` 实际调用的是**本仓库** `CFRezManager --decode-image`，不是 CF 官方解码器。0/16 失败只能说明该实现未支持这些输入；所有目标都失败的集合不能充当正确性阳性对照。
2. `n03h_dtx_container_decode.py` 的 `layout_candidates()` 使用固定尺寸列表，`brute_decode()` 只执行排序后的 `[:limit]`（默认 8）。例如列表未含 `1024×512` / `1024×1024`，没有穷尽同容量的 BC/RGB 组合。`size_family()` 又直接把 524452 命名为 `pv_bgr24_512x256_mip`，这是假设标签，不是解析出的 header。纠正方法是建立格式证据，不是把盲试范围无限扩大。
3. 原 N03-H 报告末尾本来就限定为“按现有解码”，并明确 QV codec / trailer 语义未闭合。§0 原先写“PV 是能量层、没有 512×512 原生枪身图”超出该证据，现收窄为 **tested decode negative / actual codec open**。R1 测得的字节相位、文件体积、size residue 仍有效，但像素尺寸、mip、能量层/LUT 等解释不能升级。
4. N03-A 已证明若干 REZ entry raw SHA 与 loose SHA 相等；这排除了这些样本在那次复制中被改变，不能单独证明 entry 就是 runtime 最终使用的资源或已经是可直接解码表示。N03-C 的实际 Bute path binding 仍然有效，必须与 codec / override resolution 分开。
5. N04-C 报告明确未反编译指令流；它已观测到 D3D9 effect/槽名，但尚未使用 D3DX effect API 分析公式。因此“没有路径字符串”不能关闭离线 shader 语义路线。具体技术可行性来源见 §0.4；是否兼容该 FXO 仍待下一轮实验。

此次只读补充测量（有符号 little-endian int32；PV/QV exact path 见 N03-H）：

| 样本 | SHA256 | offset 4 | offset 8 | 对 RezExtract 换位规则的结论 |
|---|---|---:|---:|---|
| BornBeast PV DTX | `c419a5fb164db6085878ff2efe21d318a85186b4e3c1fd6baba920311f6ea1d9` | 460783386 | -14977025 | 两处都不是 -2/-3/-5；单纯互换不能恢复合法 version |
| BornBeast QV DTX | `ea99c7101708b6dc04e3ab97f232f683f8b996a68e2e5b5fc1167c6cd08c0f7a` | -15794177 | -61697 | 同上 |

这些是 `OBSERVED / STRUCTURALLY_VERIFIED` 的窄结论；**未找到可以直接恢复当前样本的新算法**。A 的价值是定位实际失败层，B 的价值是打开未做过的 shader 指令分析；都不能保证最终恢复。停用的仍是 N04 进程读取路线，P4-M01 离线研究不再整体 STOP。

---

## P5-T01 — Official reference

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
Target = M4A1-雷神
```

Ground truth：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

## Legacy pre-scan

历史 commit：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

保留统计：

```text
data inventory       165082 files
recalled candidates    2856
LTB candidates         1281
canonical inspected     441
```

旧 score 只表示召回优先级，不表示 identity confidence。

## P5-T02

依赖 P4-M01 native material method。

恢复后 pipeline：

```text
validated material method
-> Transformers family inventory
-> Transformers-specific DTX/TGA/CFG revalidation
-> material binding
-> native finalist render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

`USER_VISUAL_MATCH_CONFIRMED` 仍不等于最终 `IDENTITY_CONFIRMED`。

## P5-T03

建立最终 Resource Graph：

```text
PLAYERVIEW LTB
-> texture/material/shader resources
-> world/QV
-> audio
-> animation/config
```

记录 path / SHA / size / relation / source / confidence。

## P5-T04

最终 Review 输出：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才进入 P6。

---

# 6. P6 — Final replacement / release

在最终 identity 和 native material closure 都成立后：

```text
final assets
-> clean build
-> validation
-> package
-> deploy
-> release-quality runtime verification
```

---

# 7. P7 — Enhancement

不阻塞前述 closure：

```text
visible Inspect
hand / finger IK
Blender retarget / penetration avoidance
CF original animation
CF original sound
world model / extra polish
```

---

# 8. Evidence 等级约定

| Grade | 含义 |
|---|---|
| `OBSERVED` | 当前样本直接观测 |
| `STRUCTURALLY_VERIFIED` | 格式/二进制结构机械验证 |
| `VERIFIED_CORPUS_STATISTIC` | 在明确 corpus/scope 内可复现统计 |
| `DIFFERENTIAL_SUPPORTED` | 多样本差分支持 |
| `STRONG_HYPOTHESIS` | 强线索但仍有替代解释 |
| `HYPOTHESIS` | 待验证解释 |
| `TOOL_BEHAVIOR` | 本仓库工具行为，不等于原 CF runtime |
| `EXTERNAL_TOOL_BEHAVIOR` | 外部工具声明/行为，只作参考或 positive control |
| `REFERENCE_IMPLEMENTATION` | 公开 engine/reference source 的标准实现，不自动等于当前 CF variant |
| `SOURCE1_DESIGN_CANDIDATE` | Source 1 实现候选，不等于 CF 原语义 |
| `NEGATIVE_RESULT_SCOPED` | 仅在声明范围内成立的 negative |
| `OPEN_UNRESOLVED` | 当前未闭合 |
| `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` | 缺 engine consumer 新输入 |

禁止把 filename convention、视觉相似、单一统计、reference implementation、external tool behavior 或 hypothesis 直接升级为当前 CF runtime verified fact。

---

# 9. 关键 Evidence / Checkpoint 索引

## P4

```text
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
work/m4a1_s_bornbeast/p4_prototype_01/
```

## P4-M01 / N01 / N02 / N03

```text
work/m4a1_s_bornbeast/p4_m01_native_material/
work/m4a1_s_bornbeast/p4_m01_native_material/n01/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03a_bornbeast_consumer/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03b_rez_packed_config/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03c_material_graph/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03d_ltb_piece_index/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03e_renderstyle_ltb/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03f_shader_alphamap_lookup/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03g_legacy_shader_fields/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03h_dtx_container_decode/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04a_pe_string_hits/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04b_pe_xref/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04c_playerviewmesh_fxo/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04d_packed_crossfire_static/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04e_vm_dump/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04f_process_dump/
```

## External reference implementation / positive control

```text
https://github.com/no-lith/Jupiter
https://github.com/jsj2008/lithtech
https://github.com/iQuitt/Vortigaunt
https://github.com/bxclip/Tool-Crossfire
```

## P5

```text
work/p5_leishen/t01_reference/
work/p5_leishen/t01/
work/p5_leishen/t02/
```

关键历史提交：

```text
10aa99b770e575300ca3c28324ef3de3d5b70c6b  P4 frozen baseline
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d  RV-04 evidence
632ede449578f688cea7e6b5f40cbf03700aaaa5  P4-M01 initial exploration
0dc5793b6e47cb20da9e44aebcec2195194bd6f2  R1 narrow correction
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19  N01 Phase-0 cleanup
69c03d8769db2107cd94cae11accc750716466ae  scanner/lineage repair
ea11ba143d859193213f24ab92248ff8a576b135  runtime-consumer bounded search
46fcacebbc631fc05e0d491470b5e5482bca4533  evidence cleanup
95b6bb363a5f00daf01193f53e2a27cff9cea3f8  provenance/closure cleanup
65292c742d545459974c56aec494d1d9c44039a8  final config-scope guard
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2  P5 legacy pre-scan
a561924a9c0795932f328de929bee510f6e2719a  N02-A runtime root + artifact inventory
4d7c8b64d44c7d1848f1abb5182f511e5a91107f  N02-B-R1 wrapper + native LTC decode accepted
2a4054dba6cc03bedb43201aa89692c6e0a36e88  N02-C M4A1 runtime config binding accepted
be1b150b0cc4e67e4861779079887f1cf243d9a1  N02-D REVIEW_REWORK_REQUIRED (superseded by D-R1)
2f94db91099814523d9137f2c67f3ebfed7de869  N02-E REVIEW_REWORK_REQUIRED (superseded by E-R2)
f468e96f2d956ee82f69f8372c9c7c36423897ec  N02-D-R1 path-aware REZ binding accepted
c3e8872369aad29285cbf4ddb4a821a66eb127ba  N02-D-R2 review accepted
dc3ac1b69843141b54b2ae97b868aa4a7a242d01  N02-E-R1 LTB piece table absent
2e0c750624832e28a5292a488b4bad81b3934c15  N02-E-R2 bf005 != BornBeast payload
23e275a4be0eed8fd90132095ed0c283b36a39d9  N03-A BornBeast REZ payload identity, loose-config miss
f839bdb2f572ad5269a263a62ed2b3e5f87cd947  N03-B packed BF005 M4A1-黑骑士 consumer
0e3c1e9130ea61cc2ed11c788cb33a1c6ba7d782  N03-C canonical 黑骑士 FileName graph
04e8b425b32a6db24b24acea3f4c129c2f80f38b  N03-D PV LTB Jupiter piece table, nNumTextures=0
043935f4ac948bcf30d6fa5d68371190569ac298  N03-E shared RS TEXTURE1-only, no TGA/CFG strings
62bcce21aa2f808a230c040c58802a999f645295  N03-F packed BF005 no WeaponShader/AlphaMap paths
8386de1a852b0b726504ca7ca32b21def741e710  N03-G LightCorrectionLegacyShader is int 1, SCOPED_NEGATIVE
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  N03-H tested-decode negative (scope corrected in §4.26)
d770a0a2c46a3c02f910fb28034635adac95b458  N04-A CShell SpecularMap\%s; WeaponShader dir prefix
ca8c2209541bb60f7b8cc6b7cfb4cca4715475f2  N04-B CShell LEAs SpecularMap\%s; WeaponShader 0 xref
ee092c317e3cbd42fedd130f864d022b270ab0bd  N04-C playerviewmesh.fxo sampler slots, no paths
d36bde10d3611c862fa49843cb28854fb4b75694  N04-D packed crossfire.exe stub; WeaponShader island only
be3edd98f236ef3263b3f37af0d4e3809753c0b2  N04-E crossfirebase.dll .tvm0; no CF process
729c3a3dd8d31ccbc2fc2503c386b6d9a3fdbef0  N04-F OpenProcess VM_READ denied (error 5)
```

---

# 10. 文档职责

```text
README.md  项目介绍、角色分工、阅读入口
AGENTS.md  只规定 Git 操作
plan.md    本文件：§0 当前状态/当前任务 + 长期 pipeline + 冻结事实 + Gate
task.md    短指针，指向 plan.md §0（不再单独维护执行单）
```

领导/规划 Agent 每轮 Review 后更新 `plan.md` §0（当前状态与下一任务）。冻结事实写入对应 §4.x。Executor 只执行 §0.2 里的 ACTIVE 任务；§0.2 为 NONE 时 STOP。
