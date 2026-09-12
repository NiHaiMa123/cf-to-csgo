# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-B
Title: Search REZ-resident table/config payloads for BornBeast consumer
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-A
```

# 2. Previous execution status

N03-A 已完成 BornBeast exact-token reverse lookup。

结论：

```text
CANDIDATE_ONLY
```

已确认：

```text
6/6 inventory assets
 -> runtime REZ exact path or basename+size
 -> SHA256 == P4 inventory
```

已确认的 scoped negative：

```text
loose rez/Butes/*.ltc + N02-A config-role files
do not name BornBeast inventory assets
```

# 3. Current goal

本轮目标：在 **REZ 内部** 的 table/config payload 里找 BornBeast consumer。

回答：

```text
BornBeast inventory token
 -> REZ-resident table/config payload
 -> record / field context
 -> consumer relation grade
```

# 4. Required Work

只读 N02-D-R1 的 path-aware REZ directory index（可重建，不 bulk extract）。

然后 **按扩展名** 选取 payload，对每个 unique `full_path` 做 bounded read + exact-token 搜索。

允许的扩展名：

```text
.cft
.lta
.txt
.ltc   仅当 full_path 以 BUTES/ 开头
```

优先但不是 proof 的目录信号：

```text
TABLE/ITEM.CFT
TABLE/MODELBUTE.CFT
TABLE/WEAPONPOINT.CFT
TABLE/*.CFT
```

Token 规则与 N03-A 相同：

```text
exact basename / stem / REZ logical path / SHA256 / MD5
bounded by non-identifier characters
no longer-name prefix match
```

`.ltc` 若 magic 为 CF wrapper，走已接受的 N02-B-R1 decode；否则 string-scan。
`.cft` / `.lta` / `.txt` 做 ASCII + UTF-16LE string-scan；若 ITEM.CFT 命中，再报告命中附近的字段/行上下文。

输出：

```text
work/.../n03b_rez_packed_config/
```

至少包含：

```text
packed config search report
selected payload inventory
token hits with context
resource graph update
confirmed relations
remaining ambiguity
confidence level
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把 WeaponShader `.cfg` 自身存在当成 consumer；
- 不扫描 `.dat` map blob / `.dtx` / `.bin` / `.ltb`；
- 不把全部 1747 个 REZ `.ltc` 当作本轮范围（只允许 `BUTES/`）；
- 不进入 DLL/EXE/FXO reverse；
- 不进行无目标全盘扫描；
- 不使用 filename similarity 作为 proof；
- 不冻结 CFG shader semantics；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. BORNBEAST_CONSUMER_CONFIRMED
   a REZ-resident table/config field binds a BornBeast inventory asset

B. CANDIDATE_ONLY
   hits or strong table candidates exist but the bind is not proven

C. REWORK_REQUIRED
   selection/decode path invalid
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
