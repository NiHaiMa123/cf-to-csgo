# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 **ChatGPT 对话中的 Chat/Sol** 使用。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；Codex/Luna = 本地执行、Web reference 搜索、用户 Gate 交互与证据生产。**

---

## 1. 当前阶段

截至 2026-08-20：

- P4：**`PASS / FROZEN`**；
- P5：**ACTIVE — 最终雷神资产定位**；
- P5-T01：`EXECUTION_PASS / REVIEWED`；
- P5-T02：`READY_FOR_LUNA`；
- P6：等待 P5 final asset identity；
- P7：visible Inspect / 手臂手指 retarget / CF 原动画等增强范围。

当前 P5 执行入口：

- [`P5_TASKS.md`](P5_TASKS.md)
- [`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)
- [`CODEX_TASKS.md`](CODEX_TASKS.md)

---

## 2. Chat/Sol 的职责

Chat/Sol 负责：

- 维护阶段 Plan / Task Spec / acceptance criteria；
- 读取 Luna push 的 evidence；
- 处理真正的 BLOCKED / INVALID；
- 设计 T03 provenance closure；
- 做 P5-T04 final identity Review；
- 只有证据满足 Gate 后才更新最终 authoritative status。

Chat/Sol 不得：

- 未执行就声称运行过本地 `data/**` / Blender / parser；
- 把文件名/跨服英文名直接升级成 final identity；
- 用聊天记忆覆盖最新仓库状态；
- 为了得到 PASS 临时降低 Gate。

---

## 3. P5 的关键流程边界

“先 Web Search 官网图鉴、给用户看实际目标图、等用户确认”已经固化到 Luna 的 P5-T02 Task Spec。

因此 Chat/Sol **不需要每次替 Luna 手工执行这个流程**。

正确闭环：

```text
Chat/Sol 发布一次明确 Task Spec
  -> Luna Web Search CF 官方武器百科
  -> Luna 展示真实官网图片
  -> 用户确认目标 reference
  -> Luna 本地 candidate 缩圈 / 去重
  -> Luna 生成最简百科式贴图侧视图
  -> Luna 展示本地 shortlist
  -> 用户确认本地视觉候选
  -> Luna push evidence
  -> Chat/Sol 设计/Review T03/T04
```

两个 USER GATE 都属于 Luna 的**同一个交互式执行任务**，不是每次都回 Plan 端写新指令。

---

## 4. Official reference policy

P5 目标图必须优先并强制落到：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

或该官方武器百科的详情页：

```text
https://cf.qq.com/cp/a20250701wqbk/page.html?itemid=<ITEM_ID>
```

Luna 必须 Web Search / 浏览器搜索，而不是仅凭模型记忆。

用户看到的目标图必须是：

- 官方详情页实际加载的网上图片；
- 或该详情页直接引用的腾讯 CDN 图片。

禁止把 AI 生成图、Wiki 图、媒体截图作为 USER REFERENCE GATE 的最终目标图。

第三方资料只能帮助发现关键词/别名，不能单独建立官方 identity anchor。

---

## 5. Local visual identification policy

用户确认官方目标图后，Luna 才开始本地 visual matching。

首轮强调**最低成本**：

```text
T01 index/matrix
  -> M4/M4A1 PLAYERVIEW filter
  -> exclude BL/GR/WOMAN/arms/QV
  -> SHA dedup
  -> geometry cluster
  -> 1 representative / cluster
  -> 1 orthographic side view / representative
  -> apply real local diffuse when available
  -> contact sheet
```

不要首轮做：

- 四视图；
- 动画；
- IK；
- Source retarget；
- Cycles 高质量渲染；
- 大范围 resource graph。

先用视觉把候选锁小，再进入 T03 closure。

---

## 6. P5 Review principle

最终 `IDENTITY_CONFIRMED` 至少需要：

1. 用户确认的官方目标 reference；
2. 用户确认的本地视觉 candidate；
3. 本地 model path + SHA-256；
4. 本地 texture/material path + SHA-256；
5. Shader/CFG/material 关联；
6. 声音/动画/其他同 family 资源至少路径级关联或明确 unresolved；
7. 高相似排除项及排除原因。

`USER_VISUAL_MATCH_CONFIRMED` 仍不是最终 identity；最终结论属于 P5-T04 Chat/Sol Review。

---

## 7. 当前下一步

Chat/Sol 当前不需要再手工找雷神官网图。

> **Luna 读取最新 `P5_T02_TASK_SPEC.md`，从 Mandatory Web Search 开始执行；到两个用户 Gate 时直接与用户交互，完成 T02 后再把证据交回 Chat/Sol。**