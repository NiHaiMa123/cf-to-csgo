# P4-M01-N04-C — playerviewmesh.fxo metadata

- status: **FXO_NAMES_GENERIC**
- completion: **B**
- P4-M01: still **INCOMPLETE**

未脱壳、未反编译指令流、未提交 `.fxo`。SHA 对上 N02-A inventory。

## 1. Container

`rez/Shader/playerviewmesh.fxo` 1,193,704 B，头 `01 09 ff fe`，**不是 DXBC**。明文 technique 名带 `_3_0`，按 D3D9 compiled effect 处理。无 LZMA 外壳。

对照 `playermesh.fxo` 118,048 B，同样头、同样有 Alpha/Normal/Specular sampler，没有武器路径。

`path_like`：**空**。没有 `WeaponShader\`、`.CFG`、`.TGA`。

## 2. Sampler / technique 名（OBSERVED）

贴图槽：

```text
DiffuseMap / DiffuseMapSampler
SpecularMap / SpecularMapSampler
NormalMap / NormalMapSampler
AlphaMap / AlphaMapSampler
AlphaMap2 / AlphaMapSampler2
OverlayMap / MaskMap / NoiseMap / CubeMap
```

第一人称 technique 前缀 `tPlayerViewMesh*`，含：

```text
tPlayerViewMesh
tPlayerViewMeshEmsv          (emissive)
tPlayerViewMeshAlpha
tPlayerViewMeshTexturePanning
tPlayerViewMeshGhostShader
```

参数：`SpecularPower`、`EmissiveMapIntensity`、`MapEnableState`、`TexturePanningVelocityU/V`。

## 3. 能说 / 不能说

能说：第一人称 shader **有** Alpha/Normal/Specular/Emissive 槽；引擎若绑定 TGA/DTX，会进这些 sampler。Emissive technique 与 PV DTX 能量层 **相容**（仍是 HYPOTHESIS）。

不能说：FXO 会按 `WeaponShader\%s.CFG` 或 `AlphaMap\%s_alpha.TGA` 去读文件。路径构造仍不在这份 FXO 明文里。`crossfire.exe` 的 WeaponShader 目录前缀仍然 0 code xref。

## 4. Remaining

- packed `crossfire.exe` 仍是 WeaponShader CFG 加载的缺口（另开口脱壳/运行时 dump）。
- 不宣布 P4-M01 PASS。

**status**: `FXO_NAMES_GENERIC`
