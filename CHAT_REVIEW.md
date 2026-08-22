# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 ChatGPT 对话中的 **Chat/Sol** 使用。
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / PHASE1_CONSUMER_DISCOVERY   <- CURRENT REVIEW TARGET
P5-T01             PASS / USER_REFERENCE_CONFIRMED
P5-T02             PAUSED_BY_P4_M01
P5-T03             BLOCKED_BY_T02
P5-T04             BLOCKED_BY_T03
```

当前 Review 入口：

```text
P4_M01_TASK_SPEC.md
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md
P4_M01_N01_CONTINUATION.md   <- current overlay
CODEX_TASKS.md
```

R1 history 仅在需要 predecessor evidence 时读取。

---

## 2. 最新 Review — commit 2344d61

最新 Local Executor 提交：

```text
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19
P4-M01-N01 Phase 0: R1 final consistency cleanup (gate PASS)
```

与前一 authoritative HEAD 相比，只包含 Phase-0/R1 cleanup；没有 Phase 1+ N01 outputs。

### Phase 0 正式分级

```text
CFG phase-origin span formula             ACCEPT
DTX margin / 1043-of-1046 wording         ACCEPT
H1 preview path                           ACCEPT
H1 evidence-class downgrade               ACCEPT
shader stale BGR24/scalar wording         ACCEPT
binding negative-scope wording            ACCEPT
```

因此：

```text
P4-M01-R1          = ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 = ACCEPT / FROZEN
```

### 执行完整性

原 N01 明确要求 Phase 0 后同轮进入 Phase 1，但 `2344d61` 停在 Phase 0。

```text
technical Phase-0 result   ACCEPT
execution completeness     INCOMPLETE / STOPPED_EARLY
```

这不是 blocker；下一位 Executor 直接 Phase 1，不得重跑 Phase 0。

### Phase-0 gate 工具说明

`scripts/material_recovery/n01_phase0_gate.py` 是 consistency diagnostic。Review 不能仅凭 executor 声称“30+ checks PASS”判定；应直接检查提交后的 report/script 内容。当前 Chat/Sol 已直接复核并接受 Phase 0。

---

## 3. Executor provenance

用户当前准备切换执行模型：

```text
Model: MiniMax M3
Harness: unspecified / user-selected
```

Task 继续 agent-agnostic；模型信息只用于 benchmark/provenance。

不要从 commit footer 推断真实 executor；历史：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

不是可靠模型 provenance。

---

## 4. N01 Review principle

N01 的核心问题：

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
- 相邻目录 = binding；
- length/count fit = semantic proof；
- `[0,42]` 值域小 = scalar verified；
- 能画成图 = texture role verified；
- external visual match = native semantics；
- negative 超出实际 scope；
- 为 PASS 无限扩大 blind scan。

---

## 5. 已接受 baseline — Review 不得重复打回

除非出现新 counterevidence：

```text
R1 correction                           ACCEPTED / COMPLETE
N01 Phase 0                             ACCEPT / FROZEN
DTX no formal LithTech header           VERIFIED_STRUCTURAL
DTX not LZMA                            VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodic payload  VERIFIED_STRUCTURAL
DTX one fixed-FF byte position          VERIFIED_STRUCTURAL
DTX 1024/no-mips                        STRONG_HYPOTHESIS
DTX 1043/1046 packing statistic         VERIFIED_CORPUS_STATISTIC
TGA formal repair                       ACCEPT / STRUCTURAL
CFG 237/237 single-phase mod-3 fact     VERIFIED_STRUCTURAL
CFG phase != record boundary            correction accepted
CFG primary extraction                  164/169/214 accepted
CFG phase-origin span formula           accepted
H1 path/evidence cleanup                accepted
H2 phase-mixing fix                     accepted
ArmModel [Textures]/PieceIndex format   VERIFIED_STRUCTURAL
weapon LTB short field exists           VERIFIED_STRUCTURAL
355-file config-like negative           NEGATIVE_RESULT_SCOPED
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

## 6. 当前 Review target — Phase 1 + Phase 2

下一次 Review 从 commit `2344d61...` 之后的新提交开始。

### Phase 1 — consumer discovery

至少检查：

- candidate 来自真实 code/data path；
- reference direction 是否明确；
- 是否记录 raw key/offset/field/string；
- BornBeast / Transformers / Jewelry / control 是否覆盖；
- negative 是否有 scope；
- rejected candidate 是否记录 reason。

期望：

```text
n01/consumer_candidate_matrix.json
n01/consumer_search_report.md
```

### Phase 2 — positive control + differential

ArmModel `[Textures]/PieceIndex` 只作 positive control，不允许：

```text
ArmModel has PieceIndex
=> weapon short field is PieceIndex
```

必须有 weapon-side structural/differential bridge。

至少期望：

```text
BornBeast
Transformers
Jewelry
+ 1 simple/traditional M4A1-S control if available
```

及：

```text
mesh count/names
short-field raw offset/value
geometry relation
DTX/TGA/CFG paths + SHA/size
CFG phase/sample count
resource/config references
```

输出：

```text
n01/weapon_material_differential.json
```

**当前最低 handoff = Phase 1 + Phase 2。只做 candidate list 就停止，不算完成当前 continuation。**

---

## 7. Phase 3–4 Review

### CFG consumer

优先接受 consumer contract 对 H-CFG-A/B/C 的裁决。

consumer 未找到时：

- hypotheses 保持 open；
- differential 可提高 evidence，但不能自动 semantic verified；
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

## 8. N01 PASS gate

优先 Path A：

```text
weapon mesh/piece
-> verified material/binding key
-> verified local texture set
-> CFG/material consumer role sufficiently identified
```

也允许 Path B：多个独立 same-family/control differential evidence 唯一支持上述关系，并明确 reject alternatives。

仅 basename、visual、length fit、单一 correlation 不足以 PASS。

最终期望 evidence：

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

## 9. P4-M01 final gate

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