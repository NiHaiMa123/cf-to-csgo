# P4_RV04_TEST_SPECS.md — Chat/Sol → Local Executor 独立反例执行协议

> Test Designer / Final Judge：**Chat/Sol**  
> Executor：**Any user-selected Local Executor Agent**  
> Implementation baseline：`10aa99b770e575300ca3c28324ef3de3d5b70c6b`

> 本文件是历史 RV-04 Test Spec。Executor 名称不构成当前或未来 Agent 绑定；实际历史执行者如在 evidence 中记录，保留其 provenance。

本文件只定义 P4 RV-04 的本地机械执行。Local Executor 不得修改 test target、expected gate、PASS/FAIL/INVALID 规则，不得自行给 RV-04 或 P4 最终结论。

## 1. 执行前基线保护

先读取 `AGENTS.md`、`CODEX_TASKS.md`，安全拉取最新 `master`。

Review 文档提交会让 HEAD 前移，所以**不要要求 HEAD 等于 implementation baseline**。必须验证自 `10aa99b...` 之后下列 P4 核心实现没有变化：

```powershell
git diff --exit-code 10aa99b770e575300ca3c28324ef3de3d5b70c6b -- `
  scripts/weapon_port/pipeline.py `
  scripts/weapon_port/validate_manifest_contract.py `
  scripts/weapon_port/validate_p4_t05.py `
  scripts/weapon_port/run_p4_t07.py `
  assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
```

- exit `0`：允许继续。
- 非 `0`：停止，返回 `BLOCKED_IMPLEMENTATION_CHANGED`，不要执行旧 Test Spec。

所有 mutation 必须在 fresh 临时目录执行，不修改真实 manifest、build/package/staging、Steam/MIGI addon 或 `data/**`。

允许复用 `scripts/weapon_port/run_p4_t07.py` 的 shadow-copy helper，但**禁止直接重跑整个 T07 main 后把历史 17/17 当成 RV-04**。

统一判定：

- `PASS`：mutation 有效，且被预定 target Gate 拒绝；
- `FAIL`：mutation 被接受或 target Gate 未拒绝；
- `INVALID`：unrelated error 导致未实际测试 target Gate。

任一 case 为 `FAIL` / `INVALID`，RV-04 均不能通过。

## 2. 四个固定 case

### RV04-01 — output root containment

Mutation，仅临时 manifest：

```python
manifest["outputs"]["build_root"] = "work"
```

执行：

```python
t07.run_contract_mutation(
    "rv04_output_root_guard",
    lambda m: m["outputs"].update(build_root="work"),
)
```

Expected stage：`manifest_contract`。

PASS：contract 非零拒绝，错误明确涉及 output/build root containment；真实 `work/`、`data/` 无改动。

### RV04-02 — sequence same count, wrong semantics

只把 shadow `compiled_decompiled/reference_report.json` 第一条 sequence 名改成 `mutated_sequence`，sequence count 保持不变。

执行：

```python
t07.run_shadow_mutation(
    "rv04_sequence_same_count",
    "sequence_names_and_count",
    t07.mutate_roundtrip("sequence"),
)
```

Expected Gate：`sequence_names_and_count`。

PASS：exit 非零且 failed gates 精确包含该 Gate。

### RV04-03 — mesh/bone mapping swap

只交换 manifest 前两个 mapping 的 `bone_index` 与 `bone`；group、mapping count、triangle count、OBJ 都不变。

执行：

```python
t07.run_shadow_mutation(
    "rv04_mapping_parent_clip_swap",
    "smd_manifest_bone_corners",
    t07.mutate_mapping,
)
```

Expected Gate：`smd_manifest_bone_corners`。

PASS：exit 非零且 failed gates 精确包含该 Gate。

### RV04-04 — material closure missing VTF

只在 fresh shadow addon 删除：

```text
materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vtf
```

执行：

```python
t07.run_shadow_mutation(
    "rv04_missing_vtf_material_closure",
    "material_closure",
    t07.mutate_material,
)
```

Expected Gate：`material_closure`。

PASS：exit 非零且 failed gates 精确包含该 Gate。

## 3. Local Executor 统一 runner

在 `%TEMP%` 创建临时 Python 文件，不 git add。仓库根目录执行。脚本内容：

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

BASE = "10aa99b770e575300ca3c28324ef3de3d5b70c6b"
CRITICAL = [
    "scripts/weapon_port/pipeline.py",
    "scripts/weapon_port/validate_manifest_contract.py",
    "scripts/weapon_port/validate_p4_t05.py",
    "scripts/weapon_port/run_p4_t07.py",
    "assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json",
]

head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
diff = subprocess.run(["git", "diff", "--exit-code", BASE, "--", *CRITICAL], cwd=ROOT, text=True, capture_output=True)
if diff.returncode != 0:
    print(json.dumps({"status": "BLOCKED_IMPLEMENTATION_CHANGED", "base": BASE, "head": head, "diff": diff.stdout + diff.stderr}, ensure_ascii=False, indent=2))
    raise SystemExit(2)

baseline_build = t07.read_json(t07.P4_WORK / "build_report.json")

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
    "implementation_base": BASE,
    "git_head": head,
    "critical_diff_from_base": False,
    "baseline": {
        "manifest": str(t07.MANIFEST_PATH.relative_to(ROOT)),
        "manifest_sha256": t07.sha256(t07.MANIFEST_PATH),
        "build_run_id": baseline_build.get("upstream", {}).get("run_id"),
        "build_report_sha256": t07.sha256(t07.P4_WORK / "build_report.json"),
    },
    "cases": cases,
    "case_count": len(cases),
    "passed_cases": sum(case.get("passed") is True for case in cases),
    "pass": all(case.get("passed") is True for case in cases),
    "isolation": "Each case used a fresh tempfile/shadow helper; active build, data and MIGI were not mutation targets.",
    "final_judge": "CHAT_SOL_PENDING",
}

out = t07.P4_WORK / "rv04_chat_review_report.json"
t07.write_json(out, report)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["pass"] else 1)
```

运行时把完整 stdout/stderr 保存为：

```text
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log
```

生成报告：

```text
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json
```

Local Executor 执行后只允许精确提交这两个新证据文件：

```text
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log
```

不要修改 `plan.md`、`P4_STATUS.md`、`CHAT_REVIEW.md`、生产代码或 manifest；不要自行写 `RV-04 PASS` / `P4 FROZEN`。

push 到 `master` 后停止，把 commit SHA 返回给用户，等待 Chat/Sol 重读并判定。

## 4. Chat/Sol 后续

只有 4 个 case 都实际执行、mutation 有效、target Gate 精确命中，Chat/Sol 才可判：

```text
RV-04 = PASS
```

否则按 case 判 `FAIL` / `INVALID`。不能用 T07 历史 17/17 抵消。

RV-04 通过后才进入 RV-06 最终结论；RV-06 前不得把 P4 写成 `PASS / FROZEN`。
