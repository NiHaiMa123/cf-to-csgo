# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N04-F
Title: In-memory dump of running x64/crossfire.exe modules
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N04-E
```

# 2. Previous execution status

N04-E = STATIC_ONLY_NO_PROCESS。用户随后开了 CF 并要求 dump。

# 3. Current goal

对已运行的 `crossfire.exe` 只读 dump `crossfirebase.dll` / `CShell_x64.dll` / `crossfire.exe` 映像，扫 `WeaponShader\%s.CFG`。

# 4. Required Work

- 确认 PID 与映像路径。
- `OpenProcess(PROCESS_VM_READ)` + `ReadProcessMemory` 只针对游戏模块。
- 失败则记录 Win32 last_error，不升级权限、不对抗 ACE。
- dump 文件不进 Git。

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不注入、不补丁、不驱动、不 NtRead 绕过；
- 不打开 ACE 模块；
- 不提交 .dmp/.dll。

# 6. Completion State

```text
A. DUMP_FORMAT_HIT
B. DUMP_NO_FORMAT
C. DUMP_ACCESS_DENIED
D. REWORK_REQUIRED
```

完成后 STOP。
