# P4_M01_REWORK_R1.md — BornBeast native material evidence correction

> parent_task: `P4-M01`
>
> rework_id: `P4-M01-R1`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / REWORK_REQUIRED**
>
> 本 R1 是 P4-M01 的当前纠错执行入口，不是新阶段。父任务继续保持：`P4-M01 = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`。

---

## 1. 为什么需要 R1

Local Executor 在 commit `632ede449578f688cea7e6b5f40cbf03700aaaa5` 提交了 P4-M01 A→I 的大量探索性代码/evidence，并在 commit `39e14ff6c594ad81f1b077aeeaea5645d81e02be` 把结果记录到 `plan.md`。

这批工作**不是废弃**：provenance、inventory、variant enumeration、脚本骨架与派生 evidence 都有复用价值；Git/data 边界也基本遵守。

但 Chat/Sol Review 发现多个关键结论把 hypothesis / filename convention / byte-count fit 提升成了“verified”，因此当前不能把 P4-M01 解释为“只差用户视觉 Gate”。

当前正确状态是：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / REWORK_REQUIRED
P5-T02        PAUSED_BY_P4_M01
```

用户视觉确认**不是当前 blocker**。必须先修复 binary/decode/binding/CFG evidence，再重新生成 native shader preview。

---

## 2. 对 commit 632ede4 的 Review 分级

| P4-M01 step | R1 前 Review 状态 | 处理方式 |
|---|---|---|
| A provenance audit | **ACCEPT / REUSE** | 不无理由重跑；只在发现 hash/path 错误时修正 |
| B native inventory | **REUSE_WITH_CAUTION** | 保留 inventory；不得把“未发现”自动升级为“确定不存在” |
| C DTX validation | **REWORK** | formal decoder/version/LZMA/dimension/orientation/trailer 重新验证 |
| D TGA validation/decode | **FAIL / REWORK** | 已发现 embedded footer/header offset 处理与正式 decoder 不一致 |
| E material binding | **INCOMPLETE** | basename+directory 只能证明 family association，不能满足 structural binding gate |
| F CFG reverse | **INCOMPLETE** | framing/channel/order/trailing bytes/semantic slot 未闭合 |
| G variant differential | **ACCEPT AS SUPPORTING EVIDENCE / REUSE** | 保留 inventory/diff 数据；具体 semantic interpretation 仍需 R1 验证 |
| H shader hypotheses | **DIAGNOSTIC_ONLY** | 现有 H1/H2 公式不可用于 closure；待 C/D/E/F 修正后重建 |
| I native closure | **NOT READY** | 旧 `6/8 PASS` 结论撤销；不得等待用户视觉 Gate 代替技术 closure |
| J Source 1 integration | **DEFERRED** | I 真正通过前不执行 |

旧 evidence 文件保留为历史探索性 evidence，不删除、不覆盖其 provenance；R1 可以生成 corrected/reviewed 版本或在原文件中明确 superseded 字段，但必须能区分旧结论和新结论。

---

## 3. R1-C — DTX formal revalidation

当前旧结论：

```text
PV-M4A1_S_BornBeast.DTX
= headerless BGR24 512x256 full mip chain + 163-byte trailer
```

只能视为**高优先级 hypothesis**，不能视为 verified。

### 已发现的问题

1. `p4m01_dtx_validate.py` 声称模拟 `DtxThumbnailDecoder.TryReadHeader`，但仓库正式 decoder 的受支持 version 是：

```text
-2  LT1
-3  LT1.5
-5  LT2
```

旧脚本却使用一组正整数 `1..34` 作为 `KNOWN_VERSIONS`，因此“独立复现 repo decoder”这一证据无效。

2. 旧脚本用 `entropy > 7.5` 近似判断 LZMA。R1 必须直接复用/等价复现仓库：

```text
LzmaAloneDecoder.IsCompressed
LzmaAloneDecoder.TryPrepareData
```

不能用 entropy 代替正式判定。

3. `512x256` 与 `256x512` 的 RGB24 full-mip byte count 相同。旧脚本仅因候选列表顺序/字符串选择就偏向 `512x256`，没有证明 orientation/dimension。

4. 旧 report 对 trailing bytes 曾出现 `163` 与结论文字 `164` 不一致。R1 必须精确记录 byte accounting。

### R1-C 必须完成

- 对照当前 `CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs` 的**真实** version/header parsing；
- 使用真实 LZMA detection/prepare logic 或可证明完全等价的实现；
- 明确原始 bytes、prepared bytes 是否变化；
- 枚举至少 RGB/BGR24、RGBA/BGRA32、Palette、DXT1/3/5、可能的 raw payload interpretation；
- 对所有 near-fit dimensions 做 byte-count 对比，不允许只挑 `512x256`；
- 用 UV范围、同族 DTX dimensions、mip-level spatial consistency、row/column correlation、orientation A/B 等证据区分 `512x256` 与 `256x512`；
- 分析 163 trailing bytes 的结构/分布/是否 metadata/下一层数据，而不是只称为 trailer；
- 输出 accepted/rejected matrix。

通过 R1-C 前，不得再写：

```text
base DTX role = special/energy VERIFIED
512x256 BGR24 VERIFIED
```

最多写 `hypothesis` / `supported` / `not yet proven`。

---

## 4. R1-D — TGA repair/decode correction

这是当前已确认的实现级错误。

仓库正式 `TgaThumbnailDecoder.TryRepairInsertedFooterHeader` 的关键逻辑是：

```text
signatureOffset = TRUEVISION signature position
footerOffset    = signatureOffset - 8
headerOffset    = footerOffset + 26
```

即 inserted block 的结构按正式 decoder 是：

```text
[26-byte Truevision footer][18-byte TGA header]
```

旧 `p4m01_tga_decode.py` 使用：

```text
block_start = TRUEVISION - 18
block_end   = TRUEVISION + 26
```

即按 `[18-byte header][26-byte footer]` 删除 44 bytes，和正式 decoder 不一致。

例如 Alpha：

```text
TRUEVISION signature = 886830
旧删除起点           = 886812
正式 footerOffset    = 886822
```

相差 10 bytes。即使删后总长度恰好等于 `1024*1024*3`，也不能证明像素流正确。

### R1-D 必须完成

- 直接调用/严格等价复现 `TryRepairInsertedFooterHeader` / `TryBuildRepairedTga`；
- 对 Alpha/Normal/Specular 分别记录：signatureOffset、footerOffset、headerOffset、header bytes、footer bytes；
- 验证 repaired TGA header 的 width/height/bpp/descriptor/origin；
- 用正式 decoder 输出与 R1 脚本输出做 hash/pixel equality cross-check；
- 正确 repair 后再统计 channels；
- 重新判断 `alpha=G`、`normal=B`、`specular=R` 等 channel-role hypothesis。

旧 `tga_decode_matrix.json`、旧 TGA preview 和依赖旧 preview 的 H1/H2 不能作为 closure evidence。

---

## 5. R1-E — material binding evidence

旧 `material_binding_report.json` 的核心依据是：

```text
same basename
+ directory role names
+ LTB string scan found no inline texture refs
```

这足以支持：

```text
resource-family association
```

但不满足 Task Spec E 的：

```text
mesh/piece -> material slot/index -> texture/shader/render-style structural binding
```

### R1-E 必须完成

优先路线：

1. 继续检查 LTB binary/decompressed structure，不要只做 ASCII string scan；
2. 检查 piece/material index、render style、texture index/table、numeric refs、resource IDs；
3. 检查 CF 配置/资源表是否存在外部 binding，而不是假定必须 inline 在 LTB；
4. 用同 geometry 不同 skin differential 验证 binding changes；
5. 如果经过多条独立路线后确认 CF 就采用 basename/directory convention，则必须用跨样本、negative-control、缺失/错名样本或运行时/工具代码 evidence 证明 convention 是 engine contract，而不是命名巧合。

若仍只能得到 filename+directory relation：

```text
E = INCOMPLETE / PROVISIONAL
```

closure 条件 4 不得 PASS。

---

## 6. R1-F — CFG framing + semantics

旧 CFG 结果可保留为 raw-byte differential，但不能称为 semantic reverse 完成。

### 已发现的问题

- BornBeast `492 / 3 = 164`；
- Transformers `506` 不能被 3 整除，旧脚本 `len // 3` 会丢弃最后 2 bytes；
- Jewelry `642 / 3 = 214`；
- 因此“每个 weapon CFG 都是 164-pixel RGB ramp”的总结与样本本身矛盾；
- report 字段写 `*_bgr`，但旧计算/描述中又把第一 byte 当 R，存在 RGB/BGR 语义混用；
- `semantic_binding_status` 本身仍为 `PROVISIONAL_NOT_PROVEN`。

### R1-F 必须完成

- 对每个 CFG 做 exact length/framing；
- 解释 492/506/642 为什么不同；
- 不允许通过 `len // 3` 静默丢 trailing bytes；
- 检查是否存在 header/footer/record count/flags/variable-length sections；
- 明确 byte channel order；
- 增加更多传统材质/英雄材质/同武器变体 controls；
- 把 raw color-like strip 与真正 engine semantic slot 分开；
- 必须解释 CFG 如何与 DTX/TGA/render-style/material parameter 建立关系，或明确 `semantic_binding unresolved`。

仅“能画成彩条”继续视为 diagnostic-only。

---

## 7. R1-H / R1-I — rebuild only after C/D/E/F

现有 H1/H2：

```text
out = base + specular.R * 120
out = base + cfg_midcolor * luminance * 0.5
```

其中 additive、`120`、`0.5`、midcolor sampling 都没有 engine semantic evidence，因此只作为 diagnostic hypotheses 保存。

必须在 R1-C/D/E/F 达到足够证据等级后：

1. 重新生成 native layer previews；
2. 重新生成 fixed-view shader hypotheses；
3. 显式区分：
   - verified engine semantics；
   - evidence-supported approximation；
   - exploratory hypothesis；
4. 重新生成 `native_material_closure.json`。

用户视觉 Gate 只能发生在 binary/decode/binding 技术 closure 后；不得让用户肉眼判断代替 C/D/E/F。

---

## 8. 已有 evidence 的复用规则

下一位 Agent **不要从零开始**。

默认复用：

```text
commit 632ede449578f688cea7e6b5f40cbf03700aaaa5
scripts/material_recovery/**
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

### 应优先复用

- A provenance audit；
- file hashes / paths；
- B inventory 作为扫描起点；
- G variant inventory/differential 原始统计；
- LTB variant dumps；
- 现有脚本骨架。

### 必须重新验证/修正

- DTX formal parser/LZMA/dimension/orientation；
- TGA embedded footer/header repair；
- channel role；
- material structural binding；
- CFG framing/channel/semantic binding；
- shader formulas；
- closure status。

切换模型/Agent 本身**不是重跑 A/G 或删除旧 evidence 的理由**。

---

## 9. Required R1 outputs

建议在：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/r1/
```

输出至少：

```text
dtx_revalidation_r1.json
tga_repair_r1.json
material_binding_r1.json
cfg_reverse_r1.json
shader_hypotheses_r1.json
native_material_closure_r1.json
previews/**
```

如果直接修正旧脚本，必须在 report 中保留：

```text
supersedes_commit
supersedes_report
review_reason
input_sha256
script_version/git_commit
```

不得删除 commit 632ede4 的历史 evidence 来隐藏旧错误。

---

## 10. R1 completion criteria

### R1 COMPLETE / return to normal P4-M01 closure

必须至少满足：

- TGA repair 与正式 decoder 一致且 pixel equality 可交叉验证；
- DTX interpretation 的 version/LZMA/dimension/orientation/trailer 有结构证据；
- material binding 达到 Task Spec E 的结构证据，或明确指出仍无法 closure；
- CFG framing 不丢 bytes，channel/order 与 semantic status 自洽；
- 新 shader hypotheses 不依赖已被否决的旧 decode；
- `native_material_closure_r1.json` 不把 provisional 项伪装成 PASS。

R1 完成后由 Chat/Sol 再决定：

```text
CONTINUE P4-M01
PASS / NATIVE_MATERIAL_RECOVERED
BLOCKED with evidence
```

### 当前禁止

- 因旧紫色 preview 直接要求用户确认；
- 把旧 `native_material_closure.json` 的 `6/8 PASS` 当 authoritative；
- 把 `PASS(convention)` 当结构 binding；
- 把 `len // 3` CFG strip 当 semantic decode；
- 在 I closure 之前执行 J；
- 恢复 P5-T02。

---

## 11. 当前执行入口

新 Local Executor 启动后依次读取：

```text
AGENTS.md
plan.md Section 1
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md   <- 当前具体执行入口
```

然后从现有 commit/evidence 继续 R1，不从零重做项目。
