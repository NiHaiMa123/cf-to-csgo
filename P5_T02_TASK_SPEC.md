# P5_T02_TASK_SPEC.md — 本地候选缩圈、原生材质还原与百科式侧视锁定

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **ACTIVE / NATIVE_TEXTURE_RECOVERY_REQUIRED**

---

## 1. Purpose

P5-T02 只在新 P5-T01 已完成 `USER_REFERENCE_CONFIRMED` 后执行。

T02 的问题是：

> **本地 CF `data/**` 里，哪一个第一人称 M4/M4A1 模型在正确还原本地 CF 原生材质后，与用户确认的官方武器百科目标图一致？**

T02 不再做 Web Search；官方视觉 Ground Truth 来自：

```text
work/p5_leishen/t01_reference/official_reference.json
```

T02 不允许仅凭 `Transformers` / `BornBeast` / `Thor` / `Leishen` 等内部 token 预锁身份。

**新增硬约束：原生贴图/材质还原不可跳过。灰模、错误解释的 DTX、仅 Alpha/Specular 的近似材质、外部 MOD 贴图，都只能用于诊断，不能完成 T02。**

---

## 2. Preconditions

必须同时满足：

1. `P5-T01 = PASS / USER_REFERENCE_CONFIRMED`；
2. `official_reference.json.user_confirmation = confirmed`；
3. 有官方详情页 URL 和官方图片 URL；
4. 历史本地广召回 evidence 可读：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
```

历史广召回现在语义上属于 [`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)，不要重跑全部 16 万文件，除非这些 evidence 缺失或明显失效。

若 T01 尚未确认：

```text
BLOCKED_BY_T01_USER_REFERENCE
```

并停止。

---

## 3. Candidate narrowing

### 3.1 Reuse legacy pre-scan

优先从已有 candidate index/matrix 过滤，不重新全量 inventory。

聚焦：

```text
Models/PLAYERVIEW
M4 / M4A1 / M4A1-S / M4A1S family
weapon-body candidates
```

排除/归档：

- `_BL` / `_GR`；
- `WOMAN`；
- 纯 hand / arm / sleeve；
- QV / world / 第三人称作为首轮模型；
- 明显不是 M4/M4A1 枪体的资源；
- 已知派生预览/临时输出。

### 3.2 Deduplication

按以下顺序去重：

1. exact SHA-256；
2. 如果 parser 可以稳定得到 geometry signature，再按 geometry signature 聚类；
3. 相同几何、不同皮肤/纹理的候选仍需保留 texture variant 关系，但首轮几何渲染每个 unique geometry cluster 只选一个 representative。

输出：

```text
work/p5_leishen/t02/candidate_clusters.json
```

每个 cluster 至少记录：

```text
cluster_id
representative_ltb
member_paths[]
sha256[]
geometry_signature (nullable)
variant_tokens[]
exclusion_reason (nullable)
```

---

## 4. Encyclopedia-style side view and native material hard gate

目标不是漂亮渲染，而是把本地模型统一成和官方百科图最接近的视觉表达。

每个 unique representative 首轮只生成：

```text
1 orthographic side PNG
768x384 或 1024x512
透明或白背景
统一方向
统一 fit-to-frame
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
无 Cycles
```

### 4.1 Preferred path

```text
LTB weapon mesh
  + UV
  + 本地 CF 原生颜色来源
  + 本地 CF Alpha / Normal / Specular / emissive / lookup / shader parameters（按实际证据）
  -> 可解释、可追溯的临时离线材质
  -> orthographic side PNG
```

核心目标不是“找一张看起来像 diffuse 的图片”，而是**恢复 CF 实际使用的材质输入组合**。如果该武器的最终颜色来自 lookup / mask / tint / 多层 shader，而不是单张传统 diffuse，也必须按真实关系恢复。

### 4.2 Gray/diagnostic fallback

如果某候选暂时无法解析完整材质：

- 可以生成灰模/轮廓侧视图用于廉价几何排除；
- 可以生成 raw DTX + UV、Alpha/Specular 等诊断图；
- 必须明确标记 `diagnostic_only`；
- **这些输出不能完成 `USER_VISUAL_MATCH_CONFIRMED`。**

此前“不要为了首轮识别临时造大型专有 DTX decoder”的限制，在最终候选材质无法还原时不再适用：**现在原生材质恢复本身就是 blocker，可以扩展/修复 decoder，但必须以最小、可验证、可复用实现为目标。**

### 4.3 Mandatory native-texture recovery procedure

Luna 在继续让用户从 C029/C103 选择前，必须按下列顺序执行；每一步都要写 evidence，不允许一句“贴图解析失败”后跳过。

#### A. P4 material provenance audit first

先审计 P4 黑骑士 / BornBeast Prototype 的材质来源，至少核对：

```text
work/m4a1_s_bornbeast/p4_prototype_01/build_report.json
work/m4a1_s_bornbeast/materials/**
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
```

已知风险必须验证并记录：P4 build report 曾使用：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

作为 `bornbeast_base.png` / self-illum 派生输入，再转成 Source VTF。

因此：

- P4 可继续作为 **LTB -> Source/MIGI 技术流水线** evidence；
- P4 **不能**作为“CF 原生贴图已正确解码”的 evidence；
- 外部 CS1.6 / 网络 MOD 资产可作为视觉/差分参考，但**禁止进入最终材质 provenance**；
- 生成：

```text
work/p5_leishen/t02/p4_material_provenance_audit.json
```

至少记录 `source_class = local_cf | derived_local_cf | external_reference | source1_output` 和 SHA-256。

#### B. Build a complete local Transformers material-family inventory

不要只盯当前三个文件。对 `M4A1_S_Transformers*` / 可能的 IronBeast 同族关系做本地 inventory，重点覆盖但不限于：

```text
data/**/Models/PLAYERVIEW/**
data/**/ModelTextures/PLAYERVIEW/**
data/**/ModelTextures/AlphaMap/**
data/**/ModelTextures/NormalMap/**
data/**/ModelTextures/SpecularMap/**
data/**/ModelTextures/Shader/WeaponShader/**
```

同时检查：

- LTB mesh/piece 的 material / texture index / texture name / render-style 相关字段；
- 同 basename、同 SHA、同 geometry family 的不同 skin variant；
- QV/world family 只作为关联证据，不替代第一人称主材质；
- 任何额外 lookup、detail、effect、emissive、env/reflection、color table 资源。

输出：

```text
work/p5_leishen/t02/native_material_inventory.json
```

每个资源至少记录：

```text
relative_path
sha256
size
container/type
candidate_role
binding_evidence
source_class = local_cf
```

#### C. Re-test DTX decoding; do not assume headerless BGR24 is final truth

当前 `p5_t02_texture_probe.py` 直接把 `PV-M4A1_S_Transformers.DTX` 当作 `512x256 headerless BGR24`。这只能算一个 hypothesis。

必须并行验证：

1. 仓库现有 `CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs` 的正式路径；
2. 原始/解压前后 DTX bytes 是否在 `data/**` 流程中被剥掉 header/container；
3. LithTech DTX header、version、pixel format、mipmap、command string / texture metadata 是否存在于更上游原始资源；
4. BGRA/RGBA/Palette/DXT1/DXT3/DXT5 与当前 BGR24 解释是否有任一能够产生自洽图像；
5. orientation、alpha、mip chain、trailing bytes 是否吻合；
6. 若最终确认它是 mask/lookup，而非颜色贴图，必须明确证明其角色，而不是继续把它叫 diffuse。

对每一种可行 interpretation 输出：

```text
byte layout
width/height
pixel format
channel extrema/histogram
mip layout
source SHA-256
decoded SHA-256
confidence
rejection reason (if rejected)
```

禁止通过“哪一种看起来更像官方图”单独决定二进制格式；格式判断必须先有结构证据。

#### D. Recover actual material binding from LTB / resource family

当前“C029 exact SHA family 和 C103 material family 都指向 Transformers DTX”的结论还不够。

需要尽量回答：

```text
LTB piece/mesh
 -> material slot / texture index
 -> base/lookup texture
 -> alpha
 -> normal
 -> specular
 -> shader/render-style CFG
 -> optional tint/emissive/effect inputs
```

若现有 `LithTechModelDecoder` 没暴露 material binding：

- 优先扩展它导出需要的字段；
- 或对 LTB 中 material/texture table 做最小解析；
- 不要只根据文件名猜绑定。

#### E. Treat WeaponShader CFG as binary data, not an RGB image

仓库旧 `cfg_decode` 报告把 237 个 CFG 全部做成 `raw-rgb-strip` preview；这不是 shader CFG 的语义解析。

必须重新分析：

```text
data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Transformers.CFG
```

以及一批对照 CFG。

建议按以下路线：

1. hex / entropy / repeated-record / endian 检查；
2. 检查 ASCII/UTF-16 strings、float32/float16、int flags、固定 header；
3. 对同一武器 family 的多个 skin CFG 做 byte-level differential；
4. 对简单传统材质武器 vs 英雄级武器做 differential；
5. 对 BornBeast 与 Transformers 做 field-position 对比；
6. 查仓库 Config/CrossFire decoder 是否已有可复用结构；
7. 必要时参考公开 LithTech/Jupiter 纹理与 RenderStyle 实现，但最终字段映射必须由本地数据验证。

如果 CFG 最终不是 shader 参数本体，也要通过结构证据说明它实际是什么。

#### F. Use BornBeast external material only as a differential control

P4 的外部 CS1.6 BornBeast texture **禁止**成为任何最终输出输入，但可以作为“已知最终外观近似”的 differential control：

```text
local CF BornBeast DTX
+ local Alpha/Normal/Specular
+ local BornBeast CFG
      vs
external CS1.6 flattened texture (reference only)
```

用途仅限：

- 判断本地 DTX 是否更像 base color、mask 或 lookup；
- 推断 channel/tint/emissive 的可能组合；
- 设计 shader hypothesis。

任何从外部纹理拷贝、采样、烘焙得到的颜色都不得进入 Transformers 最终贴图。

#### G. Differential analysis across variants

利用本地同几何不同皮肤是最重要的逆向手段之一。

优先比较：

```text
C029 exact-SHA family 内 Transformers / IronBeast / Gilt / Virgo / 赛事皮肤
C103 Transformers_Reaper
其他 geometry 接近但材质不同的 Transformers variants
```

目标是找出“皮肤视觉变化时，到底哪些本地文件/CFG bytes 同步变化”。

如果多个 LTB 完全同 SHA，而仅 DTX/CFG/TGA 变化，这是强 binding evidence。

#### H. Build an offline shader hypothesis renderer

在找到足够 binding 后，允许建立最小 CPU/Python/Blender-offscreen 诊断 renderer，但必须满足：

- 输入只来自 `local_cf` 原始资源或从其确定性派生的数据；
- 不用 AI 生成纹理；
- 不用外部 MOD texture 填洞；
- 每个 shader hypothesis 显式记录公式和输入；
- Alpha/Normal/Specular/lookup/tint/emissive 分层可单独开关，便于 A/B；
- 输出统一正交侧视，便于与 official reference 比较。

推荐输出：

```text
previews/native_hypotheses/<id>_base.png
previews/native_hypotheses/<id>_base_alpha.png
previews/native_hypotheses/<id>_base_spec.png
previews/native_hypotheses/<id>_full.png
native_shader_hypotheses.json
```

#### I. Native material acceptance gate

只有满足以下条件，才能把某张图称为“本地 CF 正确材质候选图”：

1. 枪体几何来自本地 LTB；
2. UV 来自该 LTB；
3. 最终可见颜色的每个输入都能追溯到本地 CF `data/**`，或可由已验证 CFG/engine semantics 的数值常量确定；
4. Alpha / Normal / Specular / emissive / lookup 等实际使用的输入都有路径 + SHA-256；
5. 不含任何 external/reference image 的像素；
6. 生成步骤可重复；
7. 与 official reference 在关键颜色分区、纹理图案、发光/高光区域和机械结构上达到足以人工辨认的程度。

如果还做不到：

```text
NATIVE_TEXTURE_RECOVERY_INCOMPLETE
```

继续 T02，不进入 T03，不要求用户在灰模/伪材质之间强选。

---

## 5. Contact sheet and shortlist

将 representative 侧视图组合为 contact sheet，并清楚标注：

```text
cluster_id
representative path short name
texture status
material provenance status
```

如果 unique cluster 很多，可先用几何轮廓自动/人工排除明显不匹配项，再只对剩余候选做完整原生材质恢复。

目标是尽快把候选压缩到可人工确认的数量，建议：

```text
Top 5–15 geometry shortlist
Top 2–5 native-material finalists
```

必须生成：

```text
work/p5_leishen/t02/contact_sheet.png
work/p5_leishen/t02/visual_shortlist.json
```

---

## 6. USER LOCAL-CANDIDATE GATE

Luna 只有在至少一个 finalist 通过 `Native material acceptance gate` 后，才把**本地真实、原生材质派生侧视图**给用户看，并同时展示用户已确认的官方 reference 作为对照。

用户可以：

- 直接确认某一 candidate；
- 要求放大/分层查看 2～3 个候选；
- 否决全部并要求继续恢复/缩圈。

用户明确确认某个本地 candidate 后，T02 状态只能写：

```text
USER_VISUAL_MATCH_CONFIRMED
```

这还不是最终 `IDENTITY_CONFIRMED`；T03 还必须闭合 model / texture / shader / sound / config provenance。

如果原生材质尚未闭合，等待状态应写：

```text
NATIVE_TEXTURE_RECOVERY_INCOMPLETE
```

而不是要求用户仅凭灰模确认。

---

## 7. Required outputs

统一输出：

```text
work/p5_leishen/t02/
```

至少：

```text
candidate_clusters.json
visual_shortlist.json
contact_sheet.png
execution.json
p4_material_provenance_audit.json
native_material_inventory.json
native_shader_hypotheses.json
```

用户确认后再增加：

```text
user_visual_confirmation.json
```

其中记录：

```text
confirmed_cluster_id
confirmed_representative_path
confirmed_model_sha256
official_reference_page
official_reference_image
native_material_status = passed
user_confirmation = confirmed
confirmed_at
```

允许额外生成：

```text
previews/*.png
previews/native_hypotheses/*.png
scripts/p5/*.py
scripts/p5/*.cs
```

仅限派生预览和可复用脚本。

---

## 8. Completion criteria

### `PASS / USER_VISUAL_MATCH_CONFIRMED`

必须满足：

1. 读取已确认的 T01 official reference；
2. 复用 legacy pre-scan 缩圈，而非无必要重扫全部数据；
3. 对 M4/M4A1 第一人称候选做 SHA/geometry 去重；
4. 对 finalist 完成本地 CF 原生材质恢复，不能使用 external MOD texture；
5. 原生材质输入、binding 和生成步骤可追溯/可重复；
6. 生成统一百科式侧视派生图；
7. 给用户看 native-material finalist；
8. 用户明确确认一个本地 candidate；
9. 记录其本地路径和 SHA-256；
10. 没有自行宣告最终 `IDENTITY_CONFIRMED`。

### `NATIVE_TEXTURE_RECOVERY_INCOMPLETE`

包括：

- 只能得到灰模；
- 只能把 DTX 当未验证的 mask/lookup；
- 只有 Alpha/Specular 近似；
- shader/CFG binding 尚未解释；
- 最终颜色依赖 external texture；
- 不能证明最终 visible color 的本地 CF 来源。

这是可继续工作的 T02 状态，不允许跳过。

### `BLOCKED`

包括：

- T01 尚未用户确认；
- legacy pre-scan evidence 丢失且无法安全重建；
- 主要 LTB 无法导出到任何可视几何；
- 本地原始资源缺失到无法继续做任何格式/材质逆向。

### `INVALID`

包括：

- 未读取 T01 confirmed reference 就开始视觉匹配；
- 用文件名直接预锁 candidate；
- 修改 `data/**`；
- 上传原始 LTB/DTX/TGA/CFG；
- 用 AI 生成本地候选图代替模型实际渲染；
- 用网络/CS1.6/MOD 贴图作为最终 base color 或填补缺失材质；
- 将 raw-rgb-strip CFG preview 当作 CFG 语义解析；
- Luna 自行写最终 `IDENTITY_CONFIRMED`。

---

## 9. Upload allowlist

只允许：

```text
work/p5_leishen/t02/candidate_clusters.json
work/p5_leishen/t02/visual_shortlist.json
work/p5_leishen/t02/contact_sheet.png
work/p5_leishen/t02/execution.json
work/p5_leishen/t02/user_visual_confirmation.json
work/p5_leishen/t02/p4_material_provenance_audit.json
work/p5_leishen/t02/native_material_inventory.json
work/p5_leishen/t02/native_shader_hypotheses.json
work/p5_leishen/t02/previews/*.png
work/p5_leishen/t02/previews/native_hypotheses/*.png
scripts/p5/*.py
scripts/p5/*.cs
```

禁止：

```text
data/**
原始 LTB / DTX / TGA / CFG / WAV
.blend 大文件
Steam/MIGI 输出
AI 生成参考图
外部 MOD/CS1.6 原始贴图进入最终资产
```

---

## 10. Handoff

T02 必须先完成：

```text
candidate narrowing
-> native texture/material recovery
-> native-material visual finalist
-> USER_VISUAL_MATCH_CONFIRMED
```

然后：

```text
STOP local visual search
-> push evidence
-> P5-T03 provenance closure
```

T03 继续确认该 model candidate 对应的完整 diffuse/lookup/normal/specular/shader/QV/sound/animation/config 是否属于同一真实 CF 资源族；**T03 不得被用来补做 T02 已要求的“最终可辨识原生材质恢复”。**
