# CF 武器 -> CS:GO Legacy Source 1 — 静态项目蓝图

> 本文件定义长期稳定的 **pipeline、阶段关系、Gate、已冻结事实和关键技术结论**。  
> 它不是当前任务单，不应因为每一轮执行而频繁改写。  
> 当前下一步永远看 [`task.md`](task.md)。Git 操作规则看 [`AGENTS.md`](AGENTS.md)。

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

Review 接受提交：

```text
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  P4-M01-N03-H
P4-M01-N03-H = ACCEPTED / SCOPED_NEGATIVE
```

```text
official Jupiter DTX header          0/16 weapon DTX
BornBeast *DTX size classes          524452 / 32932 / empty only
524452 family pixels                 scalar_or_energy
  including RoyalDragon SpecularMap
QV 32932 size-fit                    not a gun atlas
```

用户已授权后续 PE **静态** strings/xref。不附加调试器，不提交 CF binary。

当前有效 closure 边界：

```text
native gun-atlas DTX                 SCOPED_NEGATIVE_ACCEPTED
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
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  N03-H no native gun-atlas DTX; 524452 is energy
d770a0a2c46a3c02f910fb28034635adac95b458  N04-A CShell SpecularMap\%s; WeaponShader dir prefix
ca8c2209541bb60f7b8cc6b7cfb4cca4715475f2  N04-B CShell LEAs SpecularMap\%s; WeaponShader 0 xref
ee092c317e3cbd42fedd130f864d022b270ab0bd  N04-C playerviewmesh.fxo sampler slots, no paths
d36bde10d3611c862fa49843cb28854fb4b75694  N04-D packed crossfire.exe stub; WeaponShader island only
```

---

# 10. 文档职责

```text
README.md  项目介绍、角色分工、阅读入口
AGENTS.md  只规定 Git 操作
plan.md    本文件：长期 pipeline + 冻结事实 + Gate
task.md    当前动态任务 + 可尝试实现路径 + 验收要求
```

领导/规划 Agent 在每轮 Review 后主要更新 `task.md`；只有 pipeline、Gate 或冻结事实发生长期变化时才更新 `plan.md`。