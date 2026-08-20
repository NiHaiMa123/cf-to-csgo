# P5_T02_TASK_SPEC.md — 雷神视觉候选锁定

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **BLOCKED_BY_USER_REFERENCE_CONFIRMATION**

---

## 1. Purpose

P5-T01 已完成广召回。P5-T02 改为“先确认目标长什么样，再做本地统一侧视图比对”。

本任务禁止从跨服英文名、文件名或 T01 score 直接推导最终内部资源名。

正确顺序：

```text
Web Search / 官方武器百科
  -> Chat/Sol 选出“认为是目标武器”的参考图
  -> USER_REFERENCE_CONFIRMATION_GATE
  -> 用户明确确认“对，就是这把”
  -> 本地 M4/M4A1 PLAYERVIEW 候选缩小范围
  -> 按文件 hash / geometry signature 去重
  -> 最简静态灰模标准侧视图
  -> contact sheet
  -> Chat/Sol / 用户视觉排除
  -> Top 少量候选再加载本地贴图生成材质侧视图
  -> 锁定 Top 1~3
  -> P5-T03 resource graph / provenance
```

---

## 2. Mandatory Web / User confirmation gate

目标 display identity：

```text
M4A1-雷神
```

官方武器百科入口：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

在任何本地 T02 执行前，Chat/Sol MUST：

1. 使用 Web Search / Image Search 查找 `M4A1-雷神`；
2. 优先官方 CF / 腾讯素材；官方页不可抓取时可使用可信公开页面作为 identification reference；
3. 把 Chat/Sol 认为正确的目标武器图片直接展示给用户；
4. 等待用户明确确认；
5. 只有用户确认后，Chat/Sol 才把本 spec 状态改成 `READY_FOR_LUNA`。

用户未确认前：

> **Luna MUST NOT 执行 P5-T02。**

如果用户说“不是这把”，Chat/Sol 重新 Web Search 并再次展示候选图；不得进入本地模型比对。

重要纠正：

- 先前文档中把 `M4A1-雷神 -> M4A1-S Transformers` 写成确定映射，证据不足；
- 公开跨服命名存在冲突，因此该映射目前撤销为 `UNVERIFIED_ALIAS`；
- `Transformers`、`BornBeast`、`Steel/Iron Beast` 等名字只能作为本地 candidate token，不能在用户确认前冻结为目标族。

---

## 3. After-user-confirmation local scope

用户确认目标图后，Luna 先做廉价缩圈，不直接全量 Blender 渲染。

允许读取：

```text
data/rf016/Models/PLAYERVIEW/**
```

仅召回第一人称 M4/M4A1 相关 LTB，例如 basename/path 含：

```text
M4
M4A1
M4A1_S
M4A1-S
```

默认排除 presentation / hand variants：

```text
*_BL.LTB
*_GR.LTB
*_WOMAN_BL.LTB
*_WOMAN_GR.LTB
```

除非它们是唯一可用版本。

不得扫描仓库外目录；不得修改 `data/**`；不得修改 P4 frozen pipeline。

---

## 4. Phase A — deduplicate before rendering

对缩圈后的 canonical M4/M4A1 PLAYERVIEW LTB：

1. 记录 relative path / size / SHA-256；
2. 优先按完全相同 SHA-256 去重；
3. 对不同文件 hash 使用已有 parser 生成 geometry signature，至少：

```text
mesh_count
vertex_count
triangle_count
bounds
mesh/group names if available
```

4. 几何完全相同或高度同构的皮肤/活动 suffix 变体聚为一组；
5. 每个 geometry cluster 第一轮只渲染一个 representative。

输出：

```text
work/p5_leishen/t02/candidate_clusters.json
```

目标是把数百 M4 候选压缩成“独特枪体”集合，而不是把所有皮肤重复渲染。

---

## 5. Phase B — fastest geometry side-view pass

第一轮视觉只看几何，不贴图。

对每个 geometry representative：

```text
LTB -> existing parser/export -> static weapon mesh -> orthographic side view PNG
```

要求：

- 隐藏明显 hand/arm/sleeve 组；
- 正交投影；
- 固定朝向；
- 自动 fit 到相同画布；
- 简单白色或透明背景；
- 单色灰模 / silhouette；
- 不需要骨骼动作；
- 不需要 IK；
- 不需要 Source retarget；
- 不需要 Cycles / 艺术灯光。

建议单图：

```text
512x256 或 768x384
```

第一轮核心输出：

```text
work/p5_leishen/t02/geometry_contact_sheet.png
work/p5_leishen/t02/geometry_candidates.json
```

contact sheet 每格必须显示短 candidate id，路径映射写入 JSON。

---

## 6. Mandatory visual review between geometry and textures

Luna 生成 geometry contact sheet 后必须 STOP 并 push。

Chat/Sol 读取图片后：

- 与用户已确认的 Web reference 比较枪托、机匣、护木、枪口、弹匣、提把/瞄具、独特装饰结构和整体比例；
- 选 Top 3~10；
- 必要时把 contact sheet / 少量候选给用户再次确认。

在 Chat/Sol 发布下一条明确 Task Spec 前，Luna不得进入材质阶段。

---

## 7. Phase C — textured side-view only for finalists

只有 Chat/Sol 固定 Top 少量候选后，才允许：

1. 找候选对应本地 DTX/TGA/CFG；
2. 使用现有安全解码能力转成派生 PNG；
3. 将 diffuse / alpha 等按可验证方式映射到模型 UV；
4. 生成与官方百科尽量同方向的标准侧面图；
5. 生成 `textured_contact_sheet.png`。

不为第一轮筛选临时开发大型 DTX/Shader 系统；如果当前能力不足，标记 `not_available`，由下一 Task Spec处理。

---

## 8. Evidence semantics

视觉相似只负责 candidate identification，不单独证明 final provenance。

最终仍需 P5-T03 闭合：

```text
confirmed visual candidate
  -> local LTB
  -> local DTX/TGA
  -> Shader/CFG
  -> QV / sound / animation / config associations
  -> path + SHA-256
```

Luna 在 T02 任何阶段都不得写 `IDENTITY_CONFIRMED`。

---

## 9. Current stop rule

当前状态是：

```text
BLOCKED_BY_USER_REFERENCE_CONFIRMATION
```

所以此刻 Luna 的唯一正确行为：

> pull 最新 master -> 读取本 spec -> 发现用户 reference 尚未确认 -> 不扫描、不导出、不渲染、不修改文件 -> STOP。

只有 Chat/Sol 在用户明确确认目标图片后更新本文件状态，才允许开始本地 T02。