# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给**任何用户选择的、具备本地执行能力的 Agent** 使用；不绑定 Luna、Codex、GLM 或其他具体模型/Agent。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = 用户当前选择的可执行本地任务的 Agent。**

---

## 1. 当前阶段

截至 2026-08-22：

- P4 baseline：**`PASS / FROZEN`**；
- P4-M01：**`ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`**；
- **P4-M01-R1：`ACTIVE / TARGETED_REWORK_REQUIRED`，这是当前唯一具体执行子任务；**
- P5-T01：`PASS / USER_REFERENCE_CONFIRMED`；
- P5-T02：`PAUSED_BY_P4_M01`；
- P5-T03/T04：继续 blocked；
- P7 visible Inspect / 手指 retarget / CF 原动画不是当前任务。

当前正式协议：

```text
P4_M01_TASK_SPEC.md          parent contract
P4_M01_REWORK_R1.md          original R1 correction contract
P4_M01_R1_CONTINUATION.md    current targeted continuation / review overlay
```

`P4_M01_R1_CONTINUATION.md` 不代表 R2；它只收敛 R1 在 commit `bded9e8a6f7f95997d9717eb8f35beb02619f153` 之后剩余的工作。P4 baseline 的 geometry / Source build / package / MIGI 技术证据继续冻结。

---

## 2. 当前本地 Executor 角色

角色：**本地材质逆向执行器 + 证据生产器**。

任何用户选择的 Agent 只要能访问本地仓库与 `data/**`、执行项目工具链并按要求保存证据，就可以承担该角色。切换模型/Agent 不改变 Task Spec、acceptance criteria 或 authoritative state。

本地 Executor 负责：

- 安全同步最新 `master`；
- 严格执行 `P4_M01_TASK_SPEC.md`、`P4_M01_REWORK_R1.md` 与当前 `P4_M01_R1_CONTINUATION.md`；
- 读取本地 `data/**`；
- 复用 commit `632ede4` 与 `bded9e8` 的有效 evidence，不无理由从零重跑；
- 只修正当前仍 open 的 DTX/CFG/stage-2 binding/H2 问题；
- 必要时最小扩展 CFRezManager decoder/inspection code；
- 保存命令、offset、hash、报告、派生预览和 rejection evidence；
- 完成后把 scoped code/evidence push 到 `master`；
- `data/**` 原始资产永不上传。

本地 Executor 不得：

- 重跑已被 Chat/Sol 接受的 R1-D formal TGA repair，除非新 evidence 明确冲突；
- 把 DTX `1024 width / no mips` 在缺少可重跑 width scan 时写成最终 engine-verified fact；
- 把 LTB post-mesh numeric field 自动等同于 verified texture slot；
- 把 CFG `scalar + padding` 当唯一已证明 framing；
- 过滤合法 `0xFF` 后再把剩余数量称为完整 CFG record/sample count；
- 把 diagnostic shader preview 当 engine semantics；
- 直接要求用户做 final visual gate；
- 把 external CS1.6/MOD texture 当 BornBeast 或雷神 final input；
- 覆盖历史 frozen addon / P4 evidence；
- 自行恢复 P5-T02 或写最终 `IDENTITY_CONFIRMED`。

---

## 3. 每次启动顺序

1. `git status --short --branch`；
2. 确认当前分支为 `master`；
3. tracked worktree 可安全同步时：

```bash
git fetch origin
git pull --rebase origin master
```

4. 读取 [`AGENTS.md`](AGENTS.md)；
5. 读取 [`plan.md`](plan.md) 第 1 节；
6. 读取本文件；
7. 读取 [`P4_TASKS.md`](P4_TASKS.md)；
8. 读取 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)；
9. 读取 [`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md)；
10. **读取 [`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md)，它是当前 targeted work 的直接入口；**
11. 读取 commit `bded9e8` 产生的 R1 evidence：

```text
scripts/material_recovery/r1_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/r1/**
```

12. 从 continuation 的剩余任务继续，不从 A/C/D/E/F 全量重跑。

`P5_TASKS.md` 和 `P5_T02_TASK_SPEC.md` 当前只用于理解后续 handoff，不是当前第一执行入口。

---

## 4. 当前 Review 分级

Chat/Sol 对 commit `bded9e8` 的正式分级：

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

详细原因只看：

```text
P4_M01_R1_CONTINUATION.md
```

当前固定执行顺序：

```text
1. R1-C: commit reproducible width/stride scan + full-file periodicity/tail analysis
2. R1-F: triplet-vs-scalar competing hypotheses; no dropping 0xFF samples
3. R1-E stage2: use existing mapping/config/index/resolver code to seek engine binding
4. R1-H: fix channel-sampling bug; regenerate diagnostic previews only after corrected inputs
5. R1-I: regenerate closure with unresolved items left unresolved
```

当前用户视觉确认不是 blocker。

---

## 5. 已接受与仍需纠正的关键点

### R1-D TGA — ACCEPT / STRUCTURAL

正式 repair 关系：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

commit `bded9e8` 已按该结构重建 BornBeast Alpha/Normal/Specular 三张 1024×1024 / 24bpp TGA，并 supersede 旧 10-byte-shifted excision。默认不重跑。

### R1-C DTX — TARGETED_REWORK

已接受：正式 version/LZMA 纠错、旧 512×256 full-mip 结论撤销、3-byte periodic structure 有强支持。

仍需：

- 把 report 声称的 width scan 真正写进并提交可重跑脚本；
- 关键候选 width/stride 的完整 score/rejection matrix；
- full-file + tail periodicity；
- continuity 覆盖所有变化 channel；
- 2212-byte tail semantics；
- RGB/BGR order。

### R1-E binding — STAGE1_PARTIAL_ACCEPT / STAGE2_OPEN

接受 LTB 中存在 mesh-associated post-mesh numeric field 的结构证据；其含义是否为 texture slot 仍 provisional。

stage-2 优先利用：

```text
LithTechModelTextureConfigIndex.cs
LithTechTextureMappingScanner.cs
LithTechDatTextureReferenceIndex.cs
TextureReferenceResolver.cs
LithTechModelTextureLoader.cs
```

目标是证明 model/skin/numeric field 到实际 DTX/TGA/CFG texture set 的 engine/config/resource-table 关系。

### R1-F CFG — PARTIAL_ACCEPT / REFRAME

237-file corpus 的 3-byte periodic/mod-3 发现保留；但必须同时测试：

```text
H-CFG-A = RGB/BGR triplets with two fixed-FF channels
H-CFG-B = scalar + padding/alignment
```

不得用 `if raw[i] != 0xFF` 删除合法 sample 后再宣称 exact record count。

### R1-H — DIAGNOSTIC_ONLY / REWORK

`r1_shader_closure.py` 的：

```python
step = 97
```

会因为 `97 % 3 == 1` 在 byte phases 之间轮换，污染 variable-channel census。按 pixel index 或 `3*k` byte stride 修复；修后 H2 仍只是 approximation，除非 stage-2/CFG 得到 engine semantics。

---

## 6. P4 frozen 边界

P4-M01/R1 不允许修改：

```text
历史 P4 frozen run/package/deploy evidence
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 runtime slot
57-bone Source reference
sequence/attachment contract
RV-01 ~ RV-06 历史证据
```

允许新增/修改：

```text
CFRezManager/Decoders/** （与材质恢复直接相关）
相关 inspection/export code
scripts/material_recovery/**
材质恢复专用新增脚本/测试
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

如果材质恢复必须改变 frozen conversion contract，返回 Chat/Sol，不自行修改。

---

## 7. 状态语义

正常继续：

```text
P4-M01    = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1 = ACTIVE / TARGETED_REWORK_REQUIRED
```

Local Executor 只提交 corrected code/evidence，不自行把 authoritative `plan.md` 改成 PASS；最终状态由 Chat/Sol Review。

真正 BLOCKED 才返回：

- BornBeast 必要本地原始资源缺失；
- 多条独立路线都无法访问/解释必要 bytes；
- 必须改变 frozen conversion contract；
- R1/Task Spec 本身需要修改。

单个 hypothesis 失败不是 BLOCKED；保存 rejection evidence 后继续。

---

## 8. Executor provenance

任务定义继续保持 agent-agnostic，不按具体模型绑定。

用户报告 commit `bded9e8` 的执行组合为：

```text
Claude Code harness + GLM-5.3-Flash internal beta
```

该 commit footer 残留 `Co-Authored-By: Claude Opus 4.8 (1M context)`，不得据此推断实际 executor。后续若记录模型 benchmark provenance，显式写在 evidence/report 中，不复制错误 footer。

---

## 9. P5 handoff

只有 Chat/Sol Review 明确判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 P5-T02。

在此之前：

```text
P5-T02 = PAUSED_BY_P4_M01
```

---

## 10. Git / data 规则摘要

完整规则见 `AGENTS.md`。特别强调：

- Agent handoff 只认 `master`；
- `data/**` 永远 local-only；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `git add -A` / `git add --all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不使用 mirror/delete 同步；
- 原始 LTB/DTX/TGA/CFG 不上传，只上传代码、报告、hash 和派生预览；
- 不删除上一轮 evidence 来隐藏错误，新的 evidence 必须保留 supersedes/provenance 关系。
