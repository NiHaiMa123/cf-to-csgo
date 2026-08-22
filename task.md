# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-C
Title: M4A1 Weapon Record -> Runtime Asset Correlation
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-B-R1 ACCEPTED / COMPLETE
```

# 2. Previous milestone accepted

N02-B-R1 已确认：

```text
73/73 rez/Butes/*.ltc
raw magic = 54 83 B2 E1
CrossFire wrapper XOR unlock = SUCCESS
unlocked header = 00 00 00 00
LithTech native decode = 73/73 SUCCESS
decoded output = readable LTA/Bute style text
```

上一轮已证明：

```text
CF runtime Bute config layer exists
weapon/resource relationship is represented in runtime config
```

上一轮未证明：

```text
BornBeast final identity
M4A1 target weapon -> exact runtime asset path
mesh piece -> material slot
texture -> shader semantics
native pixel reconstruction
```

# 3. Current Goal

本轮不要继续研究 LTC 格式。

目标是利用已经恢复的 runtime Bute config，建立：

```text
CF Weapon Record
        -> ModelFileName
        -> SkinFileName
        -> PViewModelFileName
        -> PViewSkinFileName
        -> RenderStyle
        -> existing CF asset inventory
```

重点回答：

```text
哪个 Weapon record 对应 M4A1-family？
它引用了哪些 LTB / DTX / RenderStyle？
这些资源是否对应 BornBeast / M4A1 当前候选资产？
```

# 4. Runtime Scope

只使用已有 evidence：

```text
D:\Program Files\CF(2)
rez/Butes/*.ltc decoded outputs
existing runtime inventory
existing N01/P4/P5 manifests
```

禁止重新扫描整个 data/**。

# 5. Required Analysis

## 5.1 bf005.ltc weapon extraction

优先分析：

```text
rez/Butes/bf005.ltc
```

提取全部 Weapon records：

至少记录：

```text
record name
WeaponName
ModelFileName
SkinFileName
PViewModelFileName
PViewSkinFileName
RenderStyleFileName
PViewRenderStyleFileName
Sound references if present
```

## 5.2 M4A1 correlation

不要只搜索 BornBeast 字符串。

使用：

```text
M4
M4A1
PV-M4A1
rif_m4a1
known LTB basename
known DTX basename
known PlayerView assets
```

建立：

```text
Weapon record
      |
      +-- referenced model
      |
      +-- referenced texture
      |
      +-- referenced pview asset
```

## 5.3 Existing asset correlation

与已有：

```text
BornBeast
Transformers
Jewelry
BlueDiamond
P4 manifests
LTB inventory
DTX/TGA inventory
```

做限定 lookup。

每个命中必须记录：

```text
runtime source
record/tag/key
resource path
matched asset
match type
evidence grade
```

区分：

```text
DIRECT_CONFIG_REFERENCE
BASENAME_MATCH
PATH_MATCH
VISUAL_SIMILARITY_ONLY
```

只有 DIRECT_CONFIG_REFERENCE 才能进入 binding evidence。

# 6. Expected Output

输出目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02c_weapon_correlation/
```

至少：

```text
weapon_records.json
m4a1_correlation_report.md
resource_binding_candidates.json
```

# 7. Completion States

## A. 找到 M4A1 -> runtime asset direct binding

```text
M4A1_RUNTIME_BINDING_CONFIRMED
```

要求：

- config record context
- exact resource paths
- SHA/path evidence
- relation direction

## B. 找到 weapon records，但未关联 BornBeast

```text
M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN
```

要求：

- 已确认 weapon config
- 已确认引用资源
- 下一步唯一最高价值 gap

## C. 未找到 M4A1 record

```text
M4A1_RECORD_NOT_FOUND_BOUNDED
```

要求：

- searched scope
- searched keys
- why next target is justified

完成后 STOP，等待 Review。

# 8. Forbidden

- 不逆 DLL/EXE；
- 不做 FXO shader reverse；
- 不运行 CF client；
- 不 memory dump；
- 不重新做 LTC reverse；
- 不把文件名相似当 binding proof；
- 不宣布 P4-M01 PASS；
- 不进入 P5 identity confirmation。

# 9. Handoff

返回：

```text
status
commit SHA
changed files
M4A1 record extraction result
resource correlation result
direct evidence or bounded negative
next highest-value investigation target
```
