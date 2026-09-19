# 把 Blender/CF 金色转进游戏：spec 烘焙进 basetexture

日期：2026-09-19  
A/B：29/29  
pak：等 MIGI REBUILD

游戏里 Phong/`env_cubemap` 没有可见贡献。Blender 证明香槟金在 SpecularMap。本轮把 `clip(diffuse*0.25 + specular)` 写进共享 `$basetexture`，不靠 Phong 也能看见金色。

全枪槽 VMT 用天袭 A.8.1 写法（exponent 48 / boost 8 / phongalbedotint，无 envmap、无 alphamask）。Phong 若仍不亮，贴图本身已经是金的。

未改：模型、UV、法线、手膜、声音、位置/FOV。

烘焙预览：`work/mauser_libra/material_rendering_fix/bake_spec_to_base/cf_mauser_libra_baked_rgb.png`
