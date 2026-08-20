# P4_TASKS.md — P4 冻结入口 / 角色路由

> P4 已于 2026-08-20 完成独立 Review，最终结论为 **`PASS WITH RISK`**，项目状态为 **`PASS / FROZEN`**。
>
> 本文件不再作为待执行 P4 Task 清单；它只保留角色路由和冻结入口。

## P4 最终状态

- P4-T01～T09：完成；
- T08：`passed_user_confirmed`；
- RV-01：PASS；
- RV-02：PASS WITH NON-BLOCKING RISK；
- RV-03：PASS；
- RV-04：PASS，4/4 独立反例；
- RV-05：PASS WITH NON-BLOCKING RISK；
- RV-06：`PASS WITH RISK`；
- P4：**`PASS / FROZEN`**。

详细证据：

- [`P4_STATUS.md`](P4_STATUS.md)
- [`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)
- [`P4_RV04_TEST_SPECS.md`](P4_RV04_TEST_SPECS.md)
- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`

项目唯一 authoritative progress/status 仍是 [`plan.md`](plan.md) 第 1 节。

---

## 角色路由

### Codex / Luna / 本地 Agent

读取并遵守：[`CODEX_TASKS.md`](CODEX_TASKS.md)

默认角色：**本地执行器 / 证据生产器**。

- 不自行重新打开 P4；
- 不自行做新的 P4 Review；
- 不因为 P5 资产识别或 P7 Inspect 问题修改 P4 frozen baseline；
- 只执行用户或 Chat/Sol 明确交付的 P5/P6/P7 本地任务。

### ChatGPT Chat / Sol

读取并遵守：[`CHAT_REVIEW.md`](CHAT_REVIEW.md)

默认角色：**Planner / Test Designer / Reviewer**。

当前 active work 已转入 P5：最终雷神资产定位。

### Codex Sol

Codex Sol 不是默认额外 Gate。只有用户明确要求“Codex Sol 独立 review / milestone audit”时才执行额外审计，并与 Chat/Sol Review 分开记录。

---

## P4 冻结边界

P4 frozen/no-op 只证明转换技术链与 changed-runtime 安全，不证明：

- 当前候选是最终雷神；
- 当前网络参考材质是最终 CF 材质；
- visible Inspect / 手指 retarget 已解决；
- CF 原动画/声音/世界模型已最终化。

这些属于 P5/P6/P7，不能作为理由回滚 P4。

所有 Agent 继续遵守根目录 [`AGENTS.md`](AGENTS.md) 的 Git 同步与 `data/` 本地保护规则。
