# P5_T02_TASK_SPEC.md — 本地候选缩圈与百科式侧视锁定

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **BLOCKED_BY_T01_USER_REFERENCE**

---

## 1. Purpose

P5-T02 只在新 P5-T01 已完成 `USER_REFERENCE_CONFIRMED` 后执行。

T02 的问题是：

> **本地 CF `data/**` 里，哪一个第一人称 M4/M4A1 模型在标准贴图侧视图下与用户确认的官方武器百科目标图一致？**

T02 不再做 Web Search；官方视觉 Ground Truth 来自：

```text
work/p5_leishen/t01_reference/official_reference.json
```

T02 不允许仅凭 `Transformers` / `BornBeast` / `Thor` / `Leishen` 等内部 token 预锁身份。

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

## 4. Fastest possible encyclopedia-style side view

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
  + 本地 CF diffuse / 主颜色纹理
  -> 临时可渲染材质
  -> orthographic side PNG
```

这一步要尽可能直接把“方块贴图/atlas”通过原模型 UV 还原到枪体表面，再拍标准侧面，而不是让人去读 atlas。

### 4.2 Texture unavailable fallback

如果某候选暂时无法解析 diffuse：

- 可以先生成灰模/轮廓侧视图用于廉价几何排除；
- 标记 `texture_status=not_available`；
- 灰模不能单独完成最终本地候选确认。

不要为了首轮识别临时造大型专有 DTX decoder；优先复用仓库已有导出/转换能力。

---

## 5. Contact sheet and shortlist

将 representative 侧视图组合为 contact sheet，并清楚标注：

```text
cluster_id
representative path short name
texture status
```

如果 unique cluster 很多，可先用几何轮廓自动/人工排除明显不匹配项，再只对剩余候选做贴图侧视图。

目标是尽快把候选压缩到可人工确认的数量，建议：

```text
Top 5–15
```

而不是一次给用户看几百张。

必须生成：

```text
work/p5_leishen/t02/contact_sheet.png
work/p5_leishen/t02/visual_shortlist.json
```

---

## 6. USER LOCAL-CANDIDATE GATE

Luna 必须把 contact sheet / shortlist 中的**本地真实派生侧视图**给用户看，并同时展示用户已确认的官方 reference 作为对照。

用户可以：

- 直接确认某一 candidate；
- 要求放大 2～3 个候选；
- 否决全部并要求继续缩圈。

用户明确确认某个本地 candidate 后，T02 状态只能写：

```text
USER_VISUAL_MATCH_CONFIRMED
```

这还不是最终 `IDENTITY_CONFIRMED`；T03 还必须闭合 model / texture / shader / sound / config provenance。

等待状态：

```text
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

这不是 BLOCKED，不需要返回 Chat/Sol 改 Plan。

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
user_confirmation = confirmed
confirmed_at
```

允许额外生成：

```text
previews/*.png
scripts/p5/*.py
```

仅限派生预览和可复用脚本。

---

## 8. Completion criteria

### `PASS / USER_VISUAL_MATCH_CONFIRMED`

必须满足：

1. 读取已确认的 T01 official reference；
2. 复用 legacy pre-scan 缩圈，而非无必要重扫全部数据；
3. 对 M4/M4A1 第一人称候选做 SHA/geometry 去重；
4. 生成统一百科式侧视派生图；
5. 给用户看 contact sheet / shortlist；
6. 用户明确确认一个本地 candidate；
7. 记录其本地路径和 SHA-256；
8. 没有自行宣告最终 `IDENTITY_CONFIRMED`。

### `BLOCKED`

包括：

- T01 尚未用户确认；
- legacy pre-scan evidence 丢失且无法安全重建；
- 主要 LTB 无法导出到任何可视几何；
- 完全无法获得足以比较的本地纹理或模型预览。

### `INVALID`

包括：

- 未读取 T01 confirmed reference 就开始视觉匹配；
- 用文件名直接预锁 candidate；
- 修改 `data/**`；
- 上传原始 LTB/DTX/TGA；
- 用 AI 生成本地候选图代替模型实际渲染；
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
work/p5_leishen/t02/previews/*.png
scripts/p5/*.py
```

禁止：

```text
data/**
原始 LTB / DTX / TGA / CFG / WAV
.blend 大文件
Steam/MIGI 输出
AI 生成参考图
```

---

## 10. Handoff

T02 用户视觉确认后：

```text
STOP local visual search
-> push evidence
-> P5-T03 provenance closure
```

T03 才负责确认该 model candidate 对应的 diffuse、normal、specular、shader、QV、sound、animation/config 等是否属于同一真实 CF 资源族。