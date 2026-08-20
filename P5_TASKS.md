# P5_TASKS.md — 最终雷神资产定位任务流

> 当前阶段：**P5 — 最终雷神本地 CF 资产定位**
>
> Planner / Reviewer：**Chat/Sol**
>
> Local Executor：**Luna / 普通 Codex Agent**
>
> 项目唯一 authoritative progress/status 仍以 [`plan.md`](plan.md) 第 1 节为准；Git 与 `data/**` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 核心原则

P5 不是根据文件名猜雷神，而是建立可追溯的 asset identity chain。

新的强制顺序：

```text
Web Search / 官方武器百科
  -> Chat/Sol 展示认为正确的目标武器图片
  -> 用户确认“对，就是这把”
  -> 本地 M4/M4A1 candidate narrowing
  -> geometry/hash 去重
  -> 灰模正交侧视 contact sheet
  -> Chat/Sol / 用户视觉排除
  -> 少量 finalist 再做本地贴图侧视
  -> Resource Graph / provenance
  -> Chat/Sol 最终身份 Review
```

**用户没有确认目标图片前，不允许 Luna 开始本地 T02。**

任何单一证据（文件名、跨服 alias、T01 score、视觉相似）都不能直接得到 `IDENTITY_CONFIRMED`。

---

## 2. P5-T01 — 候选召回

状态：**EXECUTION_PASS / REVIEWED**。

执行提交：`ab7e2ef3394991ef0b4468f34cf4d6849b917dc2`。

结果：

- 扫描 `data/**` 165082 个文件；
- 召回 2856 个候选，其中 1281 个 LTB；
- 441 个 canonical LTB 尝试轻量 inspect；
- candidate index / matrix / report / execution evidence 已生成；
- 没有候选被 Luna 宣布为最终雷神。

T01 score 只代表 recall priority，不代表 identity confidence。

---

## 3. P5-T02 — 目标图确认 + 统一侧视图识别

状态：**BLOCKED_BY_USER_REFERENCE_CONFIRMATION**。

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

当前第一 Gate：

1. Chat/Sol 必须 Web Search / Image Search `M4A1-雷神`；
2. 把认为正确的目标武器图展示给用户；
3. 等用户明确确认；
4. 用户确认后才能把 T02 改为 `READY_FOR_LUNA`。

先前把：

```text
M4A1-雷神 -> M4A1-S Transformers
```

写成确定映射，现撤销为：

```text
UNVERIFIED_ALIAS
```

原因：公开跨服命名证据存在冲突。以后 alias 只用于 candidate token，不作为先验锁定。

用户确认目标图后，T02 本地识别分两轮：

### T02-A 几何快速筛选

```text
M4/M4A1 PLAYERVIEW LTB
 -> 排除 BL/GR/WOMAN presentation variants
 -> SHA / geometry signature 聚类去重
 -> 每个独特枪体只保留一个 representative
 -> 灰模正交侧视 PNG
 -> geometry_contact_sheet.png
 -> STOP for Chat/Sol review
```

### T02-B 材质精筛

仅对 Chat/Sol 选中的 Top 3~10：

```text
local DTX/TGA/CFG
 -> UV/diffuse 派生预览
 -> 百科式标准侧视图
 -> textured_contact_sheet.png
 -> Top 1~3
```

---

## 4. P5-T03 — Resource Graph / provenance

状态：`BLOCKED_BY_T02_REVIEW`。

对 T02 finalist 建立：

```text
weapon identity
  -> model LTB
  -> texture DTX/TGA
  -> Shader/CFG/material
  -> animation/config
  -> sound WAV
```

每个本地资源记录 relative path、SHA-256、size、关联证据和 confidence。

---

## 5. P5-T04 — 最终身份 Review

状态：`BLOCKED_BY_T03`。

由 Chat/Sol 输出：

- `IDENTITY_CONFIRMED`
- `IDENTITY_PROBABLE_NEEDS_EVIDENCE`
- `REWORK_CANDIDATE_SEARCH`

只有 `IDENTITY_CONFIRMED` 才允许进入 P6。

---

## 6. 角色边界

### Luna / Codex

- 严格按当前 Task Spec执行；
- 不自行扩大 scope；
- 不自行 Web Search 后替用户确认目标图；
- 不把某个英文 alias 当作确定映射；
- 不把 Top candidate 写成最终雷神；
- 不修改 P4 frozen pipeline；
- 不上传 `data/**`。

### Chat/Sol

- Web Search 定义 reference；
- 必须先把目标图展示给用户确认；
- 设计本地候选缩圈和侧视图 Task Spec；
- 审查 contact sheet；
- 最终做 identity judgement。
