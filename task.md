# task.md — 当前执行任务

> 本文件只描述 **一轮可独立 Review 的当前任务**。  
> Executor 完成本文件后必须提交 evidence 并停止；由领导/Review Agent 决定哪些结果冻结进 `plan.md`，再重写下一轮 `task.md`。  
> 长期 pipeline 与冻结事实看 [`plan.md`](plan.md)。Git 操作看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 当前任务

```text
Task ID: P4-M01-N02-A
Title: Runtime Root Discovery & Candidate Inventory
State: ACTIVE
Parent: P4-M01-N02 Runtime Artifact Acquisition
```

目标：**在本机找到可信的 CrossFire 安装/runtime root，并建立可供下一轮静态分析选择目标的 runtime artifact inventory。**

本轮只解决“新输入在哪里、有哪些候选”。

本轮 **不要求** 继续做 strings/xref/反编译/CFG consumer tracing；这些应在 Review 后按 evidence 单独生成下一轮任务。

---

# 2. 本轮需要回答

尽可能回答：

1. 本机是否存在完整或部分 CF client/runtime 安装目录？
2. 找到了哪些可信 root，依据是什么？
3. root 内有哪些值得后续静态分析的 EXE/DLL/archive/shader 类 artifact？
4. 哪些候选最值得下一轮优先分析？
5. 如果找不到，搜索范围是否足以形成 bounded negative？

---

# 3. 可尝试实现路径

以下是策略池，不是固定顺序。根据本机线索选择信息增益最高的方法即可。

## 3.1 Root discovery

可尝试：

- repo/config/report 中已有的 source/install path 线索；
- Windows uninstall registry / App Paths；
- Desktop / Start Menu `.lnk` target；
- WeGame / launcher manifest、配置或安装记录；
- 常见 Tencent / WeGame / CrossFire 目录；
- 枚举 fixed drives 后做有界目录名搜索；
- 如果 CF / WeGame **本来已经运行**，只读查询 executable path / loaded module path。

不要为了定位路径而启动游戏或未知程序。

## 3.2 Candidate inventory

对可信 root 优先 inventory：

```text
*.exe
*.dll
*.rez
*.pak
*.pck
*.bin
*.fx
*.fxc
*.cso
*.shader
*.shd
renderstyle / shader / effect related files or directories
```

避免重新扫描整套音频、贴图或旧 `data/**` corpus。

每个 artifact 尽量记录：

```text
root_id
path_alias / relative path
size_bytes
sha256
extension
file magic / PE flag / archive flag if easy to obtain
version / product / description if available
signer if available
candidate_role
why_candidate
```

本轮允许根据目录、文件类型、版本信息和模块命名做 **候选排序**，但这些只能是 triage，不是 runtime binding proof。

---

# 4. 建议实现

如果一次性命令不足以稳定复现，优先新增或完善：

```text
scripts/material_recovery/n02_runtime_artifact_acquire.py
```

建议 evidence 目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/
```

本轮建议输出：

```text
artifact_inventory.json
acquisition_report.md
```

可以增加实际有价值的辅助 JSON，但不要为了凑格式生成空报告。

---

# 5. Completion / Handoff

## A. 找到可信 runtime root 和候选

返回：

```text
RUNTIME_INVENTORY_READY_FOR_REVIEW
```

至少给出：

```text
root(s) + discovery evidence
artifact counts by type
inventory path
Top candidate list
每个 Top candidate 的 path alias + SHA256 + size + why_candidate
本轮未覆盖的范围
```

完成后 **停止**。不要自行继续做 deep strings/xref/decompile。

领导 Agent Review 后再决定下一轮，例如：

```text
N02-B PE / strings static triage
N02-B archive/shader triage
N02-B launcher/runtime-root expansion
```

## B. 没找到可信 runtime root

只有形成 bounded negative 后才返回：

```text
NO_RUNTIME_ROOT_FOUND_LOCALLY
```

至少说明：

```text
检查过哪些 discovery source
扫描过哪些盘/目录范围
排除了什么以及为什么
是否只发现 launcher / updater / unrelated Tencent components
下一轮最需要用户补充的具体输入
```

---

# 6. 本轮禁止事项

- 不重复旧 `data/**` 的 basename/config/CFG curve-fitting 搜索；
- 不执行未知 CF client/runtime binary；
- 不触发 launcher patch/update；
- 不做进程注入、anti-cheat bypass、runtime memory dump；
- 不上传 raw EXE/DLL/REZ/PAK/PCK/shader binary；
- 不把目录邻近/文件名当 material binding proof；
- 不自行宣布 `P4-M01 = NATIVE_MATERIAL_RECOVERED`；
- 不恢复 P5-T02；
- 不修改 `plan.md`。

---

# 7. Executor 交回内容

完成后只需交回：

```text
status
commit SHA
新增/修改的 scoped files
inventory/report 路径
Top candidates 或 bounded negative 摘要
需要领导 Review 的关键判断点
```

然后停止，等待下一轮 `task.md`。