# P4-M01-N03-H — BornBeast DTX vs later-era SpecularMap controls

- status: **SCOPED_NEGATIVE**
- confidence: **HIGH**
- completion: **C**
- P4-M01: still **INCOMPLETE**

本轮只回答：本机还有没有一张 **看起来像枪** 的原生 DTX。没有。

## 1. BornBeast size classes

22 个 `*BornBeast*.DTX`：

| family | size | count | meaning |
|---|---|---|---|
| `pv_bgr24_512x256_mip` | 524452 | 8 | headerless BGR24 512×256 full-mip + 163 B trailer |
| `qv_dxt1_256x256_plus_164` | 32932 | 10 | 32768+164；DXT1 假设未产出枪图 |
| `empty` | 0 | 4 | `PV-M82A1_*BornBeast*` 空文件 |

没有第三族（512×512 RGB / 标准 Jupiter 头 albedo）。

## 2. Official CFRezManager DTX header

16 个目标（QV/PV 黑骑士 + N03-G `SpecularMapName` 本地文件 + RoyalDragon PV 对照）全部：

```text
Unsupported or malformed DTX image
```

包括后期双贴图武器的 `SpecularMap\PV-M4A1_RoyalDragon_s.DTX`、`PV-RI_M4A1-S_s.DTX`。

当前客户端武器 DTX **不是** Jupiter `DtxThumbnailDecoder` 能认的 version magic（-2/-3/-5）。官方头解码不能当阳性对照。

## 3. Size-fit pixels（看图，不是文件名）

### 524452 族 = 能量/标量层，不是枪身 atlas

同一布局（BGR24 512×256 mip, offset 0）在对照武器上同样成立：

| file | mean_rgb | mean_sat | unique_q5 | visual |
|---|---|---|---|---|
| `PV-M4A1_S_BornBeast.DTX` | 255, 42, 134 | 213 | 271 | 品红能量膜 |
| `PV-M4A1_RoyalDragon.DTX` | 255, 255, 5 | 250 | 11 | 黄/青能量膜，隐约枪件轮廓 |
| `SpecularMap/PV-M4A1_RoyalDragon_s.DTX` | 23, 39, 255 | 243 | 696 | 蓝能量/标量 |

后期 `SpecularMapName` 指向的 `.dtx` 和黑骑士 PV 是 **同一容器、同一类像素**（高饱和单色层），不是 512 枪件 albedo。

### 32932 族 = 无枪 atlas

`QV-M4A1_S_BornBeast.DTX`：

| layout | leftover | visual |
|---|---|---|
| DXT1 256×256 off 0 / 164 | 164 / 0 | 棋盘噪声 |
| DXT5 256×128 / 128×256 | 164 | 棋盘噪声 |
| RGB565 128×128 / 256×64 | 164 | 细条噪声 |
| BGR24 112×98 / 128×85（size 非 3 整除，非 exact-fit） | n/a | 黄/青扫描条 |

同体积对照 `PV-M4A1-RoyalDragon_silencer.DTX` 同样是棋盘或扫描条，不是枪件岛。

`size % 3 == 1`，头 3 字节循环 `xx ff ff`，像 24-bit 单通道，但没有干净的 2 的幂尺寸。不能把 QV 升格成枪身 albedo。

### 131236 族

`PV-DualDE_GreenVein_S.DTX` DXT1 512×512 off 0/164（leftover 164）= 棋盘噪声。官方头同样失败。

## 4. Classification

```text
official Jupiter DTX header on weapon DTX     SCOPED_NEGATIVE (0/16)
BornBeast PV 524452 pixels                    scalar_or_energy (already known)
later SpecularMap / RoyalDragon 524452        scalar_or_energy (same container)
QV-M4A1_S_BornBeast 32932                     no gun atlas from size-fit
512x512 native gun albedo in *BornBeast*.DTX  SCOPED_NEGATIVE
```

## 5. Remaining ambiguity

- 524452 的 163 B trailer 语义未解；跳过 trailer 再解只是通道错位，仍是能量层。
- 32932 的真实 codec 未闭合（不是标准 DXT1/5，也不是精确 BGR24 mip）。
- 这不证明运行时第一人称不用 PV DTX；Bute 仍绑定它。只证明 **按现有解码，本机没有一张枪身 albedo**。
- 不把 CS1.6 / ComfyUI 图回写成 native。
- 不宣布 P4-M01 PASS。

关键预览：

```text
selected/bornbeast_pv_bgr24_512x256.png
selected/royaldragon_pv_bgr24_512x256.png
selected/royaldragon_s_bgr24_512x256.png
selected/bornbeast_qv_dxt1_256x256.png
```

**status**: `SCOPED_NEGATIVE`
