# task.md — 当前执行任务

> 本文件只描述 **当前下一步**：执行 Agent 现在应该解决什么、为什么、可以尝试哪些实现路径、需要返回什么 evidence。  
> 长期 pipeline 与冻结事实看 [`plan.md`](plan.md)。Git 操作看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 当前任务

```text
Task ID: P4-M01-N02
Title: Runtime Artifact Acquisition & Static Triage
State: ACTIVE / RUNTIME_ARTIFACT_ACQUISITION
Parent: P4-M01 Native Material Recovery
```

目标：**主动找到能解除 N01 `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` 的新输入，并把最有价值的 runtime/client/shader consumer 候选交回 Review。**

当前不是继续分析旧 `data/**`。旧 corpus 的 basename/config/CFG curve-fitting 搜索已经冻结。

---

# 2. Executor 需要解决的问题

尽可能回答：

1. 本机是否存在完整 CF 安装/runtime root？
2. 哪些 EXE/DLL/archive/shader 文件最可能包含 model/material/resource consumer？
3. 哪些候选直接或间接出现 `LTB / DTX / CFG / ModelTextures / WeaponShader / RenderStyle / PieceIndex` 等证据？
4. 是否能找到值得继续追的 static xref / loader / resolver / shader consumer？
5. 如果当前环境确实没有足够输入，缺口能否被明确限定，而不是只说“没找到”？

---

# 3. 实现原则

这不是固定 A→B→C 状态机。Executor 应根据已发现 evidence 动态选择**信息增益最高**的下一动作。

优先原则：

```text
direct consumer evidence
> string/import/resource/xref relation
> engine/render/resource module evidence
> archive/shader structural evidence
> filename/path inference
```

当某条路线出现强线索时，允许直接深入，不需要机械跑完其他路线。

每次扩展搜索最好能说明：

```text
current evidence
hypothesis
why this action is useful
result
how result changes next action
```

---

# 4. 可尝试实现路径 Strategy Pool

下面是**可选策略池，不是固定顺序**。Executor 可组合、跳过、扩展；也允许提出其他有明确 rationale 的 static/read-only 方法。

## 4.1 找安装/runtime root

可尝试：

- repo/config/report 中已有路径线索；
- Windows uninstall registry / App Paths；
- Desktop / Start Menu `.lnk` target；
- WeGame/launcher manifest/config；
- 常见 Tencent/WeGame/CrossFire 安装目录；
- 枚举 fixed drives 后做有界目录名搜索；
- 如果 CF/WeGame 本来已经运行，只读查询 executable / loaded module path。

目标不是启动游戏，只是定位真实 client/runtime 文件。

## 4.2 Runtime inventory

重点对象：

```text
*.exe
*.dll
*.rez
*.pak
*.pck
*.bin
shader/effect/renderstyle related files
*.fx *.fxc *.cso *.shader *.shd
```

避免再次把整套音频/贴图当新搜索目标。

每个候选尽量记录：

```text
path alias / relative path
size
sha256
file type / magic
version/product/description
signer if available
candidate role
why candidate
```

## 4.3 PE/module 静态 triage

可使用本机已有工具，例如：

```text
PowerShell Get-Item / Get-FileHash / Get-AuthenticodeSignature
dumpbin
llvm-readobj / llvm-objdump
objdump
Python pefile
Ghidra / IDA / Binary Ninja / radare2 / rizin
```

优先检查：

```text
imports / exports
sections
resources/version metadata
ASCII + UTF-16 strings
```

高价值 needles 包括但不限于：

```text
WeaponShader
ModelTextures
AlphaMap
NormalMap
SpecularMap
PieceIndex
RenderStyle
PLAYERVIEW
.LTB
.DTX
.CFG
texture
material
resource
shader
```

## 4.4 String → Xref → Consumer

如果任何模块出现高价值 string/resource evidence，优先追：

```text
string/resource
-> xref
-> containing function
-> caller/callee
-> file/archive loader
-> resource/material resolver
-> piece/material key/index use
```

重点问题：

```text
谁打开 LTB / DTX / CFG？
谁构造 ModelTextures / WeaponShader 路径？
weapon piece/short-id/index 如何进入 resolver？
CFG bytes 被按什么长度/类型读取并传给 shader？
```

一旦出现可信 consumer candidate，应停止无边界扩张并准备 handoff。

## 4.5 Imports / Module relation

如果主 EXE 没有直接 strings：

- 查看 `CreateFile/ReadFile/fopen` 等 loader API；
- 查看 Direct3D shader/texture API；
- 根据 imports 找实际 engine/render/resource DLL；
- 根据 ProductName/FileDescription/模块关系缩小范围；
- 优先追被 client 加载且实际承担资源/渲染职责的 DLL。

## 4.6 Archive / package route

如果 consumer 可能不直接散落在安装目录：

- 识别 `.rez/.pak/.pck/.bin` magic/TOC；
- 优先复用仓库已有 CFRezManager 只读能力；
- 查 embedded PE / shader / renderstyle / config；
- 提取到 local-only 临时目录后再做 hash/static triage。

Raw runtime/archive 不提交 Git。

## 4.7 Shader route

如果找到 shader/effect/renderstyle package，可尝试：

- DXBC/CTAB/constant table/resource name dump；
- shader parameter / sampler / constant register 名称；
- normal/specular/alpha/emissive 等参数关系；
- CFG sample/count 是否和 shader constants/LUT/resource slots 有结构对应。

即使还没闭合 piece binding，能闭合 CFG consumer 的一部分也有价值。

## 4.8 Launcher / manifest route

如果当前目录只有 launcher 或 client 被隐藏/按需下载：

- 检查 patch/version/download/module manifest；
- 定位真实 game executable / engine modules / runtime package；
- 不读取账号凭证，不触发 patch/update，不执行未知客户端。

## 4.9 Protected / packed client

如果主 EXE 明显 packed/protected：

- 记录 pack/protection evidence；
- 优先转向未保护 DLL、shader、archive、旧版本/备份客户端；
- 可以比较不同版本 artifact inventory 来判断 consumer 从哪个模块迁移。

本任务禁止进程注入、anti-cheat bypass、运行时内存 dump 或执行未知脱壳器。

## 4.10 其他路线

Executor 可以采用 plan 未列出的实现，只要满足：

```text
static/read-only
有明确 hypothesis/rationale
能产生可审计 evidence
不重复已冻结旧 corpus 的低价值搜索
不突破用户数据/Git安全边界
```

---

# 5. 建议输出

推荐新增一个可重复脚本，而不是只做一次性命令：

```text
scripts/material_recovery/n02_runtime_artifact_acquire.py
```

建议 evidence 目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/
```

可输出：

```text
artifact_inventory.json
string_hits.json
candidate_rank.json
static_xref_report.json        if applicable
acquisition_report.md
```

不要求所有文件都必须存在；输出应与实际采用的方法匹配。

Raw EXE/DLL/REZ/PAK/PCK/shader package 留本机，不提交。

---

# 6. Handoff / Completion

## A. 找到可信 consumer candidate

返回：

```text
RUNTIME_CONSUMER_CANDIDATE_FOUND
```

至少给出：

```text
artifact identity/path alias
sha256 + size
string/import/resource evidence
xref/function/RVA or equivalent static trace
为什么它值得继续追
当前仍有哪些 alternative explanations
推荐下一条 deeper tracing point
```

然后停止扩大搜索，commit/push scoped code + evidence，交回领导/Review Agent。

## B. 找到 runtime artifact，但需要更深静态逆向

返回：

```text
RUNTIME_ARTIFACT_FOUND_NEEDS_DEEPER_STATIC_ANALYSIS
```

必须明确列出 top candidate(s) 和具体下一追踪点，例如 function/RVA/string/xref/module relation；不能只写“需要逆向”。

## C. 本机没有找到足够输入

只有形成 bounded negative 后才返回：

```text
NO_RUNTIME_ARTIFACT_FOUND_LOCALLY
```

报告至少说明：

```text
searched roots + discovery method
candidate counts/types
PE/archive/shader coverage
needles/methods used
important negatives
excluded areas + reason
```

并明确指出下一次需要用户提供的是哪类输入，例如：

```text
另一版本完整 CF 客户端
旧客户端备份
完整 runtime/REZ package
明确的 engine/render/resource module
可信 documented/reverse-engineered binding contract
```

---

# 7. 禁止事项

- 不重复旧 `data/**` 的 basename/config/CFG curve-fitting 扫描；
- 不把文件名/目录邻近当 runtime binding proof；
- 不执行未知 CF client/runtime binary；
- 不做进程注入、anti-cheat bypass、runtime memory dump；
- 不上传 raw client/runtime/archive/shader binary；
- 不自行宣布 `P4-M01 = NATIVE_MATERIAL_RECOVERED`；
- 不恢复 P5-T02；
- 不修改 `plan.md` 的冻结事实，除非任务明确要求更新长期 pipeline/冻结结论。

---

# 8. 角色边界

执行 Agent：读取 `README.md -> AGENTS.md -> plan.md -> task.md`，执行本文件，产出代码/evidence，不自行重规划整个项目。

领导/规划/Review Agent：读取最新代码/evidence，对照 `plan.md` 的长期 Gate Review 结果，然后**重写 `task.md` 为下一步**；只有长期 pipeline、Gate 或冻结事实变化时才修改 `plan.md`。
