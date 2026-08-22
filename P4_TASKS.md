# P4_TASKS.md — P4 baseline 冻结 + P4-M01 材质纠偏入口

> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。
>
> P4 baseline 历史结论仍为 **`PASS / FROZEN`**。
>
> 当前具体执行子任务：**P4-M01-R1 — targeted continuation after commit 8af3cd0 Review**。

---

## 1. 当前 P4 结构

```text
P4 baseline   PASS / FROZEN
    |
    +-- conversion/build/package/MIGI/runtime contract      frozen
    +-- native CF material fidelity                         NOT proven historically

P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
    |
    +-- P4-M01-R1   ACTIVE / TARGETED_REWORK_REQUIRED      <- CURRENT
```

当前文件关系：

```text
P4_M01_TASK_SPEC.md          parent contract
P4_M01_REWORK_R1.md          original R1 correction contract
P4_M01_R1_CONTINUATION.md    current post-8af3 continuation/review overlay
```

若旧 R1 文档与 continuation 的当前状态/下一步冲突，以 continuation 与 `plan.md` 第 1 节为准。

---

## 2. Frozen baseline

继续冻结：

```text
P4-T01~T09 historical completion
RV-01~RV-06 historical evidence
p_cf_bornbeast_m4a4_p4_frozen_noop_01
M4A4 runtime slot
57-bone Source reference
sequence/attachment contract
```

P4-M01 不推翻 conversion/build/package/MIGI baseline，只修 native material lane。

---

## 3. P4-M01 目标

仅使用 local CF BornBeast LTB/DTX/TGA/CFG 等资源，恢复可重复、可解释、0 external pixels 的 native material，并产出可迁移到 P5 Transformers 的方法。

历史 external CS1.6 texture 只能 reference/differential control，不能进入 final pixels。

---

## 4. R1 历史与最新 Review

历史 exploration：

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5
```

first R1 correction：

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
```

latest targeted continuation：

```text
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f
```

Chat/Sol 最新正式分级：

```text
A provenance              ACCEPT / REUSE
B inventory               REUSE_WITH_CAUTION
C DTX                      PARTIAL_ACCEPT / NARROW_TARGETED_REWORK
D TGA                      ACCEPT / STRUCTURAL
E material binding         STAGE2_PARTIAL_ACCEPT / OPEN
F CFG reverse              REWORK / FRAMING_BUG
G variant differential     ACCEPT / REUSE
H shader hypotheses        H2_FIX_ACCEPTED / DIAGNOSTIC_ONLY
I native closure           NOT READY / CONTINUE
J Source1 integration      DEFERRED
```

详细技术要求只看 [`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md)。

---

## 5. 已接受，不要重跑

```text
A provenance
G variant differential
R1-D formal TGA repair
DTX formal header/LZMA verification
DTX whole-file 3-byte census
DTX committed 64..2048 width scan
H2 pixel-index sampling fix
ArmModel text material-format discovery
```

### TGA

正式关系已接受：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

### DTX

`1024 width / no-mips` 可继续作为 `STRONG_HYPOTHESIS`；不需要重跑 width scan。本轮只修 continuity 实现与 corpus statement。

### H2

旧 `step=97` byte-phase mixing 已在 `8af3cd0` 修复，默认不再返工。

---

## 6. 当前 targeted work

### F — CFG FIRST

保留：237/237 CFG 的 non-FF bytes 集中在单一 mod-3 phase。

必须修：当前脚本把 varying phase `h` 当 record head gap，导致错误 accounting/off-by-one。

BornBeast：

```text
492 = 164*3
varying positions 2,5,...,491 = 164 samples
```

当前 `492 = 2 + 163*3 + 1` / 163 samples 不接受。

必须区分：

```text
phase index != record boundary
```

至少保留：

```text
H-CFG-A byte0-origin RGB/BGR triplets
H-CFG-B scalar + padding/alignment, boundary unproven
H-CFG-C other 3-byte periodic packing
```

只允许把 mod-3 corpus pattern 写 VERIFIED。

### C — DTX narrow fix

- `continuity_all_channels()` 当前 `range(0, rb, 6)` 只覆盖 mod3==0；改成两个变化 channels 或完整 pixels；
- corpus 是 `1043/1046` size%2048==164，不能写 every/universal；
- 2212-byte tail/channel order 可继续 OPEN。

### E — Stage-2 scope correction

保留 ArmModel `[Textures]/[Properties]/PieceIndex` positive evidence。

weapon slot->texture-set 仍 OPEN。

negative result 只能限定到实际扫描的 config-like/dat/lta corpus（当前 355 files），不能写 entire local data exhaustive negative。

### H — alignment only

H2 fix 已接受。只需让 `cfg_strip()` 不再使用与新版 CFG policy 冲突的旧 `if raw[i] != 0xFF` extraction。

### I — closure

重生 closure，修正：

```text
DTX every -> 1043/1046 dominant statistic
CFG exact head-gap framing -> record boundary unresolved
```

继续 `CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`，除非新 evidence 真正达到 closure。

---

## 7. Frozen / 可修改边界

不得修改 frozen conversion/runtime contract。

P4-M01/R1 可修改：

```text
CFRezManager/Decoders/** 与材质恢复直接相关代码
inspection/export code
scripts/material_recovery/**
work/m4a1_s_bornbeast/p4_m01_native_material/**
```

`data/**` 永远 local-only。

---

## 8. Agent 路由

Local Executor 读取：

```text
AGENTS.md
plan.md
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md
```

从 commit `8af3cd0` 继续，不从零重跑。

Chat/Sol 负责最终 evidence Review 与状态决定。

---

## 9. Handoff

只有 Chat/Sol 判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复：

```text
P5-T02 -> M4A1_S_Transformers native material
```

当前继续 `P5-T02 = PAUSED_BY_P4_M01`。
