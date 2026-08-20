# P5_T02_TASK_SPEC.md — 官方图鉴确认 + 本地百科式侧视候选锁定

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **READY_FOR_LUNA**

---

## 1. Purpose

P5-T01 已完成广召回。P5-T02 不再由 Chat/Plan 端预先替用户选择“雷神对应哪个内部英文资源名”，而是把完整识别流程交给 Luna 按固定协议执行。

本任务的核心顺序必须是：

```text
Luna Web Search
  -> CF 官方武器百科详情页
  -> 找到官网实际使用的目标武器图片
  -> 把真实网上图片给用户看
  -> USER REFERENCE GATE
  -> 用户确认目标图后继续
  -> 本地 M4/M4A1 第一人称候选缩圈
  -> SHA / geometry 去重
  -> 最轻量的贴图百科式正交侧视图
  -> 批量 contact sheet / 排名
  -> USER LOCAL-CANDIDATE GATE
  -> 锁定本地候选
  -> 后续 T03 resource graph / provenance
```

本任务禁止：

- 由 Chat/Sol 每次手工代替 Luna 搜目标图；
- 未 Web Search 就凭模型记忆判断目标长相；
- 仅凭跨服英文名、文件名或 T01 score 预锁某个内部资源族；
- 使用 AI image generation / 重绘 / 合成图作为目标 reference；
- 在用户确认官网目标图之前开始本地候选渲染。

---

## 2. Phase A — mandatory Web Search of the official CF weapon handbook

### 2.1 Mandatory search

Luna **必须使用 Web Search / 浏览器搜索能力** 查找目标：

```text
M4A1-雷神
```

官方武器百科根入口：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

已知官方详情页形态类似：

```text
https://cf.qq.com/cp/a20250701wqbk/page.html?itemid=<ITEM_ID>
```

搜索必须至少尝试：

```text
M4A1-雷神 CF 武器百科
site:cf.qq.com/cp/a20250701wqbk M4A1 雷神
site:cf.qq.com/cp/a20250701wqbk "M4A1-雷神"
```

如果普通搜索引擎不能直接索引详情页，允许：

- 打开官方武器百科首页并使用站内搜索/分类；
- 检查官方页面 HTML / JS / Network 请求；
- 从官方页面实际加载的数据中定位 `itemid`、display name、图片 URL；
- 使用第三方页面只作为**发现搜索词/线索**，但最终 USER REFERENCE GATE 必须回到官方 `cf.qq.com` 武器百科页面。

### 2.2 What counts as an official image

必须找到：

1. 官方 `cf.qq.com` 武器百科详情页；
2. 详情页显示的武器名称；
3. 详情页实际加载的武器展示图片。

图片 URL 本身可以位于腾讯 CDN（例如 `gtimg` / `qpic` / 其他腾讯静态 CDN），前提是 Luna 能证明该 URL 是由该官方详情页直接引用/加载的。

不得只使用：

- 搜索引擎缩略图；
- Wiki/Fandom 图片；
- Bilibili/贴吧/17173 等截图；
- 第三方 MOD 图；
- AI 生成图、重绘图、截图重构图。

### 2.3 Present the real web image to the user

找到 Luna 认为正确的官方详情页后，Luna 必须在当前 Codex 对话中向用户展示：

```text
官方名称
官方详情页 URL
itemid（若可取得）
实际图片 URL
图片本身的可视预览
```

**“图片本身”必须是从网上找到的实际图片。不得调用图像生成模型创建替代图。**

如果 Harness 支持直接内联远程图片，直接显示实际图片；如果不能内联，则打开/下载该远程图片用于显示，并同时给出原始 URL。下载副本仅作为临时 reference，不得上传为 final CF asset。

如果存在 2～3 个可能的官方条目，可一次展示最多 3 个实际官方图片让用户选择；不得自行猜一个然后继续。

---

## 3. USER REFERENCE GATE — target image confirmation

Phase A 完成后必须停止本地资产识别，并明确询问用户：

> “这是你要找的目标武器吗？”

只有用户作出明确肯定，例如：

```text
对
确认
就是这把
是这个
```

才允许继续 Phase B。

### 用户否认

如果用户说“不是 / 找错了 / 下一张”：

```text
继续 Web Search
  -> 找下一个官方候选
  -> 再展示真实官方图片
  -> 再等待用户确认
```

不得进入本地 candidate matching。

### 搜不到官方条目

如果 Luna 的 Web Search / 浏览器工具不可用：

```text
BLOCKED_WEB_SEARCH_UNAVAILABLE
```

如果搜索可用，但无法定位目标的官方武器百科详情页和官方图片：

```text
BLOCKED_OFFICIAL_REFERENCE_NOT_FOUND
```

此时停止并向用户说明缺失项。不得用模型记忆或第三方图片绕过这个 Gate。

### Gate evidence

用户确认后生成：

```text
work/p5_leishen/t02/reference_gate.json
```

至少记录：

```text
target_display_name
official_page_url
official_itemid
source_domain
official_image_url
image_sha256_if_downloaded_temporarily
search_queries[]
user_confirmation = true
confirmation_text
confirmed_at
```

不需要把官方原图提交到 GitHub；保存 URL/hash/确认记录即可。

---

## 4. Phase B — local candidate narrowing after user confirmation

只有 `reference_gate.json.user_confirmation=true` 后才允许执行。

优先复用 P5-T01 已生成的：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
```

不要重新对 165k 个文件做一次无差别全盘扫描，除非已有 index 明显缺失必要候选。

### 4.1 First-person candidate filter

目标是第一人称 M4/M4A1 枪体候选，优先：

```text
data/rf016/Models/PLAYERVIEW/**
```

候选来源允许包括：

- path / basename 命中 M4 / M4A1 / M4A1-S 家族；
- T01 配置/reference edge 指向 M4A1 类；
- 与 M4A1 武器 family 有明确本地关联但内部名字不直观的候选。

默认排除或单独归档：

```text
*_BL*
*_GR*
*WOMAN*
纯 hand / arm / sleeve
QV / WEAPONS 第三人称模型
明显其他枪种
```

这些排除不删除原文件，只记录 exclusion reason。

### 4.2 Dedup before rendering

先做便宜去重，再渲染：

第一层：

```text
exact SHA-256
```

第二层：如果现有 parser 可稳定提供，则建立 geometry signature：

```text
mesh_count
vertex_count
triangle_count
normalized bounds
mesh/group name signature
```

几何签名相同但文件 hash 不同的变体可以聚类；每个 cluster 先选一个 representative 做首轮侧视图，同时保留 aliases/member paths。

输出：

```text
work/p5_leishen/t02/candidate_groups.json
```

必须包含：

```text
cluster_id
representative_path
representative_sha256
member_paths[]
member_sha256[]
geometry_signature
exclusion_reason_if_any
```

T01 里曾经讨论过的 `Transformers`、`BornBeast` 等名字只作为普通候选 token；**不得因为之前 Chat 的跨服别名假设而获得固定 PRIMARY 身份。**

---

## 5. Phase C — fastest encyclopedia-style textured side view

目标不是做 Blender 展示渲染，而是用最低成本把每个独特候选转换成和官方武器百科图类似的标准侧面表达。

### 5.1 Only one view in the first pass

首轮每个 representative **只生成一张**：

```text
orthographic side view
```

不要首轮生成 left/right/top/front_3q 四视图。

建议输出：

```text
768x384 或 1024x512
透明或纯白背景
正交相机
枪体自动 fit frame
统一朝向
无手臂
无动画
无 IK
无 Source retarget
无 Cycles 高质量渲染
无景深/复杂灯光/阴影特效
```

相机侧面方向应尽量和用户已经确认的官方百科图一致；如果模型天然左右相反，可水平翻转派生预览，但必须记录 `preview_mirrored=true`，不得修改原始资产。

### 5.2 Texture application

首选结果是**真正贴了本地 CF diffuse/主颜色纹理的模型侧视图**，而不是 UV 方块 atlas 本身。

对每个 representative：

```text
LTB
  -> weapon mesh
  -> material/UV
  -> 对应本地 DTX/TGA diffuse/resource
  -> 临时解码为可渲染纹理
  -> 应用到 mesh
  -> orthographic side PNG
```

优先使用仓库/用户机器已经存在、已验证、安全的解析或 DTX 转换能力。

不得为了 T02 自动下载未知第三方 EXE 或临时造一个大型专有 DTX decoder。

如果某候选暂时无法解析 diffuse：

- 先生成统一灰模/轮廓侧视图作为 `geometry_only`；
- 标记 `texture_status=not_available`；
- 可以用于第一轮几何排除；
- **不能仅凭灰模把该候选最终确认成雷神**。

### 5.3 Simplest renderer wins

允许使用：

- Blender 4.5 headless/Eevee；
- 已有轻量 OBJ/mesh renderer；
- 其他仓库现有、可重复、不会修改原资产的本地方式。

原则：哪个能最简单稳定地产生“带正确 UV/纹理的标准侧面图”，就用哪个。

不得为了视觉效果做艺术渲染。

---

## 6. Phase D — batch comparison and shortlist

生成：

```text
work/p5_leishen/t02/sideviews/*.png
work/p5_leishen/t02/contact_sheets/*.png
work/p5_leishen/t02/sideview_matrix.json
```

每张 candidate PNG 必须带可追踪 ID，不要把长路径直接烙在图像主体上；contact sheet 下方可以写：

```text
C001
C002
C003
...
```

`sideview_matrix.json` 记录：

```text
candidate_id
cluster_id
representative_path
sha256
texture_source_path
texture_source_sha256
texture_status
preview_path
preview_sha256
preview_mirrored
render_command
render_tool
```

### comparison rule

Luna 可以使用其视觉能力或简单图像/轮廓比较来给出 `Top N`，但结果只能叫：

```text
VISUAL_SHORTLIST
```

不能叫 `IDENTITY_CONFIRMED`。

优先比较：

```text
枪托外轮廓
机匣
护木
枪口/消音器
弹匣轮廓
提把/瞄具
独特装饰件
枪身比例
主色块/纹路
Logo/发光区域位置
```

不要把“文件名像雷神”计入视觉相似度。

---

## 7. USER LOCAL-CANDIDATE GATE

生成 contact sheet / Top shortlist 后，Luna 再在当前 Codex 对话里把最有可能的本地侧视图给用户看，并询问：

> “这些本地候选里，哪一个与已确认的官方目标一致？”

建议先展示 Top 3～8；若都不对，再展示下一批。

只有用户确认某个本地 candidate 后，才把它标为：

```text
USER_VISUAL_MATCH_CONFIRMED
```

仍然不能写 `IDENTITY_CONFIRMED`，因为 T03 还要做 model/texture/shader/sound provenance closure。

输出：

```text
work/p5_leishen/t02/local_candidate_gate.json
```

至少记录：

```text
selected_candidate_id
selected_model_path
selected_model_sha256
selected_preview_path
user_confirmation=true
confirmation_text
confirmed_at
```

---

## 8. Required outputs

最终 T02 完成时至少提交：

```text
work/p5_leishen/t02/reference_gate.json
work/p5_leishen/t02/candidate_groups.json
work/p5_leishen/t02/sideview_matrix.json
work/p5_leishen/t02/local_candidate_gate.json
work/p5_leishen/t02/execution.json
work/p5_leishen/t02/sideviews/*.png
work/p5_leishen/t02/contact_sheets/*.png
```

允许新增：

```text
scripts/p5/*.py
```

仅限为本任务生成索引、导出、贴图解析、标准侧视图、contact sheet 所需的可复用脚本。

不提交：

```text
官方网页原图的复制文件
网页下载包
data/** 原始 LTB/DTX/TGA/WAV/CFG
.blend 大文件
Steam/MIGI 输出
无关缓存/日志
```

`reference_gate.json` 保存官方页面和图片 URL 即可。

---

## 9. execution.json

至少记录：

```text
task_id = P5-T02
git_head
started_at / finished_at
web_search_used = true
search_queries[]
official_page_url
official_image_url
user_reference_gate
candidate_filter_counts
dedup_counts
commands[]
exit_codes[]
renderer/tool versions
output hashes
warnings/errors
user_local_candidate_gate
```

---

## 10. Completion semantics

### `EXECUTION_PASS`

只有同时满足：

1. Luna 实际执行了 Web Search；
2. 目标 reference 落在 CF 官方武器百科详情页；
3. Luna 给用户看的目标图是真实网上图片，不是生成图；
4. 用户明确确认了目标官方图片；
5. 本地候选完成缩圈和 dedup；
6. unique representative 已生成最简侧视预览；
7. 能解析纹理的候选优先使用本地真实纹理；
8. 用户明确确认了本地视觉候选；
9. `data/**` 未修改/上传；
10. Luna 未自行写 `IDENTITY_CONFIRMED`。

### `AWAITING_USER_REFERENCE_CONFIRMATION`

已经找到官方图片并展示，正在等待用户回答。此状态**不是 BLOCKED**，是正常流程 Gate。

### `AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION`

已经生成本地候选侧视图并展示，等待用户选择。此状态**不是 BLOCKED**。

### `BLOCKED`

包括：

- Web Search 工具不可用；
- 无法找到官方武器百科条目；
- 本地数据/导出能力完全无法生成任何可用侧视候选；
- 用户确认目标后却找不到合理的 M4/M4A1 本地 candidate set。

### `INVALID`

包括：

- 用 AI 生成图片冒充官网 reference；
- 用第三方图片绕过官方图鉴 Gate；
- 用户未确认目标图就开始本地 candidate matching；
- 仍预锁 `Transformers`/`BornBeast` 等名字为最终目标而不做视觉验证；
- 修改/上传 `data/**`；
- Luna 自行写 `IDENTITY_CONFIRMED`。

---

## 11. Executor interaction / stop rule

本任务是**可交互多阶段 Task**，不需要每遇到用户确认 Gate 就回到 Chat/Sol 改 Plan。

正确执行方式：

```text
Luna pull latest master
  -> Phase A Web Search
  -> 展示真实官网图
  -> 等用户确认
  -> 用户确认后直接继续 Phase B/C/D
  -> 展示本地候选
  -> 等用户确认
  -> 用户确认后写 evidence
  -> push allowlist
  -> STOP，等待 T03
```

只有 Task Spec 本身需要改变、官方网站结构发生重大变化、或执行出现真正 BLOCKED/INVALID 时，才返回 Chat/Sol 重新设计。

完成 T02 后不得自行进入 T03。