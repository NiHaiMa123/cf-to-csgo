# P4_M01_N01_CONTINUATION.md — 95b6bb3 review; one final scope-guard fix before blocker freeze

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / FINAL_SCOPE_GUARD; SUBSTANTIVE_BLOCKER = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。若历史说明冲突，以本文件为准。P4-M01 尚未 PASS；P5-T02 继续暂停。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
95b6bb363a5f00daf01193f53e2a27cff9cea3f8
P4-M01-N01: final documentation cleanup - F1 provenance parameterization, F2 closure wording, F3 counter-subset guard
```

本轮 executor provenance：

```text
executor_model   = MiniMax-M3
executor_family  = MiniMax
executor_harness = Claude Code
```

commit footer 继续定义为：

```text
NON_AUTHORITATIVE_FOR_EXECUTOR_MODEL
```

---

## 2. Chat/Sol 对 95b6bb3 的正式结论

```text
F1 reusable provenance parameterization      ACCEPT
F2 runtime-overclaim removal                 ACCEPT
F2 blocker next_step                         ACCEPT
F2 generator/report consistency              ACCEPT
F3 current 261 / 18 evidence                 ACCEPT
F3 subset implementation                     MINOR_REWORK

N01 evidence/documentation                   ACCEPT_WITH_ONE_MINOR_CODE_GUARD_FIX
N01 substantive                              BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P4-M01-N01 PASS                              NO
P4-M01                                       ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P5-T02                                       PAUSED_BY_P4_M01
```

### 已接受并冻结

以下全部不再修改其 substantive conclusion：

```text
executor provenance: CLI > env > unspecified           ACCEPT
no generic MiniMax-M3/Claude Code hardcoded default    ACCEPT
commit footer provenance NON_AUTHORITATIVE             ACCEPT
engine_binding_closure schema v3                       ACCEPT
repo directory mirroring = TOOL_BEHAVIOR               ACCEPT
original CF runtime mirroring = OPEN_UNRESOLVED        ACCEPT
substantive blocker = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS ACCEPT
next_step waits for new runtime/client artifact        ACCEPT
ArmModel positive-control boundary                     ACCEPT
CFG/channel evidence grades                            ACCEPT
current config counters 102382 / 261 / 18 / 355        ACCEPT
current target 0-hit / derived-output accounting       ACCEPT
```

---

## 3. 当前唯一执行任务：F3 structural subset guard

`95b6bb3` 增加了：

```python
assert config_candidates_decoded <= config_candidates_seen
```

但当前 `build_consumer_index()` 的 predicate 仍不一致：

```python
if ext in CONFIG_EXT and is_likely_model_texture_config(rel, ext):
    config_candidates_seen += 1

if is_likely_model_texture_config(rel, ext):
    ...
    if real_mappings:
        config_candidates_decoded += 1
```

`is_likely_model_texture_config()` 还允许：

```text
.cft .fcf .csv .dat .xml .json .lua .ref .apf
```

所以 `config_candidates_decoded` 在代码结构上并不保证属于 `config_candidates_seen`；单独的数值 assert 不能证明集合包含关系。

### 必须修法

统一 candidate predicate，例如：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)

if is_config_candidate:
    config_candidates_seen += 1
    scan_metadata[rel]["scanned"] = True

    raw = _safe_read(...)
    ...
    if real_mappings:
        config_candidates_decoded += 1
```

关键要求：

```text
config_candidates_seen
config_candidates_decoded
config_index
```

必须使用同一个 `is_config_candidate` scope；decoded 必须由 control flow 保证为 seen 的真子集，而不是只靠：

```python
assert decoded <= seen
```

assert 可以继续保留，作为 regression guard。

### 当前 evidence 不得改变

除非统一 predicate 后机械重跑确实产生变化，否则应保持：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
raw_scan_files_seen                   = 355
raw_scan_files_decoded                = 355
```

若数字变化，必须解释是 predicate scope correction 的机械结果，不得手工维持旧数字。

---

## 4. 不得顺手做的事项

本轮只修 F3。禁止：

```text
- 再做 runtime/client 搜索；
- 再扫同一 repo/data corpus；
- 重跑或重解释 CFG semantic；
- 修改 F1 provenance policy；
- 把 repo ObjExporter mirroring 升级为原 CF runtime proof；
- 输出 READY_FOR_NATIVE_MATERIAL_COMPOSITION；
- 标 P4-M01-N01 PASS；
- 标 P4-M01 PASS；
- 恢复 P5-T02。
```

---

## 5. F3 acceptance criteria

必须全部满足：

```text
[ ] seen / decoded / config_index 共用同一个 config-candidate predicate
[ ] decoded 在 control flow 上只能发生于 seen candidate
[ ] `assert config_candidates_decoded <= config_candidates_seen` 保留
[ ] 当前或新生成 report 的 scope legend 与代码 predicate 一致
[ ] JSON evidence 可正常 parse
[ ] engine_binding_closure.status = OPEN_UNRESOLVED
[ ] N01 substantive = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
[ ] data/** 未 staged / 上传
```

推荐只修改：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
```

只有机械 regeneration 必需时才触碰其他 evidence。

---

## 6. 完成后的强制状态

F3 经 Chat/Sol Review 接受后：

```text
N01 evidence cleanup = COMPLETE / FROZEN
N01 substantive      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

然后当前 corpus 的 N01 工作停止。

Blocker 只有在获得新输入时解除：

```text
CF client .exe
engine/render/resource DLL/module
original runtime bundle/archive with consumer code
shader/runtime package
reliable documented material/piece binding contract
```

重新打开时固定路线：

```text
strings/resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

仅静态、只读；不执行未知 binary；不上传 raw binary/data/**。

---

## 7. Git / data discipline

严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no destructive reset/clean
no force push
no raw CF assets/runtime binaries
```

提交前：

```bash
git status --short --branch
git diff --cached --name-only
```

只 stage F3 明确涉及的 tracked script/report/evidence。

---

## 8. 下次 Review 起点

```text
base = 95b6bb363a5f00daf01193f53e2a27cff9cea3f8
review only F3 scope-guard commits after this base
```

F3 完成后不要自行创建新的 N01 task；等待 Chat/Sol 将 N01 evidence lane 正式冻结。