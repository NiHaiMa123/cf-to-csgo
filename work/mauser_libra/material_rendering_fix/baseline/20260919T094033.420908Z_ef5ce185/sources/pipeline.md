# CF → CS:GO Legacy 第一人称武器移植 Pipeline

> 本文件只记录可复用流程和硬规则，不记录单把武器的资产表、参数、试错历史或验收截图。
> 精简前的完整项目记录备份：`pipeline.projects-backup-2026-09-19.md`。
> 各武器证据、脚本和产物统一放在 `work/<weapon>/`。

## 1. 目标与完成标准

把 CF 的第一人称武器、手臂、动画、贴图和声音转换为 CS:GO Legacy 的 stock 武器替换，并保持：

- stock 模型路径、武器槽位、序列名和声音事件兼容；
- CF 枪、手和手臂的内部关系不被拆散；
- 变换可由几何、骨架和蒙皮语义自动求得，不依赖逐武器手调；
- 截图只用于验收，不作为拟合输入；
- 只替换第一人称资源，除非任务明确要求第三人称；
- staging、MIGI addon、游戏 pak 三层内容经过哈希验证。

完成条件：

```text
P0-P6 构建通过
A/B SHA-256 一致
用户执行 MIGI REBUILD
B/C SHA-256 一致（可读取 pak 时）
用户游戏内确认模型、位置、动画、材质和声音
```

## 2. 工作目录

```text
work/<weapon>/
├─ scan/          # Bute、索引、身份和资源路径证据
├─ acquire/       # 从 REZ 分片校验恢复的原始资产
├─ decode/        # LTB/DTX/动画/手膜解码结果
├─ csref/         # stock 反编译、变换、拟合诊断
├─ texture/       # PNG、VTF、VMT
├─ sound/         # 声音探测、解码和 overlay
├─ native_vm/     # SMD、QC、studiomdl 与隔离编译目录
├─ addon/         # 仓库 staging addon
└─ deploy/        # 清单、哈希和 pak 验证证据
```

项目专属参数只写入 `work/<weapon>/**/*.json`、脚本或报告，不追加到本文件。

## 3. 阶段流程

| 阶段 | 内容 | 必须产物 |
|---|---|---|
| 身份 | Bute + REZ 索引确认唯一武器族、PV/QV、贴图、声音、特效 | `scan/*.json` |
| P0 | 从正确 REZ 分片读取并做 MD5/SHA 校验 | `acquire/verified_root/`、清单 |
| P1 | LTB skin、骨架动画、DTX/PNG、材质配置解码 | `decode/*skin*.json`、动画 payload |
| P2 | 仅在身份、UV、节点或姿态存疑时做轻量预览 | 诊断图/报告，可跳过 |
| P3 | stock 反编译；求 H、镜像 MX、残差 VIEW、挂点 | `csref/viewmodel_transform.json` |
| P4 | diffuse 超分；构建 Source 材质 | VTF/VMT |
| P5 | 生成 SMD/QC，映射序列和事件，studiomdl 编译 | `.mdl/.vvd/.vtx/.ani` |
| P6 | 解码 CF 声音并覆盖 stock 声音路径 | PCM16 WAV overlay |
| P7 | staging A → MIGI addon B → 用户 REBUILD → pak C | 哈希清单 |
| P8 | 游戏内验收 | `USER_RUNTIME_ACCEPTED` |

## 4. 身份与资产恢复

### 4.1 身份确认

1. 从 Bute/LTC 记录确认 `StandardName`、`PViewModelFileName`、`PViewSkinFileName`、动画族和声音名。
2. 枚举同族皮肤、旧版模型、BL/GR/WOMAN/socket 变体，明确排除项。
3. 用 REZ 索引确认模型、贴图、CFG、声音、QV 和特效真实存在。
4. 记录索引条目、包路径、分片号、大小和摘要；不要只凭文件名猜资产。

### 4.2 REZ 分片硬规则

- 不使用 `data/` 等旧解包目录作为可信输入。
- REZ 目录项的 `time` 字段可能是分片号，payload 位于 `RFxxx_<n>.REZ`。
- 一律通过 `scripts/material_recovery/rez_verified_payload.read_verified_payload` 读取并校验 MD5。
- `rez/`、`rez2/`…`rez6/` 都要纳入索引；新角色和新皮肤常在后续目录。
- 无摘要校验的资产只能标记为候选，不能进入生产构建。

## 5. LTB、动画与蒙皮

### 5.1 LTB 事实

- LTB 通常是 LZMA-alone 压缩的 Jupiter 模型。
- 节点保存 bind 世界矩阵；动画轨道为 local position/quaternion，需沿父链组合为 world。
- LTB mesh 通常不直接给出贴图路径；贴图绑定依赖命名约定和 CFG。
- 刚性件与节点的归属若未显式给出，应在 bind/local 空间用距离、半径和层级约束分配，并保留审计结果。

### 5.2 正确蒙皮

```text
v_anim = Σ weight_i · W_anim[i] · inverse(W_bind[i]) · v_bind
```

不得遗漏骨骼平移或 inverse bind。只应用 `W_anim` 会造成离线预览与游戏姿态不一致。

外部手臂模型与武器 PV 使用不同 bind 时，先重姿态：

```text
v_weapon_bind = Σ weight_i · B_weapon[i] · inverse(B_arm[i]) · v_arm
```

然后由武器动画骨架驱动。只使用骨名确实匹配的节点；记录未匹配骨骼。

### 5.3 默认手膜

- 默认手膜为妮妮-保卫者 `Arm_Nini_GR`，除非用户明确指定其他角色或阵营。
- 丢弃武器 LTB 内嵌的重复手/臂网格，避免双层手膜。
- 只超分手/袖 diffuse；normal 保持原始分辨率并标记 `NORMAL`。
- 手和枪必须经过同一个全局 VIEW；不得为修位置而逐骨锚到 stock 骨架。

## 6. 坐标、UV 与全局变换

### 6.1 UV

- dump JSON 使用原始 UV；写入 Source/Blender 时执行一次 `v_source = 1 - v_raw`。
- 只翻一次。判断 UV 时用 emission/无光照预览，不要让材质高光干扰。

### 6.2 基础相似变换

先在 idle 动画姿态下求 CF → Source 的相似变换：

```text
H = [sR | t]
v' = H · v
B' = H · B · inverse(H)
W' = H · W · inverse(H)
```

规则：

- 同一 FvARM playerview 空间可复用已验证的 rig-level H；新骨架必须重求。
- H 是 rig 级映射，不保证每把武器最终取景正确；逐武器位置由残差 VIEW 处理。
- 形状不同的武器不能直接全网格 ICP；优先使用枪管轴、握持区、挂点和相机侧点云等语义结构。

### 6.3 镜像

CF/Source 左右约定不一致时，在 H 后绕本武器枪身中心做镜像 `MX`：

- 顶点、bind、动画、挂点同步处理；
- 反射后反转三角绕序并重算法线；
- 不得绕世界原点镜像；不同武器必须重新计算中心。

### 6.4 残差 VIEW 拟合

保持 CF 枪—手—臂整体刚性关系：

```text
VIEW = T(replace) · T(push_cloud) · T(grip) · R_fix · T(-grip)
```

推荐语义：

| 分量 | 数据来源 |
|---|---|
| `grip` | CF idle 下，右手蒙皮表面与枪身表面最近点对的稳定接触区质心 |
| `R_fix` | 枪管/套筒方向与 stock 枪管方向；rig up 与 Source +Z |
| `push_cloud.y` | 双方相机侧枪身点云的纵深统计量 |
| `replace.z` | CF 与 stock 的真实蒙皮手—枪表面接触区高度 |
| `replace.x` | 可验证的相机空间几何或 stock 语义锚；禁止从验收截图量像素手调 |

接触区算法：

1. 分别把 CF 手 + 枪、Source 手 + stock 枪蒙皮到 idle 帧。
2. 对右手表面每个点求最近枪身表面点。
3. 取距离最小的稳定分位区间（默认 10%，并检查 5%/15% 敏感度）。
4. 使用点对中点质心作为接触语义锚，而不是 `R_Hand` 骨原点。

禁止：

- CF 骨点直接对齐 stock 骨点；两套 rig 的骨原点语义不同。
- 用离腕骨最近的枪顶点冒充真实接触点。
- 用整枪质心对齐不同拓扑武器；长机匣、低握把等会产生系统偏差。
- 用整网格 PCA 代表枪管轴；握把和装饰件会污染主轴。
- 根据截图绝对像素、截图尺寸或缩放比例反解最终位置。

截图只验证以下相对关系：手露出量、手—握把接触、枪口—机匣—握把顺序、腕—前臂轮廓和是否穿相机。

## 7. Source 1 模型构建

### 7.1 架构

- 根骨 `v_weapon`。
- 保留 stock 所需的序列名、activity、attachment 和兼容骨名。
- CF 刚性枪件绑定对应 CF 节点；手/袖使用 LBS。
- 动画直接映射 CF clip，统一采样率后写 SMD。
- attachment 以 stock idle 世界位置或明确的 CF socket 为依据。

### 7.2 隐藏 stock 手套/袖子

CS 手套和袖子通过同名 `Bip01*` bonemerge：

```text
posed = W_weapon_bone · inverse(B_arm_bind) · v_arm
```

所有兼容 `Bip01*` 骨在 rest 和每帧动画中统一放到 `(0,+500,0)`，送至相机后方。不要设 identity，不要放到 `-Y` 前方，也不要修改共享手套材质。

### 7.3 编译验证

- QC 不应意外包含 `$origin`、`$upaxis` 或额外 `$scale`。
- 编译后必须检查 `.mdl/.vvd/.dx90.vtx/.dx80.vtx/.sw.vtx`，使用动画块时还要检查 `.ani`。
- 从最终生成的 reference SMD + animation SMD 重算一帧蒙皮，确认其与拟合器预测一致。
- 检查枪身、左右手、前臂和动态装饰件的 bbox；远端装饰件不能污染枪身拟合。

## 8. 贴图与材质

### 8.1 贴图处理

- 只对 diffuse 做 RealESRGAN 4x；4096 作为中间结果，通常降采样到 2048。
- 最终 diffuse 优先 BGRA8888，并启用 `TRILINEAR`、`ANISOTROPIC`。
- normal/spec/alpha 不盲目超分；逐通道确认真实含义。
- `*_S` 可能是环境反射色图，不等于 Source 的普通 specular mask。

### 8.2 材质语义恢复

通用单位是 CF 的 shader family，不是武器名称，也不是一组固定 Phong 常量。先解析 CFG 的 Techniques/Properties 和全部贴图通道，再按目标引擎的表达能力转换：

| CF shader family | Source 近似 |
|---|---|
| diffuse/normal | base + bump |
| 普通 specular | 通道 mask + 受光照 Phong |
| albedo 金属 | albedo-tinted Phong |
| 标准 reflect cube | 仅在射线、朝向和 mip 均验证后使用 `$envmap` |
| Alpha+Snell+TransformedCube | spec → 弱受光 Phong；cube → 稳定加法环境层（emissiveblend）；diffuse → lightwarp 压缩 |
| 稀疏发光 | 仅验证过的通道 → selfillum mask |

已验证的 PlayerView Alpha+Snell+TransformedCube 公式为：

```text
out.rgb = diffuse_lit
        + SpecularMap.rgb × spec_term × AlphaMap.g
        + CubeMap × EnvCubeMapBrightness × AlphaMap.b
AlphaMap.r = opacity
spec exponent = SpecularPower × 0.25
```

Source `VertexLitGeneric` 不能表达 CF 的 transformed light direction、Snell 折射、`ReflectionIndex/RefractionIndex` 混合和 `CubeMapTransformY`。因此该 family 不得把原 cubemap 直接接到 `$envmap`：通道名称虽相同，采样射线不同，会造成错误亮斑、阴影洗白和无 mip 噪点。通用降级规则为三层模型——CF 原式中 cubemap 是不乘直射光的独立加法项，任何只重映射 diffuse 光照的方案（纯 lightwarp、selfillum 混合）都无法同时修复迎光高光爆亮与背光反射消失：

1. `SpecularMap.rgb × AlphaMap.g` 单独低通后写入 base alpha，仅它驱动受光照的 Phong；从其 RGB 能量统计 `$phongtint`，不得用暗 diffuse 的 `$phongalbedotint` 代替独立 specular 颜色；`_S` 的高频纹理不得直接成为 Phong mask；
2. cubemap 不得并入 Phong。`cubemap代表色 × EnvCubeMapBrightness × AlphaMap.b` 低通后作为 `$emissiveblendbasetexture` 的 RGB 层，用静态 `$emissiveblend`（dummy 白 texture/flow、scroll `[0 0]`）作为不随场景直射光变化的加法 pass 恢复环境反射；`$emissiveblendstrength` 由统一的受光份额推导（`1 - 受光份额`）；
3. 用 `LightBrightness` 经过统一的跨引擎尺度和上下限推导 Source 受光份额，并生成中性 `$lightwarptexture` 曲线：暗端 `1 - 受光份额`，亮端 `1.0`；它只压缩 diffuse 光照对比，不承担反射项；
4. `$phongboost` 只应用统一的目标引擎代理增益并按 specular tint 亮度归一化；已验证公式没有独立 Fresnel 衰减时使用中性 Fresnel；
5. 用 `SpecularPower × 0.25` 判定高光宽窄，再通过统一的跨引擎宽度标定映射并限制到 Source 可用范围，禁止直接复制 CFG 数值；
6. 原 cubemap、旋转和折射参数保留在审计报告中，不作为无法等价表达时的运行时贴图。

同一张高频图不得同时驱动 Phong 与 envmap。只有标准反射 family 且六面朝向、完整 mip、动态明暗都验证通过时才允许直接 `$envmap`。selfillum 只来自验证过的稀疏发光 mask；弱受光 shader family 不使用 selfillum 做对比压缩，因为带 `$bumpmap/$phong` 的 `VertexLitGeneric` 对该组合支持不稳定。lightwarp 必须是 256px 级、未压缩 BGR888、UV clamp、无 mip 的中性曲线。emissiveblend 环境层必须低通、有界且强度由 CFG 推导，不得直接复制原 cubemap 像素。

每次构建输出 shader family、转换策略、CFG 参数、通道 min/max/mean、滤波方式、VTF format/flags 和近似参数。游戏验收至少覆盖明暗两个环境，并检查噪点、洗白、底色保持和高光连续性。

## 9. 声音与事件

声音来源必须探测内容，不能按扩展名假设：

1. 若首字节/头部符合 LZMA-alone，先解压并检查输出是否为 RIFF/WAV。
2. 若 SND 只是容器或占位，检索 `FMODStudio/Weapon*.bank` 的 FSB5 流并用 vgmstream 解码。
3. 输出统一为 44.1 kHz PCM16 WAV，再映射到 stock 武器声音路径。
4. 事件时序优先使用 LTB keyframe label / clip `times_ms`，换算到 QC fps。

注意：

- `event 5004` 同 channel 的后续声音会截断前一个；静音事件也可能截断。
- 同一 PCM 不要重复挂到同一 sequence 的多个事件。
- 不改共享声音或第三人称声音，除非任务明确要求。

## 10. MIGI 部署与哈希门禁

```text
A. work/<weapon>/addon/**
        ↓ 构建脚本同步 + SHA-256
B. <game>/migi/csgo/addons/<addon>/**
        ↓ 用户手动 MIGI REBUILD
C. <game>/migi/csgo/pak01_dir.vpk + pak01_*.vpk
```

强制顺序：

1. 构建 staging A。
2. 显式同步全部变更到 B，包括新增材质、声音和模型旁文件。
3. 比较 A/B 文件清单、大小和 SHA-256；不一致不得通知用户 REBUILD。
4. 用户手动执行 MIGI REBUILD；agent 不代替用户操作 MIGI。
5. 可读取 pak 时比较 B/C；不能读取则保持 `PACK_VERIFY_PENDING`。
6. 若游戏无变化，先查 A/B/C，不要继续改 shader 或 VIEW。

MIGI UI 日期、addon 显示名和“REBUILD 成功”提示都不能代替哈希验证。松散 `migi/csgo/materials/` 在本环境不作为覆盖方案。

## 11. 验收清单

### 离线

- [ ] 资产均来自 MD5 校验后的 REZ payload
- [ ] idle 蒙皮使用 `W_anim · inverse(W_bind)`
- [ ] UV 只翻转一次
- [ ] 镜像中心、三角绕序、法线一致
- [ ] 枪、手、臂共享全局 VIEW
- [ ] 手—枪真实表面接触关系保持
- [ ] 无骨骼、顶点或动态件穿过相机
- [ ] stock 序列、activity、attachment 和声音路径兼容
- [ ] studiomdl 输出文件齐全
- [ ] A/B SHA-256 一致

### 游戏内

- [ ] MIGI REBUILD 后加载的是本轮版本
- [ ] idle 方向、远近和相对高度合理
- [ ] 手露出量、握持关系和前臂轮廓合理
- [ ] fire/draw/reload/inspect 无散架或跳变
- [ ] 枪口、抛壳、弹匣和装饰件位置正确
- [ ] 材质无洗白、噪点、反面或错误 UV
- [ ] 近/远枪声、换弹和特殊声音时序正确

## 12. 工具索引

| 用途 | 位置 |
|---|---|
| REZ 分片校验 | `scripts/material_recovery/rez_verified_payload.py` |
| REZ 索引 / DTX | `scripts/material_recovery/n05a_decoder_provenance_audit.py` |
| LTC/Bute | `scripts/material_recovery/n02_butes_config_triage.py` |
| LTB 动画 payload | `scripts/cf_ltb/p5_p7_s04_cf_animation.py` |
| LTB skin JSON | `CFRezManager --dump-ltb-skin` |
| Source 编译参考 | `scripts/p5/p5_p7_s05_cf_native_vm.py` |
| 默认 Nini 手膜 | `work/galil_ace_tianxi/decode/nini_gr/` |
| 项目历史与专属参数 | `pipeline.projects-backup-2026-09-19.md`、`work/<weapon>/` |

## 13. 维护规则

- 本文件只更新通用、已验证且可跨武器复用的规则。
- 单武器资产路径、常量、实验版本和用户验收记录只进入 `work/<weapon>/`。
- 失败方案若具有通用警示价值，只保留一句“禁止项 + 根因”，不保留逐轮过程。
- 新发现的构建、测试或部署命令应同步到项目规则文件或本工具索引。
- 不删除历史证据；归档后用链接引用，避免再次把主 pipeline 膨胀成项目日志。
