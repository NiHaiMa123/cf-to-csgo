# P4_M01_R1_CONTINUATION.md — R1 targeted continuation after commit bded9e8

> parent_task: `P4-M01`
>
> rework_id: `P4-M01-R1`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / TARGETED_REWORK_REQUIRED**
>
> 本文件是 [`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md) 的**当前 continuation / Review overlay**，不是 R2、不是新阶段。若本文件与 R1 原始协议中的“当前状态/下一步”描述冲突，以本文件和 `plan.md` 第 1 节为准；R1 的安全边界、provenance、closure gate 继续有效。

---

## 1. 本轮输入与 Review 范围

本轮 Review 的 Local Executor 提交：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
P4-M01-R1: corrected DTX/TGA/binding/CFG evidence chain
```

该提交新增 `scripts/material_recovery/r1_*.py` 和 `work/m4a1_s_bornbeast/p4_m01_native_material/r1/**`，没有上传 `data/**`，也没有自行把 `plan.md` 改成 PASS。

用户报告本轮执行环境为：

```text
Harness: Claude Code
Model:   GLM-5.3-Flash internal beta / multimodal
```

commit footer 中残留的 `Co-Authored-By: Claude Opus 4.8 (1M context)` **不能作为本轮 executor model provenance**；后续 Agent 不得沿用错误模型 footer。若需要记录 benchmark provenance，应在 evidence/report 中显式写 `executor_harness` / `executor_model`，且不把具体模型绑定为任务要求。

---

## 2. Chat/Sol 当前 Review 分级

| P4-M01 step | 当前 Review 状态 | 处理方式 |
|---|---|---|
| A provenance audit | **ACCEPT / REUSE** | 不重跑 |
| B native inventory | **REUSE_WITH_CAUTION** | 作为扫描起点 |
| C DTX validation | **PARTIAL_ACCEPT / TARGETED_REWORK** | formal header/LZMA 纠错有效；1024 stride/no-mip 证据需完整可复现；tail/channel order 仍 open |
| D TGA validation/decode | **ACCEPT / STRUCTURAL** | 正式 footer/header offset repair 已纠正；默认不重跑，除非发现新反例 |
| E material binding | **STAGE1_PARTIAL_ACCEPT / STAGE2_OPEN** | LTB post-mesh numeric field 是真实结构证据；其“texture slot”语义和 slot/model→texture-set engine binding 仍需证明 |
| F CFG reverse | **PARTIAL_ACCEPT / REFRAME** | 237-file mod-3 结构发现有价值；“scalar+padding exact framing”未证明，RGB/BGR triplet 解释仍竞争；语义未闭合 |
| G variant differential | **ACCEPT / REUSE** | 继续作为 supporting evidence |
| H shader hypotheses | **DIAGNOSTIC_ONLY / REWORK** | 已撤销旧 magic constants；H2 variable-channel sampling 存在 phase-mixing bug |
| I native closure | **NOT READY / CONTINUE** | Local Executor 正确没有自封 PASS；stage-2 binding 等仍 open |
| J Source 1 integration | **DEFERRED** | I 真正通过前不执行 |

当前状态仍是：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / TARGETED_REWORK_REQUIRED
P5-T02        PAUSED_BY_P4_M01
```

用户视觉 Gate 仍不是当前 blocker。

---

## 3. 已接受：R1-D TGA repair correction

commit `bded9e8` 已按仓库正式 `TgaThumbnailDecoder.TryRepairInsertedFooterHeader` 关系纠正：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

三张 BornBeast map 均按该结构恢复为 1024×1024 / 24bpp，并精确记录 signature/footer/header offset；旧 commit `632ede4` 的 `[sig-18, sig+26)` 44-byte excision 及其 channel/previews 被 supersede。

当前默认：

```text
R1-D = ACCEPT / STRUCTURAL
```

后续不要无理由重跑 TGA。channel 的**文件语义/engine usage**仍可随 H/E/F 继续验证，但不要把“某个变化 channel”自动等同为完整 shader semantics。

---

## 4. R1-C DTX — 只做剩余 targeted rework

本轮可接受：

- 正式 `DtxThumbnailDecoder` version 集合已改回 `-2/-3/-5`；
- BornBeast 文件 offset 0 不满足正式 LithTech DTX header；
- LZMA 不再用 entropy 代替正式 header logic；
- 旧 `512x256 full mip chain + 163-byte trailer` 结论应撤销；
- 3-byte periodic pixel-like structure 与 1024-row-stride interpretation 得到明显支持。

但**当前提交的最终 `r1_dtx_revalidate.py` 没有包含 report 所声称的 `64..2048 exhaustive width scan` 实现**。脚本直接固定：

```text
W = 1024
RB = W * 3
```

后续只在已经选定的 1024 stride 上做 continuity；因此 `row_stride_1024 = VERIFIED_STRUCTURAL` 和 `single_continuous_image_no_mips = VERIFIED_STRUCTURAL` 的证据等级高于当前可复现代码实际支撑。

另外：

- channel census 只采样前 300k bytes，却把结论写成 `throughout entire file including tail`；
- boundary delta 按固定 byte phase 抽样，需覆盖所有变化 channel / pixel records；
- 2212-byte terminal remainder 仍未解释；
- RGB/BGR/channel order 仍未证明。

### 当前必须做

1. 把 width/stride candidate scan **真正提交到可重跑脚本**，至少覆盖合理 candidate widths，并输出完整 score matrix；
2. 对 `512/1024/256/...` 等关键候选给出可复现 rejection evidence，不依赖“看起来有条纹”单一视觉理由；
3. continuity/correlation 按 pixel record 和所有变化通道验证，不能只抽固定 byte phase；
4. channel periodicity 必须覆盖**全文件和 2212-byte tail**；
5. 继续分析 terminal remainder；不要因为只占 0.42% 就当作无关；
6. 在 channel order 未证明前使用 `3-byte pixel-like records`，不要把 `BGR24` 写成最终 verified semantics。

通过前推荐证据等级：

```text
no formal LithTech header      ACCEPT
not LZMA                       ACCEPT / strong
3-byte periodic structure      STRONGLY_SUPPORTED
row stride 1024                STRONG_HYPOTHESIS pending reproducible scan
single image / no mips         STRONG_HYPOTHESIS pending reproducible scan
2212-byte tail semantics       OPEN
RGB/BGR order                  OPEN
```

---

## 5. R1-E — stage 1 保留，集中攻 stage 2

本轮从 LZMA-decoded LTB 中抽取到每个 weapon mesh 后的单字节长度 + ASCII digit numeric field，BornBeast 与 Transformers 都形成 `{0..8}` 集合；offset/vertex/face/index layout 与现有 LTB decoder 结构有一致性。

这足以接受：

```text
存在与 mesh 结构绑定的 post-mesh numeric field
```

但不能仅凭位置和 `{0..8}` 自动升级为：

```text
该字段 = texture slot ID  VERIFIED
```

更不能完成：

```text
mesh -> numeric field -> DTX/TGA/CFG texture set
```

### 下一步优先使用仓库已有基础设施

先读并利用，不要重新造一套盲扫：

```text
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureConfigIndex.cs
CFRezManager/Decoders/LithTech/Models/LithTechTextureMappingScanner.cs
CFRezManager/Decoders/LithTech/Models/LithTechDatTextureReferenceIndex.cs
CFRezManager/Decoders/LithTech/Models/TextureReferenceResolver.cs
CFRezManager/Decoders/LithTech/Models/LithTechModelTextureLoader.cs
```

目标是得到 engine/config/resource-table 侧的实际关系，或通过强 differential / negative control 证明 convention。

当前：

```text
embedded numeric field              VERIFIED_STRUCTURAL
meaning == texture slot             PROVISIONAL
stage2 model/slot -> texture set     OPEN
closure condition 4                  NOT PASS
```

---

## 6. R1-F CFG — 保留 corpus 发现，重新定义竞争 hypothesis

237 个 WeaponShader CFG 的 full-corpus scan 是有价值的新 evidence：非 `0xFF` byte 集中在单一 `offset mod 3` phase，且不同文件 phase 不同。

当前可以接受：

```text
stable 3-byte periodic structure exists
within each file, two positions are predominantly/all 0xFF and one position carries variation
```

但当前脚本：

```python
values = [raw[i] ... if raw[i] != 0xFF]
```

会把变化 channel 中**合法值为 255 的 sample**直接删除，因此 `sample_count` 不能自动视为 record/texel count。

而且以下两种解释都仍成立，必须正面对比：

```text
H-CFG-A: 3-byte RGB/BGR color records，其中两 channel 固定 255、一个 channel 变化
H-CFG-B: scalar samples + two padding bytes，且每文件存在 alignment/phase
```

不要把 H-CFG-B 直接命名为 `exact framing resolved`。

### 当前必须做

- 按完整 3-byte triplets 输出统计，不丢任何 `0xFF`；
- 明确 492/506/642 的完整 triplet + partial-tail accounting；
- 分析每个 byte position 的分布、平滑性和跨文件相位；
- 用更多 CFG 与实际 engine/config consumer 寻找 RGB/BGR/scalar 语义证据；
- CFG semantic parameter 继续保持 `UNRESOLVED`，直到有 engine-side binding。

---

## 7. R1-H — 修复 sampling bug，但继续 diagnostic-only

`r1_shader_closure.py` 中 H2 用：

```python
step = 97
for i in range(0, len(specular), step):
    for c in range(3):
        counts[c][specular[i + c]] ...
```

因为 `97 % 3 == 1`，每次采样起点会在三个 byte phase 间轮换，导致 `counts[0..2]` 混入不同实际 channel；随后选择 `var_ch` 的结果不可靠。

修法至少应按 pixel index 采样，或保证 byte stride 为 `3*k`。修复后 H2 仍只算：

```text
APPROXIMATION_HYPOTHESIS / DIAGNOSTIC_ONLY
```

除非 E/F 得到 engine composition semantics，否则不因 preview 好看而升级。

---

## 8. 当前唯一执行顺序

下一位 Local Executor 从 commit `bded9e8` 继续：

```text
1. R1-C: commit reproducible width/stride scan + full-file periodicity/tail analysis
2. R1-F: triplet-vs-scalar competing hypotheses; no dropping 0xFF samples
3. R1-E stage2: use existing mapping/config/index/resolver code to seek engine binding
4. R1-H: fix channel-sampling bug; regenerate diagnostic previews only after corrected inputs
5. R1-I: regenerate closure with unresolved items left unresolved
```

默认**不要重跑**：

```text
A provenance
G variant inventory/differential
R1-D formal TGA repair
R1-E already-extracted numeric-field census
```

除非新 evidence 明确产生冲突。

禁止：

- 执行 J；
- 恢复 P5-T02；
- 请求用户做 final visual gate；
- 把 DTX 1024/no-mip、numeric field=texture slot、CFG scalar+padding 直接写成 engine-verified fact；
- 复制错误的 executor model/co-author provenance。

---

## 9. 本 continuation 的完成条件

Local Executor push 后，Chat/Sol 至少要能复核：

- DTX width/no-mip 的关键 scan 在提交脚本里可重跑，report 不引用未提交实验；
- DTX full-file/tail/channel evidence 与结论等级匹配；
- CFG 不再因过滤 `0xFF` 而改变 record/sample accounting；
- CFG triplet-vs-scalar hypothesis 有明确 evidence matrix；
- stage-2 binding 使用了现有 mapping/config infrastructure，或有明确 negative result；
- H2 phase-mixing sampling bug 已修；
- `native_material_closure_r1.json` / superseding closure 仍不把 open 项伪装成 PASS。

完成后由 Chat/Sol 决定继续 P4-M01、进一步 targeted rework、或允许进入 native material closure。