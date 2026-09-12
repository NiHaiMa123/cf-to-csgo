# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-B
Title: Bounded RIP-relative xref of N04-A format/prefix strings
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N04-A
```

# 2. Previous execution status

N04-A = FORMAT_STRING_HIT：

```text
CShell_x64.dll   modeltextures\SpecularMap\%s          RVA 0x54C8F38
crossfire.exe    MODELTEXTURES\Shader\WeaponShader\    RVA 0x5A12A0
```

CShell 另有 Bute 字段名表。没有 `WeaponShader\%s.CFG`。未 xref。

# 3. Current goal

这两句明文有没有 **代码引用**，引用点附近是不是 Bute 皮肤加载。

回答：

```text
SpecularMap\%s
  -> LEA/RIP xref count, nearby strings
WeaponShader\ prefix
  -> LEA/RIP xref count, nearby strings
near StandardName / PViewSkinFileName / SpecularMapName ?
```

# 4. Required Work

只读这两个本地 PE（SHA 必须对上 N04-A）：

```text
x64/CShell_x64.dll
x64/crossfire.exe
```

只对 N04-A 已记录的两个 RVA 做：

1. x64 RIP-relative LEA（及 `mov reg,[rip+rel]` 指针表）xref；
2. 每个 xref 点 ±0x100 内其它 RIP-relative 字符串；
3. 目标串在 .rdata 的 ±512 字节 C-string 簇（帮助看是路径表还是 shader slot 表）。

对照公开 Jupiter：记下「有/无 WeaponShader 路径构造」，不要大段贴源码。

输出：`work/.../n04b_pe_xref/`

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不附加调试器 / 不注入 / 不 dump 运行中 CF；
- 不碰 ACE；不脱壳 `crossfirebase.dll`；
- 不把整文件反编译进 Git；不提交 PE；
- 不扩大到 272 DLL 或 FXO；
- 不把 `M4A1_S_BornBeast` 粒子名当材质绑定。

# 6. Completion State

```text
A. XREF_NEAR_BUTE_KEYS
   xref 点附近出现 StandardName / PViewSkinFileName / SpecularMapName

B. XREF_FOUND_UNRELATED
   有代码 xref，但不靠近这些 Bute key

C. NO_XREF
   明文在，但没有 RIP-relative 代码引用

D. REWORK_REQUIRED
   读不到 PE 或 SHA 对不上
```

完成后 STOP。
