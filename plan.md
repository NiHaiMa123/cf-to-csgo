# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-21
>
> 项目唯一 authoritative progress/status：**本文件第 1 节**
>
> 当前执行任务：**P4-M01 — BornBeast 原生 CF 材质恢复基准**
>
> 当前状态：**P4 baseline `PASS / FROZEN`；P4-M01 `ACTIVE / NATIVE_MATERIAL_RECOVERY_REQUIRED`；P5 `ACTIVE` 但 T02 `PAUSED_BY_P4_M01`**
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
| **P4-M01** | **ACTIVE / NATIVE_MATERIAL_RECOVERY_REQUIRED** | 当前执行：用 BornBeast 真正闭合 CF 原生材质解码/绑定/shader 语义 |
| P5-T01 | PASS / USER_REFERENCE_CONFIRMED | 雷神官方目标图已确认 |
| P5 LEGACY PRE-SCAN | EXECUTION_PASS / PRESERVED_FOR_REUSE | 本地广召回候选池保留 |
| P5-T02 | **PAUSED_BY_P4_M01** | 候选缩圈已做；等待可复用原生材质恢复方法后继续 Transformers |
| P5-T03 | BLOCKED_BY_T02 | 完整 Resource Graph / provenance closure |
| P5-T04 | BLOCKED_BY_T03 | Chat/Sol final identity review |
| P6 | BLOCKED_BY_P5 | 最终资产替换与发布质量 |
| P7 | FUTURE | visible Inspect、手指 IK/retarget、CF 原动画等增强 |

当前 Agent 启动入口：

```text
AGENTS.md
-> plan.md 第 1 节
-> CODEX_TASKS.md
-> P4_TASKS.md
-> P4_M01_TASK_SPEC.md
```

`P5_T02_TASK_SPEC.md` 当前是**暂停后的恢复协议**，不是 Luna 现在的第一执行入口。

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

### 1.3 P4-M01 — ACTIVE / NATIVE_MATERIAL_RECOVERY_REQUIRED

#### 为什么明确返回 P4

后续 provenance 审计确认，P4 可识别 BornBeast Prototype 曾使用：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

作为 base/self-illum 派生输入，再转换为 Source VTF。

这说明 P4 的**模型/编译/MIGI 技术链成立**，但 P4 的**CF native material fidelity 尚未闭合**。

用户已明确要求：贴图正确还原不能跳过，并要求当前任务先返回 P4 解决这一基础问题。因此新增：

```text
P4-M01 = post-freeze corrective material task
```

正式协议：[`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

#### P4-M01 核心目标

用 BornBeast 作为 controlled benchmark：

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

P4-M01 的优势是：已有稳定几何/UV，同时有外部 CS1.6 flatten texture 可以**仅作为 reference/differential control**，帮助判断本地资源角色；它不得提供最终像素。

#### P4-M01 必须尝试的技术路线

1. **P4 provenance audit**：反查 external/local/derived/Source 输出链；
2. **BornBeast native inventory**：完整枚举 DTX/TGA/CFG/lookup/detail/effect 等同族资源；
3. **DTX 重新验证**：正式 LithTech DTX header/version/pixel-format 路径 vs headerless payload hypothesis；
4. **TGA 重新验证**：验证旧“插入 header/footer”解释、通道和真实 map 角色；
5. **LTB material binding**：恢复 mesh/piece → slot/index → texture/shader 的结构关系；
6. **WeaponShader CFG binary reverse**：raw RGB strip 只算可视化，不算 semantic decode；
7. **同几何不同皮肤 differential**：利用外观变化定位真正变化的文件/字段；
8. **offline shader hypotheses**：base/lookup/alpha/normal/specular/tint/emissive 分层 A/B；
9. **native material closure**：所有 visible color 输入都来自 local CF / verified semantics；
10. closure 后再做 **Source 1 integration test**，且不得覆盖历史 frozen addon。

当前继续状态：

```text
P4-M01 = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

P4-M01 PASS 必须是：

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

已知诊断不能完成 identity：

```text
C029/C103 gray geometry                    diagnostic_only
headerless-BGR24 Transformers DTX          unvalidated hypothesis
raw DTX + UV                               diagnostic_only
Alpha/Specular scalar approximation        diagnostic_only
raw-rgb-strip CFG preview                  not semantic decoding
```

当前**不继续让用户在灰模/伪材质之间强选**。

P4-M01 PASS 后，P5-T02 恢复：

```text
读取 P4-M01 validated material-recovery method
-> apply to M4A1_S_Transformers family
-> Transformers-specific DTX/TGA/CFG/binding differential
-> native material acceptance gate
-> native-material side render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

若 P4-M01 方法对 Transformers 不可直接迁移，T02 可以做**变体特有扩展**，但不能退回 external texture，也不能把未验证格式当作正确 diffuse。

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

当前：P4-M01 ACTIVE。

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
3. `DtxThumbnailDecoder.cs` 已有 LithTech DTX header/version 与 BGRA/RGBA/Palette/DXT1/3/5 路径；
4. 当前 P5 probe 的 headerless BGR24 解释必须被重新验证；
5. `CfgBinaryStripDecoder.cs` 明确只是 raw RGB strip renderer，不能作为 WeaponShader CFG semantic decode；
6. BornBeast 本地 Alpha/Normal/Specular 的旧特殊 TGA 解释也需要重新交叉验证；
7. 同几何不同 skin 是恢复 binding/shader 语义的重要 differential evidence；
8. C029/C103 当前不需要用户强选，先解决 material method。

---

## 6. 技术债与阻塞级别

| 项目 | 当前判断 | 当前 blocker |
|---|---|---:|
| Native DTX/TGA interpretation 未验证闭环 | 直接影响材质正确性 | **P4-M01** |
| WeaponShader CFG 只有 raw-strip visualization | 缺 semantic decode | **P4-M01** |
| LTB material/texture/render-style binding 不完整 | 不能证明资源组合 | **P4-M01** |
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
- DTX/TGA interpretation 有结构证据；
- mesh/material binding 有结构证据；
- CFG/render-style 语义达到足够可重建程度；
- visible color 全部来自 local CF / verified semantics；
- 0 external pixels；
- clean-output 可重复生成；
- 原生材质渲染能稳定辨认 BornBeast 的主要颜色分区、图案和高光/能量区域；
- external CS1.6 texture 只作为 reference；
- 输出 `native_material_closure.json`；
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

> **Luna 不继续 P5 C029/C103 视觉强选。当前返回 P4，执行 `P4_M01_TASK_SPEC.md`：以 BornBeast 为基准完成 provenance audit、DTX/TGA 重新验证、LTB material binding、WeaponShader CFG binary reverse、同族 differential 和 offline shader hypotheses，直到得到 0 external pixels、可重复的 `NATIVE_MATERIAL_RECOVERED` closure。完成并 push evidence 后，再由 Chat/Sol Review 是否恢复 P5-T02。**
