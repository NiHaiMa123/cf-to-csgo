上一轮因 16 轮上限停止，session=01a098c9-1818-74f1-b82a-b3e9976e433b。现有 g0_query_live.py 已实际执行，baseline/live_query.json 确认 dirty=true、原filepath、frame25。不要重新遍历整个仓库或研究 quaternion；本次只完成 G0，先交检查点。

只做以下操作：
1. 在 work/p5_leishen/p7_s04_r1/scripts/ 写一个小型 Blender G0 保存脚本。通过已有 bridge 执行。先刷新 filepath/is_dirty/frame/action/slot，与 baseline/pre_hashes.json 比对旧文件 SHA。未知状态就报告。
2. 目标都必须是新唯一绝对路径，位于 p7_s04_r1/baseline。用 bpy.ops.wm.save_as_mainfile(filepath=新 live_unsaved 时间戳.blend, copy=True) 保存当前内存。要求返回 FINISHED、文件存在且非空；记录保存后 filepath 仍是旧路径。不要假定 dirty 状态是否保留，照实记录。
3. 然后用 save_as_mainfile(filepath=新 working 时间戳.blend, copy=False) 将当前会话切到新工作副本。保留所有对象/Actions/scene/帧/选择，不改动画，不清空，不重启。校验冻结旧 blend/SMD/脚本/body 的 SHA 全部未变。
4. 写 baseline/preflight.json，包含 backup/working 的绝对路径与 SHA、前后 live 状态、冻结文件比较；拓扑/约束/Action 等可引用现有 live_query.json。写 review/g0_checkpoint.json 与简短 review/g0_report.md。状态最多 G0_BACKUP_READY_FOR_REVIEW，G1 仍 pending。
5. 完成便结束。不要研究 G1、不要碰 retarget/游戏，不要 git commit/push，不改根目录 task/plan。

Python 路径 C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe，bridge scripts/cf_ltb/blender_mcp_exec.py，调用 execute_code --code-file <新脚本>，默认 127.0.0.1:9876。保持现有权限机制，不添加 bypass/always-approve。你已具备所需上下文，下一工具应直接落地保存脚本并执行，避免再次读取相同资料耗尽轮数。
