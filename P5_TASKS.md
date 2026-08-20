# P5_TASKS.md — 最终雷神资产定位任务流

> 当前阶段：**P5 — 最终雷神本地 CF 资产定位**
>
> Planner / Reviewer：**Chat/Sol**
>
> Local Executor：**Luna / 普通 Codex Agent**
>
> 项目唯一 authoritative progress/status 仍以 [`plan.md`](plan.md) 第 1 节为准；Git 与 `data/**` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. P5 的核心原则

P5 不是“根据文件名猜雷神”，而是建立可追溯的 **asset identity chain**。

最终确认必须尽量形成：

```text
官方武器身份 / reference
  -> 本地配置、ID、资源引用或候选召回
  -> PLAYERVIEW LTB 几何/机械结构
  -> DTX/TGA atlas 与 UV / Shader 关联
  -> 同变体声音、动画、配置关联
  -> 原始相对路径 + SHA-256
  -> Chat/Sol identity review
```

任何单一证据（尤其仅文件名或“看起来像”）都不能直接得到 `IDENTITY_CONFIRMED`。

---

## 2. P5 任务拆分

### P5-T01 — 官方身份锚点与本地候选召回

状态：**EXECUTION_PASS / REVIEWED**。

执行协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

执行提交：`ab7e2ef3394991ef0b4468f34cf4d6849b917dc2`。

结果：

- `data/**` 只读扫描 165082 个文件；
- 召回 2856 个候选，其中 1281 个 LTB；
- 441 个 canonical LTB 尝试轻量 inspect；
- candidate index / matrix / report / execution evidence 已生成；
- 无 candidate 被 Luna 误写成最终确认。

Chat/Sol Review 后补充了关键 alias correction：

```text
国服 M4A1-雷神  -> M4A1-S Transformers
国服 M4A1-黑骑士 -> M4A1-S Born Beast
```

因此 T01 的原始 score 只保留为召回历史，不再代表 T02 identity priority。`BornBeast` 降级为 negative control，标准 `M4A1_S_Transformers` 资源族成为主候选。

### P5-T02 — 候选模型/贴图特征提取与视觉比对

状态：**READY_FOR_LUNA**。

正式执行协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

冻结候选集合：

1. PRIMARY：`PV-M4A1_S_Transformers.LTB`；
2. SAME-FAMILY CONTROL：`PV-M4A1_S_Transformers_Classic.LTB`；
3. NEGATIVE CONTROL：`PV-M4A1_S_BornBeast.LTB`。

并核对 exact-match 本地资源族：

```text
PV-M4A1_S_Transformers.DTX
M4A1_S_Transformers_Alpha.TGA
M4A1_S_Transformers_N.TGA
M4A1_S_Transformers_S.TGA
M4A1_S_Transformers.CFG
QV-M4A1_S_Transformers.LTB / DTX
```

T02 只生成少量结构报告和标准多视图派生预览，不再全量扫描或批量渲染。

### P5-T03 — Resource Graph / provenance 收敛

状态：`BLOCKED_BY_T02_REVIEW`。

对 T02 通过的主候选建立：

```text
weapon identity
  -> model LTB
  -> texture DTX/TGA
  -> Shader/CFG/material
  -> animation/config
  -> sound WAV
```

每个本地资源记录 relative path、SHA-256、size、关联证据和 confidence。

### P5-T04 — 最终身份 Review

状态：`BLOCKED_BY_T03`。

由 Chat/Sol 执行最终 identity review，只允许输出：

- `IDENTITY_CONFIRMED`
- `IDENTITY_PROBABLE_NEEDS_EVIDENCE`
- `REWORK_CANDIDATE_SEARCH`

只有 `IDENTITY_CONFIRMED` 才允许进入 P6 替换 final inputs。

---

## 3. 证据强度

从强到弱：

1. 官方 item/resource ID 与本地配置/资源引用直接闭合；
2. 本地配置/资源 graph 明确指向同一 LTB/texture set；
3. 跨服/内部英文 alias 与本地 resource family 精确一致；
4. 模型独特轮廓与机械结构匹配；
5. atlas/纹理/Logo/发光区域与 reference 匹配，且 UV/材质引用可对应；
6. 同变体 Shader/声音/动画路径关联；
7. 文件名/目录名关键词。

文件名只用于 candidate recall，不作为最终身份证明。但当外部 alias 已独立建立后，`M4A1_S_Transformers` 的 exact family token 是重要的交叉证据。

---

## 4. 角色边界

### Luna / Codex

- 严格按当前 Task Spec 扫描和产出本地证据；
- 不自行扩大 scope；
- 不把 Top candidate 写成“最终雷神”；
- 不修改 P4 frozen pipeline；
- 不上传 `data/**`；
- 完成后 push 允许的 index/report/derived previews，然后停止等待 Chat/Sol。

### Chat/Sol

- 设计每个阶段 Task Spec；
- 审查候选排序和证据质量；
- 决定少量 OBJ/Blender/纹理视觉比对范围；
- 最终做 identity judgement。
