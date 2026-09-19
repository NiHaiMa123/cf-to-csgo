# R1A source_reference.blend 显示修复记录（G1 视图层修复，非动画/重定向修复）

状态：SOURCE_REFERENCE（骨架源参考），不构成 ANIM_FIXED / PASS / 验收。

## 用户反馈的回归
- 手臂不显示（上一版只显示枪，手臂是白块被隐藏）
- 枪模位置不对（弹匣竖条、拉机柄竖杆等部件悬浮/翻转）

## 根因
1. `BONE_MAP` 只映射前臂/手/手指/武器骨 —— 上半身链（spine/clavicle/upperarm）停在 CS rest，手被拉到 CF 位置 → 手臂网格拉成灰色巨块。
2. 逐骨 `pose.bones[].matrix =` 赋值在父子链上累积求值误差 → spine/clavicle/upperarm 爆出数千~百万级坐标。
3. CF 与 CS 骨轴约定不同：全量 CF 朝向直接套到 CS 视图骨上 → `M4A1_Clip`（24 verts）竖成黑条、`M4A1_Bolt`（110 verts）竖杆。

## 修复（r1a_source_switcher.py / r1a_apply）
- BONE_MAP 扩到全链：Scene Root → FvARM Pelvis/Spine/Spine1/Neck/Clavicle/UpperArm/Forearm/Hand/手指/Prop1。
- 赋值改为自顶向下逐骨计算 `matrix_basis`（rest_delta_from_basis），消除父子求值累积 —— 所有已映射骨的世界位置与 CF 源逐点一致（err 0.0），坐标全部有限。
- 三类骨三种策略：
  - `v_weapon.M4A1_Parent`：SLAM（直接 CF 世界矩阵）—— 枪身位姿与源一致。
  - 手臂/身体/手指骨：delta-from-bind —— 位置精确取 CF，朝向 = rest ⊗ CF世界差值（避免轴约定翻转）。
  - `M4A1_Clip` / `M4A1_Bolt`：不再映射，作为 `M4A1_Parent` 的刚性子骨 —— 随枪贴合（CS bind 关系）。代价：换弹时弹匣不再从枪上分离（其 CF 源运动仍可由骨架关节点显示）。
- 默认视图：side cam (30,-6.4,7) → 全枪+手臂同框；idle_0 / 帧0；范围 0–300。
- 诊断 joints/sticks 保持隐藏（需要看源骨架时开 `R1A_MESH_ANIM` 集合）。

## 验证
- 数值：全部 57 根姿态骨位置有限、与 CF 源一致；渲染多帧无爆坐标。
- 视觉：idle/select/reload 各帧枪体干净、弹匣入井、拉机柄贴合；手臂呈手形跟随 CF 源位置。
- 已知残留：手指偏“骨感”（CF 指位 + CS 朝向约定的折中）、弹匣换弹不分离 —— 均属于 G2 重定向范畴，本阶段不修。

## 未做
未编译、未部署、未改 Inspect/世界模型/音效/材质、未开 G2、未动冻结基线文件。
