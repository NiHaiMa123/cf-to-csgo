# P4 当前状态

> 项目唯一权威进度仍以 [`plan.md`](plan.md) 第 1 节为准。
>
> 本文件保留 P4 baseline 最终 Review 快照，并记录 2026-08-21 用户明确授权的 post-freeze material corrective task。

更新时间：2026-08-21

---

## 1. P4 baseline 历史最终结论

- P4-T01～T07：完成；
- P4-T08：`passed_user_confirmed`；
- P4-T09：完成；
- RV-01：`PASS`；
- RV-02：`PASS WITH NON-BLOCKING RISK`；
- RV-03：`PASS`；
- RV-04：`PASS`，4/4 独立高风险反例命中预定 Gate；
- RV-05：`PASS WITH NON-BLOCKING RISK`；
- RV-06：`PASS WITH RISK`；
- **P4 baseline：`PASS / FROZEN`。**

完整历史 Reviewer 记录：[`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)。

冻结实现与证据：

```text
Implementation baseline  10aa99b770e575300ca3c28324ef3de3d5b70c6b
frozen build run         run_20260819_170013_270792
RV-04 evidence commit    fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
frozen addon             p_cf_bornbeast_m4a4_p4_frozen_noop_01
Runtime slot             M4A4
Internal model           weapons/v_rif_m4a1.mdl
Inspect policy           frozen_noop_safe
final_target_identity    false
final_cf_material        false
```

P4 baseline 证明：Prototype 的 conversion/build/package/MIGI/runtime 技术链满足当时 DoD。

P4 baseline 从未证明：

- 当前候选就是最终雷神；
- CF 原生材质已经正确解码；
- external texture 可以成为 final；
- visible Inspect / Blender retarget / 手指穿模已经解决；
- CF 原动画/声音/world model 已最终化。

---

## 2. 2026-08-21 post-freeze corrective task

后续 evidence 已确认 P4 可识别 BornBeast Prototype 曾使用 external CS1.6 material input：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此历史 P4 material closure 只证明 Source 引用链存在，**不能证明 native CF material fidelity**。

用户明确要求原生贴图还原不能跳过，并授权当前先返回 P4 做材质纠偏。

新增状态：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

Native material recovery 是 hard requirement；`REQUIRED` 不作为独立 lifecycle status。

正式任务：[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

P4-M01 只重新打开：

```text
native DTX/TGA interpretation
LTB material binding
WeaponShader CFG/render-style semantics
native material reconstruction/fidelity
```

不重新打开：

```text
M4A4 runtime/skeleton/sequence/attachment contract
历史 build/package/deploy evidence
RV-01 ~ RV-06 历史 Review
frozen addon
```

---

## 3. 用户 Gate 历史快照

用户已确认 frozen/no-op addon：

- 按 F 后没有崩溃或明显运行错误；
- 无可见 Inspect 动作符合 frozen/no-op 预期；
- 武器状态正常返回；
- 之后仍可射击、换弹、切枪。

仍明确保留：

- `console_errors = not_tested`；
- `rollback_after_disable = not_tested`；
- visible Inspect / Blender retarget / 手指穿模 = P7。

这些历史结论与 P4-M01 材质任务无冲突。

---

## 4. P4-M01 当前目标

以 BornBeast 为 controlled benchmark：

```text
local LTB/UV
+ local DTX
+ local Alpha/Normal/Specular TGA
+ local WeaponShader CFG
+ local variants
-> binary/container revalidation
-> material binding
-> CFG semantic reverse
-> deterministic shader hypotheses
-> 0 external pixels native material closure
```

external CS1.6 BornBeast texture 只允许作为 `reference_only / differential_control`。

P4-M01 PASS 后才恢复 P5-T02，把经过验证的方法应用到 Transformers。

---

## 5. 角色路由

- Local Executor Agent：由用户选择；读取 [`CODEX_TASKS.md`](CODEX_TASKS.md) 和 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)，执行 P4-M01。当前任务不绑定 Luna、Codex 或任何具体模型。
- Chat/Sol：读取 [`CHAT_REVIEW.md`](CHAT_REVIEW.md)，Review P4-M01 evidence，并决定是否恢复 P5-T02。
- P5-T02 当前：`PAUSED_BY_P4_M01`。

历史文档中若保留某次实际执行者名称，只表示历史 provenance，不代表当前 Executor 要求。

---

## 6. 当前下一步

```text
P4-M01 provenance audit
-> DTX/TGA revalidation
-> LTB binding recovery
-> CFG binary reverse
-> variant differential
-> offline shader hypothesis
-> native material closure
-> Chat/Sol Review
-> resume P5-T02 only after PASS
```
