# P4_M01_TASK_SPEC.md — BornBeast 原生 CF 材质恢复基准

> task_id: `P4-M01`
>
> 类型: **post-freeze corrective material task**
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE**

---

## 1. 为什么当前返回 P4

P4 的 `PASS / FROZEN` 只证明 BornBeast Prototype 的几何、Source 1 编译、package、MIGI deploy 和 changed-runtime 技术链可以稳定工作；它从未证明 CF 原生材质已经正确恢复。

后续证据已经确认，P4 最终可识别 Prototype 材质使用过外部 CS1.6 资源：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此用户明确授权一个**受控的 P4 材质纠偏任务**：先在已经有稳定几何/UV、已有本地 DTX/TGA/CFG、又有外部 flatten 结果可作 reference-only 对照的 BornBeast 上，把 CF 原生材质链真正逆出来。

这不是推翻 P4 frozen conversion baseline。以下仍冻结：

- M4A4 runtime slot；
- Source skeleton / sequence / attachment contract；
- 已通过的 manifest / build / validation / package / deploy 技术证据；
- `Prototype-01` 历史 frozen artifact；
- P4 RV-01～RV-06 历史 Review 结论。

P4-M01 只重新打开：

```text
CF native material decode / binding / shader semantics / material fidelity
```

P5-T02 在 P4-M01 完成前暂停，不继续用雷神作为未知材质格式的第一试验对象。

---

## 2. 核心目标

P4-M01 必须回答：

> **仅使用本地 CF `data/**` 中 BornBeast 的 LTB / DTX / TGA / CFG 等资源，能否建立可解释、可重复、0 external pixels 的原生材质恢复流程，并把它应用到 BornBeast 枪体得到可辨识的正确材质？**

成功后，该流程必须足够通用，能够交给 P5-T02 继续处理 `M4A1_S_Transformers` / 雷神。

---

## 3. 不可违反的 provenance 规则

最终可见颜色或材质参数只能来自：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

禁止作为最终材质输入：

- CS1.6 / CSGO MOD texture；
- 网络下载 texture；
- 官方百科图片像素；
- AI 生成/补全 texture；
- 从 external reference 抠色、采样、烘焙、拟合后回写的颜色数据。

外部 BornBeast CS1.6 texture 只允许作为：

```text
reference_only / differential_control
```

用于判断某个本地 hypothesis 是否方向合理，不属于 final provenance。

---

## 4. Mandatory execution path

Luna 必须按下列路线执行。单条 hypothesis 失败不是 BLOCKED；记录 rejection evidence 后继续下一条。

### A. P4 material provenance audit

完整反查 P4 历史材质链：

```text
local CF inputs
external reference inputs
derived PNG
VTF/VMT
build/package/deploy outputs
```

至少检查：

```text
work/m4a1_s_bornbeast/p4_prototype_01/build_report.json
work/m4a1_s_bornbeast/materials/**
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
```

输出：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/provenance_audit.json
```

每个输入记录：

```text
relative_path
sha256
size
source_class = local_cf | derived_local_cf | external_reference | source1_output
used_for
```

### B. BornBeast 本地材质族完整 inventory

不要只看当前已知四个文件。扫描 BornBeast 同 basename / 同 geometry family / 同 skin family 的本地资源，覆盖至少：

```text
Models/PLAYERVIEW
ModelTextures/PLAYERVIEW
ModelTextures/AlphaMap
ModelTextures/NormalMap
ModelTextures/SpecularMap
ModelTextures/Shader/WeaponShader
```

并检查可能的：

```text
lookup / detail / emissive / env / reflection / effect / color table / render-style
```

输出：

```text
native_material_inventory.json
```

### C. DTX container / pixel-format 重新验证

**不得继续把“能排成一张图”当成格式正确。**

必须同时验证：

1. `CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs` 的 LithTech DTX header/version 路径；
2. 本地 `data/**` 文件是否已被上游流程剥离 header/container；
3. LZMA 解压前后 bytes；
4. header/version/width/height/mipmap/flags/texture group/command string 是否存在；
5. BGRA/RGBA/Palette/DXT1/DXT3/DXT5 与 headerless BGR24 等 interpretation；
6. mip chain、orientation、alpha、trailing bytes 是否结构自洽。

每种 interpretation 必须记录：

```text
layout
pixel_format
width/height
mip_layout
channel statistics
source_sha256
decoded_sha256
accepted/rejected
reason
```

如果 PV DTX 最终被证明是 mask / lookup / animated control，而不是 base color，必须明确记录其真实角色或当前证据级别。

### D. TGA 解码重新验证

当前 BornBeast Alpha/Normal/Specular 曾用“像素流中间插入 TGA header/footer”的特殊解释恢复。该解释也必须重新交叉验证，不得因为旧脚本能输出 PNG 就直接视为正确。

至少对照：

```text
CFRezManager/Decoders/Images/TgaThumbnailDecoder.cs
```

验证：

- header/footer 位置；
- width/height/bpp/origin；
- channel order；
- 是否存在压缩/分块/附加 metadata；
- 单通道信号究竟是正常 map、packed scalar，还是错误解释造成的假象。

输出：

```text
tga_decode_matrix.json
```

### E. 从 LTB / resource family 恢复真实 material binding

目标不是文件名联想，而是建立 evidence-backed binding：

```text
LTB piece / mesh
 -> material slot / texture index
 -> base / lookup input
 -> alpha
 -> normal
 -> specular
 -> shader / render-style / CFG
 -> optional tint / emissive / detail / effect
```

如果现有 `LithTechModelDecoder` 没暴露需要字段：

- 允许最小扩展 decoder；
- 允许增加 inspection/export report；
- 优先解析 material table / texture table / render-style reference；
- 所有新字段必须有 raw offset / value / parse evidence，不能只根据 basename 猜。

输出：

```text
material_binding_report.json
```

### F. WeaponShader CFG 二进制语义分析

旧的 `CfgBinaryStripDecoder.cs` 只做 raw RGB strip visualization。它的输出**不是 CFG semantic decode**。

必须重新分析 BornBeast CFG 以及对照 CFG：

1. hex / entropy / length / repeated-record；
2. endian；
3. ASCII / UTF-16 string；
4. float32 / float16 / int / bit flags；
5. 同武器不同 skin 的 byte-level differential；
6. 简单传统材质武器 vs 英雄级武器 differential；
7. `CfgTextDecoder.cs` / `CfgBinaryStripDecoder.cs` 只能作为已有工具参考；
8. 可参考公开 LithTech/Jupiter RenderStyle/DTX 资料形成 hypothesis，但字段意义最终必须由本地数据交叉验证。

输出：

```text
cfg_reverse_report.json
```

### G. 同几何不同皮肤 differential

优先找 BornBeast 及相关 M4A1-S variant 中：

- LTB SHA 相同但视觉不同；
- geometry signature 相同但 DTX/TGA/CFG 不同；
- CFG 变化与纹理变化同步的样本。

目标：定位“外观变化时真正变化的是哪些资源和哪些字段”。

输出：

```text
variant_diff_report.json
```

### H. Offline shader hypothesis renderer

找到足够 binding 后，建立最小、可重复的离线 renderer。可用 Python CPU、Blender offscreen 或其他本地可审计方式。

要求：

- 所有输入只来自 local_cf / verified derivatives；
- 每个 hypothesis 显式记录公式、采样通道、颜色空间、混合方式；
- base / lookup / alpha / normal / specular / tint / emissive / detail 可以单独开关；
- 不允许 external texture 填洞；
- 输出固定视角，便于 A/B。

推荐输出：

```text
previews/hypotheses/<id>_base.png
previews/hypotheses/<id>_layers.png
previews/hypotheses/<id>_full.png
shader_hypotheses.json
```

### I. Native material closure

只有满足以下条件，才能写：

```text
NATIVE_MATERIAL_RECOVERED
```

1. geometry / UV 来自本地 BornBeast LTB；
2. 最终 visible color 的每个输入都能追溯到 local CF 或已验证 CFG/engine semantics；
3. 实际使用的 alpha/normal/specular/lookup/emissive/detail 均有 path + SHA-256；
4. material binding 有结构证据；
5. 无 external pixels；
6. 生成步骤从 clean output 可重复；
7. 渲染结果在主要颜色分区、纹理图案、高光/能量区域和 UV 对位上能稳定辨认 BornBeast；
8. external CS1.6 reference 只参与视觉对照，没有参与生成。

输出：

```text
native_material_closure.json
```

若未满足则保持：

```text
NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

### J. Source 1 integration check（在 I 通过后）

P4-M01 不覆盖历史 frozen addon。建立新的、明确命名的测试 profile / addon，把 native-only 恢复结果转成 Source 1 可承载的 VMT/VTF 组合。

必须：

- 不覆盖 `p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
- 新 addon 明确标记 `p4_m01_native_material_test`；
- report 记录 native inputs -> derived texture -> VTF/VMT -> addon 的完整 hash chain；
- 若 CF 原 shader 含 Source 1 无法一比一表达的动态效果，必须把“资源语义已恢复”和“Source 1 shader 等效近似”分开记录，禁止混为一谈。

如果需要用户实机确认，只在技术 closure 完成后请求用户检查材质，不得用用户肉眼替代二进制格式/binding 证据。

---

## 5. 允许修改范围

允许：

```text
CFRezManager/Decoders/**
CFRezManager/相关 inspection/export code
scripts/material_recovery/**
scripts/weapon_port/与材质恢复直接相关的新增脚本
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

允许新增测试。

禁止为了方便修改：

```text
历史 P4 frozen run / package / deploy evidence
Prototype-01 frozen addon 内容
P4 RV-01～RV-06 历史证据
Source skeleton / sequence / attachment contract
```

若必须改变 frozen conversion contract 才能继续，停止并返回 Chat/Sol。

---

## 6. Git / data / evidence

遵守 `AGENTS.md`：

- 只以 `master` 作为 Agent handoff；
- `data/**` 永不上传；
- 只 stage 明确路径；
- 不使用 broad staging / force push / destructive clean；
- 报告记录 git commit、工具版本、输入 path/hash/size 和输出 hash。

原始 DTX/TGA/LTB/CFG 不提交；只提交代码、报告和派生预览。

---

## 7. Completion / handoff

### PASS

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

必须满足 §4-I；若执行 Source 1 integration，则相应 closure 也必须通过。

P4-M01 PASS 后：

```text
STOP BornBeast material reverse engineering
-> push scoped code + evidence to master
-> P5-T02 resume
-> apply the validated material-recovery method to M4A1_S_Transformers
```

### CONTINUE

```text
P4-M01 = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

单个 decoder/shader hypothesis 失败时使用此状态，记录 rejection 后继续。

### BLOCKED

只有在以下情况才 BLOCKED：

- 本地 BornBeast 原始资源缺失；
- 关键格式/绑定所需数据实际不存在；
- 现有环境无法读取必要 bytes，且多条独立路线都无法继续；
- 需要修改 frozen conversion contract 才能继续。

### INVALID

包括：

- 用 external MOD texture 作为最终输入；
- 用肉眼“看起来像”替代格式/绑定证据；
- 把 raw CFG strip preview 当 semantic decode；
- 修改或覆盖历史 frozen evidence；
- 上传 `data/**` 原始资产；
- 自行把 P5/雷神 identity 写成最终确认。
