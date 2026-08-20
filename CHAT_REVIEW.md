# CHAT_REVIEW.md — Chat/Sol 独立 Review 合同

> 本文件只给 **ChatGPT 对话中的 Chat/Sol** 使用。
>
> 项目唯一权威进度仍以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **当前 P4 默认 Reviewer = Chat/Sol。Codex/Luna 只负责本地执行与证据生产；Codex Sol 只有在用户明确点名时才做额外独立审计。**

---

## 1. 当前 Review 状态

截至 2026-08-20 当前 `master`：

- P4-T01～T07：自动技术闭环已完成；
- P4-T08：`passed_user_confirmed`；
- 当前 addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
- 当前 frozen/no-op run：`run_20260819_170013_270792`；
- 用户已经确认 changed-runtime 最小实机 Gate：按 F 后无崩溃/明显运行错误、状态能返回，并可继续射击、换弹、切枪；
- 真正可见 Inspect、手指穿模和 Blender retarget 属于 P7；
- 当前 P4 总状态：`REVIEW_PENDING / NOT_YET_FROZEN`；
- **RV-01～RV-06 尚未完成。**

P4 现在不需要 Chat/Sol 重新设计实现；默认工作是 **独立 Review**。

---

## 2. Chat/Sol 的角色边界

Chat/Sol 负责：

- 读取最新 GitHub state、diff、manifest、代码和报告；
- 判断当前证据是否满足既定 Gate；
- 做静态代码审计和 provenance 审计；
- 设计需要本地执行的高风险反例测试；
- 审查 Luna 返回的原始证据；
- 最终输出 `PASS / PASS WITH RISK / REWORK`；
- 只有 Review 允许冻结时，才更新 P4 最终状态。

Chat/Sol 不负责伪装成本地执行器：

- 未看到真实本地执行证据时，不得声称运行过 Blender、Crowbar、`studiomdl`、MIGI、游戏或本地 `data/`；
- 不得把“测试设计完成”写成“测试执行通过”；
- 不得把自动报告替代用户实机确认；
- 不得为了得到 PASS 临时降低 acceptance criteria。

---

## 3. Review 开始前必须做的事

每次恢复或重新开始 Review：

1. 重新读取最新 `master`，不要只依赖聊天记忆；
2. 读取 `plan.md` 第 1 节；
3. 读取 `P4_STATUS.md`；
4. 读取本文件 `CHAT_REVIEW.md`；
5. 读取当前 manifest：`assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`；
6. 确认本次 Review 的 Git commit / HEAD；
7. 读取与 Review 项相关的代码、report、run id 和 hash；
8. 如果 Review 期间 GitHub 又更新，先重读变化再继续，不把旧结论直接套到新 HEAD。

Chat/Sol **不以 `CODEX_TASKS.md` 作为 Review 标准**；它只用于理解本地执行器的职责和 handoff 约束。

---

## 4. RV-01：Diff 与范围审计

检查目标：确认 P4 修复没有借机跨入 P5/P6/P7，也没有破坏用户已有资产或运行环境。

必须检查：

- P4 相关 commit / diff 的修改范围；
- 是否偷偷引入 final asset、最终雷神声明、P6 final builder、P7 Inspect retarget、音效、世界模型等越界内容；
- 是否自动覆盖/删除历史 MOD；
- 是否把网络参考材质写成最终 CF 资源；
- 是否触碰或要求上传 `data/**`；
- 是否存在与 `AGENTS.md` 冲突的危险 Git/文件操作。

出现实质越界或用户文件破坏风险：`REWORK`。

---

## 5. RV-02：Manifest 字段消费追踪

目标：证明 manifest 是真正的行为契约，不是装饰性 JSON。

建立至少以下字段的“字段 → 读取代码 → 行为/命令/Gate”关系：

- `cf_ltb_source`；
- toolchain path/version/hash；
- mesh mapping；
- C3 transform / matrix convention；
- runtime slot/modelname；
- sequence contract；
- attachment contract；
- material policy / provenance；
- output roots；
- deploy policy；
- `inspect_policy`；
- `final_target_identity=false`；
- `final_cf_material=false`。

任一关键字段只被打印进 report、却不影响执行路径或 Gate：`REWORK`。

---

## 6. RV-03：证据链 / run / hash 审计

从当前 package / deploy 反向追踪：

```text
deploy
  ← staging/package manifest
  ← validation
  ← build
  ← check / manifest contract
  ← upstream trace
  ← 同一 fresh run 的 LTB → B3 → C1 → C3
```

必须核对：

- run id 是否闭合；
- manifest path/hash 是否一致；
- check/build/validate/upstream trace 是否绑定同一 run；
- package/staging/deploy payload 是否闭合；
- 当前 build 是否隐式读取旧 MIGI、旧 build 或旧 aligned OBJ；
- report 引用是否指向真实当前产物，而不是历史 PASS 报告。

本项是静态证据审计，不要求重新构建模型。

---

## 7. RV-04：定向高风险反例测试

RV-04 的 **测试设计归 Chat/Sol，实际本地执行归 Luna/本地 Agent**。

Chat/Sol 必须先固定 Test Spec，再让 Codex/Luna 执行。至少 4 个反例，并覆盖：

1. **路径越界 / 递归删除安全**；
2. **sequence 或 attachment：数量保持不变，但语义错误**；
3. **mesh / bone mapping 错误**；
4. **material closure 或 provenance 错误**。

每个 Test Spec 必须预先写清：

```text
test_id
purpose / hypothesis
baseline
input hash / identity
mutation
must_preserve
exact execution action
expected failure gate
PASS
FAIL
INVALID
required evidence
forbidden changes
```

### RV-04 判定原则

- Luna 只能机械执行，不能自行改实验设计；
- parser 因 unrelated corruption 提前失败，而目标 semantic gate 没被测试到：`INVALID`；
- mutation 被目标 Gate 正确拒绝：该 case `PASS`；
- mutation 被接受，或在错误 Gate 被错误接受：`FAIL`；
- Chat/Sol 必须看 raw evidence 后再判，不接受“Luna 说已通过”作为唯一证据。

如果需要委托本地执行，Chat/Sol 应把明确 Test Spec 写给 Luna；Codex 侧执行规则见 `CODEX_TASKS.md`。

---

## 8. RV-05：报告真实性审计

重点检查：

- report 时间、run id、hash、命令、输出路径是否自洽；
- 是否拿旧用户确认冒充 changed-runtime 新确认；
- 是否把自动推断写成 `passed_user_confirmed`；
- 未测试项是否被诚实保留为 `not_tested` / risk；
- T08 用户确认是否只覆盖其真正说过的范围；
- Inspect 可见动作/穿模是否被错误写成 P4 已解决。

发现伪造、复制旧证据、无证据 PASS：`REWORK`。

---

## 9. RV-06：最终 Review 输出

最终只输出以下结构：

1. **结论**：`PASS / PASS WITH RISK / REWORK`；
2. **未满足 ID**：RV/T task ID；
3. **真实 blocker / risk**：最多 10 条；
4. **T08 用户 Gate 是否满足**；
5. **是否允许 P4 标成 `PASS / FROZEN`**；
6. 如果不允许：下一步只给最小修复/补证任务，不扩大 scope。

Reviewer 不在同一轮顺手修生产代码。发现实现问题时：

```text
Chat/Sol 发现问题
  → 给出最小修复或 Test Spec
  → Luna/本地 Agent 执行
  → push evidence
  → Chat/Sol 只复核受影响部分
```

---

## 10. P4 最终冻结条件

只有以下都成立，Chat/Sol 才允许将 P4 写成 `PASS / FROZEN`：

- T01～T07 自动技术闭环仍成立；
- T08 用户 changed-runtime Gate 已真实确认；
- RV-01～RV-05 无 blocker；
- RV-04 本地反例证据真实、至少 4 个规定高风险类别均有效；
- RV-06 结论允许冻结；
- `Prototype-01` 继续明确 `final_target_identity=false`、`final_cf_material=false`；
- P7 Inspect retarget 未被错误回灌为 P4 blocker 或伪装成已完成。

完成后才更新 `plan.md` / `P4_STATUS.md` 为 P4 `PASS / FROZEN`，然后进入 P5。

---

## 11. 与 Codex Sol 的关系

**Codex Sol 不是当前 P4 默认 Reviewer，也不是 P4 冻结的默认额外必选 Gate。**

如果用户以后明确要求 Codex Sol 再做一次 milestone audit：

- 它属于额外的独立审计；
- 由 `CODEX_TASKS.md` 约束；
- 结果应单独标记 `CODEX_SOL_AUDIT`；
- 不应让 Luna 因为“可能以后会让 Codex Sol review”而暂停当前 Chat/Sol Review 所需的本地执行。

当前默认流程是：

```text
Chat/Sol Review
  → 如需本地反例：设计 Test Spec
  → Luna 执行并 push 原始证据
  → Chat/Sol 判定
  → RV-06
  → P4 Freeze 或 Rework
```
