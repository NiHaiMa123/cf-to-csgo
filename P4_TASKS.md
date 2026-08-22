# P4_TASKS.md — P4 baseline 冻结 + P4-M01 当前入口

> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。
>
> P4 baseline 历史结论仍为 **`PASS / FROZEN`**。
>
> 当前具体执行子任务：**P4-M01-N01 — Engine Material Consumer & Binding Closure**。

---

## 1. 当前 P4 结构

```text
P4 baseline   PASS / FROZEN
    |
    +-- conversion/build/package/MIGI/runtime contract       frozen
    +-- native CF material fidelity                          not proven historically

P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
    |
    +-- P4-M01-R1   ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF
    |
    +-- P4-M01-N01  ACTIVE / ENGINE_BINDING_INVESTIGATION   <- CURRENT
```

当前文件关系：

```text
P4_M01_TASK_SPEC.md                         parent contract
P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md     current direct execution spec
P4_M01_R1_CONTINUATION.md                   final R1 Review / predecessor record
```

---

## 2. Frozen baseline

继续冻结：

```text
Implementation baseline 10aa99b770e575300ca3c28324ef3de3d5b70c6b
run_20260819_170013_270792
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 runtime slot
57-bone reference
sequence/attachment contract
RV-01 ~ RV-06
```

P4-M01/N01 不重新证明或修改 frozen conversion chain。

---

## 3. R1 handoff

R1 已完成核心 correction：

- TGA formal repair；
- DTX formal route/LZMA/full-file periodicity/width scan/双变化 channel continuity；
- DTX `1043/1046` dominant statistic；
- CFG phase != record boundary；
- CFG off-by-one；
- H2 pixel-index sampling；
- ArmModel explicit `[Textures]/PieceIndex` positive control；
- binding negative scope correction。

因此：

```text
P4-M01-R1 = ACCEPTED_WITH_MINOR_CLEANUP / HANDED_OFF_TO_N01
```

剩余 minor cleanup 见 N01 Phase 0，不再展开新的 R1 investigation。

---

## 4. 当前 N01

正式协议：[`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md)。

目标：

```text
weapon mesh/piece
-> real material/binding key
-> local texture family
-> WeaponShader CFG/material resource consumer
-> channel/storage/binding semantics
```

固定顺序：

```text
Phase 0  R1 consistency cleanup
Phase 1  consumer call/data-path discovery
Phase 2  ArmModel positive control + weapon-family differential
Phase 3  WeaponShader CFG consumer identification
Phase 4  storage/channel/binding semantics
Phase 5  engine binding closure
```

Phase 0 通过后同一轮直接进入 Phase 1。

---

## 5. 当前已接受 baseline

```text
DTX no formal LithTech header           VERIFIED_STRUCTURAL
DTX not LZMA                            VERIFIED_STRUCTURAL
DTX 3-byte periodic payload             VERIFIED_STRUCTURAL
DTX 1024/no-mips                        STRONG_HYPOTHESIS
DTX channel/tail                        OPEN
TGA formal repair                       ACCEPT / STRUCTURAL
CFG 237/237 single mod-3 phase          VERIFIED_STRUCTURAL
CFG record boundary                     OPEN
ArmModel text material format           VERIFIED_STRUCTURAL
weapon post-mesh short field            VERIFIED_STRUCTURAL
short field == texture slot             PROVISIONAL
weapon slot -> texture-set              OPEN
H2 pixel-index fix                      ACCEPT / DIAGNOSTIC_ONLY
```

---

## 6. N01 允许/禁止

允许：

```text
CFRezManager/Decoders/** material-related changes
inspection/export code
scripts/material_recovery/**
work/m4a1_s_bornbeast/p4_m01_native_material/n01/**
必要的 scoped tests
```

禁止：

```text
重跑 TGA formal repair
重跑 DTX header/LZMA/width scan
用 basename 直接判 binding
把 CFG phase 当 record boundary
用 external pixels 做 final
无边界 blind scan data/**
修改 P4 frozen contract
恢复 P5-T02
```

---

## 7. N01 Review gate

至少需要看到：

```text
consumer_candidate_matrix.json
consumer_search_report.md
weapon_material_differential.json
cfg_consumer_report.json
channel_semantics_report.json
engine_binding_closure.json
```

N01 PASS 只允许进入 P4-M01 native composition/final closure；**不自动等于 P4-M01 PASS**。

只有 Chat/Sol 明确判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 P5-T02。

所有 Agent 继续遵守 [`AGENTS.md`](AGENTS.md) 的 master-only handoff 与 `data/**` local-only 规则。