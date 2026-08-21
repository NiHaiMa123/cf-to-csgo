# P5_TASKS.md — 最终雷神资产定位任务流

> 当前阶段：**P5 — ACTIVE，但 P5-T02 `PAUSED_BY_P4_M01`**
>
> Planner / Reviewer：**Chat/Sol**
>
> Local Executor：**Luna / 普通 Codex Agent**
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git 与 `data/**` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 当前依赖关系

P5 本身没有取消，但当前执行先回 P4 做 native material benchmark：

```text
P4 baseline       PASS / FROZEN
P4-M01            ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
    ↓ PASS 后
P5-T02            RESUME
```

原因：P4 BornBeast Prototype 的可识别材质曾使用 external CS1.6 texture，因此不能直接把未知的 DTX/TGA/CFG 解释迁移到雷神并要求用户视觉确认。

---

## 2. P5 标准识别顺序

```text
P5-T01  官方图鉴 Web Search + 用户确认目标图                 PASS
    ↓
P5 LEGACY PRE-SCAN                                           PASS / REUSE
    ↓
P5-T02  本地候选缩圈 + native material finalist + 用户确认   PAUSED_BY_P4_M01
    ↓
P5-T03  Resource Graph / provenance closure                  BLOCKED_BY_T02
    ↓
P5-T04  Chat/Sol final identity review                       BLOCKED_BY_T03
```

P5 的原则：

- official reference 必须来自官方 CF 页面并经用户确认；
- 文件名/跨服名/legacy score 只能作线索；
- 灰模只用于几何排除；
- native material 未闭合时不能进行最终本地候选 Gate；
- external MOD texture 不能成为 final material；
- `USER_VISUAL_MATCH_CONFIRMED` 仍不是最终 `IDENTITY_CONFIRMED`。

---

## 3. P5-T01 — PASS / USER_REFERENCE_CONFIRMED

正式协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

固定 evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

除非 evidence 损坏或用户明确否决，不重跑 T01。

---

## 4. LEGACY PRE-SCAN — PRESERVED_FOR_REUSE

历史本地广召回继续作为 T02 candidate pool：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

旧 score 不代表 identity confidence，不重新扫描全部 16 万文件，除非 evidence 缺失或明显失效。

---

## 5. P5-T02 — PAUSED_BY_P4_M01

正式恢复协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

已经完成：

```text
confirmed official reference
-> legacy pre-scan reuse
-> M4/M4A1 PLAYERVIEW narrowing
-> exact SHA dedup
-> geometry clusters
-> C029/C103 finalist diagnostics
```

当前不能通过的诊断：

```text
C029/C103 gray geometry                    diagnostic_only
headerless-BGR24 Transformers DTX          unvalidated hypothesis
raw PV DTX + UV                            diagnostic_only
Alpha/Specular scalar approximation        diagnostic_only
WeaponShader CFG raw-rgb-strip preview     not semantic decoding
```

因此当前停止：

```text
USER LOCAL-CANDIDATE GATE
```

不要要求用户在灰模/伪材质之间强选。

---

## 6. 当前为什么先做 P4-M01

BornBeast 是更合适的材质逆向 benchmark：

- 几何/UV 已稳定；
- 本地 DTX/TGA/CFG 资源已知；
- 已有历史解码脚本和失败/诊断 evidence；
- 有 external CS1.6 flatten texture 可作 `reference_only / differential_control`；
- 能先把 material method 验证清楚，再应用到 Transformers。

当前 Luna 应读取：

```text
P4_M01_TASK_SPEC.md
```

而不是继续执行 T02。

---

## 7. P4-M01 PASS 后如何恢复 T02

Chat/Sol 只有在判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

后才把 T02 改为 active。

T02 恢复后固定路线：

```text
read validated P4-M01 decoder/binding/shader method
-> apply to M4A1_S_Transformers family
-> verify Transformers-specific DTX/TGA/CFG/material binding
-> extend method only where evidence requires
-> native material acceptance gate
-> native-material orthographic finalist render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

如果 P4-M01 方法对 Transformers 不完全通用：

- 可以做 Transformers-specific extension；
- 必须继续使用 local CF evidence；
- 不允许退回 external texture；
- 不允许因为“看起来像”就跳过格式/binding 验证。

---

## 8. P5-T03 — BLOCKED_BY_T02

T03 只在 T02 native-material + user visual gate 完成后建立完整 Resource Graph：

```text
PLAYERVIEW model LTB
-> base/diffuse/lookup/DTX/TGA
-> Alpha/Normal/Specular/emissive/detail
-> Shader/CFG/material/render-style
-> QV/world
-> WAV
-> animation/config
```

每个资源记录：

```text
relative_path
sha256
size_bytes
relation
source_class
confidence / unresolved_reason
```

T03 不得被用来补做 T02 本应完成的 native material reconstruction。

---

## 9. P5-T04 — BLOCKED_BY_T03

由 Chat/Sol 最终输出之一：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才允许进入 P6。

---

## 10. 角色边界

### Luna / Codex

当前：执行 P4-M01，不执行 T02 用户 Gate。

P4-M01 PASS 后：按 `P5_T02_TASK_SPEC.md` 恢复 Transformers native material + candidate work。

不得：

- 重跑已完成 T01；
- external texture 作为 final；
- 灰模/scalar approximation 通过 T02；
- 自行写最终 identity；
- 修改 P4 frozen conversion contract。

### Chat/Sol

负责：

- P4-M01 evidence Review；
- 判断 material method 是否足够可靠/可迁移；
- P4-M01 PASS 后重新激活 T02；
- T03/T04 后续 Review。

---

## 11. 当前下一步

> **P5 当前不继续执行。先完成 `P4_M01_TASK_SPEC.md`，建立可信 native material method；通过后再恢复 `P5_T02_TASK_SPEC.md`。**
