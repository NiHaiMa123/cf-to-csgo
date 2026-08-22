# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 **ChatGPT 对话中的 Chat/Sol** 使用。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；用户选择的 Local Executor Agent = 本地执行与证据生产。**

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / TARGETED_REWORK_REQUIRED              <- 当前具体任务
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03        BLOCKED_BY_T02
P5-T04        BLOCKED_BY_T03
```

当前执行/Review 入口：

- [`P4_TASKS.md`](P4_TASKS.md)
- [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)
- [`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md)
- [`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md) ← 当前 targeted continuation
- [`CODEX_TASKS.md`](CODEX_TASKS.md)

P5 资料当前用于后续 handoff，不是当前 Local Executor 的第一执行入口。

---

## 2. 为什么当前仍在 P4-M01

P4 的历史 Review 只验收 conversion/build/package/MIGI/runtime 技术链。后续 evidence 确认 P4 可识别 BornBeast material 曾使用 external CS1.6 texture，因此 native CF material fidelity 没有闭合。

因此：

```text
P4 baseline 继续 frozen
P4-M01 单独 reopen native material lane
P5-T02 暂停
```

Chat/Sol 不得把 P4-M01 描述成“P4 整体失败”，也不得把历史 P4 `PASS / FROZEN` 描述成“原生材质已通过”。

---

## 3. Chat/Sol 当前职责

Chat/Sol 负责：

- 维护 `plan.md` / Task Spec / acceptance criteria；
- 读取 Local Executor push 的 P4-M01/R1 code/evidence；
- 判断 DTX/TGA/container/binding/CFG/shader 证据是否真的成立；
- 拒绝“能显示成图 = 格式正确”一类弱证据；
- 拒绝 external texture 进入 final provenance；
- 拒绝把 hypothesis / naming convention / byte-count fit 直接升级成 verified；
- 确认 report 中的关键验证是否真的存在于提交脚本、能重跑；
- 在 P4-M01 满足 DoD 后判定是否 `PASS / NATIVE_MATERIAL_RECOVERED`；
- 只有 P4-M01 PASS 后才恢复 P5-T02。

Chat/Sol 不得：

- 声称自己实际读取了本地 `data/**` bytes，除非有本地执行 evidence；
- 用聊天记忆覆盖 master；
- 用文件名/别名代替 material binding evidence；
- 为得到 PASS 临时降低 native-material gate；
- 把 external CS1.6 reference 的像素当作 local CF 输出；
- 因材质任务重写 frozen skeleton/sequence/runtime contract。

---

## 4. P4-M01 Review principle

最终问题：

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
9. `native_material_closure.json` 或 superseding R1 closure；
10. 所有关键输入 path/hash/size 与输出 hash；
11. 报告中的关键“verified”步骤存在于提交脚本或正式 decoder，并可复现。

### 不足以 PASS 的证据

- raw DTX 能排成一张图；
- raw CFG 能画成彩条；
- 某个 channel 看起来像 mask；
- 外部纹理贴到模型上看起来正确；
- 用户肉眼觉得“差不多”；
- 文件名能对上 BornBeast；
- basename+directory 没有 engine/结构 evidence；
- byte count/mip size 恰好 fit；
- report 声称做过某个 scan，但最终提交脚本没有该 scan；
- post-mesh numeric field 存在，就直接命名为 texture slot；
- 237 个 CFG 有 mod-3 pattern，就直接认定 scalar+padding。

### 可以支持 PASS 的证据

- binary/container 结构自洽；
- 不同 decoder / upstream bytes 交叉验证；
- LTB slot/index/render-style 或等价 engine binding evidence；
- same-geometry variant differential；
- CFG 字段/record 语义能解释不同样本变化；
- clean-output 重建一致；
- final visible color 没有任何 external pixel 来源。

---

## 5. R0 Review 历史

commit `632ede449578f688cea7e6b5f40cbf03700aaaa5` 提供了有价值 exploration evidence，但其旧 `6/8 PASS，只差用户视觉 Gate` 不被接受。

当时正式分级：

```text
A provenance              ACCEPT / REUSE
B inventory               REUSE_WITH_CAUTION
C DTX                      REWORK
D TGA                      FAIL / REWORK
E material binding         INCOMPLETE
F CFG reverse              INCOMPLETE
G variant differential     ACCEPT / REUSE
H shader hypotheses        DIAGNOSTIC_ONLY
I native closure           NOT READY
J Source1 integration      DEFERRED
```

该历史 Review 保留，用于理解为什么存在 R1。

---

## 6. 2026-08-22 对 commit bded9e8 的当前 Review

Local Executor commit：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
```

本轮整体评价：**有效推进，但未完成 R1**。正式分级：

```text
A provenance              ACCEPT / REUSE
B inventory               REUSE_WITH_CAUTION
C DTX                      PARTIAL_ACCEPT / TARGETED_REWORK
D TGA                      ACCEPT / STRUCTURAL
E material binding         STAGE1_PARTIAL_ACCEPT / STAGE2_OPEN
F CFG reverse              PARTIAL_ACCEPT / REFRAME
G variant differential     ACCEPT / REUSE
H shader hypotheses        DIAGNOSTIC_ONLY / REWORK
I native closure           NOT READY / CONTINUE
J Source1 integration      DEFERRED
```

详细 Review 与下一步以 [`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md) 为准。

### C — DTX

接受：

- 正式 DTX version/LZMA 路线纠正；
- 旧 `512x256 full-mip + 163-byte trailer` 结论撤销；
- 3-byte periodic pixel-like structure 有强支持。

不接受为最终 VERIFIED：

- `1024 width`；
- `single continuous image / no mips`；
- `BGR24` channel order。

核心原因：`dtx_revalidation_r1.json` 声称 `64..2048 exhaustive width scan`，但最终提交的 `r1_dtx_revalidate.py` 直接固定 `W=1024`，没有保存该 scan 的可重跑实现；channel census 又只采样前 300k bytes，而结论扩展到 whole file/tail。

### D — TGA

接受 formal repair correction：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

三张 BornBeast TGA 已按正式结构重建并记录 offsets。默认不重跑，除非后续 evidence 冲突。

### E — material binding

接受：LTB 中存在 mesh-associated post-mesh numeric field 的结构 evidence。

仍需证明：

```text
numeric field semantics == texture slot
model/slot -> actual DTX/TGA/CFG texture set
```

下一轮优先利用现有 `LithTechModelTextureConfigIndex`、`LithTechTextureMappingScanner`、`LithTechDatTextureReferenceIndex`、`TextureReferenceResolver`、`LithTechModelTextureLoader`，不要只靠 basename 推测 engine lookup。

### F — CFG

237-file corpus 的 mod-3/3-byte periodic pattern 是有价值 evidence，但当前至少存在两个竞争解释：

```text
RGB/BGR triplets with two fixed-FF channels
vs
scalar + padding/alignment
```

当前脚本通过 `if raw[i] != 0xFF` 删除样本，因此 `sample_count` 不能直接视为完整 record/texel count。必须保留全部 bytes 后重新 accounting。

### H — shader hypotheses

`r1_shader_closure.py` 使用 `step = 97` 做 byte sampling；因为 `97 % 3 == 1`，采样起点会在三个 byte phases 间轮换，污染 channel census。修复后 H2 仍为 diagnostic approximation，不能替代 engine semantics。

### I — closure

Local Executor 正确把状态写成：

```text
CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

Chat/Sol 同意这一点。当前不是 final user visual gate。

---

## 7. External BornBeast texture 的正确用途

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

## 8. Executor / harness provenance

任务继续保持 agent-agnostic。

用户报告 commit `bded9e8` 实际执行组合：

```text
Harness: Claude Code
Model:   GLM-5.3-Flash internal beta / multimodal
```

commit footer 残留的：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

不是可靠 executor provenance。后续 benchmark 若需记录模型/Agent，显式写 `executor_harness` / `executor_model`；不得仅从 co-author footer 推断。

---

## 9. P4-M01 -> P5-T02 handoff

只有 Chat/Sol Review 明确写：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才允许恢复 P5-T02。

恢复后的 T02：

```text
validated P4-M01 method
-> M4A1_S_Transformers family
-> Transformers-specific extension if necessary
-> native-material finalist render
-> USER LOCAL-CANDIDATE GATE
```

如果方法无法迁移，不得退回 external texture。

---

## 10. 当前下一步

> **Review 下一位 Local Executor 按 `P4_M01_R1_CONTINUATION.md` 从 commit `bded9e8` 继续产生的 targeted evidence。优先检查：DTX width/stride scan 是否真正可重跑；CFG 是否保留完整 triplets/0xFF 并比较 triplet-vs-scalar；stage-2 binding 是否利用现有 mapping/config infrastructure；H2 phase-mixing bug 是否修复。R1-D TGA 默认不重跑。当前不进入用户 final visual Gate、不执行 J、不恢复 P5-T02。**
