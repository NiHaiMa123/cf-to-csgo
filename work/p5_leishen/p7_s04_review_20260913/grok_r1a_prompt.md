请使用 grok-4.6 执行 D:\project\cf_to_csgo 的 P7-S04-R1-A。先读根目录 AGENTS.md、plan.md §0.2 和 task.md。用户明确要求先有详细方案，再由本机 Grok 逐阶段操作；这是 Planner 已完成的第一阶段交接。

只执行 task.md 的 G0–G1：保护当前 Blender 未保存现场，保存到新副本；建立正确 CF 源骨架/枪匣栓轴线与真实时间轴的对照。旧动作与旧磁盘文件继续冻结。本轮最多 SOURCE_REFERENCE_READY_FOR_REVIEW，不做第三版 retarget，不执行 G2–G5，不编译、不部署，不修改游戏、声音、材质、Inspect、world/dropped。

Blender 已运行，项目 TCP bridge 位于 scripts/cf_ltb/blender_mcp_exec.py（127.0.0.1:9876）；查询再行动。Reviewer只读证据在 work/p5_leishen/p7_s04_review_20260913/。当时文件为 work/p5_leishen/p7_s04/blender/p7_s04_current.blend，dirty=true，draw frame25，30FPS；请刷新状态。必须先保存内存中的未保存内容到新 baseline/live_unsaved_<timestamp>.blend，不能只复制磁盘文件，更不能覆盖原路径。

新产物/脚本只写 work/p5_leishen/p7_s04_r1/。用明确路径和新对象前缀，禁止清空场景/Actions/orphan purge。CF几何JSON无权重，骨架对照请标 SKELETON_ONLY_REFERENCE，不伪造原生蒙皮。压缩与解压SHA不同但来源已通过校验；详见audit_inputs.py。两版共同的clip0重置、手臂链和时间问题都已写入task，不要直接再跑旧脚本。

本机 Python 为 C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe。优先写可复现的小脚本，经项目bridge调用Blender；工具每次只完成一个明确步骤。需要工具权限时保持默认权限机制，不使用always-approve/bypassPermissions，不擅改系统权限。

请输出 source_reference.blend、source_audit.json、timeline.json、可见的检查图或短片及 review/r1a_report.md、review/r1a_result.json；具体字段与Gate见task。若有依赖/权限/解码约定不确定，保留已完成工作并明确列出，不硬闯下一层。禁止自行宣布用户接受。

Planner正在协调本轮，不要git commit/push，也不要改根目录plan/task，以免并发写入。完成G0–G1或遇到需要Review的具体阻塞后结束，返回产物路径和真实状态，等待Planner Review。
