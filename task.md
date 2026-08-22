# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-D-R2
Title: Accept path-aware REZ binding evidence and define material closure route
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-D-R1
```

# 2. Current execution status

N02-D-R1 已完成 basename-only lookup 的技术返工。

对应提交：

```text
f468e96f2d956ee82f69f8372c9c7c36423897ec
P4-M01-N02-D-R1: path-aware REZ binding closure for 60/60 M4A1 family
```

当前已具备：

```text
- REZ directory hierarchy preservation
- archive-relative full logical path
- exact path matching
- extensionless model .ltb restriction
- multiple archive ambiguity reporting
```

# 3. Current goal

本轮继续作为 Review gate，不扩大逆向范围。

需要确认：

```text
M4A1 runtime config
 -> exact REZ logical path
 -> runtime artifact
 -> material/resource binding boundary
```

明确哪些事实可以升级为 frozen evidence，哪些仍保持 OPEN_UNRESOLVED。

# 4. Required Review

检查：

```text
1. path normalization 是否具有可重复规则；
2. Models/ModelTextures virtual root strip 是否有边界；
3. extensionless model resolution 是否严格限制 .ltb；
4. exact path binding 与 unresolved 数量是否一致；
5. 是否存在 archive duplicate ambiguity；
6. 当前 binding 是否足够进入 material resource tracing。
```

# 5. Forbidden

- 不进入 P5 identity confirmation；
- 不宣布 P4-M01 PASS；
- 不把 M4A1 runtime binding 等同 BornBeast identity；
- 不扩大无目标 corpus scan；
- 不逆 DLL/EXE；
- 不逆 FXO shader；
- 不重新进行 LZX/DTX 语义推断；
- 不使用 filename similarity 作为 proof。

# 6. Expected Output

输出：

```text
work/.../n02d_r1_path_binding/review_report.md
```

报告必须包含：

```text
path binding verdict
frozen facts
remaining ambiguity
material binding gap
next highest-value investigation
```

# 7. Completion State

```text
A. ACCEPTED / COMPLETE
   exact runtime path binding frozen

B. PARTIAL
   unresolved paths remain open

C. REWORK_REQUIRED
   path evidence invalid
```

完成后返回：

```text
status
commit SHA
changed files
frozen facts
remaining blockers
next single highest-value target
```

完成后 STOP，等待 Planner/Reviewer。
