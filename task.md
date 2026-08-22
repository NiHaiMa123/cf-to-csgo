# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-E-R1
Title: LTB Material Resource Binding Evidence Recovery
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N02-D-R2
```

# 2. Current execution status

N02-D-R1 已完成 REZ basename-only binding 修复，当前边界已明确：

```text
M4A1 runtime config
 -> exact REZ logical path
 -> runtime artifact
```

该链路可以进入下一阶段，但不能直接推出：

```text
runtime M4A1 = BornBeast identity
runtime path = material closure
```

# 3. Current goal

本轮目标：建立 LTB 内部资源关系证据。

回答：

```text
PV-M4A1.LTB
 -> piece/model structure
 -> texture/material reference
 -> DTX/TGA resource path
```

需要确认：

```text
1. LTB 是否包含 material/texture slot relation；
2. piece index 与 texture reference 是否存在确定关系；
3. runtime resource graph 能否从 model 延伸到材质资源；
4. 哪些关系只能保持 OPEN_UNRESOLVED。
```

# 4. Required Work

优先使用：

```text
existing LTB parser
Jupiter reference implementation
current CF runtime LTB samples
```

输出 evidence：

```text
work/.../material_binding/
```

至少包含：

```text
ltb structure report
piece/material relation report
resource graph candidate
confidence level
```

# 5. Forbidden

- 不进入 P5 identity confirmation；
- 不宣布 P4-M01 PASS；
- 不把 M4A1 runtime binding 等同 BornBeast identity；
- 不逆 DLL/EXE；
- 不逆 FXO shader；
- 不继续无目标全盘扫描；
- 不把 filename similarity 当 proof；
- 不冻结 CFG shader semantics。

# 6. Completion State

```text
A. MATERIAL_BINDING_CONFIRMED
   LTB -> material -> texture relation established

B. MATERIAL_BINDING_PARTIAL
   only part of graph confirmed

C. REWORK_REQUIRED
   parser/evidence path invalid
```

完成后返回：

```text
status
commit SHA
changed files
confirmed relations
remaining blockers
next highest-value target
```

完成后 STOP，等待 Planner/Reviewer。
