# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-E
Title: crossfirebase.dll static + optional in-memory module dump
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N04-D
```

# 2. Previous execution status

N04-D：`x64/crossfire.exe` 是 stub，唯一导入 `crossfireBase.dll`。WeaponShader 岛有 `.cfg` 碎片，0 xref。用户授权 `.tvm0` 静态 **以及** 若进程已在跑则 dump 已加载模块。

# 3. Current goal

1. 磁盘静态：`x64/crossfirebase.dll`（及 `x64/crossfire_x64base.dll` 对照）按节扫明文/XOR，不跑脱壳器。
2. 若本机 **已经** 有 CF 进程：只读 `ReadProcessMemory` dump `crossfirebase.dll` / `crossfire.exe` / `CShell_x64.dll` 映像，再扫 `WeaponShader\%s` / `.CFG`。
3. 进程不在就不启动游戏。

# 4. Required Work

只读：

```text
D:\Program Files\CF(2)\x64\crossfirebase.dll
D:\Program Files\CF(2)\x64\crossfire_x64base.dll
```

Dump 若发生：写到 `work/.../n04e_vm_dump/dumps/`（**禁止 git add dump**）。证据只提交字符串命中表。

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不启动 CF；
- 不注入、不补丁、不写驱动；
- 不分析/对抗 ACE 模块（`ace-*.dll`、`ACE-PBC-Game.dll`）；
- 不跑网上脱壳 EXE；
- 不提交 .exe/.dll/.dmp。

# 6. Completion State

```text
A. DUMP_FORMAT_HIT
   内存映像里出现 WeaponShader\%s.CFG 或等价构造串

B. STATIC_ONLY_NO_PROCESS
   磁盘 .tvm0 仍无有用明文；进程未运行，未 dump

C. DUMP_ACCESS_DENIED
   进程在，OpenProcess/RPM 被拒绝（多半 ACE）

D. REWORK_REQUIRED
   读不到 listed DLL
```

完成后 STOP。
