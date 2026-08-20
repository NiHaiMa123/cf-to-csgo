# P5_T01_TASK_SPEC.md — 官方身份锚点与本地候选召回

> task_id: `P5-T01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **READY_FOR_LUNA**

---

## 1. Purpose

在不修改 P4 frozen pipeline、不上传 `data/**`、不凭文件名直接宣布最终身份的前提下，建立 **M4A1-雷神** 的第一轮本地候选集合。

本任务只回答：

> “本地 CF 资源中，哪些文件值得进入下一轮模型/贴图身份比对？”

本任务 **不回答**：

> “哪个文件已经被最终确认就是雷神？”

---

## 2. Official identity anchor

目标 display identity：

```text
M4A1-雷神
```

官方 reference：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

reference 类型：`OFFICIAL_CF_WEAPON_HANDBOOK_REFERENCE`

注意：

- 该网页只作为 identity / visual reference；
- 不下载或提交网页图片作为 final game asset；
- 当前 Chat/Sol 远程抓取该动态页面会超时，因此 T01 不依赖网页内部 JSON/API 才能完成；
- 若 Luna 能在本地浏览器/已有缓存中获得官方 item id、resource id、内部 key 或图片文件名，可记录为 **reference metadata**，但不得因为拿不到这些字段而阻塞第一轮本地候选召回。

---

## 3. Scope / allowed roots

### 允许读取

- `data/**` — 只读；
- 当前仓库中的已有 parser / scripts / assets / report；
- `P5_TASKS.md`、`plan.md`、`CODEX_TASKS.md`、`AGENTS.md`。

### 禁止扫描

- 仓库外的用户目录；
- Steam/MIGI 目录，除非后续 Task Spec 明确要求；
- 与 CF 资产定位无关的其他磁盘目录。

### 禁止修改

- `data/**`；
- P4 frozen code / manifest / build evidence；
- Steam/MIGI 当前 addon；
- `plan.md` 最终阶段状态。

---

## 4. Search strategy

T01 必须分层执行，先便宜召回，再轻量结构化，不允许直接全量 Blender 渲染。

### 4.1 Phase A — local inventory

对 `data/**` 建立最小文件 inventory，至少记录：

```text
relative_path
filename
extension
size_bytes
```

需要计算 SHA-256 的对象：

- 进入 candidate matrix 的候选文件；
- 与候选建立明确关联的 config / texture / shader / sound 文件。

不要求对 `data/**` 所有文件全量计算 SHA-256。

### 4.2 Phase B — lexical / path recall

候选关键词仅用于 **召回**，不是最终证明。

至少覆盖以下 token，大小写不敏感，并允许 `-` / `_` / 空格差异：

```text
M4
M4A1
M4A1-S
M4A1S
雷神
LEISHEN
LEI_SHEN
THOR
THUNDER
```

并额外扫描：

- `Models/PLAYERVIEW` 或语义等价的第一人称模型路径；
- 与候选 basename / material / resource token 同名或近似的配置、纹理、Shader、声音文件。

禁止规则：

- 不得因为文件名包含 `THOR` / `LEISHEN` 就直接标 `confirmed`；
- 不得因为文件名没有中文“雷神”就排除候选。

### 4.3 Phase C — configuration/reference graph recall

如果本地存在可读文本/JSON/XML/CFG/INI/LUA/CSV 等配置或资源表，搜索：

- `M4A1`；
- candidate basename；
- candidate material name；
- candidate numeric/resource id；
- model path；
- texture/shader/sound path。

建立最多一层到两层的 reference graph：

```text
config/item/resource record
  -> model candidate
  -> related texture/shader/sound tokens
```

若文件为不可安全解析的专有二进制，不为了 T01 新造大规模 decoder；记录为 `binary_unresolved`，留后续任务处理。

### 4.4 Phase D — light LTB candidate summary

只对进入 LTB candidate set 的文件使用仓库现有能力做轻量摘要；若当前 parser 可用，至少记录：

```text
mesh_count
vertex_count
triangle_count
bounds
node/bone names (if available)
material names / slots (if available)
contains obvious arm/hand groups (if detectable)
```

不得在 T01：

- 批量生成 Source 1 addon；
- 批量运行 Blender；
- 批量做高成本多视图渲染；
- 修改 parser 以追求完整动画解码。

如果现有 parser 不支持某字段，写 `not_available`，不要伪造。

---

## 5. Candidate ranking

评分只是 **下一轮优先级**，不等于 identity confidence。

建议 deterministic score：

```text
+100  本地配置/item/resource record 直接引用该 model candidate
 +40  位于 PLAYERVIEW / 第一人称武器模型目录
 +25  basename/path 明确包含 M4A1/M4A1S 族 token
 +20  有同 basename 或明确引用关系的 texture/material/shader
 +15  有同变体 config/resource record
 +10  有同变体 sound/animation token 关联
 +10  LTB 摘要显示为明显枪械主体而非纯手臂/附件
 -40  只命中文件名但没有任何引用/关联证据
 -80  明确是纯 hand/arm 模型
-100  已证明确属其他武器家族
```

规则：

- score 只用于排序；
- 相同证据不得重复加分；
- `Prototype-01 / BornBeast` 当前文件可以保留为 comparison / negative-control candidate，但必须标记：
  `identity_status=prototype_only_not_finally_proven`；
- 不得自动把 Top 1 写成 `雷神`。

---

## 6. Required outputs

统一输出根：

```text
work/p5_leishen/t01/
```

必须生成：

### 6.1 `candidate_index.json`

至少包含：

```json
{
  "schema": "cf2.p5.t01.candidate-index.v1",
  "task_id": "P5-T01",
  "target_identity": "M4A1-雷神",
  "official_reference_url": "https://cf.qq.com/cp/a20250701wqbk/index.html",
  "scan_roots": ["data/..."],
  "inventory_counts": {},
  "keyword_hits": {},
  "candidates": []
}
```

每个 candidate 至少记录：

```text
candidate_id
relative_path
extension
size_bytes
sha256
candidate_type (model/texture/config/shader/sound/other)
recall_reasons[]
reference_edges[]
light_summary{}
score
identity_status = CANDIDATE_ONLY
```

### 6.2 `candidate_matrix.csv`

至少列：

```text
rank
candidate_id
relative_path
candidate_type
score
sha256
primary_recall_reason
config_reference_count
related_texture_count
related_shader_count
related_sound_count
mesh_count
triangle_count
identity_status
next_action
```

### 6.3 `scan_report.md`

必须简洁记录：

- 实际扫描根；
- 文件数量；
- 使用的关键词；
- parser/配置搜索能力；
- Top 10～30 candidates；
- 每个 Top candidate 为什么入选；
- 明确排除项及排除原因；
- 未解析/受限项；
- 推荐进入 P5-T02 的 Top candidate 数量。

### 6.4 `execution.json`

记录：

```text
git_head
started_at / finished_at
commands[]
exit_codes[]
script paths / hashes if created
scan root
output hashes
errors / warnings
```

---

## 7. Completion criteria

### PASS

T01 可以标记 `EXECUTION_PASS` 的条件：

1. 扫描只发生在允许 scope；
2. `data/**` 未被修改/上传；
3. 生成 candidate index + matrix + scan report + execution report；
4. candidate 有 path/size/SHA-256 和召回理由；
5. 至少对 model candidate 建立了可用的轻量摘要或明确 `not_available` 原因；
6. 排除项有记录；
7. 没有任何 candidate 被 Luna 写成最终 `IDENTITY_CONFIRMED`；
8. 输出足以让 Chat/Sol 选择少量 T02 候选。

### BLOCKED

例如：

- `data/**` 不存在；
- 必需的当前 parser 完全不可运行，导致连候选基本摘要都不能产生；
- 扫描根无法确定且继续执行会越界。

### INVALID

例如：

- 实际扫描了仓库外用户目录；
- 为获得结果修改/删除了 `data/**`；
- 用网络第三方 MOD 文件冒充本地 final source；
- 只凭名字直接宣布最终雷神。

---

## 8. Upload allowlist

允许提交到 GitHub：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

如果为 T01 新增了一个纯扫描/索引脚本，允许额外提交：

```text
scripts/p5/*.py
```

但仅在确实需要、且脚本不包含本地绝对路径/原始资产内容时允许。

禁止上传：

```text
data/**
原始 LTB/DTX/TGA/WAV
完整网页下载包
无关日志/缓存
```

如果为了后续 T02 需要预览图，本任务先不要上传，等 Chat/Sol 根据 candidate matrix 指定具体候选后再生成。

---

## 9. Executor stop rule

Luna 完成 T01 后：

1. 精确提交 allowlist 文件；
2. push `master`；
3. 返回 commit SHA、Top candidate 数量和报告路径；
4. **停止**；
5. 不自行开始 P5-T02，不自行渲染模型，不自行宣布最终雷神。

之后由 Chat/Sol 读取 candidate matrix，决定 P5-T02 的精确候选和视觉/几何比对协议。
