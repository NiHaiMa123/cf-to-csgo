# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-D
Title: M4A1 Runtime Binding -> REZ Asset Existence Verification
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-C ACCEPTED / COMPLETE
```

# 2. Previous milestone accepted

N02-C 已确认：

```text
bf005.ltc weapon records extracted
M4A1-family records found = 10
runtime Bute binding fields recovered
BornBeast direct binding = NOT FOUND
status = M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN
```

已冻结事实：

```text
CF runtime weapon config layer is readable
M4A1 family resource references exist in Bute records
filename similarity is not binding proof
BornBeast identity remains open
```

# 3. Current Goal

验证 N02-C 找到的 runtime binding 是否对应真实 CF runtime artifact。

不要进入 shader、DLL、EXE、client execution。

目标：

```text
bf005 M4A1 Weapon Record
        -> referenced runtime path
        -> REZ archive existence
        -> artifact inventory evidence
```

重点回答：

```text
Models\\weapons\\m4a1.ltb
Models\\PlayerView\\pv-m4a1
M4A1_Silencer.ltb
pv-m4a1_silencer
以及相关 DTX
是否真实存在于当前 CF runtime REZ 中？
```

# 4. Scope

只使用：

```text
D:\\Program Files\\CF(2)
existing REZ inventory
N02-C outputs
```

允许：

```text
bounded archive lookup
path/index inspection
SHA evidence collection
```

禁止：

```text
full REZ bulk extraction
DLL/EXE reverse
FXO shader reverse
CF client execution
memory dump
```

# 5. Required Analysis

## 5.1 Runtime path lookup

针对 N02-C 输出中的：

```text
ModelFileName
SkinFileName
PViewModelFileName
PViewSkinFileName
RenderStyleFileName
```

建立：

```text
runtime binding path
-> REZ/archive source
-> exists/not exists
-> hash if extracted
```

## 5.2 Evidence classification

每个结果必须标记：

```text
DIRECT_RUNTIME_ARTIFACT
ARCHIVE_INDEX_ONLY
NOT_FOUND_IN_SCOPED_RUNTIME
```

不要把 basename match 当成 binding。

## 5.3 BornBeast relation

继续保持：

```text
runtime m4a1 path
!= BornBeast proof
```

只有发现：

```text
runtime config
+ exact artifact
+ existing BornBeast source relation
```

才提升证据等级。

# 6. Expected Output

输出目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02d_rez_asset_lookup/
```

至少：

```text
runtime_asset_lookup.json
rez_binding_report.md
```

# 7. Completion States

## A. Runtime artifact confirmed

```text
M4A1_RUNTIME_ARTIFACT_CONFIRMED
```

要求：

- runtime path
- archive source
- evidence

## B. Config exists but artifact unresolved

```text
M4A1_CONFIG_FOUND_ARTIFACT_UNRESOLVED
```

要求：

- searched scope
- missing reason
- next highest-value target

完成后 STOP，等待 Review。

# 8. Forbidden

- 不宣布 P4-M01 PASS；
- 不进入 P5 identity confirmation；
- 不使用视觉相似证明绑定；
- 不重新逆 LTC；
- 不修改长期 pipeline。

# 9. Handoff

返回：

```text
status
commit SHA
changed files
runtime path lookup result
REZ evidence
next highest-value investigation target
```
