# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-C
Title: Expand canonical 黑骑士 Weapon record into a material graph
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-B
```

# 2. Previous execution status

N03-B 已确认 packed consumer。

```text
BORNBEAST_CONSUMER_CONFIRMED
```

Canonical bind：

```text
rez/RB001.REZ / Butes/BF005.LTC
  WeaponName    M4A1-黑骑士
  StandardName  M4A1_S_BornBeast
  PViewModel    PV-M4A1_S_BornBeast
  PViewSkin     PV-M4A1_S_BornBeast.dtx
```

N03-B 快照还有 QV 模型/皮肤和两条 RenderStyle 路径，但未做 payload SHA。
TGA / CFG 未出现在快照字段里。

# 3. Current goal

把这条 **已确认的 Weapon 记录** 扩成材质图。

回答：

```text
canonical Weapon record (all keys + raw block)
  -> every file-path field
  -> REZ exact path + payload identity
  -> TGA/CFG either direct field, RS/CFG evidence, or scoped negative
```

# 4. Required Work

只针对 packed `Butes/BF005.LTC`（`rez/RB001.REZ`）和该记录引用的资源。

1. 再 decode 该 packed LTC；抽出 `StandardName=M4A1_S_BornBeast` 且
   `PViewSkinFileName` 精确指向 `PV-M4A1_S_BornBeast.dtx` 的 Weapon 块。
   Canonical 显示名是 `M4A1-黑骑士`；同皮肤的其他 WeaponName 另列，不合并成 identity。
2. 对 canonical 块输出 **raw s-expression** 和 **全部解析字段**，不限于 N03-B 快照。
3. 在该 raw 块内对 inventory TGA/CFG 做 N03-A 同款 exact-token 搜索。
4. 对块内每个文件路径字段（含 QV LTB/DTX、两条 RS）做 N02-D-R1 exact path bind，
   再 bounded SHA256。Inventory 已有 SHA 的做 byte 比较；QV 若 local `data/**` 存在对应文件也可比，但不新扫整个 data。
5. bounded 读取两条 RS LTB（已知约 111/119 字节）和
   `WeaponShader/M4A1_S_BornBeast.CFG`，只做 string/hex 观测：
   是否包含 TGA/DTX/CFG 路径。不冻结 CFG shader semantics。

REZ index 只需要本轮引用到的 archive（至少 `RB001.REZ` / `RF016.REZ` / `rf017.rez` / `rf002.rez`），不要无目标扫全部 475 个。

输出：

```text
work/.../n03c_material_graph/
```

至少包含：

```text
canonical weapon dump (raw + all keys)
material graph report
path binding + SHA table
RS/CFG observation
confirmed relations
remaining ambiguity
confidence level
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把 StandardName == CFG stem 当成 shader bind proof；
- 不把变体 DTX 当成 inventory base_dtx；
- 不进入 P5 雷神 identity；
- 不进入 DLL/EXE/FXO reverse；
- 不扫描 `.dat` / 全量 `.ltc` / 全量 REZ extract；
- 不使用 filename similarity 作为 proof；
- 不冻结 CFG shader semantics；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. BUTE_MATERIAL_GRAPH_EXPANDED
   canonical record fully dumped; every file-path field REZ-bound;
   TGA/CFG either direct-field or scoped-negative on this record

B. CANDIDATE_ONLY
   dump/bind incomplete, or only weak RS/CFG string clues

C. REWORK_REQUIRED
   packed BF005 cannot be re-decoded or path bind is invalid
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
