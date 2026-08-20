# P4_RV04_TEST_SPECS.md — Chat/Sol → Luna 独立反例执行协议

> Owner / Test Designer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> Final Judge: **Chat/Sol**
>
> 当前基线 Review HEAD：`10aa99b770e575300ca3c28324ef3de3d5b70c6b`
>
> 本文件只定义 RV-04 的本地机械执行。Luna 不得修改测试目标、expected gate、PASS/FAIL/INVALID 规则，也不得自行给 P4 最终 Review 结论。

执行前必须先读取 `AGENTS.md` 和 `CODEX_TASKS.md`，并安全拉取最新 `master`。如果拉取后 HEAD 已不是上面的基线，**停止并报告 `BLOCKED_HEAD_CHANGED`**，不要擅自把测试套到新代码上。

---

## 0. 总体规则

所有 mutation 必须在 fresh 临时目录中执行，不修改：

- 当前真实 manifest；
- 当前真实 build / package / staging；
- Steam / MIGI addon；
- `data/**` 原始资产；
- 生产 Gate 实现。

允许复用 `scripts/weapon_port/run_p4_t07.py` 已有的 shadow-copy / mutation helper，但 **禁止直接运行整个 T07 main 后把旧的 17/17 当成 RV-04**。RV-04 必须单独选择并执行下列 4 个高风险 case，生成新的独立报告。

统一结果语义：

- `PASS`：mutation 本身有效，且被预定的目标 Gate 拒绝，退出非零；
- `FAIL`：mutation 被接受，或目标 Gate 未拒绝它；
- `INVALID`：测试因 unrelated corruption、环境错误、导入错误等原因提前失败，无法证明目标 Gate；
- 任一 case 为 `FAIL` 或 `INVALID`，RV-04 不能通过，交回 Chat/Sol 判断下一步。

---

## 1. RV04-01 — 输出根路径 / 递归删除安全

**目的**：证明恶意/错误 manifest 不能把 P4 destructive output root 指到过宽的 `work/` 根目录。

**Baseline**：当前 `prototype_01_manifest.json`。

**Mutation**：仅在临时 manifest 中：

```python
manifest["outputs"]["build_root"] = "work"
```

**必须保持**：

- 其他 manifest 字段不变；
- 不修改真实仓库 manifest；
- 不调用任何真实 destructive cleanup；
- `data/**` 不动。

**执行方法**：调用 T07 helper：

```python
run_contract_mutation(
    "rv04_output_root_guard",
    lambda m: m["outputs"].update(build_root="work"),
)
```

**Expected Gate**：`manifest_contract`。

**PASS**：

- contract 返回拒绝 / 非零；
- error 明确涉及 output/build root containment；
- 真实 `work/` 和 `data/` 未被删除/改写。

**FAIL**：manifest 被接受。

**INVALID**：因为 Python/import/tempdir 等 unrelated error 未实际运行 contract。

---

## 2. RV04-02 — Sequence 数量不变但语义错误

**目的**：证明 Gate 不是只检查 9 个 sequence 的数量，而会检查名称语义。

**Baseline**：当前 frozen run 的 `compiled_decompiled/reference_report.json`。

**Mutation**：保持 sequence 数量完全不变，仅把第一条 sequence 名改成 `mutated_sequence`。

**必须保持**：

- sequence count 不变；
- 其余 sequence 不改；
- bones / attachment / material 不改；
- mutation 只发生在 fresh shadow copy。

**执行方法**：

```python
run_shadow_mutation(
    "rv04_sequence_same_count",
    "sequence_names_and_count",
    mutate_roundtrip("sequence"),
)
```

**Expected Gate**：`sequence_names_and_count`。

**PASS**：exit code 非零且 `sequence_names_and_count` 出现在 failed gates。

**FAIL**：mutation 被 validator 接受，或 validator 总 PASS。

**INVALID**：在 sequence gate 之前因 unrelated 文件损坏/环境问题失败。

---

## 3. RV04-03 — Mesh / Bone mapping 语义交换

**目的**：证明数量、group、triangle 都没变时，Parent / Clip 的 mapping 被交换仍会被拒绝。

**Mutation**：交换 manifest 前两个 mapping 的：

- `bone_index`；
- `bone`。

不改变：

- group 名；
- mapping 数量；
- triangle 数；
- OBJ；
- SMD baseline；
- 其他字段。

**执行方法**：

```python
run_shadow_mutation(
    "rv04_mapping_parent_clip_swap",
    "smd_manifest_bone_corners",
    mutate_mapping,
)
```

**Expected Gate**：`smd_manifest_bone_corners`。

**PASS**：exit code 非零且目标 Gate 明确失败。

**FAIL**：mapping 交换后仍被接受。

**INVALID**：因为不相关 parser/file error 导致未到达目标 mapping Gate。

---

## 4. RV04-04 — Material closure 缺失 VTF

**目的**：证明模型、sequence、bones 均正常时，VMT/VTF 闭包缺一个关键 VTF 仍会被拒绝。

**Mutation**：只在 fresh shadow addon 删除：

```text
materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vtf
```

**必须保持**：

- VMT 保留；
- model binaries 保留；
- manifest provenance flags 保持 Prototype；
- 真实 package/staging/addon 不动。

**执行方法**：

```python
run_shadow_mutation(
    "rv04_missing_vtf_material_closure",
    "material_closure",
    mutate_material,
)
```

**Expected Gate**：`material_closure`。

**PASS**：exit code 非零且 `material_closure` 明确失败。

**FAIL**：缺失 VTF 后 validator 仍 PASS。

**INVALID**：material validator 本身未能正常运行，或 mutation 发生在错误位置。

---

## 5. Luna 必须执行的统一 runner

不要修改仓库中的 `run_p4_t07.py`。在仓库根目录创建一个 **临时 Python 文件**（放 `%TEMP%`，不要 git add），内容等价于：

```python
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "scripts"))

from weapon_port import run_p4_t07 as t07

EXPECTED_HEAD = "10aa99b770e575300ca3c28324ef3de3d5b70c6b"
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
if head != EXPECTED_HEAD:
    print(json.dumps({"status": "BLOCKED_HEAD_CHANGED", "expected": EXPECTED_HEAD, "actual": head}, ensure_ascii=False, indent=2))
    raise SystemExit(2)

baseline_build = t07.read_json(t07.P4_WORK / "build_report.json")
baseline_run = baseline_build.get("upstream", {}).get("run_id")

cases = [
    t07.run_contract_mutation(
        "rv04_output_root_guard",
        lambda m: m["outputs"].update(build_root="work"),
    ),
    t07.run_shadow_mutation(
        "rv04_sequence_same_count",
        "sequence_names_and_count",
        t07.mutate_roundtrip("sequence"),
    ),
    t07.run_shadow_mutation(
        "rv04_mapping_parent_clip_swap",
        "smd_manifest_bone_corners",
        t07.mutate_mapping,
    ),
    t07.run_shadow_mutation(
        "rv04_missing_vtf_material_closure",
        "material_closure",
        t07.mutate_material,
    ),
]

report = {
    "schema": "cf2.p4.chat-rv04-independent.v1",
    "review_id": "RV-04",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "git_head": head,
    "baseline": {
        "manifest": str(t07.MANIFEST_PATH.relative_to(ROOT)),
        "manifest_sha256": t07.sha256(t07.MANIFEST_PATH),
        "build_run_id": baseline_run,
        "build_report_sha256": t07.sha256(t07.P4_WORK / "build_report.json"),
    },
    "cases": cases,
    "case_count": len(cases),
    "passed_cases": sum(1 for case in cases if case.get("passed") is True),
    "pass": all(case.get("passed") is True for case in cases),
    "isolation": "Each selected mutation executed through T07 helpers in a new tempfile/shadow copy. No active build, Steam/MIGI addon, or data asset mutated.",
    "final_judge": "CHAT_SOL_PENDING",
}

out = t07.P4_WORK / "rv04_chat_review_report.json"
t07.write_json(out, report)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["pass"] else 1)
```

执行完成后：

1. 保留命令行完整 stdout/stderr 到：
   `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log`
2. 保留 runner 退出码。
3. 确认生成：
   `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`
4. 检查真实 `data/`、真实 active addon、当前 build/package/staging 没有被修改。
5. **只精确提交以下新的 Review 证据文件**：
   - `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`
   - `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log`
6. 不修改 `plan.md`、`P4_STATUS.md`、`CHAT_REVIEW.md`，不自行写 RV-04 PASS，不自行冻结 P4。
7. push 到 `master` 后停止，并把 commit SHA 返回给用户；等待 Chat/Sol 重新读取证据并最终判定。

---

## 6. Chat/Sol 后续判定

Luna push 后，Chat/Sol 必须重新读取最新 HEAD 和两份 RV-04 证据。

只有 4 个 case 都实际有效且 target Gate 精确命中时：

```text
RV-04 = PASS
```

否则按 case 判为 `FAIL` 或 `INVALID`，不能用 T07 历史 17/17 抵消。

RV-04 通过后，再完成 RV-06 最终结论；在 RV-06 前不得把 P4 写成 `PASS / FROZEN`。
