# P4_TASKS.md — 兼容入口 / 角色路由

> **不要再把本文件当作一个混合的 P4 Task + Review 清单执行。**
>
> 过去本文件同时写了本地执行任务和独立 Reviewer 任务，导致 Luna / Codex Sol / Chat Sol 容易互相接管职责。自 2026-08-20 起，职责正式拆分。

## 先判断你是谁

### 如果你运行在 Codex / 本地 Agent 环境

包括：

- Luna；
- 普通 Codex Agent；
- 用户明确调用的 Codex Sol。

**读取并遵守：[`CODEX_TASKS.md`](CODEX_TASKS.md)**

默认规则：

- Luna = 本地执行器 / 证据生产器；
- 不要自行执行 RV-01～RV-06 完整 Review；
- 不要自行把 P4 标成 `PASS / FROZEN`；
- Codex Sol 只有在用户明确点名“Codex Sol 独立 review / milestone audit”时才进入额外审计模式。

### 如果你是 ChatGPT 对话中的 Chat / Sol

**读取并遵守：[`CHAT_REVIEW.md`](CHAT_REVIEW.md)**

默认规则：

- Chat/Sol = 当前 P4 默认独立 Reviewer；
- 负责 RV-01～RV-06、测试设计、证据判定和最终冻结建议；
- 需要本地执行时，把精确 Test Spec 交给 Luna；
- 不得把未执行的本地测试写成 PASS。

---

## 当前 P4 状态

项目唯一 authoritative progress/status 仍是 [`plan.md`](plan.md) 第 1 节；简要快照见 [`P4_STATUS.md`](P4_STATUS.md)。

截至当前：

- P4-T01～T07：完成；
- P4-T08：`passed_user_confirmed`；
- P4-T09：预收口完成，最终冻结待 Review；
- 当前总状态：`REVIEW_PENDING / NOT_YET_FROZEN`；
- 真正 Inspect retarget / 手指穿模属于 P7，不是 P4 blocker；
- 默认下一步：**Chat/Sol 按 `CHAT_REVIEW.md` 做 RV-01～RV-06。**

如果 RV-04 需要本地高风险反例：

```text
Chat/Sol 固定 Test Spec
  → Luna / 本地 Codex 执行
  → push 原始证据
  → Chat/Sol 判定 PASS / FAIL / INVALID
```

---

## 历史说明

拆分前的完整 P4 T01～T09 + RV-01～RV-06 混合清单仍保存在 Git 历史中（2026-08-20 之前的 `P4_TASKS.md` 版本），不作为当前 Agent 的角色指令继续执行。

所有 Agent 还必须遵守根目录 [`AGENTS.md`](AGENTS.md) 的 Git 同步和本地 `data/` 保护规则。
