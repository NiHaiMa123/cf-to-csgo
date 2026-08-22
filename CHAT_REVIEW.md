# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 ChatGPT 对话中的 **Chat/Sol** 使用。
>
> 项目唯一 authoritative progress/status 以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。

---

## 1. 当前阶段

截至 2026-08-22：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / TARGETED_REWORK_REQUIRED
P5-T01        PASS / USER_REFERENCE_CONFIRMED
P5-T02        PAUSED_BY_P4_M01
P5-T03        BLOCKED_BY_T02
P5-T04        BLOCKED_BY_T03
```

当前 Review/执行入口：

```text
P4_M01_TASK_SPEC.md
P4_M01_REWORK_R1.md
P4_M01_R1_CONTINUATION.md   <- current post-8af3 review overlay
CODEX_TASKS.md
```

---

## 2. Review principle

P4-M01 最终问题：

> BornBeast 是否已经能仅使用 local CF 资源 + verified semantics，得到可重复、可解释、0 external pixels 的正确原生材质。

Chat/Sol 必须特别拒绝：

- `能排成图 = 格式正确`；
- byte-count fit 直接升级为 verified；
- mod-3 phase 自动等同 record boundary；
- report claim 超过提交代码实际实现；
- partial corpus negative 写成 entire-local-data negative；
- filename/basename convention 冒充 structural binding；
- diagnostic shader preview 冒充 engine semantics。

---

## 3. 历史 R0 / first R1

### R0 exploration

```text
632ede449578f688cea7e6b5f40cbf03700aaaa5
```

有价值，但旧 `6/8 PASS / visual gate only` 被 Chat/Sol 否决。

### first R1 correction

```text
bded9e8a6f7f95997d9717eb8f35beb02619f153
```

有效推进：TGA repair 修正、DTX formal route、LTB numeric-field structure、CFG corpus pattern；但 DTX reproducibility、CFG framing、binding stage2、H2 sampling 仍需 targeted rework。

---

## 4. 2026-08-22 对 commit 8af3cd0 的 Review

Local Executor commit：

```text
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f
```

总体：**继续有效推进，但 R1 未完成。**

正式分级：

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

详细下一步以 [`P4_M01_R1_CONTINUATION.md`](P4_M01_R1_CONTINUATION.md) 为准。

### C — DTX

接受：

- formal DTX version `-2/-3/-5` route；
- not-LZMA detection；
- whole-file 3-byte periodic census；
- committed `64..2048 step4` width scan；
- 1024 作为 smallest strong winner；
- `1024/no-mip` 已诚实降为 `STRONG_HYPOTHESIS`；
- BGR wording 已撤销。

仍需纠正：

1. `continuity_all_channels()` 实际 `range(0, rb, 6)` 只采 mod3==0，并非 all-channel；
2. corpus 报告自身是 `1043/1046 size%2048==164`，不能写 `every non-empty PV DTX`；
3. 2212-byte tail 和 channel order 可继续 OPEN。

当前 1024 stride 可保留 strong hypothesis，不必重跑 width scan。

### D — TGA

继续 ACCEPT。正式关系：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

不重跑，除非新 evidence 冲突。

### E — Stage-2 binding

接受 positive evidence：ArmModel Shader CFG 中真实存在：

```text
[Textures] named texture refs
[Techniques]
[Properties] PieceIndex
```

这是 CF explicit material format 的 engine-format evidence。

但 weapon LTB numeric field == PieceIndex/texture slot 仍未证明；weapon mesh/slot -> DTX/TGA/CFG texture set 仍 OPEN。

negative scan 只覆盖当前 config-like/dat/lta corpus（报告为 355 files），所以只能写：

```text
not found in the scanned config-like/dat/lta corpus
```

不能写 `anywhere in local data`。

### F — CFG

这是当前最重要问题。

可保留 fact：237/237 CFG 的 non-FF bytes 集中在单一 `offset mod 3` phase，另外两 phase 为 FF。

当前 `r1_cfg_reverse.py` 错把 varying phase `h` 当 `head_partial_bytes`：

```python
body = n - h
full_triplets = body // 3
slots = raw[h + k*3]
```

这并不能证明 record 从 h 开始，并造成 off-by-one sample loss。

BornBeast：

```text
492 = 164 * 3
varying positions = 2,5,...,491  -> 164 samples
```

当前报告却写：

```text
492 = 2 + 163*3 + 1
slot_count = 163
```

因此 offset 491 被漏掉。

Review 要求重新区分：

```text
phase index != record boundary
```

至少保留：

```text
H-CFG-A byte0-origin RGB/BGR triplets; h = varying channel
H-CFG-B scalar+padding/alignment; record boundary unproven
H-CFG-C other 3-byte periodic packing
```

只允许把 corpus mod-3 pattern 写 VERIFIED。`scalar+padding exact framing` 不接受。

### H — shader hypotheses

旧 `step=97` phase-mixing bug 已在 8af3cd0 改为 pixel-index sampling，**FIX ACCEPTED**。

不要下一轮再花时间重修。H2 继续 diagnostic approximation。

需小幅对齐：`cfg_strip()` 仍有旧 `if raw[i] != 0xFF` extraction，应随 CFG 修正统一。

### I — closure

Executor 正确继续推荐：

```text
CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

Chat/Sol 同意。

但 closure v2 需修两条：

- `every non-empty PV DTX size%2048==164` -> `1043/1046 dominant pattern`；
- `CFG 492=2+163*3+1 exact framing` -> record boundary unresolved。

---

## 5. 当前 Review 下一步

下一次只重点检查：

```text
1. CFG phase-vs-record-boundary bug/off-by-one 是否真正修掉
2. DTX continuity 是否真实覆盖两个 varying channels/all pixels
3. DTX 1043/1046 corpus statistic 是否精确表述
4. binding negative scope 是否限定实际扫描 corpus
5. H2 accepted fix 是否未回退
6. closure 是否与 corrected reports 完全一致
```

默认不再 Review/要求重跑：A、G、TGA formal repair、DTX formal header/LZMA、DTX width candidate scan、H2 pixel-index fix、ArmModel material-format discovery。

---

## 6. External texture policy

历史 external CS1.6 BornBeast texture 只能 `reference_only / differential_control`。

禁止采样/抠图/bake/作为 final texture；final visible pixels 必须来自 local CF 或 verified deterministic semantics。

---

## 7. Executor provenance

用户报告当前实际执行组合：

```text
Harness: Claude Code
Model: GLM-5.3-Flash internal beta / multimodal
```

commits `bded9e8`、`8af3cd0` 的 Claude Opus co-author footer 不是可靠 executor provenance。任务继续 agent-agnostic。

---

## 8. P4-M01 -> P5 handoff

只有 Chat/Sol 明确判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

才恢复 P5-T02。当前不进入 user final visual gate、不执行 J、不恢复 P5。
