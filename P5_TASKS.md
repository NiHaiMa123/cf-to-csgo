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

状态：**READY_FOR_LUNA**。

正式执行协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

目标：

- 固定目标身份为 **M4A1-雷神**；
- 记录官方 CF 武器图鉴 reference URL；
- 在本地 `data/**` 建立与 M4/M4A1/PLAYERVIEW/配置引用相关的候选集合；
- 生成 machine-readable candidate index / matrix；
- 只做候选排序，不做最终身份宣告。

### P5-T02 — 候选模型/贴图特征提取与视觉比对

状态：`BLOCKED_BY_T01`。

预期输入：T01 排名前列候选。

预期工作：

- 对少量 LTB 候选提取 mesh、vertex、triangle、bounds、node/material 特征；
- 必要时统一导出 OBJ，并生成标准多视图；
- 将关联 DTX/TGA 转为可审查缩略图/contact sheet；
- Chat/Sol 对照官方图鉴/用户 reference 做模型轮廓、机械结构、配色、Logo/发光区域等比对。

T02 不允许全量 Blender 渲染整个 `data/**`。

### P5-T03 — Resource Graph / provenance 收敛

状态：`BLOCKED_BY_T02`。

对 Top candidate 建立：

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
3. 模型独特轮廓与机械结构匹配；
4. atlas/纹理/Logo/发光区域与 reference 匹配，且 UV/材质引用可对应；
5. 同变体 Shader/声音/动画路径关联；
6. 文件名/目录名关键词。

文件名只用于 candidate recall，不作为最终身份证明。

---

## 4. 角色边界

### Luna / Codex

- 严格按当前 Task Spec 扫描和产出本地证据；
- 不自行扩大 scope；
- 不把 Top 1 候选写成“最终雷神”；
- 不修改 P4 frozen pipeline；
- 不上传 `data/**`；
- 完成后 push 允许的 index/report，然后停止等待 Chat/Sol。

### Chat/Sol

- 设计每个阶段 Task Spec；
- 审查候选排序和证据质量；
- 决定何时值得进行 OBJ/Blender/纹理视觉比对；
- 最终做 identity judgement。
