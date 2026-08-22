# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给任何用户选择的、具备本地执行能力的 Agent 使用；Task 不绑定具体模型。
>
> 项目 coarse progress/status 以 [`plan.md`](plan.md) 第 1 节为准；当前直接执行细节以 [`P4_M01_N01_CONTINUATION.md`](P4_M01_N01_CONTINUATION.md) 为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
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
P4-M01-N01         ACTIVE / FINAL_DOCUMENTATION_CLEANUP   <- CURRENT
N01 substantive    BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P5-T01             PASS / USER_REFERENCE_CONFIRMED
P5-T02             PAUSED_BY_P4_M01
P5-T03/T04         BLOCKED
```

当前协议：

```text
P4_M01_TASK_SPEC.md                         parent contract
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md     original N01 acceptance/evidence rules
P4_M01_N01_CONTINUATION.md                  CURRENT direct execution / Review overlay
```

---

## 2. 最新 Review baseline

最新已 Review Local Executor 提交：

```text
46fcacebbc631fc05e0d491470b5e5482bca4533
P4-M01-N01: minor evidence cleanup - M1 JSON validity, M2 scope counters, M3 executor provenance
```

Chat/Sol verdict：

```text
46fcace technical cleanup                 ACCEPT
M1 JSON validity                          ACCEPT
M2 scope/count correction                 ACCEPT
M3 current-run provenance                 ACCEPT
N01 substantive result                    BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P4-M01-N01 PASS                           NO
```

下一次 Review 只看 `46fcace` 之后的 final-cleanup 提交。

---

## 3. 启动顺序

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
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md
P4_M01_N01_CONTINUATION.md   <- CURRENT direct entry
```

5. **不要重跑 N01 Phase 0 / Phase 1–5，不要重新扫描同一 repo/data corpus。**

---

## 4. 当前唯一任务：Final Documentation / Provenance Cleanup

### F1 — 通用 generator provenance 参数化

当前 `46fcace` 报告中的：

```text
executor_model = MiniMax-M3
executor_harness = Claude Code
```

对本轮历史 evidence 是正确的。

但通用 generator 不能把 MiniMax-M3/Claude Code 写死。至少检查：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
scripts/material_recovery/n01_phase1_to_phase5_runner.py
```

改成运行时参数或环境变量，例如：

```text
--executor-model / N01_EXECUTOR_MODEL
--executor-harness / N01_EXECUTOR_HARNESS
--executor-family / N01_EXECUTOR_FAMILY
```

没有输入时必须：

```text
unspecified
```

禁止默认伪造某一模型身份。

必须继续写：

```text
commit_footer_model_provenance = NON_AUTHORITATIVE
```

不要修改历史 commit footer；不要用 `Co-Authored-By: Claude Opus ...` 推断 executor。

### F2 — engine-binding closure 文案与 blocker 对齐

修：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/engine_binding_closure.json
```

不得再写成原 CF runtime 已被证明使用 directory mirroring。

当前接受的事实只有：

```text
repo exporter performs deterministic Models/... -> ModelTextures/... mirroring
= TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
```

原 CF runtime binding：

```text
OPEN_UNRESOLVED
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

同时把 stale：

```text
next_step = Awaiting Chat/Sol review for N01 Phase 1-3 findings
```

替换为：

```text
next_step = blocked pending a new original CF runtime/client artifact or equivalent documented consumer contract
```

`engine_binding_closure.status` 必须保持：

```text
OPEN_UNRESOLVED
```

### F3 — 推荐 regression guard

让：

```text
config_candidates_decoded
```

严格是：

```text
config_candidates_seen
```

的子集；建议增加：

```python
assert config_candidates_decoded <= config_candidates_seen
```

该项不改变已接受的 261 / 18 本轮 evidence。

---

## 5. 不得破坏的已接受结果

必须保持：

```text
BornBeast/Transformers/Jewelry/BlueDiamond text-config hits = 0
.dat consumer hits = 0
BornBeast derived-output hits = 4, DERIVED_OUTPUT_HIT only
CFG BornBeast = phase 2 / 164
CFG Transformers = phase 1 / 169
CFG Jewelry = phase 2 / 214
CFG BlueDiamond = phase 2 / 166
CFG semantic consumer = OPEN_UNRESOLVED
Layer B map roles = HYPOTHESIS
Source 1 mapping = SOURCE1_DESIGN_CANDIDATE
engine_binding_closure.status = OPEN_UNRESOLVED
N01 substantive = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

不得出现：

```text
READY_FOR_NATIVE_MATERIAL_COMPOSITION
P4-M01-N01 PASS
P4-M01 PASS
P5-T02 resumed
original CF runtime mirroring = verified
```

---

## 6. Final-cleanup handoff

F1/F2 完成后：

```text
N01 evidence cleanup = COMPLETE / FROZEN
N01 substantive = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

commit + push scoped changes 到 `master`，然后停止。

没有新的 CF runtime/client artifact 时，禁止：

```text
再次扫描当前 repo/data
再次曲线拟合 CFG 试图升级 semantic
把 ObjExporter heuristic 当 runtime proof
创建新的 N01 Phase 1–5 run
恢复 P5-T02
```

---

## 7. Blocker 解除后才允许继续

只有出现新输入才重新打开 substantive reverse：

```text
CF client .exe
engine/render/resource DLL/module
original runtime bundle
shader/runtime package
可靠 documented material/piece binding contract
```

新路线：

```text
strings/resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

只做静态、只读分析；不执行未知 binary；不上传 raw binary/data/**。

---

## 8. Git / data discipline

严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no force push
no destructive reset/clean
no raw CF assets/runtime binaries
```

提交前至少：

```bash
git status
git diff --cached --name-only
```

只 stage F1/F2/F3 明确需要的 tracked script/report/evidence。

---

## 9. Handoff / next Review

下一次 Chat/Sol Review：

```text
base = 46fcacebbc631fc05e0d491470b5e5482bca4533
```

F1/F2 接受后，当前 corpus 的 N01 work 冻结，等待新增 runtime artifact。