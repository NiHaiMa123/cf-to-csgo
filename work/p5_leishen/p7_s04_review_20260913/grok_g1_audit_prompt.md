继续同一个 P7-S04-R1-A。G0 已经完成且 Planner 独立复核通过，见 p7_s04_r1/review/planner_g0_review.json。用户明确说继续。无需重新请求 G0/G1 授权；G2 仍未开放。不要再执行 G0，当前 filepath 是 D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend。

这次只完成 G1 的离线约定与时间审计小检查点，写一个脚本后立刻执行，输出证据便结束。不创建 Blender 对象，不保存场景，不研究整个仓库。

1. 只读 p6/verified_root/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB，断言604808 bytes与SHA511dec8d2401a1886ddecd14b4f18e17ac0afbefd943f6dc11a3fd2f82ef6b49。压缩层provenance引用review_20260913/offline_audit.json。允许import旧p5_p7_s04_cf_animation的纯解析函数，不调用main/recover/retarget。解析顺序 parse_header → parse_skeleton → parse_weight_sets → parse_child_models → parse_anims。
2. 写 p7_s04_r1/scripts/g1_source_audit.py，输出 source/source_audit.json 和 source/timeline.json。记录节点父链、8 clips、select/reload/idle_0真实times_ms、events、100FPS fractional frame=ms/10。
3. 核查 matrix global/bind 与轨道 local 的含义：nodes.matrix是16 floats，比较row-major与transpose；分别以xyzw以及其它有证据的假设构造local→world，与各clip首帧的bind矩阵比较全部57骨的位置/旋转误差。引擎源码 model.h 的first-exported-frame注释是线索，不是直接结论。不要把一个骨的匹配当全体验证。
4. 保留原始quat并测全clips的norm范围、R转置R与determinant；单列reload左手key96。诊断对比单位化版本，验证identity、+90deg Z、q/-q，找出xyzw/conjugate方向与bind一致的约定。未知引擎插值习惯标OPEN，不声称完全还原runtime。输出raw vs normalized端点枪、左右手与idle误差（位置/角度）及全帧最大世界位置差。
5. 说明是否足够进入骨架可见对照；如果仍有歧义，列唯一具体下一验证步骤。状态用 G1_NUMERIC_AUDIT_READY_FOR_REVIEW 或 G1_CONVENTION_OPEN；不是SOURCE_REFERENCE_READY，因为还没可见对照。reference_kind=SKELETON_ONLY_REFERENCE，no weights，不能伪造蒙皮。可将已解析的必要轨道数据写 source/parsed_tracks.json 供下一步建图，本地保留，不上传原始binary。
6. 写 review/g1_audit_report.md 与 review/g1_audit_checkpoint.json，准确记录 compiled=false/deployed=false/user_accepted=false。不要改根文档、旧文件，不git commit/push。不绕权限。Python仍用已给定Codex runtime。

注意：下一阶段写Blender必须先assert前置条件，G0保存脚本仅事后报告不够健壮，本次不要重跑它。当前阶段全离线，优先用numpy/原模块纯函数完成数值审计，避免重复read/search耗尽轮数。
