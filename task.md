# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-E-R2
Title: Resolve partial material binding through bounded native resource verification
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N02-E-R1
```

# 2. Current execution status

N02-E-R1 已完成 LTB material binding boundary analysis。

结论：

```text
MATERIAL_BINDING_PARTIAL
```

已确认：

```text
PV-M4A1.LTB
 -> piece/model structure evidence
 -> material relation boundary
```

但未确认：

```text
piece
 -> exact texture resource
 -> native DTX/TGA
```

# 3. Current goal

本轮目标：补齐 native resource closure。

回答：

```text
LTB piece/material candidate
 -> runtime resource payload
 -> SHA verified asset
 -> native material graph
```

# 4. Required Work

优先执行 bounded verification：

```text
REZ directory evidence
 -> locate matching payload
 -> read bounded bytes
 -> SHA256
 -> compare local CF material assets
```

输出：

```text
work/.../material_binding/
```

至少包含：

```text
payload verification report
resource graph update
confirmed relations
remaining ambiguity
confidence level
```

# 5. Forbidden

- 不进入 P5 identity confirmation；
- 不宣布 P4-M01 PASS；
- 不把 runtime M4A1 binding 等同 BornBeast identity；
- 不逆 DLL/EXE；
- 不逆 FXO shader；
- 不进行无目标全盘扫描；
- 不冻结 CFG shader semantics；
- 不使用 filename similarity 作为 proof。

# 6. Completion State

```text
A. NATIVE_RESOURCE_CONFIRMED
   payload/material relation established

B. MATERIAL_BINDING_PARTIAL
   evidence improved but closure incomplete

C. REWORK_REQUIRED
   verification path invalid
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
