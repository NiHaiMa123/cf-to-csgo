# CF to CS:GO Modding Toolkit

将 **CrossFire（穿越火线）资源**提取、分析并转换为 **CS:GO Legacy Source 1 / MIGI** 可用 Mod 的工具与研究仓库。

仓库包含 REZ/音频处理、LTB 模型分析、Source 1 构建、MIGI 部署、原生材质逆向和最终武器资产定位工作。

---

# 1. 先看这 4 个 Markdown

根目录 Markdown：

```text
README.md  项目介绍 + 文档职责 + 领导 Agent / 执行 Agent 协作方式
AGENTS.md  只规定 Git 操作与本地文件保护
plan.md    蓝图 + 冻结事实 + Gate + §0 当前状态/当前任务
task.md    短指针，指向 plan.md §0（已与 plan 合并）
```

当前进度和下一轮任务只维护在 `plan.md` §0，不要再写一份平行的执行单。

---

# 2. 核心协作原则

这个仓库按 **Planner/Reviewer -> Executor -> Planner/Reviewer** 循环推进。

关键原则：

```text
plan.md §0 = 当前状态 + 当前一轮任务（或 NONE / STOP）
plan.md 其余 = 已确认的长期地图和冻结事实
```

`plan.md` §0.2 的 ACTIVE 任务不应该覆盖一个大阶段的所有可能工作。一个 task 应尽量是：

```text
范围明确
-> 本地 Agent 可以一次完成
-> 能产出可审计 evidence
-> 完成后值得领导 Agent 单独 Review
```

Executor 完成 `plan.md` §0.2 的一轮任务后必须停止并交回 Review，不自行连续执行后续阶段。

---

# 3. 领导 / Planning / Review Agent

适合 Chat/Sol 或其他负责全局规划和 Review 的 Agent。

每一轮：

```text
1. 读取 README.md
2. 读取 plan.md（先 §0，再冻结节）
3. 读取最新 executor commit / code / evidence
4. Review 本轮结果
5. 判断哪些结果可以正式冻结进 plan.md
6. 更新 plan.md §0（状态 + 下一轮 ACTIVE 任务或 NONE）
7. push master
```

`plan.md` 只写已经接受的长期信息，例如：

```text
pipeline / 阶段关系
Gate / acceptance criteria
正式 PASS / FROZEN checkpoint
经过 Review 接受的结构事实
经过 Review 接受的 scoped negative
长期 blocker / dependency
```

尚未 Review 的猜测不要写进冻结节。下一轮操作只写在 `plan.md` §0.2。

---

# 4. 执行 / Local Executor Agent

适合 Claude Code、Codex、MiniMax、Gemini、Luna 或其他能访问本地 repo / data / toolchain 的 Agent。

启动顺序：

```text
README.md
-> AGENTS.md
-> plan.md §0
-> plan.md 其余（背景）
```

执行 Agent：

```text
理解 plan 的长期背景
-> 只执行 plan.md §0.2 的 ACTIVE 任务
-> §0.2 为 NONE 则 STOP
-> 在任务范围内自主选择实现路线
-> 产出代码 / report / evidence
-> 精确 commit + push master
-> 返回 commit SHA 和结果摘要
-> STOP
```

Executor 不负责：

```text
自行修改长期 pipeline
自行宣布高层 Gate PASS
自行恢复被暂停的后续阶段
一轮 task 完成后继续猜下一阶段要做什么
```

这些由领导 Agent Review 后决定。

---

# 5. 标准交接循环

```text
领导 Agent
  read plan.md §0 + latest evidence
  -> Review
  -> freeze accepted facts into plan.md
  -> write ONE next review-sized task into plan.md §0.2 (or NONE)
  -> push master

执行 Agent
  pull master
  -> read README + AGENTS + plan.md §0
  -> execute ONE ACTIVE task
  -> commit code/evidence
  -> push master
  -> STOP

领导 Agent
  re-read latest master
  -> Review
  -> update plan.md §0
```

因此即使更换 Planner 或 Executor，也不依赖聊天记忆；最新 `master` 足以恢复上下文。

---

# 6. 项目长期 Pipeline

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

详细 pipeline、已完成 Gate、冻结 commit、以及 **当前状态/当前任务** 见 [`plan.md`](plan.md) **§0**。

---

# 7. 当前长期技术状态

活状态只维护在 [`plan.md`](plan.md) **§0**。这里只留不会每周改的冻结摘要：

```text
P4 Source 1 / MIGI baseline            = PASS / FROZEN
P4-M01 native material                 = INCOMPLETE
native gun-atlas DTX                   = SCOPED_NEGATIVE
WeaponShader CFG code consumer         = BLOCKED (.tvm0 + ACE VM_READ denied)
P5 雷神 identity                       = T01 图鉴已确认；等原生材质方法
```

---

# 8. 主要目录

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

# 9. 文档维护原则

不要再新增类似：

```text
P4_TASKS.md
P4_M01_CONTINUATION.md
REVIEW_FINAL_2.md
TASK_SPEC_REWORK_3.md
```

正确归属：

```text
长期事实 / pipeline / Gate / 当前状态与任务 -> plan.md
Git 操作                                    -> AGENTS.md
入口与角色说明                              -> README.md
运行细节 / evidence                         -> work/**
历史逐轮过程                                -> Git history
```

这套结构用于支持长期的跨 Planner / Executor Agent 协作。