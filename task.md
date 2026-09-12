# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-G
Title: Dump LightCorrectionLegacyShader and SpecularMapName values from packed BF005
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-F
```

# 2. Previous execution status

N03-F：黑骑士的 TGA/CFG 在 packed BF005 无 exact path。后期武器有 `SpecularMapName`（.dtx）和 `LightCorrectionLegacyShader`（18 条），黑骑士都没有。

# 3. Current goal

把这两类字段的 **实际取值** 列出来，判断是不是 CFG/shader 名。

回答：

```text
LightCorrectionLegacyShader values
  -> look like WeaponShader CFG stem? path? integer?
SpecularMapName values
  -> confirm .dtx only
黑骑士
  -> still missing both
```

# 4. Required Work

只 decode `rez/RB001.REZ` / `Butes/BF005.LTC`。

对每条含 `LightCorrectionLegacyShader` / `SpecularMapName*` / `SpecularPower` 的记录输出：

```text
WeaponName (GBK), StandardName, field, value
```

对照 `WeaponShader/` 目录里是否存在同名 `.CFG`（exact basename，不是 similarity proof：只有 value 本身已是确切 CFG 名才算命中）。

输出：

```text
work/.../n03g_legacy_shader_fields/
```

至少包含 dump 表、CFG basename 对照、remaining ambiguity。

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把缺字段当成“一定走 StandardName 约定”；
- 不进入 DLL/EXE/FXO reverse；
- 不扫描全部 CFG payload；
- 不进入 P5 identity；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. LEGACY_SHADER_FIELD_IS_CFG_NAME
   values exact-match WeaponShader/*.CFG basenames

B. CANDIDATE_ONLY
   values are names/ids but not proven CFG files

C. SCOPED_NEGATIVE
   values are not CFG names (ints, empty, unrelated)

D. REWORK_REQUIRED
   cannot re-decode packed BF005
```

完成后 STOP。
