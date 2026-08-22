# P4_M01_R1_CONTINUATION.md — R1 targeted continuation after commit 8af3cd0

> parent_task: `P4-M01`
>
> rework_id: `P4-M01-R1`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / TARGETED_REWORK_REQUIRED**
>
> 本文件是 [`P4_M01_REWORK_R1.md`](P4_M01_REWORK_R1.md) 的当前 continuation / Review overlay，不是 R2。若本文件与旧 R1 continuation 的“当前状态/下一步”描述冲突，以本文件和 `plan.md` 第 1 节为准；R1 的安全边界、provenance、closure gate 继续有效。

---

## 1. 当前 Review 输入

本轮 Local Executor 提交：

```text
8af3cd0b6c2f7ecc12a90b24e5b70c4e2d99dd8f
P4-M01-R1 targeted continuation: committed scans, CFG hypotheses, stage-2 binding
```

该提交只修改/新增 R1 scripts/evidence/previews，没有上传 `data/**`，也没有自行修改 authoritative `plan.md` 或宣布 PASS。

用户报告执行环境继续为：

```text
Harness: Claude Code
Model:   GLM-5.3-Flash internal beta / multimodal
```

commit footer 中残留的 `Co-Authored-By: Claude Opus 4.8 (1M context)` 继续不能作为 executor provenance。任务定义保持 agent-agnostic。

---

## 2. Chat/Sol 对 8af3cd0 的正式分级

| P4-M01 step | 当前 Review 状态 | 处理方式 |
|---|---|---|
| A provenance | **ACCEPT / REUSE** | 不重跑 |
| B inventory | **REUSE_WITH_CAUTION** | 作为扫描起点 |
| C DTX | **PARTIAL_ACCEPT / NARROW_TARGETED_REWORK** | formal header/LZMA、full-file census、committed width scan 有效；continuity 仍非 all-channel，1043/1046 corpus statement 需纠正；tail/channel order 仍 open |
| D TGA | **ACCEPT / STRUCTURAL** | 不重跑，除非新 evidence 冲突 |
| E binding | **STAGE2_PARTIAL_ACCEPT / OPEN** | ArmModel 显式 `[Textures]/PieceIndex` material CFG 是真实 engine-format evidence；weapon-side binding 仍未找到；negative scope 必须限定到实际扫描 corpus |
| F CFG | **REWORK / FRAMING_BUG** | 237-file mod-3 structural fact 保留；当前 `head_partial_bytes`/triplet accounting 把 byte phase 当 record boundary，并漏最后一个 varying sample |
| G variant differential | **ACCEPT / REUSE** | supporting evidence |
| H shader hypotheses | **H2_FIX_ACCEPTED / DIAGNOSTIC_ONLY** | `step=97` phase-mixing 已按 pixel index 修复；不要重修；composition semantics 仍未证明 |
| I closure | **NOT READY / CONTINUE** | closure v2 含两个过度/错误陈述，需重生 |
| J Source 1 integration | **DEFERRED** | I 真正通过前不执行 |

当前状态继续：

```text
P4 baseline   PASS / FROZEN
P4-M01        ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1     ACTIVE / TARGETED_REWORK_REQUIRED
P5-T02        PAUSED_BY_P4_M01
```

当前不是用户 final visual Gate。

---

## 3. R1-C DTX — 接受主体，只修剩余证据一致性

### 已接受

commit `8af3cd0` 已真正把以下内容写入可重跑脚本：

- `DtxThumbnailDecoder` 支持 version `-2/-3/-5` 的 formal header route；
- `LzmaAloneDecoder.TryReadHeader` 等价 detection；
- whole-file mod-3 channel census；
- width candidate scan `64..2048 step 4`；
- 1024 为最小强 winner；
- channel order 不再硬写 BGR；
- `1024 width / single image` 已降级为 `STRONG_HYPOTHESIS`，不再写 `VERIFIED_STRUCTURAL`。

这些改动有效，**不要重新推翻重做**。

### 仍需修正 1：continuity 不是 all-channel

当前 `continuity_all_channels()` 实际代码：

```python
for i in range(0, rb, 6):
    abs(above[i] - below[i])
```

因为 6 是 3-byte pixel 的整倍数，它永远采 `offset mod 3 == 0`，没有覆盖第二个变化 channel。函数名/报告写 `ALL bytes / all-channel` 超出了实现。

下一轮必须：

- 对两个变化 record offsets（当前 full-file census 显示 mod3 0/1）分别计算 boundary continuity；或
- 真正按完整 pixel/all bytes 计算；
- report 必须精确描述实际采样。

### 仍需修正 2：corpus invariant 不能写 every

当前报告自身数据：

```text
non-empty PV DTX = 1046
size % 2048:
  164 -> 1043
  550 -> 1
  672 -> 1
  676 -> 1
```

因此禁止再写：

```text
every non-empty PLAYERVIEW DTX has size == 164 (mod 2048)
```

正确表述应是：

```text
1043/1046 (99.71%) non-empty PLAYERVIEW DTX share size % 2048 == 164
= dominant / near-universal corpus packing pattern
```

三个 outlier 必须保留，不得为了 invariant 删除/忽略。

### 仍 open，不要求为 PASS 强行破解

```text
2212-byte terminal region semantics
RGB/BGR/channel order
engine-side confirmation of 1024 stride/no-mip
```

其中 tail 可以继续 `OPEN_UNRESOLVED`，只要 report/closure 不把它伪装为已解释。

推荐当前等级：

```text
no LithTech header                 VERIFIED_STRUCTURAL
not LZMA                           VERIFIED_STRUCTURAL
3-byte pixel-like periodicity      VERIFIED_STRUCTURAL
row stride 1024                    STRONG_HYPOTHESIS
single continuous image/no mips    STRONG_HYPOTHESIS
size%2048==164 dominant pattern    VERIFIED_CORPUS_STATISTIC (1043/1046), NOT universal
terminal region semantics          OPEN
channel order                      OPEN
```

---

## 4. R1-F CFG — 当前唯一明确实现级返工点

### 可保留的 structural evidence

237/237 WeaponShader CFG 均满足：

```text
所有 non-0xFF bytes 集中在一个固定 offset mod 3 phase；
另外两个 mod-3 positions 为 0xFF。
```

这是真实 corpus fact，可继续保留。

### 当前 bug：把 channel phase 当成 record head gap

`r1_cfg_reverse.py` 当前逻辑：

```python
good_h = h
body = n - good_h
full_triplets = body // 3
slots = [raw[good_h + k*3] for k in range(full_triplets)]
```

`good_h` 只证明“变化 byte 位于哪一个 mod-3 phase”，**不能证明 record 从该 offset 开始**。

例如 BornBeast：

```text
size = 492 = 164 * 3
varying bytes at positions 2,5,8,...,491
```

当前报告却写：

```text
492 = 2 + 163*3 + 1
slot_count = 163
```

因此最后一个 varying sample at offset 491 被漏掉。

Transformers/Jewelry 同理：当前 168/213 应重新检查，不能以 `head_partial_bytes` 解释 phase。

### 下一轮必须改成“竞争 framing”，而不是提前选 record boundary

至少保留：

```text
H-CFG-A: byte-0-origin 3-byte RGB/BGR records
           h = varying color channel index

H-CFG-B: scalar + two padding bytes
           h may represent scalar phase/alignment, but record boundary is not yet proven

H-CFG-C: other 3-byte periodic container/packing
```

要求：

1. **所有原始 bytes 100% accounting**；
2. mod-3 phase 与 record boundary 使用不同字段名，不再叫 `head_partial_bytes`，除非有独立 framing evidence；
3. 不过滤合法 `0xFF`；
4. 对 primary 至少明确：
   - BornBeast 492 bytes / 164 byte-0-origin triplets；
   - Transformers 506 bytes = 168 full byte-0-origin triplets + 2 bytes tail；
   - Jewelry 642 bytes / 214 byte-0-origin triplets；
5. varying-phase sample count 用数学上完整的 phase sequence计算，不能丢最后一个；
6. `scalar+padding` 可保持 `PREFERRED_NOT_PROVEN`，但 `exact framing / truncation model VERIFIED` 撤销。

当前可以 VERIFIED 的仅是：

```text
3-byte periodic/mod-3 structural pattern across 237 files
```

CFG engine consumer / semantic parameter 继续 `UNRESOLVED_PROVISIONAL`。

---

## 5. R1-E Stage-2 binding — 接受发现，但限定 negative scope

### 接受 positive evidence

本轮从：

```text
data/rf016/Models/PLAYERVIEW/ArmModel/Shader/*.CFG
```

解出 LZMA-compressed text material format，包含：

```text
[Textures]
SpecularMapName0
EnvCubeMapName0
NormalMapName0
AlphaMapName0

[Techniques]
...

[Properties]
PieceIndex
...
```

这证明 CF 至少存在**显式 named texture + per-piece index 的 material format**。这是有效 engine-format evidence。

### 仍不能推出

```text
weapon LTB numeric field == PieceIndex / texture slot
weapon mesh -> actual DTX/TGA/CFG texture set
```

这些仍为 OPEN。

### negative result 必须按实际扫描范围表述

`r1_stage2_binding.py` 当前扫描的是 config-like corpus：

```text
.cfg .ini .txt .xml .csv .ref .lua .apf .cft .fcf .dat .lta
size <= 64 MiB
```

报告记录 `355 files scanned`。

因此允许写：

```text
no BornBeast weapon-side explicit material mapping found in the scanned config-like/dat/lta corpus
```

禁止写：

```text
no mapping anywhere in local data
```

除非后续真的有覆盖全部相关资源类别的扫描/evidence。

当前 stage-2 不要求无限扩大扫描来“逼出 PASS”；若没有直接 binding，可以保留 OPEN 并寻求更强 differential/engine-consumer evidence。

---

## 6. R1-H — H2 bug 已修，默认不再重做

旧 bug：`step=97` 导致 byte phase rotation。

commit `8af3cd0` 已改成按 pixel index：

```python
base_o = pi * 3
for c in range(3):
    ...
```

当前：

```text
H2 phase-mixing bug = FIX ACCEPTED
```

但 H2 继续保持：

```text
APPROXIMATION_HYPOTHESIS / DIAGNOSTIC_ONLY
```

除非 E/F 后续得到 engine composition semantics，否则不要因为 preview 好看升级。

附带清理：`cfg_strip()` 仍沿用 `if raw[i] != 0xFF` 的旧 extraction policy。下一轮在 CFG framing 修正后，让 diagnostic CFG strip 使用同一份无损 phase/triplet数据，不再单独维护旧过滤逻辑。

---

## 7. R1-I closure — 重生，但不要为 closure 强行解决 open item

当前 closure v2 正确保持：

```text
CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
```

但需移除/修正：

```text
"every non-empty PLAYERVIEW DTX size%2048==164"
"CFG 492=2+163*3+1 exact framing"
```

下一版 closure 只需与 corrected scripts/reports 对齐：

- DTX dominant corpus pattern = 1043/1046；
- DTX 1024/no-mips = strong hypothesis；
- CFG record boundary = unresolved；
- stage-2 binding = open；
- H2 = diagnostic；
- technical closure 未完成，因此不进入 user final visual gate。

---

## 8. 当前唯一执行顺序

下一位 Local Executor 从 commit `8af3cd0` 继续，**不要从头跑 R1**：

```text
1. R1-F FIRST:
   fix phase-vs-record-boundary bug and off-by-one sample loss;
   regenerate CFG report with lossless byte accounting and competing framing hypotheses.

2. R1-C:
   fix continuity to truly cover both varying channels/all pixels;
   change 1043/1046 corpus statement from universal invariant to dominant statistic.

3. R1-E:
   narrow negative-result wording to actual scanned config-like corpus;
   preserve ArmModel explicit material-format positive evidence;
   keep weapon slot->texture-set OPEN unless new direct evidence appears.

4. R1-H:
   keep accepted pixel-index sampling fix;
   only align cfg_strip diagnostic extraction with corrected CFG policy.

5. R1-I:
   regenerate closure from corrected reports; unresolved stays unresolved.
```

默认不要重跑：

```text
A provenance
B inventory full rescan
G variant inventory/differential
R1-D TGA repair
H2 pixel-index bug fix
DTX formal header/LZMA work
DTX committed width candidate scan
ArmModel text material-format discovery
```

---

## 9. Completion criteria for this continuation

下一次 Chat/Sol Review 至少需要看到：

- CFG 不再把 mod-3 phase 当 record head gap；
- CFG primary samples/bytes 无 off-by-one 丢失，所有 bytes 可追溯；
- CFG framing status 不把 scalar+padding 提前写成 exact；
- DTX continuity 与函数/报告宣称一致，覆盖两个变化 channel或完整 pixel；
- DTX corpus statistic 精确写 1043/1046，并保留 3 个 outlier；
- binding negative result 明确限定实际扫描范围；
- H2 accepted fix 未被回退；
- closure 不再引用上述错误陈述，并继续诚实保留 OPEN 项。

完成后由 Chat/Sol 决定：继续 P4-M01、是否还需更窄 targeted work，或进入真正 native-material closure。

### 当前禁止

- 执行 J；
- 恢复 P5-T02；
- 请求用户 final visual gate；
- 为获得 PASS 无限扫描或把 open hypothesis 升级成 verified；
- 复制错误 executor model/co-author provenance。
