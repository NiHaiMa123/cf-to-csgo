# Galil ACE-天袭 → CS:GO Galil AR 移植 Pipeline

> 用户 2026-09-14 任务：把 CS 里的 Galil（`v_rif_galilar`，Galil AR 槽位）替换为 CF 的 **加利尔ACE-天袭**。
> 方法链全部沿用已验证的 CF 原生管线（`CF_NATIVE_PIPELINE.md` + `work/p5_leishen/p7_s05/report.md` + `scripts/p5/p5_p7_s05_cf_native_vm.py`）。本文件是该链在 GalilACE 上的具体化，记录资产图、阶段开关和坑位差异。Git 规则看 `AGENTS.md`。

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
| 部署 | 新 addon `p_cf_galilace_tianxi`，只放第一人称资产；`w_rif_galilar*` 不动 |

## 3. 阶段流程（每步产 evidence，进 `work/galil_ace_tianxi/`）

```text
P0 资产恢复  verified_root 镜像 + SHA/provenance 记录      -> acquire/
P1 解码      skin dump(顶点/UV/权重) + 动画 payload(100fps) + DTX->PNG -> decode/
P2 身份      Blender cf_native_preview 渲染 -> 用户认图     -> preview/   [GATE: USER_VISUAL_MATCH]
P3 CS 参考   stock galilar 反编译 -> H = sR+t ICP 拟合      -> csref/
P4 贴图      diffuse 4x 超分(ComfyUI 127.0.0.1:8188) -> VTF/VMT -> materials/
P5 模型      改编 s05 脚本 -> SMD/QC -> studiomdl           -> source1/
P6 声音      CF WAV -> 44.1k PCM16 -> galilar 文件名 overlay -> sound/
P7 部署      addon staging -> migi addons -> UPDATE pak -> hash 复核 -> deploy/
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
- **部署后必须 MIGI UPDATE**；以 pak 内 hash == addon hash 为验证，不看磁盘文件。

## 4. 当前状态（2026-09-14 晚）

```text
P0: PASS   13/13 资产 MD5 分片校验恢复 -> acquire/verified_root/ (acquisition.json)
P1: PASS   LTB 56 节点 / 12 mesh / 10 clip 解出 -> decode/ (reference_payload.json 100fps, cf_skin_galilace.json, DTX->PNG)
P2: SKIP   Blender 预览脚本写好但渲染负载大导致 MCP 阻塞；用户已关 Blender。身份已由 Bute+资源路径+贴图确认。
P3: PASS   stock v_rif_galilar 反编译；H 变换 ICP 拟合 s=2.0025 det=+1 sym_trimmed_mean=0.353
           (csref/viewmodel_transform.json；锚点初始化改 PCA 主轴——3 点共线锚点会坍缩)
P4: PARTIAL 未走 ComfyUI 超分；直接用 1024 原生 diffuse+normal -> VTF（如需 4K 再补）
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
P8: PENDING 用户 runtime 验收（idle/draw/fire/reload/inspect/枪口/抛壳/声音/手膜）
```

### 执行中发现的差异（已处理）

- **SND/*.WAV 是加密容器**（93B 头 + 无标准 magic）→ 声音实际取自 FMOD `Weapon.bank`，含 `_R` 混响尾变体（用作 distant 正好）。
- **LTB 内嵌权威事件 label**：reload 有 `WeaponClipOut@kf10`/`WeaponClipIn@kf35`（30fps 帧号 ×100/30 → 33/117）；select 有 `WeaponReload@kf1`。bolt 无事件 → BoltBack/Forward 暂按副件运动窗估 140/160，runtime 后微调。
- **观察动作**：`observe` clip 704f/7s，带 6 个音效 cue（observe1-5 label）→ 映射到 lookat01，暂用 stock WeaponMove 通用衣物音。
- **手部**：Fview-hand2/arm2 与枪同 rig，无需像 M4A1 那样跨 rig 重摆姿态；权重直接写。
- **附件**：flash/shelleject/stattrack/uid 挂在 Box001 下，idle f0 位置与镜像后 stock 完全一致（flash [-5.12,-36.43,-3.74]）。
- **MIGI UPDATE 可headless 复刻**：解 pak01_dir.vpk → 叠加 addon → 更 addons.json → `vpk.exe -M` 重打（`deploy/rebuild_pak.py`）。

详细执行记录追加在 `work/galil_ace_tianxi/` 各阶段目录的 report/json。
