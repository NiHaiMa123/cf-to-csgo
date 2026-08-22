# P4_M01_N01_CONTINUATION.md — ea11ba1 review; minor evidence cleanup then runtime-artifact blocker

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / MINOR_EVIDENCE_CLEANUP; SUBSTANTIVE_BLOCKER = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。`plan.md` 第 1 节继续保持项目 coarse authority：P4-M01 尚未 PASS，P5-T02 继续暂停；当前 N01 直接执行细节以本文件为准。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
ea11ba143d859193213f24ab92248ff8a576b135
P4-M01-N01: targeted rework - deterministic cleanup + runtime consumer search
```

本轮用户确认 executor family 为 MiniMax，运行环境为 Claude Code；commit footer 中出现的 `Co-Authored-By: Claude Opus 4.8 (1M context)` **不是可靠 executor provenance**，不得据此改写历史执行模型。若需要精确 model id，只能记录 harness/runtime 实际显示值；未知就写 `unspecified`。

---

## 2. Chat/Sol 对 ea11ba1 的正式结论

```text
ea11ba1 technical result                   ACCEPT_WITH_MINOR_EVIDENCE_CLEANUP
P4-M01-N01 substantive consumer result     BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P4-M01-N01 PASS                            NO
READY_FOR_NATIVE_MATERIAL_COMPOSITION      NO
P4-M01                                     ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P5-T02                                     PAUSED_BY_P4_M01
```

### 2.1 已接受并冻结

以下不再重跑：

```text
_ALL_ -> scanned schema bug fix                         ACCEPT
config mapping / scan metadata separation              ACCEPT
look_up_texture schema/type guards                      ACCEPT
derived-output isolation                               ACCEPT
hits_by_extension/resource_family/consumer split       ACCEPT
four target text-config hits = 0                       ACCEPT / SCOPED_NEGATIVE
four target .dat consumer hits = 0                     ACCEPT / SCOPED_NEGATIVE
CFG measured lineage                                   ACCEPT
BlueDiamond CFG sample_count = 166                     ACCEPT / OBSERVED
CFG semantic downgrade                                 ACCEPT
channel semantics Layer A/B/C separation               ACCEPT
stale Phase 4/5 false-PASS generator protection        ACCEPT
LTB short-field structural observation                 ACCEPT
repo parser non-consumption observation                ACCEPT / TOOL-CODE OBSERVATION
repo ObjExporter mirroring                             ACCEPT / TOOL-BEHAVIOR ONLY
ArmModel PieceIndex + multi-map positive control       ACCEPT
237/237 WeaponShader mod-3 structural fact             ACCEPT
engine binding closure remains OPEN_UNRESOLVED         ACCEPT
```

### 2.2 Substantive runtime search — ACCEPTED blocker

`runtime_consumer_search` 对当前 local `data/` corpus 做了 bounded、read-only 静态检查。当前 corpus 中未发现可用于真实 engine-side consumer tracing 的：

```text
CF client .exe
CF engine/runtime .dll/.so/.dylib
.rez archive
.bin/.pak/.pck/.vpp runtime bundle
compiled shader package
weapon-format material/resource table
```

因此当前 repo + 已解包静态资源不足以证明：

```text
post_mesh_short_id / piece identity
-> original CF material/shader consumer
-> texture family binding
-> WeaponShader CFG semantic consumer
```

正式 substantive 状态：

```text
BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

这不是 FAIL，也不是 PASS。不要再用 `LithTechObjExporter` basename/path heuristic 替代原 CF runtime consumer。

---

## 3. 当前唯一执行任务：Minor Evidence Cleanup

下一位 Executor **只做本节三项**。完成后 handoff，不继续 Phase 1–5，不重复 runtime search。

### M1 — 修 `runtime_consumer_search.json` 为合法 JSON

当前文件中存在 Python 风格字符串拼接：

```text
"rationale": (
  "..."
  "..."
)
```

JSON 不允许该语法。

要求：

```text
- 改成标准 JSON string；
- 不改变 substantive conclusion；
- `handoff_status` 继续为 BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS；
- 用标准 parser 验证整个 n01 JSON evidence set。
```

至少执行并保存/报告结果：

```bash
python -m json.tool work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json > NUL
```

Windows PowerShell 若 `NUL` 不适用当前 shell，可用等价的 JSON parse 命令。推荐额外验证：

```text
consumer_candidate_matrix.json
weapon_material_differential.json
cfg_consumer_report.json
channel_semantics_report.json
engine_binding_closure.json
runtime_consumer_search.json
```

### M2 — 修 Phase 1 scan-count label / counting semantics

当前 `n01_phase1_consumer_search.py::build_consumer_index()` 中：

```python
files_scanned += 1
```

发生在 config/text extension 判断之前，所以当前报告：

```text
config files scanned (post-low-value filter): 102382
```

标签不准确。`102382` 实际更接近：

```text
all files with extension seen after low-value filter
```

这不推翻 raw-needle `355` scope 或 target 0-hit 结论，但 evidence label 必须与代码口径一致。

允许两种修法，二选一：

```text
A. 保留计数逻辑，重命名字段/报告文字，例如：
   all_non_low_value_files_seen
   config_candidate_files_decoded
   raw_needle_scope_files

B. 真正把 files_scanned 改成只统计定义明确的 config candidate scope，
   同时另设 all_files_seen 计数。
```

要求最终 report / JSON 中每个 count 的 scope 能从代码机械复现；不得把所有 extension 文件数叫 `config files scanned`。

### M3 — provenance 规则固定

不要修改历史 commit footer。未来 evidence/report 若记录 executor：

```text
executor_model = <actual harness/runtime model id if visible; otherwise unspecified>
executor_harness = Claude Code (when applicable)
executor_provenance_source = runtime/harness display or user-confirmed family
```

明确：

```text
commit Co-Authored-By footer = NON_AUTHORITATIVE_FOR_EXECUTOR_MODEL
```

若 harness 自动添加错误 footer，不要以此改变 evidence 里的真实 provenance。

---

## 4. Minor cleanup acceptance criteria

本轮可由 Local Executor 提交推荐结果，但最终接受仍由 Chat/Sol Review。

必须全部满足：

```text
[ ] runtime_consumer_search.json 可被标准 JSON parser 读取
[ ] n01 关键 JSON evidence 全部 parse PASS
[ ] 102382 等 scan count 标签与实际 counting scope 一致
[ ] 0-hit / DERIVED_OUTPUT_HIT 结论未被改写或混淆
[ ] CFG / channel evidence grades 未被重新升级
[ ] engine_binding_closure 仍为 OPEN_UNRESOLVED
[ ] 无 READY_FOR_NATIVE_MATERIAL_COMPOSITION
[ ] provenance 不再依赖 commit footer 推断 executor
[ ] data/** 未 staged / 上传
```

允许修改范围优先保持：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json
```

只有验证需要时才触碰其他 n01 evidence；不得顺手重写已接受结果。

---

## 5. Minor cleanup 完成后的强制停止点

如果 M1–M3 全部完成：

```text
N01 evidence cleanup = COMPLETE
N01 substantive state = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

然后停止并 commit/push handoff。

**禁止再次执行：**

```text
- 全量重跑 N01 Phase 1–5；
- 重复扫描同一 repo/data corpus，希望换模型得到不同 consumer；
- 把 repo ObjExporter heuristic 升级成 CF engine proof；
- 重新曲线拟合 CFG 并升级 semantic；
- 生成 READY/PASS closure；
- 恢复 P5-T02。
```

在没有新增 runtime artifact 的情况下，重复搜索当前 corpus 不构成 substantive progress。

---

## 6. Blocker 解除条件

只有获得新的 **CF 原始 runtime/client artifact** 或同等级 documented consumer contract，才重新打开 substantive N01 consumer search。

优先可接受输入：

```text
CrossFire client executable
engine/render/resource DLL
runtime module
original REZ/runtime bundle containing engine-side resolver code
shader/runtime package
可靠的官方/逆向文档，能给出 material/piece binding contract
```

本地二进制仍然：

```text
- 只做静态、只读分析；
- 不执行未知 client binary；
- 不上传 binary/raw data；
- 只提交 path/hash/size/string/xref 等 provenance/evidence。
```

一旦 artifact 可用，下一 continuation 应从：

```text
strings / resource names
-> static xref
-> loader/resolver call chain
-> piece/material key use
-> texture/WeaponShader consumer contract
```

开始，而不是回到 basename scan。

---

## 7. 已接受 baseline — 不要重跑

```text
P4 baseline                              PASS / FROZEN
P4-M01-R1                                ACCEPTED / COMPLETE
N01 Phase 0                              ACCEPT / FROZEN
TGA formal repair                        ACCEPT
DTX no formal header / not LZMA          VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodicity        VERIFIED_STRUCTURAL
DTX 1024 stride                          STRONG_HYPOTHESIS
DTX 1043/1046 statistic                  VERIFIED_CORPUS_STATISTIC
CFG 237/237 mod-3 structure              VERIFIED_STRUCTURAL
ArmModel [Textures]/PieceIndex           ENGINE_FORMAT_POSITIVE_CONTROL
69c03d/e11 CFG measured-data lineage     ACCEPT
repo LTB short-id non-consumption        ACCEPT / CODE OBSERVATION
repo ObjExporter mirroring               ACCEPT / TOOL-BEHAVIOR
CFG semantic interpretation              OPEN_UNRESOLVED
original CF runtime consumer              BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

仍未证明：

```text
post_mesh_short_id semantic meaning
original piece/material -> texture binding
WeaponShader CFG semantic consumer
DTX/TGA original native shader roles
DTX tail semantics
native composition closure
```

---

## 8. Git / data discipline

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

只 stage M1–M3 明确修改的 tracked script/report/evidence。

---

## 9. 当前状态 / 下次 Review 起点

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / MINOR_EVIDENCE_CLEANUP
N01 substantive    BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P5-T02             PAUSED_BY_P4_M01
```

下一次 Chat/Sol Review：

```text
base = ea11ba143d859193213f24ab92248ff8a576b135
review only minor-cleanup commits after this base
```

M1–M3 完成后，不再给当前 corpus 分配新的 N01 substantive search task；等待新增 runtime artifact。