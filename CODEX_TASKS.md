# CODEX_TASKS.md — Codex / Luna 本地执行合同

> 本文件只给 **Codex 环境中的 Agent** 使用，包括 Luna、本地执行 Agent，以及用户明确调用时的 Codex Sol。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = Luna / 普通 Codex Agent。**

---

## 1. 当前阶段

截至 2026-08-20：

- P4：**PASS / FROZEN**；
- P5：**ACTIVE**；
- P5-T01：**EXECUTION_PASS / REVIEWED**；
- P5-T02：**BLOCKED_BY_USER_REFERENCE_CONFIRMATION**；
- 当前正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

---

## 2. Luna 默认角色

Luna = **本地执行器 + 证据生产器**。

可以：

- 安全 pull 最新 master；
- 读取本地 `data/**`；
- 在 Task Spec 明确允许后执行扫描、解析、Blender、Python 等本地任务；
- 生成 path/hash/report/派生预览；
- push allowlist 内证据。

不得：

- 自行 Review P4；
- 自行决定哪张 Web 图片就是目标；
- 代替用户通过 reference confirmation Gate；
- 根据英文 alias / 文件名 / T01 score 宣布某候选就是雷神；
- 自行进入下一阶段；
- 修改 P4 frozen pipeline；
- 上传 `data/**`。

---

## 3. 当前强制停止条件

当前 P5-T02 尚未通过：

```text
USER_REFERENCE_CONFIRMATION_GATE
```

因此 Luna 当前唯一正确行为是：

```text
git pull latest master
 -> read AGENTS.md
 -> read CODEX_TASKS.md
 -> read P5_TASKS.md
 -> read P5_T02_TASK_SPEC.md
 -> observe BLOCKED_BY_USER_REFERENCE_CONFIRMATION
 -> DO NOT scan
 -> DO NOT export
 -> DO NOT render
 -> DO NOT change files
 -> STOP
```

只有 Chat/Sol 在用户明确说“对，就是这把”后，把 `P5_T02_TASK_SPEC.md` 更新为 `READY_FOR_LUNA`，Luna 才能开始 T02-A。

---

## 4. 用户确认后的 T02-A 预期任务

未来解锁后，Luna 只按正式 spec 执行：

```text
M4/M4A1 PLAYERVIEW candidate narrowing
 -> exclude presentation variants
 -> SHA / geometry dedupe
 -> one representative per unique gun body
 -> gray orthographic side-view PNG
 -> geometry_contact_sheet.png
 -> push
 -> STOP for Chat/Sol review
```

第一轮不做全量贴图、Shader、IK、动作、Source retarget。

---

## 5. Git / data 安全摘要

完整规则见 [`AGENTS.md`](AGENTS.md)。特别强调：

- `data/**` 永远 local-only；
- pull 前检查 `git status`；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `git add -A` / `git add --all`；
- 禁止默认 destructive Git 操作；
- 不 force-push；
- 不 mirror/delete ignored 本地资产。

---

## 6. Codex Sol

Codex Sol 只有用户明确点名做额外 audit/review 时才进入审计模式；默认不替代 Chat/Sol，也不能绕过 USER_REFERENCE_CONFIRMATION_GATE。
