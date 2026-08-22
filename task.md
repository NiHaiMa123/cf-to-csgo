# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-D-R1
Title: Path-Aware REZ Runtime Binding Revalidation
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-C ACCEPTED / COMPLETE
Reworks: P4-M01-N02-D / N02-E REVIEW_REWORK_REQUIRED
```

# 2. Review reason

N02-C 的 runtime Bute 解析和 M4A1 config binding 可以接受；但 N02-D/E 当前不能冻结。

Review 发现 N02-D 的 archive lookup 存在两个关键问题：

```text
1. REZ parser 递归读取目录时没有保留 parent directory path；
   最终 index key 实际是 lowercase basename，而不是完整 archive path。

2. extensionless ModelFileName / PViewModelFileName
   会对 .ltb/.dtx/.tga/.lto/.ltc/.rez/.dat 做宽泛 fallback；
   因此 pv-m4a1 可能同时命中 PV-M4A1.LTB 和 PV-M4A1.DTX，
   不能据此宣称 runtime full-path binding 已确认。
```

N02-E 又直接继承 N02-D 的候选 entry，因此 payload hash 结论也不能作为 binding closure。

另外 N02-E evidence 内部存在 Review 必须纠正的不一致：

```text
summary: REZ MD5 MATCH = 12
summary: REZ MD5 MISMATCH = 17
summary: skipped = 0
```

但报告 verdict 文本写成“全部 match 或 skipped”。

对 DTX mismatch 的 LZX 解释目前只允许记录为 hypothesis，不能冻结成事实。

# 3. Current Goal

本轮只返工：

```text
bf005 M4A1 runtime binding path
        -> path-aware REZ directory tree
        -> exact archive-relative path match
```

本轮不要继续 payload SHA，不做 BornBeast identity，不做 shader/PE reverse。

目标是回答：

```text
N02-C 中每一个 Model/Skin/PView/RenderStyle runtime path，
是否能在当前 CF REZ 中以“完整逻辑路径”找到对应 entry？
```

# 4. Required implementation correction

## 4.1 Preserve REZ directory hierarchy

修复 REZ parser：directory recursion 必须携带 parent path。

每个 file entry 至少记录：

```text
archive-relative full path
basename
REZ archive path
data_offset
size
id
catalog md5
```

例如必须能够区分：

```text
Models/PlayerView/PV-M4A1.LTB
ModelTextures/PlayerView/PV-M4A1.DTX
```

禁止再把二者仅以：

```text
pv-m4a1.ltb
pv-m4a1.dtx
```

放入无目录语义的 basename-only binding index。

## 4.2 Exact runtime-path matching

对有扩展名的 Bute value：

```text
normalize slash + case
-> exact archive-relative logical path match
```

只有 exact path 才可判：

```text
DIRECT_RUNTIME_PATH_BINDING
```

basename-only 命中只能是：

```text
BASENAME_CANDIDATE_ONLY
```

不得进入 binding closure。

## 4.3 Extensionless model path rule

对：

```text
ModelFileName
PViewModelFileName
```

如果 Bute value 无扩展名，只允许 field-specific model resolution：

```text
exact logical path + .ltb
```

除非有 Jupiter / CF runtime / repo consumer evidence 明确证明其他扩展名规则，否则禁止尝试：

```text
.dtx
.tga
.lto
.ltc
.rez
.dat
```

SkinFileName / RenderStyleFileName 等已有明确扩展名时保持原值 exact match。

## 4.4 Duplicate/archive ambiguity

如果同一个完整逻辑 path 出现在多个 REZ：

- 全部记录；
- 不静默选第一个；
- 没有明确 REZ load-order / override semantics 证据时，不宣布某一个 archive 是 authoritative consumer；
- 可标记：

```text
EXACT_PATH_MULTIPLE_ARCHIVES
```

但这不否定“该 path 在 runtime corpus 中存在”。

# 5. Scope

只使用：

```text
D:\Program Files\CF(2)
rez/ rez2/ rez3/ rez4/ rez5/ rez6/
N02-C weapon records / binding outputs
existing CFRezManager REZ reader/crypto implementation
```

允许读取 REZ directory metadata。

本轮禁止读取 payload bytes 作为主要工作。

# 6. Expected Output

输出目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02d_r1_path_binding/
```

至少：

```text
path_aware_rez_index_summary.json
runtime_path_binding.json
path_binding_report.md
```

报告必须明确给出：

```text
runtime binding count
exact full-path binding count
basename-only candidate count
not-found count
multiple-archive exact-path count
extensionless model resolutions
```

并逐条列出 M4A1 family binding。

# 7. Completion States

## A. Path-aware binding closure succeeds

```text
M4A1_RUNTIME_PATH_BINDING_CONFIRMED
```

要求：

- directory hierarchy mechanically preserved；
- runtime full paths exact-matched；
- extensionless model paths only resolved as justified `.ltb`；
- ambiguity explicitly reported。

## B. Some bindings remain ambiguous/missing

```text
M4A1_RUNTIME_PATH_BINDING_PARTIAL
```

要求明确列出 unresolved paths 与原因。

## C. Existing N02-D conclusion invalidated

```text
M4A1_RUNTIME_PATH_BINDING_REWORK_REQUIRED
```

如果 basename-only 命中无法复现为 full-path match，必须如实降级。

# 8. Forbidden

- 不继续 N02-E payload hash；
- 不解释或逆向 LZX；
- 不把 DTX MD5 mismatch 归因冻结为某种压缩语义；
- 不逆 DLL/EXE；
- 不逆 FXO shader；
- 不运行 CF client；
- 不 memory dump；
- 不重新逆 LTC；
- 不进入 P5；
- 不宣布 P4-M01 PASS；
- 不把 basename similarity 当 path binding proof。

# 9. Handoff

完成后返回：

```text
status
commit SHA
changed files
REZ hierarchy preservation result
exact full-path binding result
extensionless .ltb resolution result
archive ambiguity result
bounded negative if any
next single highest-value target
```

完成后 STOP，等待 Review。
