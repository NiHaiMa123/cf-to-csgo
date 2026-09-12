# N05-K — Offline FXO preview with BornBeast CFG

Result: **FXO_CFG_PREVIEW_RENDERED**. P4-M01 remains **INCOMPLETE**.

Technique `tPlayerViewMeshAlphaAproxSnellTransformedCube` pass 0. FXO SHA match=True. Cube SHA match=True.

Two shots on the same mesh/maps/camera: D3DX compiled defaults vs BornBeast CFG scalars.

CFG shot shows a solid black-knight body with serial and beast-head reds. Defaults look washed. CFG values change the picture; they still must not be copied into Source VMT.

- `d3dx_defaults`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\d3dx_defaults.png`
- `bornbeast_cfg`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\bornbeast_cfg.png`

## Limitations

- Self-built D3D9 device, not CrossFire runtime.
- Technique is still the EnvCubeUsage=2 name-level hypothesis.
- Camera/light are studio values, not CF's live light list.
- Rest-pose unskinned OBJ; hands omitted.
- CFG scalars were applied to this effect, not copied into Source VMT.
- Not a P4-M01 PASS.
