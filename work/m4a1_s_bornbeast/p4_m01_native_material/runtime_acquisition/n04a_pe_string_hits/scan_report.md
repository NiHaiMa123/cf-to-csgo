# P4-M01-N04-A — Engine PE exact-token strings

- status: **FORMAT_STRING_HIT**
- completion: **A**
- confidence: **HIGH** for the two format/prefix strings below
- P4-M01: still **INCOMPLETE**（本轮没有 xref，没有合成规则）

7 个目标全部可读，SHA 与 N02-A inventory 一致。未复制 PE 进仓库。未附加调试器。

## 1. Per-file

| file | size | packed heuristic | class | notable |
|---|---|---|---|---|
| `x64/CShell_x64.dll` | 124 MB | no（正常 PE，`.text` entropy 6.06） | FORMAT | Bute 字段名 + `SpecularMap\%s` |
| `x64/crossfire.exe` | 7.8 MB | yes（节全名 `.std`，高熵，但仍有明文） | FORMAT | `MODELTEXTURES\Shader\WeaponShader\` |
| `x64/crossfirebase.dll` | 40 MB | yes（`.tvm0` 32 MB） | PACKED_OR_NO_HIT | 0 token |
| `x64/crossfire_x64base.dll` | 36 MB | `.tp6d`/`.tvm0` | no_hit | 0 token |
| `x64/server_x64.dll` | 1.7 MB | no | no_hit | |
| `rez/Object_x64.lto` | 1.2 MB | no | TOKEN | `NormalMap` 1 |
| `rez/Object.lto` | 0.8 MB | no | TOKEN | `NormalMap` 1 |

## 2. Format / path construction（A 的依据）

`x64/CShell_x64.dll` RVA `0x54C8F38`:

```text
modeltextures\SpecularMap\%s
```

周围明文：`playerview/..._s.dtx`、`modeltextures\playerview\...`

这是 **sprintf 路径构造**，和 N03-G 后期武器 `SpecularMapName → SpecularMap\*.dtx` 同一形态。黑骑士没有该 Bute 字段，所以这条串不能单独证明黑骑士走 SpecularMap。

`x64/crossfire.exe` RVA `0x5A12A0`:

```text
MODELTEXTURES\Shader\WeaponShader\
```

同簇还有 `NormalMap`、`AlphaMap`、`EnvCubeMap`、`tPlayerViewMesh`。这是目录前缀，**同一 NUL 串里没有 `%s.CFG`**。不能升格成 `WeaponShader\%s.CFG` 已证实。

## 3. 必须降级的命中

- `M4A1_S_BornBeast` 在 CShell 里是粒子名 `pv_vvip_m4a1_s_bornbeast2_reload_v3`，不是 CFG/材质绑定。
- CShell 里 `AlphaMap` 紧挨 UI `NUIBG_SUPERSOLDIER_TM.dtx`，不是武器 TGA 路径。
- CShell 里 `PViewSkinFileName` / `StandardName` / `SpecularMapName` / `LightCorrectionLegacyShader` 是 **Bute 字段名表**（和 N03-C/G dump 一致），证明 CShell 读这些 key，不是拼路径本身。

## 4. Remaining ambiguity

- 没有找到 `WeaponShader\%s.CFG` 或 `AlphaMap\%s_alpha.TGA`。
- `crossfirebase.dll` 有 Themida 风格 `.tvm0`，明文扫描空；不脱壳。
- 下一轮 N04-B 只应对 `modeltextures\SpecularMap\%s` 和 `MODELTEXTURES\Shader\WeaponShader\` 做有限 xref，不扫全 DLL。

**status**: `FORMAT_STRING_HIT`
