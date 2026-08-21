# CODEX_TASKS.md — Codex / Luna 本地执行合同

> 本文件只给 **Codex 环境中的 Agent** 使用，包括 Luna、本地执行 Agent，以及用户明确调用时的 Codex Sol。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = Luna / 普通 Codex Agent。**

---

## 1. 当前阶段

截至 2026-08-21：

- P4 baseline：**`PASS / FROZEN`**；
- **P4-M01：`ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`，这是当前唯一执行任务；**
- P5-T01：`PASS / USER_REFERENCE_CONFIRMED`；
- P5-T02：`PAUSED_BY_P4_M01`；
- P5-T03/T04：继续 blocked；
- P7 visible Inspect / 手指 retarget / CF 原动画不是当前任务。

当前正式协议：

```text
P4_M01_TASK_SPEC.md
```

P4 baseline 的 geometry / Source build / package / MIGI 技术证据继续冻结；P4-M01 只重新打开 native CF material decode / binding / shader fidelity。Native material recovery 是当前 hard requirement，但 `REQUIRED` 不作为单独 lifecycle status。

---

## 2. Luna 当前角色

角色：**本地材质逆向执行器 + 证据生产器**。

Luna 负责：

- 安全同步最新 `master`；
- 严格执行 `P4_M01_TASK_SPEC.md`；
- 读取本地 `data/**`；
- 对 BornBeast DTX/TGA/CFG/LTB material binding 做可验证逆向；
- 必要时最小扩展 CFRezManager decoder/inspection code；
- 构建 deterministic offline shader hypotheses；
- 保存命令、offset、hash、报告、派生预览和 rejection evidence；
- 完成后把 scoped code/evidence push 到 `master`；
- `data/**` 原始资产永不上传。

Luna 不得：

- 继续要求用户在 C029/C103 灰模之间强选；
- 重跑已完成的雷神 T01 Web Search；
- 把 external CS1.6/MOD texture 当 BornBeast 或雷神 final input；
- 从 external reference 抠色、采样、烘焙后冒充 local CF；
- 把 `CfgBinaryStripDecoder` 的 raw strip 当 CFG semantic decode；
- 仅凭“能显示成图片”宣布 DTX/TGA 格式正确；
- 覆盖历史 frozen addon / P4 evidence；
- 修改 frozen M4A4 skeleton/sequence/attachment/build contract；
- 自行恢复 P5-T02 或写最终 `IDENTITY_CONFIRMED`。

---

## 3. 每次启动顺序

1. `git status --short --branch`；
2. 确认当前分支为 `master`；
3. tracked worktree 可安全同步时：

```bash
git fetch origin
git pull --rebase origin master
```

4. 读取 [`AGENTS.md`](AGENTS.md)；
5. 读取 [`plan.md`](plan.md) 第 1 节；
6. 读取本文件；
7. 读取 [`P4_TASKS.md`](P4_TASKS.md)；
8. **读取 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)；**
9. 读取 P4 BornBeast 历史 material evidence：

```text
work/m4a1_s_bornbeast/p4_prototype_01/build_report.json
work/m4a1_s_bornbeast/materials/material_decode_report.json
work/m4a1_s_bornbeast/materials/**
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
```

10. 从 P4-M01 provenance audit 开始/继续。

`P5_TASKS.md` 和 `P5_T02_TASK_SPEC.md` 当前只用于理解后续 handoff，不是当前第一执行入口。

---

## 4. 当前任务：P4-M01 Native Material Recovery

### 已知事实

P4 历史可识别材质使用过：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此：

```text
P4 conversion/runtime chain = valid frozen evidence
P4 native CF material fidelity = not closed
```

当前必须在 BornBeast 上解决 native material method，再把方法交给 P5 Transformers。

### 固定执行路线

```text
A. P4 material provenance audit
-> B. BornBeast local material-family inventory
-> C. DTX container/pixel-format revalidation
-> D. TGA interpretation revalidation
-> E. LTB material/texture/render-style binding recovery
-> F. WeaponShader CFG binary semantic reverse
-> G. same-geometry / variant differential analysis
-> H. deterministic offline shader hypotheses
-> I. native material closure (0 external pixels)
-> J. Source 1 integration check on a NEW test addon, only after closure
```

详细 acceptance/rejection 规则只看 `P4_M01_TASK_SPEC.md`。

---

## 5. 关键 decoder 语义

仓库已有：

```text
CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs
CFRezManager/Decoders/Images/TgaThumbnailDecoder.cs
CFRezManager/Decoders/Config/CfgTextDecoder.cs
CFRezManager/Decoders/Config/CfgBinaryStripDecoder.cs
```

注意：

- `DtxThumbnailDecoder` 已有 LithTech DTX header/version 和 BGRA/RGBA/Palette/DXT1/3/5 路径；旧 headerless BGR24 解释必须交叉验证；
- `CfgBinaryStripDecoder` 源码只是 raw RGB strip detector/renderer，**不是 shader CFG parser**；
- 旧 BornBeast TGA 特殊布局解释也必须重新验证；
- decoder 产出 PNG 只证明“某种解释能输出像素”，不证明解释语义正确。

---

## 6. P4 frozen 边界

P4-M01 不允许修改：

```text
历史 P4 frozen run/package/deploy evidence
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 runtime slot
57-bone Source reference
sequence/attachment contract
RV-01 ~ RV-06 历史证据
```

允许新增/修改：

```text
CFRezManager/Decoders/** （与材质恢复直接相关）
相关 inspection/export code
scripts/material_recovery/**
材质恢复专用新增脚本/测试
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

如果材质恢复必须改变 frozen conversion contract，返回 Chat/Sol，不自行修改。

---

## 7. 状态语义

正常继续：

```text
P4-M01 = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

单个 DTX/CFG/shader hypothesis 失败不需要停；保存 rejection evidence 后继续。

通过：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

Luna 只提交 evidence，不自行把 authoritative `plan.md` 改成 PASS；最终状态由 Chat/Sol Review。

真正 BLOCKED 才返回：

- BornBeast 必要本地原始资源缺失；
- 多条独立路线都无法访问/解释必要 bytes；
- 必须改变 frozen conversion contract；
- Task Spec 本身需要修改。

---

## 8. P5 handoff

P4-M01 经 Chat/Sol Review PASS 后，才恢复：

```text
P5-T02
-> apply validated material-recovery method to M4A1_S_Transformers
-> Transformers-specific extension if required
-> native material finalist
-> USER LOCAL-CANDIDATE GATE
```

在此之前 P5-T02 保持 `PAUSED_BY_P4_M01`。

---

## 9. Git / data 规则摘要

完整规则见 `AGENTS.md`。特别强调：

- Agent handoff 只认 `master`；
- `data/**` 永远 local-only；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `git add -A` / `git add --all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不使用 mirror/delete 同步；
- 原始 LTB/DTX/TGA/CFG 不上传，只上传代码、报告、hash 和派生预览。
