# P5_T01_TASK_SPEC.md — 官方 CF 武器百科目标图确认

> task_id: `P5-T01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **PASS / USER_REFERENCE_CONFIRMED — COMPLETED**

> 本文件保留 T01 的完成协议和 acceptance criteria。它**不是当前执行入口**。当前执行任务见 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。

---

## 1. Purpose

P5-T01 只解决：

> **用户所说的目标武器，在 CF 官方武器百科里是哪一个条目、长什么样。**

T01 不扫描本地 `data/**`，不根据内部英文名猜身份，不进入模型渲染。

完成顺序：

```text
Luna Web Search
-> CF 官方武器百科
-> 官方详情页
-> 官网实际加载的真实武器图片
-> 展示给用户
-> USER REFERENCE GATE
-> 用户确认
```

---

## 2. Target / fixed evidence

目标 display name：

```text
M4A1-雷神
```

固定 evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

用户已经确认 official reference。除非 evidence 损坏或用户明确否决，不重跑 T01。

---

## 3. Historical acceptance criteria

T01 PASS 必须具备：

1. 官方 `cf.qq.com` 武器百科详情页；
2. 详情页显示的武器名称；
3. 详情页实际加载/引用的武器展示图片；
4. Luna 实际执行 Web Search / 官方网页查找；
5. 图片展示给用户；
6. 用户明确确认；
7. evidence 已写入上述两个 tracked report；
8. 不使用 AI / 第三方图片冒充官方 reference。

这些条件已经满足，因此当前状态固定为：

```text
PASS / USER_REFERENCE_CONFIRMED
```

---

## 4. Official reference policy

有效 reference：

```text
cf.qq.com 官方详情页
+
该详情页实际加载/引用的腾讯 CDN 图片
```

不得替代为：

- 搜索引擎缩略图；
- Wiki/Fandom 图；
- Bilibili / 贴吧 / 媒体截图；
- 第三方 MOD 图；
- AI image generation / 重绘 / 合成图。

第三方资料只能用于发现关键词/别名。

---

## 5. Current reuse rule

所有后续 P5 任务只读取：

```text
confirmed official_page_url
confirmed official_image_url
user_confirmation
```

作为 Ground Truth。

不要因为 P4-M01 material work、P5-T02 pause 或候选变化而重做 T01。

只有以下情况允许重新打开 T01：

- 用户明确说现有官方图不是目标；
- evidence 文件损坏/丢失；
- 官方 page/image relation 被证明记录错误。

---

## 6. Handoff history

T01 完成后原本进入 T02。当前因 native material 基础方法未验证，执行依赖已调整为：

```text
P5-T01 PASS
+
P5 candidate evidence preserved
+
P4-M01 native material benchmark ACTIVE
-> P4-M01 PASS 后恢复 P5-T02
```

历史本地广召回仍见 [`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)。
