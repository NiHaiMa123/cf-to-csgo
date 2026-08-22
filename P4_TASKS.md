# P4_TASKS.md — P4 baseline 冻结 + P4-M01 材质纠偏入口

> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。
>
> P4 baseline 历史结论仍为 **`PASS / FROZEN`**。
>
> 当前具体执行子任务：**P4-M01-R1 — targeted continuation after partial Review acceptance**。

---

## 1. 当前 P4 结构

```text
P4 baseline   PASS / FROZEN
    |
    +-- conversion/build/package/MIGI/runtime contract      frozen
    +-- native CF material fidelity                         NOT proven historically

P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
    |
    +-- P4-M01-R1   ACTIVE / TARGETED_REWORK_REQUIRED      <- CURRENT
```

Native material recovery 是 P4-M01 的 hard requirement；R1 是父任务内的 evidence correction，不重新跑 P4 baseline，也不推翻 RV-01～RV-06。

当前 R1 文件关系：

```text
P4_M01_REWORK_R1.md          original R1 correction contract
P4_M01_R1_CONTINUATION.md    current continuation / Review overlay
```

若二者对“当前状态/下一步”的描述冲突，以 continuation 与 `plan.md` 第 1 节为准。

---

## 2. 历史 frozen baseline

保留：

- P4-T01～T09：历史完成；
- T08：`passed_user_confirmed`；
- RV-01～RV-06：历史完成；
- 最终历史 Review：`PASS WITH RISK`；
- frozen addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
- runtime：M4A4；
- `final_target_identity=false`；
- `final_cf_material=false`。

历史证据：

- [`P4_STATUS.md`](P4_STATUS.md)
- [`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)
- [`P4_RV04_TEST_SPECS.md`](P4_RV04_TEST_SPECS.md)

这些文件记录 baseline 历史，不能拿来证明 native material 已正确恢复。

---

## 3. P4-M01 主任务

主协议：[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

目标：

> 在不使用 external pixels 的前提下，仅用 local CF BornBeast LTB/DTX/TGA/CFG 等资源恢复正确、可重复、可解释的 native material，并产出可迁移到 P5 Transformers 的方法。

固定技术路线：

```text
provenance audit
-> native material inventory
-> DTX revalidation
-> TGA revalidation
-> LTB material binding
-> WeaponShader CFG binary reverse
-> variant differential
-> offline shader hypotheses
-> native material closure
-> optional Source 1 integration check after closure
```

---

## 4. R1 历史与当前 Review

第一轮 exploration commit：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5
```

Chat/Sol 当时判定其 C/D/E/F/H/I 证据等级过高，因此创建 R1。

当前 Local Executor continuation commit：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
```

该提交不是全 PASS，但有实质进展。当前正式 Review：

```text
A provenance              ACCEPT / REUSE
B inventory               REUSE_WITH_CAUTION
C DTX                      PARTIAL_ACCEPT / TARGETED_REWORK
D TGA                      ACCEPT / STRUCTURAL
E material binding         STAGE1_PARTIAL_ACCEPT / STAGE2_OPEN
F CFG reverse              PARTIAL_ACCEPT / REFRAME
G variant differential     ACCEPT / REUSE
H shader hypotheses        DIAGNOSTIC_ONLY / REWORK
I native closure           NOT READY / CONTINUE
J Source1 integration      DEFERRED
```

详细理由与当前唯一执行顺序见：

[`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md)

---

## 5. 当前已接受内容

### R1-D TGA

正式 decoder 的：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

已被 `bded9e8` 的 R1 repair 脚本正确采用，旧 10-byte-shifted excision 被 supersede。默认：

```text
R1-D = ACCEPT / STRUCTURAL
```

不要无理由重跑。

### R1-E stage 1

LTB 中已找到 mesh-associated post-mesh numeric field，BornBeast/Transformers 都有 `{0..8}` 结构集合。接受“该 numeric field 是真实 LTB 结构”；其含义是否等于 texture slot 仍 provisional。

### CFG corpus finding

237 个 WeaponShader CFG 的 3-byte periodic/mod-3 现象保留为有效 supporting evidence，但尚不能唯一解释为 `scalar + padding`。

---

## 6. 当前剩余 targeted work

### C — DTX

- 把 report 声称的 width/stride scan 真正提交到可重跑脚本；
- 关键 width 候选输出完整 score/rejection matrix；
- full-file + 2212-byte tail periodicity；
- continuity 覆盖所有变化 channel；
- terminal remainder semantics；
- RGB/BGR order。

当前不要把 `1024 width / no mips` 写成最终 engine-verified fact，直到可复现 evidence 与 report 对齐。

### E — stage-2 binding

优先利用仓库已有：

```text
LithTechModelTextureConfigIndex.cs
LithTechTextureMappingScanner.cs
LithTechDatTextureReferenceIndex.cs
TextureReferenceResolver.cs
LithTechModelTextureLoader.cs
```

目标：证明 model/skin/numeric field 到实际 DTX/TGA/CFG texture set 的 engine/config/resource-table 关系，或提交明确 negative result。

### F — CFG

必须同时比较：

```text
H-CFG-A = RGB/BGR color triplets with two fixed-FF channels
H-CFG-B = scalar + padding/alignment
```

不得过滤合法 `0xFF` sample 后把剩余数量当完整 record count；必须精确 accounting 492/506/642 bytes。

### H — shader diagnostic

`r1_shader_closure.py` 中 `step = 97` 导致 byte phase 混采，因为 `97 % 3 == 1`。按 pixel index 或 `3*k` byte stride 修复。修复后仍保持 `DIAGNOSTIC_ONLY`，直到 engine composition semantics 有证据。

### I — closure

继续保持 `NOT READY / CONTINUE`。技术 open items 未闭合前不请求用户 final visual gate。

---

## 7. Frozen 与可修改边界

### 不得修改

```text
历史 frozen run/package/deploy evidence
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 skeleton/sequence/attachment contract
RV-01 ~ RV-06 历史证据
```

### P4-M01 / R1 允许

```text
CFRezManager/Decoders/** 中与材质恢复直接相关的代码
相关 inspection/export code
scripts/material_recovery/**
材质恢复专用脚本/测试
work/m4a1_s_bornbeast/p4_m01_native_material/**
closure 后独立命名的新材质测试 addon
```

如果必须改 frozen conversion contract 才能继续，停止并返回 Chat/Sol。

---

## 8. 角色路由

### Local Executor Agent

由用户选择，不绑定任何具体模型。读取：

```text
AGENTS.md
plan.md
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
```

从 commit `bded9e8` 和现有 R1 evidence 继续，不重跑已接受的 TGA/A/G。

### Chat/Sol

读取：

```text
AGENTS.md
plan.md
CHAT_REVIEW.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
```

负责 evidence Review 和是否允许 `P4-M01 PASS` / 恢复 P5-T02。

---

## 9. Handoff

只有 Chat/Sol 判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复：

```text
P5-T02
-> apply validated method to M4A1_S_Transformers
```

所有 Agent 继续遵守 [`AGENTS.md`](AGENTS.md) 的 master-only handoff 与 `data/**` 本地保护规则。
