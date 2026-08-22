# task.md — 当前执行任务

> 本文件只描述 **一轮可独立 Review 的当前任务**。  
> Executor 完成本文件后必须提交 evidence 并停止；由领导/Review Agent 决定哪些结果冻结进 `plan.md`，再重写下一轮 `task.md`。  
> 长期 pipeline 与冻结事实看 [`plan.md`](plan.md)。Git 操作看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 当前任务

```text
Task ID: P4-M01-N02-B-R1
Title: CrossFire LTC Wrapper Validation & Bute Semantic Correlation
State: ACTIVE / REWORK
Parent: P4-M01-N02-B Existing LTC Decoder Validation & Bute Semantic Correlation
Reworks commit: 539ae93a760fec0722e787fcb79365d1bc633e69
Depends on: P4-M01-N02-A ACCEPTED / COMPLETE
```

## Review correction

上一轮 `539ae93...` 的样本枚举和 raw magic 统计有价值，但最终结论 **未被 Review 接受**。

上一轮有效观测：

```text
73 x rez/Butes/*.ltc
73 / 73 first-4-byte magic = 54 83 B2 E1
35 x bf-prefixed .ltc
rez/bf000.lta first bytes differ from bf*.ltc
```

上一轮 **不得作为冻结事实继续使用** 的结论：

```text
CF_LTC_VARIANT_CONFIRMED
"LithTechLtcNativeDecoder is incompatible with current CF runtime"
"crossfireBase.dll / server.dll xref is the only next path"
```

原因：上一轮直接把 raw CF `.ltc` 喂给了底层 `LithTechLtcNativeDecoder`，但仓库真实 CF-specific 调用链是：

```text
CFRezManager/Decoders/CrossFire/CrossFireLtcDecoder.cs
  -> detect CrossFire magic 54 83 B2 E1
  -> TryUnlockCrossFirePayload(...)
  -> 16-byte repeating XOR
  -> LithTechLtcNativeDecoder.TryDecode(...)
  -> decoded LTA/Bute-style text
```

因此本轮必须验证 **完整 wrapper path**，不能再次只验证底层 decoder。

---

# 2. 已知 repo implementation

必须先阅读并按实际 caller chain 理解：

```text
CFRezManager/Decoders/CrossFire/CrossFireLtcDecoder.cs
CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs
```

当前 repo 中已存在的 CF wrapper constants：

```text
CrossFireLtcMagic =
54 83 B2 E1

CrossFireLtcXorKey =
54 83 B2 E1
10 3F 6E 9D
CC FB 2A 59
88 B7 E6 15
```

`TryUnlockCrossFirePayload` 对整个 payload 使用 16-byte repeating XOR。

注意：

```text
54 83 B2 E1
XOR
54 83 B2 E1
=
00 00 00 00
```

这正是底层 `LithTechLtcNativeDecoder` 所要求的 4-byte zero header，因此必须机械验证这一调用链是否在真实 runtime samples 上成立。

不要因为源码里存在该实现就假定它正确；但也不要绕过它重新从 raw bytes 下结论。

---

# 3. Runtime scope

只使用 N02-A 已确认的 trusted runtime root：

```text
D:\Program Files\CF(2)
```

本轮主 scope：

```text
73 x rez/Butes/*.ltc
```

其中已知：

```text
73 / 73 raw magic = 54 83 B2 E1
35 x bf-prefixed .ltc
```

`rez/bf000.lta` 可以作为后续语义比较 control，但 **不要把 `.lta` 当 `.ltc` 输入喂给 LTC decoder**。

---

# 4. 本轮必须回答

## 4.1 CrossFire wrapper 是否真实适配 73 个 runtime LTC

对全部 73 个 `rez/Butes/*.ltc`：

1. 验证 raw first-4 bytes 是否仍为 `54 83 B2 E1`；
2. 使用 repo 中现有 16-byte repeating XOR 做 unlock；
3. 记录 unlocked first 16/32 bytes；
4. 统计多少样本 unlock 后 first-4 bytes 为 `00 00 00 00`；
5. 再把 **unlocked payload** 送入 `LithTechLtcNativeDecoder`；
6. 记录 decode success/failure、failure mode、decoded size、decoded SHA256；
7. same input 重复运行应得到相同 decoded SHA256。

必须明确区分：

```text
raw CF wrapper compatibility
unlocked standard-LTC compatibility
native decode compatibility
text/Bute semantic validity
```

不能再把 raw-header mismatch 直接叫作 native decoder incompatibility。

## 4.2 验证 CrossFireLtcDecoder 的实际行为

优先复用/调用现有 C# implementation；若为了批量分析在 Python 中复现：

```text
CrossFire magic detection
16-byte repeating XOR
LithTech native decode
```

必须证明 Python 与 C# 对同一 sample 的关键中间结果一致：

```text
unlocked SHA256
unlocked first bytes
decoded SHA256 / failure mode
```

不要 silent fork 两套 semantics。

## 4.3 Decoded Bute/LTA semantics

对 native decode 成功且文本可解释的样本，参考：

```text
https://github.com/no-lith/Jupiter
  Libs/LIB-ButeMgr
  Libs/LIB-LTAMgr

https://github.com/jsj2008/lithtech
```

解析至少包括：

```text
tag / section
key = value
string / numeric / bool / vector-like values
resource path / basename
model / texture / shader / material-like references
weapon/item/config identifiers
```

必须区分 evidence：

```text
RAW_DECODED_TEXT
PARSED_FIELD
INFERRED_SEMANTIC_ROLE
DIRECT_BINDING_RELATION
```

字段名看起来像材质，不等于 binding proof。

## 4.4 bf000.lta 与 bf*.ltc

只有在 bf*.ltc 成功 decode 后，再比较：

```text
rez/bf000.lta
vs
bf*.ltc decoded outputs
```

回答：

1. 是否共享相同 grammar / tag / key style；
2. 是否存在 shared ids / range / record naming；
3. 是否存在可机械证明的 parent/index/member/reference relation；
4. 或仅有 `bf` filename-prefix correlation。

raw wire format 不同不是语义无关证明；filename 相似也不是关系证明。

## 4.5 Target/resource correlation

只复用现有 N01 / R1 / manifests / reports 中已经抽取的 scope；不要重扫整个 `data/**`。

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

如果 decoded config 自身给出新的 resource basename，可在 **限定范围** 内与已有 runtime inventory 做 lookup。

每个命中至少记录：

```text
runtime source path alias
raw SHA256
unlocked SHA256
decoded SHA256
tag / key / field / record
matched resource / identifier
relationship direction if explicitly expressed
match type
confidence / evidence grade
```

只有结构中明确表达资源关系时，才能升级为 binding evidence。

---

# 5. 推荐实现

优先修改/重用：

```text
scripts/material_recovery/n02_butes_config_triage.py
```

推荐流水线：

```text
1. enumerate only rez/Butes/*.ltc
2. verify raw magic cluster
3. apply existing CrossFire 16-byte XOR wrapper
4. verify unlocked header cluster
5. run existing LithTech native decoder semantics
6. classify decode output
7. parse Bute/LTA semantics
8. scoped target/resource correlation
9. emit audit evidence
```

如果现有 `CrossFireLtcDecoder.cs` 本身需要 patch，必须基于真实失败 cluster，并附 regression evidence；不要因为单个异常样本就重写整个 decoder。

---

# 6. 输出

继续使用：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02b_butes_config/
```

至少输出：

```text
wrapper_validation.json
ltc_decoder_validation.json
bute_parse_inventory.json
correlation_report.json
n02b_r1_wrapper_report.md
```

`wrapper_validation.json` 至少包含：

```text
sample_count
raw_magic_counts
unlock_success_count
unlocked_zero_header_count
unlocked_magic/header clusters
raw/unlocked SHA256 mapping
```

`ltc_decoder_validation.json` 至少包含：

```text
native_decode_success_count
failure_count
failure clusters
decoded SHA256
repeatability result
```

不要提交 raw CF runtime `.ltc/.lta` 副本。

---

# 7. Completion / Handoff

完成后只允许以下状态之一。

## A. Wrapper + native decoder 跑通，并找到直接 binding evidence

```text
RUNTIME_BUTE_BINDING_EVIDENCE_READY
```

必须给出：

```text
validated wrapper method
validated native decode method
source/raw/unlocked/decoded hashes
parsed field context
explicit model/material/texture/shader relationship
remaining CFG/render semantic gap
```

## B. Wrapper + native decoder 跑通，但没有目标 binding

```text
RUNTIME_BUTE_PARSED_NO_TARGET_BINDING
```

必须给出：

```text
73-sample wrapper/decode coverage
Bute/LTA grammar coverage
bounded target correlation negative
single next highest-value consumer target
```

只有这时下一轮才考虑具体 PE/DLL/FXO consumer。

## C. Wrapper unlock 成功，但 native decoder 仍存在真实 incompatibility

```text
POST_UNLOCK_LTC_VARIANT_EVIDENCE_READY
```

必须给出：

```text
raw 54 83 B2 E1 -> XOR unlock evidence
unlocked header / cluster statistics
working vs failing sample clusters if any
mechanical post-unlock bitstream differential
why existing native decoder fails after correct wrapper
minimal next investigation target
```

注意：只有 **正确执行 wrapper 后仍失败**，才允许讨论真正的 LTC variant。

## D. Repo wrapper 本身与真实 runtime 不匹配

```text
CF_LTC_WRAPPER_MISMATCH_EVIDENCE_READY
```

必须给出：

```text
73-sample raw magic evidence
repo wrapper transform output
why expected zero header / downstream contract fails
mechanical mismatch evidence
minimal proposed wrapper correction
```

完成后 **STOP**。不要自行继续 N02-C。

---

# 8. 本轮禁止事项

- 不把上一轮 `CF_LTC_VARIANT_CONFIRMED` 当已接受事实；
- 不把“必须逆 crossfireBase.dll/server.dll”当已批准路线；
- 不直接将 raw `54 83 B2 E1` LTC 喂给底层 native decoder 后据此下结论；
- 不把 `.lta` 当 `.ltc` decoder 输入；
- 不做任何 DLL/EXE decompile、strings/xref 作为本轮主任务；
- 不开始 FXO shader reverse；
- 不执行 CF client/runtime binary；
- 不注入进程、不绕 anti-cheat、不做 memory dump；
- 不执行未经审计的社区 converter binary/rar；
- 不解包大型 REZ 作为本轮主任务；
- 不重新扫描整个 `data/**`；
- 不上传 raw runtime binary/config；
- 不把 filename/string coexistence 当 binding proof；
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
73-sample raw magic verdict
CrossFire XOR wrapper verdict
post-unlock header verdict
LithTech native decoder verdict
Bute/LTA semantic parse verdict
bf000.lta <-> decoded bf*.ltc relationship verdict
target/resource correlation verdict
direct evidence 或 bounded negative
建议下一轮唯一最高优先级 target
需要领导 Review 的关键判断点
```

然后停止，等待下一轮 `task.md`。
