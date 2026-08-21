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
P5-T02  本地候选缩圈 / 原生材质正确还原 / 用户确认本地候选
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
- 内部英文名、跨服名、文件名、legacy score 都只能作为候选线索；
- 本地候选首轮采用最低成本的单张正交侧视图，不做四视图、动画、IK、Source retarget 或高质量渲染；
- **最终候选确认前必须正确恢复本地 CF 原生材质；灰模、mask-like DTX、Alpha/Specular 近似和外部 MOD texture 均不能通过 T02；**
- 最终身份仍必须经 T03 provenance + T04 Review，不能仅凭“看起来像”。

---

## 2. P5-T01 — 官方 CF 武器百科目标图确认

状态：**PASS / USER_REFERENCE_CONFIRMED**。

正式协议：[`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)。

已固定 evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

除非 evidence 损坏或用户明确否决，不重跑 T01。

---

## 3. 历史本地广召回 — LEGACY PRE-SCAN

此前 Luna 已经以旧 `P5-T01` 编号执行过一次本地 `data/**` 广召回。为避免重扫 16 万文件，该执行结果继续保留，但不再定义为当前 T01。

兼容说明：[`P5_LEGACY_PRE_SCAN.md`](P5_LEGACY_PRE_SCAN.md)。

历史输出：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

这些文件现在只是 **T02 candidate pool**；旧 score 不代表 identity confidence。

---

## 4. P5-T02 — 本地候选缩圈 + 原生材质恢复

状态：**ACTIVE / NATIVE_TEXTURE_RECOVERY_REQUIRED**。

正式协议：[`P5_T02_TASK_SPEC.md`](P5_T02_TASK_SPEC.md)。

已完成：

```text
confirmed official reference
  -> LEGACY PRE-SCAN reuse
  -> M4/M4A1 PLAYERVIEW narrowing
  -> exact SHA dedup
  -> geometry clusters
  -> C029/C103 finalist diagnostics
```

当前诊断结论不能完成 T02：

```text
C029/C103 gray geometry                  diagnostic_only
raw PV-M4A1_S_Transformers.DTX + UV      diagnostic_only
Alpha/Specular approximation             diagnostic_only
WeaponShader CFG raw-rgb-strip preview   not semantic decoding
```

当前必须继续：

```text
P4 material provenance audit
  -> native Transformers material inventory
  -> DTX decode/container cross-validation
  -> LTB material/texture binding recovery
  -> WeaponShader CFG binary analysis
  -> same-geometry skin differential analysis
  -> offline native shader hypotheses
  -> native material acceptance gate
  -> native-material finalist render
  -> user local-candidate confirmation
```

### 4.1 P4 provenance warning

P4 BornBeast/黑骑士 Prototype 的技术流水线可继续冻结，但其最终材质 fidelity 不能当作 native CF decoder evidence。

P4 build evidence 已显示 external source：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

被用于派生 Prototype base/self-illum texture。

因此 external CS1.6/网络 MOD 资源：

- 可以用于视觉参考/差分 control；
- **不得成为雷神最终材质输入；**
- 不得被标为 `local_cf`。

### 4.2 T02 native material hard gate

最终可辨识材质必须做到：

```text
LTB geometry/UV            local CF
visible color inputs       local CF / verified CFG constants
Alpha/Normal/Specular      local CF when used
lookup/detail/emissive     local CF when used
shader/material binding    evidence-backed
external pixels            NONE
reconstruction             reproducible
```

如果尚未满足，状态写：

```text
NATIVE_TEXTURE_RECOVERY_INCOMPLETE
```

这是继续执行状态，不允许跳过到 T03，也不要求用户仅凭灰模强选。

通过 native material gate 后才进入：

```text
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

用户确认后状态：

```text
USER_VISUAL_MATCH_CONFIRMED
```

仍不是最终 `IDENTITY_CONFIRMED`。

---

## 5. P5-T03 — Resource Graph / provenance closure

状态：`BLOCKED_BY_T02`。

T03 在 T02 已经完成“可辨识原生材质恢复”的前提下，对用户视觉确认的本地 candidate 建立完整资源图：

```text
PLAYERVIEW model LTB
  -> base/lookup/diffuse family
  -> Alpha / Normal / Specular / emissive / detail
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

T03 不得被用来补做 T02 本应完成的“最终可辨识 native material reconstruction”。

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

- 已完成 T01 evidence 的读取；
- T02 本地候选缩圈/去重；
- DTX/TGA/CFG/LTB material binding 的本地逆向；
- native material hypothesis 和可重复 render；
- 两个用户 Gate 的交互等待与继续执行；
- 证据产出；
- 不上传 `data/**`。

不得：

- 生成目标 reference 图；
- 凭文件名预锁候选；
- 用网络/CS1.6/MOD texture 作为最终材质；
- 仅凭灰模或 scalar approximation 通过 T02；
- 自行写最终 `IDENTITY_CONFIRMED`；
- 修改 P4 frozen conversion pipeline。

### Chat/Sol

负责：

- Task Spec / acceptance criteria；
- T03 provenance 审查；
- T04 最终 identity Review；
- 真正 BLOCKED/INVALID 时重新设计流程。

正常的 native texture hypothesis 失败不需要返回 Chat/Sol；记录 evidence 后继续下一条路线。
