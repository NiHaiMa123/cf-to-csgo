# N05-K — Offline FXO preview with BornBeast CFG

Result: **FXO_CFG_PREVIEW_RENDERED**. P4-M01 remains **INCOMPLETE**.

Hardware D3D9 rendered hypothesized technique `tPlayerViewMeshAlphaAproxSnellTransformedCube` pass 0 on the verified PV weapon OBJ (4008 tri, hands omitted) with recovered Diffuse/Normal/Specular/Alpha and the SHA-matching `Black_Shader03` cube.

Two shots, same camera/mesh/maps:

- `d3dx_defaults.png` — compiled effect defaults (`LightBrightness=1`, `SpecularPower=8`, `AmbientLightColor=0.2`, `ReflectionIndex=0`). Darker, washed, red spec still visible.
- `bornbeast_cfg.png` — BornBeast CFG scalars (`LightBrightness=0.01`, `SpecularPower=1`, `DiffuseBoost=0.1`, `AmbientLightColor=0.01`, `EnvCubeMapBrightness=4`, `ReflectionIndex=0.9`). Solid black-knight body, serial `M4A1SSQ00083`, beast-head reds.

CFG values change the look. They still must not be copied as Source 1 `$phongexponent` / `$envmaptint`. Studio camera/light are not CF's live light list. Technique selection remains name-level. Not PASS.

Technique `tPlayerViewMeshAlphaAproxSnellTransformedCube` pass 0. FXO SHA match=True. Cube SHA match=True.

Two shots on the same mesh/maps/camera: D3DX compiled defaults vs BornBeast CFG scalars.

- `d3dx_defaults`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\d3dx_defaults.png`
- `bornbeast_cfg`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\bornbeast_cfg.png`

## Limitations

- Self-built D3D9 device, not CrossFire runtime.
- Technique is still the EnvCubeUsage=2 name-level hypothesis.
- Camera/light are studio values, not CF's live light list.
- Rest-pose unskinned OBJ; hands omitted.
- CFG scalars were applied to this effect, not copied into Source VMT.
- Not a P4-M01 PASS.
