# P4_M01_R1_CONTINUATION.md — R1 final Review / handoff to N01

> parent_task: `P4-M01`
>
> rework_id: `P4-M01-R1`
>
> Planner / Reviewer: **Chat/Sol**
>
> 当前状态: **ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01**

本文件现在是 R1 的最终 Review 记录，不再是当前 Local Executor 的第一执行入口。

当前执行入口：

[`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md)

R1 剩余的公式/path/注释/label 一致性问题已被收进 N01 Phase 0；完成 Phase 0 后 Executor 必须在同一轮直接进入真正的 engine material consumer/binding 调查，不再把项目停留在 R1 evidence-cleanup 循环。

---

## 1. 最终 Review 输入

最后一轮 R1 narrow rework：

```text
0dc5793b6e47cb20da9e44aebcec2195194bd6f2
P4-M01-R1 narrow rework: CFG framing fix, DTX continuity/scope, closure v3
```

前置关键提交：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f
```

该轮继续保持正确 authority boundary：Local Executor 只提交 code/evidence，不自行修改 `plan.md` 或宣布 `P4-M01 PASS`。

---

## 2. R1 最终分级

| Step | R1 最终 Review | 说明 |
|---|---|---|
| A provenance | **ACCEPT / REUSE** | 不重跑 |
| B inventory | **REUSE_WITH_CAUTION** | 作为后续差分输入 |
| C DTX | **CORE_CORRECTION_ACCEPTED** | formal header/LZMA/full-file census/width scan/双变化 channel continuity 已对齐；1024/no-mips 仍 strong hypothesis；tail/order open |
| D TGA | **ACCEPT / STRUCTURAL** | formal repair 接受 |
| E binding exploration | **PARTIAL_ACCEPT / HANDOFF_TO_N01** | ArmModel explicit material format 接受；weapon binding 仍是 N01 主问题 |
| F CFG correction | **CORE_CORRECTION_ACCEPTED** | phase-vs-boundary 和 off-by-one 已修；record boundary/consumer 仍 open |
| G variant differential | **ACCEPT / REUSE** | 后续 N01 继续使用 |
| H shader diagnostic | **H2_FIX_ACCEPTED / DIAGNOSTIC_ONLY** | pixel-index sampling fix 接受 |
| I R1 closure report | **ACCEPT_AS_INCOMPLETE_STATE_RECORD** | 正确保持 `CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`；不是 P4-M01 completion closure |
| J Source 1 integration | **DEFERRED** | 仍未到 final composition |

R1 的任务是纠正旧 evidence chain，不是破解全部 material semantics。该纠错目标现在已基本完成。

---

## 3. 已接受并冻结为 N01 输入的事实

### DTX

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC / NOT universal
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

### TGA

正式 inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular formal repair 接受；不要重跑旧 offset 争论。

### CFG

```text
237/237 WeaponShader CFG:
all non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

R1 已纠正：

- `phase != record boundary`；
- BornBeast/Transformers/Jewelry varying-phase sequence 分别为 `164/169/214`，不再丢最后 sample；
- H-CFG-A/B/C 保持竞争；
- scalar+padding 不是 exact framing；
- semantic consumer 仍 OPEN。

### Engine material positive control

ArmModel LZMA text CFG 已证明 CF 存在：

```text
[Textures] named texture references
[Techniques]
[Properties] PieceIndex
```

这是 `VERIFIED_STRUCTURAL` positive control；不能直接等同为 weapon format。

### Binding

```text
weapon LTB post-mesh short field exists          VERIFIED_STRUCTURAL
general field meaning == texture slot            PROVISIONAL
weapon mesh/piece -> actual texture set           OPEN
```

config-like/dat/lta 355-file negative 只对该实际扫描 corpus 生效，不是整个 local data exhaustive negative。

---

## 4. 仍需做的 minor consistency cleanup

这些不是新的 R1 investigation，全部转入 N01 Phase 0：

1. `r1_cfg_reverse.py` 的 `phase_origin.identity` 公式必须数学自洽。当前 sample count 是对的，但不能写 `first + sample_count*3 + trailing`；使用：

```text
first + (sample_count - 1)*3 + 1 + trailing
```

或只记录 first/last/count。

2. DTX report/docstring：
   - `1043/1046 = 99.71% dominant statistic`；
   - 删除旧 `every`；
   - 不写严格 `>3x margin`，除非数值实际满足。

3. shader evidence：
   - H1 preview path 指向真实 `h1_base_flat_r1.png` 并与 SHA 对齐；
   - H1 evidence class 从 `VERIFIED_DECODE_ONLY` 降到 layout-hypothesis/diagnostic 等与 DTX 当前等级一致的状态；
   - 清理顶部旧 `DTX=BGR24`、`CFG=scalar strip` 等过时描述。

4. binding 脚本顶部旧“full local data”类措辞与 v3 scoped negative 对齐。

完成后重新生成受影响 report/closure，作为 N01 preflight evidence。

---

## 5. R1 handoff 结论

```text
P4-M01-R1 = ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01
```

这**不等于**：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

真正剩余的 substantive blocker 已经不是 R1 evidence bug，而是：

```text
weapon-side material consumer / binding
WeaponShader CFG semantic consumer
DTX/TGA storage/channel/binding semantics
native composition closure
```

这些由：

[`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md)

继续。

P5-T02 仍 `PAUSED_BY_P4_M01`；当前仍不是 final user visual gate。