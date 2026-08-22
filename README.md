# CF to CS:GO Modding Toolkit

将 **CrossFire（穿越火线）资源**提取、分析并转换为 **CS:GO Legacy Source 1 / MIGI** 可用 Mod 的工具与研究仓库。

仓库包含 REZ/音频处理、LTB 模型分析、Source 1 构建、MIGI 部署、原生材质逆向和最终武器资产定位工作。

---

# 1. 先看这 4 个 Markdown

根目录只保留 4 个职责明确的 Markdown：

```text
README.md  项目介绍 + 文档职责 + 领导 Agent / 执行 Agent 协作方式
AGENTS.md  只规定 Git 操作与本地文件保护
plan.md    静态长期蓝图：完整 pipeline、Gate、冻结事实、关键技术结论
task.md    动态当前任务：下一步要做什么、可尝试路径、输出和验收要求
```

这四个文件故意分开，避免“长期计划、当前任务、Git 规则、Review 历史”混在一个文件里反复覆盖。

---

# 2. 两类 Agent 怎么工作

## 领导 / Planning / Review Agent

适合 Chat/Sol 或其他负责全局规划与 Review 的 Agent。

每一轮应：

```text
1. 读取 README.md
2. 读取 plan.md，理解长期 pipeline / Gate / frozen facts
3. 读取 task.md，知道当前执行目标
4. 读取最新 executor commit / evidence
5. Review 当前结果
6. 决定下一步
7. 重写 task.md
```

只有以下情况才修改 `plan.md`：

```text
长期 pipeline 发生变化
阶段 Gate 发生变化
某个关键事实正式冻结 / 被新 counterevidence 推翻
长期阶段关系发生变化
```

不要把每一轮临时尝试、executor checklist、短期分支都写进 `plan.md`。

## 执行 / Local Executor Agent

适合 Claude Code、Codex、MiniMax、Gemini、Luna 或其他能访问本地 repo / data / toolchain 的 Agent。

启动顺序：

```text
README.md
-> AGENTS.md
-> plan.md
-> task.md
```

执行 Agent 应：

```text
理解 plan 的长期上下文
-> 只执行 task.md 当前任务
-> 根据 task 中的策略池自主选择高信息增益实现路线
-> 产出代码 / report / evidence
-> 精确 commit + push master
-> 停止并交回领导 Agent Review
```

执行 Agent **不负责自行重规划整个项目**，也不应该因为一条实现路径失败就把“下一步怎么办”重新抛给用户；`task.md` 会给出目标、边界、可尝试路线和 handoff 条件。

---

# 3. 跨领导 Agent / 执行 Agent 的交接协议

标准循环：

```text
领导 Agent
  read plan + current task + latest evidence
  -> Review
  -> 写新的 task.md
  -> push master

执行 Agent
  pull master
  -> read AGENTS + plan + task
  -> execute
  -> commit code/evidence
  -> push master

领导 Agent
  re-read latest master
  -> Review
  -> 写下一轮 task.md
```

这样即使更换：

```text
Sol -> 其他 planning model
MiniMax -> Gemini -> Luna -> Codex
```

也不依赖聊天记忆。任何新 Agent 只要读这 4 个 Markdown 和最新 evidence，就能恢复正确上下文。

---

# 4. 项目长期 Pipeline

简化主链：

```text
CF 原始资源
-> REZ / LTB / DTX / TGA / CFG / audio
-> model / UV / skeleton / animation evidence
-> Source 1 SMD / QC / VMT / VTF
-> compile / validate / package / MIGI
-> native CF material recovery
-> final M4A1-雷神 identity
-> release quality
-> Inspect / IK / CF original animation/sound enhancements
```

详细 pipeline、已完成 Gate、冻结 commit、N01/DTX/TGA/CFG 关键结论全部见 [`plan.md`](plan.md)。

当前执行内容不要从 README 猜，**只看 [`task.md`](task.md)**。

---

# 5. 当前技术大状态

长期上已经确认：

```text
CF weapon -> Source 1 -> MIGI baseline = PASS / FROZEN
BornBeast native material closure      = INCOMPLETE
old-corpus engine consumer search      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
P5 final Leishen flow                  = waiting for native material method
```

当前下一步由 `task.md` 单独维护，因此 README 不复制 task 细节，避免入口说明过期。

---

# 6. 主要目录

```text
CFRezManager/              C# CF resource manager / decoder / inspection
scripts/
  cf_extract/              CF REZ / FMOD extraction
  audio_clean/             audio repair / cleanup
  cf_ltb/                  LTB diagnostics
  weapon_port/             CF weapon -> Source 1 pipeline
  material_recovery/       native material / runtime evidence research
  csgo_pack/               CS:GO / MIGI packaging
  gsi/                     game-state integration
assets/weapons/            auditable weapon manifests / mappings
work/                      tracked reports / evidence / derived outputs
data/                      local CF inputs; never upload
migi_tools/                MIGI toolchain
tools/                     third-party tools
tests/                     smoke / regression tests
```

---

# 7. 常用入口

项目冒烟：

```powershell
python tests/run_smoke.py
```

构建 CFRezManager：

```powershell
dotnet build .\CFRezManager\CFRezManager.csproj --no-restore
```

Source 1 武器流水线：

```text
scripts/weapon_port/pipeline.py
```

材质/runtime evidence：

```text
scripts/material_recovery/
```

---

# 8. 文档维护原则

不要再新增：

```text
P4_TASKS.md
P4_M01_CONTINUATION.md
REVIEW_FINAL_2.md
TASK_SPEC_REWORK_3.md
```

类似的根目录流程文档。

正确做法：

```text
长期事实 / pipeline / Gate -> plan.md
当前下一步                  -> task.md
Git 规则                     -> AGENTS.md
入口与角色说明               -> README.md
运行细节 / evidence           -> work/**
历史逐轮过程                  -> Git history
```

这套结构就是为了支持长期的“领导 Agent 负责 plan/review、执行 Agent 负责落地”的跨模型协作。
