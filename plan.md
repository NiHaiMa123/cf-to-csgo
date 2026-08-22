# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-22
>
> 项目唯一 authoritative progress/status：**本文件第 1 节**
>
> 当前执行任务：**P4-M01-N01 — Phase 1 consumer discovery**
>
> 当前状态：**P4 baseline `PASS / FROZEN`；P4-M01 `ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`；P4-M01-R1 `ACCEPTED / COMPLETE`；P4-M01-N01 Phase 0 `ACCEPT / FROZEN`；P4-M01-N01 `ACTIVE / PHASE1_CONSUMER_DISCOVERY`；P5-T02 `PAUSED_BY_P4_M01`**
>
> 当前运行槽位：**M4A4**
>
> 冻结技术样机：**`Prototype-01`**
>
> 当前内部模型名：`weapons/v_rif_m4a1.mdl`

---

## 1. 唯一权威进度

### 1.1 状态总表

| 阶段 / Task | 当前状态 | 含义 |
|---|---|---|
| P0–P3 | DONE / HISTORICAL | Source 1 基线、CF 静态导出、M4A4 映射、历史编译/材质引用基础 |
| P4 baseline | **PASS / FROZEN** | 几何→Source 1→package→MIGI 技术链已冻结 |
| **P4-M01** | **ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE** | BornBeast 原生 CF 材质恢复 benchmark |
| P4-M01-R1 | **ACCEPTED / COMPLETE** | evidence correction 已完成，不再进入 R1 cleanup loop |
| P4-M01-N01 Phase 0 | **ACCEPT / FROZEN** | R1 final consistency cleanup 已经 Chat/Sol Review 接受 |
| **P4-M01-N01** | **ACTIVE / PHASE1_CONSUMER_DISCOVERY** | **当前唯一具体执行任务：真实 material consumer / binding / CFG semantic consumer / channel semantics** |
| P5-T01 | PASS / USER_REFERENCE_CONFIRMED | 雷神官方目标图已确认 |
| P5 LEGACY PRE-SCAN | EXECUTION_PASS / PRESERVED_FOR_REUSE | 本地广召回候选池保留 |
| P5-T02 | **PAUSED_BY_P4_M01** | 等 P4-M01 原生材质方法闭合后继续 Transformers |
| P5-T03 | BLOCKED_BY_T02 | Resource Graph / provenance closure |
| P5-T04 | BLOCKED_BY_T03 | Chat/Sol final identity review |
| P6 | BLOCKED_BY_P5 | 最终资产替换与发布质量 |
| P7 | FUTURE | visible Inspect、手指 IK/retarget、CF 原动画等增强 |

状态命名：

```text
NATIVE_MATERIAL_RECOVERY_INCOMPLETE = P4-M01 尚未完成 native material closure
PHASE1_CONSUMER_DISCOVERY           = 正在定位真实 engine/config/resource consumer
NATIVE_MATERIAL_RECOVERED           = P4-M01 completion result，必须经 Chat/Sol Review
```

当前 Agent 启动入口：

```text
AGENTS.md
-> plan.md 第 1 节
-> CODEX_TASKS.md
-> P4_TASKS.md
-> P4_M01_TASK_SPEC.md
-> P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md
-> P4_M01_N01_CONTINUATION.md   <- CURRENT direct entry
```

R1 历史需要时再读：

```text
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
```

`P5_T02_TASK_SPEC.md` 仍是暂停后的恢复协议，不是当前执行入口。

---

### 1.2 P4 baseline — PASS / FROZEN

冻结证据：

```text
Implementation baseline: 10aa99b770e575300ca3c28324ef3de3d5b70c6b
frozen build run:       run_20260819_170013_270792
RV-04 evidence commit:  fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
frozen addon:           p_cf_bornbeast_m4a4_p4_frozen_noop_01
runtime slot:           M4A4
internal model:         weapons/v_rif_m4a1.mdl
```

P4 baseline 已证明：

- manifest-driven 本地 CF LTB fresh build；
- M4A4 Source skeleton / sequence / attachment contract；
- mesh→bone、SMD/QC、studiomdl、Crowbar roundtrip；
- validation/package/staging/deploy provenance；
- destructive-operation guards / negative tests；
- frozen/no-op Inspect changed-runtime 用户 Gate。

P4 baseline 从未证明：

- Prototype 就是最终雷神；
- CF 原生材质已正确恢复；
- external texture 可进入 final；
- visible Inspect / 手指 IK 已完成；
- CF 原动画/声音/world model 已最终化。

因此 P4 baseline 继续冻结；P4-M01 不修改 frozen conversion contract。

---

### 1.3 P4-M01 — ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE

P4 Prototype 曾使用外部 CS1.6 BornBeast texture：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此 conversion/build/MIGI 技术链成立，但 native CF material fidelity 未闭合。

P4-M01 主协议：[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

核心目标：

```text
local BornBeast LTB / UV
+ local DTX
+ local Alpha/Normal/Specular TGA
+ local WeaponShader CFG
+ local same-family variants
-> decode/container evidence
-> real material binding
-> CFG/render semantics
-> 0 external pixels native composition
-> reproducible closure
```

external CS1.6 texture 只允许 `reference_only / differential_control`。

#### R1 correction history

关键提交：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5   R0 exploration
bded9e8a6f7f95997d9717eb8f35beb02619f153   first R1 correction
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f   targeted continuation
0dc5793b6e47cb20da9e44aebcec2195194bd6f2   narrow rework
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19   N01 Phase-0 final consistency cleanup
```

Chat/Sol 对 `2344d61` 的结论：Phase 0 cleanup 已接受；R1 正式结束。

```text
P4-M01-R1          = ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 = ACCEPT / FROZEN
```

`2344d61` 没有进入 N01 Phase 1，因此 substantive N01 work 仍未开始；这不是 blocker，下一位 Executor 直接从 Phase 1 继续。

#### 当前 executor benchmark context

用户当前准备切换：

```text
Model: MiniMax M3
Harness: unspecified / user-selected
```

模型信息只用于 benchmark/provenance；Task 保持 agent-agnostic。不得从 commit footer 推断真实 executor。

#### 当前可复用 evidence baseline

**DTX**

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC / NOT universal
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

**TGA**

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular formal repair 已接受。

**WeaponShader CFG**

```text
237/237 files:
non-0xFF bytes occupy one fixed offset-mod-3 phase per file;
other two phases are constant 0xFF.
```

R1/N01 Phase0 已完成：

```text
phase != record boundary                ACCEPT
BornBeast varying-phase samples         164
Transformers                            169
Jewelry                                 214
phase-origin span accounting            ACCEPT
record boundary                         OPEN
H-CFG-A RGB/BGR triplets                OPEN
H-CFG-B scalar + padding                PREFERRED_NOT_PROVEN
H-CFG-C other periodic packing          OPEN
semantic consumer                       OPEN
```

**Engine material positive control**

ArmModel LZMA text CFG 已证明 CF 存在：

```text
[Textures] named texture refs
[Techniques]
[Properties] PieceIndex
```

这是 engine-format positive evidence；不能直接等同 weapon format。

**Weapon binding**

```text
LTB post-mesh short field exists        VERIFIED_STRUCTURAL
field == texture slot/PieceIndex        PROVISIONAL
weapon mesh/piece -> texture set        OPEN
```

355-file config-like/dat/lta negative 是 scoped negative，不是 whole-data exhaustive negative。

---

### 1.4 P4-M01-N01 — ACTIVE / PHASE1_CONSUMER_DISCOVERY

原始任务：[`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md)。

当前 overlay：[`P4_M01_N01_CONTINUATION.md`](P4_M01_N01_CONTINUATION.md)。

N01 当前直接回答：

> **CF weapon 的 model/piece、texture family、WeaponShader CFG 究竟由哪个 engine/config/resource path 关联和消费？**

Phase 0 已冻结，不再执行。

当前固定顺序：

```text
Phase 1  consumer call/data-path discovery
Phase 2  ArmModel positive control + weapon-family differential
Phase 3  WeaponShader CFG consumer identification
Phase 4  storage/channel/binding semantics
Phase 5  engine binding closure
```

当前最低 handoff：

```text
Phase 1 outputs
+ Phase 2 weapon_material_differential.json
```

不能只做 candidate list 后停止。

N01 substantive priority：

```text
consumer/reference evidence
> structural binding
> same-family differential
> bounded binary hypothesis
> preview appearance
```

优先利用现有仓库基础设施：

```text
LithTechModelTextureConfigIndex.cs
LithTechTextureMappingScanner.cs
LithTechDatTextureReferenceIndex.cs
TextureReferenceResolver.cs
LithTechModelTextureLoader.cs
LithTechModelDecoder.cs
CfgTextDecoder.cs
CfgBinaryStripDecoder.cs
```

目标不是列类名，而是找真实调用/数据关系并产出：

```text
n01/consumer_candidate_matrix.json
n01/consumer_search_report.md
n01/weapon_material_differential.json
n01/cfg_consumer_report.json
n01/channel_semantics_report.json
n01/engine_binding_closure.json
```

N01 PASS 不自动恢复 P5；它只代表 engine binding/consumer lane 足以进入 P4-M01 native composition/final closure。

---

### 1.5 P5 — ACTIVE，但 T02 暂停等待 P4-M01

P5 目标仍是最终雷神资产定位。

```text
P5-T01                  PASS / USER_REFERENCE_CONFIRMED
P5 LEGACY PRE-SCAN      PASS / REUSE
P5-T02                  PAUSED_BY_P4_M01
P5-T03                  BLOCKED_BY_T02
P5-T04                  BLOCKED_BY_T03
```

T01 固定 evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

Legacy pre-scan：

```text
data/** inventory       165082 files
recalled candidates      2856
LTB candidates           1281
canonical LTB inspected   441
```

当前 finalist diagnostics 已覆盖 C029/C103；不让用户在灰模/伪材质之间强选。

只有：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

后才恢复 P5-T02：

```text
validated material method
-> M4A1_S_Transformers family
-> Transformers-specific native material differential
-> native-material finalist render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

---

## 2. 三条工作线

### Track A — Source 1 conversion baseline

状态：**P4 baseline PASS / FROZEN**。

```text
CF LTB
-> mesh/UV/normal
-> M4A4 skeleton mapping
-> SMD/QC/VMT/VTF
-> studiomdl
-> roundtrip validation
-> package/staging/deploy
-> runtime gate
```

### Track B — Native material recovery

状态：**P4-M01 ACTIVE；当前 P4-M01-N01 Phase 1**。

回答：CF 原生 texture/material 如何被解释、绑定和组合。

### Track C — Final Leishen identity

状态：**P5 ACTIVE；T02 等待 Track B**。

依赖：

```text
Track A frozen technical baseline
       +
Track B validated native material method
       +
P5 official reference/candidate evidence
       -> final identity
```

---

## 3. 资产来源政策

### final 允许

- 本地 CF 原始资源；
- 本地 CS:GO Legacy VPK 仅作为 skeleton/sequence/attachment/runtime compatibility 基线。

### reference-only

- CF 官方图；
- Wiki/媒体/论坛截图；
- 第三方 MOD；
- 网络 GoldSrc/CS1.6 texture；
- P4 external BornBeast texture。

### 禁止

- external pixels 进入 final；
- AI 生成/重绘 texture 填洞；
- 从 reference 采色/烘焙后冒充 local CF；
- 用“能显示成图”代替 format/binding evidence；
- 用 basename convention 代替 engine binding；
- 修改/删除 `data/**` 配合 Git；
- 覆盖 P4 frozen evidence。

---

## 4. Frozen 与可修改边界

### 继续冻结

```text
M4A4 runtime slot
57-bone reference
sequence/attachment contract
frozen build/package/deploy evidence
RV-01 ~ RV-06
p_cf_bornbeast_m4a4_p4_frozen_noop_01
```

### P4-M01/N01 可修改

```text
CFRezManager/Decoders/** 中与材质 consumer/binding 直接相关的代码
inspection/export code
scripts/material_recovery/**
相关测试
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

若必须改变 frozen conversion contract，停止并返回 Chat/Sol。

---

## 5. 当前 blocker

| 项目 | 当前判断 | Blocker |
|---|---|---:|
| R1 evidence consistency | **ACCEPTED / COMPLETE** | — |
| N01 Phase 0 | **ACCEPT / FROZEN** | — |
| weapon material consumer | 未定位/未闭合 | **P4-M01-N01 Phase 1** |
| weapon piece→texture-set binding | LTB field provisional；ArmModel positive control 已有 | **P4-M01-N01** |
| WeaponShader CFG consumer/semantic | mod-3 structural fact 已证，consumer 未知 | **P4-M01-N01** |
| DTX/TGA channel/binding semantics | storage/layout 部分已证，engine role/order 未闭合 | **P4-M01-N01** |
| TGA formal repair | ACCEPT / STRUCTURAL | — |
| H2 phase mixing | FIX ACCEPTED | — |
| BornBeast external material provenance | 已确认，不能 final | P4-M01 |
| Transformers native material | 等待 P4-M01 | P5-T02 |
| final Leishen identity | 未完成 | P5 |
| animation/IK/visible Inspect | 当前非 blocker | P7 |

---

## 6. Definition of Done

### 6.1 P4 baseline

保持 `PASS / FROZEN`。

### 6.2 N01 DoD

至少得到 direct engine/resource closure，或多个独立 differential evidence 唯一支持：

```text
weapon mesh/piece
-> material/binding key
-> local texture family
-> CFG/material resource role
```

basename、视觉相似、长度 fit、单一统计相关不足以 PASS。

### 6.3 P4-M01 DoD

- native input inventory 完整；
- DTX/TGA 关键结构可复现；
- mesh/material binding 有 engine/structural evidence；
- CFG/render semantics 达到足够可重建程度；
- visible color 全部 local CF / verified semantics；
- 0 external pixels；
- clean-output 可重复；
- native composition 可稳定辨认 BornBeast 主要颜色/图案/高光区域；
- external texture 仅 reference；
- Chat/Sol Review 判 `PASS / NATIVE_MATERIAL_RECOVERED`。

### 6.4 P5 final identity

P4-M01 PASS 后才恢复 Transformers/native finalist/user gate/provenance closure。

---

## 7. 当前唯一下一步

> **Local Executor 同步最新 `master`，读取 `P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md` 与当前 `P4_M01_N01_CONTINUATION.md`。N01 Phase 0 已 `ACCEPT / FROZEN`，禁止重跑；直接从 Phase 1 开始，沿仓库现有 texture config/mapping/index/resolver/decoder 调用与本地 resource relation 寻找真实 weapon material consumer。随后必须完成 Phase 2：以 ArmModel explicit `[Textures]/PieceIndex` 为 positive control，对 BornBeast/Transformers/Jewelry/简单 M4A1-S control 做 same-family differential。当前最低 handoff 是 Phase 1 两个 consumer outputs + Phase 2 `weapon_material_differential.json`；不能只生成 candidate list 就停止。若已找到 credible consumer candidate，可同轮继续 Phase 3–5。不要重跑 TGA、DTX header/LZMA/width scan，不要无边界盲扫 `data/**`。完成后 push scoped code/evidence 到 `master`，由 Chat/Sol Review N01。当前不执行 J、不恢复 P5-T02、不请求 final user visual gate。**