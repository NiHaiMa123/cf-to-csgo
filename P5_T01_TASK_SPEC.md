# P5_T01_TASK_SPEC.md — 官方 CF 武器百科目标图确认

> task_id: `P5-T01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **READY_FOR_LUNA**

---

## 1. Purpose

P5-T01 只解决一个问题：

> **用户所说的目标武器，在 CF 官方武器百科里到底是哪一个条目、长什么样。**

T01 不扫描本地 `data/**`，不根据内部英文名猜身份，不进入模型渲染。

正确顺序：

```text
Luna mandatory Web Search
  -> CF 官方武器百科
  -> 官方详情页
  -> 官网实际加载的真实武器图片
  -> 展示给用户
  -> USER REFERENCE GATE
  -> 用户确认 / 否决
```

这是所有后续本地资产识别的视觉 Ground Truth。

---

## 2. Target

目标 display name：

```text
M4A1-雷神
```

官方武器百科入口：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

已知详情页形态可能类似：

```text
https://cf.qq.com/cp/a20250701wqbk/page.html?itemid=<ITEM_ID>
```

---

## 3. Mandatory Web Search

Luna **必须实际调用 Web Search / 浏览器搜索能力**。不能只使用模型记忆、聊天历史或本地文件名。

至少尝试：

```text
M4A1-雷神 CF 武器百科
site:cf.qq.com/cp/a20250701wqbk M4A1 雷神
site:cf.qq.com/cp/a20250701wqbk "M4A1-雷神"
```

如果普通搜索引擎不能直接索引详情页，允许：

- 打开官方百科首页并使用站内分类/搜索；
- 检查官方页面 HTML / JS；
- 检查 Network 请求；
- 从官方页面加载的数据中定位 `itemid`、display name、图片 URL；
- 使用第三方网页仅作为搜索线索，但最终必须回到官方 `cf.qq.com` 详情页。

---

## 4. What counts as valid official reference

T01 PASS 候选必须同时具备：

1. 官方 `cf.qq.com` 武器百科详情页；
2. 详情页显示的武器名称；
3. 详情页实际加载/引用的武器展示图片。

图片本身可以来自腾讯 CDN，例如 `gtimg` / `qpic` / 其他腾讯静态资源域名，只要能证明它由该官方详情页实际引用。

不得以以下内容替代：

- 搜索引擎缩略图；
- Wiki/Fandom 图；
- Bilibili / 贴吧 / 17173 等第三方截图；
- 第三方 MOD 图；
- AI image generation；
- 重绘、合成或根据描述生成的替代图。

---

## 5. USER REFERENCE GATE

找到 Luna 认为正确的官方条目后，Luna 必须在当前 Codex 对话中展示：

```text
官方名称
官方详情页 URL
itemid（若可取得）
官方图片原始 URL
真实图片的可视预览
```

如果 Harness 支持远程图片内联，直接内联真实 URL；如果不能内联，可临时下载官方图片用于显示，但必须同时保留原始 URL，且临时副本不能进入 final asset provenance。

若有 2～3 个可能的官方条目，可以一次展示最多 3 个，让用户选择。

然后等待用户明确回复：

```text
确认，就是这把
```

或等价明确确认。

等待状态：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
```

这不是 BLOCKED，不需要回 Chat/Sol 改 Plan。

如果用户否决，Luna 在**同一个 T01** 中继续 Web Search，直到找到新候选或真的无法找到官方条目。

---

## 6. Required evidence after user confirmation

用户确认后，生成：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

`official_reference.json` 至少记录：

```text
schema = cf2.p5.t01.official-reference.v1
task_id = P5-T01
target_display_name
official_page_url
itemid (nullable)
official_image_url
image_source_domain
page_to_image_relation
user_confirmation = confirmed
confirmed_at
search_queries[]
source_notes[]
```

如果临时下载了官方图片用于展示，可记录 hash，但**默认不要把官网原图提交进仓库**；URL + 页面关系 + 用户确认即为 T01 reference evidence。

---

## 7. Completion criteria

### `PASS / USER_REFERENCE_CONFIRMED`

必须满足：

1. Luna 实际执行了 Web Search / 官方网页查找；
2. 找到官方 `cf.qq.com` 详情页；
3. 找到该详情页实际加载的真实网络武器图片；
4. 图片已展示给用户；
5. 用户明确确认目标图；
6. `official_reference.json` / `reference_report.md` 已生成；
7. 没有开始本地候选视觉匹配。

### `BLOCKED_WEB_SEARCH_UNAVAILABLE`

Harness 没有可用 Web Search / 浏览器能力，且无法访问官方图鉴。

### `BLOCKED_OFFICIAL_REFERENCE_NOT_FOUND`

经过合理搜索、站内查找和官方页面检查后，仍无法定位官方条目或官网实际图片。

### `INVALID`

包括：

- 没有 Web Search 就凭记忆宣布目标图；
- 使用生成图片作为 reference；
- 使用第三方图片冒充官网图片；
- 用户没有确认就直接进入本地模型匹配。

---

## 8. Upload allowlist

只允许：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

禁止上传：

```text
data/**
官网整页下载包
第三方图片包
AI 生成图
无关缓存
```

---

## 9. Handoff to T02

用户确认并完成 T01 evidence 后，Luna **可以直接进入 `P5_T02_TASK_SPEC.md`**，不需要再返回 Chat/Sol 修改 Plan。

T02 必须读取 T01 的：

```text
confirmed official_page_url
confirmed official_image_url
user_confirmation
```

作为视觉 Ground Truth。

历史上已经完成的本地广召回不再叫当前 T01；它保留为 [`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)，T02 可以直接复用其 candidate index/matrix，避免重复扫描全部 `data/**`。