# CF Material Reconstruction v2 — 通用执行计划

> 目标：建立一套可跨武器复用的 CF → CS:GO Legacy 材质重建与降级转换框架。
>
> 本计划不是“毛瑟专用修复”。`M1896_Libra / 毛瑟-天秤座`只是首个 reference implementation，用来把通用框架完整跑通。
>
> 执行 Agent：SWE2。
>
> 完成后，真正验证通过、可跨武器复用的规则并入 `pipeline.md`；单武器证据继续保存在 `work/<weapon>/`。

---

# 0. 核心原则

本项目以后处理的不是“贴图转换”，而是“材质转换”。

统一目标：

```text
CF raw assets
  -> verified decode
  -> mesh/UV compatibility
  -> Material IR
  -> CF reference shader
  -> CF semantic validation
  -> material-region analysis
  -> Source 1 translator
  -> optional multi-material mesh split
  -> Source VTF/VMT
  -> offline comparison
  -> CSGO runtime validation
```

必须始终分清三个层级：

### Truth 1 — CF material truth

回答：

> CF 原始 mesh / UV / diffuse / normal / specular / alpha / cubemap / CFG 在原 shader 语义下应该表现成什么样？

### Preview — Blender / offline renderer

回答：

> 我们对 CF shader 的理解是否自洽？Source 降级方案是否存在明显错误？

Blender 只是实验台和离线验证环境。

**Blender is NOT Source 1 ground truth.**

### Truth 2 — CSGO runtime truth

回答：

> Source 1 / CS:GO Legacy 实际运行时最终渲染成什么样？

最终验收只以 CSGO runtime 为准。

---

# 1. 当前问题与为什么需要 v2

现有材质转换链：

```text
scripts/material_recovery/cf_source_material.py
work/<weapon>/texture/*.py
```

已经能处理部分 diffuse / Phong / normal / glow，但复杂 CF shader 仍存在明显问题。

以首个 reference weapon `M1896_Libra` 为例，其材质当前识别为：

```text
player_view_alpha_snell_transformed_cube
```

现有近似：

```text
diffuse  -> lightwarp
specular -> Source Phong
cubemap * Alpha.B -> emissiveblend 静态加法层
```

已知失败：

- CF cubemap 直接接 Source `$envmap` 时，采样模型不等价；
- 会出现错误反射纹、噪点、洗白；
- spec/env 能量硬塞进 Phong 会丢失原材质结构；
- `$selfillum` / `$lightwarp` 不能等价承担 CF 独立环境反射项；
- 静态 emissive cubemap proxy 会产生颜色与能量失真；
- 继续微调 `SOURCE_PROXY_GAIN`、`SOURCE_ENV_PROXY_GAIN` 一类常量，没有证明可形成跨武器通用解。

所以 v2 不再以：

> “继续调 VMT 参数，直到当前一把枪看起来差不多”

作为主路线。

---

# 2. 通用性边界

本框架必须能够支持不同 CF 武器和不同 shader family。

首个 reference implementation：

```text
M1896_Libra / 毛瑟-天秤座
```

后续应能够复用到：

```text
M4A1-雷神
Galil ACE-天袭
Kukri_Beast / 屠龙
其它 CF PlayerView 武器
```

通用代码不得依赖：

- 毛瑟文件名；
- 毛瑟专属参数；
- 固定 Alpha 通道语义；
- 固定 metal/glow 分类数量；
- 固定 Source VMT 数量；
- 固定 shader family。

毛瑟专属证据只允许放：

```text
work/mauser_libra/material_v2/
```

通用代码放：

```text
scripts/material_recovery/
```

---

# 3. 非目标 / 禁止项

默认禁止：

1. 不重写 REZ 分片读取逻辑。
2. 不重写 DTX 解码器。
3. 不修改全局 UV 规则。
4. 不因为“看起来不对”就推断贴图解码错。
5. 不继续对旧 m7 做 m8/m9 式经验参数迭代。
6. 不用 CSGO 截图反推 CF shader 常量。
7. 不要求“一把枪 = 一个 VMT”。
8. 不让生成式 AI 修改 normal/spec/mask 数值语义。
9. 不把武器专属 magic number 塞进通用转换器。
10. 不因为材质任务修改 VIEW、动画、声音、attachment。
11. 不把 Blender Principled BSDF 的参数机械映射成 Source VMT。
12. 不因为 Blender 看起来正确就声称 CSGO runtime 已正确。

只有独立证据证明底层 decode 错误时，才允许修改 REZ / DTX / UV 层。

---

# 4. 必须继承的已验证规则

## 4.1 Verified asset provenance

继续使用：

```text
scripts/material_recovery/rez_verified_payload.py
read_verified_payload(...)
```

所有原资产必须保留：

- REZ path；
- shard；
- MD5；
- SHA-256；
- decoded output hash。

---

## 4.2 UV

当前通用规则：

```text
v_source = 1 - v_raw
```

只翻一次。

不要在材质失败后排列组合 UV。

---

## 4.3 Mesh / UV / texture compatibility

屠龙已证明：

- diffuse 可以正确；
- UV dump 也可以正确；
- 但如果拿错 LTB variant / mesh，最终仍会完全错贴。

因此每个武器进入材质重建前都必须通过：

```text
mesh <-> UV <-> diffuse compatibility gate
```

该 Gate 必须用无光照 Emission 方式验证。

如果失败：

1. 查同族 BL / GR / WOMAN / socket variants；
2. 对比 vertex / triangle / UV；
3. 找与 diffuse 匹配的 mesh；
4. 不修改全局 UV decoder 来掩盖 variant 选错。

---

# 5. 通用目录结构

每把武器统一：

```text
work/<weapon>/material_v2/
├─ audit/
├─ ir/
├─ reference_cf/
├─ segmentation/
├─ upscale/
├─ source/
├─ preview_source/
└─ reports/
```

首个 reference implementation：

```text
work/mauser_libra/material_v2/
```

---

# 6. Phase A — 输入与 Mesh/UV 审计

## A1. 输入闭包

对当前武器收集其实际存在的：

```text
LTB mesh / UV
Diffuse
Normal
Specular
Alpha / mask
Cubemap
CFG
其它 overlay / material map
```

不是所有武器都要求每一种资源存在。

产物：

```text
work/<weapon>/material_v2/audit/input_manifest.json
```

必须记录：

- verified source path；
- file hash；
- decoded hash；
- image size / format / channels；
- cubemap face / mip metadata；
- CFG hash；
- mesh identity。

### A1 Gate

输入 provenance 不完整则停止。

---

## A2. Mesh / UV / diffuse compatibility

使用 Blender headless 或独立离线 renderer：

```text
Emission(diffuse)
```

输出：

```text
audit/emission_reference.png
audit/uv_overlay.png
audit/mesh_uv_diffuse_report.json
```

至少检查：

- atlas 是否落在合理部件；
- UV seam 是否连续；
- 关键图案是否落在正确零件；
- triangle 是否大量采到黑底/错误区域。

### A2 Gate

必须先确认几何和 diffuse 的基础映射可信。

A2 不通过：

> 禁止继续研究 shader。

---

# 7. Phase B — Material IR

新增通用模块：

```text
scripts/material_recovery/material_ir.py
```

Material IR 是整个 v2 的核心中间表示。

最低字段：

```json
{
  "material_id": "...",
  "shader_family": "...",
  "source_assets": {},
  "cfg": {
    "techniques": {},
    "properties": {}
  },
  "channel_semantics": {},
  "sampling_semantics": {},
  "observations": {},
  "inferences": {},
  "approximations": {},
  "unknowns": {},
  "evidence": {},
  "confidence": {}
}
```

强制区分：

```text
OBSERVED
INFERRED
APPROXIMATED
UNKNOWN
```

禁止：

> 文件名叫 SpecularMap，所以它一定等于 Source specular mask。

---

## B1. CFG 完整解析

完整读取所有实际 section。

不得在此阶段直接转换成 Source 参数。

---

## B2. 贴图通道审计

对所有存在的 texture channel 输出：

- min / max / mean；
- percentiles；
- histogram；
- spatial preview；
- sparsity；
- channel correlation；
- 与 diffuse / UV island 的相关性。

产物：

```text
ir/<material>.material_ir.json
reports/channel_audit.json
reports/channel_sheet.png
```

毛瑟的现有旧结论只能作为待验证提示，不能直接继承。

---

# 8. Phase C — CF Reference Renderer

这是第一核心阶段。

新增：

```text
scripts/material_recovery/cf_reference_renderer.py
```

实现可以使用：

- Blender headless；
- Blender custom node graph；
- Blender scripted shading；
- 独立 Python/software renderer；
- 其它可审计离线 renderer。

优先选择 Blender，因为需要直接在真实武器 mesh / UV / normal 上检查结果。

但必须遵守：

> Blender 负责实现“我们恢复出的 CF shader”，不是使用 Principled BSDF 猜一个相似材质。

---

## C1. CF shader family implementation

每种 shader family 实现独立 reference path。

不能把所有武器都套成一个统一 Phong。

对于 `M1896_Libra` 这个 reference implementation，当前待验证公式：

```text
out.rgb =
    diffuse_lit
  + SpecularMap.rgb * spec_term * Alpha.G
  + CubeSample.rgb * EnvCubeMapBrightness * Alpha.B
```

并研究/接入：

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

不知道的行为必须标 `UNKNOWN`，禁止偷偷补经验值。

---

## C2. Directional cubemap sampling

禁止：

```text
mean(cubemap RGB)
```

替代真实环境采样。

必须实现：

- view direction；
- surface normal；
- reflection vector；
- refraction vector；
- cubemap face lookup；
- configurable coordinate transform；
- ReflectionIndex；
- RefractionIndex；
- CubeMapTransform。

至少输出：

```text
test sphere
test plane
actual weapon mesh
```

三种 reference。

---

## C3. Blender CF Reference scene

建立固定 Blender 测试场景。

相机、灯光、曝光、颜色管理必须固定并写入 manifest。

至少：

```text
neutral
front-lit
side-lit
back/dark
rotated-view
```

目的：

> 验证 shader 行为是否自洽，而不是追求和 CSGO 一样。

产物：

```text
reference_cf/reference_manifest.json
reference_cf/*.png
```

---

## Gate A — CF semantic validation

通过条件：

1. diffuse 基础区域稳定；
2. specular 作用区域合理；
3. cubemap 随 view / normal 变化；
4. 不再是静态 UV 贴色；
5. mask/channel 响应空间关系合理；
6. unknowns 被明确列出；
7. 不靠 weapon-specific magic number 才能成立。

Gate A 不通过：

> 停止 Source translator 工作，继续 CF shader family 研究。

---

# 9. Phase D — 材质区域分析

Gate A 通过后才做。

目标：

```text
triangle -> material_region_id
```

优先利用真实资产，而不是视觉 AI 猜：

```text
diffuse chroma
specular response
alpha/mask
normal variance
CF reference response
mesh piece
mesh connectivity
UV island
```

候选类别示例：

```text
dark_metal
bright_metal
gold_metal
painted_surface
plastic
glow
glass/translucent
other
```

类别不是固定 schema。

---

## D1. Triangle classification

流程：

1. 计算 triangle 的 UV 覆盖；
2. 汇总 diffuse/spec/mask/reference response；
3. 保留 mesh piece / UV island 连续性；
4. 聚类候选材质类型；
5. 合并微型孤岛；
6. 控制 material slot 数量。

产物：

```text
segmentation/triangle_materials.json
segmentation/region_preview.png
```

### D Gate

要求：

- 分区和真实零件/纹理结构一致；
- 不出现大量单三角噪声；
- 每个 region 都能解释分类依据。

---

# 10. Phase E — 纹理高清化 v2

高清化发生在材质语义理解之后。

---

## E1. Diffuse

允许 AI upscale。

要求：

- 原图永久保留；
- 4x 只作为中间结果；
- 最终通常 2048；
- 对比纹样、文字、边缘是否被改；
- 不改变 atlas / UV。

可以：

```text
按 material region 分区域增强
-> 再合回原 atlas
```

---

## E2. Normal

禁止生成式 AI。

流程：

```text
decode normal vector
-> resize/interpolate
-> renormalize
-> encode
```

---

## E3. Specular / Alpha / masks

禁止生成式 AI。

只允许：

- bicubic / Lanczos；
- edge-aware resize；
- controlled blur；
- normalization / remap，但必须有语义依据。

必须比较处理前后 histogram / area coverage。

---

# 11. Phase F — Source 1 Translator v2

新增：

```text
scripts/material_recovery/source1_material_translator.py
```

输入：

```text
Material IR
CF reference behavior
material regions
processed maps
```

输出：

```text
Source VTF set
Source VMT set
triangle -> material slot
translation_report.json
```

原则：

> Source translator 的任务是“有意识地降级”，不是假装 Source 1 能完整表达 CF shader。

---

## F1. 区域级 Source 策略

### dark / colored metal

优先：

```text
VertexLitGeneric
+ base
+ bump
+ controlled Phong
+ optional albedo tint
```

### bright / gold metal

允许测试：

```text
colored Phong
low-intensity envmap
split material
```

但 runtime `$envmap` 只能在方向/mip/明暗都验证后使用。

### glow

仅有真实稀疏发光证据时：

```text
$selfillum
或独立 glow material
```

### translucent / special CF shader

若 Source 无法等价：

- 明确标 `unsupported_by_source1`；
- 选择最小破坏近似；
- 必要时拆独立 material；
- 不允许用固定 cubemap 平均色模拟动态反射并称为等价。

---

# 12. Phase G — 多材质模型写出

通用目标：

```text
原模型
+ 原 UV
+ 原骨架
+ 原动画
+ 新 triangle material assignment
```

只修改：

> material slot assignment。

对于 reference weapon 毛瑟，先扩展其 native VM builder。

之后抽象成可复用 material-assignment 接口。

### G Gate

拆分前后必须满足：

- vertex position 不变；
- triangle geometry 不变；
- UV 不变；
- skin weights 不变；
- bind 不变；
- animation 不变；
- VIEW 不变；
- 只有 material ID 变化。

---

# 13. Phase H — Blender Source-like Preview

这是第二个 Blender 用途。

目的不是还原 CF，而是：

> 在进 CSGO 之前，离线检查 Source 降级方案是否存在明显错误。

必须建立一个 Source-like shader，而不是普通 Principled BSDF。

尽量模拟：

```text
base texture
normal
Phong exponent
Phong boost
Phong tint
Fresnel
selfillum
envmap proxy
lightwarp proxy
```

这里只要求行为近似，不要求和 Source 1 数学完全一致。

---

## H1. A/B preview

同一个 Blender scene：

```text
Left:  CF Reference shader
Right: Source-like approximation
```

固定：

- camera；
- mesh；
- pose；
- lights；
- exposure；
- color management。

对比：

- base color；
- dark-region retention；
- metal hue；
- highlight continuity；
- view dependence；
- glow locality；
- shadow behavior。

产物：

```text
preview_source/reference_vs_source_sheet.png
reports/source_translation_report.json
```

报告必须标：

```text
preserved
approximated
lost
unsupported_by_source1
```

---

## H2. Blender 限制声明

每轮报告必须自动写入：

```text
Blender preview is diagnostic only.
It is not Source 1 / CS:GO runtime ground truth.
```

禁止用 Blender preview PASS 代替游戏验收。

---

# 14. Phase I — CSGO Runtime Validation

这是最终 Source 真值。

只有 A-H 全部通过才部署。

继续遵守：

```text
A. work/<weapon>/addon
-> B. MIGI addon
-> user MIGI REBUILD
-> C. pak
```

要求：

1. A/B manifest + SHA-256 一致；
2. 用户执行 MIGI REBUILD；
3. 可读取时验证 B/C SHA-256；
4. 再做游戏内明/暗环境验收。

如果游戏结果与 Blender Source-like preview 不一致：

> 以 CSGO runtime 为准。

然后调查 Source-specific 差异：

- VertexLitGeneric 实现；
- viewmodel lighting；
- gamma / HDR；
- normal convention；
- envmap；
- Fresnel；
- texture filtering / mip；
- VTF format；
- Source material parameter interaction。

禁止反过来修改 CF truth 来迎合 Source runtime。

---

# 15. Reference Implementation — M1896_Libra

毛瑟只承担：

> 首个完整验证样本。

它不是框架本身。

reference inputs：

```text
PV-M1896_Libra.DTX
M1896_Libra.CFG
M1896_Libra_S.TGA
M1896_Libra_N.TGA
M1896_Libra_alpha.TGA
LobbyCube.DDS
对应 LTB mesh / UV
```

reference-specific evidence：

```text
work/mauser_libra/material_v2/
```

reference-specific threshold / fallback：

只能放 weapon-local config，不得硬编码进通用模块。

毛瑟跑通后必须做一次：

```text
genericity review
```

检查：

- 通用模块是否出现 Mauser/M1896 名称；
- 是否出现毛瑟专属 channel assumption；
- 是否出现毛瑟专属固定阈值；
- 是否可直接替换输入 weapon manifest 跑第二把武器。

---

# 16. 第二武器通用性验证

毛瑟完成后，本计划不能立即宣告“通用框架完成”。

必须选择第二把不同 shader/material 类型的武器做 smoke validation。

优先从已有项目选择：

```text
Galil ACE-天袭
M4A1-雷神
Kukri_Beast
```

只需跑：

```text
A
B
C minimal reference
F translator
H preview
```

目的：

> 确认框架不是只对 M1896_Libra 特化。

如果第二把武器需要修改通用模块：

- 修改后重新跑毛瑟 regression；
- 再跑第二武器；
- 两边同时 PASS 才认为接口稳定。

---

# 17. 验收标准

## Framework acceptance

- [ ] REZ/DTX/UV 层未被无证据重写
- [ ] mesh/UV/diffuse compatibility 有独立 Gate
- [ ] Material IR 为通用 schema
- [ ] shader family 可扩展
- [ ] observed/inferred/unknown/approximation 分离
- [ ] cubemap 使用方向采样
- [ ] Blender CF Reference 不依赖 Principled 猜测
- [ ] Blender Source-like preview 明确不是 runtime truth
- [ ] Source translator 支持多 material slot
- [ ] normal/spec/mask 未经生成式 AI 改写
- [ ] material split 不改变 geometry/rig/animation
- [ ] CSGO runtime 为最终 Source 验收
- [ ] 第二把武器 smoke validation 通过

---

## Reference weapon acceptance — M1896_Libra

不要求 Source 1 100% 复现 CF。

要求：

1. 不出现旧 m7 明显整体偏色；
2. 暗色主体不被洗白；
3. 金属/高光区域与 CF reference 区域一致；
4. 不把整张 `_S` 高频纹理直接变成反射噪声；
5. 环境响应不能是固定 UV 贴色；
6. 明暗环境下 base color 仍可辨；
7. 无新增 UV / normal / mesh 问题。

---

# 18. 停止条件

出现以下情况立即停止当前阶段：

1. asset provenance 不完整；
2. mesh/UV/diffuse compatibility 未通过；
3. CF reference shader 无法解释主要通道；
4. 必须靠 weapon-specific magic number 才能继续；
5. Blender reference 需要 Principled 手调才能“看起来正确”；
6. Source material split 改变 geometry/rig/animation；
7. A/B/C hash 不一致；
8. 游戏无变化但 pak 尚未验证；
9. Source runtime 不一致时有人试图修改 CF truth 来迎合结果。

---

# 19. 代码组织

通用代码：

```text
scripts/material_recovery/
├─ material_ir.py
├─ cf_reference_renderer.py
├─ source1_material_translator.py
└─ shared shader-family helpers
```

单武器：

```text
work/<weapon>/material_v2/
```

禁止在通用代码里出现：

```text
mauser
M1896
galil
tulong
具体武器路径
具体武器阈值
```

除非只是测试 fixture 名称。

---

# 20. SWE2 执行顺序

首个 reference implementation：

```text
A1 -> A2
-> B1 -> B2
-> C1 -> C2 -> C3
-> Gate A
-> D
-> E
-> F
-> G
-> H1 -> H2
-> I
-> genericity review
-> second-weapon smoke validation
```

不要跳过 Gate A 直接继续 Source VMT 调参。

每完成阶段：

1. 更新本 `plan.md` 状态；
2. 保存 evidence；
3. 跑离线验证；
4. 只提交相关文件；
5. push master；
6. 再进入下一阶段。

状态：

```text
TODO
ACTIVE
PASS
BLOCKED
REJECTED
```

---

# 21. 当前状态

```text
Framework skeleton            ACTIVE
  material_ir.py              PASS
  input_manifest.py           PASS

Reference: M1896_Libra
A1 input closure              PASS (11 assets, provenance+hashes, 0 problems)
A2 mesh/UV/diffuse gate       PASS (2767 tris, 0 UV out-of-range; emission render + UV overlay visually verified: zodiac/barrel/engraving islands land correctly)
B1 CFG parse                  PASS (material_ir.json: 9 properties OBSERVED; alpha/spec-exponent semantics INFERRED pending C; 3 sampling UNKNOWNs declared)
B2 channel audit              PASS (alpha.R/G uniform 1.0; alpha.B env-mask mean 0.107; _S lum↔diffuse corr 0.93 — spec map is chromatic not scalar; cubemap face0 grayscale 0.49)
C1 shader family              PASS (software renderer cf_reference_renderer.py; formula pieces tagged INFERRED; Blender skipped — transformed/refract ray not expressible in nodes, plan allows software path)
C2 directional cubemap        PASS (reflect/refract/rotY ray + DX face lookup on sphere/plane/mesh; no mean-cubemap)
C3 Blender CF reference       PASS (5 fixed scenes + component decomposition; software-render equivalent, manifest records reason)
Gate A                        PASS (6/6 behavioral checks: cube varies with normal 0.147, view-dependent corr -0.03, diffuse/spec/cube terms present and bounded, 3 UNKNOWNs declared)
D material regions            PASS (6 regions: 2 env_reflective_metal, warm_metal_dark, 2 dark, mid_surface; island merge coherent; preview saved)
E upscale v2                  PASS (diffuse AI 4x cache -> 2048; normal renormalized; spec/alpha resize-only; lum drift 0.0000 on masks, originals preserved)
F Source translator           PASS (source1_material_translator.py: 6 slots, envmap_metal uses engine env_cubemap + normalmapalphaenvmapmask — CF lobby cube never bound; base BGRA8888 alpha=phong mask, normal DXT5 alpha=env mask; tags preserved/approximated/lost/unsupported)
G material assignment         PASS (build_mauser_vm.py --v2: per-tri slot names in SMD, 2767 tris match regions exactly; MDL contains 6 material names; geometry/rig/anim untouched; staged addon_v2 29 files, MIGI deploy deferred to Phase I)
H1 Blender Source-like A/B    PASS (software Source-like shader on same frame/camera/lights as CF ref — plan permits non-Principled equivalent; 5-scene sheet + per-scene deltas; structure/hue/region separation verified, brightness gap documented as lost ambient fill)
H2 preview limitation report  PASS (source_translation_report.json auto-includes limitation statement + preserved/approximated/lost/unsupported tags)
I CSGO runtime                TODO

Genericity review             TODO
Second-weapon smoke test      TODO
```

当前第一步：

> 先创建通用 Material IR / manifest 接口，然后用 `M1896_Libra` 填充第一个真实样本。接着做 A1/A2。不要修改当前已部署 m7 材质。
