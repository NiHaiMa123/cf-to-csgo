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
P4-M01-N01         ACTIVE / MINOR_EVIDENCE_CLEANUP   <- CURRENT
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

最新已 Review 的 Local Executor 提交：

```text
ea11ba143d859193213f24ab92248ff8a576b135
P4-M01-N01: targeted rework - deterministic cleanup + runtime consumer search
```

Chat/Sol verdict：

```text
ea11ba1 technical result                  ACCEPT_WITH_MINOR_EVIDENCE_CLEANUP
schema / derived-hit / scope cleanup      ACCEPT
CFG semantic downgrade                    ACCEPT
channel Layer A/B/C split                 ACCEPT
false-PASS generator protection           ACCEPT
runtime consumer search methodology       ACCEPT
substantive result                        BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P4-M01-N01 PASS                            NO
```

下一次 Review 只看 `ea11ba1` 之后的 minor-cleanup 提交。

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

5. **不要重跑 N01 Phase 0 / Phase 1–5。**

---

## 4. 当前唯一任务：三项 Minor Evidence Cleanup

### M1 — JSON 合法性

修：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json
```

当前 `rationale` 使用 Python 风格：

```text
"rationale": (
  "..."
  "..."
)
```

必须改成合法标准 JSON string，不改变：

```text
handoff_status = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

并用标准 JSON parser 验证至少：

```text
consumer_candidate_matrix.json
weapon_material_differential.json
cfg_consumer_report.json
channel_semantics_report.json
engine_binding_closure.json
runtime_consumer_search.json
```

### M2 — scan-count 口径/标签

当前 `n01_phase1_consumer_search.py` 的 `files_scanned` 在 config extension 判定前增加，因此报告中的：

```text
config files scanned (post-low-value filter): 102382
```

标签不准确。

修法二选一：

```text
A. 保留当前计数，改成 all_non_low_value_files_seen 等准确名称；
B. 把 config candidate count 与 all files seen 分成两个独立计数。
```

最终至少明确：

```text
all files seen scope
config candidate/decode scope
raw needle scope = 355 files
```

每个 count 必须能由代码机械复现。

### M3 — executor provenance

最新用户确认 executor family 为 MiniMax，harness 为 Claude Code；精确 model id 若 runtime 未显示就写 `unspecified`。

禁止从：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

推断实际 executor。

报告规则：

```text
executor_model = <runtime value or unspecified>
executor_harness = Claude Code (when applicable)
commit_footer_model_provenance = NON_AUTHORITATIVE
```

不要改写历史 commit footer。

---

## 5. Minor cleanup 不得破坏的已接受结果

必须保持：

```text
BornBeast/Transformers/Jewelry/BlueDiamond text-config hits = 0
.dat consumer hits = 0
BornBeast derived output hits = 4, DERIVED_OUTPUT_HIT only
CFG BornBeast = phase 2 / 164
CFG Transformers = phase 1 / 169
CFG Jewelry = phase 2 / 214
CFG BlueDiamond = phase 2 / 166
CFG semantic consumer = OPEN_UNRESOLVED
Layer B map roles = HYPOTHESIS
Source 1 mapping = SOURCE1_DESIGN_CANDIDATE
engine_binding_closure = OPEN_UNRESOLVED
```

不得出现：

```text
READY_FOR_NATIVE_MATERIAL_COMPOSITION
P4-M01-N01 PASS
P4-M01 PASS
P5-T02 resumed
```

---

## 6. 当前 substantive blocker

本地现有 `data/` corpus 已做 bounded 静态搜索，没有发现：

```text
CF client executable
engine/runtime DLL/module
REZ/runtime archive
compiled shader package
weapon material/resource table
```

因此真实 CF consumer 当前无法继续闭合：

```text
post_mesh_short_id / piece identity
-> engine material/shader resolver
-> texture family
-> WeaponShader CFG semantic consumer
```

正式状态：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

**没有新增 runtime artifact 时，不得再次扫描同一 repo/data corpus 作为新 substantive task。**

---

## 7. Blocker 解除后才允许的新方向

只有用户后续提供或本地出现新的原始 CF runtime/client artifact 时，才重新开启 consumer reverse。

可接受目标：

```text
.exe / .dll / engine module
runtime/resource bundle
shader/runtime package
可靠的 material/piece binding contract 文档
```

只做静态、只读分析，不执行未知 binary，不上传 binary/raw `data/**`。

新分析路线固定为：

```text
strings/resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

不得回退到 basename heuristic 作为 engine proof。

---

## 8. Git / data discipline

严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no force push
no destructive reset/clean
no raw LTB/DTX/TGA/CFG/runtime binaries
```

提交前至少：

```bash
git status
git diff --cached --name-only
```

只 stage M1–M3 需要的 tracked script/report/evidence。

---

## 9. Handoff

M1–M3 完成后：

```text
N01 evidence cleanup = COMPLETE
N01 substantive state = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

commit + push 到 `master` 后停止。

Chat/Sol 下一次 Review：

```text
base = ea11ba143d859193213f24ab92248ff8a576b135
```

除非新增 runtime artifact，否则不要创建新的 N01 substantive scan/run。