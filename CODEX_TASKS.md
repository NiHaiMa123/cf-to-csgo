# CODEX_TASKS.md — Local Executor 本地执行合同

> 本文件给任何用户选择的、具备本地执行能力的 Agent 使用；不绑定 Luna、Codex、GLM 或其他具体模型/Agent。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> 默认 Planner / Reviewer = **Chat/Sol**；默认本地 Executor = 用户当前选择的可执行本地任务的 Agent。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / TARGETED_REWORK_REQUIRED   <- CURRENT
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03/T04    BLOCKED
```

协议顺序：

```text
P4_M01_TASK_SPEC.md          parent contract
P4_M01_REWORK_R1.md          original R1 correction contract
P4_M01_R1_CONTINUATION.md    current direct execution/review overlay
```

`P4_M01_R1_CONTINUATION.md` 不是 R2；当前版本已经包含 Chat/Sol 对 commit `8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f` 的 Review。

---

## 2. 每次启动

1. `git status --short --branch`；
2. 确认 `master`；
3. 安全同步：

```bash
git fetch origin
git pull --rebase origin master
```

4. 读取：

```text
AGENTS.md
plan.md 第1节
CODEX_TASKS.md
P4_TASKS.md
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md   <- current direct entry
```

5. 复用：

```text
commit 632ede4 historical exploration evidence
commit bded9e8 first R1 correction
commit 8af3cd0 latest targeted continuation
scripts/material_recovery/r1_*.py
work/m4a1_s_bornbeast/p4_m01_native_material/r1/**
```

不要从头重跑 R1。

---

## 3. 当前正式 Review

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

## 4. 当前唯一执行顺序

### 1) R1-F CFG — FIRST

保留已证明事实：

```text
237/237 WeaponShader CFG:
all non-0xFF bytes occupy one fixed offset-mod-3 phase;
the other two phases are 0xFF.
```

必须修当前 `r1_cfg_reverse.py`：

- `good_h` 是 varying byte phase，不是已证明的 record head gap；
- 禁止再把 `h` 命名/解释成 `head_partial_bytes`，除非有独立 framing evidence；
- 当前 BornBeast `492 = 2 + 163*3 + 1` 解释会漏 offset 491 的最后一个 varying sample；
- 所有 bytes 必须 100% accounting；
- primary 至少保留 byte-0-origin accounting：

```text
BornBeast     492 = 164*3
Transformers  506 = 168*3 + 2
Jewelry       642 = 214*3
```

- varying-phase sample sequence 也必须完整计算，不能 off-by-one；
- 保持竞争 hypothesis：

```text
H-CFG-A RGB/BGR triplets, h = varying color channel
H-CFG-B scalar + padding/alignment, record boundary unproven
H-CFG-C other 3-byte periodic packing
```

只允许把 **3-byte periodic/mod-3 structural pattern** 写 VERIFIED。CFG semantic consumer 继续 OPEN。

### 2) R1-C DTX — narrow fix only

不要重跑 formal DTX/LZMA 或 width candidate scan；这些已经有效提交。

只修：

- `continuity_all_channels()` 当前 `range(0, rb, 6)` 只采 mod3==0；改成真正覆盖两个变化 channel或完整 pixels；
- report 的 `all-channel` 描述必须与代码一致；
- corpus 数据是：

```text
1046 non-empty PV DTX
1043 size%2048 == 164
3 outliers: 550 / 672 / 676
```

因此只能写 `1043/1046 = 99.71% dominant pattern`，禁止再写 `every` / universal invariant；
- 2212-byte tail 与 channel order 可继续 OPEN，不要求为本轮 PASS 强行破解。

### 3) R1-E Stage-2 — scope correction

保留 ArmModel text material CFG positive evidence：

```text
[Textures] named texture fields
[Techniques]
[Properties] PieceIndex
```

这证明 CF 存在 explicit per-piece material format。

但 weapon slot→texture-set 仍 OPEN。

negative result 只能描述实际扫描范围：

```text
scanned config-like/dat/lta corpus
.cfg .ini .txt .xml .csv .ref .lua .apf .cft .fcf .dat .lta
<=64 MiB
355 files in current run
```

禁止写 `no mapping anywhere in local data`。

### 4) R1-H — accepted fix, no repeat

commit `8af3cd0` 已把旧 `step=97` byte-phase mixing 改为 pixel-index sampling：

```text
H2 phase-mixing fix = ACCEPTED
```

不要再次重修。只在 CFG 修正后把 `cfg_strip()` 的旧 `if raw[i] != 0xFF` extraction 与新 CFG policy 对齐。

H1/H2 继续 `DIAGNOSTIC_ONLY`，不代表 engine composition semantics。

### 5) R1-I closure

重生 closure，删除/修正旧错误陈述：

```text
"every PV DTX size%2048==164"
"CFG 492=2+163*3+1 exact framing"
```

所有 OPEN 项继续 OPEN。

---

## 5. 默认不要重跑

```text
A provenance
B full inventory rescan
G variant differential
R1-D formal TGA repair
DTX formal header/LZMA verification
DTX committed width candidate scan
H2 pixel-index sampling fix
ArmModel text material-format discovery
```

除非新 evidence 明确冲突。

---

## 6. Executor 不得

- 上传/修改/删除 `data/**`；
- `git add .` / `git add -A` / `git add --all`；
- force push / destructive reset/clean；
- 重跑 accepted work 只为了产生更多文件；
- 把 CFG mod-3 phase 自动当 record boundary；
- 把 `scalar+padding` 写成 exact framing；
- 把 1043/1046 写成 every/universal；
- 把 scanned config-like negative 写成整个 local data 的 exhaustive negative；
- 把 LTB numeric field 自动命名为 verified texture slot；
- 把 diagnostic preview 当 engine semantics；
- 请求用户 final visual gate；
- 执行 J / 恢复 P5-T02；
- 自行把 `plan.md` 改成 PASS。

---

## 7. 完成后提交

只 push scoped code/evidence。报告必须保留 supersedes/review_reason/input hashes，并保证关键 claim 能在提交代码中重跑。

完成后推荐状态仍只能由 Executor写为 evidence recommendation，例如：

```text
CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

最终 P4-M01 状态由 Chat/Sol Review 决定。

---

## 8. Executor provenance

任务保持 agent-agnostic。用户报告当前实测组合是：

```text
Harness: Claude Code
Model: GLM-5.3-Flash internal beta / multimodal
```

`bded9e8` 和 `8af3cd0` footer 中的 `Co-Authored-By: Claude Opus 4.8` 不是可靠实际模型 provenance。后续如记录 benchmark，显式写 `executor_harness` / `executor_model`，不要复制错误 footer。

---

## 9. P5 handoff

只有 Chat/Sol 明确判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 `P5-T02`。当前继续 `PAUSED_BY_P4_M01`。
