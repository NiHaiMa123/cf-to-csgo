# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 **ChatGPT 对话中的 Chat/Sol** 使用。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；Codex/Luna = 本地执行与证据生产。**

---

## 1. 当前阶段

截至 2026-08-21：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_REQUIRED   <- 当前任务
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03        BLOCKED_BY_T02
P5-T04        BLOCKED_BY_T03
```

当前执行入口：

- [`P4_TASKS.md`](P4_TASKS.md)
- [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)
- [`CODEX_TASKS.md`](CODEX_TASKS.md)

P5 资料当前用于后续 handoff，不是 Luna 的第一执行入口。

---

## 2. 为什么当前返回 P4

P4 的历史 Review 只验收了 conversion/build/package/MIGI/runtime 技术链。后续 evidence 确认 P4 可识别 BornBeast material 使用过 external CS1.6 texture，因此 native CF material fidelity 没有闭合。

用户明确要求：原生贴图正确还原不能跳过，并要求当前先回 P4 解决基础材质恢复方法。

因此：

```text
P4 baseline 继续 frozen
P4-M01 单独 reopen native material lane
P5-T02 暂停
```

Chat/Sol 不得把 P4-M01 描述成“P4 整体失败”或“推翻历史 RV-06”；也不得把历史 P4 `PASS / FROZEN` 描述成“原生材质已通过”。

---

## 3. Chat/Sol 当前职责

Chat/Sol 负责：

- 维护 `plan.md` / Task Spec / acceptance criteria；
- 读取 Luna push 的 P4-M01 code/evidence；
- 判断 DTX/TGA/container/binding/CFG/shader 证据是否真的成立；
- 拒绝“能显示成图 = 格式正确”一类弱证据；
- 拒绝 external texture 进入 final provenance；
- 在 P4-M01 满足 DoD 后判定是否 `PASS / NATIVE_MATERIAL_RECOVERED`；
- 只有 P4-M01 PASS 后才恢复 P5-T02；
- 后续继续负责 P5-T03/T04。

Chat/Sol 不得：

- 声称自己实际读取了本地 `data/**` bytes，除非有本地执行 evidence；
- 用聊天记忆覆盖 master；
- 用文件名/别名代替 material binding evidence；
- 为得到 PASS 临时降低 native-material gate；
- 把 external CS1.6 reference 的像素当作 local CF 输出；
- 因材质任务重写 frozen skeleton/sequence/runtime contract。

---

## 4. P4-M01 Review principle

P4-M01 的最终问题是：

> **BornBeast 是否已经能仅使用 local CF 资源 + verified semantics，得到可重复、可解释、0 external pixels 的正确原生材质。**

最低必须看到：

1. provenance audit；
2. native material inventory；
3. DTX interpretation matrix；
4. TGA interpretation matrix；
5. material binding report；
6. CFG reverse report；
7. variant differential evidence；
8. shader hypotheses；
9. `native_material_closure.json`；
10. 所有关键输入 path/hash/size 与输出 hash。

### 不足以 PASS 的证据

- raw DTX 能排成一张图；
- raw CFG 能画成彩条；
- 某个 channel 看起来像 mask；
- 外部纹理贴到模型上看起来正确；
- 用户肉眼觉得“差不多”；
- 文件名能对上 BornBeast；
- Source VMT/VTF closure 只证明引用存在。

### 可以支持 PASS 的证据

- binary/container 结构自洽；
- 不同 decoder / upstream bytes 交叉验证；
- LTB slot/index/render-style binding；
- same-geometry variant differential；
- CFG 字段/record 语义能解释不同样本变化；
- clean-output 重建一致；
- final visible color 没有任何 external pixel 来源。

---

## 5. External BornBeast texture 的正确用途

历史 CS1.6 BornBeast texture 只能是：

```text
reference_only / differential_control
```

允许：

- 比较大区域配色、纹理分区、能量/高光位置；
- 判断某个 local map 更像 base/mask/lookup；
- 帮助决定下一条 hypothesis。

禁止：

- 采样 RGB；
- 抠图；
- texture bake；
- 训练/拟合 local texture；
- 作为 Source final base texture；
- 进入 `source_class=local_cf`。

---

## 6. P4-M01 -> P5-T02 handoff

只有 Chat/Sol Review 明确写：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才允许恢复 P5-T02。

恢复后的 T02 不再重复 BornBeast 基础逆向，而是：

```text
validated P4-M01 method
-> M4A1_S_Transformers family
-> Transformers-specific extension if necessary
-> native-material finalist render
-> USER LOCAL-CANDIDATE GATE
```

如果方法无法迁移，不得退回 external texture；应记录迁移失败证据并重新设计 Transformers-specific extension。

---

## 7. 历史 P5 状态

P5-T01 已完成，official reference evidence 已固定。不要重跑 Mandatory Web Search，除非用户明确否决现有 reference 或 evidence 损坏。

P5 LEGACY PRE-SCAN 继续保留为候选池，不重扫全部 `data/**`。

C029/C103 当前只是 geometry/material candidate evidence；在 native material 恢复前不要要求用户强选。

---

## 8. 当前下一步

> **等待/审查 Luna 按 `P4_M01_TASK_SPEC.md` 生成的 BornBeast native-material evidence。当前不执行 P5-T02 用户候选 Gate，不重做 T01，不进入 P5-T03。**
