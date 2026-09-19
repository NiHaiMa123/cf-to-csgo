# CF 原生预览（纯 CF 解包数据）— cf_native_preview.blend

## 状态

`source\cf_native_preview.blend` 已保存。**纯 CF 数据**，无任何 CS 骨架/网格/参数参与显示：

- 骨架：CF LTB 原始 57 节点（`R1A_CF_ANIM` 显示骨架 + `R1A_CF_DEFORM` 隐藏变形骨架）
- 网格：`cf_skin_dump.json` 导出的 11 个 PV-M4A1_S_Transformers.LTB 网格（4,370 顶点）
  - 蒙皮：`Fview-hand2`(1090v) / `Fview-arm2`(190v) —— 真权重+骨索引
  - 刚性件：Body/MAG/part01–05/Reload01/Reload02
- 动作：8 个 CF 原生 clip 全部可切（idle_0/select/reload/fire/prefire/postfire/run/knife-attack）

## 关键技术结论（本次定位）

1. **skinning 约定**：`v' = anim_world(N) @ inv(bind_world(N)) @ v`，其中
   - `bind_world` = LTB 节点记录里存的 4×4（行主序，trans@[3,7,11]）—— 已确认是 world，非 local
   - `anim_world` = payload `pos`+`quat_xyzw_world`（轨道 local 沿父链组合，标准 xyzw 四元数公式）
   - 验证：idle_0 f10 全部枪械节点 delta=0°；select f5 全节点一致 13.6°；fire ~2° —— 刚性整体运动
2. **原 Blender 散架根因**：armature rest 朝向必须 Y 沿骨轴，`rest_rot ≠ bind_rot` → armature modifier 的 `pose@inv(rest)` 旋转分量逐骨不同 → 件散。位置对但朝向错。
3. **解法**：隐藏 deformer 骨架 `R1A_CF_DEFORM`，烘焙 `pose_world = anim @ inv(bind) @ rest_local`（rest 被 inv 消掉），所有网格 armature modifier 指向它。位置逐点验证 = payload（err 0.0）。
4. **Blender 5.2 action_slot**：`animation_data.action` 赋值后必须同时设 `action_slot = action.slots[0]`，否则 fcurve 不评估。

## 刚性件→节点归属（最近顶点/质心 + 关节动作帧一致）

| mesh | node | 依据 |
|---|---|---|
| Body | Dummy01 | 组件根；开火时子节点全对其刚性 |
| MAG | Bone06 | 最近顶点 0.59；reload 中唯一大位移节点（弹匣出井） |
| Reload01 | Bone04 | 最近顶点 0.19；select/reload 拉机柄 |
| Reload02 | Box001 | 最近顶点 0.47 |
| part01–05 | Box003/004/005/006/002 | 最近顶点 ~0.00007（顶点恰在节点上） |

## 用法

- N 面板 → `CF` 页 → `CF clip` 下拉切换 8 个动作；播放头 0..clip 长度
- `R1A_CF_DEFORM` 隐藏（纯变形器）；`R1A_CF_ANIM` 是 CF 骨架关节线框（视口可见，不渲染）
- 重开文件若面板消失：Scripting 工作区对 `cf_native_switcher.py` 跑 Run Script

## 限制 / 已知项

- 无贴图（LTB OBJ 导出 0 贴图、11 missing）—— 占位材质（枪黑、手臂肤色）
- CF 视角模型 bind 是枪口朝上持握 —— 这是真实 CF PV 朝向，非 bug
- reload 中 Box003-6 挂载的小件有大开合动作（雷神皮肤特性），已按真实节点跟随
- 这是原生数据显示预览，**不是** CS-ready 重定向结果；G2 重定向阶段另算
- `r1a_apply`（CS 预览 handler）在本文件里仍注册着，只驱动已隐藏的 CS 对象，互不影响

## 灵狐者手膜替换（同日追加）

- 角色手臂膜库：`data/rf016/Models/PLAYERVIEW/ArmModel/Arm_*.LTB` —— 每角色独立第一人称手臂模型（灵狐者=FoxHowl，7 皮肤 × BL/GR）
- 已换 `Arm_Foxhowl_Renewal_GR.LTB`（新灵狐者·保卫者）：`fox_gr_hand` 4786v + `Arm_W` 851v（含手套+外套袖口）
- 换膜流程：`--dump-ltb-skin` 导 JSON → `bpy_foxarms.py` 改 ARMDUMP 路径重跑（自动删旧 CF_FVIEW_*、重建 DEFORM_ARMS 骨架+8 action）
- 骨架为 FvARM 46 节点子集（无枪挂点），骨名全同 → 同一套 clip 数据直接驱动
- **bind 与枪模不同**（手在体侧 vs 手前伸）→ 第二根隐藏变形骨架 `R1A_CF_DEFORM_ARMS`，烘 `anim@inv(bind_arm)@rest`，8 个 `R1A_CFDA_*` action
- 切换器 `_apply` 同时驱动 3 个骨架：DEFORM(枪) + DEFORM_ARMS(灵狐者手臂) + CF_ANIM(显示骨架)
- 原 `CF_Fview-hand2/arm2` 保留但隐藏 —— 想换回默认手就反隐藏+藏 CF_FVIEW_*
- 164 个武器 PV 变体（`data/p5_t02_native/ltb/`）也各带不同手膜（BL/GR/WOMAN/电竞版），同法可换
- 贴图：手臂 LTB 无内嵌贴图路径，UV 已建，材质仍占位 —— 走 material_recovery 线

## 贴图恢复（同日追加）—— material_recovery 管线复用成功

- **关键坑（N05-B 已解）**：REZ 目录项的 time 字段实际是分片号，payload 在 `rfXXX_<n>.rez`；`data/rf017` 老解包全坏（0/3258 有效）。用 `rez_verified_payload.read_verified_payload` + `n05a.decode_repo_pixels` 直接拿正确字节。
- **绑定不在 LTB 里**：LTB 只有 `advanced_shader` 命令行和 mesh 名；贴图名是**命名约定** `FVIEW_<HAND|ARM>_<角色>_<阵营>`，辅以 `AdvancedShader|WeaponShader/<名>.CFG`（列 SpecularMap/NormalMap/AlphaMap/EnvCubeMap 名称+光照参数）。
- **新包在 rez2/**：renewal 级角色资源在 `rez2/RF016.REZ`(模型) / `rez2/RF017.REZ`(贴图+CFG)，老 `rez/` 里没有。
- 灵狐者 Renewal GR：`PLAYERVIEW/FVIEW_{HAND,ARM}_Foxhowl_Renewal_GR.DTX`(512²) + Spec/Normal/Alpha PNG + `Arm_Foxhowl_Renewal_GR_Piece{0,1}.CFG` —— 已贴到 `CF_fox_gr_hand`/`CF_Arm_W`
- 雷神原版枪皮：`PLAYERVIEW/PV-M4A1_S_Transformers.DTX`(1024²) + `_S/_N/_alpha.tga` + `WeaponShader/M4A1_S_Transformers.CFG`（EnvCubeUsage=2 等参数）—— 已贴到全部 9 个 CF_M4A1_transformers_* 件
- 渲染验证：idle 全身带皮 + reload f80 弹匣随左手拔出，全部正确
- 可复用脚本：`work/p5_leishen/p7_s04_r1/scripts/{find_arm_tex,decode_renewal,decode_gun2,bpy_apply_tex,bpy_apply_guntex}.py`

## 修正（同日追加2）

- **UV V 翻转 bug**：dump JSON 是原始解码 UV，Blender 写入必须 `v → 1-v`（t02 已验证：OBJ 导出写 `vt(u,1-v)`，二次翻转会把弹匣井贴到枪托）。枪 9 件 + 手臂 mesh 已全部翻正
- **换潜伏者（BL）**：`Arm_Foxhowl_Renewal_BL.LTB`（fox_bl_HAND 3721v + Arm_W 801v，露指战术手套）+ `FVIEW_{HAND,ARM}_Foxhowl_Renewal_BL.DTX` + `Arm_Foxhowl_Renewal_BL_Piece{0,1}.CFG`
- bpy_foxarms.py 清理模式要从 `CF_FVIEW_` 扩成所有非枪 CF_* 网格（GR 残留 `CF_fox_gr_hand`/`CF_Arm_W` 曾被漏删）
