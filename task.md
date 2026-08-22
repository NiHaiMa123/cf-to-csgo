# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N02-E
Title: M4A1 Runtime Artifact Payload SHA Verification
State: ACTIVE
Parent: P4-M01-N02 Runtime Bute Semantic Recovery
Depends on: P4-M01-N02-D ACCEPTED / COMPLETE
```

# 2. Previous milestone accepted

N02-D 已确认：

```text
M4A1 family runtime binding paths = 60
REZ entries checked = 60
DIRECT_RUNTIME_ARTIFACT = 60
ARCHIVE_INDEX_ONLY = 0
NOT_FOUND_IN_SCOPED_RUNTIME = 0
status = M4A1_RUNTIME_ARTIFACT_CONFIRMED
```

已冻结：

```text
bf005.ltc M4A1 records reference real CF runtime assets
runtime Bute binding -> REZ artifact relation confirmed
BornBeast identity remains open
```

# 3. Current Goal

在不进行完整 REZ 解包的情况下，读取已确认 runtime artifact 的 payload，建立 SHA 级证据。

目标：

```text
M4A1 runtime artifact
        -> REZ entry metadata
        -> bounded payload read
        -> SHA256
        -> compare with existing evidence
```

# 4. Scope

只使用：

```text
D:\Program Files\CF(2)
N02-D REZ index outputs
N02-C weapon bindings
existing P4 manifests
```

允许：

```text
read exact entry offset + size
hash payload
compare known SHA
```

禁止：

```text
full REZ extraction
DLL/EXE reverse
FXO shader reverse
CF client execution
memory dump
```

# 5. Required Analysis

## 5.1 Payload verification

优先验证：

```text
PV-M4A1 / m4a1 LTB
M4A1 related DTX
RenderStyle resources
```

记录：

```text
runtime path
REZ archive
offset
size
sha256
existing relation
```

## 5.2 BornBeast relation

继续保持证据等级：

```text
runtime M4A1 artifact
!=
BornBeast proof
```

只有 payload hash 与已有 BornBeast source evidence 建立明确关系时，才能提升结论。

# 6. Expected Output

输出目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02e_payload_hash/
```

至少：

```text
payload_hash_verification.json
payload_hash_report.md
```

# 7. Completion States

## A. Payload relation confirmed

```text
M4A1_RUNTIME_PAYLOAD_VERIFIED
```

## B. Runtime artifact confirmed but payload relation open

```text
M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN
```

完成后 STOP，等待 Review。

# 8. Forbidden

- 不宣布 P4-M01 PASS；
- 不进入 P5 identity confirmation；
- 不用文件名相似替代 hash 证据；
- 不修改长期 pipeline。

# 9. Handoff

返回：

```text
status
commit SHA
changed files
payload hash result
BornBeast relation result
next highest-value investigation target
```
