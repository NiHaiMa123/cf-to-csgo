# CF Material Reconstruction v2 — 执行计划

> 目标：重构 CF → CS:GO Legacy 的贴图/材质转换链。停止继续在当前单一 `VertexLitGeneric` 代理方案上做 m8/m9 式经验参数微调，先把 CF 原材质语义恢复正确，再设计 Source 1 可审计的降级表达。
>
> 首个验证样本：`M1896_Libra / 毛瑟-天秤座`。
>
> 执行 Agent：SWE2。
>
> 本计划是当前活任务执行文档。完成后，把真正验证通过、可跨武器复用的规则并入 `pipeline.md`；单武器证据继续保存在 `work/<weapon>/`。

---

## 0. 背景与当前问题

当前毛瑟材质已识别为：

```text
player_view_alpha_snell_transformed_cube
```

现有转换链位于：

```text
scripts/material_recovery/cf_source_material.py
work/mauser_libra/texture/build_textures.py
```

当前 m7 近似为：

```text
diffuse  -> lightwarp
specular -> Source Phong
cubemap * Alpha.B -> emissiveblend 静态加法层
```

游戏内已验证：

- 直接把 CF cubemap 接 Source `$envmap`：采样射线不等价，出现错误纹路、噪点、洗白；
- spec/env 能量合并到 Phong：整体过暗且高频纹路错误；
- `$selfillum` / `$lightwarp` 不能承担 CF 独立环境反射项；
- 当前 `$emissiveblend` 代理层颜色/能量错误；
- 继续调整 `SOURCE_PROXY_GAIN`、`SOURCE_ENV_PROXY_GAIN` 等全局经验常量，没有证明能收敛到 CF 原材质。

因此本轮不再把“调 Source VMT 参数直到看起来差不多”当主路线。

---

# 1. 总目标

建立可复用的：

```text
CF raw assets
  -> verified decode
  -> Material IR
  -> CF reference shader / reference renderer
  -> CF semantic validation gate
  -> Source 1 material translator
  -> optional multi-material mesh split
  -> Source VTF/VMT
  -> runtime validation
```

必须明确区分两个问题：

### Gate A — CF 材质解释是否正确

回答：

> 使用 CF 原始 diffuse / normal / specular / alpha / cubemap / CFG，按恢复出的 CF shader 语义渲染，是否能得到自洽、可信的原始材质表现？

Gate A 不通过时：

- 禁止继续调 Source VMT；
- 禁止用 Source 游戏截图反推 CF shader 参数；
- 回到 CFG / shader family / 通道语义 / cubemap 采样模型继续调查。

### Gate B — Source 1 降级是否合理

Gate A 通过后才回答：

> 已知 CF 原材质行为后，Source 1 该如何用一组可审计的近似表达最大程度保留颜色、材质区域、金属层次和发光关系？

Gate B 可以允许近似，但近似必须明确记录损失。

---

# 2. 非目标 / 禁止项

本轮默认**不做**：

1. 不重写 REZ 分片读取逻辑。
2. 不重写 DTX 解码器。
3. 不修改全局 UV 规则。
4. 不因为材质看起来不对就假设贴图解码错。
5. 不继续对毛瑟 m7 直接做 m8/m9 参数微调。
6. 不用游戏截图量像素来反推材质常量。
7. 不把一把武器强制压成一个 VMT。
8. 不让 AI 超分直接修改 normal/spec/mask 的数值语义。
9. 不引入武器专属 magic number 来假装“通用转换器”。
10. 不改模型位置、动画、声音和已收敛的 VIEW 拟合。

只有出现独立证据证明底层解码错误，才允许修改 REZ/DTX/UV 层。

---

# 3. 必须继承的已验证事实

## 3.1 资产读取

继续使用：

```text
scripts/material_recovery/rez_verified_payload.py
read_verified_payload(...)
```

所有原资产必须保留来源、MD5/SHA-256 与 REZ 分片证据。

## 3.2 UV

当前通用规则仍为：

```text
Source/Blender: v_source = 1 - v_raw
```

只翻一次。

不要因为材质结果异常而排列组合 UV。

## 3.3 屠龙教训

`Kukri_Beast` 已证明：

- 原 diffuse 可以是正确的；
- UV dump 也可以是正确的；
- 但如果选择错误的 LTB variant / mesh，贴图仍会完全错位；
- `PV-Kukri_Beast_GR.LTB/Object066` 与 diffuse 匹配，而无后缀旧 mesh 不匹配。

因此每个材质样本进入 Material Reconstruction 前，必须先有：

```text
mesh <-> UV <-> diffuse compatibility gate
```

此 Gate 用无光照/Emission 方式验证，不用 Phong/envmap 干扰判断。

---

# 4. 新架构

## 4.1 Material IR

新增通用中间表示，建议：

```text
scripts/material_recovery/material_ir.py
```

Material IR 至少包含：

```json
{
  "material_id": "...",
  "shader_family": "...",
  "source_assets": {
    "diffuse": "...",
    "normal": "...",
    "specular": "...",
    "alpha": "...",
    "cubemaps": []
  },
  "cfg": {
    "techniques": {},
    "properties": {}
  },
  "channel_semantics": {
    "alpha_r": "...",
    "alpha_g": "...",
    "alpha_b": "...",
    "alpha_a": "...",
    "specular_rgb": "..."
  },
  "sampling_semantics": {
    "cubemap_usage": 0,
    "reflection_index": 0.0,
    "refraction_index": 0.0,
    "cube_transform": {}
  },
  "evidence": {},
  "confidence": {}
}
```

要求：

- observed / inferred / approximated 分开；
- 不允许把“文件名叫 SpecularMap”直接等同于 Source specular mask；
- 每个通道都输出 min/max/mean/percentiles；
- 保存输入文件 SHA-256；
- 保存 CFG 原始值和解析值；
- shader family 分类必须可追踪。

---

# 5. Phase A — 毛瑟原资产审计

目录：

```text
work/mauser_libra/material_v2/
```

建立：

```text
material_v2/
├─ audit/
├─ ir/
├─ reference/
├─ segmentation/
├─ source/
└─ reports/
```

## A1. 输入闭包

确认并记录：

```text
PV-M1896_Libra.DTX
M1896_Libra.CFG
M1896_Libra_S.TGA
M1896_Libra_N.TGA
M1896_Libra_alpha.TGA
LobbyCube.DDS
对应 LTB mesh / UV
```

产物：

```text
material_v2/audit/input_manifest.json
```

内容必须包括：

- REZ path；
- verified payload hash；
- decoded output hash；
- 分辨率、格式、通道数；
- CFG 原文 hash；
- cubemap 面数、顺序、mip 信息。

### A1 Gate

所有输入可追溯、hash 完整，否则停止。

---

## A2. Mesh / UV / diffuse compatibility

做一个完全不受灯光影响的离线渲染：

```text
Emission(diffuse)
```

至少输出：

- 正常 UV 结果；
- UV 岛覆盖图；
- mesh triangle -> atlas 区域可视化；
- 关键零件 close-up。

不要测试 8 种 UV 排列组合，默认只验证现行 `(u, 1-v)`。

如果出现类似屠龙的明显错贴：

1. 搜索同族 BL/GR/WOMAN/socket variant；
2. 对比 mesh 顶点数 / triangle / UV；
3. 找与 diffuse 实际匹配的 variant；
4. 记录 runtime 选模仍未知时的限制。

产物：

```text
material_v2/audit/mesh_uv_diffuse_report.json
material_v2/audit/emission_reference.png
```

### A2 Gate

必须先证明 mesh/UV/diffuse 基础映射可信。

---

# 6. Phase B — CF Material IR

## B1. CFG 完整解析

不要只提取当前几个字段。

完整解析：

```text
[Techniques]
[Properties]
以及 CFG 中其它实际 section
```

对毛瑟至少明确：

```text
SpecularMappingEnabled
EnvCubeMappingEnabled
NormalMappingEnabled
EnvCubeUsage
ReflectionIndex
RefractionIndex
CubeMapTransformY
LightBrightness
DiffuseBoost
AmbientLightColor
EnvCubeMapBrightness
SpecularPower
```

不得在这一步映射到 Source 参数。

---

## B2. 通道审计

对：

```text
Diffuse RGB/A
Specular RGB/A
Alpha R/G/B/A
Normal RGB/A
Cubemap 6 faces
```

输出：

- histogram；
- percentiles；
- spatial preview；
- channel correlation；
- 稀疏度；
- 与 diffuse 的区域相关性；
- Alpha 各通道是否常量。

毛瑟当前已知：

```text
Alpha.R ≈ 255 constant
Alpha.G ≈ 255 constant
Alpha.B = spatial mask
```

必须重新从原图验证，不直接继承旧报告结论。

产物：

```text
material_v2/ir/m1896_libra.material_ir.json
material_v2/reports/channel_audit.json
material_v2/reports/channel_sheet.png
```

---

# 7. Phase C — CF Reference Shader

这是本轮核心。

新增独立 reference shader / renderer，不依赖 Source 1。

实现位置可选：

```text
scripts/material_recovery/cf_reference_renderer.py
```

或 Blender headless shader graph。

优先目标不是“漂亮”，而是准确表达已知 CF 语义。

## C1. 首版公式

基于当前已有证据，实现：

```text
out.rgb =
    diffuse_lit
  + SpecularMap.rgb * spec_term * Alpha.G
  + CubeSample.rgb * EnvCubeMapBrightness * Alpha.B
```

并显式接入：

```text
SpecularPower
LightBrightness
DiffuseBoost
AmbientLightColor
ReflectionIndex
RefractionIndex
CubeMapTransformY
EnvCubeUsage
```

其中未知公式不得暗中拍脑袋补齐。

必须标记：

```text
OBSERVED
INFERRED
UNKNOWN
APPROXIMATED_FOR_REFERENCE
```

---

## C2. Cubemap 采样

不得再：

```text
mean(cubemap RGB)
```

代替反射。

必须真正按方向采样 cubemap。

至少支持：

- view direction；
- surface normal；
- reflection vector；
- refraction vector；
- ReflectionIndex / RefractionIndex；
- CubeMapTransformY；
- CF 坐标约定的可配置 axis transform。

输出固定测试球 / 平面 / 实际枪模三类 reference。

---

## C3. Reference sweep

建立固定相机与固定灯光测试集：

```text
front-lit
side-lit
back/dark
neutral studio
rotated view
```

所有测试用同一组输入，不做逐场景手调。

产物：

```text
material_v2/reference/reference_manifest.json
material_v2/reference/*.png
```

### Gate A

通过条件：

1. diffuse 区域颜色稳定；
2. specular 只出现在合理区域；
3. cubemap 响应随视角/法线变化，而不是静态贴色；
4. Alpha.B 的环境反射区域作用自洽；
5. 不出现旧 Source 方案那种固定 UV 反射纹；
6. 所有未知项在报告中明确标记。

如果 Gate A 不通过：

> 停止 Source translator 开发，继续 CF shader 研究。

---

# 8. Phase D — 材质区域分割

Gate A 通过后，建立 Source 降级所需的区域分类。

目标不是 AI 语义分割，而是优先利用原始资产：

```text
diffuse chroma
specular energy / chroma
Alpha masks
normal variance
shader response
mesh connectivity
UV island
```

生成候选类别：

```text
dark_metal
bright/gold_metal
painted_surface
glow/emissive
dielectric/plastic
other
```

类别数量不固定，也不要强制毛瑟一定有全部类别。

## D1. Triangle material classification

最终目标是：

```text
triangle -> material_region_id
```

流程建议：

1. 在 UV 中计算每个 triangle 覆盖区域；
2. 统计该 triangle 的 diffuse/spec/alpha/reference-response；
3. 先按 UV island / mesh piece 保持局部连续；
4. 再按材质特征聚类；
5. 小孤岛做邻域合并；
6. 不允许切碎到大量微型 material slot。

输出：

```text
material_v2/segmentation/triangle_materials.json
material_v2/segmentation/region_preview.png
```

### D Gate

要求：

- 区域边界基本跟真实零件/纹理区域一致；
- 不出现大量单三角噪声；
- 能明确解释为什么某区域是 metal/glow/paint。

---

# 9. Phase E — 纹理高清化 v2

## E1. Diffuse

允许 AI upscale，但必须：

- 原始 diffuse 保留；
- 4x 只作为中间结果；
- 最终通常 2048；
- 对比输入/输出，防止改花纹、文字、边界；
- 最终 Source 主 diffuse 优先 BGRA8888。

如果分区差异明显，可以按区域处理后合成 atlas，但必须保留原 UV。

---

## E2. Normal

禁止 RealESRGAN。

流程：

```text
resize
-> decode normal vector
-> interpolate
-> renormalize XYZ
-> encode
```

输出 normal validity 报告。

---

## E3. Specular / Alpha / masks

禁止生成式 AI。

采用：

- bicubic / Lanczos；
- edge-aware resize；
- 必要时低通；
- 保留数值分布；
- 记录 resize 前后 histogram 差异。

特别是 mask 不得因为“看起来更锐”而改变面积比例。

---

# 10. Phase F — Source 1 Translator v2

新增通用转换模块，建议：

```text
scripts/material_recovery/source1_material_translator.py
```

输入：

```text
Material IR
CF reference response
triangle material regions
```

输出：

```text
Source VTF/VMT set
triangle -> Source material slot
translation_report.json
```

原则：

> 不再要求一个 CF shader family 必须压成一个 Source VMT。

允许：

```text
cf_mauser_darkmetal.vmt
cf_mauser_gold.vmt
cf_mauser_paint.vmt
cf_mauser_glow.vmt
```

---

## F1. Source 材质策略

按区域选择最简单稳定的表达：

### dark / colored metal

优先：

```text
VertexLitGeneric
+ basetexture
+ bumpmap
+ controlled Phong
+ optional albedo tint
```

不要默认 envmap。

### bright/gold metal

可测试：

```text
colored Phong
或
经过 Gate 验证的低强度 envmap
```

只有 cubemap 方向、mip、动态明暗都通过时才允许 runtime `$envmap`。

### glow

只在确有稀疏发光证据时：

```text
$selfillum
或独立 material
```

不要拿 selfillum 当“环境稳定层”。

### CF transformed Snell/cube

Source 无法等价时：

- 明确降级；
- 优先区域化近似；
- 不把 CF cubemap 平均颜色做成整层静态 emissive 假装等价。

---

# 11. Phase G — 模型多材质写出

扩展毛瑟 native VM 构建器。

要求：

1. 几何、骨架、动画、VIEW 全不变；
2. 只修改 triangle material assignment；
3. SMD 中按 region 写多个 material name；
4. 编译后验证 triangle count / vertex positions / bind / animation hash 或数值一致；
5. 不因为材质拆分改变 mesh 空间位置。

产物：

```text
work/mauser_libra/material_v2/source/material_assignment.json
work/mauser_libra/material_v2/source/compile_audit.json
```

### G Gate

材质拆分前后：

- 顶点位置不变；
- UV 不变；
- skin weights 不变；
- animation 不变；
- 仅 material slot 改变。

---

# 12. Phase H — 离线 Source 对比

不要直接进游戏盲测。

建立固定对比：

```text
CF reference render
vs
Source approximation render / preview
```

对比维度：

- base color；
- dark-region retention；
- gold/metal hue；
- highlight continuity；
- glow locality；
- view-dependent response；
- shadow behavior。

报告必须区分：

```text
preserved
approximated
lost
unsupported_by_source1
```

输出：

```text
material_v2/reports/source_translation_report.json
material_v2/reports/reference_vs_source_sheet.png
```

---

# 13. Phase I — 游戏部署验证

只有 A-H 全部通过才部署。

遵守现有三层门禁：

```text
A work/mauser_libra/addon
-> B MIGI addon
-> user MIGI REBUILD
-> C pak
```

要求：

1. A/B manifest + SHA-256 一致；
2. 用户执行 MIGI REBUILD；
3. 可读取时验证 B/C SHA-256；
4. 再进行明/暗两种环境的游戏截图验收。

本轮游戏验收只评价材质，不修改：

- VIEW；
- 动画；
- sounds；
- attachment。

---

# 14. 验收标准

## 必须通过

- [ ] 原始资产闭包完整且 hash 可追溯
- [ ] mesh/UV/diffuse compatibility 通过
- [ ] Material IR 可重建且不含隐藏 magic number
- [ ] CF reference shader 真正方向采样 cubemap
- [ ] Gate A 通过后才进入 Source translator
- [ ] normal/spec/mask 未经生成式 AI 改写
- [ ] Source 允许多 material slot
- [ ] 多材质拆分不改变几何/骨架/动画
- [ ] Source translator 输出损失报告
- [ ] A/B hash 通过
- [ ] 用户 REBUILD 后再做 runtime 判定

## 毛瑟首轮成功标准

不要求 Source 1 100% 复现 CF。

要求：

1. 不再出现 m7 的明显整体偏色；
2. 暗色主体不能被洗白；
3. 金色/高光区域与原材质区域一致；
4. 高光不应把整张 `_S` 高频纹理直接投成反射噪声；
5. 环境响应不能是固定 UV 贴色；
6. 明暗环境下都保持基础颜色可辨；
7. 无新增 UV 错位、normal 错向或 mesh 变化。

---

# 15. 停止条件

出现以下情况立即停当前阶段并报告，不跨阶段硬做：

1. 原资产 hash / provenance 不完整；
2. mesh/UV/diffuse 不匹配且 variant 尚未确认；
3. CF reference shader 无法解释主要通道行为；
4. 必须靠武器专属 magic number 才能继续；
5. Source 多材质拆分改变了模型空间/动画结果；
6. A/B/C 部署链 hash 不一致；
7. 游戏没有变化但尚未完成 pak 内容验证。

---

# 16. 代码组织要求

通用代码放：

```text
scripts/material_recovery/
```

建议最终至少有：

```text
material_ir.py
cf_reference_renderer.py
source1_material_translator.py
```

毛瑟专属执行/证据放：

```text
work/mauser_libra/material_v2/
```

禁止把毛瑟专属阈值硬编码到通用模块。

如确需阈值，必须：

- 由输入统计推导；或
- 放进 weapon-local config；
- 在报告中说明来源。

---

# 17. SWE2 执行顺序

严格按：

```text
A1 -> A2
-> B1 -> B2
-> C1 -> C2 -> C3
-> Gate A
-> D
-> E
-> F
-> G
-> H
-> I
```

不要跳过 Gate A 直接继续 Source VMT 调参。

每完成一个 Phase：

1. 更新本 `plan.md` 对应状态；
2. 保存 evidence；
3. 跑该阶段的离线验证；
4. 只提交本阶段相关文件；
5. push master；
6. 再进入下一阶段。

状态格式：

```text
TODO
ACTIVE
PASS
BLOCKED
REJECTED
```

---

# 18. 当前状态

```text
A1  TODO
A2  TODO
B1  TODO
B2  TODO
C1  TODO
C2  TODO
C3  TODO
Gate A TODO
D   TODO
E   TODO
F   TODO
G   TODO
H   TODO
I   TODO
```

当前第一步：

> 从 `M1896_Libra` 原始资产重新建立 `material_v2/audit/input_manifest.json`，并做 mesh/UV/diffuse Emission compatibility 验证。不要修改当前已部署 m7 材质。
