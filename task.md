# task.md — 当前执行任务

> 本文件只描述 **一轮可独立 Review 的当前任务**。  
> Executor 完成本文件后必须提交 evidence 并停止；由领导/Review Agent 决定哪些结果冻结进 `plan.md`，再重写下一轮 `task.md`。  
> 长期 pipeline 与冻结事实看 [`plan.md`](plan.md)。Git 操作看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 当前任务

```text
Task ID: P4-M01-N02-B
Title: Existing LTC Decoder Validation & Bute Semantic Correlation
State: ACTIVE
Parent: P4-M01-N02 Runtime Artifact Acquisition / Static Triage
Depends on: P4-M01-N02-A ACCEPTED / COMPLETE
```

目标：**不要从零逆向 LTC。先验证仓库现有 `LithTechLtcNativeDecoder` 能否稳定解码真实 `rez/Butes/*.ltc`，再参考公开 Jupiter Bute/LTA 实现解析 decoded semantics，并与 BornBeast / WeaponShader / model-material resources 做结构化 correlation。**

本轮只解决：

```text
existing decoder validation
-> decoded Bute/LTA semantics
-> target/resource correlation
-> direct config binding evidence OR bounded negative
```

完成后必须停止并交回 Review。

---

# 2. 已冻结输入与 reference hierarchy

## 2.1 Runtime input

N02-A 已确认：

```text
trusted runtime root = D:\Program Files\CF(2)
73 x rez/Butes/*.ltc
35 x bf-prefixed .ltc within that set
rez/bf000.lta = 30,002 bytes
17 shader-bearing files
272 DLL
27 EXE
476 REZ
```

N02-A evidence：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/root_discovery.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/artifact_inventory.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/acquisition_report.md
```

## 2.2 Existing repo implementation

仓库已有：

```text
CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs
```

该实现已经定义 deterministic LTC native decode path。

本轮第一原则：

```text
validate it first
!= assume it is correct
!= rewrite it before testing
```

## 2.3 Public reference implementations

优先参考：

```text
https://github.com/no-lith/Jupiter
  Libs/LIB-ButeMgr
  Libs/LIB-LTAMgr

https://github.com/jsj2008/lithtech
  Jupiter engine/runtime/model and related parser/consumer source
```

它们只作为标准 LithTech/Jupiter `REFERENCE_IMPLEMENTATION`；必须用当前 CF runtime sample 验证版本差异。

允许作为 positive control / differential clue：

```text
https://github.com/iQuitt/Vortigaunt
https://github.com/bxclip/Tool-Crossfire
```

外部工具声明或输出只能算 `EXTERNAL_TOOL_BEHAVIOR`，不能直接当当前 CF runtime proof；不要执行未经审计的未知 binary/rar 工具作为本轮依赖。

---

# 3. 本轮必须回答

## 3.1 Existing LTC decoder 是否适配当前 runtime

至少对以下 sample classes 验证：

```text
多个 bf*.ltc
多个非-bf rez/Butes/*.ltc
必要时不同 size / family 的边界样本
```

必须回答：

1. 当前 `LithTechLtcNativeDecoder` 成功率是多少？
2. 成功输出是否是可解释的 LTA/Bute-style structured text，而不是仅“产生字节”？
3. decoded output 是否有稳定 terminator / tag / key-value / numeric/string grammar？
4. decode 结果是否可重复，same input 是否稳定得到 same output hash？
5. 失败样本是否形成明确 variant cluster，而不是直接宣称 decoder 错误？

如果现有 decoder 大部分成功，本轮 **禁止重新发明 LTC compression parser**。

如果出现真实不兼容，必须先形成：

```text
sample path alias
SHA256
failure mode
header/bitstream differential
cluster statistics
```

再提出最小 CF-specific decoder patch。

## 3.2 Decoded Bute/LTA semantics

对成功 decode 的输出，优先按 Jupiter `LIB-ButeMgr / LIB-LTAMgr` 的 grammar/semantics 解析。

寻找但不限于：

```text
[tag]
key = value
string / number / bool / vector-like value
resource basename/path
model / texture / shader references
weapon/item/config identifiers
```

需要区分：

```text
raw decoded text
parsed field
inferred semantic role
```

不能因为 key 名看起来像材质就直接升级为 binding proof。

## 3.3 bf000.lta / bf*.ltc relationship

比较：

```text
rez/bf000.lta
vs
bf*.ltc decoded output
```

回答：

1. 是否共享同一 grammar？
2. `.lta` 是 plaintext source、index、base table、family root，还是 unrelated same-prefix file？
3. 是否存在 shared tag/key/id range？
4. 是否存在可机械证明的 parent/child、index/member 或 reference relation？

文件名相似不能算关系证明。

## 3.4 Target/resource correlation

只复用现有 N01 / manifest / report 中已经抽取的 target basename / identifier，不重新扫描整个 `data/**`。

优先目标：

```text
BornBeast
Transformers
Jewelry
BlueDiamond
WeaponShader
known DTX/TGA basenames
known LTB/model basenames
LTB post-mesh short ASCII identifiers
```

同时允许从 decoded runtime config 自身提取新的 resource basename，再与现有 inventory 做 **限定范围** lookup。

每个 match 必须记录：

```text
runtime source path alias
source SHA256
decoded output SHA256
tag / key / field / record
original offset or recoverable source context
matched resource / identifier
match type
relationship direction if expressed
confidence / evidence grade
```

---

# 4. Evidence strength rules

以下可以构成较强 evidence：

```text
structured field explicitly assigns model/texture/shader/resource
stable id maps to resource path across multiple records
parent record references child/material/texture identifier
same semantic relation repeats across different weapon families
```

以下 **不能** 单独算 binding proof：

```text
bf filename prefix
same directory
raw string co-occurrence
substring match
visual similarity
external tool says it is so
repo exporter happens to mirror a path
```

本轮目标不是强行得到 `P4-M01 PASS`，而是提升 evidence quality。

---

# 5. 推荐实现

优先新增或完善：

```text
scripts/material_recovery/n02_butes_config_triage.py
```

实现顺序建议：

```text
1. enumerate runtime .ltc/.lta samples
2. call/port/reuse existing LithTechLtcNativeDecoder logic
3. record decode success/failure + hashes
4. classify decoded syntax
5. parse Bute/LTA tags/keys/values deterministically
6. correlate only against scoped known resource identifiers
7. emit evidence report
```

可以直接在 Python 中复现现有 C# decoder 逻辑用于批量 analysis，但必须证明与 C# implementation 对同一 sample 输出一致；不要因为方便就 silently fork 两套不同 semantics。

如确实需要修改 `CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs`，必须有真实失败样本和 regression evidence 支持，避免无证据重写。

---

# 6. 输出

建议 evidence 目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02b_butes_config/
```

至少输出：

```text
ltc_decoder_validation.json
bute_parse_inventory.json
correlation_report.json
n02b_butes_config_report.md
```

如果修改 decoder，再增加：

```text
decoder_regression.json
```

报告至少包含：

```text
sample coverage
success/failure counts
existing decoder verdict
Bute/LTA grammar verdict
bf000.lta relationship verdict
target/resource matches
binding-evidence grade
remaining blocker
```

不要提交 raw CF runtime `.ltc/.lta` 副本；仓库只保存 metadata、hash、解析字段和必要 derived evidence。

---

# 7. Completion / Handoff

完成后返回以下之一：

## A. Existing decoder + config semantics 给出直接 binding evidence

```text
RUNTIME_BUTE_BINDING_EVIDENCE_READY
```

至少给出：

```text
validated decoder method
source path alias + SHA256
decoded output hash
parsed tag/key/field context
explicit model/material/texture/shader relation
cross-family validation if available
remaining CFG/render semantic gap
```

## B. Existing decoder 有效，Bute/LTA 已解析，但没有目标 binding

```text
RUNTIME_BUTE_PARSED_NO_TARGET_BINDING
```

至少给出：

```text
decoder validation scope
Bute/LTA parsed grammar
all target correlation scope
bounded negative
next single highest-value consumer artifact
```

这时下一轮才考虑：

```text
specific PE/DLL consumer
or specific FXO/render consumer
```

不要泛泛写“反编译 EXE”。

## C. Existing decoder 与当前 CF runtime 存在真实 variant

```text
CF_LTC_VARIANT_CONFIRMED
```

必须给出：

```text
working vs failing sample clusters
SHA256
mechanical bitstream/header differential
why current decoder fails
minimal proposed variant handling
regression criteria
```

只有这种情况，下一轮才值得把 LTC format differential 本身升级为主任务。

完成后 **STOP**。不要自行继续 N02-C。

---

# 8. 本轮禁止事项

- 不从零重新逆 LTC compression，除非先证明 existing decoder 对真实 sample 不兼容；
- 不把 public Jupiter source 当当前 CF runtime 自动证明；
- 不执行未经审计的社区 converter binary/rar；
- 不执行任何 CF client/runtime binary；
- 不注入进程、不绕 anti-cheat、不做 memory dump；
- 不做宽泛 EXE/DLL decompile/xref；
- 不开始 FXO shader 反编译；
- 不解包大型 REZ 作为本轮主任务；
- 不重新扫描整个 `data/**`；
- 不上传 raw runtime binary/config 副本；
- 不把文件名、字符串共现或目录邻近当 binding proof；
- 不自行宣布 `P4-M01 = NATIVE_MATERIAL_RECOVERED`；
- 不恢复 P5-T02；
- 不修改 `plan.md`。

---

# 9. Executor 交回内容

完成后只需交回：

```text
status
commit SHA
新增/修改的 scoped files
existing LTC decoder verdict
Bute/LTA semantic parse verdict
bf000.lta <-> bf*.ltc relationship verdict
target/resource correlation verdict
direct evidence 或 bounded negative
建议下一轮唯一最高优先级 consumer target
需要领导 Review 的关键判断点
```

然后停止，等待下一轮 `task.md`。