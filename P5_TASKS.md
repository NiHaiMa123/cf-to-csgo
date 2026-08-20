# P5_TASKS.md — 最终雷神资产定位任务流

> 当前阶段：**P5 — ACTIVE**
>
> Planner / Reviewer：**Chat/Sol**
>
> Local Executor：**Luna / 普通 Codex Agent**
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git 与 `data/**` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 固定业务流程

P5 的标准识别顺序统一为：

```text
P5-T01  官方图鉴 Web Search + 用户确认目标图
    ↓
P5-T02  本地候选缩圈 / 去重 / 百科式侧视图 + 用户确认本地候选
    ↓
P5-T03  Resource Graph / provenance closure
    ↓
P5-T04  Chat/Sol final identity review
```

关键原则：

- Web Search 是 T01 的强制执行步骤；
- 必须找到 CF 官方武器百科详情页及其实际加载的真实武器图片；
- 给用户看的目标图必须是网上找到的真实图片，禁止 AI 生成图代替；
- 用户确认官方目标图之前，不能开始本地视觉匹配；
- 内部英文名、跨服名、文件名、T01 legacy score 都只能作为候选线索；
- 本地候选首轮采用最低成本的单张正交侧视图，不做四视图、动画、IK、Source retarget 或高质量渲染；
- 最终身份必须经 T03 provenance + T04 Review，不能仅凭“看起来像”。

---

## 2. P5-T01 — 官方 CF 武器百科目标图确认

状态：**READY_FOR_LUNA**。

正式协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

Luna 必须：

```text
Web Search
  -> CF 官方武器百科
  -> 官方详情页
  -> 官网实际加载图片
  -> 把真实网络图片给用户看
  -> 等用户确认
```

正常等待状态：

```text
AWAITING_USER_REFERENCE_CONFIRMATION
```

用户否决时，Luna 在同一个 T01 中继续搜索，不需要回 Chat/Sol 改 Plan。

T01 完成条件：

```text
PASS / USER_REFERENCE_CONFIRMED
```

证据输出：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

---

## 3. 历史本地广召回 — LEGACY PRE-SCAN

此前 Luna 已经以旧 `P5-T01` 编号执行过一次本地 `data/**` 广召回。为避免重扫 16 万文件，该执行结果继续保留，但不再定义为当前 T01。

兼容说明：[`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)。

历史提交：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

历史输出：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

这些文件现在只是 **T02 candidate pool**。

旧 score 不代表 identity confidence。

---

## 4. P5-T02 — 本地候选缩圈与百科式侧视锁定

状态：**BLOCKED_BY_T01_USER_REFERENCE**。

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

用户确认 T01 官方目标图后，Luna 可以直接进入 T02，不需要 Chat/Sol 再改状态。

T02 流程：

```text
读取 confirmed official reference
  -> 复用 LEGACY PRE-SCAN
  -> 聚焦 M4/M4A1 PLAYERVIEW
  -> 排除 BL/GR/WOMAN/纯手臂/QV
  -> exact SHA 去重
  -> geometry signature 聚类（可用时）
  -> 每个 unique cluster 只渲染一个 representative
  -> 应用本地 diffuse/主纹理
  -> 百科式正交侧视 PNG
  -> contact sheet / Top 5–15
  -> 用户确认本地候选
```

首轮渲染目标：

```text
768x384 或 1024x512
透明/白背景
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
无 Cycles
```

用户确认后状态：

```text
USER_VISUAL_MATCH_CONFIRMED
```

仍不是最终 `IDENTITY_CONFIRMED`。

---

## 5. P5-T03 — Resource Graph / provenance closure

状态：`BLOCKED_BY_T02`。

对用户视觉确认的本地 candidate 建立：

```text
PLAYERVIEW model LTB
  -> diffuse / DTX / TGA
  -> Alpha / Normal / Specular
  -> Shader / CFG / material
  -> QV / world family
  -> sound WAV
  -> animation / config references
```

每个资源记录：

```text
relative_path
sha256
size_bytes
relation
source_class
confidence / unresolved reason
```

---

## 6. P5-T04 — Final identity Review

状态：`BLOCKED_BY_T03`。

由 Chat/Sol 最终输出之一：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才允许进入 P6。

---

## 7. 角色边界

### Luna / Codex

负责：

- T01 Web Search 和官方图片展示；
- 两个用户 Gate 的交互等待与继续执行；
- T02 本地候选缩圈/去重/实际模型侧视图生成；
- 证据产出；
- 不上传 `data/**`。

不得：

- 生成目标 reference 图；
- 未确认官方目标图就进入 T02；
- 凭文件名预锁候选；
- 自行写最终 `IDENTITY_CONFIRMED`；
- 修改 P4 frozen pipeline。

### Chat/Sol

负责：

- Task Spec / acceptance criteria；
- T03 provenance 审查；
- T04 最终 identity Review；
- 真正 BLOCKED/INVALID 时重新设计流程。

正常的用户确认 Gate 不需要返回 Chat/Sol 重写 Plan。