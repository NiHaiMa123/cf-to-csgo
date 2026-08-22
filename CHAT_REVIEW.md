# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 ChatGPT 对话中的 **Chat/Sol** 使用。
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01
P4-M01-N01    ACTIVE / ENGINE_BINDING_INVESTIGATION   <- CURRENT REVIEW TARGET
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03        BLOCKED_BY_T02
P5-T04        BLOCKED_BY_T03
```

当前 Review 入口：

```text
P4_M01_TASK_SPEC.md
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md
CODEX_TASKS.md
```

R1 history：

```text
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
```

---

## 2. R1 final Review

最后一轮：

```text
0dc5793b6e47cb20da9e44aebcec2195194bd6f2
```

Chat/Sol 接受 R1 核心 correction：

```text
DTX formal header/LZMA correction
DTX whole-file 3-byte periodicity
DTX committed width scan
DTX two-varying-channel continuity
1043/1046 dominant statistic wording
TGA formal repair
CFG phase-vs-record-boundary correction
CFG 164/169/214 complete sample extraction
H2 pixel-index sampling
ArmModel material-format positive control
binding negative-scope correction
```

仍有 minor consistency：

```text
CFG phase-origin identity formula
DTX >3x/stale every wording
H1 preview path/SHA
H1 evidence class
stale BGR24/scalar/full-data comments
```

这些已转入 N01 Phase 0，不再单独维持 R1 substantive loop。

```text
P4-M01-R1 = ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01
```

---

## 3. N01 Review principle

N01 的问题不是“还能不能多扫几个文件”，而是：

> **是否找到足够强的 engine/resource evidence，把 weapon mesh/piece 与实际 local texture family、WeaponShader CFG/material consumer 关联起来。**

证据优先级：

```text
engine/resource consumer evidence
> structural binding
> same-family differential
> bounded binary hypothesis
> preview appearance
```

拒绝：

- basename convention = binding；
- 文件在相邻目录 = binding；
- 长度/count fit = semantic proof；
- `[0,42]` 值域小 = scalar verified；
- 能画成图 = texture role verified；
- external texture visual match = native semantics；
- negative scan 超出实际 scope；
- 为得到 PASS 无限扩大 blind scan。

---

## 4. 已接受 baseline，Review 时不得重复打回

除非新 counterevidence：

```text
DTX no formal LithTech header             VERIFIED_STRUCTURAL
DTX not LZMA                              VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodic payload    VERIFIED_STRUCTURAL
DTX one fixed-FF byte position            VERIFIED_STRUCTURAL
DTX 1024/no-mips                          STRONG_HYPOTHESIS
DTX 1043/1046 packing statistic           VERIFIED_CORPUS_STATISTIC
TGA formal repair                         ACCEPT / STRUCTURAL
CFG 237/237 single-phase mod-3 fact       VERIFIED_STRUCTURAL
CFG phase != record boundary              correction accepted
CFG primary sample extraction             164/169/214 accepted
H2 phase-mixing fix                       accepted
ArmModel [Textures]/PieceIndex format     VERIFIED_STRUCTURAL
weapon LTB short field exists             VERIFIED_STRUCTURAL
```

仍 open：

```text
DTX/TGA channel/binding semantics
DTX tail semantics
weapon short-field meaning
weapon piece/material -> texture set
WeaponShader CFG record boundary
WeaponShader CFG consumer/semantic
native composition
```

---

## 5. Phase 0 Review

N01 Phase 0 只验：

```text
CFG phase-origin formula arithmetic
DTX wording/docstring consistency
H1 preview path/SHA consistency
H1 evidence-class consistency
shader/binding stale comments removed
reports regenerated without evidence escalation
```

Phase 0 是 housekeeping，不应该再次消耗一整轮任务。

Executor 按 spec 可在 Phase 0 self-check 通过后直接进入 Phase 1。

---

## 6. Phase 1–4 Review

### Consumer discovery

至少检查：

- candidate 是否来自真实 code/data path；
- 是否记录 reference direction；
- 是否有 raw key/offset/field/string；
- BornBeast/control 是否都检查；
- negative 是否有 scope；
- rejected candidate 是否记录原因。

### Positive control + differential

ArmModel `[Textures]/PieceIndex` 只作为 positive control。Review 不允许：

```text
ArmModel has PieceIndex
=> weapon short field is PieceIndex
```

必须有 weapon-side structural/differential bridge。

至少期望 BornBeast/Transformers/Jewelry + 一个简单 control 的：

```text
mesh count/names
short field raw offset/value
geometry relation
DTX/TGA/CFG paths + SHA/size
CFG phase/sample count
resource/config references
```

### CFG consumer

优先接受 consumer contract 对 H-CFG-A/B/C 的裁决。

若 consumer 未找到：

- hypotheses 保持 open；
- differential 可提高 evidence，但不能自动变 semantic verified；
- sample count 与 piece count 等单一相关不足以 closure。

### Channel semantics

必须分开：

```text
storage order
map/binding role
shader composition role
```

TGA storage-byte facts不能直接替代 shader role；DTX 1024 layout 仍 strong hypothesis，直到有更直接 evidence。

---

## 7. N01 PASS gate

优先 Path A：

```text
weapon mesh/piece
-> verified material/binding key
-> verified local texture set
-> CFG/material consumer role sufficiently identified
```

也允许 Path B：多个独立 same-family/control differential evidence 唯一支持上述关系，并明确 reject alternatives。

仅 basename、visual、length fit、单一 correlation 不足以 PASS。

期望 evidence：

```text
n01/consumer_candidate_matrix.json
n01/consumer_search_report.md
n01/weapon_material_differential.json
n01/cfg_consumer_report.json
n01/channel_semantics_report.json
n01/engine_binding_closure.json
```

N01 PASS 只允许进入 P4-M01 native composition/final material closure；不自动恢复 P5。

---

## 8. P4-M01 final gate

只有最终看到：

- mesh/material binding closure；
- CFG/render semantics 足够重建；
- visible color 只来自 local CF / verified semantics；
- 0 external pixels；
- clean reproducible output；
- BornBeast native composition 可稳定辨认；
- provenance/hash/path 闭合；

才允许：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

然后恢复 P5-T02。

当前不进入 final user visual gate，不执行 Source1 final integration，不恢复 P5-T02。