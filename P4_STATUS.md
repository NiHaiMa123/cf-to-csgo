# P4 当前状态

> 项目唯一权威进度仍以 [plan.md](plan.md) 第 1 节为准。本文件保留 P4 最终 Review 快照。

更新时间：2026-08-20

## 最终结论

- P4-T01～T07：完成。
- P4-T08：`passed_user_confirmed`。
- P4-T09：完成。
- RV-01：`PASS`。
- RV-02：`PASS WITH NON-BLOCKING RISK`。
- RV-03：`PASS`。
- RV-04：`PASS`，4/4 独立高风险反例命中预定 Gate。
- RV-05：`PASS WITH NON-BLOCKING RISK`。
- RV-06：**`PASS WITH RISK`**。
- P4 总状态：**`PASS / FROZEN`**。
- 当前 active phase：**P5 — 最终雷神资产定位**。

完整最终 Reviewer 记录：[`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)。

## 冻结实现与证据

- Implementation baseline：`10aa99b770e575300ca3c28324ef3de3d5b70c6b`
- frozen/no-op build run：`run_20260819_170013_270792`
- RV-04 evidence commit：`fd61d6ae7567a01c585e1144e2cab88ddb6aa85d`
- 当前 addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`
- Runtime slot：M4A4
- Internal model：`weapons/v_rif_m4a1.mdl`
- Inspect policy：`frozen_noop_safe`
- `final_target_identity=false`
- `final_cf_material=false`

P4 冻结意味着：Prototype 的转换技术流水线满足当前 DoD，可以作为 P5/P6 的稳定技术基线。**不意味着当前候选就是最终雷神，也不意味着最终 CF 材质、可见 Inspect retarget、手指接触或 CF 原动画已经完成。**

## 用户 Gate

用户已确认当前 frozen/no-op addon：

- 按 F 后没有崩溃或明显运行错误；
- 无可见 Inspect 动作符合 frozen/no-op 预期；
- 武器状态正常返回；
- 之后仍可射击、换弹、切枪。

仍明确保留：

- `console_errors = not_tested`；
- `rollback_after_disable = not_tested`；
- visible Inspect / Blender retarget / 手指穿模 = P7。

这些在 RV-06 中被判为非阻塞风险，不得以后改写成“已经测试通过”。

## RV-04 独立反例

Chat/Sol 固定 Test Spec，Luna 只负责本地机械执行。新证据：

- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`
- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log`

结果：

1. output root containment -> `manifest_contract`：PASS；
2. sequence 数量不变、名称错误 -> `sequence_names_and_count`：PASS；
3. Parent/Clip mapping 语义交换 -> `smd_manifest_bone_corners`：PASS；
4. 缺失关键 VTF -> `material_closure`：PASS。

`case_count=4`、`passed_cases=4`、`pass=true`，且 Review 执行前后没有 P4 核心实现 diff。

## 冻结时保留的非阻塞风险

1. CLI `--inspect-policy` 仍可显式 override manifest 默认策略；T05 尚未独立锁死 effective policy 必须等于 manifest policy。
2. toolchain contract 尚未完全 manifest-driven；部分实际工具由 pipeline 路径解析并通过 run evidence 追踪。
3. 控制台清洁度没有单独用户确认。
4. addon 停用后的 rollback 没有单独用户确认。
5. Windows working-tree SHA 与历史 build/package 中的 manifest byte SHA 存在差异；Git 比较未发现 manifest 语义修改，后续 provenance 最好增加规范化 hash / Git blob identity，消除 EOL 类字节差异歧义。

以上均不阻塞进入 P5，但不能被静默删除或描述成已解决。

## 角色路由

- Codex / Luna：读取 [`CODEX_TASKS.md`](CODEX_TASKS.md)，只执行用户或 Chat/Sol 明确交付的本地任务。
- Chat/Sol：读取 [`CHAT_REVIEW.md`](CHAT_REVIEW.md)，负责 P5 计划、任务拆分、证据审查和后续阶段 Review。
- Codex Sol：只有用户明确点名做额外 milestone audit 时才进入独立审计；不是默认 Gate。

## 下一步

P4 不再继续实现。下一步转入 P5：

```text
Chat/Sol 定义 P5 资产定位任务和验收
  -> Luna 在本地 data/** 中扫描/提取候选
  -> 只上传候选路径、hash、缩略/报告等允许证据，不上传 data 原资产
  -> Chat/Sol 比对候选与雷神参考特征
  -> 锁定最终模型/贴图/Shader/声音来源
  -> P5 Gate
```

除非新证据证明 P4 frozen contract 本身有回归，否则不得为了 P5 资产识别或 P7 Inspect 视觉问题重新打开 P4。
