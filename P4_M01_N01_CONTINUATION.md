# P4_M01_N01_CONTINUATION.md — 46fcace review; final documentation cleanup then blocker freeze

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / FINAL_DOCUMENTATION_CLEANUP; SUBSTANTIVE_BLOCKER = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。若历史任务说明与本文件冲突，以本文件为准。P4-M01 尚未 PASS；P5-T02 继续暂停。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
46fcacebbc631fc05e0d491470b5e5482bca4533
P4-M01-N01: minor evidence cleanup - M1 JSON validity, M2 scope counters, M3 executor provenance
```

本轮实际 executor provenance：

```text
executor_model  = MiniMax-M3
executor_family = MiniMax
executor_harness = Claude Code
```

commit footer 中自动出现的：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

继续定义为：

```text
NON_AUTHORITATIVE_FOR_EXECUTOR_MODEL
```

模型 provenance 只能来自实际 harness/runtime 显示值；没有可靠值就写 `unspecified`。

---

## 2. Chat/Sol 对 46fcace 的正式结论

```text
46fcace technical cleanup                 ACCEPT
M1 JSON validity                          ACCEPT
M2 scan-count correction                  ACCEPT
M3 current-run provenance                 ACCEPT
N01 substantive consumer result           BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P4-M01-N01 PASS                           NO
READY_FOR_NATIVE_MATERIAL_COMPOSITION     NO
P4-M01                                    ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P5-T02                                    PAUSED_BY_P4_M01
```

### 2.1 已接受并冻结，不要重跑

```text
_ALL_ / "scanned" pseudo-hit fix                     ACCEPT
config mapping / scan metadata separation            ACCEPT
derived-output isolation                             ACCEPT
hits_by_extension/resource_family/consumer split     ACCEPT
BornBeast/Transformers/Jewelry/BlueDiamond text hits 0  ACCEPT / SCOPED_NEGATIVE
.dat consumer hits 0                                 ACCEPT / SCOPED_NEGATIVE
BornBeast derived-output hits 4                      ACCEPT / DERIVED_OUTPUT_HIT ONLY
JSON evidence parse cleanup                          ACCEPT
CFG measured lineage                                 ACCEPT
BornBeast CFG phase 2 / 164                          ACCEPT / OBSERVED
Transformers CFG phase 1 / 169                       ACCEPT / OBSERVED
Jewelry CFG phase 2 / 214                            ACCEPT / OBSERVED
BlueDiamond CFG phase 2 / 166                        ACCEPT / OBSERVED
CFG semantic downgrade                               ACCEPT
channel semantics Layer A/B/C split                  ACCEPT
false-PASS generator guard                           ACCEPT
LTB post-mesh short field                            ACCEPT / STRUCTURAL
repo parser does not consume short id                ACCEPT / TOOL-CODE OBSERVATION
repo ObjExporter path mirroring                      ACCEPT / TOOL-BEHAVIOR ONLY
ArmModel PieceIndex + multi-map positive control     ACCEPT
237/237 WeaponShader mod-3 structural fact           ACCEPT
engine_binding_closure.status OPEN_UNRESOLVED        ACCEPT
```

---

## 3. 当前 substantive blocker — 已确认

当前 local `data/` corpus 已完成 bounded、read-only 静态检查，没有发现可用于原 CF engine-side consumer tracing 的：

```text
CF client executable
CF engine/runtime DLL/module
original runtime/REZ bundle containing consumer code
compiled shader/runtime package
weapon-format material/resource table
```

所以当前材料不足以证明：

```text
post_mesh_short_id / piece identity
-> original CF material/shader resolver
-> texture family binding
-> WeaponShader CFG semantic consumer
```

正式 substantive 状态：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

这是“输入不足导致阻塞”，不是 PASS，也不是新的 FAIL。没有新增 runtime artifact 时，禁止重复扫描当前 repo/data corpus，禁止继续用 basename/path heuristic 替代原游戏 consumer。

---

## 4. 当前唯一执行任务：Final Documentation / Provenance Cleanup

下一位 Executor **只做 F1–F2；F3 是推荐 regression guard**。完成后停止。

### F1 — provenance generator 不得硬编码 MiniMax-M3

`46fcace` 当前报告中的 MiniMax-M3 provenance 对本轮是正确的，但生成脚本把本轮模型写死在通用 generator 中，未来换模型重跑会产生错误 provenance。

涉及至少：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
scripts/material_recovery/n01_phase1_to_phase5_runner.py
```

要求改成运行时可配置，例如任一等价方案：

```text
CLI args:
  --executor-model
  --executor-harness
  --executor-family

或 environment:
  N01_EXECUTOR_MODEL
  N01_EXECUTOR_HARNESS
  N01_EXECUTOR_FAMILY
```

固定 fallback：

```text
executor_model  = unspecified
executor_harness = unspecified
executor_family = unspecified
```

不得把某次 benchmark identity 固化成通用脚本默认值。

当前 `46fcace` 已生成的 report 可以继续保留 MiniMax-M3，因为它描述的是这次真实运行；只有未来 regeneration 才读取参数/环境变量。

必须保留：

```text
commit_footer_model_provenance = NON_AUTHORITATIVE
```

### F2 — 清理 `engine_binding_closure.json` 的 runtime overclaim / stale next_step

当前文件仍有过时措辞：

```text
CrossFire LithTech runtime appears to resolve the 5-map material family via deterministic directory mirroring.
```

这超出当前证据。当前只接受：

```text
repository exporter performs deterministic Models/... -> ModelTextures/... path mirroring
= TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
```

原 CF runtime binding 必须继续：

```text
OPEN_UNRESOLVED / BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

因此把该项改成类似：

```text
status = TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
evidence = repo exporter performs deterministic filename/path mirroring; this is not proof of the original CrossFire runtime binding
original_cf_runtime_binding = OPEN_UNRESOLVED
```

同时把 stale：

```text
next_step = Awaiting Chat/Sol review for N01 Phase 1-3 findings
```

改成：

```text
next_step = BLOCKED pending new original CF runtime/client artifact or equivalent documented consumer contract
```

`status` 必须继续：

```text
OPEN_UNRESOLVED
```

### F3 — 推荐：scope-counter regression guard

`config_candidates_decoded` 应当严格是 `config_candidates_seen` 的子集。建议让计数发生在同一个 candidate predicate 下，并加：

```python
assert config_candidates_decoded <= config_candidates_seen
```

这只是 future-regression cleanup，不改变 46fcace 当前 261 / 18 的已接受观测。

---

## 5. Final cleanup acceptance criteria

必须满足：

```text
[ ] 通用 generator 不再硬编码 MiniMax-M3 / Claude Code
[ ] provenance 未提供时稳定 fallback 为 unspecified
[ ] 当前 MiniMax 运行报告仍可保留 MiniMax-M3 历史 provenance
[ ] commit footer 继续 NON_AUTHORITATIVE
[ ] engine_binding_closure 不再暗示 original CF runtime mirroring 已被证明
[ ] engine_binding_closure.next_step 指向 runtime-artifact blocker
[ ] engine_binding_closure.status 仍为 OPEN_UNRESOLVED
[ ] CFG/channel grades未升级
[ ] 无 READY_FOR_NATIVE_MATERIAL_COMPOSITION
[ ] 无 P4-M01-N01 PASS / P4-M01 PASS / P5-T02 resumed
[ ] data/** 未 staged / 上传
```

完成后推荐状态：

```text
N01 evidence cleanup = COMPLETE / FROZEN
N01 substantive state = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

然后停止，不创建新的 N01 repo/data search run。

---

## 6. Blocker 解除条件

只有获得新的、与原 CF consumer 等级相当的输入，才重新打开 substantive N01：

```text
CrossFire client executable
engine/render/resource DLL/module
original runtime bundle / archive containing consumer code
shader/runtime package
可靠 documented material/piece binding contract
```

安全边界：

```text
只做静态、只读分析
不执行未知 client binary
不上传 binary/raw data/**
只提交 relative path / SHA256 / size / string offsets / xref / call-chain evidence
```

重新打开后的固定路线：

```text
strings / resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture family / WeaponShader consumer contract
```

不得回到 basename heuristic 当 engine proof。

---

## 7. Git / data discipline

继续严格遵守 `AGENTS.md`：

```text
master only
never upload data/**
no git add . / -A / --all
no destructive reset/clean
no force push
no raw CF assets/runtime binaries
```

启动：

```bash
git status --short --branch
git fetch origin
git pull --rebase origin master
```

提交前：

```bash
git status
git diff --cached --name-only
```

只 stage F1/F2/F3 涉及的 tracked script/report/evidence。

---

## 8. 当前状态 / 下次 Review 起点

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / FINAL_DOCUMENTATION_CLEANUP
N01 substantive    BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P5-T02             PAUSED_BY_P4_M01
```

下一次 Chat/Sol Review：

```text
base = 46fcacebbc631fc05e0d491470b5e5482bca4533
review only final-cleanup commits after this base
```

F1/F2 完成并接受后，当前 corpus 的 N01 work 冻结；等待新增 runtime artifact。