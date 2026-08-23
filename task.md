# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-A
Title: BornBeast consumer path discovery after runtime payload separation
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N02-E-R2
```

# 2. Previous execution status

N02-E-R2 已完成 bounded REZ payload SHA256 verification。

结论：

```text
MATERIAL_BINDING_PARTIAL
```

已确认：

```text
N02-D-R1 runtime path binding
 -> bounded payload extraction
 -> SHA256 identity evidence
```

结果：

```text
24 unique payloads verified
0 SHA256 matches BornBeast P4 baseline inventory
```

因此冻结当前范围内结论：

```text
bf005 M4A1 runtime family
!=
BornBeast native asset
```

该结论仅针对当前 bf005 consumer scope，不代表 BornBeast runtime entry 不存在。

# 3. Current goal

本轮目标：寻找 BornBeast native asset 的真实 consumer path。

回答：

```text
BornBeast inventory asset
 -> runtime/config consumer
 -> REZ/resource path
 -> payload identity
```

# 4. Required Work

优先执行 bounded reverse lookup：

```text
BornBeast native inventory
 -> reverse filename/hash/path references
 -> LTC/Bute/config candidates
 -> runtime resource relation
```

输出：

```text
work/.../bornbeast_consumer/
```

至少包含：

```text
consumer candidate report
resource graph update
confirmed relations
remaining ambiguity
confidence level
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把普通 M4A1 runtime binding 等同 BornBeast identity；
- 不进入 DLL/EXE/FXO reverse；
- 不进行无目标全盘扫描；
- 不使用 filename similarity 作为 proof；
- 不冻结 CFG shader semantics；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. BORNBEAST_CONSUMER_CONFIRMED
   runtime consumer path established

B. CANDIDATE_ONLY
   candidates found but identity not proven

C. REWORK_REQUIRED
   search boundary invalid
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
