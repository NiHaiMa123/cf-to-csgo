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
- P5-T01：**EXECUTION_PASS / REVIEWED**；
- P5-T02：**READY_FOR_LUNA**；
- P5 任务流：[`P5_TASKS.md`](P5_TASKS.md)；
- 当前正式执行协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)；
- P4 visible Inspect / 手指 retarget 属于 P7，不是当前任务；
- P4 frozen baseline 不得因为 P5/P7 问题被自行重写。

---

## 2. Luna / 普通 Codex Agent 的默认角色

角色：**本地执行器 + Web reference finder + 用户 Gate 交互执行器 + 证据生产器**。

Luna 负责：

- 安全拉取最新 `master`；
- 严格执行当前 Task Spec；
- 使用 Harness 自带 Web Search / 浏览器能力搜索官方 reference；
- 在 Task Spec 指定的用户 Gate 把真实网络图片/本地派生预览展示给用户；
- 等待用户确认后在**同一个 Task Spec** 中继续后续阶段；
- 读取本地 `data/**` 和本地工具链；
- 运行扫描、解析、Blender、Python 等只能在用户机器执行的工作；
- 保留 command、stdout/stderr、exit code、hash、report；
- 只提交允许上传的派生证据；
- `data/**` 原始资产永远不上传。

Luna **不是默认最终 Reviewer**，不得自行：

- 把某个 P5 candidate 写成最终 `IDENTITY_CONFIRMED`；
- 降低 Chat/Sol 已设定的 acceptance criteria；
- 修改 P4 frozen pipeline；
- 用聊天记忆覆盖仓库 Task Spec。

---

## 3. 当前最重要的流程纠正

之前曾出现“由 Chat 先猜某个英文内部资源族，再让 Luna 验证”的路径。这个流程从现在起废止。

P5-T02 的正确流程是：

```text
Luna Web Search
  -> CF 官方武器百科
  -> Luna 找到官网真实武器图片
  -> Luna 给用户看
  -> USER REFERENCE GATE
  -> 用户确认后 Luna 继续
  -> 本地候选缩圈 / 去重
  -> 最简百科式贴图正交侧视图
  -> USER LOCAL-CANDIDATE GATE
  -> push evidence
  -> STOP
```

因此：

- Luna **必须 Web Search**，不能仅使用模型记忆；
- 官网图鉴 `https://cf.qq.com/cp/a20250701wqbk/index.html` 是目标 reference 的强制官方入口；
- 给用户看的图必须是从网页找到的真实图片，**不得生成图片**；
- `Transformers`、`BornBeast`、`Thor`、`Leishen` 等 token 只是候选线索，不是预先确认的身份；
- 用户确认 Gate 属于执行流程，不需要返回 Chat/Sol 逐次改 Plan。

---

## 4. 每次启动顺序

1. 读取 `AGENTS.md`；
2. 读取 `plan.md` 第 1 节；
3. 读取本文件 `CODEX_TASKS.md`；
4. 读取 `P5_TASKS.md`；
5. 读取当前默认 Task Spec：`P5_T02_TASK_SPEC.md`；
6. `git status --short --branch`；
7. tracked 工作区可安全同步时执行 `git fetch origin` + `git pull --rebase origin master`；
8. 从 `P5_T02_TASK_SPEC.md` Phase A 开始执行。

不要把聊天记忆、旧分支、旧 MOD、历史报告或本地未提交实验当作 authoritative task source。

---

## 5. P5-T02 Phase A：必须先搜官网图鉴

Luna 必须先 Web Search：

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

普通搜索引擎找不到时，允许打开官方首页、使用站内功能、检查 HTML/JS/Network 请求。

第三方页面可以帮助发现线索，但 USER REFERENCE GATE 必须使用官方 `cf.qq.com` 详情页及其实际加载图片。

找到候选后，在 Codex 对话中显示：

```text
官方名称
官方详情页
itemid
原始图片 URL
真实图片预览
```

禁止调用图片生成工具创建“参考图”。

然后停止在：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
```

这不是 BLOCKED。

---

## 6. 用户确认后直接继续，不回 Plan 端

用户明确确认目标官方图片后，Luna **直接继续** P5-T02 Phase B/C/D：

1. 复用 T01 candidate index/matrix；
2. 聚焦 M4/M4A1 `PLAYERVIEW` 第一人称候选；
3. 排除/归档 `_BL`、`_GR`、`WOMAN`、纯手臂、QV/第三人称；
4. exact SHA 去重；
5. 可用时 geometry signature 聚类；
6. 每个 unique cluster 首轮只渲染一个 representative；
7. 首轮只做一张标准正交侧面图；
8. 优先应用本地真实 diffuse/主颜色纹理；
9. 做 contact sheet / visual shortlist；
10. 把本地 Top candidates 给用户看，执行第二个用户 Gate。

用户确认某个本地 candidate 后，只能写：

```text
USER_VISUAL_MATCH_CONFIRMED
```

不能写最终 `IDENTITY_CONFIRMED`。

---

## 7. 最简侧面图原则

目标是类似武器百科的侧面表达，不是漂亮渲染。

首轮：

```text
1 candidate = 1 orthographic side PNG
768x384 或 1024x512
透明/白背景
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
```

优先路径：

```text
LTB weapon mesh
  + UV
  + 本地 CF diffuse/主纹理
  -> 临时可渲染纹理
  -> 标准侧面 PNG
```

如果纹理暂时不可解析，可以用灰模/轮廓做便宜排除，但不能凭灰模完成最终锁定。

不要首轮生成四视图，不要用 Cycles，不要做艺术灯光。

---

## 8. Git / data 规则

完整规则见 [`AGENTS.md`](AGENTS.md)。特别强调：

- `data/**` 永远 local-only；
- GitHub 没有 `data/` 不等于本地应该删除；
- pull 前检查 `git status`；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .`、`git add -A`、`git add --all`；
- 默认禁止 `git reset --hard`、`git clean -fd`、`git clean -fdx`、`git restore .`、`git checkout -- .`；
- 不 force-push；
- 不使用 mirror/delete 同步破坏 ignored 本地资产。

---

## 9. 当前默认停止条件

P5-T02 是交互式多阶段任务。

在以下两个状态，Luna应**等待用户**，而不是返回 Chat 重新设计：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

只有以下情况才返回 Chat/Sol：

- `BLOCKED_WEB_SEARCH_UNAVAILABLE`；
- `BLOCKED_OFFICIAL_REFERENCE_NOT_FOUND`；
- 本地 candidate/export/texture pipeline 真正阻塞；
- Task Spec 需要修改；
- 出现 INVALID 条件。

完成两个用户 Gate 和全部 T02 evidence 后：

> **只提交 `P5_T02_TASK_SPEC.md` allowlist 内的派生证据，push `master`，然后停止。不得自行进入 T03。**