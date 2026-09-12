# N05-G — Blender native preview

Result: **BLENDER_NATIVE_PREVIEW_SHOWN**. P4-M01 remains **INCOMPLETE**. `final_cf_material=false`. Frozen addon untouched, not deployed.

Live Blender MCP `127.0.0.1:9876` (Blender 5.2.1 LTS) now shows the verified PV LTB with N05-F recovered maps in EEVEE Rendered view.

| Item | Path |
|---|---|
| Blend | `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05g_blender_native_preview/n05g_bornbeast_native_preview.blend` |
| Gun 3/4 | `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05g_blender_native_preview/n05g_viewport_gun.png` |
| Rest-pose + hands | `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05g_blender_native_preview/n05g_viewport.png` |
| Mesh | `data/n05d_binding/obj_export/PV-M4A1_S_BornBeast.obj` (N05-D raw transform, 11 piece / 5342 tri) |
| Maps | N05-F `_png/{diffuse,normal,specular,alpha}.png` |

Visible on the gun shot: carry-handle serial `M4A1SSQ00083`, beast-head handguard, suppressor red ring. Hands share the same 1024 PV atlas and are rest-pose (not animated); they start hidden in the live view.

Not proven: piece→sampler runtime, CFG scalars as Source phong, alpha convention, cubemap lighting. This is a Blender look, not P4-M01 PASS.
