# P4 当前状态

> 这是一份状态快照；项目唯一权威进度仍以 [plan.md](plan.md) 第 1 节为准。

更新时间：2026-08-20

## 当前结论

- P4-T01～T07：自动技术闭环已完成。
- P4-T08：用户已确认当前 frozen/no-op addon 的最小实机 Gate 没有问题。
- P4-T09：文档预收口已完成，但最终冻结仍等待 RV-01～RV-06 独立 Review。
- 当前 P4 总状态：`REVIEW_PENDING / NOT_YET_FROZEN`。

## Review 角色已经拆分

为避免 Luna、Codex Sol 和 Chat/Sol 混淆职责，原 `P4_TASKS.md` 已改为兼容路由入口，正式工作文件拆成两份：

- **Codex / Luna / 本地执行 Agent：[`CODEX_TASKS.md`](CODEX_TASKS.md)**
  - 默认只负责本地执行、环境操作、测试运行和原始证据生产；
  - Luna 不自行做 RV-01～RV-06 完整 Review；
  - Codex Sol 只有在用户明确点名要求独立审计时才 Review。

- **ChatGPT Chat/Sol：[`CHAT_REVIEW.md`](CHAT_REVIEW.md)**
  - 当前 P4 默认独立 Reviewer；
  - 负责 RV-01～RV-06、测试设计、证据审查和最终冻结建议；
  - 需要本地测试时，由 Chat/Sol 先固定 Test Spec，再交 Luna 执行。

因此当前默认下一步是：**Chat/Sol 开始 Review；不是 Luna 或 Codex Sol 自行接管 Review。**

## 用户已确认的范围

当前测试 addon：

`p_cf_bornbeast_m4a4_p4_frozen_noop_01`

用户确认按 F 后：

- 没有崩溃或明显运行错误；
- 没有可见 Inspect 动作符合 frozen/no-op 预期；
- 武器状态正常返回；
- 仍可射击、换弹和切枪。

这次确认不代表可见 Inspect、手指穿模、Blender retarget 或最终雷神资产已经完成；这些仍属于 P7/P5/P6 后续范围。控制台清洁度和停用后的回滚也没有被推断为已测试。

## 已有证据

- 用户实机记录：`work/m4a1_s_bornbeast/p4_prototype_01/prototype_01_game_regression.json`
- 自动构建 run：`run_20260819_170013_270792`
- 自动闭环：build、Crowbar roundtrip、15/15 validation、package、staging、deploy
- Codex 本地执行合同：`CODEX_TASKS.md`
- Chat/Sol Review 合同：`CHAT_REVIEW.md`
- 旧链接兼容入口：`P4_TASKS.md`

## 尚未完成

1. Chat/Sol 的 RV-01～RV-06 独立 Review 尚未完成。
2. RV-04 如果需要本地高风险反例，由 Chat/Sol 设计协议，Luna 执行并上传原始证据，再由 Chat/Sol 判定。
3. 在 Review 无 blocker 后，才可把 `plan.md` 和本状态快照改为 P4 `PASS / FROZEN`。
4. 真正可见 Inspect retarget、手部接触/穿模和最终雷神资产定位不属于当前 P4 收尾。

## 恢复工作时的下一步

```text
Chat/Sol 读取最新 master
  → 按 CHAT_REVIEW.md 执行 RV-01 / RV-02 / RV-03
  → 为 RV-04 设计至少 4 个高风险 Test Spec
  → 如需本地执行，Luna 按 CODEX_TASKS.md 机械执行并 push 证据
  → Chat/Sol 完成 RV-05 / RV-06
  → PASS 则冻结 P4；否则只退回最小修复项
```
