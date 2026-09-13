# CF 武器 -> CS:GO Legacy Source 1 — 蓝图与当前任务

> 本文件同时是 **长期 pipeline / Gate / 冻结事实** 和 **当前状态与当前任务**。  
> 原独立 `task.md` 已并入 **§0**。Git 规则看 [`AGENTS.md`](AGENTS.md)，角色看 [`README.md`](README.md)。

---

# 0. 现在的情况

```text
Date captured                 : 2026-09-13
P4 Source 1 / MIGI baseline   : PASS / FROZEN
P4-M01 native material        : INCOMPLETE (lighting deferred)
P5 雷神 identity              : IDENTITY_CONFIRMED (base Transformers)
Current executor task         : NONE
Last completed task           : P7-S04 broken CF anim loaded in Blender for fix/verify
Last accepted evidence commit : ae848d6
State                         : LIGHTING_DEFERRED / P4-M01_INCOMPLETE / P5_IDENTITY_CONFIRMED / P6_IDENTITY_REPLACEMENT_DEPLOYED / P7_ORIGINAL_SOUND_DEPLOYED / P7_VISIBLE_INSPECT_USER_ACCEPTED / P7_WORLD_MODEL_USER_ACCEPTED / P7_CF_ANIM_REJECTED_IN_GAME / P7_CF_ANIM_IN_BLENDER / SOUND_RETIMED_TO_CF_ANIM / INSPECT_CLIPPING_NOTED
```

## 0.1 已钉死

- P4 证明 CF LTB 能进 Source 1 / MIGI（M4A4 槽）。Prototype **不是**最终雷神，也 **不是**原生材质。
- 黑骑士 Bute 只绑 PV LTB + PV DTX + 共用 RS（TEXTURE1）。TGA/CFG 路径在 packed BF005 上是 0。
- **已恢复 BornBeast PV 原生枪身 atlas**：`rez/rf017_8.rez`，标准 -5 / DXT1 / 1024×1024；目录 MD5 匹配，Python 与现有 CFRezManager 图像 decoder 的 RGBA 像素完全一致。根因是旧工具按主索引文件读取 payload，未路由到编号分包，详见 §4.27。
- 本轮 9/9 材质目标通过目录 MD5。Normal / Specular / Alpha 是无需修复的标准 TGA；WeaponShader CFG 是含贴图名和参数的明文。此前“无头 DTX / 三字节 CFG / TGA 插入修复”不能代表这些正确资源。
- 512×512 是历史外部参考的尺寸，不是 UV 必须使用的贴图尺寸。N05-D：verified PV LTB 11 piece / 5342 tri，UV 全在 0–1；武器 piece 的 UV 岛落在 verified 1024 PV DTX 的枪身/弹匣/序列号 `M4A1SSQ00083` 区域。手和枪共用这一张 PV atlas。CS1.6 / ComfyUI 禁止当 P4-M01 final 像素。
- 命名 cube `ModelTextures/EnvCubeMap/Black_Shader03.DDS` 已从 `rez3/RF017.REZ` 等 6 份相同副本恢复（SHA256 `c4954419d59bea55b0f592957eab92fa623583d28158cbf84e95bacd233c4e92`，393344 字节）。首面预览近黑，与名称及 CFG `EnvCubeMapBrightness=4` 相容；不是 runtime 公式证明。
- `playerviewmesh.fxo` 有 Alpha/Normal/Specular/Emissive **槽名**，没有文件路径。
- CShell 有 `modeltextures\SpecularMap\%s`（12 LEA，后期 `.dtx` 路线）。黑骑士 Bute 没有 `SpecularMapName`；这与新恢复 CFG 中的 `SpecularMapName2` 是不同来源。
- `crossfire.exe` 明文岛：`MODELTEXTURES\Shader\WeaponShader\` + `.cfg`，**0 代码引用**。它是 stub，只导入 packed `crossfirebase.dll`（`.tvm0`）。
- 磁盘 `crossfirebase.dll` 无 WeaponShader 明文。N04-F 当时的 PID 33100 = `x64/crossfire.exe`，`OpenProcess(VM_READ)` = Win32 **5**。这是历史观测，不是当前进程状态；未绕过 ACE。
- 正式提取/预览入口已接入 MD5 验证的主文件/编号分包 resolver（N05-C）。`extract_all.py`、CFRezManager Extract/Explorer/模型贴图/CFG/sprite/OBJ，以及 N05-A 的 `read_payload_bytes(..., entry=)` 走同一规则。目录缓存 v2、缩略图缓存 v2。无 MD5 不得宣称已验证或猜分包。历史 `data/rf017` 仍是旧主文件提取，不能当 final。

## 0.2 当前任务

```text
Task ID : NONE
State   : P6_IDENTITY_REPLACEMENT_DEPLOYED / P7_ORIGINAL_SOUND_DEPLOYED / P7_VISIBLE_INSPECT_USER_ACCEPTED / P7_WORLD_MODEL_USER_ACCEPTED / P7_CF_ANIM_IN_BLENDER
Goal    : 在 Blender 里改/验证 CF 动作，通过前不再进游戏编译
Last    : User rejected in-game CF anim (hands deform). Current viewmodel is in Blender.
Result  : P7_CF_ANIM_IN_BLENDER
```

**2026-09-13 用户决定（仍有效）**：不必再做 CF 打光对等。CF 打光本身一般，贴图质感以后专门调。因此停止：CFG→Source `$phong`/`$envmap` 拟合、继续灌 FXO 公式进游戏。P6 VMT 沿用 N05-J 公式通道，没有把 CFG 标量抄进 phong。不宣布 P4-M01 PASS。N04-F 仍暂停。

**P5-T02**：用户 2026-09-13 在 Blender 中确认 base `PV-M4A1_S_Transformers`（DTX 与 `_PC` 同字节）是 **M4A1-雷神**。`USER_VISUAL_MATCH_CONFIRMED`。不是 `IDENTITY_CONFIRMED`，不是 P6。同时指出 raw LTB 导入左右反了；已在 Blender 对 LTB X 做 scale −1 并翻法线。用户确认「对了」。证据 [`work/p5_leishen/t02_native/visual_match.json`](work/p5_leishen/t02_native/visual_match.json)。未部署、未改 N05-J / frozen。

**P5-T03**：已用 N05-C 验证 reader 建立 identity-core 资源图。packed Bute `rez/Butes/BF005.LTC` 的 canonical Weapon 记录 WeaponName=`M4A1-雷神` / StandardName=`M4A1_S_Transformers`，`PViewModelFileName` / `PViewSkinFileName` / `ModelFileName` / `SkinFileName` 与用户认图的 PV LTB+DTX 及 QV LTB+DTX 一致。CFG Name2 TGA/cube 仍是 config 引用。Identity-core 无独立 REZ WAV；Bute 枪声事件名是 `ShootM4A1-S-Beast`。证据 [`work/p5_leishen/t03/report.md`](work/p5_leishen/t03/report.md)。

**P5-T04**：`IDENTITY_CONFIRMED`。依据 T01 图鉴 + T02 用户认图 + T03 Bute 路径/SHA。证据 [`work/p5_leishen/t04/identity_review.json`](work/p5_leishen/t04/identity_review.json)。

**P6**：用户 2026-09-13 明确开做。已把确认身份的 base Transformers PV LTB 和 verified DTX/TGA/cube 编进独立 addon `p_cf_leishen_m4a4_p6`，部署到 M4A4 槽。首发把 LTB X 镜像做在 C3 之前，枪在 CF X≈+1.5，绕原点翻转后 Source X 中心到 −5.5，左手对不上；用户截图「错位」。已改为先冻结 C3，再绕 Source X=0 镜像。最终武器包围盒 X 中心 −0.18（P4 BornBeast 为 +0.10）。N05-J 与 frozen 都 parked、未改 frozen 文件。`final_target_identity=true`，`final_cf_material=false`。不是 P4-M01 PASS。证据 [`work/p5_leishen/p6/report.md`](work/p5_leishen/p6/report.md)。

**P7-S01**：用户 2026-09-13 「好了」。声音按 CS 动作对齐已接受。**标记：之后替换成 CF 原动作还需要再调声音时间**（`SOUND_RETIME_REQUIRED_ON_CF_ANIM`）。证据 [`work/p5_leishen/p7/report.md`](work/p5_leishen/p7/report.md)。

**P7-S02**：用户 2026-09-13 「除了小穿模，没问题」。Inspect 已接受（CS lookat，不是 CF 检视）。**标记：F 检视手指小穿模**（`INSPECT_CLIPPING_NOTED`），与 P4 同一类问题，IK / retarget 仍开放。未改 frozen addon、未改 P7-S01 声音。证据 [`work/p5_leishen/p7_s02/report.md`](work/p5_leishen/p7_s02/report.md)。

**P7-S03**：用户 2026-09-13 「可以」。World / dropped 已接受。证据 [`work/p5_leishen/p7_s03/report.md`](work/p5_leishen/p7_s03/report.md)。

**P7-S04**：用户 2026-09-13 进游戏：**完全不行，全部动作手都会变形**。自动 world-space retarget 作废。已把当前第一人称（P6 枪 + CS bonemerge 手 + 失败的 CF clip）载入 Blender，**通过前不再编译进游戏**。场景 [`work/p5_leishen/p7_s04/blender/p7_s04_current.blend`](work/p5_leishen/p7_s04/blender/p7_s04_current.blend)。

游戏当前加载：`p_cf_leishen_m4a4_p6` + `p_cf_leishen_m4a4_p7_sound`。N05-J 与 frozen 都 parked 在 `migi/csgo/_parked_addons/`。

N05-E 已在自建 D3D9 device 上载入当前磁盘 `playerviewmesh.fxo`（111 参数 / 43 technique）。CFG 的 `SpecularPower` / `LightBrightness` / `DiffuseBoost` / `AmbientLightColor` / `EnvCubeMapBrightness` / `ReflectionIndex` / `RefractionIndex` 与 effect 参数同名；`DiffuseMap`/`SpecularMap`/`NormalMap`/`AlphaMap`/`CubeMap` 槽存在。D3DX 默认值与 BornBeast CFG 不同，不能当运行时。`CubeMapTransformY` 无同名参数。live FXO SHA 已与 N04-C 不同。未附加 CF。P4-M01 仍 INCOMPLETE。

N05-F 已把 verified PV DTX + Normal/Specular/Alpha TGA + cube 首面编成独立 Source 1 VTF/VMT 诊断包，`final_cf_material=false`，未覆盖 frozen addon，未部署。CFG 标量没有当成 Source 1 phong/envmap 数值。P4-M01 仍 INCOMPLETE。

N05-G 已通过 Blender MCP `127.0.0.1:9876` 把 N05-D 的 raw PV LTB OBJ 和 N05-F 的 PNG 贴进当前 Blender（EEVEE Rendered）。枪身 3/4 可见序列号 `M4A1SSQ00083` 与兽头护手。手模 rest-pose 未蒙皮，默认隐藏。这是离线展示，不是 runtime 公式。

N05-H 已把 P4 编译网格（字节不变）和 N05-F VTF 接到 MDL 材质路径 `rif_m4a1`，部署为独立 addon `p_cf_bornbeast_m4a4_n05h_native_diag`。frozen 文件未改，文件夹移到 `migi/csgo/_parked_addons/`。用户已确认游戏内 M4A4 槽替换成功。那是诊断 Gate，不是 P4-M01 PASS。`$phongexponent 16` 仍是占位。

N05-I 已在自建 D3D9 device 上对 `playerviewmesh.fxo` 做 per-pass `ShaderBytecode.Disassemble`（51 个 unique shader）。`D3DXDisassembleEffect` 失败。假设 technique `tPlayerViewMeshAlphaAproxSnellTransformedCube`（`EnvCubeUsage=2` + AlphaMapName2，仍是名字级假设）的共享 PS 实际采样 Diffuse/Normal/Specular/Alpha/Cube。该 PS 中 AlphaMap.r=不透明度、.g=spec 混合、.b=cube 混合；preshader 使用 `SpecularPower * 0.25` 作为 pow 指数。BornBeast Alpha TGA 的 R/G 恒为 255，只有 B 有空间变化。CFG 标量仍不是 Source 1 phong 数。

N05-J 已把诊断 addon 换成 `p_cf_bornbeast_m4a4_n05j_formula_diag`：`$envmapmask` 来自 AlphaMap.b，去掉 N05-H 的 `$normalmapalphaenvmapmask`。N05-H 文件夹已从 addons 删除，frozen 仍 parked。用户观察：反射比 N05-H 弱一点，其余正常；N05-H env 观感也无问题。保留公式 mask，不回退。

N05-K 已在自建 Hardware D3D9 上渲染假设 technique。`bornbeast_cfg.png` 因 CFG `LightBrightness=0.01` 对人眼是近黑影（枪像素中位亮度约 13），不能当认图材料。`maps_on_mesh_studio_crop.png` 是 studio 灯，只用来看图是否在网格上。用户 2026-09-13 决定不继续打光对等。未附加 CF，未把 CFG 抄进 VMT。仍不是 PASS。

证据：

- N05-E：`work/.../n05e_fxo_offline_inspect/`
- N05-F：`work/.../n05f_source1_native_map/{report.md,mapping.json,materials/}`
- N05-G：`work/.../n05g_blender_native_preview/{report.md,n05g_viewport_gun.png}`
- N05-H：`work/.../n05h_nonfrozen_native_addon/{report.md,mapping.json,addon/}`
- N05-I：`work/.../n05i_fxo_formula/{report.md,formula.json,asm/unique/}`
- N05-J：`work/.../n05j_formula_channel_addon/{report.md,mapping.json,addon/}`
- N05-K：`work/.../n05k_fxo_cfg_preview/{report.md,bornbeast_cfg.png,d3dx_defaults.png}`
- P5-T02 native：`work/p5_leishen/t02_native/{report.md,gate/gate_sheet.png,execution.json}`
- P5-T03 graph：`work/p5_leishen/t03/{report.md,resource_graph.json,bute_canonical.json}`
- P5-T04 identity：`work/p5_leishen/t04/{report.md,identity_review.json}`
- P6 replacement：`work/p5_leishen/p6/{report.md,execution.json,mapping.json,addon/}`
- P7-S01 sound：`work/p5_leishen/p7/{report.md,execution.json,mapping.json,addon/}`
- P7-S02 inspect：`work/p5_leishen/p7_s02/{report.md,execution.json}`
- P7-S03 world：`work/p5_leishen/p7_s03/{report.md,execution.json,mapping.json,addon/}`
- P7-S04 CF anim decode：`work/p5_leishen/p7_s04/{report.md,execution.json}`

## 0.3 禁止

- 不宣布 P4-M01 PASS
- 不把 CS1.6 / ComfyUI / 图鉴当 native final
- 不注入、不补丁、不驱动、不 NtRead 绕过 ACE
- 不 git add `data/**`、CF `.exe/.dll/.fxo/.dmp`
- 未经用户再开任务，不再拟合 CF 打光或改诊断 VMT 质感
- 不把 M4A1-黑骑士 / BornBeast 写成雷神；不把 filename `Transformers` 当 identity
- 不把 `USER_VISUAL_MATCH_CONFIRMED` 单独写成 P6；P6 需用户单独开任务（本轮已开）
- 不在用户认图前写 `USER_VISUAL_MATCH_CONFIRMED` / `IDENTITY_CONFIRMED`
- 不把 P6 部署写成 P4-M01 PASS 或 lighting match
- 不覆盖 parked frozen addon 文件
- 不把 Qingchun / BB / Zeekr / BornBeast WAV 当雷神原声
- 不把未重建的 FMOD 多层事件图写成完整 CF 枪声还原

## 0.4 2026-09-12 联网复盘：可尝试路径与顺序

**更新判断**：用户 2026-09-13 推迟 CF 打光对等与贴图质感。路线 B 的游戏内 shading 不再是当前任务。P4-M01 仍 INCOMPLETE。N04-F 继续暂停。P5 身份已是 `IDENTITY_CONFIRMED`。P6 雷神 identity replacement 已部署，用户确认模型没问题。P7-S01 声音用户已接受（当时按 CS 动作时间）。P7-S02 Inspect 用户已接受，F 时手指小穿模记下。P7-S03 world/dropped 用户已接受。P7-S04 自动接到第一人称被用户否定（手变形）；现已进 Blender 改，通过前不回游戏。

| 优先级 / 路线 | 新依据与要回答的问题 | 最小实验 / 成功标准 | 边界与停止条件 |
|---|---|---|---|
| 1 / A：正确来源接入 | N05-C 已完成：正式入口 9/9 SHA256 与 N05-B 一致 | 已交付 `VERIFIED_READER_INTEGRATED`；旧 `data/rf017` 仍弃用 | 不覆盖旧 data，不按主文件范围丢弃合法分包 entry，不用无 MD5 的猜测作为成功 |
| 2 / C：正确输入的绑定与副本差分 | N05-D 完成：PV LTB UV 落在 verified 1024 atlas；cube 已恢复 | 已交付 `MESH_UV_AND_CUBE_RECOVERED_BINDING_OPEN`；piece→sampler 仍开放 | 归一化 UV 允许不同分辨率；QV 副本保留，不贴到 PV |
| 3 / B：FXO 离线语义分析 | N05-I/K 已交付公式与离线预览。用户 2026-09-13 推迟打光对等 | 离线证据保留；**当前不把公式灌进游戏 VMT，不调质感** | 质感/phong 以后单独开任务；不得把这次推迟当成 P4-M01 PASS |
| 4 / D：可合法取得的兼容旧版本作参考 | Jupiter / CF 工具可解释标准路径，较早版本或不同地区 variant 可能暴露更少的格式差异 | 只有已获得可信版本与相关资源后，做旧/新 loader 或资源格式差分，提炼规则回验当前本机样本 | 尚无这样的新输入，不承诺能取得；旧版本行为/像素不自动成为当前 CF final，也不采用私服/脱壳工具包补缺口 |
| 产品备选 / E：可用外观版本 | P4 已具备构建/部署能力，CS1.6 atlas 可作已有视觉演示 | 用户选择此交付目标后单独生成可看版本，`final_cf_material=false` | 不计为 native PASS，不借此跳过 P5 身份 Gate；此次仅规划，不部署 |

**B 的具体可行性**：[`D3DXCreateEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxcreateeffect) 接受 ASCII 或 binary effect；[`ID3DXBaseEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/id3dxbaseeffect) 可枚举参数、technique/pass 和取值；[`D3DXDisassembleEffect`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxdisassembleeffect) 可反汇编已加载 effect。N05-I：`D3DXDisassembleEffect` 失败；per-pass [`D3DXDisassembleShader`](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxdisassembleshader) 经 SharpDX `ShaderBytecode.Disassemble` 成功。需要自建 D3D9 device，**不是对 `.fxo` 跑 DXBC 工具，也不是执行 CF 客户端**。公式已抽出后，通道角色可以接到诊断 VMT；仍不得把 CFG 标量抄成 Source phong 数，不靠调参把外部参考“拟合”成原生。

**没有默认启用的路径**：继续扫同一 packed PE 的 strings/xref、重复 VM_READ、换权限/驱动/注入抓取，都没有本轮新证据支持。RenderDoc 官方[支持表](https://github.com/baldurk/renderdoc/blob/v1.x/README.md#api-support) 明确不支持 D3D9；[apitrace](https://github.com/apitrace/apitrace/blob/master/docs/USAGE.markdown) 支持 D3D9，但 Windows 跟踪需要 wrapper/插入，不能当成无侵入方案。只有未来自有离线 harness 才考虑图形跟踪；不用于本次 ACE 保护进程。用户已有合法 dump 时可保留原 C 分叉，但它不再是所有离线工作的前置条件。

**源码与参考入口（联网核查日期 2026-09-12）**：

| 来源 / 固定版本 | 已核实的具体内容 | 对当前任务的限制 |
|---|---|---|
| [no-lith/RezExtract `src/rez.cpp`](https://github.com/no-lith/RezExtract/blob/b3f87a9c731c0bbc1900da2fd37e41b9a02e1e63/src/rez.cpp#L338-L369) | `b3f87a9`：DTX 提取选项会交换 offset 4/8 的四字节字段以恢复版本位置 | 旧错源字节不满足换位前置；N05-B 正确 PV/QV 已是标准头，无需此变换 |
| [YoungFine0825/LTB2FBX `DtxConverter.cpp`](https://github.com/YoungFine0825/LTB2FBX/blob/06d749d56d6c929ba6c538cc26aa11cc1f7f1566/Source/DtxConverter.cpp)、[底层 `dtxmgr.cpp`](https://github.com/YoungFine0825/LTB2FBX/blob/06d749d56d6c929ba6c538cc26aa11cc1f7f1566/ThirdParty/lithtech/runtime/shared/dtxmgr.cpp) | `06d749d`：尝试 LZMA 后走 LithTech texture loader；`dtx_Create` 检查 resource type/version/mip 范围 | 是可审计参考与工具对照，不能承诺支持 2026 本机 variant；不用其测试资源当 final |
| [iQuitt/Vortigaunt `DtxConverter.cpp`](https://github.com/iQuitt/Vortigaunt/blob/d739d1f900c261fc1ae67e11b436410084dda1aa/src/core/converters/DtxConverter.cpp)、[底层 `dtxmgr.cpp`](https://github.com/iQuitt/Vortigaunt/blob/d739d1f900c261fc1ae67e11b436410084dda1aa/ThirdParty/lithtech/runtime/shared/dtxmgr.cpp) | `d739d1f`：也使用 LZMA/同源 LithTech loader | 两工具都失败/成功不是两份独立的 CF runtime 证明 |
| [no-lith/Jupiter](https://github.com/no-lith/Jupiter)、[jsj2008/lithtech](https://github.com/jsj2008/lithtech) | 标准 engine/render/resource contract 的源码参考入口，沿用 §4.9 | 公开仓库不是当前 CF 或官方授权来源证明；具体采用函数时再固定 commit |

微软 [Texture Coordinates](https://learn.microsoft.com/en-us/windows/win32/direct3d9/texture-coordinates) 说明常规 UV 是归一化坐标；因此 512 与 1024 的尺寸差本身不是 atlas 不兼容的证据。当前 LTB 的具体 UV 布局仍以正确来源的网格验证为准。

推进规则：**N05-C 正式入口接入 → 正确 PV/CFG 的绑定验证 → FXO/Source 1 语义映射**。像素、绑定、公式分别验收；只有 §3 的全部条件成立才能 native PASS。P5 身份已是 `IDENTITY_CONFIRMED`。P6 已部署 identity replacement，不是 native PASS。P4-M01 仍 INCOMPLETE。

---

# 1. 总体目标

把 CrossFire 本地资源可靠转换为 CS:GO Legacy Source 1 / MIGI 可用武器 Mod，并最终完成目标武器身份、原生材质、发布质量与后续动画/IK增强。

完整主链：

```text
CF 原始资源
-> REZ / LTB / DTX / TGA / CFG / audio 提取与解析
-> 武器模型 / UV / 骨骼 / 动作关系
-> Source 1 SMD / QC / VMT / VTF
-> compile / validate / package / MIGI
-> CF 原生材质恢复
-> 最终目标资产确认
-> release-quality replacement
-> Inspect / IK / CF 原动画/声音等增强
```

---

# 2. 阶段 Pipeline

## P0-P3 — 前置基础

包含资源解包、音频工具、LTB 基础研究、Source 1 兼容性与 M4A4 映射等历史基础工作。

状态：`DONE / HISTORICAL`。

## P4 — Source 1 conversion baseline

目标：证明 CF 第一人称武器能稳定进入 Source 1 构建与 MIGI runtime。

固定链：

```text
local CF LTB
-> mesh / UV / normal / bone mapping
-> SMD / QC
-> Source 1 material references
-> studiomdl
-> Crowbar roundtrip
-> validation
-> package / staging
-> MIGI deploy
-> user runtime Gate
```

### P4 冻结结论

```text
P4 baseline = PASS / FROZEN
```

冻结身份：

```text
Implementation baseline : 10aa99b770e575300ca3c28324ef3de3d5b70c6b
Frozen build run        : run_20260819_170013_270792
RV-04 evidence commit   : fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
Frozen addon            : p_cf_bornbeast_m4a4_p4_frozen_noop_01
Runtime slot            : M4A4
Internal model          : weapons/v_rif_m4a1.mdl
Inspect policy          : frozen_noop_safe
final_target_identity   : false
final_cf_material       : false
```

已证明：

- fresh local CF LTB 能进入完整 Source 1 构建；
- M4A4 skeleton / sequence / attachment contract 可工作；
- mesh-to-bone、SMD/QC、studiomdl、roundtrip、validation、package、deploy 可闭环；
- runtime changed-state 用户 Gate 通过。

P4 从未证明：

- Prototype 就是最终雷神；
- CF 原生材质已经正确恢复；
- external texture 可作为 final；
- visible Inspect / hand-finger IK 已完成；
- CF 原动画、声音、world model 已最终化。

### RV-04 冻结反例

4/4 高风险 mutation 被预定 Gate 拒绝：

```text
unsafe output root              -> manifest_contract
same sequence count/wrong name -> sequence_names_and_count
bone semantic swap             -> smd_manifest_bone_corners
missing critical VTF           -> material_closure
```

`material_closure` 只证明 Source 1 引用闭合，不证明上游 CF 像素语义正确。

---

# 3. P4-M01 — Native Material Recovery

目的：补齐 P4 从未证明的 CF 原生材质 fidelity。

历史 Prototype 曾使用 external CS1.6 BornBeast texture，因此必须把原生材质作为独立 hard requirement。

目标链：

```text
BornBeast local LTB / UV
+ DTX
+ Alpha / Normal / Specular TGA
+ WeaponShader CFG
+ same-family variants
-> container / storage evidence
-> real mesh/piece material binding
-> CFG / render semantics
-> native-only composition
-> reproducible Source 1 mapping
```

最终可见材质只能来自：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

禁止 final pixels 来自：

- external MOD texture；
- 官网/网络图片；
- AI 生成/补全贴图；
- 从 reference 反采样后回写的颜色。

### P4-M01 PASS Gate

只有同时满足：

1. geometry / UV 来自 local CF；
2. 实际材质资源都有 path + SHA；
3. mesh/piece -> material/texture binding 有结构或 direct consumer evidence；
4. CFG/render semantics 足够解释真实消费方式；
5. visible color 100% local CF / verified semantics；
6. 0 external pixels；
7. clean output 可重复；
8. BornBeast native result 可稳定辨认；

才能判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

---

# 4. P4-M01-R1 / N01 / N02 — 冻结技术结论

## 4.1 R1

R1 已完成早期材质 evidence 纠错，状态：

```text
P4-M01-R1 = ACCEPTED / COMPLETE
```

## 4.2 DTX

> N05-B 来源纠正（§4.27）：下列统计仅保留为旧提取字节的历史观测。BornBeast PV/QV 等本轮目标此前读错物理分包；正确 PV 为标准 -5 / DXT1 / 1024×1024，不能继续沿用“无头/固定 FF 相位”作为其格式结论。

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

## 4.3 TGA

> N05-B 来源纠正（§4.27）：正确分包中的 BornBeast Alpha/Normal/Specular 均为可直接读取的标准 TGA，不需要下述 repair。历史修复产物不能继续作为这三个逻辑资源的原生像素来源。

Formal inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular repair 已结构验证；文件名不等于 shader role 证明。

## 4.4 WeaponShader CFG

> N05-B 来源纠正（§4.27）：正确 BornBeast CFG 是 492 字节 ASCII，含 `[Textures]`、`[Techniques]`、`[Properties]`。下列相位统计对应旧错源字节；LUT/packed constants 假设不适用于该已验证 CFG。其他文件尚未逐个回验，不能把整个旧 corpus 直接升级为原生格式证据。

237/237 文件满足：

```text
non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

已接受测量：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

证据等级：

```text
single-mod3 structure          STRUCTURALLY_VERIFIED
per-file measured sequence     OBSERVED
cross-skin differences         DIFFERENTIAL_SUPPORTED
CFG = 1D LUT                   HYPOTHESIS
CFG = packed shader constants  HYPOTHESIS
actual semantic consumer       OPEN_UNRESOLVED
Source1 mapping                SOURCE1_DESIGN_CANDIDATE
```

## 4.5 ArmModel positive control

ArmModel text CFG 已证明 engine-format 中存在：

```text
[Textures]
[Techniques]
[Properties] PieceIndex
```

但不能直接推出 weapon 使用相同 contract。

## 4.6 Weapon binding

```text
LTB post-mesh short ASCII field exists        STRUCTURALLY_VERIFIED
short id == texture/material slot             NOT PROVEN
repo parser semantic material use             NOT PROVEN
ObjExporter Models->ModelTextures mirroring   TOOL_BEHAVIOR
original CF piece->texture binding            OPEN_UNRESOLVED
```

Repo exporter 的路径镜像不是原 CF runtime proof。

## 4.7 N01 scope freeze

最终 scanner scope：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
config_index_keys                    = 18
config_index mapping tuples          = 72
raw_scan_files_seen                  = 355
raw_scan_files_decoded               = 355
```

统一 predicate：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

Scoped negative：

```text
BornBeast      text-config hits = 0
Transformers   text-config hits = 0
Jewelry        text-config hits = 0
BlueDiamond    text-config hits = 0
.dat consumer hits             = 0
BornBeast derived-output hits  = 4 / DERIVED_OUTPUT_HIT only
```

N01 在关闭当时的状态：

```text
P4-M01-N01 evidence      = COMPLETE / FROZEN
N01 old-corpus search    = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
engine binding closure   = OPEN_UNRESOLVED
```

这只描述 **旧 `data/**` corpus 的证据边界**；N02-A 后已取得新的本机 runtime 输入，不能再把整个 P4-M01 路线概括为“没有 runtime artifact”。

## 4.8 N02-A runtime acquisition freeze

Review 接受提交：

```text
a561924a9c0795932f328de929bee510f6e2719a
P4-M01-N02-A = ACCEPTED / COMPLETE
```

可信 runtime root：

```text
D:\Program Files\CF(2)
```

选择依据为本机只读观测同时存在：

```text
CF executable signal
REZ signal
rez/ directory
link.ini
```

N02-A 在该 root 建立 depth<=6、限定扩展名的 runtime artifact inventory：

```text
total candidates = 2273
.bin             = 1291
.rez             = 476
.dll             = 272
.ltc             = 73
.pak             = 58
.dat             = 44
.exe             = 27
.fxo             = 14
.ini             = 8
.lta             = 5
.fx              = 3
.lto             = 2
```

SHA256：

```text
2262 / 2273 captured
11 omitted = files >512 MiB, recorded explicitly as null
```

对 P4-M01 信息增益最高的新输入：

```text
73 x rez/Butes/*.ltc
35 x bf-prefixed .ltc within that set
rez/bf000.lta = 30,002 bytes
17 shader-bearing files (.fx/.fxo)
272 DLL + 27 EXE available for later static consumer tracing
476 REZ available for later bounded archive work
```

接受的边界：

- `rez/Butes/*.ltc` 的存在是 **真实 runtime artifact evidence**；
- 它们此前未被 N01 的 unpacked `data/**` config scope 覆盖，因此重新打开 config 路线；
- `bf` 文件名族只构成候选排序信号，**尚不能**证明 BornBeast / bdf / weapon binding；
- shader/EXE/DLL/REZ 目前只是 inventory candidate，尚无 strings/xref/decompile consumer proof；
- 其余 9 个硬编码候选 root 不存在只形成该探测集合内的 bounded negative，不代表对整机所有可能安装位置的穷尽证明。

当前状态更新为：

```text
runtime artifact acquisition blocker = CLEARED_FOR_STATIC_TRIAGE
engine binding closure               = OPEN_UNRESOLVED
CFG/render semantic closure          = OPEN_UNRESOLVED
P4-M01                                = INCOMPLETE
```

后续应优先从低成本、直接相关的 runtime config 证据开始；只有 config 路线不足时，再升级到 PE / shader / archive consumer tracing。

## 4.9 LithTech / CrossFire reference hierarchy

后续格式研究不再默认从 raw bytes 独立逆向。固定采用以下 reference hierarchy：

```text
1. public LithTech/Jupiter source
   -> 标准 engine/file/runtime semantics 的第一参考

2. CF-specific community tools
   -> CrossFire variant 的 positive control / differential clue

3. this repo CFRezManager
   -> 本项目资源入口、浏览、提取、快速 decode/preview implementation

4. current local CF runtime evidence
   -> 对当前 CrossFire 客户端实际行为的最终验真来源
```

核心原则：

```text
standard Jupiter behavior
-> compare existing CF tools / repo implementation
-> validate against current CF runtime artifacts
-> reverse only the remaining CF-specific delta
```

### 4.9.1 已确认的 public reference implementations

长期参考：

```text
https://github.com/no-lith/Jupiter
https://github.com/jsj2008/lithtech
```

已确认公开 Jupiter 源码包含或可追踪：

```text
LIB-ButeMgr
LIB-LTAMgr
LIB-DTXMgr
LIB-RezMgr
runtime/model
runtime/render / render_a / render_b
clientfx
controlfilemgr
```

`jsj2008/lithtech/runtime/model/src/model_load.cpp` 还直接暴露标准 Jupiter LTB 的 piece texture indices、render style、bone/node、animation compression/load contract，因此后续 LTB 研究应先做 Jupiter-vs-CF differential，而不是重复从零猜标准字段。

这些源码是 **REFERENCE_IMPLEMENTATION**，不是当前 CF client behavior 的自动证明；版本差异必须由本机 artifact 验证。

### 4.9.2 已确认的 CF-specific community references

可作为 positive control / differential reference：

```text
https://github.com/iQuitt/Vortigaunt
  LTB -> SMD with bones/animations
  DTX support
  REZ extraction explicitly tested with CrossFire

https://github.com/bxclip/Tool-Crossfire
  project declares LTB -> LTA / CFT -> CSV / LTC -> LTA
```

社区工具结论等级默认：

```text
EXTERNAL_TOOL_BEHAVIOR / POSITIVE_CONTROL
```

除非源码可审计并被当前 CF artifact 复现，否则不能直接升级为 runtime fact。尤其只提供 binary/rar 的工具不应作为 production dependency，也不应未经审计执行未知二进制。

### 4.9.3 CFRezManager role freeze

`CFRezManager` 的长期角色冻结为：

```text
REZ browse / inventory / extract / repack
format preview
DTX / image / audio / config / model quick decode
local deterministic conversion helpers
reference-adapter implementation
```

它 **不是** 整个 CF engine semantics 的唯一 authority。

当前 repo 已存在：

```text
CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs
```

该实现已经给出 LTC 的 deterministic native decode path；因此后续 N02-B 不应再把“LTC 是什么压缩/编码格式”作为首要逆向问题，而应先：

```text
validate existing LTC decoder on current runtime samples
-> recover decoded LTA/Bute-form content where possible
-> parse semantics using Jupiter Bute/LTA reference
-> correlate resource bindings
```

只有现有 decoder 与真实 runtime sample 不一致时，才进入 LTC format differential reverse。

## 4.10 N02-B-R1 / N02-C Review freeze 与 N02-D/E rework boundary

Review 接受：

```text
4d7c8b64d44c7d1848f1abb5182f511e5a91107f  P4-M01-N02-B-R1
2a4054dba6cc03bedb43201aa89692c6e0a36e88  P4-M01-N02-C
```

N02-B-R1 已确认当前 runtime `rez/Butes/*.ltc` 的真实 decode chain：

```text
raw magic 54 83 B2 E1
-> CrossFire wrapper XOR unlock
-> unlocked 00 00 00 00 header
-> LithTechLtcNativeDecoder
-> readable LTA/Bute-style text
```

当前样本：

```text
73 / 73 wrapper unlock success
73 / 73 native decode success
73 / 73 Bute/LTA-style parse success
```

因此以下长期事实可以冻结：

```text
current CF runtime Bute config layer exists                    VERIFIED_RUNTIME_INPUT
repo CrossFire LTC wrapper + native decoder works on 73/73    STRUCTURALLY_VERIFIED
weapon/resource relations exist in decoded Bute records        DIRECT_CONFIG_RELATION
```

N02-C 在 `bf005.ltc` 中找到 10 个 M4A1-family Weapon records，并直接读取：

```text
ModelFileName
SkinFileName
PViewModelFileName
PViewSkinFileName
RenderStyleFileName
PViewRenderStyleFileName
```

因此可以冻结：

```text
M4A1-family runtime config records found     ACCEPTED / COMPLETE
M4A1 config -> resource-path relation        DIRECT_CONFIG_RELATION
BornBeast direct config reference            NOT FOUND IN THIS SCOPED LAYER
```

注意：`BornBeast / Transformers / Jewelry / BlueDiamond` 在该 decoded Bute layer 中未命中，只是对声明 scope 的 bounded negative；不能推出这些 family 不存在于其他 config/material/runtime layer。

### N02-D / N02-E Review 结论

以下提交 **不冻结**：

```text
be1b150b0cc4e67e4861779079887f1cf243d9a1  P4-M01-N02-D
2f94db91099814523d9137f2c67f3ebfed7de869  P4-M01-N02-E
```

状态统一为：

```text
P4-M01-N02-D = REVIEW_REWORK_REQUIRED
P4-M01-N02-E = REVIEW_REWORK_REQUIRED
```

原因 1：N02-D 的 REZ recursion 没有把 directory parent path 写入 file entry，最终 index 实际为：

```text
lowercase basename -> REZ entries
```

而不是：

```text
archive-relative full logical path -> REZ entries
```

因此它不能区分例如：

```text
Models/PlayerView/PV-M4A1.LTB
ModelTextures/PlayerView/PV-M4A1.DTX
```

只按 basename 命中的结果不能升级为 exact runtime path binding。

原因 2：对没有扩展名的 `ModelFileName / PViewModelFileName`，N02-D 使用：

```text
.ltb / .dtx / .tga / .lto / .ltc / .rez / .dat
```

宽泛 fallback。该策略会把 model path 引向非 model artifact；在没有 consumer semantics 证据时不成立。返工后 extensionless model path 默认只允许按 field semantics 尝试 exact logical path + `.ltb`，其他扩展名必须另有证据。

原因 3：N02-E 直接继承 N02-D 的候选 entry，因此其 payload hash 虽然是对选中 offset/size 的真实机械测量，但 **不能反向修复错误或过宽的 path selector**。

N02-E 当前可保留为未冻结观测：

```text
29 selected unique REZ entries
12 catalog-MD5 matches
17 catalog-MD5 mismatches
0 skipped
0 selected payload SHA256 matches known P4 BornBeast source LTB SHA256
```

但不能把这组数字解释为：

```text
M4A1 exact runtime artifact closure
BornBeast runtime non-identity closure
```

直到 N02-D-R1 通过 full-path revalidation。

另外 N02-E 报告存在内部文字不一致：统计为 `12 MATCH / 17 MISMATCH / 0 skipped`，verdict 段却写成“全部 match 或 skipped”；该结论文本不得引用为冻结事实。

对 DTX MD5 mismatch 的 `LZX` 解释当前仅为：

```text
HYPOTHESIS / NEEDS_FORMAT_OR_CONSUMER_EVIDENCE
```

不能冻结为“REZ directory MD5 一定计算在某个 pre/post compression representation”之类的 engine fact。

原始 N02-D / N02-E 提交仍不冻结。后续 D-R1 / D-R2 / E-R1 / E-R2 已在 §4.11 接受。

## 4.11 N02-D-R1 / D-R2 / E-R1 / E-R2 freeze

Review 接受：

```text
f468e96f2d956ee82f69f8372c9c7c36423897ec  P4-M01-N02-D-R1
e6204b46e841b19386e82f4f103883981ae2ee07  P4-M01-N02-D-R2 review 6/6
c3e8872369aad29285cbf4ddb4a821a66eb127ba  P4-M01-N02-D-R2 refined checklist ACCEPTED
dc3ac1b69843141b54b2ae97b868aa4a7a242d01  P4-M01-N02-E-R1
2e0c750624832e28a5292a488b4bad81b3934c15  P4-M01-N02-E-R2
```

N02-D-R1 以 archive-relative full logical path 重做 REZ binding，60/60 `(WeaponName, field)` 命中。接受的规则：

```text
backslash -> slash, uppercase
strip one leading virtual root in {Models/, ModelTextures/}
keep RS/ (literal rf002.rez directory)
extensionless ModelFileName / PViewModelFileName -> only .LTB
multi-archive hits reported, no load-order authority claimed
```

因此：

```text
bf005 M4A1 exact REZ full-path binding    ACCEPTED / COMPLETE
```

N02-E-R1：8 个 N02-D-R1 LTB 解压后均无 Jupiter LTA `(piece` / `(texture` / `(renderstyle` / `(material` 原子，也无 `.dtx` / `.tga` 内嵌引用。LTB 内 piece→DTX/TGA 不能从该 binary 直接读出。

```text
LTB-internal piece -> texture/material    OPEN_UNRESOLVED
MATERIAL_BINDING_PARTIAL                  ACCEPTED as round status
```

N02-E-R2：24 个 unique `(rez_path, full_path)` payload 全部 bounded SHA256 成功，**0** 个等于 BornBeast P4 inventory。该结论把 N02-C 的 bf005 文本 negative 提升到 byte identity：

```text
bf005 M4A1 runtime family
!=
BornBeast native asset
SCOPED_NEGATIVE_ACCEPTED
```

N02-E 原始提交的 basename index / 过宽 extension fallback 仍不得引用。

## 4.12 N03-A freeze

Review 接受提交：

```text
23e275a4be0eed8fd90132095ed0c283b36a39d9  P4-M01-N03-A
P4-M01-N03-A = ACCEPTED / CANDIDATE_ONLY
```

从 BornBeast inventory 做 exact-token 反向查找（basename / stem / logical path / SHA256 / MD5；拒绝更长 ident 前缀）。

Loose config 范围：N02-A config-role ∪ `rez/Butes/` 目录，107 文件，73/73 LTC decode，7337 lisp records：

```text
DIRECT_CONFIG_FIELD hits     0
bounded text-token hits      0
```

因此：

```text
loose rez/Butes Bute+config layer
does not name BornBeast inventory assets
SCOPED_NEGATIVE_ACCEPTED
```

同一轮在当前客户端 REZ 中用 exact path（CFG 为 basename+size 过滤器）做 bounded payload SHA256，6/6 inventory 角色均命中：

```text
geometry   PLAYERVIEW/PV-M4A1_S_BornBeast.LTB
           rez/RF016.REZ, rez2/RF016.REZ, rez4/RF016.REZ
           SHA256 == inventory                          PAYLOAD_IDENTITY
base_dtx   PLAYERVIEW/PV-M4A1_S_BornBeast.DTX
           rez/rf017.rez                                PAYLOAD_IDENTITY
alpha      AlphaMap/M4A1_S_BornBeast_alpha.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
normal     NormalMap/M4A1_S_BornBeast_N.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
specular   SpecularMap/M4A1_S_BornBeast_S.TGA
           rez/rf017.rez                                PAYLOAD_IDENTITY
shader_cfg WeaponShader/M4A1_S_BornBeast.CFG
           rez/rf017.rez                                PAYLOAD_IDENTITY
```

`shader_cfg` 的 inventory 路径在 strip `ModelTextures/` 后变成 `SHADER/WEAPONSHADER/...`，runtime 实际为 `WeaponShader/...`（无 `Shader/` 前缀）。这是 normalisation miss，不是缺文件。

不能从 N03-A 推出：

```text
BornBeast has no runtime consumer anywhere
WeaponShader CFG is the consumer table
piece -> DTX/TGA binding
P4-M01 PASS
```

当前有效 closure 边界见 §4.13 更新后的表。N03-A 的 loose-config negative 仍然成立。

## 4.13 N03-B freeze

Review 接受提交：

```text
f839bdb2f572ad5269a263a62ed2b3e5f87cd947  P4-M01-N03-B
P4-M01-N03-B = ACCEPTED / BORNBEAST_CONSUMER_CONFIRMED
```

REZ-resident 扩展名选择：`.cft` `.lta` `.txt` + `BUTES/*.ltc`，1559 unique payloads。

```text
TABLE/*.CFT exact BornBeast tokens     0   SCOPED_NEGATIVE
.lta / .txt                            0   SCOPED_NEGATIVE
packed Butes/BF005.LTC hits            1 file
```

Consumer 不在 loose `rez/Butes/bf005.ltc`，而在：

```text
rez/RB001.REZ
  -> Butes/BF005.LTC
  size 5,892,359
  decode 8205 lisp records
```

该 packed payload 与 loose `rez/Butes/bf005.ltc`（N02-C / N03-A 用的那份）**不是同一文件**。

Canonical Weapon 记录：

```text
WeaponName     M4A1-黑骑士
StandardName   M4A1_S_BornBeast
PViewModelFileName  Models\PlayerView\PV-M4A1_S_BornBeast
PViewSkinFileName   ModelTextures\PlayerView\PV-M4A1_S_BornBeast.dtx
```

`PViewModelFileName` / `PViewSkinFileName` 精确对应 N03-A 已 SHA 验证的 inventory geometry + base_dtx。

同一 packed 表里还有一批变体，共用 `PV-M4A1_S_BornBeast` LTB，但 DTX 不同（NobleGold / BeijingOpera / PCCafe 等）。变体 DTX **不是** P4 inventory `base_dtx`。

N03-B 快照字段还包括：

```text
ModelFileName  Models\Weapons\QV-M4A1_S_BornBeast.ltb
SkinFileName   ModelTextures\Weapons\QV-M4A1_S_BornBeast.dtx
RenderStyleFileName        RS\NinjaTranslucent.ltb
PViewRenderStyleFileName   RS\PVModelDefault.ltb
BigIconName                M4A1_S_BornBeast
```

QV / RS 路径在 N03-B **未**做 payload SHA。Alpha / Normal / Specular TGA 与 WeaponShader CFG **没有**出现在已快照的文件路径字段里；`StandardName`/`BigIconName` 等于 CFG stem 只是 alias，不是 CFG 路径绑定。

不能从 N03-B 推出：

```text
P4-M01 PASS
TGA/CFG engine consumption contract
piece -> DTX/TGA
M4A1-黑骑士 == P5 雷神
```

当前有效 closure 边界：

```text
runtime root acquisition                 ACCEPTED
LTC wrapper/native decode                ACCEPTED
runtime Bute config parse                ACCEPTED
M4A1 config -> resource path             ACCEPTED
bf005 M4A1 exact REZ full-path binding   ACCEPTED
loose bf005 M4A1 != BornBeast payload    SCOPED_NEGATIVE_ACCEPTED
BornBeast runtime REZ payload identity   ACCEPTED
loose Bute/config BornBeast consumer     SCOPED_NEGATIVE_ACCEPTED
packed BF005 BornBeast consumer          ACCEPTED
  WeaponName M4A1-黑骑士
  -> PV LTB + PV DTX (inventory SHA)
QV / RS payload identity                 see §4.14
mesh/piece -> material binding           OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
TGA/CFG file-path on Weapon record       see §4.14
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

## 4.14 N03-C freeze

Review 接受提交：

```text
0e3c1e9130ea61cc2ed11c788cb33a1c6ba7d782  P4-M01-N03-C
P4-M01-N03-C = ACCEPTED / BUTE_MATERIAL_GRAPH_EXPANDED
```

Canonical packed Weapon 1002（`M4A1-黑骑士` / `StandardName=M4A1_S_BornBeast`）已 dump 105 keys + raw s-expression。7 个 `*FileName` 全部 REZ exact-path bind：

```text
PViewModelFileName   PLAYERVIEW/PV-M4A1_S_BornBeast.LTB     inventory SHA
PViewSkinFileName    PLAYERVIEW/PV-M4A1_S_BornBeast.DTX     inventory SHA
ModelFileName        WEAPONS/QV-M4A1_S_BornBeast.LTB        rez2 copy == local data
                                                            rez/ copy differs by 2 bytes
SkinFileName         WEAPONS/QV-M4A1_S_BornBeast.DTX        local data SHA
PreViewModelFileName WEAPONS/QV-M4A1_S_BornBeast_preview.LTB  bound, no local SHA
RenderStyleFileName  RS/NINJATRANSLUCENT.LTB (111 B)        bound
PViewRenderStyleFileName RS/PVMODELDEFAULT.LTB (119 B)      bound
```

`rez/` vs `rez2/` 的 QV LTB 字节不等；无 load-order authority，不得挑选“官方”副本。

Weapon raw 块内 inventory TGA/CFG exact path：**0**。`StandardName` / `BigIconName` = CFG stem 仅为 alias。RS LTB 与 WeaponShader CFG 无可打印 `.tga/.dtx/.cfg` 路径。

```text
Bute record binds LTB+DTX+RS only
TGA/CFG file-path on canonical Weapon     SCOPED_NEGATIVE_ACCEPTED
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
mesh/piece -> material binding           OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.15 更新。

## 4.15 N03-D freeze

Review 接受提交：

```text
04e8b425b32a6db24b24acea3f4c129c2f80f38b  P4-M01-N03-D
P4-M01-N03-D = ACCEPTED / PIECE_TEXTURE_INDEX_STRUCTURAL
```

Canonical `PLAYERVIEW/PV-M4A1_S_BornBeast.LTB`（`rez/RF016.REZ`，N03-C SHA）LZMA-alone 解压后是 Jupiter D3D 模型：

```text
LTB_Header fileType = 1 (LTB_D3D_MODEL_FILE)
LTB_Header version  = 9  (uint16 at offset 2, aligned 20-byte header)
model fileVersion   = 25
alloc.nPieces       = 11
stream nPieces      = 11
```

CF 相对 `ModelPiece::Load` 的 delta：fileVersion 25 **省略** 源码中已废弃的 min/max LOD offset 那对 uint32。后续 piece 用“下一个 uint16 名 + 合理 nLODs”扫描接上，不是完整 `CDIModelDrawable::Load`。

11 个 piece 全部 `nNumTextures = 0`。`m_iTextures[4]` 仍按 Jupiter 固定数组写出（手/QV `[0,1,0,1]`，枪身 `[0,1,2,1]`），**不是** DTX/TGA 路径。可见 PV 皮肤仍来自 Bute `PViewSkinFileName`。

QV LTB（`rez2` 副本）1 piece，同样 `nNumTextures=0`。

```text
LTB piece names + nPieces              STRUCTURALLY_VERIFIED
LTB extra texture filenames            SCOPED_NEGATIVE (nNumTextures=0)
index -> DTX/TGA path                  OPEN_UNRESOLVED
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
Jupiter LTB piece table on PV model      ACCEPTED
LTB extra texture filenames              SCOPED_NEGATIVE_ACCEPTED
index -> DTX/TGA path                    OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.16 更新。

## 4.16 N03-E freeze

Review 接受提交：

```text
043935f4ac948bcf30d6fa5d68371190569ac298  P4-M01-N03-E
P4-M01-N03-E = ACCEPTED / RENDERSTYLE_STRUCTURAL
```

`RS/NINJATRANSLUCENT.LTB` 与 `RS/PVMODELDEFAULT.LTB`（`rez/rf002.rez`）LZMA-alone 解压后是 Jupiter renderstyle：

```text
LTB_Header fileType = 5 (LTB_D3D_RENDERSTYLE_FILE)
LTB_Header version  = 3 (RENDERSTYLE_D3D_VERSION, uint16 at offset 2)
iRenStyleCnt        = 1
iRenderPasses       = 1
```

CF delta：byte 1 of the 20-byte aligned header is non-zero（model LTB 该位为 0）。

两文件均为单 pass：

```text
stage 0 TextureParam = RENDERSTYLE_USE_TEXTURE1
stage 1..3           = RENDERSTYLE_NOTEXTURE
BlendMode            = BLEND_MOD_SRCALPHA
```

解压体内无 `.cfg` / `.fx` / `.tga` / `.dtx` / `WeaponShader` 字符串。`USE_TEXTURE1` 与 Bute 单张 `PViewSkinFileName` DTX 一致；这两条共用 RS **不能** 选择 BornBeast TGA/CFG。

```text
shared RS samples TEXTURE1 only           STRUCTURALLY_VERIFIED
RS body names TGA/CFG                     SCOPED_NEGATIVE
```

当前有效 closure 边界：

```text
packed BF005 BornBeast consumer          ACCEPTED
canonical Weapon FileName graph          ACCEPTED
TGA/CFG as Weapon file-path fields       SCOPED_NEGATIVE_ACCEPTED
Jupiter LTB piece table on PV model      ACCEPTED
LTB extra texture filenames              SCOPED_NEGATIVE_ACCEPTED
shared RS TEXTURE1-only                  ACCEPTED
RS body TGA/CFG strings                  SCOPED_NEGATIVE_ACCEPTED
index -> DTX/TGA path                    OPEN_UNRESOLVED
CFG/render semantic closure              OPEN_UNRESOLVED
BornBeast native material closure        OPEN_UNRESOLVED
P4-M01                                   INCOMPLETE
```

该表被 §4.17 更新。

## 4.17 N03-F freeze

Review 接受提交：

```text
62bcce21aa2f808a230c040c58802a999f645295  P4-M01-N03-F
P4-M01-N03-F = ACCEPTED / CANDIDATE_ONLY
```

packed `Butes/BF005.LTC` 全部 8205 条记录：

```text
exact WeaponShader/M4A1_S_BornBeast.CFG     0
exact Alpha/Normal/Specular TGA paths       0
path segment WeaponShader/ or AlphaMap/     0
path segment SpecularMap/                   32 (other weapons only)
```

后期武器有 `SpecularMapName` → `ModelTextures\SpecularMap\*.dtx`（DTX，不是 TGA）。黑骑士没有该字段，也没有 `AlphaMapName` / `WeaponShader*`。四份 inventory 文件仍在 `rf017.rez`（存在 ≠ consumer）。

公开社区没有把 2013 年 WeaponShader CFG + Alpha/Normal TGA 的 **runtime 路径消费** 做成可审计 closure。已有成功仅限于：REZ/LTB/DTX 提取、OBJ/SMD 移植、CLIENTFX 特效、以及 Bute `SpecularMapName` 双贴图时代。

当前有效 closure 边界：

```text
packed BF005 exact TGA/CFG paths             SCOPED_NEGATIVE_ACCEPTED
SpecularMapName on later weapons (.dtx)      OBSERVED (not 黑骑士)
WeaponShader CFG runtime bind                OPEN_UNRESOLVED
P4-M01                                       INCOMPLETE
```

## 4.18 N03-G freeze

Review 接受提交：

```text
8386de1a852b0b726504ca7ca32b21def741e710  P4-M01-N03-G
P4-M01-N03-G = ACCEPTED / SCOPED_NEGATIVE
```

packed BF005 含 `LightCorrectionLegacyShader` / `SpecularMapName*` / `SpecularPower` 的记录 49 条：

```text
LightCorrectionLegacyShader values     18, all integer `1`
exact WeaponShader/*.CFG stem match    0
SpecularMapName                        SpecularMap\*.dtx only (later weapons)
M4A1-黑骑士 / M4A1_S_BornBeast         不在 dump 中（字段缺失）
```

`LightCorrectionLegacyShader` 是数值 flag，不是 CFG 名或路径。缺字段不是 StandardName 约定的证明。

当前有效 closure 边界：

```text
packed BF005 exact TGA/CFG paths             SCOPED_NEGATIVE_ACCEPTED
LightCorrectionLegacyShader                  SCOPED_NEGATIVE_ACCEPTED (int 1)
SpecularMapName on later weapons (.dtx)      OBSERVED (not 黑骑士)
WeaponShader CFG runtime bind                OPEN_UNRESOLVED
QV/PV DTX pixel role                         see N03-H
BornBeast native material closure            OPEN_UNRESOLVED
P4-M01                                       INCOMPLETE
```

## 4.19 N03-H freeze

> 2026-09-12 Review：先在 §4.26 收窄语义；随后 §4.27 证明本轮 BornBeast PV/QV 等旧输入读错分包。下述 negative 仅是历史 SHA 输入的结果，不能否定正确资源；已恢复真实 PV atlas，当前状态以 §0 / §4.27 为准。

Review 接受提交：

```text
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  P4-M01-N03-H
P4-M01-N03-H = ACCEPTED / SCOPED_NEGATIVE
```

```text
repo standard Jupiter decoder       0/16 weapon DTX
BornBeast *DTX size classes          524452 / 32932 / empty only
524452 guessed-layout preview       visually scalar_or_energy
actual codec / shader role          OPEN_UNRESOLVED
QV 32932 size-fit                    not a gun atlas
```

用户已授权后续 PE **静态** strings/xref。不附加调试器，不提交 CF binary。

当前有效 closure 边界：

```text
native gun-atlas via tested decodes  SCOPED_NEGATIVE_ACCEPTED
native albedo existence / codec      OPEN_UNRESOLVED
WeaponShader CFG runtime bind        OPEN_UNRESOLVED (N04 PE)
P4-M01                               INCOMPLETE
```

## 4.20 N04-A freeze

Review 接受提交：

```text
d770a0a2c46a3c02f910fb28034635adac95b458  P4-M01-N04-A
P4-M01-N04-A = ACCEPTED / FORMAT_STRING_HIT
```

```text
CShell_x64.dll   modeltextures\SpecularMap\%s
crossfire.exe    MODELTEXTURES\Shader\WeaponShader\
CShell Bute keys PViewSkinFileName / SpecularMapName / LightCorrectionLegacyShader
WeaponShader\%s.CFG                  NOT found
M4A1_S_BornBeast token               CLIENTFX particle, not material bind
crossfirebase.dll                    packed .tvm0, 0 token
```

当前有效 closure 边界：

```text
SpecularMap path sprintf             OBSERVED in CShell
WeaponShader directory prefix        OBSERVED in crossfire.exe
code xref / consumer function        OPEN (N04-B)
P4-M01                               INCOMPLETE
```

## 4.21 N04-B freeze

Review 接受提交：

```text
ca8c2209541bb60f7b8cc6b7cfb4cca4715475f2  P4-M01-N04-B
P4-M01-N04-B = ACCEPTED / XREF_FOUND_UNRELATED
```

```text
CShell_x64.dll  modeltextures\SpecularMap\%s   12 LEA
                nearby: modeltextures\playerview\
                not near Bute field names
crossfire.exe   WeaponShader\ prefix           0 RIP xref (packed .std)
```

这是后期 SpecularMap `.dtx` 拼接，不是黑骑士 TGA/CFG。

当前有效 closure 边界：

```text
SpecularMap\%s code xref             STRUCTURALLY_VERIFIED (later-era .dtx)
WeaponShader CFG code consumer       OPEN (packed exe, 0 xref)
P4-M01                               INCOMPLETE
```

## 4.22 N04-C freeze

Review 接受提交：

```text
ee092c317e3cbd42fedd130f864d022b270ab0bd  P4-M01-N04-C
P4-M01-N04-C = ACCEPTED / FXO_NAMES_GENERIC
```

```text
playerviewmesh.fxo   D3D9 effect, not DXBC
samplers             Diffuse/Specular/Normal/Alpha/Overlay/Mask/Noise
techniques           tPlayerViewMesh / tPlayerViewMeshEmsv
WeaponShader/CFG/TGA paths           none
```

用户已授权 packed `crossfire.exe` **额外静态**（不脱壳、不附加进程）。

当前有效 closure 边界：

```text
FXO sampler slots                    OBSERVED
WeaponShader CFG code consumer       OPEN (N04-D packed exe static)
P4-M01                               INCOMPLETE
```

## 4.23 N04-D freeze

Review 接受提交：

```text
d36bde10d3611c862fa49843cb28854fb4b75694  P4-M01-N04-D
P4-M01-N04-D = ACCEPTED / STRING_ISLAND_ONLY
```

```text
x64/crossfire.exe     stub, sole import crossfireBase.dll
WeaponShader island   dir prefix + adjacent .cfg, 0 xref
```

用户已授权 `.tvm0` 静态 + 若进程已运行则模块 dump。不启动游戏，不对抗 ACE。

当前有效 closure 边界：

```text
WeaponShader CFG code consumer       OPEN (N04-E)
P4-M01                               INCOMPLETE
```

## 4.24 N04-E freeze

Review 接受提交：

```text
be3edd98f236ef3263b3f37af0d4e3809753c0b2  P4-M01-N04-E
P4-M01-N04-E = ACCEPTED / STATIC_ONLY_NO_PROCESS
```

磁盘 `crossfirebase.dll` / `crossfire_x64base.dll` 为 `.tvm0`，0 WeaponShader token。当时无进程。

## 4.25 N04-F freeze

> 本节保留当时的进程读取结果；它不再阻断离线原生贴图/CFG 恢复，见 §4.27。

Review 接受提交：

```text
729c3a3dd8d31ccbc2fc2503c386b6d9a3fdbef0  P4-M01-N04-F
P4-M01-N04-F = ACCEPTED / DUMP_ACCESS_DENIED
```

```text
PID 33100 = D:\Program Files\CF(2)\x64\crossfire.exe
PROCESS_QUERY_LIMITED_INFORMATION  ok
PROCESS_VM_READ / SNAPMODULE       last_error 5
no dump files
```

当前有效 closure 边界：

```text
native gun-atlas via tested decodes  SCOPED_NEGATIVE (scope clarified in §4.26)
SpecularMap\%s (later-era .dtx)      STRUCTURALLY_VERIFIED in CShell
WeaponShader CFG code consumer       BLOCKED (packed .tvm0 + ACE denies VM_READ)
P4-M01                               INCOMPLETE
```

活状态以 **§0** 为准。

---

## 4.26 2026-09-12 Planner 证据边界审计

> 这是 N05-A 前的历史审计。下表旧 PV/QV SHA 已在 §4.27 被定位为错误物理文件切片；“未找到恢复算法 / actual codec open”不是最新结论。无需新 codec 即可解码正确分包中的这两个目标。

本节冻结的是代码与证据的适用范围修正，不是新的 decode / native PASS。此次没有重跑 N03-H，也没有更改其历史 report、JSON、预览或本地用户修改。

1. N03-H 的 `official_decode()` 实际调用的是**本仓库** `CFRezManager --decode-image`，不是 CF 官方解码器。0/16 失败只能说明该实现未支持这些输入；所有目标都失败的集合不能充当正确性阳性对照。
2. `n03h_dtx_container_decode.py` 的 `layout_candidates()` 使用固定尺寸列表，`brute_decode()` 只执行排序后的 `[:limit]`（默认 8）。例如列表未含 `1024×512` / `1024×1024`，没有穷尽同容量的 BC/RGB 组合。`size_family()` 又直接把 524452 命名为 `pv_bgr24_512x256_mip`，这是假设标签，不是解析出的 header。纠正方法是建立格式证据，不是把盲试范围无限扩大。
3. 原 N03-H 报告末尾本来就限定为“按现有解码”，并明确 QV codec / trailer 语义未闭合。§0 原先写“PV 是能量层、没有 512×512 原生枪身图”超出该证据，现收窄为 **tested decode negative / actual codec open**。R1 测得的字节相位、文件体积、size residue 仍有效，但像素尺寸、mip、能量层/LUT 等解释不能升级。
4. N03-A 已证明若干 REZ entry raw SHA 与 loose SHA 相等；这排除了这些样本在那次复制中被改变，不能单独证明 entry 就是 runtime 最终使用的资源或已经是可直接解码表示。N03-C 的实际 Bute path binding 仍然有效，必须与 codec / override resolution 分开。
5. N04-C 报告明确未反编译指令流；它已观测到 D3D9 effect/槽名，但尚未使用 D3DX effect API 分析公式。因此“没有路径字符串”不能关闭离线 shader 语义路线。具体技术可行性来源见 §0.4；是否兼容该 FXO 仍待下一轮实验。

此次只读补充测量（有符号 little-endian int32；PV/QV exact path 见 N03-H）：

| 样本 | SHA256 | offset 4 | offset 8 | 对 RezExtract 换位规则的结论 |
|---|---|---:|---:|---|
| BornBeast PV DTX | `c419a5fb164db6085878ff2efe21d318a85186b4e3c1fd6baba920311f6ea1d9` | 460783386 | -14977025 | 两处都不是 -2/-3/-5；单纯互换不能恢复合法 version |
| BornBeast QV DTX | `ea99c7101708b6dc04e3ab97f232f683f8b996a68e2e5b5fc1167c6cd08c0f7a` | -15794177 | -61697 | 同上 |

这些是 `OBSERVED / STRUCTURALLY_VERIFIED` 的窄结论；**未找到可以直接恢复当前样本的新算法**。A 的价值是定位实际失败层，B 的价值是打开未做过的 shader 指令分析；都不能保证最终恢复。停用的仍是 N04 进程读取路线，P4-M01 离线研究不再整体 STOP。

---

## 4.27 2026-09-12 N05-A Review / N05-B 分包恢复冻结

```text
Reviewed N05-A : 32d2ec2e72439be28c471139e6f2e5805ae73729
Evidence      : 37d231ddc3ce0409b39ca05aad743f3d91875f52
N05-A review  : ACCEPTED_WITH_CORRECTIONS
N05-B result  : PV_DTX_AND_TEXT_CFG_RECOVERED_FROM_NUMBERED_PARTS
P4-M01        : INCOMPLETE
```

证据与复现入口：

- [N05-B report](work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/report.md)
- [9 个目标的来源、MD5、SHA256、解码与对照结果](work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/recovery.json)
- [恢复的 PV 原生像素](work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/bornbeast_pv_dtx.png)、[解析的 CFG](work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/bornbeast_cfg.json)
- `python -B scripts/material_recovery/n05b_shard_material_recovery.py`（本机 Python 完整路径见 report）

**根因与验证范围**：`rez/rf017.rez` 是目录所在文件；本次 9 个材质 entry 的 legacy `time` 字段分别指向同目录 `rf017_<time>.rez`。相同 offset/size 在对应分包内的字节与目录 MD5 **9/9 精确一致**，主文件切片均不匹配。读取器必须同时验证候选来源和内容，不可只比较错误主文件切片与 loose 副本是否相等。正常单文件 REZ 仍可使用 timestamp；本结论不把所有版本的 `time` 无条件改定义。

| 逻辑资源 | 分包编号 | 已验证结果 |
|---|---:|---|
| `PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` | 8 | -5 / DXT1 / 1024×1024 / 1 mip，164 字节 header + 524288 payload |
| `WEAPONS/QV-M4A1_S_BornBeast.DTX` | 13 | -5 / DXT1 / 256×256；与 rez2 的 QV 1024 是不同有效副本 |
| RoyalDragon PV / Specular | 8 / 12 | -5 / DXT1 / 1024×1024 |
| GreenVein Specular | 12 | -5 / DXT1 / 512×512 |
| BornBeast Alpha / Normal / Specular TGA | 2 / 6 / 12 | 标准 1024×1024 TGA，直接解析，无 inserted repair |
| BornBeast WeaponShader CFG | 9 | 492 字节 ASCII，三个 INI section |

PV 的完整来源：offset `186436476`、size `524452`、目录 MD5 `C242A039731CF13CF9570BC2A56DC77F`、SHA256 `a30c9a271612dec05cb44f44e6e9412be398350e5fb6ac93966aea4b7f56b4ba`。Python 与现有编译的 CFRezManager 图像 decoder 输出 RGBA **逐像素完全一致**。这证明 decoder 在取得正确字节后可用，不证明 CFRezManager 的归档读取已经修好。PNG 保留原始暗色，不提亮、不混入外部像素。

CFG 明文直接引用 `SpecularMapName2=M4A1_S_BornBeast_S.tga`、`NormalMapName2=M4A1_S_BornBeast_N.tga`、`AlphaMapName2=M4A1_S_BornBeast_alpha.tga`、`EnvCubeMapName2=Black_Shader03.dds`，并给出 mapping 开关及 `LightBrightness=0.01`、`EnvCubeMapBrightness=4`、`DiffuseBoost=0.1` 等参数。文件引用和值属于直接证据；`2` 后缀语义、piece/sampler/technique 选择及实际运行值仍未闭合。命名 cube 尚未在本轮提取。

**N05-A 纠错**：

1. `scan_local_control_dtx()` 把 64 字节前缀传入要求完整 LT2 header/payload 的 parser，已用合法 292 字节合成 DTX 复现假阴性。现改为先用 8 字节筛选版本，再读完整文件验证；新增两项扫描回归测试。
2. 修复后旧 `data/rf017/ModelTextures` 仍是 0/3258。这只描述旧提取目录，不能推出安装目录内没有合法 DTX；本轮正确分包正例已经反证后者。未覆盖旧 data 来改变测量结果。
3. N05-A 的 `rez2/RF017.REZ` QV SHA `73a954f8540cd7660c1a6cc1b65dc240c2421c37909e7a8f35d4e6f789b59965` 仍是有效正例；其两个已保存预览也精确匹配。未把 QV 套到 PV，也未声称 rez2 有 runtime 加载优先权。
4. N05-A 的 `dtx_Create=True` 是 Python 移植的结构门槛，不是运行上游 C++ 工具；合成色块不能验证所有 mip / alpha 行为。
5. 历史 R1/N03/N05-A 的相位、尺寸和 hash 测量保留为原 SHA 的观测。对本轮已证实错源的目标，撤回其作为当前逻辑资源格式/像素语义的依据；不据此无证据地否定或确认其他 BF/RS/LTB 资源。

**工程验证与剩余边界**：7 项回归测试通过；5 项 resolver 测试覆盖主文件范围合法却内容错误、分包范围超出主文件、普通 timestamp、错误 MD5、多候选匹配。主索引 4417 entry 中有 155 个 range 超出主文件长度，**不能因此判为资源损坏**，应按所选分包检查边界。新 helper 只在唯一候选通过 MD5 时返回字节。

当前正式归档提取、Explorer/模型预览及缓存仍待 N05-C 接入；旧工具不得重建 final 输入。正确 PV LTB/UV、命名 cube、CFG 到 shader 的绑定与 Source 1 渲染仍待验证，§3 PASS Gate 未满足。本轮没有修改 P4 frozen build、游戏进程、原始输入或已有用户工作。

---

## P5-T01 — Official reference

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
Target = M4A1-雷神
```

Ground truth：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

## Legacy pre-scan

历史 commit：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

保留统计：

```text
data inventory       165082 files
recalled candidates    2856
LTB candidates         1281
canonical inspected     441
```

旧 score 只表示召回优先级，不表示 identity confidence。

## P5-T02

依赖 P4-M01 native material method。用户 2026-09-13 已开做。

```text
validated material method          DONE (N05-C)
-> Transformers family inventory   DONE (973 hits / 77 PV DTX)
-> DTX/TGA/CFG revalidation        DONE (MD5-verified; base==PC)
-> material binding                CFG Name2 + same-stem only; no Bute
-> native finalist render          DONE gate/gate_sheet.png
-> USER LOCAL-CANDIDATE GATE       DONE (Blender)
-> USER_VISUAL_MATCH_CONFIRMED     base PV-M4A1_S_Transformers
-> LTB X mirror                    applied in Blender preview
```

`USER_VISUAL_MATCH_CONFIRMED` 仍不等于最终 `IDENTITY_CONFIRMED`。

## P5-T03

```text
P5-T03 = RESOURCE_GRAPH_RECORDED
```

```text
PLAYERVIEW LTB
-> texture/material/shader resources
-> world/QV
-> audio
-> animation/config
```

已记录 path / SHA / size / relation / source / confidence。Canonical Bute：`rez/Butes/BF005.LTC` record 856，WeaponName `M4A1-雷神`。Identity-core 无独立 WAV。

证据：

```text
work/p5_leishen/t03/report.md
work/p5_leishen/t03/resource_graph.json
work/p5_leishen/t03/bute_canonical.json
```

## P5-T04

```text
P5-T04 = IDENTITY_CONFIRMED
```

本地身份 = base `PV-M4A1_S_Transformers`。只有 `IDENTITY_CONFIRMED` 才进入 P6。P6 已由用户 2026-09-13 开做并部署。

证据：

```text
work/p5_leishen/t04/identity_review.json
work/p5_leishen/t04/report.md
```

---

# 6. P6 — Final replacement / release

```text
P6 = P6_IDENTITY_REPLACEMENT_DEPLOYED
final_target_identity = true
final_cf_material     = false
addon                 = p_cf_leishen_m4a4_p6
runtime slot          = M4A4 / weapons/v_rif_m4a1.mdl
```

用户 2026-09-13 在 `IDENTITY_CONFIRMED` 之后明确开 P6。已完成：

```text
verified Transformers PV LTB/DTX/TGA/cube
-> frozen C3 M4A4 matrix
-> Source X mirror through 0 + reverse faces
-> SMD / QC / studiomdl
-> N05-J formula VMT (AlphaMap.b = $envmapmask)
-> package
-> deploy (N05-J parked; frozen parked, unmodified)
```

还不是：

- P4-M01 PASS / lighting match
- release-quality runtime verification（模型用户已看过；枪声等待听音 Gate）
- P7 Inspect / 原动画 / world model（S01 原声已接受；S02 Inspect 已接受但手指穿模仍记；S03 world 已部署待看）

证据：

```text
work/p5_leishen/p6/report.md
work/p5_leishen/p6/execution.json
work/p5_leishen/p6/mapping.json
```

---

# 7. P7 — Enhancement

不阻塞前述 closure：

```text
visible Inspect            <- P7-S02 USER_ACCEPTED (CS lookat); INSPECT_CLIPPING_NOTED
hand / finger IK           <- open (F 检视小穿模)
Blender retarget / penetration avoidance
CF original animation      <- P7-S04 clips DECODED; not on viewmodel yet; retime P7-S01 when wired
CF original sound          <- P7-S01 USER_ACCEPTED on CS timing; SOUND_RETIME_REQUIRED_ON_CF_ANIM
world model / extra polish <- P7-S03 USER_ACCEPTED
```

## 7.1 P7-S01 CF original sound

```text
P7-S01 = P7_ORIGINAL_SOUND_DEPLOYED
addon  = p_cf_leishen_m4a4_p7_sound
source = rez/FMODStudio/Weapons/M4A1IronBeast.bank
event  = ShootM4A1-S-Beast (Bute; FMOD, not REZ WAV)
slot   = CS:GO M4A4 Weapon_M4A1.Single / clip / distant
```

用户 2026-09-13 「好了」：按 CS 动作对齐的声音已接受。**替换 CF 原动作后必须再调声音时间**（`SOUND_RETIME_REQUIRED_ON_CF_ANIM`）。

## 7.2 P7-S02 visible Inspect

```text
P7-S02 = P7_VISIBLE_INSPECT_DEPLOYED
inspect_policy = official_cs_lookat
cf_original_animation = false
```

P6 Inspect 从 frozen idle 换成官方 M4A4 lookat01/prepare/loop。不是 CF 检视。声音未改。用户 2026-09-13 接受，F 时手指小穿模记下。

证据：

```text
work/p5_leishen/p7_s02/report.md
work/p5_leishen/p7_s02/execution.json
```

## 7.3 P7-S03 world / dropped model

```text
P7-S03 = P7_WORLD_MODEL_DEPLOYED
source = Bute QV-M4A1_S_Transformers.LTB + QV DTX
slot   = weapons/w_rif_m4a1.mdl + weapons/w_rif_m4a1_dropped.mdl
addon  = p_cf_leishen_m4a4_p6 (world files added; v_rif hashes unchanged)
```

QV 单 piece，官方 mag bodygroup blank。皮肤只用 QV DTX。未改 frozen / P7-S01 声音 / 第一人称网格。用户 2026-09-13 「可以」。

## 7.4 P7-S04 CF original animation decode

```text
P7-S04 = P7_CF_ANIM_CLIPS_DECODED
source = PV-M4A1_S_Transformers.LTB (Jupiter ModelAnim, compression NONE)
clips  = reload 1600ms / select 640ms / idle_0 3000ms / fire 90ms / prefire / postfire / run / knife-attack
reload events = smoke@0, WeaponClipOut@194ms, WeaponClipIn@718ms, WeaponReload@1211ms
viewmodel     = not replaced (P6 still CS skeleton weights)
```

证据：

```text
work/p5_leishen/p7_s04/report.md
work/p5_leishen/p7_s04/execution.json
```

证据：

```text
work/p5_leishen/p7_s03/report.md
work/p5_leishen/p7_s03/execution.json
work/p5_leishen/p7_s03/mapping.json
```

证据：

```text
work/p5_leishen/p7/report.md
work/p5_leishen/p7/execution.json
work/p5_leishen/p7/mapping.json
```

---

# 8. Evidence 等级约定

| Grade | 含义 |
|---|---|
| `OBSERVED` | 当前样本直接观测 |
| `STRUCTURALLY_VERIFIED` | 格式/二进制结构机械验证 |
| `VERIFIED_CORPUS_STATISTIC` | 在明确 corpus/scope 内可复现统计 |
| `DIFFERENTIAL_SUPPORTED` | 多样本差分支持 |
| `STRONG_HYPOTHESIS` | 强线索但仍有替代解释 |
| `HYPOTHESIS` | 待验证解释 |
| `TOOL_BEHAVIOR` | 本仓库工具行为，不等于原 CF runtime |
| `EXTERNAL_TOOL_BEHAVIOR` | 外部工具声明/行为，只作参考或 positive control |
| `REFERENCE_IMPLEMENTATION` | 公开 engine/reference source 的标准实现，不自动等于当前 CF variant |
| `SOURCE1_DESIGN_CANDIDATE` | Source 1 实现候选，不等于 CF 原语义 |
| `NEGATIVE_RESULT_SCOPED` | 仅在声明范围内成立的 negative |
| `OPEN_UNRESOLVED` | 当前未闭合 |
| `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` | 缺 engine consumer 新输入 |

禁止把 filename convention、视觉相似、单一统计、reference implementation、external tool behavior 或 hypothesis 直接升级为当前 CF runtime verified fact。

---

# 9. 关键 Evidence / Checkpoint 索引

## P4

```text
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
work/m4a1_s_bornbeast/p4_prototype_01/
```

## P4-M01 / N01 / N02 / N03

```text
work/m4a1_s_bornbeast/p4_m01_native_material/
work/m4a1_s_bornbeast/p4_m01_native_material/n01/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03a_bornbeast_consumer/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03b_rez_packed_config/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03c_material_graph/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03d_ltb_piece_index/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03e_renderstyle_ltb/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03f_shader_alphamap_lookup/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03g_legacy_shader_fields/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n03h_dtx_container_decode/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04a_pe_string_hits/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04b_pe_xref/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04c_playerviewmesh_fxo/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04d_packed_crossfire_static/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04e_vm_dump/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n04f_process_dump/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05a_decoder_audit/
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/
```

## External reference implementation / positive control

```text
https://github.com/no-lith/Jupiter
https://github.com/jsj2008/lithtech
https://github.com/iQuitt/Vortigaunt
https://github.com/bxclip/Tool-Crossfire
```

## P5

```text
work/p5_leishen/t01_reference/
work/p5_leishen/t01/
work/p5_leishen/t02/
work/p5_leishen/t02_native/
work/p5_leishen/t03/
work/p5_leishen/t04/
work/p5_leishen/p6/
work/p5_leishen/p7/
work/p5_leishen/p7_s02/
```

关键历史提交：

```text
10aa99b770e575300ca3c28324ef3de3d5b70c6b  P4 frozen baseline
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d  RV-04 evidence
632ede449578f688cea7e6b5f40cbf03700aaaa5  P4-M01 initial exploration
0dc5793b6e47cb20da9e44aebcec2195194bd6f2  R1 narrow correction
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19  N01 Phase-0 cleanup
69c03d8769db2107cd94cae11accc750716466ae  scanner/lineage repair
ea11ba143d859193213f24ab92248ff8a576b135  runtime-consumer bounded search
46fcacebbc631fc05e0d491470b5e5482bca4533  evidence cleanup
95b6bb363a5f00daf01193f53e2a27cff9cea3f8  provenance/closure cleanup
65292c742d545459974c56aec494d1d9c44039a8  final config-scope guard
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2  P5 legacy pre-scan
a561924a9c0795932f328de929bee510f6e2719a  N02-A runtime root + artifact inventory
4d7c8b64d44c7d1848f1abb5182f511e5a91107f  N02-B-R1 wrapper + native LTC decode accepted
2a4054dba6cc03bedb43201aa89692c6e0a36e88  N02-C M4A1 runtime config binding accepted
be1b150b0cc4e67e4861779079887f1cf243d9a1  N02-D REVIEW_REWORK_REQUIRED (superseded by D-R1)
2f94db91099814523d9137f2c67f3ebfed7de869  N02-E REVIEW_REWORK_REQUIRED (superseded by E-R2)
f468e96f2d956ee82f69f8372c9c7c36423897ec  N02-D-R1 path-aware REZ binding accepted
c3e8872369aad29285cbf4ddb4a821a66eb127ba  N02-D-R2 review accepted
dc3ac1b69843141b54b2ae97b868aa4a7a242d01  N02-E-R1 LTB piece table absent
2e0c750624832e28a5292a488b4bad81b3934c15  N02-E-R2 bf005 != BornBeast payload
23e275a4be0eed8fd90132095ed0c283b36a39d9  N03-A BornBeast REZ payload identity, loose-config miss
f839bdb2f572ad5269a263a62ed2b3e5f87cd947  N03-B packed BF005 M4A1-黑骑士 consumer
0e3c1e9130ea61cc2ed11c788cb33a1c6ba7d782  N03-C canonical 黑骑士 FileName graph
04e8b425b32a6db24b24acea3f4c129c2f80f38b  N03-D PV LTB Jupiter piece table, nNumTextures=0
043935f4ac948bcf30d6fa5d68371190569ac298  N03-E shared RS TEXTURE1-only, no TGA/CFG strings
62bcce21aa2f808a230c040c58802a999f645295  N03-F packed BF005 no WeaponShader/AlphaMap paths
8386de1a852b0b726504ca7ca32b21def741e710  N03-G LightCorrectionLegacyShader is int 1, SCOPED_NEGATIVE
3c29eb58691cc7b0d6fe70297fbb427dbc14d2d6  N03-H tested-decode negative (scope corrected in §4.26)
d770a0a2c46a3c02f910fb28034635adac95b458  N04-A CShell SpecularMap\%s; WeaponShader dir prefix
ca8c2209541bb60f7b8cc6b7cfb4cca4715475f2  N04-B CShell LEAs SpecularMap\%s; WeaponShader 0 xref
ee092c317e3cbd42fedd130f864d022b270ab0bd  N04-C playerviewmesh.fxo sampler slots, no paths
d36bde10d3611c862fa49843cb28854fb4b75694  N04-D packed crossfire.exe stub; WeaponShader island only
be3edd98f236ef3263b3f37af0d4e3809753c0b2  N04-E crossfirebase.dll .tvm0; no CF process
729c3a3dd8d31ccbc2fc2503c386b6d9a3fdbef0  N04-F OpenProcess VM_READ denied (error 5)
32d2ec2e72439be28c471139e6f2e5805ae73729  N05-A decoder/provenance audit (review corrections in §4.27)
37d231ddc3ce0409b39ca05aad743f3d91875f52  N05-B MD5-verified numbered parts recover PV/TGA/text CFG
```

---

# 10. 文档职责

```text
README.md  项目介绍、角色分工、阅读入口
AGENTS.md  只规定 Git 操作
plan.md    本文件：§0 当前状态/当前任务 + 长期 pipeline + 冻结事实 + Gate
task.md    短指针，指向 plan.md §0（不再单独维护执行单）
```

领导/规划 Agent 每轮 Review 后更新 `plan.md` §0（当前状态与下一任务）。冻结事实写入对应 §4.x。Executor 只执行 §0.2 里的 ACTIVE 任务；§0.2 为 NONE 时 STOP。
