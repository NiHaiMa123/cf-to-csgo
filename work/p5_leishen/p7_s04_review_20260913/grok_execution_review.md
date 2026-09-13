# Grok 4.6 执行与复核记录

用户已指定本机 Grok 终端。执行器 `D:\software\grok build\grok.exe`，显式模型 `grok-4.6`；独立 headless session `01a098c9-1818-74f1-b82a-b3e9976e433b`，未使用绕过权限参数。没有向其他模型代发。

## 已发生的执行

1. G0–G1合并指令，16轮上限：只完成只读查询、冻结输入哈希和查询脚本，因max turns reached结束。
2. 收窄为G0，6轮上限：Grok完成Save Copy和新working文件，返回 `G0_BACKUP_READY_FOR_REVIEW`。Planner独立读取live和磁盘SHA后为 **G0_VERIFIED**。
3. G1离线数值审计，8轮上限：Grok写并执行 `p7_s04_r1/scripts/g1_source_audit.py`，生成 `source/source_audit.json`、`timeline.json`、`parsed_tracks.json`，最后因max turns reached停止。没有生成完整G1报告或source_reference.blend，没有修改场景或动画。本记录是Planner复核结论，不能冒充Grok已交完整报告。

当前无本轮仍运行的Grok进程。动画状态仍 **REJECTED / NOT_FIXED**；compiled=false，deployed=false，user_accepted=false。

## G0复核

当前Blender文件：`work/p5_leishen/p7_s04_r1/baseline/working_20260913_113051.blend`。

未保存内存备份：同目录 `live_unsaved_20260913_113051.blend`。两次Save操作FINISHED，文件均17471964字节。Planner复核9个冻结文件、2个新文件SHA以及当前路径、14对象、6Actions、draw25/OBdraw均通过，见 [planner_g0_review.json](../p7_s04_r1/review/planner_g0_review.json)。备份未在另一Blender进程中重新打开，不能把哈希检查描述为完整文件重载测试。

G0脚本仅在事后报告部分失败条件，复用不安全：本次实测保存成功；后续不得重跑该脚本，必须先assert路径/哈希/目标不存在和上一保存成功。

## G1方法复核：CHANGES_REQUIRED

- 首版按所有clips首帧与bind的最大误差排名，选择row3平移。这混合行列约定，已否决。Grok第二次执行已将端点计算固定为xyzw、col3平移、parent@local；该修正与SDK代码和Planner独立数值一致。
- 当前资源的bind不同于当前动画首帧，不代表解析失败。53/57个bind父相对位置与reload0 local匹配、枪分支能对齐，是有用证据；其余差异必须保留，不能当作可随意增加骨盆偏移的授权。全部flags为0，未启用rotation-only。
- **否决当前JSON的next_verification_step**：`B_local @ inverse(A_reload0) @ A(t)` 在t=0必定得到B_local，这是构造恒等式，不是格式验证。它会把CF源动作重定向到另一姿态，不能用于建立“原始CF对照”。不得执行这一步后声称源骨架正确。
- raw矩阵不是单位正交旋转，直接用trace公式计算角度不可靠。raw侧保留RᵀR/determinant和位置；角度使用单位化版本，或明示经polar decomposition提取后的旋转。
- `max_world_travel` 是相对首帧的行程，并非raw与normalized两路之差。所需差值已由Planner独立计算，见 [review_g1_numeric.json](review_g1_numeric.json)。

可以保留的测量：源body/packed来源正确，57节点/8clips；draw640ms、reload1600ms；reload左手key96的raw矩阵det=0.9276306731，正交误差0.0723688076。单位化对全帧关节点位置的最大影响：reload约0.04845196 CF单位（key96，L Finger12），select约0.00003590。单位化端点枪/双手与idle位置误差均<0.00004、角度<0.00012度。这不等于完成手套、袖子或游戏验收。

## 下一份Grok操作单（仍在G1，尚未派发）

1. 阅读本复核、`source_convention_research.md`和task G1。使用新小检查点，避免继续在大历史中反复读取。
2. 保留当前审计为失败证据，新写 `g1_source_audit_v3.py` 与 `source_audit_v3.json`。不沿用自动挑选winner，不强制bind=clip0，不加入骨盆或根骨补偿。
3. 明确格式约定来自公开SDK和本地验证：xyzw、col3、parent@local；flags全部0；原始tracks不变。逐帧57骨与现有纯函数比较；raw/normalized两路正交性及差值与Planner报告对照。记录SDK版本不等于当前CF runtime的边界。
4. 为源对照选择明确标注的normalized/shortest-arc SLERP诊断采样；保留原始quat。写真实ms时间轴，不把LINEAR分量曲线冒充SLERP。若采样方式仍有疑问，指出具体误差，不用bind匹配掩盖。
5. 数值复核通过后，才建新 `CF_SOURCE_REFERENCE` 场景和前缀对象；可以分别画原始轨道骨架与静态bind骨架，清晰区分，不能将两者强行叠合。无权重时标SKELETON_ONLY_REFERENCE。保留当前CS旧场景用于后续对照。
6. 输出可播放的新source_reference.blend、固定镜头的全动作检查材料、source_audit_v3.json、timeline和r1a_report/result。先assert工作副本路径和旧文件hash，保存到新目标，不复用G0脚本。
7. 完成G1后停；G2控制rig/接触修复仍未开放。禁止编译、部署、宣称用户接受。

## Git交付状态

最初详细方案已本地提交 `febb9f0`。本次后续检查点由Planner精确提交；`.blend`备份与parsed_tracks原始轨道转储保留本地，不加入本次提交。用户已有scan.json修改保持未动。

`origin`为用户拥有的公开仓库 `NiHaiMa123/cf-to-csgo`。自动审批两次拒绝push：虽然已核实所有者，仍要求针对公开发布含本地路径/资源诊断文本的明确许可。没有改用其他渠道绕过。当前GitHub未收到本轮提交。
