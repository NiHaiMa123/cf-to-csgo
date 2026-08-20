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
- P5：**ACTIVE — 最终雷神资产定位**；
- 当前任务：**P5-T01 READY_FOR_LUNA**；
- 当前正式协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)；
- P5-T02：`BLOCKED_BY_T01_USER_REFERENCE`；
- 历史本地广召回：[`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)，可在 T02 复用；
- P4 visible Inspect / 手指 retarget 属于 P7，不是当前任务。

---

## 2. Luna 默认角色

角色：**本地执行器 + Web reference finder + 用户 Gate 交互执行器 + 证据生产器**。

Luna 负责：

- 安全拉取最新 `master`；
- 严格执行当前 Task Spec；
- 使用 Harness 的 Web Search / 浏览器能力搜索 CF 官方 reference；
- 把真实网络图片展示给用户；
- 在用户 Gate 等待明确确认；
- 确认后在同一任务链继续后续阶段；
- 读取本地 `data/**`、运行本地 parser/Blender/Python 等；
- 保留命令、hash、报告和派生预览；
- `data/**` 原始资产永远不上传。

Luna 不是最终 Reviewer，不得：

- 生成目标 reference 图；
- 用模型记忆代替 Web Search；
- 把第三方图片冒充官方图；
- 未经用户确认就开始本地视觉锁定；
- 自行写最终 `IDENTITY_CONFIRMED`；
- 修改 P4 frozen pipeline。

---

## 3. 当前 P5 编号

```text
P5-T01  官方图鉴 Web Search + 用户确认目标图
P5-T02  本地候选缩圈/去重/百科式侧视图 + 用户确认本地候选
P5-T03  Resource Graph / provenance closure
P5-T04  Chat/Sol final identity review
```

此前以旧 `P5-T01` 名义完成的本地广召回现在统一视为：

```text
LEGACY PRE-SCAN
```

其输出不作废，但不再决定当前任务编号。详见 `P5_LEGACY_PRE_SCAN.md`。

---

## 4. 每次启动顺序

1. 读取 `AGENTS.md`；
2. 读取 `plan.md` 第 1 节；
3. 读取本文件 `CODEX_TASKS.md`；
4. 读取 `P5_TASKS.md`；
5. 当前先读取 `P5_T01_TASK_SPEC.md`；
6. `git status --short --branch`；
7. tracked 工作区可安全同步时执行 `git fetch origin` + `git pull --rebase origin master`；
8. 从 P5-T01 Mandatory Web Search 开始。

不要把聊天记忆、旧分支、旧 MOD、历史别名猜测或旧 candidate score 当作 authoritative identity。

---

## 5. P5-T01 — 必须先搜官网图鉴

Luna 必须实际 Web Search：

```text
M4A1-雷神 CF 武器百科
site:cf.qq.com/cp/a20250701wqbk M4A1 雷神
site:cf.qq.com/cp/a20250701wqbk "M4A1-雷神"
```

目标：

```text
official detail page
itemid（若可取得）
display name
actual image URL loaded by official page
```

普通搜索找不到时，可打开官方首页、使用站内功能、检查 HTML/JS/Network。

找到候选后必须给用户展示：

```text
官方名称
官方详情页 URL
itemid
官方图片 URL
真实图片预览
```

然后等待：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
```

用户否决时继续同一个 T01 的搜索；不需要回 Chat 改 Plan。

用户确认后生成 T01 evidence，并可直接进入 T02。

---

## 6. P5-T02 — 用户确认官网图后直接继续

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

T02 必须读取 T01 confirmed reference，然后：

```text
复用 LEGACY PRE-SCAN candidate index/matrix
  -> M4/M4A1 PLAYERVIEW 缩圈
  -> 排除 BL/GR/WOMAN/纯手臂/QV
  -> exact SHA 去重
  -> geometry cluster（可用时）
  -> 每 cluster 1 个 representative
  -> 本地 diffuse/主纹理 + UV
  -> 百科式正交侧视 PNG
  -> contact sheet / Top shortlist
  -> 给用户看本地候选
  -> 等用户确认
```

第二个正常等待状态：

```text
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

用户确认后只能写：

```text
USER_VISUAL_MATCH_CONFIRMED
```

不能写最终 `IDENTITY_CONFIRMED`。

---

## 7. 最简侧面图原则

```text
1 unique candidate = 1 orthographic side PNG
768x384 或 1024x512
透明/白背景
统一方向/fit
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
无 Cycles
```

优先把本地 diffuse/主颜色贴图按原模型 UV 应用到枪体后再截图。

如果纹理暂时不可解析，可以用灰模做廉价排除，但不能仅凭灰模最终确认。

---

## 8. Git / data 规则摘要

完整规则见 [`AGENTS.md`](AGENTS.md)。特别强调：

- `data/**` 永远 local-only；
- pull 前检查 `git status`；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .`、`git add -A`、`git add --all`；
- 默认禁止 destructive Git clean/reset；
- 不 force-push；
- 不使用 mirror/delete 同步破坏 ignored 本地资产。

---

## 9. 返回 Chat/Sol 的条件

正常用户确认 Gate 不需要返回 Chat/Sol。

只有以下情况才返回：

- `BLOCKED_WEB_SEARCH_UNAVAILABLE`；
- `BLOCKED_OFFICIAL_REFERENCE_NOT_FOUND`；
- T02 本地 export/texture/preview pipeline 真正阻塞；
- Task Spec 需要修改；
- 出现 INVALID 条件；
- 完成 T02 全部 evidence，需要进入 T03/T04 Review。
