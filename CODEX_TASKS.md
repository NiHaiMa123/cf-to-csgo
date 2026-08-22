# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给任何用户选择的、具备本地执行能力的 Agent 使用；Task 不绑定具体模型。
>
> 项目 authoritative coarse progress/status 以 [`plan.md`](plan.md) 第 1 节为准；当前直接执行细节以 [`P4_M01_N01_CONTINUATION.md`](P4_M01_N01_CONTINUATION.md) 为准；Git/data 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
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
P4-M01-N01         ACTIVE / N01_TARGETED_REWORK   <- CURRENT
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
69c03d8769db2107cd94cae11accc750716466ae
P4-M01-N01: Fix scanner bug, lineage, and investigate binding key
```

Chat/Sol verdict：

```text
69c03d overall                         REWORK_REQUIRED
extension normalization                ACCEPT
Phase2 -> Phase3 CFG lineage            ACCEPT
repo LTB short-id non-consumption       ACCEPT / CODE OBSERVATION
repo ObjExporter mirroring              ACCEPT / TOOL_BEHAVIOR
engine_binding_closure OPEN_UNRESOLVED  ACCEPT
P4-M01-N01 PASS                         NO
```

下一次 Review 只看 `69c03d` 之后的新提交。

---

## 3. 当前 executor benchmark context

用户准备在新的 Claude Code 窗口中切换到 MiniMax 再执行一轮。

```text
Model: MiniMax
Exact model id: MUST record from actual harness/runtime; do not guess
Harness: Claude Code / user-selected local execution environment
```

该信息只用于 benchmark/provenance，不改变 Task acceptance criteria。

报告若记录 executor：

```text
executor_model = <actual exact model id shown by harness>
executor_harness = Claude Code
```

禁止根据历史 commit footer 推断模型。

---

## 4. 每次启动顺序

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

5. 不要执行 N01 Phase 0；它已 `ACCEPT / FROZEN`。

---

## 5. 当前唯一任务：N01 targeted rework

本轮不是重新跑 Phase 1–5，而是：

```text
A. 修 69c03d 仍存在的 deterministic evidence bugs
B. 清理 CFG/channel semantic overclaim
C. 消毒 stale false-PASS generator
D. 若本地存在 CF client/runtime 静态文件，转向真实 runtime consumer 搜索
```

详细要求全部在 `P4_M01_N01_CONTINUATION.md`。

### A. 必修 deterministic bugs

#### config-index schema bug

不得再出现：

```text
_ALL_ -> s/c/a/n/e/d
```

原因是 `"scanned"` 被错误当 texture iterable。必须把 scan metadata 与 parsed mappings 分离，并加 regression guard。

#### raw grep / `.dat` scope bug

不得把 `.txt/.cfg/.lta/.dat` 的总 hits 写成 `.dat consumer hits`。

必须分：

```text
hits_by_extension
hits_by_resource_family
hits_by_consumer
```

`data/out/**`、`work/**`、generated reports 不能作为原始 CF native consumer evidence。

### B. CFG semantic cleanup

保留：

```text
237/237 single-mod3 form                 STRUCTURALLY_VERIFIED
per-file phase/count/sample sequence      OBSERVED
cross-skin measured differences           DIFFERENTIAL_SUPPORTED
```

保持假说：

```text
CFG = 1D LUT                              HYPOTHESIS
CFG = packed constants                    HYPOTHESIS
CFG -> Phong/selfillum mapping            SOURCE1_DESIGN_CANDIDATE
```

没有真实 consumer/reference contract 不得 semantic upgrade。

### C. stale Phase 4/5 generator cleanup

`n01_phase1_to_phase5_runner.py` 不得保留一个可再次生成：

```text
READY_FOR_NATIVE_MATERIAL_COMPOSITION
```

的旧路径。

必须删除、禁用或重写为当前 hypothesis-graded / OPEN_UNRESOLVED behavior。

---

## 6. Substantive next direction：真实 CF runtime consumer

当前 repo 已经证明的是“我们的工具怎么做”，不是“CF 原客户端怎么做”：

```text
LTB short field exists
current C# parser does not expose/use it
current ObjExporter uses source filename/path mirroring
```

下一步若要继续闭合原生绑定，优先检查本地 corpus 是否存在：

```text
CF client .exe/.dll/engine modules
shader packages
material/resource tables
other runtime index/config bundles
```

只做静态、只读、bounded 搜索；不要执行未知客户端二进制。

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

ASCII 与 UTF-16LE 都检查。

若命中 native binary/resource，至少记录：

```text
relative path
SHA256
size
module/file identity
needle + encoding
offset/RVA if derivable
nearby resource/path strings
actual xref/call-chain only when tooling truly derives it
```

若本地根本没有 runtime artifacts，明确：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

不得退回用 basename heuristic 冒充 engine consumer。

---

## 7. 本轮允许的 handoff result

```text
DIRECT_CONSUMER_CANDIDATE_FOUND
OPEN_UNRESOLVED / NEGATIVE_RESULT_SCOPED
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

Local Executor 不得自行给：

```text
P4-M01-N01 PASS
READY_FOR_NATIVE_MATERIAL_COMPOSITION
P4-M01 PASS
P5-T02 resumed
```

这些只能由 Chat/Sol Review 在 evidence 满足既有 criteria 后决定。

---

## 8. 已接受 baseline — 不要重跑

```text
P4 baseline                              PASS / FROZEN
R1 correction                            ACCEPTED / COMPLETE
N01 Phase 0                              ACCEPT / FROZEN
TGA formal repair                        ACCEPT
DTX no formal header / not LZMA          VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodicity        VERIFIED_STRUCTURAL
DTX 1024 stride                          STRONG_HYPOTHESIS
DTX 1043/1046 statistic                  VERIFIED_CORPUS_STATISTIC
CFG 237/237 mod-3 structure              VERIFIED_STRUCTURAL
ArmModel [Textures]/PieceIndex format    VERIFIED_STRUCTURAL
69c03d CFG measured-data lineage         ACCEPT
69c03d repo parser short-id observation  ACCEPT
69c03d ObjExporter mirroring observation ACCEPT / TOOL_BEHAVIOR
```

仍 open：

```text
original CF weapon material consumer
post_mesh_short_id semantic meaning
piece/material -> texture-set binding
WeaponShader CFG semantic consumer
DTX/TGA native shader roles
DTX tail semantics
native composition closure
```

---

## 9. Git / data discipline

严格遵守 `AGENTS.md`：

- handoff 只认 `master`；
- `data/**` 永远 local-only；
- 禁止 `git add .` / `-A` / `--all`；
- 不 force-push；
- 不 destructive reset/clean；
- 不上传 raw LTB/DTX/TGA/CFG/client binaries；
- 每个 local-only input 只提交 path/hash/size 等 provenance；
- negative result 必须带 scan scope/count/excludes；
- 不删除历史 evidence 来隐藏错误。

提交前至少：

```bash
git status --short --branch
git diff --cached --name-only
```

只 stage 本轮明确修改的脚本与 `n01/**` evidence/report。

---

## 10. Handoff

本轮完成后 commit + push scoped code/evidence 到 `master`。

Chat/Sol 下一次 Review：

```text
base = 69c03d8769db2107cd94cae11accc750716466ae
```

P4-M01 / N01 状态保持 ACTIVE，P5-T02 保持暂停，直到 Chat/Sol 明确升级。