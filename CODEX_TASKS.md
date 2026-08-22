# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给任何用户选择的、具备本地执行能力的 Agent 使用；不绑定具体模型。
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> Planner / Reviewer = **Chat/Sol**；Local Executor = 用户当前选择的本地执行 Agent。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01
P4-M01-N01    ACTIVE / ENGINE_BINDING_INVESTIGATION   <- CURRENT
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03/T04    BLOCKED
```

当前协议：

```text
P4_M01_TASK_SPEC.md                         parent contract
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md     CURRENT direct execution spec
P4_M01_R1_CONTINUATION.md                   predecessor/final R1 Review only
```

R1 不再是当前 substantive task。

---

## 2. 每次启动顺序

1. `git status --short --branch`；
2. 确认当前分支 `master`；
3. tracked worktree 可安全同步时：

```bash
git fetch origin
git pull --rebase origin master
```

4. 读取：

```text
AGENTS.md
plan.md 第 1 节
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md
```

5. 只在需要理解 predecessor evidence 时读取：

```text
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
scripts/material_recovery/r1_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/r1/**
```

6. 不从 A/B/C/D/F 全量重跑。

---

## 3. 当前角色

Local Executor = **engine material consumer / binding reverse executor + evidence producer**。

负责：

- 先完成 N01 Phase 0 的 R1 minor consistency cleanup；
- Phase 0 self-check 通过后，**同一轮直接进入 Phase 1，不等待 Chat/Sol 再切状态**；
- 沿现有 decoder/index/mapping/resolver 与本地 resource relation 定位真实 consumer；
- 用 ArmModel material CFG 作为 positive control，不直接套用 weapon；
- 做 BornBeast / Transformers / Jewelry / 简单 control 的 same-family differential；
- 寻找 piece/material key → texture set → WeaponShader CFG/resource role 的 evidence；
- 区分 storage byte order、map binding role、shader composition semantics；
- 保存 raw offset/value/hash/path、consumer candidate、negative evidence、rejection evidence；
- push scoped code/evidence 到 `master`。

不得：

- 重跑已接受的 TGA formal repair；
- 重跑 DTX formal header/LZMA/width scan；
- 再把 CFG mod-3 phase 当 record boundary；
- 用 basename convention 直接证明 binding；
- 为得到 PASS 无边界扫描整个 `data/**`；
- 把 external texture 作为 final pixels；
- 把 diagnostic preview 当 engine semantics；
- 修改 P4 frozen skeleton/sequence/runtime contract；
- 自行恢复 P5-T02；
- 自行把 `plan.md` 改成 P4-M01 PASS。

---

## 4. N01 Phase 0 — 只做 final consistency cleanup

必须先修：

```text
CFG phase-origin identity formula
DTX >3x / stale every wording
H1 preview path + SHA consistency
H1 evidence class downgrade
shader stale BGR24/scalar-strip comments
binding stale full-local-data comments
```

CFG sample count `164/169/214` 已正确，不要退回旧 extraction。

Phase 0 gate：

```text
formula arithmetic self-consistent
path exists and SHA matches
comments == report evidence grade
no universal/exact-framing stale claim
open item remains open
```

然后直接进入 Phase 1。

---

## 5. N01 substantive route

固定顺序：

```text
Phase 1  consumer call/data-path discovery
Phase 2  ArmModel positive control + weapon-family differential
Phase 3  WeaponShader CFG consumer identification
Phase 4  storage/channel/binding semantics
Phase 5  engine binding closure
```

优先利用：

```text
LithTechModelTextureConfigIndex.cs
LithTechTextureMappingScanner.cs
LithTechDatTextureReferenceIndex.cs
TextureReferenceResolver.cs
LithTechModelTextureLoader.cs
LithTechModelDecoder.cs
CfgTextDecoder.cs
CfgBinaryStripDecoder.cs
```

重点是找到真实调用/数据关系，不是把类名写进报告。

输出优先：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
work/m4a1_s_bornbeast/p4_m01_native_material/n01/weapon_material_differential.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/cfg_consumer_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/channel_semantics_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/engine_binding_closure.json
```

---

## 6. Evidence policy

优先级：

```text
engine/resource consumer evidence
> structural binding
> same-family differential
> bounded binary hypothesis
> preview appearance
```

允许状态：

```text
OBSERVED
STRUCTURALLY_VERIFIED
DIFFERENTIAL_SUPPORTED
SEMANTICALLY_VERIFIED
PROVISIONAL
HYPOTHESIS
NEGATIVE_RESULT_SCOPED
OPEN_UNRESOLVED
```

仅 basename、视觉相似、长度 fit、单一相关性不能升级为 binding PASS。

---

## 7. 已接受 baseline，不要重跑

```text
A provenance audit
R1-D formal TGA repair
DTX formal -2/-3/-5 route
DTX not-LZMA
DTX whole-file 3-byte periodicity
DTX committed width scan
DTX 1043/1046 dominant statistic
CFG 237/237 single-phase mod-3 structural fact
CFG phase-vs-boundary correction
CFG 164/169/214 complete phase samples
H2 pixel-index fix
ArmModel [Textures]/PieceIndex positive control
355-file config-like negative scope definition
G variant inventory/differential evidence
```

仍 open：

```text
weapon material consumer
weapon piece/material -> texture-set binding
WeaponShader CFG consumer/semantic
DTX/TGA channel/binding semantics
DTX tail semantics
native composition closure
```

---

## 8. Git / data

- Agent handoff 只认 `master`；
- `data/**` 永远 local-only；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `-A` / `--all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不上传原始 LTB/DTX/TGA/CFG；
- 不删除历史 evidence 隐藏错误；
- 新报告保持 supersedes/provenance 链。

---

## 9. Handoff

N01 完成后 Local Executor 只提交：

```text
corrected Phase-0 evidence
N01 consumer/binding code + reports
recommended state
```

Chat/Sol 决定 N01 是否 PASS，以及是否进入 P4-M01 native composition/final closure。

只有最终：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 P5-T02。