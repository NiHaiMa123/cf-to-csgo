# P4_M01_N01_CONTINUATION.md — 69c03d review; current entry = evidence cleanup + true consumer search

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / N01_TARGETED_REWORK**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。`plan.md` 第 1 节仍保持 authoritative coarse state：P4-M01 尚未完成，P5-T02 继续暂停。若旧 continuation 与本文件冲突，以本文件为准。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
69c03d8769db2107cd94cae11accc750716466ae
P4-M01-N01: Fix scanner bug, lineage, and investigate binding key
```

该提交基于 Chat/Sol 对 `df48af65` 的 rework 指令，主要修改：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
scripts/material_recovery/n01_phase1_to_phase5_runner.py
work/m4a1_s_bornbeast/p4_m01_native_material/n01/**
```

并新增：

```text
n01/consumer_binding_investigation.json
```

本轮用户确认 executor benchmark：

```text
executor_model = Gemini 3.1 Pro
executor_harness = user-selected / unspecified
```

下一轮用户准备切换到 MiniMax。Task 仍保持 agent-agnostic；MiniMax 具体 model id 必须从实际 harness/runtime 记录，不要猜版本。

---

## 2. Chat/Sol 对 69c03d 的正式结论

```text
69c03d overall                         REWORK_REQUIRED
P4-M01-N01                             ACTIVE / N01_TARGETED_REWORK
Path B closure                         INCOMPLETE / NOT ACCEPTED
engine_binding_closure.status          OPEN_UNRESOLVED   <- ACCEPT
READY_FOR_NATIVE_MATERIAL_COMPOSITION  NOT ACCEPTED
P4-M01                                 ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P5-T02                                 PAUSED_BY_P4_M01
```

### 已接受

```text
extension normalization fix                    ACCEPT
Phase 2 -> Phase 3 CFG measured-data lineage   ACCEPT
BornBeast CFG = 492 bytes / phase 2 / 164       ACCEPT / OBSERVED
LTB parser does not expose short-id semantics   ACCEPT / REPO-CODE OBSERVATION
ObjExporter filename/path mirroring behavior    ACCEPT / TOOL_BEHAVIOR
final closure downgrade to OPEN_UNRESOLVED      ACCEPT
```

### 仍需 rework

```text
Phase 1 config-index hit generation             INVALID
.dat consumer hit accounting                    INVALID
CFG semantic grade / stale conclusion           REWORK
channel_semantics_report stale semantic claims  REWORK
stale Phase 4/5 generator code                  REWORK
true original CF consumer                       OPEN_UNRESOLVED
```

不要重跑已接受的 R1、N01 Phase 0、DTX/TGA formal work。

---

## 3. 确定性 bug：必须先修

### 3.1 `_ALL_ -> scanned` 字符串迭代 bug

当前 scanner 构建 index 时存在：

```python
config_index["_ALL_"].append((rel, "scanned"))
```

随后 `look_up_texture()` 把第二项当 texture iterable：

```python
for mk, textures in mappings:
    ...
    for t in textures:
```

于是字符串 `"scanned"` 被拆成字符，正式报告产生伪命中：

```text
_ALL_ -> s
_ALL_ -> c
_ALL_ -> a
_ALL_ -> n
_ALL_ -> e
_ALL_ -> d
```

修复要求：

```text
- config_index 只存真实 parsed mapping objects；
- “file was scanned/indexed” metadata 放独立统计结构，不得混入 mapping values；
- 为 look_up_texture 加 schema/type guard；字符串不能被当 texture list；
- 增加 regression assert：四个 target 不得出现 1-char texture ref；
- 重新生成 consumer_candidate_matrix.json / consumer_search_report.md。
```

### 3.2 raw grep / `.dat` hit scope 混淆

当前 scanner 把：

```text
.cfg/.ini/.txt/.dat/.lta
```

全部命中混入同一个 `raw_grep_hits[target]`，随后又把其总数写成：

```text
LithTechDatTextureReferenceIndex BornBeast_hit_count
```

导致 `out/*.txt` 等 derived reports 被错误计入 `.dat` consumer hit。

修复要求：

```text
hits_by_extension
hits_by_resource_family
hits_by_consumer
```

必须分开计数。

同时：

```text
data/out/**
work/**
历史 generated reports
```

不得作为“原始 CF resource consumer hit”证据。可以单独记录为 `DERIVED_OUTPUT_HIT`，但不能支持 native binding。

每个 scoped negative/hit 必须带：

```text
scan root
include extensions
exclude paths
files scanned
files decoded
hit count
hit paths
```

---

## 4. CFG evidence boundary：本轮必须清理干净

69c03d 已修正 measured values，但 `cfg_consumer_report.json` 仍保留旧 semantic overclaim，例如：

```text
H-CFG-A = DIFFERENTIAL_SUPPORTED 1D Color/Intensity LUT
WeaponShader CFGs function as binary shader parameter/LUT strips
CFG -> Source1 Phong exponent / boost / selfillum tint
```

并存在 stale prose：BlueDiamond 实测 `sample_count=166`，旧文字仍说与 BornBeast 同为 `164`。

本轮固定 evidence grade：

```text
237/237 single-mod3 structural form     STRUCTURALLY_VERIFIED
per-file phase/count/sample sequence    OBSERVED
cross-skin sequence/count differences   DIFFERENTIAL_SUPPORTED
CFG = 1D LUT                            HYPOTHESIS
CFG = packed shader constants           HYPOTHESIS
CFG -> Phong exponent/boost             SOURCE1_DESIGN_CANDIDATE
CFG -> selfillum tint                   SOURCE1_DESIGN_CANDIDATE
```

除非找到真实 consumer/reference contract，不得升级 LUT/parameter semantics。

要求：

```text
- 清除所有 stale 164/phase/value prose；
- conclusion 只能说 binary single-phase mod-3 structure verified，semantic consumer unresolved；
- Source1 映射必须放 conversion-design namespace/section，不得写成 recovered CF fact。
```

---

## 5. Phase 4/5 stale outputs 与 generator 必须消毒

当前 `channel_semantics_report.json` 仍含旧的未证明声明：

```text
AlphaMap = transparency + emissive glow mask
SpecularMap = gloss/roughness map
WeaponShader CFG = shader parameter & color LUT profile
CFG -> phongboost/phongexponent/selfillum
```

这些不能继续作为 recovered native CF semantics。

本轮要求：

```text
Layer A: storage/container facts
Layer B: naming/directory/resource-role hypotheses
Layer C: Source1 conversion design candidates
```

三层严格分开，每条 Layer B/C 给 evidence grade。

另外 `n01_phase1_to_phase5_runner.py` 中旧 `run_phase4_channel_semantics()` / `run_phase5_engine_binding_closure()` 仍能生成过时的：

```text
READY_FOR_NATIVE_MATERIAL_COMPOSITION
```

即使当前 `main()` 不调用，也属于 future regression hazard。

必须二选一：

```text
A. 删除/禁用旧 generator；
B. 重写为只生成当前 OPEN_UNRESOLVED + hypothesis-graded report。
```

必须增加 regression guard：任何 N01 runner 在没有 direct/accepted Path-B evidence 时，不得输出 `READY_FOR_NATIVE_MATERIAL_COMPOSITION`。

---

## 6. 已经得到的关键结论：不要再绕 repo exporter

当前 repo behavior 已足够明确：

```text
LTB post_mesh_short_id exists structurally
-> current C# LithTechModelDecoder does not expose/use it as material binding
-> current LithTechObjExporter falls back to model/source filename/path candidates
-> Models/... -> ModelTextures/... mirroring is repo/tool behavior
```

因此下一轮不得再把 `LithTechObjExporter` 当成“CF 原游戏 engine consumer”的证明。

当前真正缺失的一跳仍是：

```text
original CF runtime/resource system:
post_mesh_short_id / piece identity
-> material/shader binding
-> texture family
-> WeaponShader CFG semantic consumer
```

---

## 7. MiniMax 下一轮执行顺序

### Step A — deterministic cleanup（必须完成）

1. 修 `_ALL_ -> scanned` schema bug；
2. 修 raw grep / `.dat` scope accounting；
3. 排除或单列 derived outputs；
4. 重新生成 Phase 1 matrix/report；
5. 清理 CFG semantic grades + stale prose；
6. 清理 `channel_semantics_report.json`；
7. 删除/重写 stale Phase 4/5 false-PASS generator；
8. 加 regression assertions。

这一步完成后，旧 69c03d 中以下 evidence 仍保留：

```text
CFG measured metrics
LTB short field structural observation
repo parser non-consumption observation
repo exporter mirroring observation
ArmModel positive control
237/237 CFG structural fact
OPEN_UNRESOLVED closure
```

### Step B — substantive search：找 repo 之外的真实 consumer

先判断本地可访问 corpus 是否包含 CF client/runtime 静态文件，例如：

```text
.exe / .dll / engine modules
shader packages
material/resource tables
other config/index bundles
```

只做**静态、只读、bounded**搜索；不要运行未知客户端二进制。

优先 needles：

```text
WeaponShader
AlphaMap
NormalMap
SpecularMap
PieceIndex
ModelTextures/Shader
PLAYERVIEW
PV-M4A1_S_BornBeast
```

ASCII + UTF-16LE 都检查。若命中 native binary：

```text
record file path / SHA256 / size
PE/module identity if applicable
needle encoding
raw offset / RVA when derivable
nearby strings / resource names
cross-reference candidate only if tooling truly derives it
```

若本地已有反汇编/静态分析工具，可进一步做 bounded xref/call-chain tracing；没有就不要伪造“consumer”。

目标是寻找：

```text
resource/path string
-> lookup/index/resolver candidate
-> material/shader structure
-> piece/material key use
```

如果 corpus 根本没有 client/runtime binaries，也要明确：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

而不是继续从 repo heuristic 推断 engine semantics。

### Step C — handoff boundary

本轮允许三种结果：

```text
DIRECT_CONSUMER_CANDIDATE_FOUND
OPEN_UNRESOLVED / NEGATIVE_RESULT_SCOPED
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

不得为了结束任务强行输出 PASS。

---

## 8. 必需输出

至少更新：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
scripts/material_recovery/n01_phase1_to_phase5_runner.py
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
work/m4a1_s_bornbeast/p4_m01_native_material/n01/cfg_consumer_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/channel_semantics_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/engine_binding_closure.json
```

若执行 Step B，新增一个独立、可审计报告，例如：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json
```

报告必须记录 scan scope 与 provenance，不上传 raw `data/**`。

---

## 9. Git / safety / provenance

继续严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no destructive reset/clean
no force push
no raw local CF assets
```

每个 local-only input/evidence 至少记录：

```text
relative_path
sha256
size
scan/tool version
run timestamp/run_id where applicable
```

新窗口启动先执行：

```bash
git status --short --branch
git fetch origin
git pull --rebase origin master
```

若 tracked worktree 有未完成修改，按 `AGENTS.md` 停止自动同步并保护本地工作。

---

## 10. 当前状态 / 下次 Review 起点

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / N01_TARGETED_REWORK
P5-T02             PAUSED_BY_P4_M01
```

下一次 Chat/Sol Review：

```text
base = 69c03d8769db2107cd94cae11accc750716466ae
review only commits after this base
```

不要重新执行 Phase 0，不要恢复 P5-T02，不要自行把 P4-M01/N01 标 PASS。