# P5_TASKS.md — 最终雷神资产定位任务流

> 当前阶段：**P5 — 最终雷神本地 CF 资产定位**
>
> Planner / Reviewer：**Chat/Sol**
>
> Local Executor：**Luna / 普通 Codex Agent**
>
> 项目唯一 authoritative progress/status 仍以 [`plan.md`](plan.md) 第 1 节为准；Git 与 `data/**` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. P5 核心原则

P5 不是根据文件名、跨服英文名或模型记忆猜“哪个是雷神”，而是建立可重复的资产身份链。

固定流程：

```text
Luna Web Search
  -> CF 官方武器百科详情页
  -> 官网实际加载的目标武器图片
  -> 用户确认目标图
  -> 本地候选缩圈 / 去重
  -> 最简百科式贴图正交侧视图
  -> contact sheet / visual shortlist
  -> 用户确认本地候选
  -> model / texture / shader / sound provenance closure
  -> Chat/Sol final identity review
```

强制规则：

- **官网图鉴搜索属于 Luna 的执行任务，不属于每次都由 Chat/Plan 端代做的规划步骤。**
- 目标图必须是 Web Search 找到的真实网络图片；禁止生成图代替。
- USER REFERENCE GATE 必须落在 CF 官方武器百科详情页及其实际加载图片。
- 第三方 Wiki、Fandom、Bilibili、贴吧、媒体页只能帮助发现搜索线索，不能绕过官方图鉴 Gate。
- 只有用户确认官网目标图后，Luna 才能继续本地 candidate matching。
- 任何 `Transformers`、`BornBeast`、`Thor`、`Leishen` 等内部/英文 token 都只能作为候选线索，不能提前固定最终身份。

---

## 2. P5-T01 — 本地广召回

状态：**EXECUTION_PASS / REVIEWED**。

执行协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

执行提交：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

已完成：

- `data/**` 只读 inventory：165082 files；
- 召回 2856 candidates；
- 其中 1281 LTB；
- 441 canonical LTB 尝试轻量 inspect；
- 生成 candidate index / matrix / report / execution evidence；
- 未把任何 candidate 写成最终确认。

T01 的 score 只用于**广召回历史排序**，不能作为最终 identity confidence。

历史讨论中出现过 `Transformers` / `BornBeast` 等跨服别名假设；从 P5-T02 起这些都降级为普通候选线索，必须重新经过官方目标图 + 本地视觉比对验证。

---

## 3. P5-T02 — 官方目标图确认 + 本地百科式侧视候选锁定

状态：**READY_FOR_LUNA**。

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

### T02-A：Mandatory official Web Search

Luna 必须先搜索：

```text
M4A1-雷神
https://cf.qq.com/cp/a20250701wqbk/index.html
```

目标是定位官方武器百科详情页、`itemid`（若可取得）和该详情页实际加载的武器图片。

然后在 Codex 对话里**直接给用户看真实官网图片**并等待确认。

正常状态：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
```

这不是 blocker，不需要回 Chat 重新设计。

### T02-B：候选缩圈与去重

用户确认官网目标图后，Luna 直接继续：

- 复用 T01 candidate index/matrix；
- 聚焦 M4/M4A1 第一人称 `PLAYERVIEW` 候选；
- 排除/归档 `_BL`、`_GR`、`WOMAN`、纯手臂、QV/第三人称等；
- exact SHA 去重；
- 可用时再按 geometry signature 聚类；
- 每个独特 cluster 首轮只保留一个 representative 渲染。

### T02-C：最快百科式侧视图

首轮每个 unique representative 只生成**一张**标准侧面图：

```text
orthographic side view
768x384 或 1024x512
透明/白背景
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
```

优先把本地 CF diffuse/主颜色纹理通过模型 UV 应用到 mesh 后渲染，而不是直接比较方块 atlas。

如果某候选暂时无法解析纹理，可先生成灰模/轮廓用于便宜排除，但不能仅凭灰模最终确认。

### T02-D：第二个人工视觉 Gate

Luna 生成 contact sheet / Top shortlist 后，把本地实际侧视候选给用户看。

用户确认后状态为：

```text
USER_VISUAL_MATCH_CONFIRMED
```

仍然不是最终 `IDENTITY_CONFIRMED`；T03 还要闭合 provenance。

---

## 4. P5-T03 — Resource Graph / provenance closure

状态：`BLOCKED_BY_T02`。

对用户视觉确认的本地 candidate 建立：

```text
confirmed display target
  -> PLAYERVIEW model LTB
  -> diffuse / DTX / TGA
  -> Alpha / Normal / Specular
  -> Shader / CFG / material
  -> QV / world family
  -> sound WAV
  -> animation / config references
```

每个本地资源至少记录：

```text
relative_path
sha256
size_bytes
relation
source_class
confidence / unresolved reason
```

最终来源只能是本地 CF 原始资产；网络图片只保留 reference URL/hash，不进入 final game asset provenance。

---

## 5. P5-T04 — Final identity Review

状态：`BLOCKED_BY_T03`。

由 Chat/Sol 根据 T02 用户视觉 Gate + T03 provenance evidence 最终输出之一：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才允许进入 P6 替换 final inputs。

---

## 6. 证据强度

从强到弱：

1. 用户确认的 CF 官方武器百科目标图；
2. 本地模型标准侧面轮廓/机械结构与官方图匹配；
3. 本地真实 diffuse/纹理映射后的颜色/纹路/Logo/发光区域匹配；
4. 本地配置/resource graph 明确闭合同一 model/texture/shader family；
5. QV/sound/animation 等同变体资源关联；
6. 路径/文件名/跨服英文 token。

文件名和英文 token 永远不能单独得到 final identity。

---

## 7. 角色边界

### Luna / Codex

Luna 负责完整 T02 交互式执行：

```text
Web Search
  -> 给用户看真实官网图片
  -> 等用户确认
  -> 本地缩圈 / 去重 / 单侧面批量渲染
  -> 给用户看本地候选
  -> 等用户确认
  -> push evidence
  -> STOP
```

两个用户 Gate 都属于同一个 Task Spec，**不需要每个 Gate 都返回 Chat/Sol 改 Plan。**

Luna 不得：

- 生成目标 reference 图；
- 用户未确认官网图就开始本地视觉锁定；
- 预锁 `Transformers` / `BornBeast` 等名字；
- 修改 P4 frozen pipeline；
- 上传 `data/**`；
- 自行写最终 `IDENTITY_CONFIRMED`；
- T02 完成后自行进入 T03。

### Chat/Sol

Chat/Sol 负责：

- 维护 Task Spec / acceptance criteria；
- 当 Task Spec 真正遇到 BLOCKED/INVALID 时重新设计；
- T03/T04 的 provenance 和最终 identity review。

Chat/Sol **不需要**在每一把武器上重复手工执行“先搜官网图给用户确认”这一步；该行为已经固化为 Luna 的 T02 执行协议。