# N05-K — Offline FXO preview with BornBeast CFG

Result: **FXO_CFG_PREVIEW_RENDERED**. P4-M01 remains **INCOMPLETE**.

Technique `tPlayerViewMeshAlphaAproxSnellTransformedCube` pass 0. FXO SHA match=True. Cube SHA match=True.

CFG `LightBrightness=0.01` makes `bornbeast_cfg.png` a near-silhouette (gun pixel median ~13). That file is not for identity inspection.

`maps_on_mesh_studio.png` uses studio lights (not CFG) so the recovered maps can actually be seen. Crop is `maps_on_mesh_studio_crop.png`.

- `d3dx_defaults`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\d3dx_defaults.png`
- `bornbeast_cfg`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\bornbeast_cfg.png`
- `maps_on_mesh_studio`: `D:\project\cf_to_csgo\work\m4a1_s_bornbeast\p4_m01_native_material\runtime_acquisition\n05k_fxo_cfg_preview\maps_on_mesh_studio.png`

## Limitations

- Self-built D3D9 device, not CrossFire runtime.
- Technique is still the EnvCubeUsage=2 name-level hypothesis.
- Camera/light are studio values, not CF's live light list.
- Rest-pose unskinned OBJ; hands omitted.
- CFG scalars were applied to this effect, not copied into Source VMT.
- Not a P4-M01 PASS.
