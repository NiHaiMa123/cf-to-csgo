# P4_M01_N01_CONTINUATION.md — Phase 0 accepted; current entry = Phase 1 consumer discovery

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / PHASE1_CONSUMER_DISCOVERY**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。若原始 N01 spec 与本文件在“当前 phase / 下一步 / 已接受项”上冲突，以本文件和 `plan.md` 第 1 节为准。原始 N01 的 provenance、evidence、Git/data、安全边界继续有效。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19
P4-M01-N01 Phase 0: R1 final consistency cleanup (gate PASS)
```

与上一 authoritative HEAD `d4c5cfcba541f3dc77eb38d21328c380de75c06d` 相比，该提交只修改 N01 Phase-0/R1 cleanup 相关脚本和 R1 reports，并新增：

```text
scripts/material_recovery/n01_phase0_gate.py
```

没有新增 N01 Phase 1+ 预期输出：

```text
n01/consumer_candidate_matrix.json
n01/consumer_search_report.md
n01/weapon_material_differential.json
n01/cfg_consumer_report.json
n01/channel_semantics_report.json
n01/engine_binding_closure.json
```

因此本轮属于 **Phase 0 cleanup complete, substantive N01 work not started**。

---

## 2. Chat/Sol 对 2344d61 的正式 Review

### 2.1 Phase 0 — ACCEPT / FROZEN

以下已逐项复核并接受：

```text
CFG phase-origin span accounting        ACCEPT
DTX margin / dominant-stat wording      ACCEPT
H1 preview path                         ACCEPT
H1 evidence-class downgrade             ACCEPT
shader stale BGR24/scalar wording       ACCEPT
binding negative-scope wording          ACCEPT
```

具体：

- CFG `accounting_phase_origin.identity` 已改为：

```text
n = first_offset + (sample_count - 1)*3 + 1 + trailing
```

BornBeast / Transformers / Jewelry 的 `164 / 169 / 214` sample extraction 保持不变；
- DTX 不再写 `>3x`，报告记录 measured margin，`1024 stride` 继续 `STRONG_HYPOTHESIS`；
- `1043/1046 = 99.71%` 继续明确为 dominant statistic，不是 universal invariant；
- `H1_base_flat.preview` 已指向实际 `h1_base_flat_r1.png`；
- H1 已降为 `EVIDENCE_SUPPORTED_LAYOUT_HYPOTHESIS / DIAGNOSTIC_LAYER_RENDER`；
- stale `DTX=BGR24` / `CFG=stride-3 scalar` / whole-data negative wording已清理。

`n01_phase0_gate.py` 可以作为 consistency diagnostic，但当前 Review 不依赖其进程退出码作为唯一 PASS 证据；Chat/Sol 已直接对提交后的脚本/report 做内容复核。

### 2.2 R1 状态升级

Phase 0 已收掉 R1 最后的 minor cleanup，因此：

```text
P4-M01-R1 = ACCEPTED / COMPLETE
```

不要再读取 R1 continuation 后重新执行 cleanup，除非出现新的 counterevidence。

### 2.3 执行完整性

原始 N01 spec 明确：

```text
Phase 0 PASS -> same run continue Phase 1
```

但 `2344d61` 在 Phase 0 后停止，没有进入 Phase 1。故：

```text
Phase 0 technical result = ACCEPT
N01 execution completeness = INCOMPLETE / STOPPED_EARLY
```

这不是 blocker，也不是要求重跑 Phase 0；下一位 Executor 直接从 Phase 1 继续。

---

## 3. 当前 Executor / benchmark provenance

用户当前准备切换执行模型：

```text
Model: MiniMax M3
Harness: user-selected / not specified in current Review
```

该信息仅用于 benchmark/provenance，不是 Task requirement。N01 继续保持 agent-agnostic。

历史 GLM 执行可保留为 previous benchmark context；不要根据 commit footer 推断真实模型。尤其不要复制：

```text
Co-Authored-By: Claude Opus 4.8 (1M context)
```

作为 MiniMax M3 或其他 executor provenance。

若新 evidence 需要记录当前 executor，显式写：

```text
executor_model = MiniMax M3
executor_harness = <actual harness if known locally>
```

未知 harness 就写 `unspecified`，不要猜。

---

## 4. 当前直接执行入口：Phase 1

**不要运行 Phase 0。**

同步最新 `master` 后，直接从原始 N01 spec 的：

```text
Phase 1 — consumer call/data-path discovery
```

开始。

当前问题：

> `ModelTextures/Shader/WeaponShader/*.CFG`、LTB post-mesh short field、DTX/TGA texture family，究竟被哪个 code/config/resource consumer 关联和消费？

优先沿已有代码关系，不先做 basename/global blind scan：

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

必须追真实数据流：

```text
producer/index/table
-> key / piece / model identifier
-> resolver / lookup
-> texture family / material resource
-> consumer
```

每个 candidate 至少记录：

```text
candidate_consumer / resource_family
source code path or local resource path
reference direction
raw key / field / offset / string
BornBeast hit?
Transformers hit?
Jewelry/control hit?
evidence class
accepted / rejected / open
reason
```

输出：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
```

---

## 5. Phase 2 必须跟进，不得只停在 candidate list

Phase 1 后继续 ArmModel positive control + weapon-family differential：

```text
BornBeast
Transformers
Jewelry
+ 至少 1 个简单/传统 M4A1-S control（若本地已有）
```

至少记录：

```text
LTB mesh count / mesh names
post-mesh short field raw offset/value
geometry SHA/signature relation
DTX path/SHA/size
Alpha/Normal/Specular path/SHA/size
WeaponShader CFG path/SHA/size
CFG varying phase/sample count
material/config/resource references
```

目标不是证明 basename，而是找**随 piece/material/skin 变化同步变化的 binding key**。

输出：

```text
n01/weapon_material_differential.json
```

### 当前最低 handoff 要求

MiniMax M3 本轮至少应完成并 push：

```text
Phase 1 outputs
+ Phase 2 differential output
```

不要在只生成 Phase 1 candidate list 后就停止。

若 Phase 1/2 已找到强 consumer candidate，继续原 N01 Phase 3–5；若未找到，保存 scoped negative/rejection evidence 后仍完成 Phase 2，再明确下一 continuation point。

---

## 6. Phase 3–5 继续沿原 N01 spec

### Phase 3 — WeaponShader CFG consumer

优先级：

```text
consumer/reference evidence
> binary curve fitting
> preview appearance
```

consumer 未找到时，H-CFG-A/B/C 继续保持 hypothesis；不能因 `[0,42]` 值域或 count fit 升级 semantic verified。

### Phase 4 — storage/channel/binding semantics

严格分开：

```text
storage byte order
map/binding role
shader composition role
```

DTX channel order/tail 可以保持 OPEN；TGA storage facts不能自动替代 shader role。

### Phase 5 — engine binding closure

优先 direct Path A；若 direct table 不存在，Path B 必须有多个独立 same-family/control differential evidence，并能 reject alternatives。

输出仍为：

```text
n01/cfg_consumer_report.json
n01/channel_semantics_report.json
n01/engine_binding_closure.json
```

---

## 7. 已接受 baseline — MiniMax M3 不得重跑

```text
R1 = ACCEPTED / COMPLETE
N01 Phase 0 = ACCEPT / FROZEN
TGA formal repair
DTX formal header/LZMA checks
DTX whole-file 3-byte periodicity
DTX 64..2048 width scan
DTX two-varying-offset continuity
DTX 1043/1046 dominant statistic
CFG 237/237 mod-3 structural fact
CFG phase-vs-record-boundary correction
CFG 164/169/214 sample extraction
CFG phase-origin span formula cleanup
H1 path/evidence cleanup
H2 pixel-index sampling fix
ArmModel [Textures]/PieceIndex positive control discovery
355-file scoped config-like negative definition
```

仍 open：

```text
weapon material consumer
weapon short-field semantic
weapon piece/material -> texture-set binding
WeaponShader CFG consumer / record semantic
DTX/TGA binding/channel semantics
DTX tail semantics
native composition closure
```

---

## 8. Git / evidence discipline

继续遵守 `AGENTS.md`：

- handoff 只认 `master`；
- `data/**` local-only；
- 不 broad stage；
- 不 force push / destructive reset/clean；
- 不上传 raw CF assets；
- 只提交 scoped code/evidence；
- negative result 必须写扫描 scope；
- Local Executor 不自行把 `plan.md` 改 PASS；
- 不执行 P5-T02 / final visual gate。

---

## 9. 当前状态

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / PHASE1_CONSUMER_DISCOVERY
P5-T02             PAUSED_BY_P4_M01
```

下一次 Chat/Sol Review 从 `2344d61` 之后的新提交开始，只审 Phase 1+ evidence，不再重审 Phase 0。