# CF → CS:GO Legacy 移植 Pipeline

> 方法链沿用已验证的 CF 原生管线（**附录 A**；参考实现 `scripts/p5/p5_p7_s05_cf_native_vm.py`、`work/galil_ace_tianxi/native_vm/build_galilace_vm.py`）。
> **附录 B** 是天袭 idle 光效冻结（2026-09-16）。
> 活任务写在本文对应武器节；Git 规则看 `README.md` §5。
>
> **当前活任务（2026-09-19）**：把 CS 原版 Glock（`v_pist_glock18`）替换为 CF **毛瑟-天秤座**（`M1896_Libra`）。走完整原生管线。
> 屠龙-春桃刀 P0–P7 完成、等用户 MIGI REBUILD 与 P8 验收，见下文「屠龙-春桃」节；天袭（Galil AR）已冻结，见「Galil ACE-天袭」节。

---

# 毛瑟-天秤座 → CS:GO Glock-18

> 用户 2026-09-19 任务：把 CS 里的 Glock（`v_pist_glock18`）替换为 CF 的 **毛瑟-天秤座**。

## M.0 身份确认（已查证 2026-09-19）

Bute `rez/Butes/BF005.LTC` Weapon 记录 #1462 / #1794（MD5 校验解码，两条字段相同）：

```text
WeaponName    = 毛瑟-天秤座
StandardName  = M1896_Libra
PViewModel    = Models\PlayerView\PV-M1896_Libra        <- 网格/动画
PViewSkin     = ModelTextures\PLAYERVIEW\PV-M1896_Libra.dtx
QV            = Models\Weapons\QV-M1896_Libra.ltb
PVEffectName  = pv_gun_mauser_libra                    <- idle 特效存在，首轮不做
GViewAnim     = mauser / Pistol；GVModelScale=1.5
FireAnimMultiplier=3.5  ChangeWeaponAnimRatio=1.1  ReloadAnimRatio=1.1
```

同族排除：`M1896`（原版毛瑟）、`M1896_USS`（多皮肤共用壳）、`M1896_Hellfire`/`_Gold`/`_RoyalDragon10`/`_UltimateGoldsmith`/`_Valentine2020`/`_Festa_*`/`_BluePottery`/`_Flamingo` 等其它皮肤；`PI_MAUSER`（更早一代旧模型）；`PV-M1896_Libra_{BL,GR,WOMAN_*}` 是同模型 socket/手型变体。

证据：`work/mauser_libra/scan/bute_mauser_libra.json`（记录 #1462/#1794）、`scan/index_hits.json`。

Bute 声音名（#1462）：Shoot=`ShootMauser`→`snd/weapon/Mauser/Mauser_Shoot`，ClipOut=`Mauser_ClipOut`，ClipIn=`Mauser_ClipIn`，Reload=`Mauser_Reload`，Select/BlowBack=`Mauser_Select`；Extra01/02=`M14EBR_Taurus_CoinSelect`（星座彩蛋音，首轮可挂 draw）。`SND/**/*.WAV` 是加密容器，PCM 仍走 FMOD `Weapon.bank`。

## M.1 CF 资产图（全部走 MD5 分片校验读 `read_verified_payload`）

| 角色 | REZ 内路径 | 所在包 | 备注 |
|---|---|---|---|
| PV LTB（枪+手臂骨架+动画） | `Models/PLAYERVIEW/PV-M1896_Libra.LTB` | `rez/RF016.REZ` | 166932B |
| PV 贴图（diffuse） | `ModelTextures/PLAYERVIEW/PV-M1896_Libra.DTX` | `rez/rf017.rez` | 524452B |
| 材质 CFG | `ModelTextures/Shader/WeaponShader/M1896_Libra.CFG` | `rez/rf017.rez` | 475B |
| Specular | `ModelTextures/SpecularMap/M1896_Libra_S.TGA` | `rez/rf017.rez` | 3.1MB TGA |
| Normal | `ModelTextures/NormalMap/M1896_Libra_N.TGA` | `rez/rf017.rez` | 3.1MB TGA |
| Alpha | `ModelTextures/AlphaMap/M1896_Libra_alpha.TGA` | `rez/rf017.rez` | 3.1MB TGA |
| socket 变体（特效挂点参考） | `PV-M1896_Libra_{BL,GR}.LTB` | `rez/RF016.REZ` | 65KB；含 `fix_effect_*` socket，备用 |
| QV（第三人称，可选） | `QV-M1896_Libra.ltb` + `QV-M1896_Libra.DTX` | `rez/RF016` / `rez/rf017` | 首轮只做第一人称 |
| 手膜（默认） | `Arm_Nini_GR.LTB` + `FVIEW_{HAND,ARM}_Nini_GR` | 复用天袭 `decode/nini_gr/` | **妮妮-保卫者**；见 A.9 |

## M.2 CS 侧目标

| 项 | 值 |
|---|---|
| 槽位 | Glock-18（CT 默认手枪） |
| 模型 | `models/weapons/v_pist_glock18.{mdl,vvd,vtx,ani}` |
| 参考 | stock `v_pist_glock18` QC/序列名/挂点 + `game_sounds_weapons` 的 `Weapon_Glock.*` |
| 声音路径 | `sound/weapons/glock/*.wav`（以 stock manifest 为准） |
| 部署 | 新 addon `p_cf_mauser_libra_p1`，只放第一人称资产 |

## M.3 阶段流程（evidence 进 `work/mauser_libra/`）

沿用 §3 / 附录 A 全部硬规则：REZ 分片校验、UV `v→1-v` 一次、H 后绕**枪身中心**镜像、CS `Bip01*` 钉 `(0,+500,0)`、只超 diffuse、默认妮妮手膜 A.9 / 油光 A.8.2、枪身金属 Phong A.8.1（无 envmap）、MIGI A→B→用户 REBUILD→C。

| 阶段 | 脚本 | 状态 |
|---|---|---|
| 身份 | `scan/scan_index.py` `scan/scan_bute.py` | PASS（记录 #1462/#1794；PV/QV/贴图/CFG 全部命中） |
| P0 | `acquire/acquire_assets.py` | PASS（10/10 资产 MD5 分片校验 → `acquire/verified_root/`） |
| P1 | `decode/decode_assets.py` | PASS：59 骨 / 12 mesh（`PV-Mauser_Libra` 1798v 刚性绑 Dummy01；reload/reload02→Box03/Box02；coin→Box010；Line→Box011；bull 系→Box04/Box09 链）；clips=`prefire/postfire/run/fire/select/reload/idle_0`；diffuse 1024 DXT1 |
| P2 | 默认 SKIP | — |
| P3 | `csref/extract_glock_ref.py` `csref/fit_transform.py` | PASS：stock v_pist_glock18 反编译（6 序列：idle/firesingle/firelast/draw/reload/lookat01）；H 复用天袭（s=2.0025，同一 FvARM playerview 空间）；MX 绕枪身 bbox x 中心 -6.98；挂点 flash/shelleject/stattrack/uid 取自 stock idle f0 |
| P4 | `texture/build_textures.py` | PASS：ComfyUI 4x→2048 BGRA8888；VMT Phong 48/8 + Half-Lambert + CF normal，无 envmap |
| P5 | `native_vm/build_mauser_vm.py` | PASS：114 骨；Nini GR LBS；6 序列；刚性件按 bind 局部匈牙利分配一对一绑定；draw/reload 挂投币音事件；studiomdl 一次通过 6 文件齐全 |
| P6 | `sound/build_sound_overlay.py` | PASS：**SND WAV 实为 LZMA 压缩 RIFF**（0x5D 头直接 lzma 解，非加密）；Mauser_{Shoot,Select,ClipOut,ClipIn}+Taurus Coin{Select,Reload} 44.1k PCM16 → 8 个 glock18 wave 路径 |
| P7 | A→B hash；用户 MIGI REBUILD；B→C | A/B **23/23** SHA-256 一致。**等用户 MIGI REBUILD** |
| P8 | 用户游戏内验收 | GATE：v1 偏近→手调 push；v3 骨骼点对位残差→手臂穿相机（失败）；v5 顶点云对齐→远近正确但枪管正对视线显"正脸"；v6 +CF偏轴偏航→过度；v7 屏幕解算（f=565 假设错）→**截图证实用户测的是 v6 旧版**；v8 **CF质心屏幕位置重定位**已部署待复测 |

### P3c 自动残差 VIEW 拟合（`csref/fit_view.py`，未来武器通用）

**问题**：H 是骨架级配准（FvARM playerview 空间→眼位空间），不归一化逐武器落点——CF 每把枪离 Scene Root 的固有偏移被原样带入（手枪天然贴脸、步枪靠前），手调 push 不可持续。

**失败教训（v3，勿复用）**：不要把 CF 骨骼点锚到 stock 骨骼点——两套 rig 身体/手臂相对手的排布不同，手腕对位（位移 ~9-18 单位+旋转）会把整条手臂甩进视锥。Prop1→glock_parent 也不可行：Prop1 是掌心道具骨，不在枪中线上。

**最终方案——旋转 + 顶点云取景对齐**（保持 CF rig 内部一致性，手-枪-臂整体只平移+微旋）：

```
VIEW* = T(re-place) · T(push_cloud) · T(grip) · R_fix · T(-grip)
```

| 成分 | 求法 |
|---|---|
| grip（旋转枢轴） | `idle_0` f0 下 Nini 右手蒙皮表面与 Mauser 枪身表面最近 10% 点对的中点质心；使用构建器实际的 re-pose + Source LBS 数学，不使用腕骨原点 |
| R_fix | 枪身 PCA1→stock `(flash−glock_parent)`；CF 骨架 +Y→stock +Z（毛瑟实测仅 1.7°） |
| push_cloud | `near_centroid(stock_gun_verts_idle) − near_centroid(our_gun_verts)`，近端区=各自 y 范围靠镜头 40% 一段的质心，三轴全对齐 |
| re-place（横向） | 枪身质心**横向**重定位到 **CF 参考图里枪身质心的屏幕 x**，经校准投影反算：f=288/tan(30°)（用户 viewmodel_fov=60）、屏幕右=-x。毛瑟 spec x=660 → centroid x=-4.8。**v6 教训**：把 Scene Root 偏轴角（26°）当眼位角搬到 CS 会甩出屏外——Scene Root ≠ 眼位；枪管本身在两引擎都与视轴平行，侧影只能来自离轴放置，不能靠偏航 |
| re-place（垂直） | **真实蒙皮表面接触区 z 对齐**：Source 侧把标准 fullfinger 手套按 Glock idle 骨架蒙皮，CF 侧把 Nini 手按构建器的 re-pose + Source LBS 蒙皮；分别求右手表面到枪身表面最近 10% 点对的中点质心，再对齐 z。毛瑟本轮 Source 目标 `-4.216`，拟合后 `-4.216`。**失败教训**：不能把“离 R_Hand 骨原点最近的枪顶点”称为接触点；stock/CF 腕骨原点约定不同，该错误锚把模型从过低一次抬高 3.36，游戏内明显过高。也不能用枪质心/顶点云 z：驳壳枪与 Glock 质量分布不同 |

**引擎投影标定（2026-09-19 验证）**：CS:GO viewmodel 投影 = 眼位空间 pinhole，f=288/tan(viewmodel_fov/2)，offset=(off_x·right, off_y·fwd, off_z·up)（用户值 fov60→f498.8、off(1,1,-1)→眼位(-1,-1,-1)），-x=右/-y=前/+z=上。验证法：把任一已部署版本的蒙皮顶点按此投影叠加到游戏截图——v6 顶点云与游戏渲染**逐像素吻合**，引擎无隐藏变换。**截图只作验证，不作拟合依据**（像素量取噪声大）。 |

**v4→v5 教训**：单地标（glock_parent/R_Hand/uid）语义不等价，会把枪留在视线正中——端视下手枪呈"竖直柱"，被误读为"枪管上翘"。**顶点云对齐**让枪落到 stock 偏轴位置，透视自然露出侧影。验证法：把 stock 顶点也做 bind→idle 蒙皮后同投影渲染——stock 自己也是一坨竖直柱，说明"柱"是端视正常形态而非朝向错误。

毛瑟实测（v8）：push=(4.07,-6.0,+0.73)+质心重定位；枪身落 (-5.7,-25.6,-9.5)~(-4.1,-12.4,-3.0)，质心投到 ~(685,510)px ≈ CF 图枪身质心 (660,430)，横向偏轴 ~14.5°（stock 9.5° ↔ CF SceneRoot 26°之间）。已知残余差异：CF 双手持枪姿态使双臂呈扇形摊开（stock 手收成窄条贴枪）；bull 星座件（Box04-08）idle 时停在眼后 y+20/z-22（动画内容，select/reload 才入画）。

builder：`VIEW = PUSH·ROLL·view_matrix`（`view_push_*`/`view_roll_deg` 仍可叠加微调）；`ARM_WEAPON` 已置空——Prop1 隶属枪链（parent=骨架根），不吃手臂 mod。

刚性件→节点归属（LTB 不直给，bind 局部空间最近邻匈牙利分配）：`PV-Mauser_Libra→Dummy01`、`reload→Box03`、`reload02→Box02`、`coin→Box010`、`Line→Box011`、`Bull-C→Box04`（Prop1 链，跟手）、`bull-set→Box08`、`bull01→Box07`、`bull002→Box06`、`bull003→Box05`（Box09 链，Scene Root 下）。bull 系 idle 时停在远端隐藏位，select/reload 时绕场飞动——天秤座星座件，属动画内容。

**2026-09-19 声音通路更正**：`SND/**/*.WAV` 的“加密容器”实为 LZMA-alone 压缩 RIFF（首字节 0x5D，`lzma.decompress FORMAT_ALONE` 直接出 WAV）；本武器 PCM 全走 SND，Weapon.bank 无 Mauser 流。此结论仅限老枪族，新武器仍以 FSB 为准。

首轮不做：`pv_gun_mauser_libra` idle 特效、QV 第三人称、观察动作（lookat01 暂用 idle_0）。

## M.4 材质光照迭代与当前状态（2026-09-19 快照）

位置/动画已通过顶点云+接触区拟合收敛（见 P3c）。剩余未过验收的是**材质光照**。迭代记录：

| 版本 | 方案 | 游戏内结果 |
|---|---|---|
| m1 | 套天袭固定 Phong 48/8，无 envmap | 暗部发黑、无金属层次 |
| m2 | `_S`+Alpha.B 驱动 Phong + 原 LobbyCube 直绑 `$envmap` | 白噪点、反射纹路错误（transformed cube 采样射线不等价） |
| m3 | 禁用运行时 envmap；spec+env 能量合并低通进 Phong | 噪点消失但整体过暗、无光泽 |
| m4 | CFG 能量校准：`$phongtint`/中性 Fresnel/boost 归一 | 仍暗；且 `_S` 高频纹路在阳光下显成错误反射纹 |
| m5 | 稳定层 `$selfillum` + `$selfillummask`（均值 0.6） | **画面零变化**——带 bumpmap/phong 的 VertexLitGeneric 下该组合不生效 |
| m6 | 改用中性 `$lightwarptexture`（暗端 0.6/亮端 1.0）+ `_S` 只作 tint | **画面零变化**——lightwarp 只压 diffuse，碰不到 Phong 项 |
| m7（当前已部署） | 三层模型：lightwarp(diffuse) + 减半 Phong(spec) + `$emissiveblend` 加法层承载 `cubemap色×EnvCubeMapBrightness×Alpha.B` | **颜色不对**（用户截图验证失败，加法层偏色/过量） |

当前部署参数（全自动推导，无手调）：`phongexponent 2`、`phongboost 0.939`、`phongtint [1 .766 .531]`、Fresnel `[1 1 1]`、lightwarp floor 0.6、`emissiveblendstrength 0.6`、env_overlay 均值 ~0.23。A/B SHA-256 `28/28`；pak 需用户 REBUILD 后做 B/C。

**未决问题**：CF `Alpha+Snell+TransformedCube` 的稳定环境反射在 Source 里仍无验证通过的载体——`$envmap` 射线不等价、`$selfillum` 不生效、`$emissiveblend` 偏色。下一步候选：查 CS:GO VertexLitGeneric 实际支持的未试参数、把 env 能量烘进 base 纹理并进一步压低 Phong、或接受双材质分件渲染。**`SOURCE_PROXY_GAIN=0.75`/`SOURCE_ENV_PROXY_GAIN=1.5` 是两个全局共享常量，调校时先动它们，勿写武器专属值。**

---

# 屠龙-春桃 → CS:GO 默认刀

> **2026-09-18 贴图复核更正（离线通过，未部署）**：无后缀 `PV-Kukri_Beast.LTB` 的 `objObject03000` 网格/UV 与当前 diffuse 不匹配。基版 `PV-Kukri_Beast_GR.LTB` 的 `Object066` + 同一原图已在 Blender 恢复连续龙纹、金色刀尖和正确握柄。下文历史记录中“UV 已正确”“分段悬浮是真实几何”撤销：白色几何渲染显示横带来自错贴黑底。取景/手臂参数仍冻结；更换网格需先做 `B_old_Box01 @ inverse(B_GR_Box01)` bind 重绑。证据、复现脚本和剩余材质问题见 `work/tulong_chuntao/TEXTURE_STATUS.md` 顶部；生产 addon 未变。

## T.0 身份确认（已查证 2026-09-17）

Bute `rez/Butes/BF005.LTC` Weapon 记录 #6041（MD5 校验解码）：

```text
WeaponName    = 魂·屠龙-春桃
StandardName  = Kukri_Beast_spring
PViewModel    = Models\PLAYERVIEW\PV-Kukri_Beast          <- 网格/动画（与 Spring LTB 字节相同）
PViewSkin     = ModelTextures\PLAYERVIEW\PV-Kukri_Beast_spring.dtx
QV            = Models\WEAPONS\QV-Kukri_Beast.ltb
```

同族：`Kukri_Beast` = **屠龙**（记录 #1003，现装第三方 addon `p_Kukri_Beast` 用的就是这个）。春桃是花卉系列皮肤，不是另一把刀。

排除：`DragonBlade`/`斩神刀`/`斩魔刀`（另一族近战）；`Kukri_Beast_Silver`/`_AD`/`_BO` 等其它屠龙皮肤。

证据：`work/tulong_chuntao/scan/bute_tulong.json`、`scan/kukri_spring_hits.json`、`acquire/acquisition.json`。

`PV-Kukri_Beast.LTB` 与 `PV-Kukri_Beast_Spring.LTB` SHA-256 相同（76201B），春桃差异只在贴图/CFG。

## T.1 CF 资产图（全部走 MD5 分片校验读 `read_verified_payload`）

| 角色 | REZ 内路径 | 所在包 | 备注 |
|---|---|---|---|
| PV LTB（刀+手臂骨架+动画） | `Models/PLAYERVIEW/PV-Kukri_Beast.LTB` | `rez4/RF016.REZ` | 76201B；与 `_Spring.LTB` 同哈希 |
| PV 贴图（春桃 diffuse） | `ModelTextures/PLAYERVIEW/PV-Kukri_Beast_spring.DTX` | `rez4/RF017.REZ` | 524452B |
| 材质 CFG | `ModelTextures/Shader/WeaponShader/Kukri_Beast_Spring.CFG` | `rez4/RF017.REZ` | 2915B |
| Specular | `ModelTextures/SpecularMap/Kukri_Beast_Spring_S.PNG` | `rez4/RF017.REZ` | 直接 PNG |
| Normal | `ModelTextures/NormalMap/Kukri_Beast_Spring_N.PNG` | `rez4/RF017.REZ` | 直接 PNG |
| Alpha | `ModelTextures/AlphaMap/Kukri_Beast_Spring_A.PNG` | `rez4/RF017.REZ` | 直接 PNG |
| QV（第三人称，可选） | `QV-Kukri_Beast.ltb` + `QV-Kukri_Beast_Spring.DTX` | `rez4/RF016` / `rez4/RF017` | 首轮只做第一人称 |
| 手膜（默认） | `Arm_Nini_GR.LTB` + `FVIEW_{HAND,ARM}_Nini_GR` | 复用天袭 `decode/nini_gr/` | **妮妮-保卫者**；见 A.9 |

Bute 声音名（#6041，与原版屠龙相同）：Attack=`Kukri_Attack`，Hit=`KukriBeast_Hit`，Select=`Kukri_Select`，地表=`Kukri_{Metal,Stone,Wood}`。PCM 走 FMOD `Weapon.bank`，`SND/**/*.WAV` 不用。

基版屠龙有 `PVEffectName=pv_knife_Kukri_trail`；春桃记录未写独立 idle 特效。首轮不做刀光拖尾。

## T.2 CS 侧目标

| 项 | 值 |
|---|---|
| 槽位 | 默认 CT 刀 + 默认 T 刀（两边同一把 CF 屠龙-春桃） |
| 模型 | `models/weapons/v_knife_default_ct.*` 与 `v_knife_default_t.*` |
| 参考 | stock `v_knife_default_{ct,t}` QC/序列名/挂点 + `Weapon_Knife.*` 声音路径 |
| 声音路径 | `sound/weapons/knife/*.wav`（以 stock manifest 为准） |
| 部署 | 新 addon `p_cf_tulong_chuntao_p1`；**不改** `p_Kukri_Beast`。REBUILD 前用户在 MIGI 关掉 `p_Kukri_Beast`，否则两边抢同一 mdl 路径 |

## T.3 阶段流程（evidence 进 `work/tulong_chuntao/`）

沿用 §3 / 附录 A。硬规则不变：REZ 分片、UV `v→1-v` 一次、绕**本武器**中心镜像、CS `Bip01*` 钉 `(0,+500,0)`、只超 diffuse、默认妮妮手膜 A.9 / 油光 A.8.2、刀身金属 Phong A.8.1（无 envmap）、MIGI A→B→用户 REBUILD→C。

**H**：屠龙和天袭都是 CF PLAYERVIEW（FvARM + 武器同一套骨架），手膜跟着武器走。H 直接复用天袭已拟合的 CF→第一人称相似变换，**不要**拿 CS 默认小刀做 ICP（形状不是一类），也**不要**抄第三方 `p_Kukri_Beast` 的 ValveBiped 定位。MX 仍按本刀 H 后 bbox 的 x 中心镜像。MX 后已反转三角绕序并据此重算法线，**不得再二次翻转刀身法线**。

**2026-09-17 第三轮修正（贴图+取景，对照 CF 实机 GIF/检视图）**：刀身 UV 上一轮判反了——离线渲染证明游戏实际采样行 = `(1-v_smd)`（VTFCmd 链路等效一次翻转），所以刀身也必须 `v_smd=1-v_raw`（`flip_knife_v=true`，与手膜同约定；之前"dump 已是 Source 方向"的结论是错的）。取景：CF 实机里刀贴**最右缘**、刀面**正对镜头**、刀尖朝上近竖直；当前姿态差一个绕刀身长轴的 roll。新增后校正 `VIEW = PUSH2 @ T(pivot)·R(tilt·axis, axis_roll)·Ry(tilt)·T(-pivot) @ PUSH @ ROLL`：`view_tilt_deg=-35`（屏幕面内）、`view_axis_roll_deg=66.5`（刀轴）、`view_axis=[0.392,0.424,0.817]`、`view_pivot=[-5.53,-32.68,-3.78]`（握点，旧 view 空间）、`view_push2=[-6.52,+10.51,-4.58]`（更右更近更低）。刀身分段悬浮板块是 Beast 真实几何，间隙正常。刀身 VMT 仍停 `$bumpmap`、保留 `$halflambert`。

| 阶段 | 脚本 | 状态 |
|---|---|---|
| 身份 | `scan/scan_bute.py` `scan/scan_kukri_spring.py` | PASS |
| P0 | `acquire/acquire_assets.py` | PASS（9/9，Spring LTB=base LTB） |
| P1 | `decode/decode_assets.py` | PASS：48 骨 / 3 mesh（刀 `objObject03000` 1128v 刚性绑 Box01）；clips=`select/idle_0/run/bigshot/combo_1/combo_2`；diffuse 1024 DXT1 |
| P2 | 默认 SKIP | — |
| P3 | `csref/extract_knife_ref.py` `csref/fit_transform.py` `_diag_fit2.py` | PASS：H = 天袭（s=2.0025）；MX 绕本刀 bbox x；内层 `view_push_y≈-22.08`/`view_push_z=-3.5`；外层后校正 `tilt=-35`+`axisroll=66.5`+`push2=[-6.52,10.51,-4.58]`（对 CF 实机帧拟合：刀右缘、面朝镜头、尖向上）。序列名仍来自 stock `v_{ct,t}_knife_anim` |
| P4 | `texture/build_textures.py` | PASS：ComfyUI 4x→2048 BGRA8888；刀身 VMT Phong 48/8 + Half-Lambert，无 envmap、停用不兼容的 CF normal map |
| P5 | `native_vm/build_tulong_vm.py` | PASS：97 骨；Nini GR LBS；13 个 stock 刀序列名映射 CF clip；CT/T 各编译一份；刀身与手膜统一 `v_smd=1-v_raw`；无二次法线反转 |
| P6 | `sound/build_sound_overlay.py` | PASS：Weapon.bank 无 dry `Kukri_Attack`/`KukriBeast_Hit`，用 `KUKRI_ATTACK_{1,2,3}_R` + `KUKRI_SELECT_R` overlay `knife_slash/hit/stab/deploy` |
| P7 | A→B hash；用户 MIGI REBUILD；B→C | A/B **31/31** SHA-256 一致（R4 基线：原版屠龙贴图 + 纯 MX@H 天袭变换，VIEW 全归零）。旧 addon `p_Kukri_Beast` 已移到 `migi/csgo/_parked_addons/`。**等用户 MIGI REBUILD** |
| P8 | 用户游戏内验收 | GATE |

**2026-09-17 第四轮（用户回退到基线）**：第三轮自定义 VIEW 校正被用户否决（"位置和贴图还是不对"）。按用户要求回退：**贴图改原版屠龙** `PV-Kukri_Beast.DTX`（512 DXT1→ComfyUI 4x→2048 VTF，材质 `cf_kukri_beast`，VMT 同 Phong 48/8+Half-Lambert 配方；新脚本 `texture/build_textures_beast.py`；基版配套 S/N/Alpha 已由 `acquire/acquire_beast_base.py` 提取）；**取景全部归零**（`view_push*`=0、`view_roll/tilt/axis_roll`=0），`VIEW=I`，变换退化为与天袭逐字相同的 `MXH=MX@H`、`rest/anim_world=MX@(H@x@Hinv)@MX`。几何/UV 不变（base=spring 同 LTB），`flip_knife_v=true` 保留。build 脚本中刀身材质抽常量 `KNIFE_MAT="cf_kukri_beast"`（换皮肤只需改这一个值）。离线渲染确认：刀在右缘、暗红刀身+金爪贴图正确。本轮不做任何微调，等用户游戏内实测后再动。 |

**2026-09-17 第五轮（用户逐指令验收通过——最终取景，已冻结）**：位置经用户逐步指令调定，用户确认"已经可以了"。最终 `viewmodel_transform.json` 参数（**勿再动**）：

- 整体平移 `view_push=(-4.0, -11.0, -6.5)`（view 空间：-Y 推远 / -X 屏幕右 / +Z 上）
- 整体旋转 `VIEW` 外层 = `T(view_pivot)·R(view_axis, axisroll)·T(-view_pivot)`：`view_axis_roll_deg=20.06`、`view_axis=[-0.6687,0.3512,-0.6554]`、`view_pivot=[-4.51,-16.14,-8.36]`（= **idle 姿态两肩点 `FvARM-bone L/R UpperArm` 连线中点**，post-push pre-axis 空间，用户指定该中心）
- `view_roll/tilt/push2 = 0`
- **左右手独立修饰**（动画帧骨骼世界左乘刚体矩阵 `M = T(off)·T(arm_pivot)·R(arm_rot)·T(-arm_pivot)`，ref/bind 帧不动→顶点经蒙皮跟随）：`arm_offset_l=[6,4,-4]`、`arm_offset_r=[-1,0,-1]`、`arm_pivot` 同肩点中点、`arm_rot_l = 绕[0,-1,0] 转 20°`（=用户系前向 x 轴顺时针20°）、`arm_rot_r=0`。`FvARM-bone L/R Clavicle` 锚定不动；刀骨 `FvARM-bone Prop1`+`Box01` 归入右臂组跟随
- 用户坐标系约定（口头指令）：**x=视角前方、y=右、z=上**；换算到 view 空间即 `x_user=-Y_view、y_user=-X_view、z_user=+Z_view`（右手系，T 为反射共轭 `R_view=T@R_user@T`，`T=[[0,-1,0],[-1,0,0],[0,0,1]]`）
- "一拳"≈2 view 单位

剩余问题：贴图仍不对（刀身游戏内偏暗红，CF 原版为亮金+红龙），下一步排查。

首轮不做：刀光 `pv_knife_Kukri_trail`、第三人称 QV、观察动作（CF 无 observe，lookat01 暂用 idle）。

手膜不重新提取：指向已冻结的 `work/galil_ace_tianxi/decode/nini_gr/`。

---

# Galil ACE-天袭 → CS:GO Galil AR

> 用户 2026-09-14 任务：把 CS 里的 Galil（`v_rif_galilar`，Galil AR 槽位）替换为 CF 的 **加利尔ACE-天袭**。已冻结。

## 0. 身份确认（已查证 2026-09-14）

Bute `rez/Butes/BF005.LTC` Weapon 记录 #6941/#6942（MD5 校验解码）：

```text
WeaponName    = 加利尔ACE-天袭
StandardName  = GalilACE_PhantomBeast          <- VVIP 形态
第二行同名    = 变换(Chg)形态 PV-GalilACE_PhantomBeast_Chg（后续增强，首轮不做）
```

同族排除：`GalilACE`（普通版）、`GalilACE_Prototype`（原型）、`_GJZX`/`_WC25`（PhantomBeast 的其它皮肤，同名 CFG/贴图族，不是天袭本体）。

证据：`work/galil_ace_tianxi/scan/galil_index_hits.json`（464 索引 / 255257 条目）、`work/galil_ace_tianxi/scan/bute_galilace.json`。

## 1. CF 资产图（全部走 MD5 分片校验读 `read_verified_payload`）

| 角色 | REZ 内路径 | 所在包 | 备注 |
|---|---|---|---|
| PV LTB（枪+手臂骨架+动画） | `Models/PLAYERVIEW/PV-GalilACE_PhantomBeast.LTB` | `rez4/RF016.REZ` | 518960B，LZMA 压缩 |
| PV 贴图（diffuse atlas） | `ModelTextures/PLAYERVIEW/PV-GalilACE_PhantomBeast.DTX` | `rez6/RF017.REZ` | 524452B |
| 材质 CFG | `ModelTextures/Shader/WeaponShader/GalilACE_PhantomBeast.CFG` | `rez6/RF017.REZ` | 4084B 明文 |
| Specular（环境反射色图） | `ModelTextures/SpecularMap/GalilACE_PhantomBeast_S.PNG` | `rez6/RF017.REZ` | 直接 PNG |
| Normal | `ModelTextures/NormalMap/GalilACE_PhantomBeast_N.PNG` | `rez6/RF017.REZ` | 直接 PNG |
| Alpha | `ModelTextures/AlphaMap/GalilACE_PhantomBeast_A.PNG` | `rez6/RF017.REZ` | 直接 PNG |
| 声音 WAV ×12 | `SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB[Chg]_*.WAV` | `rez4/RF018.REZ` | **是加密容器**（非 RIFF）；实际 PCM 走 `rez/FMODStudio/Weapon/Weapon.bank` 的 `GalilACEPhantomB_*` FSB 流（vgmstream 解码） |
| QV（第三人称，可选） | `Models/WEAPONS/QV-GalilACE_PhantomBeast.ltb` + `.dtx` | `rez4/RF016` / `rez6/RF017` | 首轮只做第一人称 |
| 手膜（默认） | `Arm_Nini_GR.LTB` + `FVIEW_{HAND,ARM}_Nini_GR` | `rez4/RF016` + `rez6/RF017` | **妮妮-保卫者**；LBS 重摆进枪 bind。见 A.9 |

Bute 声音名映射（记录 #6941）：Shoot=`GalilACEPhantomB_Shoot`，ClipOut=`GalilACEPhantomB_ClipOut`，ClipIn=`GalilACEPhantomB_ClipIn`，Select/换弹=`GalilACEPhantomB_Select`，变形=`GalilACEPhantomB_Chg`，观察=`GalilACEPhantomB_Obv`，近战=`GalilACEPhantomB_ATT`。

**与雷神的差异**：PhantomBeast PV LTB 是 VVIP 模型（~519KB vs 雷神 153KB），节点/件数/`PIECE_NODE` 映射都要重新算；有 `PVEffectName=pv_galilace_phantombeast_idle`。idle 组已按附录 B 做了有限移植并冻结，不是 1:1 转换器；`_Chg` 变换形态仍不做。

## 2. CS 侧目标

| 项 | 值 |
|---|---|
| 槽位 | Galil AR（T 步枪） |
| 模型 | `models/weapons/v_rif_galilar.{mdl,vvd,vtx,ani}` |
| 参考 | 从 `csgo/pak01_dir.vpk` 抽 stock v_rif_galilar + QC/序列名/挂点 + `game_sounds_weapons` 的 `Weapon_GalilAR.*` 文件名 |
| 声音路径 | `sound/weapons/galilar/*.wav`（以 stock manifest 为准） |
| 部署 | 新 addon `p_cf_tianxi_galilar_p1`，只放第一人称资产；`w_rif_galilar*` 不动 |

## 3. 阶段流程（每步产 evidence，进 `work/galil_ace_tianxi/`）

```text
P0 资产恢复  verified_root 镜像 + SHA/provenance 记录      -> acquire/
P1 解码      skin dump(顶点/UV/权重) + 动画 payload(100fps) + DTX->PNG -> decode/
P2 身份      [默认 SKIP] Bute+资源路径+贴图证据确认；Blender 预览仅拟合存疑时跑轻量模式
P3 CS 参考   stock galilar 反编译 -> H = sR+t ICP 拟合      -> csref/
P4 贴图      diffuse 4x 超分(ComfyUI 127.0.0.1:8188) -> VTF/VMT -> materials/
P5 模型      改编 s05 脚本 -> SMD/QC -> studiomdl           -> source1/
P6 声音      CF WAV -> 44.1k PCM16 -> galilar 文件名 overlay -> sound/
P7 部署      agent: addon 落盘到 migi addons -> 用户: MIGI REBUILD -> agent: pak hash 复核 -> deploy/
P8 验收      用户游戏内确认第一人称/声音/动作                [GATE: USER_RUNTIME_ACCEPTED]
```

硬规则（继承 CF_NATIVE_PIPELINE）：

- **REZ 分片**：一律 `read_verified_payload(index, entry)`，无 MD5 不算已验证；`data/` 老解包不用作输入。
- **UV**：dump JSON 是原始 UV，进 Source/Blender 写 `v → 1-v`，只做一次。
- **镜像**：CF 原始左右反；Source 1 侧在 H 之后绕**枪身中心**镜像（不是原点），顶点/rest/动画/挂点同步，三角绕序反转。
- **CS 手臂隐藏**：47 根 `Bip01*` 骨全帧钉 `(0,+500,0)`（相机后方），不做 identity 塌陷。
- **H 变换**：ICP 拟合 `CF idle-posed 枪顶点 → stock galilar idle-posed 顶点`，`v'=Hv`、`R'=H·B·H⁻¹`、`W'=H·W·H⁻¹`。
- **超分**：只超 diffuse；normal/spec 不超。
- **默认手膜**：妮妮-保卫者（`Arm_Nini_GR` + `FVIEW_{HAND,ARM}_Nini_GR`），diffuse 4x→2048，VMT 走 A.8.2。新武器默认用这套；用户点名角色/阵营才换。不要默认回 FoxHowl 或 Roxana。
- **事件时序**：按 CF clip `times_ms` 投到 100fps 帧号；同 channel 后续事件会截断前音（BoltBack/BoltForward 坑）。
- **MIGI REBUILD/REBUILD 由用户手动执行**：agent 只负责把 addon 落盘到 `migi/csgo/addons/` 并提醒用户点 REBUILD，不替用户操作 MIGI；以 pak 内 hash == MIGI addon hash 为最终验证，不看 UI 日期或仓库 staging 文件。

## 3.1 MIGI 三层产物链（强制检查，避免“REBUILD 后没变化”）

MIGI 部署存在三个彼此独立的层级：

```text
A. 仓库 staging
   work/<weapon>/addon/**
          ↓ agent 必须显式复制，并先做 hash 对比
B. 实际 MIGI addon
   <game>/migi/csgo/addons/<addon>/**
          ↓ 用户手动点击 MIGI REBUILD
C. 游戏实际读取的 pak
   <game>/migi/csgo/pak01_dir.vpk + pak01_*.vpk
```

**重复出现“调了多版但游戏完全没变化”的根因**：材质脚本只更新了 A，未同步到 B。用户点击 REBUILD 时，MIGI 正确地从 B 重新打包，但 B 仍是旧版，所以 C 也仍是旧版。仓库产物变新、提交变更、甚至 REBUILD 成功，都不能证明游戏读取到了新文件。

强制执行顺序：

1. 构建脚本先输出 A。
2. agent 将本轮全部变更文件显式复制到 B；不能写 `migi/csgo/materials/` 松散目录代替 B（用户已验证松散文件不覆盖 pak）。
3. **在要求用户 REBUILD 之前**，agent 必须比较 A 与 B 的关键文件 SHA-256；文件清单、大小和 hash 全部一致才可通知用户。新增文件（如 `_S.vtf`、`_M.vtf`、cubemap）也必须在 B 存在。
4. agent 停止，通知用户打开 MIGI 点击 **REBUILD**；不得替用户执行。
5. 用户完成 REBUILD 后，agent 再比较 C 内条目与 B 的 SHA-256；一致才可进入游戏视觉验收。若不能立即读取 C，状态保持 `PACK_VERIFY_PENDING`，不得声称新版本已生效。
6. 若游戏画面“完全没变化”，**先查 A/B/C 哈希，不要继续调 shader 参数**。只有三层一致后仍无变化，才排查 VMT 参数、材质搜索路径或模型 material name。

检查时不要依赖 MIGI 列表里的日期、addon 显示名或 REBUILD 成功提示；这些都不等价于文件内容一致。贴图脚本必须同时定义仓库 staging 路径和实际 MIGI addon 路径，例如本轮：

```text
A = work/galil_ace_tianxi/addon/materials/.../cf_tianxi/
B = <game>/migi/csgo/addons/p_cf_tianxi_galilar_p1/materials/.../cf_tianxi/
```

本轮事故证据：实际 B 一直保留 v1（VMT 276B、diffuse 1.3MB DXT1），而 A 已是 v5（VMT 833B、diffuse 22MB BGRA8888，并新增 `_S`/`_M`/`cf_gold_cube.vtf`）。修复后 A/B 三个关键文件 SHA-256 已一致；修复提交 `b884090`。

## 4. 当前状态（2026-09-16 冻结；手膜 2026-09-17 改为默认妮妮-保卫者）

```text
P0: PASS   13/13 资产 MD5 分片校验恢复 -> acquire/verified_root/ (acquisition.json)
P1: PASS   LTB 56 节点 / 12 mesh / 10 clip 解出 -> decode/ (reference_payload.json 100fps, cf_skin_galilace.json, DTX->PNG)
P2: SKIP   Blender 预览脚本写好但渲染负载大导致 MCP 阻塞；用户已关 Blender。身份已由 Bute+资源路径+贴图确认。
P3: PASS   stock v_rif_galilar 反编译；H 变换 ICP 拟合 s=2.0025 det=+1 sym_trimmed_mean=0.353
           (csref/viewmodel_transform.json；锚点初始化改 PCA 主轴——3 点共线锚点会坍缩)
P4: FROZEN v7 架构 + 2026-09-16 金属参考值：ComfyUI 4x 后降采样到 2048 -> BGRA8888 无损 diffuse；
           _M 只取稀疏 G/B 发光信息；禁用 envmap/rimlight；
           金属 = albedo-tinted Phong，**exponent=48 / boost=8 / fresnel=[0.05 0.45 1]**
           （v7 原 boost=2，用户连续两次「提高一倍」后冻结为 8，见 A.8.1；
           2026-09-17 枪身试用 A.8.2 油光后按用户要求退回）；
           高光继承枪身 diffuse 本色并随 viewmodel 光照变化；VTF 加 TRILINEAR+ANISOTROPIC(+NORMAL)
           (texture/build_textures_v2.py)
P5: PASS   work/galil_ace_tianxi/native_vm/build_galilace_vm.py
           123 骨（1 root + 47 CS 塌陷 + 55 CF + 4 attach + galilar_parent + 15 fx）
           8 序列：idle/fire1-3/reload/draw/lookat01(=observe 704f)/prepare/loop
           事件用 LTB 权威 keyframe label：ClipOut@33 ClipIn@117 (100fps)
           手膜默认 **Nini GR / 妮妮-保卫者**（`decode/nini_gr/`，LBS 重摆，4x 2048，A.8.2）
           studiomdl 一次通过，6 文件齐全
P6: PASS   Weapon.bank FSB 流 -> 44.1k PCM16 -> 8 个 galilar wave 路径
           (fire×4=dry Shoot_1, distant=Shoot_1_R, clipout, clipin, draw=Select)
           boltback/boltforward 保留 stock；WeaponMove*=stock 共享 foley 不动
P7: PASS   pak01_dir.vpk 重建（vpk.exe -M），addons.json 加入 p_cf_tianxi_galilar_p1，
           23 文件全部入 pak 并复核；旧 pak 备份在 deploy/pak01_backup/
           注：本轮 pak 由 agent headless 重建（vpk -M）完成，仅作一次性验证；
           正式流程定为用户手动 MIGI REBUILD，agent 不做此步。
P8: PASS   用户游戏内确认：模型/动画/声音正常（2026-09-14）
           手膜：FoxHowl → Roxana GR（已冻存）→ **Nini GR 为默认**（2026-09-17 写入；MIGI REBUILD 后验收）
```

### 4.1 M4A1-雷神同步整改（2026-09-15）

```text
材质: STAGED  原 diffuse=1024 DXT1/699KB（未超分，RGB mean=12.9/16.4/16.6）；
                 `scripts/p5/build_leishen_texture_v2.py` 已执行 ComfyUI RealESRGAN 4x，
                 降采样到 2048，gamma=0.72/brightness=1.08/color=1.08/contrast=1.03，
                 输出 2048 BGRA8888/22MB + TRILINEAR/ANISOTROPIC，A/B hash PASS；
                 VMT 使用本色 Phong（无 envmap/envmapmask）；数值未跟天袭 2026-09-16 冻结值同步。
合并: STAGED  p_cf_leishen_m4a4_p7_sound 的 9 个 WAV 已并入
                 p_cf_leishen_m4a4_p6（现共 39 文件，无路径冲突，9/9 hash PASS）。
退役: PASS    活动 addons 中已移除 p_cf_leishen_m4a4_p7_sound；同内容 parked 备份保留。
脚本: PASS    scripts/p5/p5_p7_original_sound.py 后续直接 merge 到 P6，不再创建第二 addon；
                 scripts/p5/merge_leishen_addons.py 负责旧双-addon 的一次性安全合并。
打包: PACK_VERIFY_PENDING  等用户 MIGI REBUILD；agent 不执行。
```

合并证据：`work/p5_leishen/unified_addon.json`。canonical addon 固定为 `p_cf_leishen_m4a4_p6`。

### 4.2 天袭光效与金属（2026-09-16 冻结；2026-09-17 手臂油光）

```text
金属:   FROZEN  A.8.1 参考值（boost=8 / exponent=48）。不要加回 envmap。
        2026-09-17 枪身试用 A.8.2 后已退回。
手臂:   FROZEN  默认手膜 = 妮妮-保卫者（Nini GR），见 A.9。
        油光 A.8.2（boost=1.2 / exponent=5 / fresnel=[0.15 0.55 1]），无 envmap。
光效:   FROZEN  idle 组做到当前层即止，见附录 B。
        已装车：L/R 流光各 front+COPY+back、parts 蓝/红、三角 L/R、simbol/glow、glitch；
                龙眼 PCF 已按用户要求改回「枪上光晕 + 地面会投一份」的版本（`cf_tianxi_eye` @ fx16，无 view model effect）。
                2026-09-17 fx16 骨原点 `EYE_CAL=(0,0,-0.25)` 下移（先试 -2.5 过多，改为十分之一）。体积光球关闭。
        否决：手工交叉龙眼面片（ENABLE_EYE_GEOMETRY=False）。
        未做：其余 7 个 ParticleSystem、动作组、变换形态。
A/B:    56/56 SHA-256（staging addon ↔ MIGI addon p_cf_tianxi_galilar_p1）。
C/游戏: PACK_VERIFY_PENDING，用户 MIGI REBUILD 后才核 pak。
```

## 5. 复现索引（照此可重走全流程）

前置依赖（`scripts/_paths.py` 提供）：CF 客户端目录、CS:GO 目录、
`vgmstream-cli`、`ffmpeg`、Crowbar（stock 反编译）、Source SDK `studiomdl.exe`、`vpk.exe`。

| 阶段 | 脚本 | 输入 → 输出 |
|---|---|---|
| 身份扫描 | `scan/scan_galil_index.py` `scan/find_bute_records.py` `scan/scan_fview_index.py` | REZ 索引 + Bute → `scan/*.json` |
| P0 | `acquire/acquire_assets.py` | REZ 条目 → `acquire/verified_root/` + `acquisition.json` |
| P0 手膜 | `acquire/acquire_nini_gr.py` | 默认妮妮-保卫者 → `verified_root/` + `nini_gr_acquisition.json` |
| P1 | `decode/decode_assets.py` | verified_root LTB/DTX → `decode/`（payload/skin/audit/PNG） |
| P1 手膜 | `decode/nini_gr/prepare_nini_gr.py` | Nini LTB dump + DTX→PNG + RealESRGAN 4x → `decode/nini_gr/` |
| P2 | 默认跳过；存疑时 `preview/bpy_build_preview.py` | decode → Blender 预览（只建 mesh+单帧姿态，不烘焙不渲染） |
| P3 | `csref/extract_galilar_ref.py` `csref/fit_transform.py` | pak01 stock mdl → `csref/decompiled_stock/` + `viewmodel_transform.json` |
| P4 | `texture/build_textures_v2.py` | ComfyUI 超分 diffuse + 稀疏 `_M` 发光 mask + albedo-tinted Phong VMT → staging，并同步实际 MIGI addon |
| P5 | `native_vm/build_galilace_vm.py` | decode+csref+armtex → `native_vm/source1/` → studiomdl → `addon/` |
| P6 | `sound/build_sound_overlay.py` | `Weapon.bank` FSB（vgmstream+ffmpeg）→ `addon/sound/weapons/galilar/` |
| P7 | agent: A→B 同步并校验；**用户: MIGI REBUILD**；agent: B→C 校验 | staging addon → `migi/csgo/addons/` → 用户 REBUILD → pak hash 复核；详见 §3.1 |
| P8 | 用户游戏内验收 | — |

## 6. 已知回退 / 后续增强位

- `BoltBack/BoltForward` 帧 140/160 是按副件运动估的（CF 无 bolt label）——换弹尾段机械声不对位就调 `build_galilace_vm.py` 这两个帧号。
- `PV-GalilACE_PhantomBeast_Chg` 变换形态、QV 第三人称仍未做。idle 光效已按附录 B 冻结，不是完整 CF 还原。
- diffuse 经 4x 超分后以 2048 BGRA8888 无损 VTF 输出；免重启路线弃用（`mat_reloadallmaterials` 闪退 + 用户实测松散文件不覆盖 pak）。迭代 = 改 `build_textures_v2.py` 参数重跑落 staging 并同步实际 addon → A/B hash Gate → 用户 MIGI REBUILD → B/C hash Gate → 上游戏验收。
- **v5 黄绿噪点根因**：`GalilACE_PhantomBeast_M.PNG` 没有 alpha，R 通道全 255；直接作为 `$selfillummask` 等于整枪自发光。彩色高频 `_S` 同时驱动 phong exponent 与 envmap mask，再叠加只有一个 mip 的 Gold_map01 cubemap，进一步放大反射斑点。v6 只取 `_M` 的 `max(G,B)` 作为稀疏发光遮罩并移除高频驱动，噪点消失。
- **v6 阴影下仍泛白根因**：`$envmap` 是环境反射加色，不等于枪身本色金属，暗处仍会叠加 cubemap；rimlight 也会继续抬亮边缘。用户要求的是贴图本色的金属高光，因此 v7 完全移除 envmap/rimlight，仅保留 `$phongalbedotint 1` 的 Phong，高光颜色继承 diffuse。
- observe 的 6 个音效 cue 暂用 stock `WeaponMove*` 通用衣物音。

### 执行中发现的差异（已处理）

- **SND/*.WAV 是加密容器**（93B 头 + 无标准 magic）→ 声音实际取自 FMOD `Weapon.bank`，含 `_R` 混响尾变体（用作 distant 正好）。
- **LTB 内嵌权威事件 label**：reload 有 `WeaponClipOut@kf10`/`WeaponClipIn@kf35`（30fps 帧号 ×100/30 → 33/117）；select 有 `WeaponReload@kf1`。bolt 无事件 → BoltBack/Forward 暂按副件运动窗估 140/160，runtime 后微调。
- **观察动作**：`observe` clip 704f/7s，带 6 个音效 cue（observe1-5 label）→ 映射到 lookat01，暂用 stock WeaponMove 通用衣物音。
- **手部**：武器 LTB 内嵌 `Fview-hand2/arm2` 已弃用。默认外挂 `Arm_Nini_GR.LTB`，FvARM 骨名对齐后 LBS 重摆进枪 bind（见 A.9）。
- **附件**：flash/shelleject/stattrack/uid 挂在 Box001 下，idle f0 位置与镜像后 stock 完全一致（flash [-5.12,-36.43,-3.74]）。
- **MIGI REBUILD 可headless 复刻**：解 pak01_dir.vpk → 叠加 addon → 更 addons.json → `vpk.exe -M` 重打（`deploy/rebuild_pak.py`）。

详细执行记录追加在 `work/galil_ace_tianxi/` 各阶段目录的 report/json。

---

# 附录 A. CF 原生资产 → CS:GO Legacy 通用管线（原 CF_NATIVE_PIPELINE.md，2026-09-14 并入）

2026-09-13～14 走通的完整链路：CF LTB 解包 → 贴图恢复 → Source 1 SMD/QC → 第一人称 MIGI 替换。只记**可复用的结论和坑**；运行时成品与验证看 `work/p5_leishen/p7_s05/`。

## A.1 数据通路总览

```text
REZ 包(分片) --read_verified_payload--> 原始字节
  ├─ .LTB(LZMA) --LithTechModelDecoder--> 骨架节点+bind世界矩阵+local动画轨道+蒙皮网格
  │     └─ --dump-ltb-skin (CFRezManager) --> skin JSON(顶点/三角/UV/权重/骨索引)
  ├─ .DTX --decode_repo_pixels--> PNG   (DXT1 等)
  ├─ .TGA/.PNG --> 直接可用
  └─ .CFG --> 贴图清单+光照参数        (WeaponShader/AdvancedShader)
```

## A.2 REZ 分片坑（最大的一个）

- `data/rf017` 等**老解包目录里的 DTX 全是坏字节**（0/3258 有效），别再直接用。
- REZ 目录项的 `time` 字段实际是**分片号**：payload 在 `rfXXX_<n>.rez`。
- 正确读法：`scripts/material_recovery/rez_verified_payload.read_verified_payload(index, entry)` —— 自动选分片、MD5 校验。
- **新内容在 `rez2/`..`rez6/`**：Renewal 级资源在 `rez2/RF016.REZ`(模型) / `rez2/RF017.REZ`(贴图+CFG)，老 `rez/` 里没有。
- 贴图索引读法：`n05a_decoder_provenance_audit.read_rez_index_mmap(rez)`。

## A.3 LTB 结构事实

- LTB = LZMA-alone 压缩的 Jupiter 二进制模型（首字节 0x5D）。
- 骨架节点存的是 **bind 世界矩阵**（不是 local）。
- 动画轨道是 **local pos/quat**，沿父链组合成 world。
- **LTB 里没有贴图引用**。mesh 只有名字 + `advanced_shader` 命令行。贴图绑定 = 命名约定 + CFG 外挂。
- 刚性件→节点归属 LTB 不直给：用 **bind 世界最近节点** 判定。

## A.4 蒙皮/变换约定（全部数值验证过）

```text
v' = anim_world @ inv(bind_world) @ v        # 世界空间蒙皮
```

- idle 帧全节点 delta = 0° —— 约定正确的判据。
- **Blender 骨骼 rest ≠ CF bind**：Blender 强制骨骼 Y 轴沿骨轴 → 普通 armature modifier 会逐骨错旋。解法 = 校正变形骨架：`pose_world = anim_world @ inv(bind_world) @ rest_world`。
- 手臂模型 bind 与枪不同（手在体侧 vs 前伸）→ 手臂要自己的 DEFORM 骨架，同套 clip 数据双烘。

## A.5 UV 约定（踩过两次）

- dump JSON 给**原始解码 UV**；进 Source/Blender 写 `uv = (u, 1-v)`，**只做一次**（翻两次=没翻）。
- 验证方法：贴图接 Emission 渲染，纯看 UV 落点。

## A.6 镜像 + 坐标（Source 1 第一人称运行时）

- 不得把 Blender 预览的 root 变换直接当 viewmodel 变换。
- 拟合 **CF idle-posed 枪顶点 → stock idle-posed 枪顶点**：`H = sR+t`；整个场景统一 `v'=Hv`、`R'=H·B·H⁻¹`、`W'=H·W·H⁻¹`。只变顶点不共轭骨骼会散架。
- 左右修正在 H 之后，**绕枪身中心镜像**（不是原点）；顶点、rest、动画、attachment 全部同步镜像，并反转三角绕序。
- 不要用 decompiled 紧凑模型的 posed 网格拟合尺度；正确参考是官方正常 viewmodel（枪长约 35 单位）。
- stock attachment 世界位可直接作拟合目标，镜像时 attachment 一起镜像。

## A.7 贴图定位方法（命名约定）

| 资产 | 贴图路径(rez 内) | 例子 |
|---|---|---|
| 武器 PV | `PLAYERVIEW/PV-<模型名>.DTX` | `PV-M4A1_S_Transformers.DTX` |
| 角色手臂 | `PLAYERVIEW/FVIEW_{HAND,ARM}_<角色>_<BL|GR>.DTX` | 默认 `FVIEW_HAND_Nini_GR.DTX` |
| 配套图 | `SpecularMap/*_S`、`NormalMap/*_N`、`AlphaMap/*_Alpha` | PNG/TGA |
| 材质参数 | `WeaponShader/<枪>.CFG`、`AdvancedShader/Arm_<角色>_<阵营>_Piece<N>.CFG` | INI 文本 |

CFG 里直接写着全部贴图名 + 光照参数（SpecularPower、EnvCubeUsage、EnvCubeMapBrightness 等）。

## A.8 CF 材质的坑：specular map ≠ 高光图

- `*_S` 打开常是**亮银色完整枪图** —— 它是**环境反射色图**（`EnvCubeUsage=2`，envcube 采样后乘它）。
- alpha/mask 文件必须逐通道检查，不能按文件名假设 alpha 存在：天袭 `_M` 实际是 RGB，R=255 整面背景，发光信息在稀疏 G/B；直接用作 `$selfillummask` 会让整枪发光。
- 同一张高频 `_S` 不要同时驱动 `$phongexponenttexture` 和 `$envmapmask`，否则细节会被重复放大成反射噪点。

### A.8.1 第一人称金属参考值（冻结：天袭 2026-09-16）

目标是“金属高光呈现枪身本色，并随 viewmodel 光照明暗变化”。**默认且冻结**为 albedo-tinted Phong，不使用加色 envmap/rimlight。

天袭枪身 VMT 冻结值（`cf_galilace_pb.vmt` / `texture/build_textures_v2.py` 的 `gun_vmt()`）：

```vmt
"VertexLitGeneric"
{
    "$basetexture" "models/weapons/v_models/cf_tianxi/cf_galilace_pb"
    "$bumpmap" "models/weapons/v_models/cf_tianxi/cf_galilace_pb_n"
    "$phong" "1"
    "$phongexponent" "48"
    "$phongboost" "8"
    "$phongfresnelranges" "[0.05 0.45 1]"
    "$phongalbedotint" "1"
    "$selfillum" "1"
    "$selfillummask" "models/weapons/v_models/cf_tianxi/cf_galilace_pb_m"
    "$selfillumtint" "[0.1 0.25 0.65]"
    "$nocull" "0"
}
```

| 参数 | 冻结值 | 含义 |
|---|---|---|
| `$phongexponent` | `48` | 高光锐度（越大越尖） |
| `$phongboost` | `8` | 高光强度。v7 原为 2；2026-09-16 用户两次「提高一倍」后定为 8 |
| `$phongfresnelranges` | `[0.05 0.45 1]` | 正视 / 中角 / 掠射 |
| `$phongalbedotint` | `1` | 高光颜色继承 diffuse，金色仍是金色 |
| `$selfillumtint` | `[0.1 0.25 0.65]` | 仅能量纹路，不是金属 |

这是 Source 侧游戏内观感参考，**不是** CF CFG 的 SpecularPower 原公式。其他武器以此为起点，按验收改 boost，但不得把 envmap/rimlight 加回来，也不得用高频 `_S` 同时驱动 `$phongexponenttexture` 与 `$envmapmask`。selfillum 只允许逐通道验证过的稀疏 mask（天袭 = `_M` 的 `max(G,B)`）。

### A.8.2 第一人称油光 Phong（手臂冻结：2026-09-17）

目标是绸缎/油面高光：宽瓣、随光照走、正面不会整面发白。**禁止 envmap/rimlight**——Roxana 手臂接过 CF `Silver_map02` 立方体（`EnvCubeMapIntensity` 0.2/0.24）后，第一人称整臂加色并带无 mip 噪点，与枪身 v6 环境反射洗白同类，已撤销。

验收路径：手臂 `$phongboost` 0.6 → 1.2 → 油面试验 2.4（exponent 5）→ 用户「再减弱一半」回到 **1.2**。指数留在 5（比金属 48 宽）。

当前值写在默认手膜 `cf_nini_{hand,arm}_gr.vmt`（`native_vm/build_galilace_vm.py` 的 `arm_oil_vmt()`）。枪身 2026-09-17 试用过同一套后按用户要求退回 A.8.1。换角色时油光参数跟手膜走，不跟枪走。

```vmt
"$phong" "1"
"$phongexponent" "5"
"$phongboost" "1.2"
"$phongfresnelranges" "[0.15 0.55 1]"
"$phongalbedotint" "1"
```

| 参数 | 值 | 含义 |
|---|---|---|
| `$phongexponent` | `5` | 宽瓣油面；小于 A.8.1 的 48 |
| `$phongboost` | `1.2` | 强度。2.4 减半后的验收值 |
| `$phongfresnelranges` | `[0.15 0.55 1]` | 受光面一条高光，不是整臂发白 |
| `$phongalbedotint` | `1` | 高光跟贴图走 |
| `$envmap` / `$rimlight` | 禁用 | 第一人称 cubemap 会洗白+噪点 |

只用于手/袖。枪身 Phong 保持 A.8.1，**不改** `$selfillum`。

## A.9 手膜/角色系统（默认冻结：妮妮-保卫者 2026-09-17）

**默认手膜 = 妮妮-保卫者（Nini GR）。** 新武器第一人称手臂一律用这套，除非用户当场指定别的角色或阵营。不要默认回 FoxHowl / Roxana，也不要用武器 LTB 内嵌的 `Fview-hand*`/`Fview-arm*`。

### A.9.1 默认资产（MD5 分片已校验）

| 资产 | REZ 路径 | 包 | 备注 |
|---|---|---|---|
| ArmModel LTB | `Models/PLAYERVIEW/ArmModel/Arm_Nini_GR.LTB` | `rez4/RF016.REZ` | 154738B；46 骨 / 2 mesh |
| 手 diffuse | `ModelTextures/PLAYERVIEW/FVIEW_HAND_Nini_GR.DTX` | `rez6/RF017.REZ` | 131236B = 512 DXT1 |
| 袖 diffuse | `ModelTextures/PLAYERVIEW/FVIEW_ARM_Nini_GR.DTX` | `rez6/RF017.REZ` | 同上，无原生 HD |
| Normal | `ModelTextures/NormalMap/FVIEW_{HAND,ARM}_Nini_GR_N.PNG` | `rez6/RF017.REZ` | 保持 512，标 `NORMAL` |
| Spec / Alpha / CFG | `SpecularMap/*_S`、`AlphaMap/*_A`、`AdvancedShader/Arm_Nini_GR_Piece{0,1}.CFG` | `rez6/RF017.REZ` | 证据保留；Source 不用 `_S` 当 envmap |

网格（`decode/nini_gr/cf_skin_nini_gr.json`）：`FVIEW_HAND_NINI_GR001` 4593v / `FVIEW_ARM_NINI_GR001` 1914v。骨架 46 根 `FvARM-bone*`，**骨名与枪 PV 骨架一致** → 同套 clip 驱动，零重定向。

贴图：REZ 内没有高于 512 的手/袖 diffuse。按用户要求**直接** RealESRGAN 4x → 2048 BGRA8888（`decode/nini_gr/up/4x_FVIEW_{HAND,ARM}_Nini_GR.png`）。只超 diffuse。

Source 材质名：`cf_nini_hand_gr` / `cf_nini_arm_gr`。VMT 油光见 A.8.2。构建入口：`native_vm/build_galilace_vm.py` 的 `ARMDUMP`/`ARMTEX` 指向 `decode/nini_gr/`。

脚本：`acquire/acquire_nini_gr.py`、`decode/nini_gr/prepare_nini_gr.py`。

### A.9.2 接入规则（LBS）

CF 手臂 bind 是体侧休息位，枪 PV 的 FvARM 是持枪前伸位。逐顶点：

```text
v_gun = Σ w_i · B_gun[i] · inv(B_arm[i]) · v_arm
```

再走枪的 MXH。武器内嵌 Fview 网格丢掉，不要和默认 ArmModel 叠两层手。

### A.9.3 换膜（仅用户点名时）

1. 若当前手膜已验收，先整包冻存（天袭先例：`work/galil_ace_tianxi/arms/roxana_gr_frozen/`）。
2. `Arm_<角色>_<皮肤>_<BL|GR>.LTB` + `FVIEW_{HAND,ARM}_*` 走 MD5 分片提取。
3. `--dump-ltb-skin` → 确认 FvARM 骨名对齐 → LBS。
4. 无原生 HD 则 ComfyUI 4x 到 2048；normal 不超。
5. VMT 沿用 A.8.2，**禁止**把 CF `EnvCubeMap`（如 `Silver_map02`）接到第一人称手臂。
6. 从 staging/MIGI 清掉上一套 `cf_*hand*` / `cf_*arm*`，A/B hash 后再让用户 REBUILD。

### A.9.4 历史（不是默认）

- 灵狐者=FoxHowl（Casual/Deneb/Flower/Seaside/Teacher/Veteran_CFPassS7/Renewal × BL/GR）。雷神成品仍是 FoxHowl Renewal **BL**，不回溯改。
- 传说女帝=Roxana GR。天袭中间验收过，整包冻存在 `work/galil_ace_tianxi/arms/roxana_gr_frozen/`；不再作为默认。

## A.10 超分（ComfyUI）

- 本地 ComfyUI `127.0.0.1:8188`，模型 `RealESRGAN_x4plus.pth`，输入 `D:\Comfy-Desktop\ComfyUI-Shared\input`。
- 标准链：原生 1024 diffuse → RealESRGAN 4x 得 4096 → Lanczos 降到 2048 → 颜色校正 → `BGRA8888` 无损 VTF，并启用 `TRILINEAR`/`ANISOTROPIC`。4096 只作超分中间件；最终 2048 可减少显存和 VPK 体积，同时明显优于 1024 DXT1。
- 暗色金属 atlas 可使用雷神验收前参数作为起点：gamma `0.72`、brightness `1.08`、color `1.08`、contrast `1.03`；黑色 UV gutter 在 gamma 曲线下仍保持 0，不做固定灰度抬底。
- 雷神实现：`scripts/p5/build_leishen_texture_v2.py`；天袭实现：`work/galil_ace_tianxi/texture/build_textures_v2.py`。
- **只超 diffuse**；normal/spec 超分会引入伪细节。normal 保留原生分辨率并正确标记 `NORMAL`。

## A.11 Source 1 第一人称架构（P7-S05 / 本轮 Galil 同构）

天袭当前约 123 骨：`v_weapon` 根 + 47 根 CS `Bip01*` bonemerge 兼容骨 + CF 骨 + 4 根 attachment 骨 + fx 骨。CF 枪件刚性绑定 CF 节点；**默认手/袖来自 `Arm_Nini_GR.LTB`**，按逐顶点 LBS 烘到枪 bind 空间；idle/fire/reload/draw 直接使用 CF clip。

只部署第一人称资产（`v_rif_*` 模型 + 材质 + 声音 overlay）；不得改 `w_rif_*` 或第三人称材料。每次部署后对 world 文件做 hash/时间戳复核。

## A.12 隐藏 CS 手套/袖子的 bonemerge 坑

CS 手套和袖子是独立模型，按同名 `Bip01*` 骨 bonemerge 到武器模型：

```text
posed = W_weapon_bone @ inv(B_arm_bind) @ v_arm
```

- 把 CS 骨设成 identity **不会透明**：顶点落在相机附近形成满屏碎片。
- 钉到 `(0,-500,0)` 也不对：`-Y` 是枪口前方，远处仍能看到缩成一团的手膜。
- **已验证**：所有 CS `Bip01*` rest 与每帧动画统一钉 `(0,+500,0)`，送到相机后方视锥外。
- 不用透明材质：袖子/手套材料是共享 bonemerge 模型，替换会影响其他武器。

## A.13 CF 声音映射与事件时序

- CF 武器声音在 `rez/FMODStudio/Weapon(s)/*.bank`（FSB5），vgmstream 解出后转 44.1 kHz PCM16。`SND/**/*.WAV` 多为加密容器，不作输入。
- 模型事件用 `event 5004`。
- **同 channel 后续事件截断前音**：`BoltBack`/`BoltForward` 都是 `CHAN_ITEM`，即使后一个是静音 WAV 也会停掉前一个。静音事件必须放在有声事件**之前**，或干脆不发。
- 同一 PCM 不要映射给同 sequence 的两个事件（会叠音）。

## A.14 MIGI 更新与声音验证

- 必须遵守 §3.1 的 **staging A → MIGI addon B → pak C** 三层校验；只更新仓库 staging 不会被 MIGI REBUILD 读取。
- 改 `migi/csgo/addons/<addon>/` 后游戏不会自动读 addon 目录；必须由用户执行 **MIGI REBUILD** 写进 `pak01_dir.vpk`。
- REBUILD 前验证 A hash == B hash；REBUILD 后验证 B hash == C hash。任一不一致都不得进入视觉调参。
- `migi/csgo/materials/` 松散文件在本环境不覆盖 pak，不能作为迭代部署路线。
- 控制台 `play weapons/<dir>/<file>.wav` 可验证运行时解析到的实际 WAV。
- `snd_show 1` 在这套 Legacy/MIGI 环境无有用输出；`soundcache/*.cache` 不要未证明就删。

## A.15 工具/脚本索引

| 用途 | 位置 |
|---|---|
| LTB→skin JSON | `CFRezManager --dump-ltb-skin --input X.LTB --output Y.json` |
| LTB→骨架+动画 payload | `scripts/cf_ltb/p5_p7_s04_cf_animation.py` |
| REZ 分片校验读 | `scripts/material_recovery/rez_verified_payload.py` |
| REZ 索引 / DTX 解码 | `scripts/material_recovery/n05a_decoder_provenance_audit.py` |
| LTC 解密（bf*.ltc） | `scripts/material_recovery/n02_butes_config_triage._decode_ltc_c_sharp`（16B XOR key `5483B2E1…` + LZ） |
| CFT 表 | LZMA 解压后逐字节 XOR 0x10 |
| CF 声音提取/overlay | `scripts/p5/p5_p7_original_sound.py` |
| SMD/QC/编译/部署参考实现 | `scripts/p5/p5_p7_s05_cf_native_vm.py`（雷神；手膜仍是 FoxHowl BL，不当前默认） |
| 默认手膜 acquire | `work/galil_ace_tianxi/acquire/acquire_nini_gr.py` |
| 默认手膜 dump+4x | `work/galil_ace_tianxi/decode/nini_gr/prepare_nini_gr.py` |
| 天袭 VM（默认 Nini GR） | `work/galil_ace_tianxi/native_vm/build_galilace_vm.py` |

## A.16 公网工具对比（搜过的）

`lxh251826/CFRezManager`（本仓库前身）、`no-lith/RezExtract`、RaGEZONE `CF-REZTOOL`、mpgh `LTB→SMD` —— 都能解包/转格式，但**都没有分片校验**（拿到坏字节不自知）、**动画基本丢**、没有材质恢复。

---

# 附录 B. 天袭光效（原 `plan.md`，2026-09-16 并入并冻结）

> 2026-09-16 用户指示：金属光泽参考值固化；光效做到当前层即止。
> 逐轮试验过程留在 git history 与 `work/galil_ace_tianxi/effects/`。本附录只保留冻结结论、证据等级和以后若重启所需的约束。不要把本附录当活跃迭代清单。

## B.1 冻结范围

| 项 | 状态 |
|---|---|
| 枪身金属 | **FROZEN** 见 A.8.1：exponent=48 / boost=8 / fresnel=`[0.05 0.45 1]` / albedotint=1，无 envmap/rimlight |
| 默认手膜 | **FROZEN** 妮妮-保卫者（Nini GR），见 A.9 |
| 手臂油光 | **FROZEN** 见 A.8.2：exponent=5 / boost=1.2 / fresnel=`[0.15 0.55 1]`，无 envmap |
| idle LTBModel 层 | **FROZEN** 已进模型（见 B.4） |
| 龙眼 / 尾部 FlareSprite | **FROZEN** PCF + 模型 `$keyvalues` particles |
| 手工交叉龙眼面片 | **REJECTED** `ENABLE_EYE_GEOMETRY = False` |
| 其余 7 个 ParticleSystem | **DEFERRED** 未实现（避免过亮） |
| 动作组（draw/fire/reload/inspect） | **DEFERRED** |
| 变换形态 / QV 第三人称 | **DEFERRED** |
| addon A/B | 56/56 SHA-256 |
| pak C / 游戏 | `PACK_VERIFY_PENDING`（用户 MIGI REBUILD） |

完成定义：用户说「做到这样」即止。尚未恢复的空间层、动作组和动态照明明确列为缺口，不能凭材质编译成功标记全部还原。

## B.2 CF 来源（E0/E1 已完成，不必重做）

Bute `PVEffectName=pv_galilace_phantombeast_idle`。ClientFX 优先入口：`D:/Program Files/CF(2)/rez/RF004.REZ` 内 `ClientFX/CLIENTFX.FXF` / `.FCF`（目录 MD5 已校验）。解析按 [clientfx_tool](https://github.com/lokea2/clientfx_tool) `bin30_codec.cpp` 布局；**分析时不用 `-c20`**（会丢节点）。本地 FCF 是名称树，FXF 才是效果定义。

idle 组 **29 节点：14 LTBModel、7 ParticleSystem、5 Sprite、3 FlareSpriteFX**。全量导出：`work/galil_ace_tianxi/effects/discovery/clientfx_group_pv_galilace_phantombeast_idle.json`。

socket **不在**主体 `PV-GalilACE_PhantomBeast.LTB`（`nSockets=0`），而在 `PV-GalilACE_PhantomBeast_BL.LTB` / `_GR.LTB`（`nSockets=39`，含全部被引用的 `fix_effect_*`）。解析：`effects/discovery/parse_sockets.py` → `sockets.json`。多数 `fix_effect_*` 挂 `Box001`；若干环境位挂 `Scene Root`；`fix_effect_7` 挂 `Dummy008`。

FCF 名称树另有 63 个 `pv_galilace_phantombeast*` 组（idle/observe/reload/select/speed/chg × 皮肤）。动作组有原始定义，本冻结不实施。

资源图：`asset_graph.json`（99 文件 MD5）、`texture_channels.json`（76/76 DTX）、`previews/`。武器描述：`assets/weapons/galil_ace_tianxi/effects.json`。

## B.3 类型映射（已用天袭验证）

CF→CS **没有**通用 1:1 转换器，按类型拆：

| CF 类型 | Source 实现 | 天袭冻结现状 |
|---|---|---|
| LTBModel | 原几何 → SMD，additive `UnlitGeneric`，蒙皮到 fx 骨 | 已接 13 层 |
| FlareSpriteFX / 朝向相机的 Sprite | PCF sprite + `Movement Lock to Control Point` + 模型 `$keyvalues` particles | 龙眼簇 + 尾部 |
| ParticleSystem | 手工重建 PCF，无转换器 | 7 个未做 |

路径选择（原 plan 路径 A–F 的冻结结论）：枪身发光走 A（稀疏 selfillum，已在 v7）；表面流光走 C+B（原 LTB 网格 + AnimatedTexture）；龙眼光晕走 D（PCF），交叉面片 C 被否决。Fire-Kirin（`D:\data\mod\p_ak47_beast`）只可借「体积加法 mesh + jiggle」思路，禁止抄红橙外观或 ValveBiped 重网格。

## B.4 当前装车层

实现入口：`work/galil_ace_tianxi/native_vm/build_galilace_vm.py` 的 `FX_LAYERS` / QC `$keyvalues`；PCF 文本 `effects/probes/cf_tianxi_fx.txt` → `cf_tianxi_galilar_p1.pcf`（MIGI 约定：addon `p_cf_tianxi_galilar_p1` 对应该文件名）。

**网格（原 LTB，Sk/Offset 来自 FXF）：**

| 层 | socket | Sk | CF Offset | Source 校准 |
|---|---|---|---|---|
| L-flow front / COPY / back | `fix_effect_9` | 0.026 / 0.026 / 0.037 | `(0,1,0)` | `FLOW_CAL=(0,+4.0 Y,-1.8 Z)` |
| R-flow front / COPY / back | `fix_effect_23` | 0.0278 / 0.0278 / 0.0367 | `(1,1,0)` | 同上 `FLOW_CAL`（R 侧未单独验收） |
| parts 蓝 / 红、三角 L / R | `fix_effect_5` | 0.15 | 0 | 无 |
| simbol / simbol_glow | `fix_effect_10` / `11` | 0.002 / 0.016 | 0（原 CF `(0,2,0)` 在世界轴相加会抬到枪上方） | 无 |
| glitch | `fix_effect_10` | 0.0048 | 0（同上） | 无 |

流光贴图：AURA_54 / AURA_55 原 24 帧 SPR → 多帧 BGRA8888 VTF + `AnimatedTexture`。颜色乘数用节点原 Ck，未增强帧 RGB/alpha。

**龙眼：** 用户要求改回会投到地面的 PCF 版。`cf_tianxi_eye`（main+core+rbw+prism）挂 `fx16`，无 `view model effect`。2026-09-17 骨原点 `EYE_CAL=(0,0,-0.25)` Source Z（与 FLOW_CAL 同轴；先试 -2.5 过多，改为十分之一）；体积光球 / 交叉面片均关闭。simbol Offset 仍归零。

**未装车（DEFERRED）：** `core-glow`、`L-flow-p`、`R-flow-p`、`ALL-p-big-BB`、`ALL-p-big-YY`、`yellow-prism-TOP`、`yellow-prism-TAIL`；`cf_tianxi_rear`（fx34 精灵，已从模型撤下，避免漏到世界空间）。

## B.5 定位：哪些有依据，哪些是简化

CF 链：`父骨骼 bind × socket 局部 (pos/quat/scale) × ClientFX Offset/Sk`，再进 Source `MXH`（绕枪 `x=-5.223` 镜像 × ICP H，`s≈2.0025`）。

| 部分 | 证据等级 | 说明 |
|---|---|---|
| socket 名、父节点、局部 pos/quat/scale | **verified** | `_BL` LTB `LoadSockets` |
| 节点 Offset / Sk / Ck / 贴图路径 | **verified** | FXF 全量导出 |
| fx 骨平移 = `MXH @ socket.trans` | **verified** | 共轭 `anim_world` 平移会偏出枪身约 5 单位，已修 |
| mesh 忽略 socket 旋转；Offset 按 CF 世界轴相加 | **simplified** | 当前 `FX_LAYERS` 实现 |
| `FLOW_CAL=(0,4,-1.8)` | **approximation** | L-flow 游戏内校准；R-flow 直接复用 |
| PCF 半径 / alpha / rate | **approximation** | 无 CF→PCF 公式 |

挂点身份可靠。若某层漂了或贴面不对，先查旋转/Offset 简化与 `FLOW_CAL`，不要先改 socket 名。

## B.6 已否决与已知坑

- 交叉正交 additive 面片当龙眼：游戏内「太差、有面片感」，保持禁用。
- draw 事件创建粒子：切枪/状态切换后消失。常驻效果必须写模型 `$keyvalues -> particles`（`follow_attachment`）。
- 无 `Movement Lock` 的 PCF 会在世界坐标拖影。
- `build_galilace_vm.py` **不得**覆盖 v7 的 `cf_galilace_pb.vmt/vtf`（曾把 2048 BGRA 降成 DXT1）。
- DMX 数组元素间必须有逗号；内嵌 `DmeParticleSystemDefinition` 会让 `dmxconvert` 段错误。子效果用顶层定义 + `DmeParticleChild`。
- SMD 光效材质不要 `$vertexcolor/$vertexalpha`（无顶点色会把加法输出打成 0）。
- 贴图增强（SHINE_06 ×8 alpha 等）是失败的手工试验，不当事原转换参数。
- 2026-09-16：墙上游离蓝火一部分来自 `simbol`/`glitch` 抬出枪外（Offset 已归零）；地面/墙面那颗四角星是 `cf_tianxi_eye` 的世界空间投影。已从模型 `$keyvalues` 去掉该粒子。`"view model effect"` 不能只关世界通道，不要再用。

## B.7 以后若重启（当前不要做）

1. 活状态只改本文件，不要再新建根目录 `plan.md`。
2. 优先恢复 mesh 的 socket 旋转 + socket 局部 Offset；R-flow 在单独看图前不要继续叠 `FLOW_CAL`。
3. 7 个 ParticleSystem 与动作组有原始 FXF，但需要独立亮度预算，不能直接叠到当前层上。
4. 部署仍走 §3.1：A→B hash → 用户 MIGI REBUILD → B→C hash。松散 `migi/csgo/materials/` 不覆盖 pak。

## B.8 证据索引

均在 `work/galil_ace_tianxi/`：

| 路径 | 内容 |
|---|---|
| `effects/discovery/clientfx_group_pv_galilace_phantombeast_idle.json` | idle 组 29 节点全属性 |
| `effects/discovery/sockets.json` | 39 socket |
| `effects/discovery/asset_graph.json` / `texture_channels.json` / `previews/` | 资源与贴图通道 |
| `effects/baseline/manifest.json` | E0 A/B 基线 |
| `effects/review/` | 失败审计与分析 |
| `effects/probes/cf_tianxi_fx.txt` | PCF 源文本 |
| `native_vm/build_galilace_vm.py` | `FX_LAYERS`、挂点、QC |
| `assets/weapons/galil_ace_tianxi/effects.json` | 节点级中间描述 |
| `texture/build_textures_v2.py` | 冻结金属 VMT（A.8.1） |
