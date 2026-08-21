# P4_TASKS.md — P4 baseline 冻结 + P4-M01 材质纠偏入口

> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。
>
> P4 baseline 历史结论仍为 **`PASS / FROZEN`**。
>
> 当前具体执行子任务：**P4-M01-R1 — BornBeast native material evidence correction**。

---

## 1. 当前 P4 结构

```text
P4 baseline   PASS / FROZEN
    |
    +-- conversion/build/package/MIGI/runtime contract      frozen
    +-- native CF material fidelity                         NOT proven historically

P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
    |
    +-- P4-M01-R1   ACTIVE / REWORK_REQUIRED               <- CURRENT
```

Native material recovery 是 P4-M01 的 hard requirement；R1 是父任务内的 evidence correction，不重新跑 P4 baseline，也不推翻 RV-01～RV-06。

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

## 4. 当前纠错任务：P4-M01-R1

正式协议：[`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md)。

上一轮 Local Executor 在 commit：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5
```

提交了大量 A→I exploration evidence。Chat/Sol Review 后，不把这些产出全部作废，而是按证据等级复用：

```text
A provenance              ACCEPT / REUSE
B inventory               REUSE_WITH_CAUTION
C DTX                      REWORK
D TGA                      FAIL / REWORK
E material binding         INCOMPLETE
F CFG reverse              INCOMPLETE
G variant differential     ACCEPT AS SUPPORTING EVIDENCE / REUSE
H shader hypotheses        DIAGNOSTIC_ONLY
I native closure           NOT READY
J Source1 integration      DEFERRED
```

当前不是“等用户确认紫色 preview”。R1 必须先完成：

```text
R1-C DTX formal revalidation
-> R1-D TGA repair correction
-> R1-E structural material binding
-> R1-F CFG exact framing + semantic binding
-> R1-H rebuild shader hypotheses
-> R1-I regenerate closure
```

下一位 Agent 不得仅因为模型/Agent 更换而重跑 A/G；从最新 `master` 和已有 evidence 继续。

---

## 5. R1 已确认的 Review 问题

### DTX

- 正式 `DtxThumbnailDecoder` version 为 `-2/-3/-5`；
- 上一轮脚本使用正数 version 集合，不能称为正式 parser 复现；
- LZMA 需要真实 `LzmaAloneDecoder` 逻辑；
- `512x256` 与 `256x512` byte-count 相同，尺寸/orientation 尚未证明；
- trailer byte accounting 必须重做。

### TGA

正式 decoder inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

上一轮 `TRUEVISION - 18 ... +26` 删除区间与正式 decoder 不一致，因此旧 TGA channel/previews 不得继续作为 closure evidence。

### Binding

basename+directory relation 只能支持 resource-family association；结构 binding 仍需 engine/config/binary/differential evidence。

### CFG

492/506/642 byte 样本长度不支持“统一 164×3 bytes”结论；不允许用 `len // 3` 静默丢 bytes。RGB/BGR order 与 semantic slot 仍需证明。

---

## 6. Frozen 与可修改边界

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

## 7. 角色路由

### Local Executor Agent

由用户选择，不绑定任何具体模型。只要能访问本地仓库与 `data/**`、运行项目工具链、保留 evidence 并按规则 push 到 `master`，即可执行当前任务。

读取：

```text
AGENTS.md
plan.md
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
```

当前只执行 R1，不继续 P5 C029/C103 用户强选，不请求用户确认旧紫色 preview。

### Chat/Sol

读取：

```text
AGENTS.md
plan.md
CHAT_REVIEW.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
```

负责 evidence Review 和是否允许 `P4-M01 PASS` / 恢复 P5-T02。

---

## 8. Handoff

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
