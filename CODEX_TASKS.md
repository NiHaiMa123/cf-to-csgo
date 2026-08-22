# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给任何用户选择的、具备本地执行能力的 Agent 使用；Task 不绑定具体模型。
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> Planner / Reviewer = **Chat/Sol**；Local Executor = 用户当前选择的本地执行 Agent。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / PHASE1_CONSUMER_DISCOVERY   <- CURRENT
P5-T01             PASS / USER_REFERENCE_CONFIRMED
P5-T02             PAUSED_BY_P4_M01
P5-T03/T04         BLOCKED
```

当前协议：

```text
P4_M01_TASK_SPEC.md                         parent contract
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md     N01 original technical route
P4_M01_N01_CONTINUATION.md                  CURRENT direct execution / Review overlay
```

R1 文件仅作历史 evidence，不是当前执行入口。

---

## 2. 当前 executor benchmark context

用户当前准备切换执行模型：

```text
Model: MiniMax M3
Harness: unspecified / user-selected
```

这只是 benchmark/provenance，不改变 Task acceptance criteria。

若报告中记录 executor：

```text
executor_model = MiniMax M3
executor_harness = <actual harness if known; otherwise unspecified>
```

禁止从 commit footer 推断执行模型；不要复制历史错误 footer：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

---

## 3. 每次启动顺序

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
P4_M01_N01_CONTINUATION.md   <- CURRENT direct entry
```

5. 需要 predecessor evidence 时再读：

```text
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
scripts/material_recovery/r1_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/r1/**
```

6. **不要执行 N01 Phase 0；它已 Chat/Sol ACCEPT / FROZEN。**

---

## 4. 最新 Review 基线

最新执行提交：

```text
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19
```

Chat/Sol Review：

```text
N01 Phase 0 technical result   ACCEPT / FROZEN
N01 execution completeness     INCOMPLETE / STOPPED_EARLY
```

已接受：

```text
CFG phase-origin span accounting
DTX measured-margin / 1043-of-1046 wording
H1 preview path + evidence downgrade
shader stale BGR24/scalar cleanup
binding negative-scope cleanup
```

因此：

```text
P4-M01-R1 = ACCEPTED / COMPLETE
```

下一位 Executor 直接从 N01 Phase 1 开始。

---

## 5. 当前角色

Local Executor = **engine material consumer / binding reverse executor + evidence producer**。

当前必须：

- 沿 repo 现有 decoder/index/mapping/resolver 找真实 consumer/data path；
- 用 ArmModel explicit material CFG 作为 positive control，不直接套用 weapon；
- 做 BornBeast / Transformers / Jewelry / 简单 control same-family differential；
- 找 piece/material key → texture family → WeaponShader/material resource role；
- 区分 storage order、binding role、shader composition semantics；
- 保存 raw key/offset/value/path/hash、candidate/rejection/scoped negative；
- push scoped code/evidence 到 `master`。

不得：

- 重跑 N01 Phase 0；
- 重跑已接受 TGA formal repair；
- 重跑 DTX formal header/LZMA/width scan；
- 再把 CFG mod-3 phase 当 record boundary；
- basename convention = binding；
- 为得到 PASS 无边界扫描整个 `data/**`；
- external texture 进入 final pixels；
- diagnostic preview = engine semantics；
- 修改 frozen skeleton/sequence/runtime contract；
- 自行恢复 P5-T02；
- 自行把 `plan.md` 改 P4-M01 PASS。

---

## 6. 当前固定执行顺序

### Phase 1 — consumer call/data-path discovery

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

要求找真实调用/数据关系：

```text
producer/index/table
-> key / model / piece identifier
-> resolver/lookup
-> texture/material resource
-> consumer
```

输出：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
```

### Phase 2 — positive control + weapon differential

至少：

```text
BornBeast
Transformers
Jewelry
+ 1 simple/traditional M4A1-S control if locally available
```

输出：

```text
n01/weapon_material_differential.json
```

**本轮最低 handoff：Phase 1 + Phase 2 必须都完成。不要只生成 candidate list 就停止。**

### Phase 3–5

若 Phase 1/2 已产生 credible consumer candidate，继续：

```text
Phase 3 WeaponShader CFG consumer
Phase 4 storage/channel/binding semantics
Phase 5 engine binding closure
```

输出：

```text
n01/cfg_consumer_report.json
n01/channel_semantics_report.json
n01/engine_binding_closure.json
```

若 direct consumer 暂未找到，保存 bounded negative/rejection evidence，完成 Phase 2 后明确 continuation point；不得用 basename/length-fit 强行 closure。

---

## 7. Evidence policy

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

仅 basename、视觉相似、长度 fit、单一 correlation 不足以 PASS。

---

## 8. 已接受 baseline — 不要重跑

```text
R1 correction                           ACCEPTED / COMPLETE
N01 Phase 0                             ACCEPT / FROZEN
TGA formal repair                       ACCEPT / STRUCTURAL
DTX no formal LithTech header           VERIFIED_STRUCTURAL
DTX not LZMA                            VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodicity       VERIFIED_STRUCTURAL
DTX committed width scan                ACCEPT
DTX two-varying-offset continuity       ACCEPT
DTX 1043/1046 dominant statistic        ACCEPT
DTX 1024/no-mips                        STRONG_HYPOTHESIS
CFG 237/237 mod-3 structural fact       VERIFIED_STRUCTURAL
CFG phase-vs-boundary correction        ACCEPT
CFG 164/169/214 extraction              ACCEPT
CFG phase-origin formula cleanup        ACCEPT
H1 path/evidence cleanup                ACCEPT
H2 pixel-index fix                      ACCEPT / DIAGNOSTIC_ONLY
ArmModel [Textures]/PieceIndex format   VERIFIED_STRUCTURAL
355-file config-like negative scope     NEGATIVE_RESULT_SCOPED
```

仍 open：

```text
weapon material consumer
weapon short-field meaning
weapon piece/material -> texture-set binding
WeaponShader CFG consumer/semantic
DTX/TGA binding/channel semantics
DTX tail semantics
native composition closure
```

---

## 9. Git / data

- handoff 只认 `master`；
- `data/**` 永远 local-only；
- push 前精确 `git add -- <paths>`；
- 禁止 `git add .` / `-A` / `--all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不上传 raw LTB/DTX/TGA/CFG；
- 不删除历史 evidence 隐藏错误；
- 新报告保持 supersedes/provenance 链。

---

## 10. Handoff

N01 完成后 Local Executor 只提交 scoped code/evidence + recommended state；Chat/Sol 决定 N01 是否 PASS。

N01 PASS 只允许进入 P4-M01 native composition/final closure，不自动恢复 P5。

只有最终：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 P5-T02。