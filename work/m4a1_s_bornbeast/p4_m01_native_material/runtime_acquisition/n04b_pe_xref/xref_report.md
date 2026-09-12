# P4-M01-N04-B — Bounded xref of N04-A strings

- status: **XREF_FOUND_UNRELATED**
- completion: **B**
- P4-M01: still **INCOMPLETE**

只读 `CShell_x64.dll` 与 `crossfire.exe`。SHA 对上 N04-A。无调试器、无 PE 入库。

公开 Jupiter 的模型/RenderStyle 加载走 LTB texture index + TEXTURE1，**没有** `WeaponShader/*.CFG` 或 `AlphaMap/*.TGA` 路径。CF delta 是 CShell 里的路径格式串。

## 1. `modeltextures\SpecularMap\%s` — CShell_x64.dll

- 字符串 RVA `0x54C8F38`（file offset 88887352），12 条 `lea r8,[rip+disp]`。
- 每个 xref ±0x100 内另一句明文只有：`modeltextures\playerview\`。
- **没有** `StandardName` / `PViewSkinFileName` / `SpecularMapName` 字段名（那些在 CShell 另一处 Bute 表，N04-A 已见）。
- 同簇 rdata（±512）还有 `_s.dtx`（20 条 xref）和 `modeltextures/playerview/`（8 条）。

解读（OBSERVED，不是黑骑士证明）：

```text
CShell 用 sprintf 拼 SpecularMap\*.dtx
同一代码点还拿着 playerview\ 前缀
这是后期双贴图 .dtx 路线，对应 N03-G SpecularMapName
黑骑士 Bute 没有 SpecularMapName，本轮不能把这条 xref 接到 BornBeast TGA/CFG
```

## 2. `MODELTEXTURES\Shader\WeaponShader\` — crossfire.exe

- 明文还在，和 `NormalMap` / `AlphaMap` / `PostProcess` / `tPlayerViewMesh` 同一数据岛。
- RIP-relative xref：**0**；64-bit VA 指针：**0**。
- `crossfire.exe` 节名全是 `.std`，明文岛几乎没有代码引用（lea 目标仅 1466 个，对比 CShell 百万级）。代码侧像被壳过，**本轮不脱壳**。

不能证明谁加载 `WeaponShader\*.CFG`。

## 3. Completion

```text
SpecularMap\%s          12 LEA, paired with playerview\ prefix     B
WeaponShader\ prefix    plaintext only, no code xref               C for this string
near Bute field names   no
```

总体 **B**：有代码 xref，但不在 Bute key 旁边。

## 4. Remaining

- N04-C：仅当有人授权对 packed `crossfire.exe` 做更多静态，或只读 `playerviewmesh.fxo` 常量名；当前 **没有** WeaponShader 的 code consumer。
- 不宣布 P4-M01 PASS。
- 不把 `_s.dtx` 拼路径当成黑骑士 `_S.TGA`。

**status**: `XREF_FOUND_UNRELATED`
