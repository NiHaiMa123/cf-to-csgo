# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-C
Title: Read-only metadata/strings from playerviewmesh.fxo
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N04-B
```

# 2. Previous execution status

N04-B = XREF_FOUND_UNRELATED：CShell 对 `SpecularMap\%s` 有 12 条 LEA，旁边是 `playerview\`，不是 Bute 字段名。`WeaponShader\` 前缀在 packed `crossfire.exe` 里 **0 xref**。不脱壳。

# 3. Current goal

只读第一人称 mesh shader 的 **常量/采样器名**，看它有没有 CFG/TGA/WeaponShader 路径。

回答：

```text
playerviewmesh.fxo
  -> DXBC? LZMA? printable sampler/cbuffer names?
  -> WeaponShader / AlphaMap / SpecularMap / .CFG / .TGA tokens?
```

# 4. Required Work

只读本机：

```text
D:\Program Files\CF(2)\rez\Shader\playerviewmesh.fxo
```

对照（可选，同一目录，帮助区分通用 vs 武器专用）：

```text
rez/Shader/playermesh.fxo
```

允许：LZMA-alone 外壳剥开、ASCII/UTF-16 字符串、DXBC magic、token 命中表。

禁止：还原完整 HLSL、写 PoC/exploit、反编译指令流进仓库、提交 .fxo。

输出：`work/.../n04c_playerviewmesh_fxo/`

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不脱壳 `crossfire.exe` / `crossfirebase.dll`；
- 不附加调试器；
- 不碰 ACE；
- 不扫全部 14 个 FXO（最多 playerviewmesh + playermesh 对照）；
- 不 git add .fxo/.exe/.dll。

# 6. Completion State

```text
A. FXO_NAMES_WEAPONSHADER
   常量/采样器名含 WeaponShader 或 AlphaMap/CFG/TGA 路径

B. FXO_NAMES_GENERIC
   有 tPlayerViewMesh / 贴图槽名，但没有 CFG/TGA 路径

C. FXO_NO_USEFUL_STRINGS
   解不开或没有相关明文

D. REWORK_REQUIRED
   读不到 listed fxo
```

完成后 STOP。
