# Blender look-dev：游戏里 VMT 几乎不动的原因

日期：2026-09-19

游戏内 M1/M2/M6env/M4/M4b/M6phong 均已确认 pak 加载，画面几乎不变。用户要求先 Blender。

## 结论

**不是贴图解不出来。** Diffuse 偏暗；香槟金和金属层次在 **SpecularMap** 和 **cubemap** 里。CF 公式是相加：

`albedo*(0.01 + 0.2*N.L + 0.01) + spec*(N.H^0.25)*alpha.G + cube*3*alpha.B`

Diffuse 一项几乎是黑的。当前 CS:GO 第一人称上 Phong / `env_cubemap` 没有可见贡献，所以只能看见暗 Diffuse，看起来像橄榄金。

Blender 里加上 spec+env 之后，金框、天秤徽章、枪管金属明显亮起来。数据本身能做出目标，不是“本来就不行”。

## 产物

`work/mauser_libra/material_rendering_fix/blender_lookdev/`

| 文件 | 含义 |
|---|---|
| `unlit_three_quarter.png` | 只有 Diffuse，接近现在游戏 |
| `cf_additive_three_quarter.png` | CF 相加公式（spec+env） |
| `unlit_front.png` / `cf_additive_front.png` | 正视 |
| `cf_lookdev.blend` | 场景 |

对照：`material_v2/reference_cf/component_specular.png`（金几乎全来自 spec）、`component_diffuse_lit.png`（几乎全黑）。

Blender cubemap 采样是近似，有一些块状反射；软件参考渲染更干净。对比目的已经达到。

## 下一刀（转化到游戏）

不要再单独拧 Phong 指数/增益。要把 spec 能量送进这套 viewmodel **实际会画的通道**：

1. 全枪槽用天袭已验证的 Phong 写法（`phongalbedotint`、boost 8、无 alphamask）做一次“Phong 到底会不会亮”的总试验；或
2. 若仍无反应：把 spec（+有限 env）烘焙进 `$basetexture`，让游戏不靠 Phong 也能看见金色。
