# CODEX_TASKS.md — Codex / Luna 本地执行合同

> 本文件只给 **Codex 环境中的 Agent** 使用，包括 Luna、本地执行 Agent，以及用户明确调用时的 Codex Sol。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；默认本地 Executor = Luna / 普通 Codex Agent。**

---

## 1. 当前阶段

截至 2026-08-21：

- P4：**`PASS / FROZEN`**，但其材质 fidelity/provenance 不能作为原生 CF 贴图解码已完成的证据；
- P5：**ACTIVE — 最终雷神资产定位**；
- P5-T01：**`PASS / USER_REFERENCE_CONFIRMED`**；
- 当前任务：**P5-T02 `ACTIVE / NATIVE_TEXTURE_RECOVERY_REQUIRED`**；
- 当前正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)；
- 历史本地广召回：[`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)，T02 继续复用；
- 当前 C029/C103 灰模、raw PV DTX UV diagnostic、Alpha/Specular approximation 均为 `diagnostic_only`；
- **原生贴图/材质正确还原是 T02 hard gate，不允许跳到 T03；**
- P4 visible Inspect / 手指 retarget 属于 P7，不是当前任务。

---

## 2. Luna 默认角色

角色：**本地执行器 + 用户 Gate 交互执行器 + 证据生产器**。

Luna 负责：

- 安全拉取最新 `master`；
- 严格执行当前 Task Spec；
- 读取本地 `data/**`、运行本地 parser/CFRezManager/Blender/Python/C# 等；
- 对本地 CF 原生 DTX/TGA/CFG/LTB/material binding 做可验证逆向；
- 保留命令、hash、报告和派生预览；
- 只有在 native material gate 通过后才把最终候选图给用户确认；
- `data/**` 原始资产永远不上传。

Luna 不是最终 Reviewer，不得：

- 生成目标 reference 图；
- 用模型记忆代替已有 official reference evidence；
- 把第三方/网络/CS1.6 MOD 图片冒充本地 CF 材质；
- 仅凭文件名预锁 identity；
- 仅凭灰模、mask-like DTX 或 Alpha/Specular 近似要求用户强选；
- 自行写最终 `IDENTITY_CONFIRMED`；
- 修改 P4 frozen conversion pipeline。

---

## 3. 当前 P5 编号

```text
P5-T01  官方图鉴 Web Search + 用户确认目标图                    PASS
P5-T02  本地候选缩圈 + 原生材质恢复 + 用户确认本地候选          ACTIVE
P5-T03  Resource Graph / provenance closure                    BLOCKED_BY_T02
P5-T04  Chat/Sol final identity review                         BLOCKED_BY_T03
```

此前以旧 `P5-T01` 名义完成的本地广召回现在统一视为：

```text
LEGACY PRE-SCAN
```

其输出不作废，但旧 score 只代表 recall priority，不代表 identity confidence。

---

## 4. 每次启动顺序

1. 读取 `AGENTS.md`；
2. 读取 `plan.md` 第 1 节；
3. 读取本文件 `CODEX_TASKS.md`；
4. 读取 `P5_TASKS.md`；
5. **当前必须读取 `P5_T02_TASK_SPEC.md`；**
6. 读取：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t02/execution.json
work/p5_leishen/t02/visual_shortlist.json
```

7. `git status --short --branch`；
8. tracked 工作区可安全同步时执行 `git fetch origin` + `git pull --rebase origin master`；
9. 从 **P4 material provenance audit + native texture recovery** 继续，不重做已完成 T01 Web Search。

不要把聊天记忆、旧分支、旧 MOD、历史别名猜测或旧 candidate score 当作 authoritative identity。

---

## 5. T01 已完成

官方目标 evidence 已固定：

```text
work/p5_leishen/t01_reference/official_reference.json
```

用户已确认 `M4A1-雷神` 官方详情页和官方图片。除非 evidence 损坏或用户明确否决，不重跑 T01。

---

## 6. P5-T02 — 当前必须执行的原生材质硬 Gate

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

当前已完成：

```text
LEGACY PRE-SCAN reuse
  -> M4/M4A1 PLAYERVIEW 缩圈
  -> exact SHA clusters
  -> geometry shortlist
  -> C029/C103 finalist diagnostics
```

当前未完成：

```text
native CF color/material reconstruction
```

下一步固定为：

```text
P4 external-material provenance audit
  -> Transformers native material-family inventory
  -> re-test DTX container/pixel-format interpretation
  -> recover LTB material/texture binding
  -> reverse/analyze WeaponShader CFG semantics
  -> differential analysis across same-geometry skin variants
  -> offline native shader hypotheses
  -> Native material acceptance gate
  -> native-material finalist render
  -> USER LOCAL-CANDIDATE GATE
```

### P4 已知 provenance 风险

P4 Prototype build report 中存在以下 external 输入：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

它曾被用于生成 `bornbeast_base.png` / self-illum，再转换成 Source VTF。

因此：

- P4 仍证明 conversion/build/package/MIGI 技术链；
- P4 不证明 native CF texture fidelity；
- external texture 只能作为 differential/reference，禁止进入雷神最终材质。

### 当前 texture/shader diagnostics 的语义

以下均不能 PASS：

```text
C029/C103 gray geometry
PV-M4A1_S_Transformers.DTX interpreted only as headerless BGR24
raw PV DTX + UV diagnostic
Alpha/Specular scalar shader approximation
raw-rgb-strip CFG preview
```

特别注意：仓库已有 `CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs`，支持 LithTech DTX header/version 与多种 pixel formats。当前 headerless BGR24 解释必须与正式 decoder / 更上游原始 bytes 交叉验证。

### T02 正常继续状态

只要还在做材质逆向而非环境完全不可用，状态写：

```text
NATIVE_TEXTURE_RECOVERY_INCOMPLETE
```

**这不是允许跳过的 soft risk。**

只有 native material acceptance gate 通过后，才能给用户最终候选图并等待：

```text
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

用户确认后只能写：

```text
USER_VISUAL_MATCH_CONFIRMED
```

不能写最终 `IDENTITY_CONFIRMED`。

---

## 7. Native material evidence principle

最终可见颜色的每个输入必须属于：

```text
local_cf
或
verified deterministic derivative of local_cf / decoded CFG semantics
```

允许：

- 本地 LTB geometry/UV；
- 本地 DTX/TGA/CFG；
- 本地 Alpha/Normal/Specular/lookup/detail/emissive/effect；
- 从这些输入确定性生成的离线 diagnostic/render。

禁止作为最终材质输入：

- CS1.6/CSGO MOD texture；
- 网络下载 texture；
- 官方百科 PNG；
- AI 生成/补全 texture；
- 从 external texture 采样或烘焙出的颜色。

外部图只可用于 reference / differential hypothesis，不属于 final provenance。

---

## 8. 最简侧面图原则

```text
1 unique candidate = 1 orthographic side PNG
768x384 或 1024x512
透明/白背景
统一方向/fit
无手臂
无动画
无 IK
无 Source retarget
无复杂灯光
无 Cycles
```

但 finalist 必须使用通过 native material gate 的材质，不能用灰模完成最终确认。

---

## 9. Git / data 规则摘要

完整规则见 [`AGENTS.md`](AGENTS.md)。特别强调：

- `data/**` 永远 local-only；
- pull 前检查 `git status`；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .`、`git add -A`、`git add --all`；
- 默认禁止 destructive Git clean/reset；
- 不 force-push；
- 不使用 mirror/delete 同步破坏 ignored 本地资产。

---

## 10. 返回 Chat/Sol 的条件

正常材质逆向中的失败 hypothesis 不需要返回 Chat/Sol，记录 rejection evidence 后继续下一条。

只有以下情况才返回：

- 本地原始 Transformers 资产缺失，无法继续；
- DTX/CFG/绑定结构经多条独立路线仍无法取得可验证进展；
- 需要改变 Task Spec；
- 出现 INVALID 条件；
- T02 native-material + user visual evidence 全部完成，需要进入 T03/T04 Review。
