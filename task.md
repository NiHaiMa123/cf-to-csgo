# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-A
Title: Exact-token string scan of authorized engine PEs
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-H
```

# 2. Previous execution status

N03-H：官方 DTX 头 0/16。524452 族（黑骑士 PV 和战龙对照）都是能量/标量层。QV 32932 size-fit 不是枪 atlas。Bute/DTX 像素路线关闭。用户授权 DLL，限定静态 strings。

# 3. Current goal

在 7 个真实（非 1 字节 stub）游戏 PE 里找 **明文路径构造串**。

回答：

```text
WeaponShader / AlphaMap / NormalMap / SpecularMap
  -> present as directory token?
  -> present as sprintf format (WeaponShader\%s.CFG)?
which PE
  -> packed vs plaintext
```

# 4. Required Work

只读本机 `D:\Program Files\CF(2)` 下列文件（N02-A SHA 对账）：

```text
x64/CShell_x64.dll
x64/crossfirebase.dll
x64/crossfire_x64base.dll
x64/crossfire.exe
x64/server_x64.dll
rez/Object_x64.lto
rez/Object.lto
```

ASCII + UTF-16LE，exact token（大小写不敏感子串，禁止 fuzzy/similarity）：

```text
WeaponShader
AlphaMap
NormalMap
SpecularMap
LightCorrectionLegacyShader
PViewSkinFileName
StandardName
M4A1_S_BornBeast
playerviewmesh
```

命中时记录 file offset / RVA / encoding / 字符串全文 / 前后 32 字节 printable context。单独标记是否含 `%s` / `%S` / `%hs` 或 `WeaponShader\` 路径片段。

输出：

```text
work/.../n04a_pe_string_hits/
```

至少：PE 身份表（size/SHA/packed heuristic）、命中表、remaining ambiguity。

不把 PE 文件复制进仓库。

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不附加调试器、不注入、不 dump 运行中 CF；
- 不碰 ACE / 反作弊 DLL；
- 不跑脱壳器 / 未知 EXE；
- 不反编译函数体（本轮只要 strings）；
- 不扫全部 272 DLL；
- 不进入 FXO；
- 不修改历史 accepted evidence；
- 不 git add 任何 .exe/.dll/.lto/.fxo。

# 6. Completion State

```text
A. FORMAT_STRING_HIT
   WeaponShader/%s 或 AlphaMap/%s 一类构造串

B. TOKEN_HIT_NO_FORMAT
   有目录名/扩展名 token，没有路径构造格式串

C. PACKED_OR_NO_HIT
   目标高熵或无这些明文

D. REWORK_REQUIRED
   读不到 listed x64 PE
```

完成后 STOP。
