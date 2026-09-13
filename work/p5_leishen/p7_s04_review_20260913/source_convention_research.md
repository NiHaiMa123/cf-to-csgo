# G1 源约定补充核查（2026-09-13）

这份笔记是 Planner 联网阅读代码、再检查本机 LTB 的结果。公开 LithTech 代码镜像可解释格式约定，尚未证明当前 CF runtime 与该版本逐行相同。

- [LTRotation 定义及序列化](https://raw.githubusercontent.com/jsj2008/lithtech/master/sdk/inc/ltrotation.h)：分量顺序为 x/y/z/w，单位旋转为0/0/0/1；ConvertToMatrix和Slerp委托给quat函数。这支持现有xyzw读取顺序，不能单独证明当前CF中的插值归一化策略。
- [TransformMaker 动画求值](https://raw.githubusercontent.com/jsj2008/lithtech/master/runtime/model/src/transformmaker.cpp)：同clip取前后关键帧，旋转调用Slerp、位置按时间参数插值，递归使用parent乘local；rotation-only节点从bind父偏移取位置。根节点还可叠加每动画平移，不能把引擎外层修饰也声称已复原。
- [quat基础约定](https://raw.githubusercontent.com/jsj2008/lithtech/master/sdk/inc/ltquatbase.h)：旋转向量辅助函数假设单位quaternion。这里只看到声明及部分inline函数，尚未由此核实Slerp/ConvertToMatrix内部是否归一化。
- [Blender F-Curve说明](https://docs.blender.org/manual/id/3.0/animation/keyframes/introduction.html)：关键帧值按曲线插值。不能把四个quaternion分量设成LINEAR就直接宣称等于SLERP；源对照应使用显式采样器，并测Blender中间帧与采样器的姿态误差。旧文档解释曲线概念，当前5.2.1行为需要实测。

本机实际排除项：独立读取当前604808字节PV LTB的全部57个节点，取节点index之后的flags字节（payload+2），计数 **flags=0：57个**。因此当前文件没有启用rotation-only分支；旧parser丢弃flags是通用缺口，不能把它当本次拉伸根因。需要在G1新审计保留flags并assert，而不是修改旧文件。

接下来的本地验证：全部57骨对比bind与各clip首帧；raw/normalized两路比较正交性、端点角度与全帧世界位置差。先得到可量化差异，再选择诊断采样约定。
