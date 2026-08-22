# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-22
>
> 项目唯一 authoritative progress/status：**本文件第 1 节**
>
> 当前执行任务：**P4-M01-R1 — BornBeast native material targeted continuation**
>
> 当前状态：**P4 baseline `PASS / FROZEN`；P4-M01 `ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`；P4-M01-R1 `ACTIVE / TARGETED_REWORK_REQUIRED`；P5 `ACTIVE` 但 T02 `PAUSED_BY_P4_M01`**
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
| **P4-M01** | **ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE** | 当前父任务：用 BornBeast 闭合 CF 原生材质解码/绑定/shader 语义 |
| **P4-M01-R1** | **ACTIVE / TARGETED_REWORK_REQUIRED** | R1 已有部分 evidence 被接受；当前只修剩余 DTX/CFG/stage-2 binding/H2 问题 |
| P5-T01 | PASS / USER_REFERENCE_CONFIRMED | 雷神官方目标图已确认 |
| P5 LEGACY PRE-SCAN | EXECUTION_PASS / PRESERVED_FOR_REUSE | 本地广召回候选池保留 |
| P5-T02 | **PAUSED_BY_P4_M01** | 候选缩圈已做；等待可复用原生材质恢复方法后继续 Transformers |
| P5-T03 | BLOCKED_BY_T02 | 完整 Resource Graph / provenance closure |
| P5-T04 | BLOCKED_BY_T03 | Chat/Sol final identity review |
| P6 | BLOCKED_BY_P5 | 最终资产替换与发布质量 |
| P7 | FUTURE | visible Inspect、手指 IK/retarget、CF 原动画等增强 |

状态命名规则：

```text
NATIVE_MATERIAL_RECOVERY_INCOMPLETE = P4-M01 正在执行、尚未满足 native material closure
REWORK_REQUIRED                     = R1 初始广泛纠错状态
TARGETED_REWORK_REQUIRED            = R1 已部分通过 Review，只剩明确的 targeted open items
NATIVE_MATERIAL_RECOVERED            = P4-M01 completion result（需 Chat/Sol Review）
```

当前 Agent 启动入口：

```text
AGENTS.md
-> plan.md 第 1 节
-> CODEX_TASKS.md
-> P4_TASKS.md
-> P4_M01_TASK_SPEC.md
-> P4_M01_REWORK_R1.md
-> P4_M01_R1_CONTINUATION.md   <- 当前直接执行入口
```

`P4_M01_R1_CONTINUATION.md` 不是 R2；它是同一个 R1 在最新 Review 后的 continuation overlay。

`P5_T02_TASK_SPEC.md` 当前是**暂停后的恢复协议**，不是当前 Local Executor 的第一执行入口。

---

### 1.2 P4 baseline — PASS / FROZEN

P4 baseline 已完成 P4-T01～T09、用户 Gate 和独立 Review。历史最终结论：`PASS WITH RISK`，允许 `PASS / FROZEN`。

冻结实现/证据：

```text
Implementation baseline: 10aa99b770e575300ca3c28324ef3de3d5b70c6b
frozen build run:       run_20260819_170013_270792
RV-04 evidence commit:  fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
frozen addon:           p_cf_bornbeast_m4a4_p4_frozen_noop_01
runtime slot:           M4A4
internal model:         weapons/v_rif_m4a1.mdl
```

P4 baseline **已经证明**：

- manifest-driven 本地 CF LTB fresh build；
- M4A4 Source skeleton / sequence / attachment contract；
- mesh→bone、SMD/QC、studiomdl、Crowbar roundtrip；
- validation / package / staging / deploy provenance；
- destructive-operation guards / negative tests；
- frozen/no-op Inspect changed-runtime 用户 Gate。

P4 baseline **从未证明**：

- Prototype 就是最终雷神；
- CF 原生材质已经正确解码；
- 第三方/网络材质可以成为 final；
- visible Inspect / 手指接触 / Blender retarget 已解决；
- CF 原动画/声音/world model 已最终化。

因此 P4 baseline 继续冻结。P4-M01 不修改或否定上述技术证据。

---

### 1.3 P4-M01 — ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE

#### 为什么明确返回 P4

provenance 审计确认，P4 可识别 BornBeast Prototype 曾使用：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

作为 base/self-illum 派生输入，再转换为 Source VTF。

这说明 P4 的**模型/编译/MIGI 技术链成立**，但 P4 的**CF native material fidelity 尚未闭合**。

正式主协议：[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

核心目标：

```text
本地 BornBeast LTB / UV
+ 本地 PV DTX
+ 本地 Alpha / Normal / Specular TGA
+ 本地 WeaponShader CFG
+ 本地同族 variant
-> 恢复真实 container / pixel format
-> 恢复 material binding
-> 逆 CFG / render-style 语义
-> 建立可解释 shader hypothesis
-> 0 external pixels 的 native material render
-> 可重复 closure
```

外部 CS1.6 BornBeast texture 只能作为 reference/differential control，不得提供 final pixels。

#### R0 exploration 与 R1 原始纠错

Local Executor 在 commit：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5
```

提交了 A→I 探索性代码/evidence；随后 `39e14ff6c594ad81f1b077aeeaea5645d81e02be` 一度把状态描述成“6/8 PASS，只差用户视觉 Gate”。

Chat/Sol Review 不接受该 closure，创建：

[`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md)

R0 中继续复用：A provenance、B inventory 起点、G variant differential、hash/path、脚本骨架和历史 evidence；旧错误结论不删除但被 supersede。

#### commit bded9e8 — R1 有效推进，但未完成

当前 Local Executor continuation commit：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
```

新增：

```text
scripts/material_recovery/r1_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/r1/**
```

该轮没有上传 `data/**`，也没有自行改 `plan.md` 宣布 PASS。Chat/Sol 当前正式 Review：

| Step | 当前 Review 状态 | 当前判断 |
|---|---|---|
| A provenance | **ACCEPT / REUSE** | 不重跑 |
| B inventory | **REUSE_WITH_CAUTION** | 作为扫描起点 |
| C DTX | **PARTIAL_ACCEPT / TARGETED_REWORK** | formal header/LZMA 纠错有效；1024 stride/no-mip 关键 scan 未进入最终可重跑脚本；tail/channel order 仍 open |
| D TGA | **ACCEPT / STRUCTURAL** | 已按正式 footer/header offset 纠正，旧 10-byte-shifted repair 被 supersede |
| E binding | **STAGE1_PARTIAL_ACCEPT / STAGE2_OPEN** | mesh-associated numeric field 是真实结构 evidence；`= texture slot` 与 slot/model→texture set 仍需 engine/config proof |
| F CFG | **PARTIAL_ACCEPT / REFRAME** | 237-file 3-byte periodic/mod-3 发现有效；RGB/BGR triplets vs scalar+padding 仍是竞争解释 |
| G variant differential | **ACCEPT / REUSE** | supporting evidence 保留 |
| H shader hypotheses | **DIAGNOSTIC_ONLY / REWORK** | 旧 magic constants 已撤销；H2 `step=97` 存在 byte-phase mixing bug |
| I closure | **NOT READY / CONTINUE** | 正确保持 `NATIVE_MATERIAL_RECOVERY_INCOMPLETE` |
| J Source 1 integration | **DEFERRED** | I 真正通过前不执行 |

详细 Review 与精确执行要求：[`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md)。

#### 当前已接受，不要无理由重跑

```text
A provenance audit
G variant inventory/differential
R1-D formal TGA repair/decode correction
R1-E 已抽取的 mesh-associated numeric-field census
```

R1-D 的正式关系：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular 已按该结构恢复为 1024×1024 / 24bpp，并记录 offset/hash。后续 channel engine semantics 可继续验证，但不需要再做旧 TGA offset 纠错。

#### 当前剩余 targeted work

**R1-C DTX**

已接受：正式 `-2/-3/-5` header route、LZMA 纠错、旧 `512x256 full mip + 163-byte trailer` 撤销、3-byte periodic pixel-like structure 有强支持。

仍需：

- 把 report 声称的 width/stride candidate scan 真正提交成可重跑代码；
- 输出关键 width 候选完整 score/rejection matrix；
- full-file + 2212-byte tail periodicity；
- continuity/correlation 覆盖所有变化 channel；
- terminal remainder semantics；
- RGB/BGR/channel order。

在这些 evidence 完成前，`1024 width / single continuous image / no mips` 维持 strong hypothesis，不升级为最终 engine-verified fact。

**R1-E stage-2 binding**

接受“存在 mesh-associated post-mesh numeric field”这一结构事实；其含义是否为 texture slot 仍 provisional。

下一轮优先使用现有基础设施：

```text
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureConfigIndex.cs
CFRezManager/Decoders/LithTech/Models/LithTechTextureMappingScanner.cs
CFRezManager/Decoders/LithTech/Models/LithTechDatTextureReferenceIndex.cs
CFRezManager/Decoders/LithTech/Models/TextureReferenceResolver.cs
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureLoader.cs
```

目标是证明 model/skin/numeric field → DTX/TGA/CFG texture set 的 engine/config/resource-table 关系，或产出明确 negative result。

**R1-F CFG**

237 个 WeaponShader CFG 的 3-byte periodic/mod-3 pattern 保留，但至少要同时测试：

```text
H-CFG-A = RGB/BGR color triplets，其中两 channel 固定/近固定 0xFF
H-CFG-B = scalar samples + padding/alignment
```

当前脚本 `if raw[i] != 0xFF` 会删除合法值为 255 的 sample，因此不能把过滤后数量称为完整 record/texel count。必须保留完整 bytes，并精确 accounting 492/506/642。

**R1-H shader diagnostic**

`r1_shader_closure.py` 使用 `step = 97`；因 `97 % 3 == 1`，采样起点在三个 byte phases 间轮换，variable-channel census 不可靠。改成 pixel-index 或 `3*k` byte stride。修后 H2 仍是 approximation/diagnostic，除非 E/F 得到 engine semantics。

#### 当前状态

```text
P4-M01    = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1 = ACTIVE / TARGETED_REWORK_REQUIRED
```

当前**不是用户 final visual Gate**。不要执行 J，不恢复 P5-T02。

P4-M01 真正 PASS 必须是：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

然后才恢复 P5-T02。

---

### 1.4 P5 — ACTIVE，但 T02 暂停等待 P4-M01

P5 目标仍是：**最终雷神资产定位**。

标准顺序：

```text
P5-T01  官方图鉴 Web Search + 用户确认目标图                 PASS
P5 LEGACY PRE-SCAN                                          PASS / REUSE
P5-T02  本地候选缩圈 + native material finalist + 用户确认   PAUSED_BY_P4_M01
P5-T03  Resource Graph / provenance closure                 BLOCKED_BY_T02
P5-T04  Chat/Sol final identity review                      BLOCKED_BY_T03
```

#### P5-T01 — PASS / USER_REFERENCE_CONFIRMED

固定 evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

官方目标为用户已确认的 `M4A1-雷神`。除非 evidence 损坏或用户明确否决，不重跑 Web Search。

#### LEGACY PRE-SCAN — PRESERVED_FOR_REUSE

历史提交：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

历史结果：

```text
data/** inventory       165082 files
recalled candidates      2856
LTB candidates           1281
canonical LTB inspected   441
```

输出：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

旧 score 只是 recall priority，不是 identity confidence。

#### P5-T02 — PAUSED_BY_P4_M01

已经完成：

```text
confirmed official reference
-> legacy pre-scan reuse
-> M4/M4A1 PLAYERVIEW narrowing
-> exact SHA / geometry cluster
-> C029/C103 finalist diagnostics
```

当前不继续让用户在灰模/伪材质之间强选。

P4-M01 PASS 后，P5-T02 恢复：

```text
validated P4-M01 material-recovery method
-> apply to M4A1_S_Transformers family
-> Transformers-specific DTX/TGA/CFG/binding differential
-> native material acceptance gate
-> native-material side render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

若方法对 Transformers 不可直接迁移，可做变体特有扩展，但不能退回 external texture，也不能把未验证格式当作正确 diffuse。

#### P5-T03 / T04

T03 只在 T02 native material + user visual gate 完成后建立完整：

```text
model LTB
-> diffuse/base/lookup/DTX/TGA
-> Alpha/Normal/Specular/emissive/detail
-> Shader/CFG/material
-> QV/world
-> WAV
-> animation/config
```

T04 由 Chat/Sol 输出：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才进入 P6。

---

## 2. 三条工作线与依赖关系

### Track A — Source 1 conversion baseline

回答：**已知 CF 武器资产能否稳定进入 CS:GO Legacy Source 1。**

状态：P4 baseline 已冻结。

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

回答：**CF 原生纹理/材质究竟如何被解释、绑定和组合。**

当前：P4-M01 ACTIVE，具体处于 P4-M01-R1 targeted continuation。

先 BornBeast benchmark，方法稳定后再迁移到 Transformers。

### Track C — Final Leishen identity

回答：**真正雷神对应本地哪套 LTB/DTX/TGA/CFG/WAV。**

当前：P5 ACTIVE，但 T02 暂停等待 Track B。

依赖：

```text
Track A frozen technical baseline
       +
Track B validated native material method
       +
P5 official reference / candidate evidence
       -> final identity
```

---

## 3. 资产来源政策

### final 允许来源

- 本地 CF 原始资源：模型、材质、动画、声音的唯一 final 来源；
- 本地 CS:GO Legacy VPK：目标 skeleton、sequence、attachment、QC/runtime compatibility 基线。

### reference-only

- CF 官方武器百科图片；
- Wiki/媒体/论坛截图；
- 第三方 MOD；
- 网络 GoldSrc/CS1.6 texture；
- P4 external BornBeast texture。

reference 可以用于搜索、视觉对照、differential hypothesis；**不能提供最终像素或资源 provenance**。

### 禁止

- AI 生成/重绘 texture 填洞；
- external texture 作为 final base color；
- 从 external 图采样/烘焙颜色后冒充 local CF；
- 用第三方 MOD 成功运行证明 CF parser 语义正确；
- 在 report 中隐去 external source；
- 修改/删除 `data/**` 来配合 Git；
- 为当前任务覆盖历史 P4 frozen evidence。

---

## 4. P4 frozen contract 与 P4-M01 可修改边界

### 继续冻结

- M4A4 runtime slot；
- 57-bone reference；
- sequence / attachment contract；
- frozen build/package/deploy evidence；
- RV-01～RV-06 历史 Review；
- `p_cf_bornbeast_m4a4_p4_frozen_noop_01`。

### P4-M01 可修改/新增

- CFRezManager DTX/TGA/CFG/LTB material inspection/decoder；
- 与 material recovery 直接相关的脚本；
- 新测试；
- `work/m4a1_s_bornbeast/p4_m01_native_material/**` 派生 evidence；
- closure 后新的、独立命名的 native-material test addon。

如果必须改变 frozen skeleton/build/runtime contract 才能恢复材质，P4-M01 必须停止并返回 Chat/Sol，不得静默修改 baseline。

---

## 5. 已知关键事实与当前判断

1. P4 build/report 已证明 external CS1.6 texture 进入过 Prototype material derivation；
2. P4 material closure 过去只证明 Source `SMD -> VMT -> VTF` 引用存在，不证明 VTF 像素来自正确 CF native decode；
3. 正式 `DtxThumbnailDecoder.cs` 支持 LithTech DTX version `-2/-3/-5`；BornBeast PV DTX 不满足该正式 header，且 R1 evidence 强支持 uncompressed 3-byte periodic pixel-like payload；
4. 旧 `512x256 full-mip + 163-byte trailer` 已撤销；`1024 stride / single image / no mips` 当前是 strong hypothesis，需把关键 scan 真正纳入可重跑脚本；2212-byte tail 与 channel order 仍 open；
5. `TgaThumbnailDecoder.cs` inserted repair 使用 `footerOffset = TRUEVISION - 8`、`headerOffset = footerOffset + 26`；R1-D 已按该逻辑纠正并接受；
6. LTB 中存在 mesh-associated post-mesh numeric field；其确切语义是否为 texture slot、以及 stage-2 texture-set binding 尚未证明；
7. 237-file WeaponShader CFG corpus 存在稳定 3-byte periodic/mod-3 结构；RGB/BGR triplets 与 scalar+padding 仍需竞争验证，semantic parameter 未闭合；
8. `r1_shader_closure.py` H2 的 `step=97` 存在 byte-phase mixing bug，修复后仍只算 diagnostic approximation；
9. 同几何不同 skin 是恢复 binding/shader 语义的重要 differential evidence；
10. C029/C103 当前不需要用户强选，先解决 material method。

---

## 6. 技术债与阻塞级别

| 项目 | 当前判断 | 当前 blocker |
|---|---|---:|
| Native DTX width/no-mip/tail/channel order | R1-C targeted reproducibility + tail analysis | **P4-M01-R1** |
| TGA formal repair | **R1-D ACCEPT / STRUCTURAL**；不再是当前 blocker | — |
| WeaponShader CFG framing/semantic binding | triplet-vs-scalar + full-byte accounting + engine semantic | **P4-M01-R1** |
| LTB/material stage-2 binding | numeric field 结构已发现，engine/config texture-set mapping 未闭合 | **P4-M01-R1** |
| Shader H2 diagnostic implementation | `step=97` phase-mixing bug | **P4-M01-R1** |
| BornBeast Prototype external material provenance | 已确认，不能 final | **P4-M01** |
| Transformers native material 未恢复 | P5 finalist 无法正确渲染 | **P5-T02，等待 P4-M01** |
| 最终雷神 identity 未确认 | 不能进入 P6 | **P5** |
| CF animation clips 未完整解码 | 不影响当前材质任务 | P7 |
| 03–08 精确机械语义未证明 | Prototype Parent fallback | P6/P7 视 final asset 处理 |
| visible Inspect / 手指穿模 | 不影响当前材质任务 | P7 |
| world/drop model | 第一人称当前不受影响 | P7 |

---

## 7. Definition of Done

### 7.1 P4 baseline — DONE

保持历史 `PASS / FROZEN`；不因 P4-M01 材质纠偏而取消。

### 7.2 P4-M01 DoD

必须满足：

- BornBeast native material inputs 完整 inventory；
- DTX/TGA interpretation 有结构证据，且关键验证在提交脚本/正式 decoder 中可复现；
- mesh/material binding 有结构/engine evidence；
- CFG/render-style 语义达到足够可重建程度；
- visible color 全部来自 local CF / verified semantics；
- 0 external pixels；
- clean-output 可重复生成；
- 原生材质渲染能稳定辨认 BornBeast 的主要颜色分区、图案和高光/能量区域；
- external CS1.6 texture 只作为 reference；
- 输出经过 R1 修正后的 closure；
- Chat/Sol Review 允许恢复 P5-T02。

### 7.3 P5 Asset Identity DoD

- T01 official reference 已确认；
- P4-M01 material method 已 PASS；
- Transformers native material finalist 已恢复；
- 用户确认本地 candidate；
- model/material/shader/sound/config provenance 闭合；
- 高相似候选排除理由可解释；
- Chat/Sol T04 输出 `IDENTITY_CONFIRMED`。

### 7.4 最终雷神 DoD

- 枪体和材质来自经确认的本地 CF 原始资源；
- final addon 不依赖 external MOD texture；
- mesh/UV/bones/attachments/material/sound 达到发布质量；
- 必要的 Source 1 shader approximation 与 CF native resource semantics 分开记录；
- frozen pipeline 可从 final inputs 生成独立 MIGI 发布包；
- 自动证据 + 用户实机证据 + provenance 同时成立。

---

## 8. 当前唯一下一步

> **当前 Local Executor 同步最新 `master`，读取 `P4_M01_R1_CONTINUATION.md`，从 commit `bded9e8` 和现有 R1 evidence 继续，不从零重跑。顺序：①把 DTX width/stride scan 与 full-file/tail evidence 真正提交成可重跑代码；②CFG 保留完整 3-byte triplets/合法 `0xFF`，比较 RGB/BGR-triplet vs scalar+padding；③利用仓库现有 mapping/config/index/resolver 基础设施攻 stage-2 binding；④修复 H2 `step=97` byte-phase mixing bug；⑤重建 closure，open 项继续保持 open。R1-D TGA 默认不重跑。当前不要求用户 final visual Gate，不执行 J，不恢复 P5-T02。完成并 push scoped code/evidence 后，由 Chat/Sol 再 Review。**
