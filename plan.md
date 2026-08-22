# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-22
>
> 项目唯一 authoritative progress/status：**本文件第 1 节**
>
> 当前执行任务：**P4-M01-N01 — final documentation/provenance cleanup before runtime-artifact blocker freeze**
>
> 当前状态：**P4 baseline `PASS / FROZEN`；P4-M01 `ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`；P4-M01-R1 `ACCEPTED / COMPLETE`；P4-M01-N01 Phase 0 `ACCEPT / FROZEN`；P4-M01-N01 `ACTIVE / FINAL_DOCUMENTATION_CLEANUP`；N01 substantive `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS`；P5-T02 `PAUSED_BY_P4_M01`**
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
| **P4-M01** | **ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE** | BornBeast 原生 CF 材质恢复 benchmark 尚未闭合 |
| P4-M01-R1 | **ACCEPTED / COMPLETE** | evidence correction 已完成，不再进入 R1 cleanup loop |
| P4-M01-N01 Phase 0 | **ACCEPT / FROZEN** | R1 final consistency cleanup 已经 Chat/Sol Review 接受 |
| **P4-M01-N01** | **ACTIVE / FINAL_DOCUMENTATION_CLEANUP** | 当前只收 provenance generator 与 closure 文案；substantive consumer 已受 runtime artifact blocker 阻塞 |
| N01 substantive | **BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS** | 当前 repo + 已解包静态资源没有原 CF client/runtime consumer code，无法继续闭合真实 binding |
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
FINAL_DOCUMENTATION_CLEANUP        = N01 当前只剩 evidence/provenance 文案与 generator 收口
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS = 当前 corpus 缺原 CF runtime/client consumer artifact
NATIVE_MATERIAL_RECOVERED          = P4-M01 completion result，必须经 Chat/Sol Review
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

#### R1 / N01 correction history

关键提交：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5   R0 exploration
bded9e8a6f7f95997d9717eb8f35beb02619f153   first R1 correction
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f   targeted continuation
0dc5793b6e47cb20da9e44aebcec2195194bd6f2   narrow rework
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19   N01 Phase-0 final consistency cleanup
df48af65f2273772fedd7f61c8c230b2184cf8b4   first Phase1-5 consumer attempt
69c03d8769db2107cd94cae11accc750716466ae   scanner/lineage/binding-key repair
ea11ba143d859193213f24ab92248ff8a576b135   deterministic cleanup + runtime consumer search
46fcacebbc631fc05e0d491470b5e5482bca4533   minor evidence cleanup M1/M2/M3
```

当前 Review 结果：

```text
P4-M01-R1          = ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 = ACCEPT / FROZEN
46fcace cleanup    = ACCEPT
N01 substantive    = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

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

当前 accepted measured samples：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

semantic grading：

```text
single-mod3 structural form               STRUCTURALLY_VERIFIED
per-file phase/count/sample sequence      OBSERVED
cross-skin measured differences           DIFFERENTIAL_SUPPORTED
CFG = 1D LUT                              HYPOTHESIS
CFG = packed shader constants             HYPOTHESIS
CFG -> Source1 Phong/selfillum mapping    SOURCE1_DESIGN_CANDIDATE
actual CF semantic consumer               OPEN_UNRESOLVED
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
LTB post-mesh short field exists             VERIFIED_STRUCTURAL
field == texture slot/PieceIndex             HYPOTHESIS / NOT PROVEN
repo C# parser consumes it as material key   NO / TOOL-CODE OBSERVATION
repo ObjExporter path mirroring              TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
original CF piece -> texture binding          OPEN_UNRESOLVED
```

当前 scoped consumer negatives：

```text
BornBeast/Transformers/Jewelry/BlueDiamond text-config hits = 0
.dat consumer hits = 0
BornBeast derived-output hits = 4, DERIVED_OUTPUT_HIT only
```

这些只对已声明 scan scope 有效，不是 whole-game universal negative。

---

### 1.4 P4-M01-N01 — ACTIVE / FINAL_DOCUMENTATION_CLEANUP

原始任务：[`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md)。

当前 overlay：[`P4_M01_N01_CONTINUATION.md`](P4_M01_N01_CONTINUATION.md)。

N01 substantive question 仍是：

> **CF weapon 的 model/piece、texture family、WeaponShader CFG 究竟由哪个原 engine/config/resource path 关联和消费？**

但当前 local corpus 已经到达可证明边界：

```text
repo/tool consumer behavior                   已查清
static asset/config scoped consumer search    已完成
original CF runtime/client consumer code      当前 corpus 不存在
```

因此 substantive 状态：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

当前唯一执行内容不是重新研究 Phase 1–5，而是 final cleanup：

```text
F1  通用 N01 generator 的 executor provenance 改成 runtime-configurable；默认 unspecified
F2  engine_binding_closure 清掉 original-runtime mirroring overclaim，并把 next_step 改成 runtime-artifact blocker
F3  可选：给 config scope counters 增加 decoded <= seen regression guard
```

F1/F2 接受后：

```text
N01 evidence cleanup = COMPLETE / FROZEN
N01 substantive      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

不得在没有新 runtime artifact 时创建新的 N01 substantive scan/run。

Blocker 解除条件：

```text
CrossFire client executable
engine/render/resource DLL/module
original runtime bundle/archive containing consumer code
shader/runtime package
可靠 documented material/piece binding contract
```

Blocker 解除后固定路线：

```text
strings / resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

只做静态、只读分析；不执行未知 binary；不上传 raw binary/data/**。

N01 PASS 不自动恢复 P5；即使未来 consumer closure 成立，也只代表可继续 P4-M01 native composition/final closure。

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

状态：**P4-M01 ACTIVE；当前 N01 substantive 被 runtime artifact blocker 阻塞，只剩 final documentation cleanup。**

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
| N01 deterministic/evidence cleanup through 46fcace | **ACCEPT** | — |
| weapon material consumer | repo/tool behavior 已查清；original runtime consumer 未定位 | **BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS** |
| weapon piece→texture-set binding | LTB field structural；original binding 未证 | **BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS** |
| WeaponShader CFG consumer/semantic | mod-3 structural fact 已证，semantic consumer 未知 | **BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS** |
| DTX/TGA channel/binding semantics | storage/layout 部分已证，original engine role/order 未闭合 | P4-M01 / runtime evidence |
| N01 final documentation cleanup | F1 provenance generator + F2 closure wording | **CURRENT** |
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

当前 corpus 尚不能满足，因此 N01 substantive 处于 `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS`。

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

> **Local Executor 同步最新 `master`，读取 `CODEX_TASKS.md` 与 `P4_M01_N01_CONTINUATION.md`。不要重跑 N01 Phase 0 / Phase 1–5，不要再次扫描同一 repo/data corpus。当前只完成 final cleanup：F1 将 N01 通用 generator 中硬编码的 `MiniMax-M3 / Claude Code` provenance 改为 runtime 参数/环境变量驱动，缺省 `unspecified`，同时保留 commit footer `NON_AUTHORITATIVE`；F2 清理 `engine_binding_closure.json` 中“原 CF runtime appears to use directory mirroring”的 overclaim，只保留 repo exporter 的 `TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE`，并把 `next_step` 改为等待新的 CF runtime/client artifact 或等价 documented consumer contract；F3 可选增加 `config_candidates_decoded <= config_candidates_seen` regression guard。完成后 push scoped changes 到 `master` 并停止。当前 N01 substantive 状态固定为 `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS`，P4-M01 仍 ACTIVE，P5-T02 继续暂停。**