# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-D
Title: Extra static analysis of packed x64/crossfire.exe
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N04-C
```

# 2. Previous execution status

N04-C = FXO_NAMES_GENERIC：`playerviewmesh.fxo` 有 Alpha/Normal/Specular sampler 和 `tPlayerViewMeshEmsv`，没有 CFG/TGA 路径。WeaponShader 加载仍缺 code consumer。用户授权对 packed `crossfire.exe` 做更深静态（仍不脱壳、不附加进程）。

# 3. Current goal

在 `x64/crossfire.exe` 里把 WeaponShader 明文岛吃透：有没有 `%s.CFG`、指针表、XOR 编码、或 LEA 目录里的其它路径构造。

# 4. Required Work

只读 `D:\Program Files\CF(2)\x64\crossfire.exe`（SHA 必须对上 N04-A）。

1. 节表 / 入口 / import DLL 名 / overlay；不跑脱壳器。
2. 低熵节抽出全部 ASCII 串，过滤 WeaponShader / AlphaMap / .CFG / %s / playerviewmesh。
3. 全文件 1-byte XOR 搜 `WeaponShader`、`AlphaMap`、`.CFG`（key 1–255）。
4. 把 N04-B 的全部 RIP-LEA 目标串编目，列出含 shader/texture/cfg 的项。
5. 对 `MODELTEXTURES\Shader\WeaponShader\` 搜 64-bit VA、32-bit RVA、±16 对齐。

输出：`work/.../n04d_packed_crossfire_static/`

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不附加调试器 / 不注入 / 不 dump 运行中 CF；
- 不跑未知脱壳 EXE；不碰 ACE；
- 不提交 .exe/.dll/.fxo；
- 不扩大到 `crossfirebase.dll` 的 `.tvm0` 脱壳。

# 6. Completion State

```text
A. FORMAT_OR_XREF_HIT
   找到 WeaponShader\%s.CFG 或对该前缀的指针/LEA

B. STRING_ISLAND_ONLY
   仍只有明文目录前缀，无构造串、无代码/指针引用

C. PACKED_OPAQUE
   低熵岛之外无法得到更多相关明文

D. REWORK_REQUIRED
   SHA 对不上或读不到文件
```

完成后 STOP。
