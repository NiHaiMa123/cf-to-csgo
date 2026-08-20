# CODEX_TASKS.md — Codex / Luna 本地执行合同

> 本文件只给 **Codex 环境中的 Agent** 使用，包括 Luna、本地执行 Agent，以及用户明确调用时的 Codex Sol。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = Luna / 普通 Codex Agent。**

---

## 1. 当前阶段

截至 2026-08-20：

- P4：**`PASS / FROZEN`**；
- P4 最终 Review：`PASS WITH RISK`，允许冻结；
- P5：**ACTIVE — 最终雷神资产定位**；
- P5-T01：**EXECUTION_PASS / REVIEWED**；
- P5-T02：**READY_FOR_LUNA**；
- P5 任务流：[`P5_TASKS.md`](P5_TASKS.md)；
- 当前正式执行协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)；
- P4 visible Inspect / 手指 retarget 属于 P7，不是当前任务；
- P4 frozen baseline 不得因为 P5/P7 问题被自行重写。

P4 证据：[`P4_STATUS.md`](P4_STATUS.md)、[`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)。

---

## 2. Luna / 普通 Codex Agent 的默认角色

角色：**本地执行器 + 证据生产器**。

职责：

- 安全拉取最新 `master`；
- 读取本地 `data/**` 和本地工具链；
- 运行只能在用户机器执行的扫描、解析、Blender、Crowbar、`studiomdl`、MIGI、Python 等任务；
- 严格执行用户或 Chat/Sol 已经固定的 Task/Test Spec；
- 保留 command、stdout/stderr、exit code、run id、hash、report；
- 只提交允许上传的代码、报告和证据；
- `data/**` 原始资产永远不上传。

Luna **不是默认 Reviewer**，不得自行：

- 重新 Review P4；
- 把某个 P5 候选直接声明为“最终雷神”；
- 降低 Chat/Sol 已设定的 candidate / identity acceptance criteria；
- 因看到某个候选“看起来像”就跳过 provenance；
- 修改 `plan.md` 的阶段最终状态，除非任务明确要求执行一个已经由 Reviewer 判定的状态更新。

---

## 3. Codex Sol

Codex Sol 默认也不承担额外独立 Review。

只有用户明确说出类似：

- “用 Codex Sol 做独立 review”；
- “让 Codex Sol 做 milestone audit”；

才进入额外审计模式。结果必须单独标记 `CODEX_SOL_AUDIT`，不能覆盖 Chat/Sol 的正式 Review 记录。

---

## 4. 每次启动顺序

1. 读取 `AGENTS.md`；
2. 读取 `plan.md` 第 1 节；
3. 读取本文件 `CODEX_TASKS.md`；
4. 读取当前阶段任务流 `P5_TASKS.md`；
5. 读取当前默认 Task Spec：`P5_T02_TASK_SPEC.md`；
6. `git status --short --branch`；
7. tracked 工作区可安全同步时执行 `git fetch origin` + `git pull --rebase origin master`；
8. 再严格执行 Task Spec。

不要把聊天记忆、旧分支、旧 MOD、历史报告或本地未提交实验当作 authoritative task source。

---

## 5. 当前 P5 identity correction

P5-T01 完成后，Chat/Sol 使用外部 identity reference 纠正了 T01 原始 recall ranking：

```text
M4A1-雷神  -> M4A1-S Transformers
M4A1-黑骑士 -> M4A1-S Born Beast
```

因此：

- T01 的 BornBeast 高分只代表 M4A1/历史配置召回强，不代表雷神身份；
- `PV-M4A1_S_Transformers.LTB` 是当前 T02 PRIMARY；
- `PV-M4A1_S_Transformers_Classic.LTB` 是 same-family control；
- `PV-M4A1_S_BornBeast.LTB` 是 negative control；
- Luna 不得按 T01 排名继续自己挑 Top 30，也不得自行扩大 T02 候选。

---

## 6. 当前 P5-T02 任务

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

执行目标：

```text
verify frozen input hashes
  -> export PRIMARY / same-family / negative-control LTB
  -> structure compare
  -> Blender 4.5 standardized multiview previews
  -> verify exact local Transformers DTX/TGA/CFG resource family
  -> review_sheet.png + JSON evidence
  -> push
  -> STOP for Chat/Sol review
```

特别禁止：

- 继续全量扫描 `data/**`；
- 把 Transformers 的某个其他皮肤 / suffix variant 擅自加入候选；
- 修改 P4 frozen pipeline；
- Steam / MIGI deploy；
- Luna 自行写 `IDENTITY_CONFIRMED`；
- 自行进入 T03。

---

## 7. 当前 P5 执行原则

P5 目标是**最终雷神本地 CF 资产身份定位**，不是继续改 P4 pipeline。

必须遵守：

1. 原始 `data/**` 不上传；
2. 可以上传路径、hash、size、解析报告、Task Spec 明确允许的预览图/缩略图和 candidate matrix；
3. 不把网络第三方 MOD 当作 final source；
4. 最终资产身份由 Chat/Sol 根据证据判定，Luna 只报告候选事实；
5. T02 只处理固定三个模型和 exact-match Transformers 资源族，不做全量 Blender。

---

## 8. Chat → Codex 委托协议

当 Chat/Sol 给出 Task/Test Spec 时，至少应包含：

```text
task_id
purpose
scope
input roots / allowed data paths
operation / search strategy
must_preserve
expected outputs
evidence fields
PASS / FAIL / INVALID 或 candidate ranking 规则
forbidden changes
upload allowlist
```

Luna 执行时：

- 不改变任务目标；
- 不私自扩大扫描到不相关用户目录；
- 不把困难步骤换成语义不同的简单步骤；
- unrelated error 标记 `INVALID/BLOCKED`；
- 只返回执行事实和证据，不替 Reviewer 做最终身份结论。

---

## 9. Git / data 规则摘要

完整规则见 [`AGENTS.md`](AGENTS.md)。特别强调：

- `data/**` 永远 local-only；
- GitHub 没有 `data/` 不等于本地应该删除；
- pull 前检查 `git status`；
- 同一 tracked 文件本地/远端都改过时停止自动处理冲突；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .`、`git add -A`、`git add --all`；
- 默认禁止 `git reset --hard`、`git clean -fd`、`git clean -fdx`、`git restore .`、`git checkout -- .`；
- 不 force-push；
- 不使用 mirror/delete 同步破坏 ignored 本地资产。

---

## 10. 当前默认停止条件

完成 `P5_T02_TASK_SPEC.md` 后：

> **Luna 只提交 Task Spec upload allowlist 内的派生证据，然后停止。不得自行开始 P5-T03，不得自行宣布最终雷神。**
