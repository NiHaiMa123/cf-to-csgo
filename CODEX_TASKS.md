# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给**任何用户选择的、具备本地执行能力的 Agent** 使用；不绑定 Luna、Codex 或其他具体模型/Agent。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = 用户当前选择的可执行本地任务的 Agent。**

---

## 1. 当前阶段

截至 2026-08-22：

- P4 baseline：**`PASS / FROZEN`**；
- P4-M01：**`ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`**；
- **P4-M01-R1：`ACTIVE / REWORK_REQUIRED`，这是当前唯一具体执行子任务；**
- P5-T01：`PASS / USER_REFERENCE_CONFIRMED`；
- P5-T02：`PAUSED_BY_P4_M01`；
- P5-T03/T04：继续 blocked；
- P7 visible Inspect / 手指 retarget / CF 原动画不是当前任务。

当前正式协议：

```text
P4_M01_TASK_SPEC.md       parent contract
P4_M01_REWORK_R1.md       current execution entry
```

P4 baseline 的 geometry / Source build / package / MIGI 技术证据继续冻结。P4-M01-R1 只纠正 native CF material decode / binding / shader evidence，不修改 frozen conversion baseline。

---

## 2. 当前本地 Executor 角色

角色：**本地材质逆向执行器 + 证据生产器**。

任何用户选择的 Agent 只要能访问本地仓库与 `data/**`、执行项目工具链并按要求保存证据，就可以承担该角色。切换 Agent 不改变 Task Spec、acceptance criteria 或 authoritative state。

本地 Executor 负责：

- 安全同步最新 `master`；
- 严格执行 `P4_M01_TASK_SPEC.md` 与当前 `P4_M01_REWORK_R1.md`；
- 读取本地 `data/**`；
- 复用 commit `632ede449578f688cea7e6b5f40cbf03700aaaa5` 的已有 evidence，不无理由从零重跑；
- 修正 BornBeast DTX/TGA/CFG/LTB material binding 的关键证据问题；
- 必要时最小扩展 CFRezManager decoder/inspection code；
- 在 C/D/E/F 修正后重新构建 deterministic offline shader hypotheses；
- 保存命令、offset、hash、报告、派生预览和 rejection evidence；
- 完成后把 scoped code/evidence push 到 `master`；
- `data/**` 原始资产永不上传。

本地 Executor 不得：

- 把旧 `native_material_closure.json` 的 `6/8 PASS` 当 authoritative；
- 直接要求用户确认旧紫色 preview；
- 继续要求用户在 C029/C103 灰模之间强选；
- 重跑已完成的雷神 T01 Web Search；
- 把 external CS1.6/MOD texture 当 BornBeast 或雷神 final input；
- 从 external reference 抠色、采样、烘焙后冒充 local CF；
- 把 `CfgBinaryStripDecoder` 的 raw strip 当 CFG semantic decode；
- 仅凭“能显示成图片”宣布 DTX/TGA 格式正确；
- 把 basename+directory convention 自动算作 structural material binding；
- 覆盖历史 frozen addon / P4 evidence；
- 修改 frozen M4A4 skeleton/sequence/attachment/build contract；
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
9. **读取 [`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md)；**
10. 读取上一轮可复用 evidence：

```text
scripts/material_recovery/**
work/m4a1_s_bornbeast/p4_m01_native_material/**
commit 632ede449578f688cea7e6b5f40cbf03700aaaa5
```

11. 从 R1-C / R1-D / R1-E / R1-F 开始或继续；A provenance 与 G variant evidence 默认复用。

`P5_TASKS.md` 和 `P5_T02_TASK_SPEC.md` 当前只用于理解后续 handoff，不是当前第一执行入口。

---

## 4. 当前任务：P4-M01-R1 Evidence Rework

Chat/Sol 已 Review 上一轮 A→I evidence，当前正式分级：

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

详细原因与执行要求只看：

```text
P4_M01_REWORK_R1.md
```

固定 R1 路线：

```text
R1-C DTX formal parser/LZMA/dimension/orientation/trailer revalidation
-> R1-D TGA repair exactly aligned with TgaThumbnailDecoder
-> R1-E structural material binding
-> R1-F CFG exact framing/channel/semantic binding
-> R1-H rebuild native shader hypotheses
-> R1-I regenerate closure
```

当前用户视觉确认不是 blocker。技术 evidence 未闭合前不请求用户判定紫色 preview 是否“正确”。

---

## 5. 关键已知 Review 纠错

### DTX

- 正式 `DtxThumbnailDecoder` 的已知 version 是 `-2/-3/-5`；
- 旧脚本用正数 `1..34` 不能称为复现正式 parser；
- LZMA 必须用 `LzmaAloneDecoder` 实际逻辑，不用 entropy 代替；
- `512x256` 与 `256x512` byte count 相同，需额外结构证据区分；
- trailing bytes 必须精确 accounting。

### TGA

正式 repair 关键关系：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

旧 `TRUEVISION - 18 ... +26` 删除法与正式 decoder 不一致，因此旧 TGA decode/channel role/preview 均需 R1 重做。

### Material binding

```text
same basename + directory role
```

只能支持 resource-family association。除非用 engine/config/跨样本/negative-control 等证据证明这是正式 contract，否则不能让 closure 条件 4 PASS。

### CFG

- 492 bytes 可被 3 整除；506 bytes 不可；642 bytes 得 214 records；
- 不允许 `len // 3` 静默丢 trailing bytes；
- RGB/BGR order 必须自洽；
- raw color strip 不等于 shader semantic binding。

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
P4-M01-R1 = ACTIVE / REWORK_REQUIRED
```

R1 完成后，本地 Executor 只提交 corrected code/evidence，不自行把 authoritative `plan.md` 改成 PASS；最终状态由 Chat/Sol Review。

真正 BLOCKED 才返回：

- BornBeast 必要本地原始资源缺失；
- 多条独立路线都无法访问/解释必要 bytes；
- 必须改变 frozen conversion contract；
- R1/Task Spec 本身需要修改。

单个 hypothesis 失败不是 BLOCKED；保存 rejection evidence 后继续。

---

## 8. P5 handoff

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

## 9. Git / data 规则摘要

完整规则见 `AGENTS.md`。特别强调：

- Agent handoff 只认 `master`；
- `data/**` 永远 local-only；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `git add -A` / `git add --all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不使用 mirror/delete 同步；
- 原始 LTB/DTX/TGA/CFG 不上传，只上传代码、报告、hash 和派生预览；
- 不删除上一轮 evidence 来隐藏错误，新的 R1 evidence 必须保留 supersedes/provenance 关系。
