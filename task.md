# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-F
Title: Exact-path reverse lookup of WeaponShader/ and AlphaMap/ in packed BF005
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-E
```

# 2. Previous execution status

N03-E：共用 RS 只采样 `TEXTURE1`，体内无 TGA/CFG 字符串。
N03-C：canonical Weapon 105 个字段没有 TGA/CFG 路径。
N03-B 搜过 inventory token，但 CFG 的 rez_path 用了错误的 `SHADER/WEAPONSHADER/`（N03-A normalisation miss）。本轮用 **runtime 真实路径** 重查。

# 3. Current goal

在 packed `Butes/BF005.LTC` 的 **全部** lisp 记录里，对 TGA/CFG 做 exact path 反查，并对照全表 `*FileName` 字段集合。

回答：

```text
runtime path
  WeaponShader/M4A1_S_BornBeast.CFG
  AlphaMap/M4A1_S_BornBeast_alpha.TGA
  NormalMap/M4A1_S_BornBeast_N.TGA
  SpecularMap/M4A1_S_BornBeast_S.TGA
  -> any BF005 record/field
  -> FileName-key union vs 黑骑士 keys
```

# 4. Required Work

只 decode `rez/RB001.REZ` / `Butes/BF005.LTC`（N03-B/C 已 bind）。不要再扫 475 个 REZ，不要扫 4925 个 CFG 文件体。

1. 抽出全部 lisp 记录（所有 `_head`，不限 Weapon）。
2. Exact token（bounded，不用 `M4A1_S_BornBeast` stem）：
   - `WeaponShader/M4A1_S_BornBeast.CFG` 与反斜杠形式
   - `AlphaMap/M4A1_S_BornBeast_alpha.TGA` 等三张 TGA 的 runtime 相对路径
   - inventory `ModelTextures\Shader\WeaponShader\...` 与 `ModelTextures\AlphaMap\...` 源路径
3. 字段值若包含路径段 `WeaponShader\` / `AlphaMap\` / `NormalMap\` / `SpecularMap\`（后面跟文件名），记为 directory-prefix hit（这是 path segment，不是 filename similarity）。
4. 统计全表 `*FileName` 键的并集，对比 Weapon 1002 / 黑骑士 已有键。若别的武器有 `AlphaMap*` 字段而黑骑士没有，记为 differential；若全表都没有，记 scoped negative。
5. REZ 目录只做一件事：确认这四个 runtime `full_path` 仍存在（N03-A 已有 SHA，不重复当 consumer）。

输出：

```text
work/.../n03f_shader_alphamap_lookup/
```

至少包含：

```text
exact-path hit report
FileName-key union vs canonical Weapon
directory-prefix hits
confirmed relations
remaining ambiguity
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不使用 `M4A1_S_BornBeast` stem 当 CFG proof（那是 StandardName alias）；
- 不把目录里还有别的 AlphaMap 文件当成 binding；
- 不扫描全部 `.cfg` payload / 全部非 BUTES `.ltc`；
- 不进入 DLL/EXE/FXO reverse；
- 不进入 P5 identity；
- 不冻结 CFG shader semantics；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. SHADER_ALPHAMAP_CONSUMER_CONFIRMED
   a BF005 field exact-binds one of the four runtime paths

B. CANDIDATE_ONLY
   directory-prefix or FileName-key differential only

C. SCOPED_NEGATIVE
   no exact path in any BF005 record; FileName-key union has no Alpha/Shader path field

D. REWORK_REQUIRED
   cannot re-decode packed BF005
```

完成后返回 status / commit SHA / changed files / confirmed relations / remaining blockers / next highest-value target。

完成后 STOP，等待 Planner/Reviewer。
