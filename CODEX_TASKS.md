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
P4-M01-N01         ACTIVE / FINAL_SCOPE_GUARD   <- CURRENT
N01 substantive    BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P5-T01             PASS / USER_REFERENCE_CONFIRMED
P5-T02             PAUSED_BY_P4_M01
P5-T03/T04         BLOCKED
```

当前 direct entry：

```text
P4_M01_N01_CONTINUATION.md
```

---

## 2. 最新 Review baseline

最新已 Review Local Executor 提交：

```text
95b6bb363a5f00daf01193f53e2a27cff9cea3f8
P4-M01-N01: final documentation cleanup - F1 provenance parameterization, F2 closure wording, F3 counter-subset guard
```

Chat/Sol verdict：

```text
F1 provenance parameterization      ACCEPT
F2 closure wording/blocker          ACCEPT
F3 current evidence                 ACCEPT
F3 implementation                   MINOR_REWORK
N01 substantive                     BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

下一次 Review 只看 `95b6bb3` 之后的 F3 scope-guard commit。

---

## 3. 启动顺序

1. `git status --short --branch`
2. 确认 `master`
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
P4_M01_N01_CONTINUATION.md
```

5. **不要重跑 N01 Phase 0/1–5，不要重新扫描当前 corpus。**

---

## 4. 当前唯一任务：F3 config-candidate scope guard

当前 bug 是两个 counter 没有被同一个 predicate 结构约束：

```python
if ext in CONFIG_EXT and is_likely_model_texture_config(rel, ext):
    config_candidates_seen += 1

if is_likely_model_texture_config(rel, ext):
    ...
    if real_mappings:
        config_candidates_decoded += 1
```

而 `is_likely_model_texture_config()` 允许 `.cft/.fcf/.csv/.dat/.xml/.json/.lua/.ref/.apf` 等额外扩展名。

因此当前：

```python
assert config_candidates_decoded <= config_candidates_seen
```

只检查数值关系，不能证明 decoded 真的是 seen 的集合子集。

### 必须改成

定义一次：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

然后：

```text
config_candidates_seen
config_candidates_decoded
config_index
```

全部只在 `is_config_candidate` 分支中产生。

保留：

```python
assert config_candidates_decoded <= config_candidates_seen
```

但它只作为 regression guard，不再代替 structural control-flow guarantee。

---

## 5. 必须保持的已接受结果

除非统一 predicate 后机械重跑产生可解释变化，否则保持：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
raw_scan_files_seen                   = 355
raw_scan_files_decoded                = 355
```

并保持：

```text
four target text-config hits = 0
.dat consumer hits = 0
BornBeast DERIVED_OUTPUT_HIT = 4
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

如果 counter 因 predicate 修正而变化，必须记录机械原因；禁止手改回旧数字。

---

## 6. 禁止事项

本轮不要：

```text
重新做 runtime consumer search
重复扫描 repo/data
重新解释 CFG
修改 F1 provenance policy
修改已接受 F2 closure boundary
把 ObjExporter mirroring 当 original CF runtime proof
输出 READY_FOR_NATIVE_MATERIAL_COMPOSITION
标 P4-M01-N01 PASS
标 P4-M01 PASS
恢复 P5-T02
```

---

## 7. Handoff / 完成条件

F3 完成后 commit + push scoped changes 到 `master`，然后停止。

Chat/Sol Review acceptance criteria：

```text
seen/decoded/config_index 共用同一个 config candidate predicate
decoded control flow 严格位于 seen candidate scope 内
assert decoded <= seen 保留
report/JSON scope legend 与代码一致
关键 JSON parse PASS
engine_binding_closure.status = OPEN_UNRESOLVED
N01 substantive = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
data/** 未 staged / 上传
```

接受后状态将更新为：

```text
N01 evidence cleanup = COMPLETE / FROZEN
N01 substantive      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

当前 corpus 不再分配 N01 substantive task。

---

## 8. Blocker 解除条件

只有新增：

```text
CF client .exe
engine/render/resource DLL/module
original runtime bundle/archive with consumer code
shader/runtime package
reliable documented material/piece binding contract
```

才重新打开 N01。

新路线固定为：

```text
strings/resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

只做静态、只读分析；不执行未知 binary；不上传 raw binary/data/**。

---

## 9. Git / data discipline

严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no destructive reset/clean
no force push
```

提交前：

```bash
git status --short --branch
git diff --cached --name-only
```

只 stage F3 明确需要的 tracked script/report/evidence。

---

## 10. Next Review

```text
base = 95b6bb363a5f00daf01193f53e2a27cff9cea3f8
```

F3 完成后不要自行继续新的 N01 task；等待 Chat/Sol freeze。