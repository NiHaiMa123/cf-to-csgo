# P4_TASKS.md — P4 baseline 冻结 + P4-M01 材质纠偏入口

> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。
>
> P4 baseline 历史结论仍为 **`PASS / FROZEN`**。
>
> 用户于 2026-08-21 明确授权一个 post-freeze corrective task：**P4-M01 — BornBeast 原生 CF 材质恢复基准**。

---

## 1. 当前 P4 结构

```text
P4 baseline   PASS / FROZEN
    |
    +-- conversion/build/package/MIGI/runtime contract      frozen
    +-- native CF material fidelity                         NOT proven historically

P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

Native material recovery 是 P4-M01 的 hard requirement；`REQUIRED` 不作为独立 lifecycle status。

P4-M01 不是重新跑 P4-T01～T09，也不是推翻 RV-01～RV-06。

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

## 3. 当前任务：P4-M01

正式协议：

[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)

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

## 4. Frozen 与可修改边界

### 不得修改

```text
历史 frozen run/package/deploy evidence
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 skeleton/sequence/attachment contract
RV-01 ~ RV-06 历史证据
```

### P4-M01 允许

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

## 5. 角色路由

### Local Executor Agent

由用户选择，不绑定 Luna、Codex 或任何具体模型。只要能访问本地仓库与 `data/**`、运行项目工具链、保留 evidence 并按规则 push 到 `master`，即可执行当前任务。

读取：

```text
AGENTS.md
plan.md
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
```

当前只执行 P4-M01，不继续 P5 C029/C103 用户强选。

### Chat/Sol

读取：

```text
AGENTS.md
plan.md
CHAT_REVIEW.md
P4_M01_TASK_SPEC.md
```

负责 evidence Review 和是否允许 `P4-M01 PASS` / 恢复 P5-T02。

---

## 6. Handoff

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
