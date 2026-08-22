# P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md — Engine Material Consumer & Binding Closure

> task_id: `P4-M01-N01`
>
> parent_task: `P4-M01`
>
> predecessor: `P4-M01-R1`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / ENGINE_BINDING_INVESTIGATION**

本任务不是 R2，也不是再次纠错 R1。R1 已完成核心 evidence correction；本任务把剩余 minor consistency cleanup 作为 Phase 0，然后正式进入 P4-M01 的下一条 substantive lane：**寻找 CF weapon material 的真实 engine/resource consumer，闭合 mesh/piece → material/texture-set → CFG/render semantics。**

P4 baseline 继续 `PASS / FROZEN`；P5-T02 继续 `PAUSED_BY_P4_M01`。

---

## 1. 输入基线

当前已接受并应复用：

```text
P4 baseline                       PASS / FROZEN
R1-D TGA formal repair            ACCEPT / STRUCTURAL
DTX no LithTech header            VERIFIED_STRUCTURAL
DTX not LZMA                      VERIFIED_STRUCTURAL
DTX 3-byte periodic payload       VERIFIED_STRUCTURAL
DTX 1024 stride / single image    STRONG_HYPOTHESIS
DTX channel order                 OPEN
DTX terminal 2212-byte semantics  OPEN
CFG 237/237 single mod-3 phase    VERIFIED_STRUCTURAL
CFG record boundary               OPEN
CFG semantic consumer             OPEN
ArmModel text material format     VERIFIED_STRUCTURAL
weapon LTB short field semantics  PROVISIONAL
weapon slot -> texture set        OPEN
H2 pixel-index sampling fix       ACCEPT / DIAGNOSTIC_ONLY
```

关键执行提交：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f
0dc5793b6e47cb20da9e44aebcec2195194bd6f2
```

R1 历史错误不删除；新 evidence 必须保持 supersedes/provenance 链。

---

## 2. Phase 0 — R1 final consistency cleanup（必须先做，但不得扩张成新一轮 R1）

只处理以下局部问题，然后立即进入 Phase 1：

### 0.1 CFG phase-origin accounting formula

当前 sample extraction `range(ph, n, 3)` 已正确得到：

```text
BornBeast     164
Transformers  169
Jewelry       214
```

但 `accounting_phase_origin.identity` 不能写成：

```text
n = first_offset + sample_count*3 + trailing
```

因为 sample 是相隔 3 bytes 的**单字节位置**，不是 `sample_count` 个 3-byte record。

应使用等价且数学自洽的 span accounting，例如：

```text
n = first_offset + (sample_count - 1)*3 + 1 + trailing_bytes_after_last_sample
```

或直接记录 first/last/count 而不伪造 record-size identity。

### 0.2 DTX wording/docstring

- 保留 1024 stride = `STRONG_HYPOTHESIS`；
- 不再写 `>3x margin`，除非计算值严格满足；当前 nearest distinct ~1020 的比值约 2.99x，overall runner-up 2048 约 1.62x；
- 删除/修正文档顶部遗留的 `every non-empty PV DTX` universal wording；正式结论是 `1043/1046 = 99.71% dominant statistic`。

### 0.3 shader report metadata

- `H1_base_flat` preview path 必须指向实际生成的 `h1_base_flat_r1.png`，path 与 SHA 一致；
- `H1_base_flat` 不得标 `VERIFIED_DECODE_ONLY`，因为 1024 layout/channel order 尚未完全 semantic-verified。建议：

```text
EVIDENCE_SUPPORTED_LAYOUT_HYPOTHESIS / DIAGNOSTIC_LAYER_RENDER
```

- 清理脚本顶部遗留的 `DTX=BGR24`、`CFG=stride-3 scalar strip` 等过时描述；
- TGA storage order 与 shader semantic role 必须分开描述。

### 0.4 binding docstring/scope

保留 v3 report 的 scope-limited negative；清理顶部任何仍暗示 `full local data` exhaustive negative 的旧注释。

### 0.5 Phase-0 gate

重新生成受影响 report/closure，必须满足：

```text
formula arithmetic self-consistent
path exists and SHA matches
script comments == report evidence grade
no stale universal/exact-framing wording
no open item upgraded to verified
```

**Phase 0 通过后，不等待 Chat/Sol，再继续 Phase 1。**

---

## 3. Phase 1 — 找真实 material consumer，不再盲扫 basename

核心问题：

> `ModelTextures/Shader/WeaponShader/*.CFG`、LTB post-mesh short field、DTX/TGA texture family，究竟被哪个 engine/config/resource path 关联并消费？

优先读取/复用仓库已有基础设施：

```text
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureConfigIndex.cs
CFRezManager/Decoders/LithTech/Models/LithTechTextureMappingScanner.cs
CFRezManager/Decoders/LithTech/Models/LithTechDatTextureReferenceIndex.cs
CFRezManager/Decoders/LithTech/Models/TextureReferenceResolver.cs
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureLoader.cs
CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs
CFRezManager/Decoders/Images/CfgTextDecoder.cs
CFRezManager/Decoders/Images/CfgBinaryStripDecoder.cs
```

要求不是“把这些类名写进报告”，而是沿调用/数据关系建立 `consumer_candidate_matrix.json`：

```text
candidate_consumer / resource_family
source code path or local resource path
input resource type
reference direction
raw key / offset / field / string
BornBeast hit?
Transformers/Jewelry/control hit?
evidence = direct | structural | differential | negative
status = accepted | rejected | open
reason
```

优先搜索方向：

1. 谁创建/读取 texture config/index/mapping；
2. 谁把 model/piece 名或 index 传给 texture resolver；
3. 谁引用 `Shader/WeaponShader` 或等价 shader/material family；
4. 是否存在 render-style/material table/resource table 把 weapon model 与 texture set 关联；
5. LTB 后置 short string 是否被 decoder 下游当 piece/material name，而不是先假定 texture slot。

不要因为没找到文本引用就继续无边界扫描整个 `data/**`。每次扩张扫描范围必须写清“为什么该资源类别可能是 consumer”。

输出：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
```

---

## 4. Phase 2 — Engine-format positive control → weapon differential

已知正样本：ArmModel LZMA text material CFG：

```text
[Textures]
SpecularMapName0
EnvCubeMapName0
NormalMapName0
AlphaMapName0

[Properties]
PieceIndex
```

不要直接把 ArmModel format 套到 weapon。把它作为**positive control**，比较：

```text
ArmModel piece count / PieceIndex / texture-set structure
vs
BornBeast / Transformers / Jewelry LTB mesh/piece structure
vs
WeaponShader CFG length/phase/sample structure
vs
DTX/TGA family membership
```

至少建立 same-family differential：

```text
BornBeast
Transformers
Jewelry
+ 1 个简单/传统 M4A1-S control（若本地已有可识别样本）
```

对每个样本记录：

```text
LTB mesh count
mesh names
post-mesh short field raw value + offset
geometry signature / SHA relation
DTX path/SHA/size
Alpha/Normal/Specular path/SHA/size
WeaponShader CFG path/SHA/size
CFG varying phase / sample count
any material/config/resource-table references
```

目标：找到**随 skin/material 变化而同步变化的 binding key**。只有文件名相似不算 direct binding。

输出：

```text
n01/weapon_material_differential.json
```

---

## 5. Phase 3 — WeaponShader CFG：先定位 consumer，再谈 semantic decode

R1 已证明：237/237 文件存在 single-phase mod-3 structure；这不等于已知 scalar/color record。

N01 优先级：

```text
consumer/reference evidence > binary-value curve fitting > preview appearance
```

如果找到 consumer：

- 记录调用/字段/offset；
- 解释 consumer 期待的数据类型、record stride、count、channel/parameter meaning；
- 用 BornBeast + 至少两个 control 交叉验证；
- 把 H-CFG-A/B/C 中不符合 consumer contract 的解释正式 reject。

如果暂时找不到 consumer：

- 保持 `record boundary / scalar+padding / RGB/BGR` 为 hypothesis；
- 允许做有界 differential，例如 CFG sample count 是否与 piece/material count、某 render table count、texture lookup dimension存在稳定关系；
- 禁止因为 `[0,42]` 值域“小”就单独升级 scalar semantics。

输出：

```text
n01/cfg_consumer_report.json
```

---

## 6. Phase 4 — Channel/storage semantics 分层闭合

必须分开三件事：

```text
A. storage byte order
B. map role / binding role
C. shader composition semantics
```

### TGA

TGA formal repair 已接受；下一步只确认：

- decoder/storage byte order；
- map 文件名角色是否与实际 binding 一致；
- varying channel 在 consumer 中代表什么。

### DTX

保留：

```text
3-byte periodic payload VERIFIED_STRUCTURAL
1024 stride STRONG_HYPOTHESIS
```

寻找 engine/resource consumer 对 byte order、texture role、tail packing 的解释。若没有 direct evidence，channel order/tail 可以继续 OPEN，不得为了进入 render 强行定值。

输出：

```text
n01/channel_semantics_report.json
```

---

## 7. Phase 5 — Binding/consumer closure

N01 不是要求“所有未知都必须破解”，而是要求把**真正阻塞 native material composition 的关键关系**分级清楚。

推荐 evidence 状态：

```text
OBSERVED
STRUCTURALLY_VERIFIED
DIFFERENTIAL_SUPPORTED
SEMANTICALLY_VERIFIED
PROVISIONAL
HYPOTHESIS
NEGATIVE_RESULT_SCOPED
OPEN_UNRESOLVED
```

### N01 PASS 最低条件

至少满足其一：

**Path A — direct engine/resource closure**

```text
weapon mesh/piece
-> verified material/binding key
-> verified local texture set
-> CFG/material consumer role sufficiently identified
```

或：

**Path B — strong differential closure**

没有找到单一明文 table，但多个独立 same-family/control evidence 能唯一支持：

```text
piece/material identity
-> texture family
-> CFG resource role
```

且 alternative explanations 被明确 reject。

仅有 basename convention、视觉相似、长度 fit、单一统计相关，不足以 PASS。

输出：

```text
n01/engine_binding_closure.json
```

N01 PASS 后才进入 P4-M01 的 native composition/final material closure lane；仍不得直接恢复 P5-T02，除非 Chat/Sol 最终判 `P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED`。

---

## 8. 当前执行顺序

```text
0. R1 final consistency cleanup
1. consumer call/data-path discovery
2. ArmModel positive control + weapon-family differential
3. locate/identify WeaponShader CFG consumer
4. storage/channel/binding semantics
5. engine binding closure
```

禁止退回：

```text
重新跑 TGA formal repair
重新争论 DTX header/LZMA
重新跑 DTX width scan
再把 CFG phase 当 record boundary
再用 external texture 提供 final pixels
为得到 PASS 无边界扫描 data/**
```

---

## 9. Git / data / authority

继续遵守 `AGENTS.md`：

- handoff 只认 `master`；
- `data/**` 永远 local-only；
- 不 broad stage；
- 不 force push / destructive reset/clean；
- 原始 CF assets 不上传；
- 只提交 scoped code/evidence/derived previews；
- Local Executor 不自行把 `plan.md` 改 PASS。

当前用户 visual gate 不是 blocker。先完成 technical engine/material binding closure。