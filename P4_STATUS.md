# P4 当前状态

> 项目唯一权威进度仍以 [plan.md](plan.md) 第 1 节为准。本文件是 P4 的当前 Review 快照。

更新时间：2026-08-20

## 当前总状态

- P4-T01～T07：自动技术闭环已完成。
- P4-T08：`passed_user_confirmed`。
- P4-T09：文档预收口已完成，最终冻结等待 Review。
- P4 当前总状态：`REVIEW_PENDING / NOT_YET_FROZEN`。
- P4 当前实现 Review baseline：`10aa99b770e575300ca3c28324ef3de3d5b70c6b`。
- baseline 之后目前只有 Review 文档提交；RV-04 会先检查 P4 核心实现是否仍与该 baseline 相同。

## Review 角色

- Codex / Luna / 本地执行 Agent：读取 [`CODEX_TASKS.md`](CODEX_TASKS.md)，只负责本地执行和原始证据生产。
- ChatGPT Chat/Sol：读取 [`CHAT_REVIEW.md`](CHAT_REVIEW.md)，是当前默认独立 Reviewer。
- 旧 [`P4_TASKS.md`](P4_TASKS.md) 只作为角色路由入口。
- Codex Sol 只有用户明确点名要求额外 milestone audit 时才做独立审计；不是当前 P4 默认 Gate。

## 用户 Gate

当前 addon：

`p_cf_bornbeast_m4a4_p4_frozen_noop_01`

用户已确认：

- 按 F 后没有崩溃或明显运行错误；
- 无可见 Inspect 动作符合 frozen/no-op 预期；
- 武器状态正常返回；
- 之后仍可射击、换弹、切枪。

`prototype_01_game_regression.json` 仍把控制台清洁度和停用后的 rollback 保留为 `not_tested`，没有把它们伪造成 PASS。可见 Inspect、手指穿模和 Blender retarget 属于 P7，不是 P4 blocker。

## Chat/Sol Review 当前进度

### RV-01 — PASS

范围审计通过：从 `29671c8` 到 implementation baseline / 当前 Review 文档提交，P4 收口修改集中于 P4 pipeline、manifest、P4 build/work 证据与文档；没有把 P5/P6/P7 final builder、最终雷神资产、音效或世界模型重新接入当前 P4 pipeline。当前 deploy report 的动作是创建新 addon，`target_before.file_count=0`，没有用覆盖历史 MOD 制造 PASS。

### RV-02 — STATIC PASS，保留 2 个待 RV-06 判断的风险

已确认：

- `cf_ltb_source` 实际驱动 CFRezManager fresh export，并有输入 hash Gate；
- `mesh_bone_mapping` 实际驱动 C1 expected groups、SMD bone binding、triangle/corner Gate；
- C3 alignment manifest 实际进入 fixed-transform command，matrix/source/target/normal/winding policy 有 contract Gate；
- runtime/modelname、sequence、attachment、material policy、output roots、Prototype flags 都实际影响 Gate / build / package；
- tool/input hash mismatch 会导致 contract 非零失败。

风险：

1. `--inspect-policy` 仍允许显式 CLI override；manifest 的 `frozen_noop_safe` 是默认值，但 T05 当前没有独立 `effective inspect policy == manifest inspect_policy` Gate。当前 frozen artifact 本身正确，但该 override 是否应在 P4 freeze 前进一步硬化，由 RV-06 决定。
2. manifest `toolchain` 中部分历史 builder/validator 主要作为 hash/provenance Gate；实际 `studiomdl` / Crowbar / VTFCmd 和部分 helper 由 pipeline 路径解析并在 run evidence 中记录，而不是全部由 manifest toolchain 字段直接驱动。当前 run provenance 可追踪，但这是通用化前的设计债。

目前未发现会推翻当前 frozen artifact 的静态 blocker。

### RV-03 — PASS

当前证据链闭合到同一 run：

`run_20260819_170013_270792`

已静态核对：

- upstream trace 从本地 CF LTB 开始，记录 LTB / CFRezManager 输入 hash；
- B3 → C1 → C3 四个 upstream step exit code 为 0；
- build report 绑定相同 run id / run root / fresh C3 aligned OBJ；
- validation report 绑定相同 run id，并验证 dependency chain；
- package manifest 绑定相同 build / validate / trace 与 manifest hash；
- package / staging payload tree hash 相同；
- deploy report 绑定相同 run，并逐文件确认 staging == deployed target。

`check_report` 是 manifest-level 检查，没有 run id；package 仍绑定它的文件 hash和当前 manifest，而 build/validate/trace 负责 run-specific provenance。当前没有发现旧 MIGI/旧 build/旧 aligned OBJ 被作为 fresh run 隐式输入。

### RV-04 — READY_FOR_LUNA / NOT EXECUTED YET

精确 Test Spec 已写入：

[`P4_RV04_TEST_SPECS.md`](P4_RV04_TEST_SPECS.md)

固定 4 个独立高风险反例：

1. output root containment；
2. sequence 数量不变但名称错误；
3. Parent / Clip mesh-bone mapping 语义交换；
4. material closure 缺失关键 VTF。

Luna 只执行 spec、生成：

```text
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log
```

然后 push 并停止，等待 Chat/Sol 判定。

### RV-05 — STATIC PASS WITH RISK

当前 `prototype_01_game_regression.json` 的 changed-runtime 用户确认与 frozen/no-op P4 边界一致；没有把 Blender retarget 当游戏证据，也没有把 `console_errors` / `rollback_after_disable` 自动升级为 PASS。

保留风险：这两个历史矩阵项仍是 `not_tested`。当前 P4 changed-runtime Gate 不要求用它们阻塞 frozen/no-op 收口；是否在 RV-06 输出中保留为 `PASS WITH RISK` 项，由最终 Reviewer 统一决定。

### RV-06 — PENDING

只有 RV-04 新证据由 Chat/Sol 审核完成后，才执行最终：

```text
PASS / PASS WITH RISK / REWORK
```

并决定是否允许 P4 `PASS / FROZEN`。

## 当前下一步

```text
用户/本地环境 pull 最新 master
  → Luna 读取 CODEX_TASKS.md + P4_RV04_TEST_SPECS.md
  → 只执行 RV-04 四个 Test Spec
  → push 两份新证据并停止
  → Chat/Sol 重读最新 HEAD + RV-04 evidence
  → RV-04 判定
  → RV-06 最终 Review
  → 无 blocker 才冻结 P4 并进入 P5
```
