# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-D-R2
Title: Review path-aware REZ binding result and establish next material closure boundary
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-D-R1
```

# 2. Current review status

N02-D-R1 已完成上一轮 rework 目标：从 basename-only lookup 改为 path-aware REZ binding。

已确认修复方向：

```text
- REZ directory hierarchy preserved
- full logical path index introduced
- exact path matching replaces basename proof
- extensionless model path restricted to .ltb rule
- archive ambiguity explicitly reported
```

对应提交：

```text
f468e96f2d956ee82f69f8372c9c7c36423897ec
P4-M01-N02-D-R1: path-aware REZ binding closure for 60/60 M4A1 family
```

# 3. Current goal

本轮不是继续扩大搜索范围，而是 Review N02-D-R1 evidence，确认哪些事实可以冻结，并决定下一条最高价值 closure 路线。

回答：

```text
M4A1 runtime config
 -> exact REZ logical path
 -> runtime artifact
 -> material/resource binding
```

当前只允许提升到 evidence 支持的等级。

# 4. Required Review

检查：

```text
1. path normalization 是否有明确规则；
2. virtual root strip 是否只作用于已证明的 Models/ModelTextures；
3. extensionless ModelFileName/PViewModelFileName 是否只解析 .ltb；
4. multiple archive path 是否完整保留；
5. exact binding 数量与 unresolved 数量是否一致；
6. 是否仍存在 material binding closure 缺口。
```

# 5. Forbidden

- 不进入 P5 identity confirmation；
- 不宣布 P4-M01 PASS；
- 不把 runtime M4A1 binding 等同 BornBeast identity；
- 不继续扩大无目标 corpus scan；
- 不逆 DLL/EXE；
- 不逆 FXO shader；
- 不重新进行 LZX/DTX 语义推断；
- 不使用 filename similarity 作为 proof。

# 6. Expected Output

如果 evidence 足够：

```text
work/.../n02d_r1_path_binding/review_report.md
```

记录：

```text
exact path binding result
remaining ambiguity
material binding gap
next recommended investigation
```

# 7. Completion State

可能结果：

```text
A. N02-D-R1 ACCEPTED / COMPLETE
   -> exact runtime path binding frozen

B. N02-D-R1 PARTIAL
   -> keep unresolved paths open

C. REWORK_REQUIRED
   -> only if path evidence itself fails review
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