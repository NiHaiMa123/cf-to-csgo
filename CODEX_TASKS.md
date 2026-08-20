# CODEX_TASKS.md — Codex / Luna 本地执行合同

> 本文件只给 **Codex 环境中的 Agent** 使用，包括 Luna、本地执行 Agent，以及用户明确调用时的 Codex Sol。
>
> 项目唯一权威进度仍以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 和 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认独立 Reviewer 不是 Codex Sol，而是 Chat/Sol；Chat 侧 Review 规则见 [`CHAT_REVIEW.md`](CHAT_REVIEW.md)。**

---

## 1. 角色必须先分清

### 1.1 Luna / 普通 Codex Agent

默认角色：**本地执行器 + 证据生产器**。

职责：

- 拉取最新 `master`；
- 读取本地 `data/` 和本地工具链；
- 运行 Blender、Crowbar、`studiomdl`、MIGI、Python 测试和其他只能在用户机器执行的操作；
- 按 Chat/Sol 已经固定好的测试协议执行；
- 保存 command、stdout/stderr、exit code、run id、hash、report；
- 将允许上传的代码/报告/证据提交到 GitHub；
- 遇到失败按 `BLOCKED` / `INVALID` / `EXECUTION_FAIL` 如实返回。

Luna **不是默认独立 Reviewer**。不得因为看到 `RV-01～RV-06`、`REVIEW_PENDING` 或“需要 Review”就自行开始完整 Review，更不得自行把 P4 标成 `PASS / FROZEN`。

### 1.2 Codex Sol

Codex Sol 默认也**不承担本项目的独立 Review**。

只有用户明确说出类似以下指令时，Codex Sol 才进入额外独立审计模式：

- “用 Codex Sol 做一次独立 review”；
- “让 Codex Sol 做 milestone audit”；
- 其他同等明确、指定 **Codex Sol** 为 Reviewer 的指令。

否则：

- 不要因为模型能力更强就主动接管 Chat/Sol Review；
- 不要重复 Chat/Sol 已经完成或正在进行的 Review；
- 不要把 Codex Sol 审计当成 P4 的默认必选 Gate。

如用户显式要求 Codex Sol 审计，结果必须标记为 `CODEX_SOL_AUDIT`，与 `CHAT_REVIEW.md` 中的 Chat/Sol Review 分开记录。

---

## 2. 当前 P4 状态

截至 2026-08-20 当前 `master`：

- P4-T01～T07：自动技术闭环已完成；
- P4-T08：`passed_user_confirmed`；
- 当前 addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
- 当前 frozen/no-op run：`run_20260819_170013_270792`；
- 用户已确认按 F 后无崩溃/明显运行错误，状态能返回，并可继续射击、换弹、切枪；
- 真正可见 Inspect、手指穿模、Blender retarget 属于 P7，不是 P4 blocker；
- 当前 P4 总状态：`REVIEW_PENDING / NOT_YET_FROZEN`；
- **默认下一步是 Chat/Sol 执行 RV-01～RV-06 Review，而不是 Luna 自行 Review。**

因此，在没有新的 Chat 任务或用户明确要求前，Codex/Luna 的默认动作是：**不要继续改 P4 实现。**

---

## 3. Codex 启动顺序

每次开始新任务时按以下顺序：

1. 读取 `AGENTS.md`；
2. 读取 `plan.md` 第 1 节；
3. 读取 `P4_STATUS.md`（若当前仍处于 P4）；
4. 读取本文件 `CODEX_TASKS.md`；
5. `git status --short --branch`；
6. 在 tracked 工作区可安全同步时执行 `git fetch origin` + `git pull --rebase origin master`；
7. 再执行用户或 Chat/Sol 明确交付的本地任务。

不要把聊天记忆、旧日志、旧分支或旧 MOD 当作当前任务源。

---

## 4. Chat → Codex 的测试委托协议

当 Chat/Sol Review 需要本地执行（典型是 RV-04），Codex/Luna 只执行 **已经固定的 Test Spec**。

每个 Test Spec 至少必须包含：

```text
test_id
purpose / hypothesis
baseline
input identity / hash
mutation or operation
must_preserve invariants
exact command / action
expected failing gate or expected result
PASS criteria
FAIL criteria
INVALID criteria
required evidence
forbidden changes
```

Luna 执行规则：

1. 不改变 test target；
2. 不降低 acceptance criteria；
3. 不把难做的 mutation 换成更简单但不同语义的 mutation；
4. 不修改生产 Gate 来让测试通过；
5. unrelated error 时标记 `INVALID`，不是 PASS；
6. 完成后只返回原始证据和执行事实，不替 Chat/Sol 做最终 Reviewer 判定。

### 4.1 RV-04 的最低本地执行范围

如果 Chat/Sol 委托当前 P4 的 RV-04，至少执行 4 个高风险反例，且必须覆盖：

1. 路径越界 / 递归删除安全；
2. sequence 或 attachment 的“数量不变但语义错误”；
3. mesh / bone mapping 错误；
4. material closure 或 provenance 错误。

具体 mutation、命令和验收由 `CHAT_REVIEW.md` 的 Reviewer 在执行前固定；Luna 不自行选择替代测试。

---

## 5. 本地证据要求

环境依赖任务优先保存：

```text
run_id
git_commit
input_relative_path
input_sha256
command
cwd
exit_code
stdout/stderr log
output hashes
report path + report hash
tool version
```

涉及 `data/` 时：

- 可以记录相对路径、SHA-256、size、ID；
- 不上传原始 `data/**`；
- 不把 hash 误写成对资产语义正确性的证明。

Codex/Luna 允许输出的最终状态主要是：

- `EXECUTOR_DONE`
- `BLOCKED`
- `INVALID`
- `EXECUTION_FAIL`

**不要输出 `REVIEW_PASS`、`P4_FROZEN` 或等价最终 Reviewer 结论，除非用户明确把 Codex Sol 指定为独立 Reviewer。**

---

## 6. Git / 上传 / 拉取

完整规则见 `AGENTS.md`。本文件再次强调当前项目最重要的边界：

- `data/**` 永远本地-only，不上传、不删除；
- GitHub 没有 `data/` 不等于本地应删除；
- pull 前先看 `git status`；
- 本地和远端同一 tracked 文件都改过时停止自动合并并报告冲突；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .`、`git add -A`、`git add --all`；
- 默认禁止 `git reset --hard`、`git clean -fd`、`git clean -fdx`、`git restore .`、`git checkout -- .`；
- 不 force-push；
- 不用 mirror/delete 同步方式破坏本地 ignored 数据。

---

## 7. 当前 P4 已完成执行事实（供 Codex 定位，不是 Review 结论）

- T01：现场隔离 / 权威状态修正；
- T02：manifest 契约、tool/input hash、输出路径安全、deploy guard；
- T03：manifest LTB → B3 → C1 → C3 fresh run；
- T04：Source 1 单入口 build、隔离 `studiomdl`、Crowbar roundtrip；
- T05：15 个自动语义 Gate；
- T06：package / staging / explicit deploy hash/provenance 闭环；
- T07：17 个负向 mutation 17/17 被预期 Gate 拒绝 + 双正向 run 语义复现；
- T08：frozen/no-op changed-runtime 用户 Gate 已确认；
- T09：文档预收口完成，最终冻结等待 Chat/Sol Review。

主要证据位于：

```text
work/m4a1_s_bornbeast/p4_prototype_01/
  check_report.json
  build_report.json
  validation_report.json
  upstream_trace_report.json
  manifest_contract_report.json
  negative_test_report.json
  reproducibility_report.json
  package_manifest.json
  deploy_report.json
  prototype_01_game_regression.json
```

---

## 8. 当前默认停止条件

在 `CHAT_REVIEW.md` 没有产生新的本地执行委托前：

> **Codex/Luna 停止继续实现 P4，不自行做 RV-01～RV-06，不重新做 Inspect retarget。等待 Chat/Sol Review 或用户新的明确任务。**
