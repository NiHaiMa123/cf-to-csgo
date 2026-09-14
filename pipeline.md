# Galil ACE-天袭 → CS:GO Galil AR 移植 Pipeline

> 用户 2026-09-14 任务：把 CS 里的 Galil（`v_rif_galilar`，Galil AR 槽位）替换为 CF 的 **加利尔ACE-天袭**。
> 方法链沿用已验证的 CF 原生管线（**附录 A**，原 `CF_NATIVE_PIPELINE.md` 已并入本文；参考实现 `scripts/p5/p5_p7_s05_cf_native_vm.py`，成品 `work/p5_leishen/p7_s05/`）。本文件 = 通用方法 + GalilACE 具体化（资产图、阶段开关、坑位差异）。Git 规则看 `README.md` §5。

---

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
| 手膜（同一 LTB 内嵌） | `Fview-hand2`/`Fview-arm2` mesh，蒙皮在同一套 56 节点 rig 上 | LTB 内 | 贴图复用 `work/p5_leishen/p7_s04_r1/source/armtex/`（Fview 族 UV 兼容） |

Bute 声音名映射（记录 #6941）：Shoot=`GalilACEPhantomB_Shoot`，ClipOut=`GalilACEPhantomB_ClipOut`，ClipIn=`GalilACEPhantomB_ClipIn`，Select/换弹=`GalilACEPhantomB_Select`，变形=`GalilACEPhantomB_Chg`，观察=`GalilACEPhantomB_Obv`，近战=`GalilACEPhantomB_ATT`。

**与雷神的差异**：PhantomBeast PV LTB 是 VVIP 模型（~519KB vs 雷神 153KB），节点/件数/`PIECE_NODE` 映射都要重新算；有 `PVEffectName=pv_galilace_phantombeast_idle` 粒子特效（不可移植，记为已知回退）；`_Chg` 变换形态首轮不做。

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
P7 部署      agent: addon 落盘到 migi addons -> 用户: MIGI UPDATE -> agent: pak hash 复核 -> deploy/
P8 验收      用户游戏内确认第一人称/声音/动作                [GATE: USER_RUNTIME_ACCEPTED]
```

硬规则（继承 CF_NATIVE_PIPELINE）：

- **REZ 分片**：一律 `read_verified_payload(index, entry)`，无 MD5 不算已验证；`data/` 老解包不用作输入。
- **UV**：dump JSON 是原始 UV，进 Source/Blender 写 `v → 1-v`，只做一次。
- **镜像**：CF 原始左右反；Source 1 侧在 H 之后绕**枪身中心**镜像（不是原点），顶点/rest/动画/挂点同步，三角绕序反转。
- **CS 手臂隐藏**：47 根 `Bip01*` 骨全帧钉 `(0,+500,0)`（相机后方），不做 identity 塌陷。
- **H 变换**：ICP 拟合 `CF idle-posed 枪顶点 → stock galilar idle-posed 顶点`，`v'=Hv`、`R'=H·B·H⁻¹`、`W'=H·W·H⁻¹`。
- **超分**：只超 diffuse；normal/spec 不超。
- **事件时序**：按 CF clip `times_ms` 投到 100fps 帧号；同 channel 后续事件会截断前音（BoltBack/BoltForward 坑）。
- **MIGI UPDATE/REBUILD 由用户手动执行**：agent 只负责把 addon 落盘到 `migi/csgo/addons/` 并提醒用户点 REBUILD，不替用户操作 MIGI；以 pak 内 hash == MIGI addon hash 为最终验证，不看 UI 日期或仓库 staging 文件。

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

## 4. 当前状态（2026-09-14 晚，用户已验收）

```text
P0: PASS   13/13 资产 MD5 分片校验恢复 -> acquire/verified_root/ (acquisition.json)
P1: PASS   LTB 56 节点 / 12 mesh / 10 clip 解出 -> decode/ (reference_payload.json 100fps, cf_skin_galilace.json, DTX->PNG)
P2: SKIP   Blender 预览脚本写好但渲染负载大导致 MCP 阻塞；用户已关 Blender。身份已由 Bute+资源路径+贴图确认。
P3: PASS   stock v_rif_galilar 反编译；H 变换 ICP 拟合 s=2.0025 det=+1 sym_trimmed_mean=0.353
           (csref/viewmodel_transform.json；锚点初始化改 PCA 主轴——3 点共线锚点会坍缩)
P4: PASS   v6：ComfyUI 4x 后降采样到 2048 -> BGRA8888 无损 diffuse；
           _S 低通平滑生成独立 BGRA8888 env mask；_M 只取稀疏 G/B 发光信息；
           phong 改回标量 exponent=48；使用地图自带有 mip 的 env_cubemap，避免单 mip
           Gold_map01 产生黄绿反射噪点；VTF 加 TRILINEAR+ANISOTROPIC(+NORMAL) flag
           (texture/build_textures_v2.py；参数映射自 CFG EnvCubeMapBrightness=3 等)
P5: PASS   work/galil_ace_tianxi/native_vm/build_galilace_vm.py
           108 骨（1 root + 47 CS 塌陷 + 55 CF + 4 attach + galilar_parent）
           8 序列：idle/fire1-3/reload/draw/lookat01(=observe 704f)/prepare/loop
           事件用 LTB 权威 keyframe label：ClipOut@33 ClipIn@117 (100fps)
           studiomdl 一次通过，6 文件齐全
P6: PASS   Weapon.bank FSB 流 -> 44.1k PCM16 -> 8 个 galilar wave 路径
           (fire×4=dry Shoot_1, distant=Shoot_1_R, clipout, clipin, draw=Select)
           boltback/boltforward 保留 stock；WeaponMove*=stock 共享 foley 不动
P7: PASS   pak01_dir.vpk 重建（vpk.exe -M），addons.json 加入 p_cf_tianxi_galilar_p1，
           23 文件全部入 pak 并复核；旧 pak 备份在 deploy/pak01_backup/
           注：本轮 pak 由 agent headless 重建（vpk -M）完成，仅作一次性验证；
           正式流程定为用户手动 MIGI UPDATE，agent 不做此步。
P8: PASS   用户游戏内确认：模型/手膜/动画/声音正常（2026-09-14）
```

## 5. 复现索引（照此可重走全流程）

前置依赖（`scripts/_paths.py` 提供）：CF 客户端目录、CS:GO 目录、
`vgmstream-cli`、`ffmpeg`、Crowbar（stock 反编译）、Source SDK `studiomdl.exe`、`vpk.exe`。

| 阶段 | 脚本 | 输入 → 输出 |
|---|---|---|
| 身份扫描 | `scan/scan_galil_index.py` `scan/find_bute_records.py` `scan/scan_fview_index.py` | REZ 索引 + Bute → `scan/*.json` |
| P0 | `acquire/acquire_assets.py` | REZ 条目 → `acquire/verified_root/` + `acquisition.json` |
| P1 | `decode/decode_assets.py` | verified_root LTB/DTX → `decode/`（payload/skin/audit/PNG） |
| P2 | 默认跳过；存疑时 `preview/bpy_build_preview.py` | decode → Blender 预览（只建 mesh+单帧姿态，不烘焙不渲染） |
| P3 | `csref/extract_galilar_ref.py` `csref/fit_transform.py` | pak01 stock mdl → `csref/decompiled_stock/` + `viewmodel_transform.json` |
| P4 | `texture/build_textures_v2.py` | ComfyUI 超分 diffuse + _S/_M mask + VMT → 仓库 staging addon，并同步至实际 MIGI addon |
| P5 | `native_vm/build_galilace_vm.py` | decode+csref+armtex → `native_vm/source1/` → studiomdl → `addon/` |
| P6 | `sound/build_sound_overlay.py` | `Weapon.bank` FSB（vgmstream+ffmpeg）→ `addon/sound/weapons/galilar/` |
| P7 | agent: A→B 同步并校验；**用户: MIGI REBUILD**；agent: B→C 校验 | staging addon → `migi/csgo/addons/` → 用户 REBUILD → pak hash 复核；详见 §3.1 |
| P8 | 用户游戏内验收 | — |

## 6. 已知回退 / 后续增强位

- `BoltBack/BoltForward` 帧 140/160 是按副件运动估的（CF 无 bolt label）——换弹尾段机械声不对位就调 `build_galilace_vm.py` 这两个帧号。
- `PV-GalilACE_PhantomBeast_Chg` 变换形态、QV 第三人称、`pv_galilace_phantombeast_idle` 粒子特效首轮未做。
- diffuse 经 4x 超分后以 2048 BGRA8888 无损 VTF 输出；免重启路线弃用（`mat_reloadallmaterials` 闪退 + 用户实测松散文件不覆盖 pak）。迭代 = 改 `build_textures_v2.py` 参数重跑落 staging 并同步实际 addon → A/B hash Gate → 用户 MIGI REBUILD → B/C hash Gate → 上游戏验收。
- **v5 黄绿噪点根因**：`GalilACE_PhantomBeast_M.PNG` 没有 alpha，R 通道全 255；直接作为 `$selfillummask` 等于整枪自发光。彩色高频 `_S` 同时驱动 phong exponent 与 envmap mask，再叠加只有一个 mip 的 Gold_map01 cubemap，进一步放大反射斑点。v6 只取 `_M` 的 `max(G,B)` 作为稀疏发光遮罩；`_S` 先 GaussianBlur 再独立生成 env mask；phong 使用标量 exponent；envmap 回退到地图 mipmapped `env_cubemap`。
- observe 的 6 个音效 cue 暂用 stock `WeaponMove*` 通用衣物音。

### 执行中发现的差异（已处理）

- **SND/*.WAV 是加密容器**（93B 头 + 无标准 magic）→ 声音实际取自 FMOD `Weapon.bank`，含 `_R` 混响尾变体（用作 distant 正好）。
- **LTB 内嵌权威事件 label**：reload 有 `WeaponClipOut@kf10`/`WeaponClipIn@kf35`（30fps 帧号 ×100/30 → 33/117）；select 有 `WeaponReload@kf1`。bolt 无事件 → BoltBack/Forward 暂按副件运动窗估 140/160，runtime 后微调。
- **观察动作**：`observe` clip 704f/7s，带 6 个音效 cue（observe1-5 label）→ 映射到 lookat01，暂用 stock WeaponMove 通用衣物音。
- **手部**：Fview-hand2/arm2 与枪同 rig，无需像 M4A1 那样跨 rig 重摆姿态；权重直接写。
- **附件**：flash/shelleject/stattrack/uid 挂在 Box001 下，idle f0 位置与镜像后 stock 完全一致（flash [-5.12,-36.43,-3.74]）。
- **MIGI UPDATE 可headless 复刻**：解 pak01_dir.vpk → 叠加 addon → 更 addons.json → `vpk.exe -M` 重打（`deploy/rebuild_pak.py`）。

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
| 角色手臂 | `PLAYERVIEW/FVIEW_{HAND,ARM}_<角色>_<BL|GR>.DTX` | `FVIEW_HAND_Foxhowl_Renewal_BL.DTX` |
| 配套图 | `SpecularMap/*_S`、`NormalMap/*_N`、`AlphaMap/*_Alpha` | PNG/TGA |
| 材质参数 | `WeaponShader/<枪>.CFG`、`AdvancedShader/Arm_<角色>_<阵营>_Piece<N>.CFG` | INI 文本 |

CFG 里直接写着全部贴图名 + 光照参数（SpecularPower、EnvCubeUsage、EnvCubeMapBrightness 等）。

## A.8 CF 材质的坑：specular map ≠ 高光图

- `*_S` 打开常是**亮银色完整枪图** —— 它是**环境反射色图**（`EnvCubeUsage=2`，envcube 采样后乘它）。
- alpha 图一般是全不透明遮罩；发光条要真还原得走 emission。

## A.9 手膜/角色系统

- CF 每角色第一人称手臂是独立 LTB：`Models/PLAYERVIEW/ArmModel/Arm_<角色>_<皮肤>_<BL|GR>.LTB`；也有武器 LTB 内嵌 Fview 手臂（GalilACE 如此）。
- 灵狐者=FoxHowl，皮肤：Casual/Deneb/Flower/Seaside/Teacher/Veteran_CFPassS7/Renewal 等。
- 手臂骨架 = FvARM 节点子集，**骨名与枪骨架完全一致** → 同套 clip 直接驱动，零重定向。

## A.10 超分（ComfyUI）

- 本地 ComfyUI `127.0.0.1:8188`，模型 `RealESRGAN_x4plus.pth`，输入 `D:\Comfy-Desktop\ComfyUI-Shared\input`。
- `work/p5_leishen/p7_s04_r1/scripts/comfy_upscale.py` —— 四节点 POST `/prompt`。
- **只超 diffuse**；normal/spec 超分会引入伪细节。

## A.11 Source 1 第一人称架构（P7-S05 / 本轮 Galil 同构）

108 骨：`v_weapon` 根 + 47 根 CS `Bip01*` bonemerge 兼容骨 + CF 骨 + 4 根 attachment 骨。CF 枪件刚性绑定 CF 节点；CF 手/臂按逐顶点 LBS 烘到枪 bind 空间；idle/fire/reload/draw 直接使用 CF clip。

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
| SMD/QC/编译/部署参考实现 | `scripts/p5/p5_p7_s05_cf_native_vm.py` |

## A.16 公网工具对比（搜过的）

`lxh251826/CFRezManager`（本仓库前身）、`no-lith/RezExtract`、RaGEZONE `CF-REZTOOL`、mpgh `LTB→SMD` —— 都能解包/转格式，但**都没有分片校验**（拿到坏字节不自知）、**动画基本丢**、没有材质恢复。
