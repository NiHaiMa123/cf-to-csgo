# N05-E — Offline playerviewmesh.fxo inspect

Result: **FXO_EFFECT_ENUMERATED**. P4-M01 remains **INCOMPLETE**.

Source SHA256 `d1672ba7e0a0f5b69e6a9520ec4ba0c6d4fb08b435aff1f3a3110af408bfb99c`. N04-C SHA match=False (live `playerviewmesh.fxo` changed since N04-C). Load ok=True.

Exact CFG property names present as effect parameters: `SpecularPower`, `LightBrightness`, `DiffuseBoost`, `AmbientLightColor`, `EnvCubeMapBrightness`, `ReflectionIndex`, `RefractionIndex`. Sampler slots `DiffuseMap` / `SpecularMap` / `NormalMap` / `AlphaMap` / `CubeMap` exist. `CubeMapTransformY` has no effect name hit.

D3DX compiled defaults are **not** the BornBeast CFG values (`SpecularPower` 8 vs CFG 1, `LightBrightness` 1 vs 0.01, `EnvCubeMapBrightness` 0.05 vs 4, `ReflectionIndex` 0 vs 0.9). That is evidence the CFG is a per-weapon override, not that these defaults are what the client uses.

Parameters: 111. Techniques: 43.

## CFG name overlap

| CFG field | value | effect names |
|---|---|---|
| `Textures.SpecularMapName2` | `M4A1_S_BornBeast_S.tga` | `SpecularMap`, `SpecularMapSampler`, `SpecularMappingFactor` |
| `Textures.EnvCubeMapName2` | `Black_Shader03.dds` | `CubeMap`, `CubeMapSampler`, `EnvCubeMapBrightness`, `EnvCubeMappingFactor` |
| `Textures.NormalMapName2` | `M4A1_S_BornBeast_N.tga` | `NormalMap`, `NormalMapSampler`, `NormalMappingFactor` |
| `Textures.AlphaMapName2` | `M4A1_S_BornBeast_alpha.tga` | `AlphaMap`, `AlphaMap2`, `AlphaMapSampler`, `AlphaMapSampler2` |
| `Techniques.DiffuseMappingEnabled` | `1` | `DiffuseBoost`, `DiffuseMap`, `DiffuseMapSampler`, `DiffuseMappingFactor`, `GlobalDiffuseAlpha`, `MapEnableState`, `gLightDiffuse`, `gMaterialDiffuse` |
| `Techniques.SpecularMappingEnabled` | `1` | `MapEnableState`, `SpecularBacklighting`, `SpecularHighlight`, `SpecularLength`, `SpecularMap`, `SpecularMapSampler`, `SpecularMappingFactor`, `SpecularPower`, `gLightSpecular`, `gMaterialSpecular`, `gMaterialSpecularPower` |
| `Techniques.EnvCubeMappingEnabled` | `1` | `CubeMap`, `CubeMapSampler`, `EnvCubeMapBrightness`, `EnvCubeMappingFactor`, `MapEnableState`, `tPlayerViewMeshAlphaAproxSnellTransformedCube`, `tPlayerViewMeshAlphaAproxSnellTransformedCubeEmsv`, `tPlayerViewMeshAproxSnellTransformedCube`, `tPlayerViewMeshAproxSnellTransformedCubeEmsv`, `tRefractionModelAlphaAproxSnellTransformedCube`, `tRefractionModelAlphaAproxSnellTransformedCubeEmsv`, `tRefractionModelAproxSnellTransformedCube`, `tRefractionModelAproxSnellTransformedCubeEmsv` |
| `Techniques.NormalMappingEnabled` | `1` | `MapEnableState`, `NormalBoost`, `NormalMap`, `NormalMapSampler`, `NormalMappingFactor` |
| `Properties.LightBrightness` | `0.01` | `EnvCubeMapBrightness`, `GhostOverlayBrightness`, `LightBrightness` |
| `Properties.EnvCubeMapBrightness` | `4` | `CubeMap`, `CubeMapSampler`, `EnvCubeMapBrightness`, `EnvCubeMappingFactor`, `GhostOverlayBrightness`, `LightBrightness` |
| `Properties.SpecularPower` | `1` | `SpecularPower`, `gMaterialSpecularPower` |
| `Properties.DiffuseBoost` | `0.1` | `DiffuseBoost` |
| `Properties.AmbientLightColor` | `0.01` | `AmbientLightColor`, `gDefaultAmbient`, `gLightAmbient`, `gMaterialAmbient` |
| `Properties.RefractionIndex` | `0.01` | `RefractionIndex`, `RefractionParam`, `tRefractionModel`, `tRefractionModelAlpha`, `tRefractionModelAlphaAproxSnell`, `tRefractionModelAlphaAproxSnellEmsv`, `tRefractionModelAlphaAproxSnellTransformedCube`, `tRefractionModelAlphaAproxSnellTransformedCubeEmsv`, `tRefractionModelAlphaEmsv`, `tRefractionModelAlphaRefract`, `tRefractionModelAlphaRefractEmsv`, `tRefractionModelAproxSnell`, `tRefractionModelAproxSnellEmsv`, `tRefractionModelAproxSnellTransformedCube`, `tRefractionModelAproxSnellTransformedCubeEmsv`, `tRefractionModelEmsv`, `tRefractionModelGhostShaderWepon`, `tRefractionModelGhostShaderWeponEmsv`, `tRefractionModelGhostShaderWeponTexturePanning`, `tRefractionModelGhostShaderWeponTexturePanningEmsv`, `tRefractionModelRefract`, `tRefractionModelRefractEmsv` |
| `Properties.ReflectionIndex` | `0.9` | `ReflectionIndex` |
| `Properties.EnvCubeUsage` | `2` | `CubeMap`, `CubeMapSampler`, `EnvCubeMapBrightness`, `EnvCubeMappingFactor` |
| `Properties.CubeMapTransformY` | `-20` | — |

## Limitations

- D3DX default values are not BornBeast runtime selection.
- Name overlap is not a sampler binding proof.
- This harness does not attach CrossFire or ACE.
- Raw FXO stays in data/n05e_fxo and is not committed.
