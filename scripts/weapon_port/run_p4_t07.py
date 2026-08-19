"""Execute the P4-T07 negative-gate and reproducibility checks.

The mutation checks are deliberately run against a temporary shadow copy of
the P4 project.  No mutation is ever applied to the active build, work,
Steam, or MIGI directories.  The two positive runs are real pipeline builds;
only their run-local artifacts are compared.
"""

from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from weapon_port import pipeline  # noqa: E402
from weapon_port import validate_manifest_contract as manifest_contract  # noqa: E402
from weapon_port import validate_materials  # noqa: E402
from weapon_port import validate_p4_t05  # noqa: E402


MANIFEST_PATH = PROJECT_ROOT / "assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json"
P4_WORK = PROJECT_ROOT / "work/m4a1_s_bornbeast/p4_prototype_01"
P4_BUILD = PROJECT_ROOT / "build/m4a1_s_bornbeast_m4a4/p4_prototype_01"
REPORT_DIR = P4_WORK
RUNNER_SCHEMA = "cf2.p4.t07-report.v1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_paths(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        result = value
        for old, new in replacements:
            result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [replace_paths(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_paths(item, replacements) for key, item in value.items()}
    return value


def update_trace_hash(trace_path: Path, output_path: Path) -> None:
    trace = read_json(trace_path)
    target = str(output_path.resolve())
    found = False
    for record in trace.get("outputs", {}).values():
        if isinstance(record, dict) and Path(str(record.get("path", ""))).resolve() == output_path.resolve():
            record["sha256"] = sha256(output_path) if output_path.is_file() else None
            found = True
    if not found:
        raise AssertionError(f"Mutation output is not represented in trace: {target}")
    write_json(trace_path, trace)


def current_run_root() -> Path:
    build = read_json(P4_WORK / "build_report.json")
    run_root = Path(build["upstream"]["run_root"])
    if not run_root.is_dir():
        raise RuntimeError(f"Current build run does not exist: {run_root}")
    return run_root


def copy_shadow(shadow_root: Path) -> tuple[Path, Path, Path, Path]:
    """Copy only the inputs and outputs consumed by the T05 validator."""
    run_root = current_run_root()
    required = [
        Path("assets/weapons/m4a1_s_bornbeast"),
        Path("data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB"),
        Path("work/m4a1_s_bornbeast/reference_m4a4"),
        Path("work/m4a1_s_bornbeast/source_dump/c3_alignment_m4a4"),
    ]
    for relative in required:
        source = PROJECT_ROOT / relative
        destination = shadow_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

    build_relative = P4_BUILD.relative_to(PROJECT_ROOT)
    run_relative = run_root.relative_to(PROJECT_ROOT)
    shadow_build = shadow_root / build_relative
    shadow_run = shadow_root / run_relative
    shutil.copytree(P4_BUILD, shadow_build, dirs_exist_ok=True)
    shutil.copytree(run_root, shadow_run, dirs_exist_ok=True)

    work_relative = P4_WORK.relative_to(PROJECT_ROOT)
    shadow_work = shadow_root / work_relative
    shadow_work.mkdir(parents=True, exist_ok=True)
    for name in ("build_report.json", "upstream_trace_report.json", "check_report.json", "material_closure_report.json"):
        source = P4_WORK / name
        if source.is_file():
            data = read_json(source)
            data = replace_paths(data, [(str(PROJECT_ROOT), str(shadow_root))])
            write_json(shadow_work / name, data)
    for relative in ("staging", "package"):
        source = P4_WORK / relative
        if source.is_dir():
            shutil.copytree(source, shadow_work / relative, dirs_exist_ok=True)

    manifest = read_json(MANIFEST_PATH)
    shadow_manifest = shadow_root / Path("assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json")
    write_json(shadow_manifest, manifest)
    return shadow_root, shadow_manifest, shadow_work, shadow_run


def run_t05(shadow_root: Path, manifest_path: Path, output_path: Path) -> tuple[int, dict[str, Any], str]:
    """Invoke the real T05 validator in-process with its project root shadowed."""
    # validate_p4_t05 imports the script as top-level ``pipeline`` after it
    # prepends scripts/ to sys.path.  Keep the exact module object it uses
    # shadowed; weapon_port.pipeline is a different import alias.
    validator_pipeline = validate_p4_t05.p
    previous_root = validator_pipeline.PROJECT_ROOT
    previous_args = sys.argv[:]
    validator_pipeline.PROJECT_ROOT = shadow_root
    try:
        sys.argv = [
            str(validate_p4_t05.__file__),
            "--manifest", str(manifest_path),
            "--report", str(output_path),
        ]
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = validate_p4_t05.main()
        report = read_json(output_path) if output_path.is_file() else {}
        return int(code), report, captured.getvalue()
    finally:
        sys.argv = previous_args
        validator_pipeline.PROJECT_ROOT = previous_root


def run_contract_mutation(name: str, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    mutate(manifest)
    with tempfile.TemporaryDirectory(prefix=f"cf2_t07_{name}_") as temporary:
        path = Path(temporary) / "manifest.json"
        write_json(path, manifest)
        passed, report = manifest_contract.validate_manifest_contract(path)
    return {
        "name": name,
        "expected_stage": "manifest_contract",
        "exit_code": 0 if passed else 1,
        "passed": not passed,
        "failed_gates": report.get("errors", []),
        "stdout": "manifest contract returned PASS" if passed else "manifest contract rejected mutation",
    }


def run_shadow_mutation(
    name: str,
    expected_stage: str,
    mutate: Callable[[Path, Path, Path, Path, dict[str, Any]], None],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"cf2_t07_{name}_") as temporary:
        shadow_root = Path(temporary)
        shadow_root, manifest_path, shadow_work, shadow_run = copy_shadow(shadow_root)
        manifest = read_json(manifest_path)
        mutate(shadow_root, shadow_work, shadow_run, manifest_path, manifest)
        write_json(manifest_path, manifest)
        # The staging tree is a T06 output, not an input to an isolated T05
        # mutation.  Remove it so a deliberately mutated build addon cannot
        # create a noisy downstream addon_staging_hashes failure.
        for stale in (shadow_work / "staging", shadow_work / "package"):
            if stale.exists():
                shutil.rmtree(stale)
        report_path = shadow_work / "validation_report.json"
        code, report, stdout = run_t05(shadow_root, manifest_path, report_path)
        failed = report.get("errors", [])
        passed = code != 0 and expected_stage in failed
        return {
            "name": name,
            "expected_stage": expected_stage,
            "exit_code": code,
            "passed": passed,
            "failed_gates": failed,
            "stdout": stdout[-1000:],
        }


def mutate_b3_obj(kind: str) -> Callable[[Path, Path, Path, Path, dict[str, Any]], None]:
    def mutate(_shadow: Path, _work: Path, run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
        path = run / "b3_raw/PV-M4A1_S_BornBeast_Classic.obj"
        lines = path.read_text(encoding="utf-8").splitlines()
        if kind == "triangle":
            for index in range(len(lines) - 1, -1, -1):
                if lines[index].startswith("f "):
                    del lines[index]
                    break
        elif kind == "group":
            for index, line in enumerate(lines):
                if line.startswith("g "):
                    lines[index] = "g MUTATED_GROUP"
                    break
        elif kind == "uv":
            for index, line in enumerate(lines):
                if line.startswith("f "):
                    tokens = line.split()
                    refs = tokens[1].split("/")
                    refs[1] = "999999"
                    tokens[1] = "/".join(refs)
                    lines[index] = " ".join(tokens)
                    break
        elif kind == "normal":
            for index in range(len(lines) - 1, -1, -1):
                if lines[index].startswith("vn "):
                    del lines[index]
                    break
        else:
            raise AssertionError(kind)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        update_trace_hash(_work / "upstream_trace_report.json", path)
    return mutate


def mutate_mapping(_shadow: Path, _work: Path, _run: Path, _manifest_path: Path, manifest: dict[str, Any]) -> None:
    first, second = manifest["mesh_bone_mapping"][0], manifest["mesh_bone_mapping"][1]
    first["bone_index"], second["bone_index"] = second["bone_index"], first["bone_index"]
    first["bone"], second["bone"] = second["bone"], first["bone"]


def mutate_matrix(shadow: Path, _work: Path, _run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
    path = shadow / "assets/weapons/m4a1_s_bornbeast/c3_alignment_m4a4_manifest.json"
    data = read_json(path)
    data["matrix_convention"] = "row vector; [p,1] @ matrix_cf_to_source"
    write_json(path, data)


def mutate_determinant(_shadow: Path, work: Path, run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
    path = run / "c3_aligned/c3_fixed_transform_report.json"
    data = read_json(path)
    data.setdefault("transform", {})["rotation_determinant"] = -1.0
    write_json(path, data)
    update_trace_hash(work / "upstream_trace_report.json", path)


def mutate_roundtrip(kind: str) -> Callable[[Path, Path, Path, Path, dict[str, Any]], None]:
    def mutate(_shadow: Path, _work: Path, run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
        path = run / "compiled_decompiled/reference_report.json"
        data = read_json(path)
        if kind == "sequence":
            data["sequences"][0]["name"] = "mutated_sequence"
        elif kind == "attachment":
            data["attachments"][0]["bone"] = "v_weapon.M4A1_Clip"
        else:
            raise AssertionError(kind)
        write_json(path, data)
    return mutate


def mutate_missing_binary(filename: str) -> Callable[[Path, Path, Path, Path, dict[str, Any]], None]:
    def mutate(_shadow: Path, _work: Path, _run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
        path = _shadow / "build/m4a1_s_bornbeast_m4a4/p4_prototype_01/addon/models/weapons" / filename
        path.unlink()
    return mutate


def mutate_material(shadow: Path, work: Path, _run: Path, _manifest_path: Path, _manifest: dict[str, Any]) -> None:
    addon = shadow / "build/m4a1_s_bornbeast_m4a4/p4_prototype_01/addon"
    missing = addon / "materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vtf"
    missing.unlink()
    qc = shadow / "build/m4a1_s_bornbeast_m4a4/p4_prototype_01/source1/v_rif_m4a1.qc"
    smd = shadow / "build/m4a1_s_bornbeast_m4a4/p4_prototype_01/source1/cf_bornbeast_full_m4a4.smd"
    report = work / "material_closure_report.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "weapon_port/validate_materials.py"), "--qc", str(qc), "--smd", str(smd), "--addon", str(addon), "--report", str(report)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode == 0:
        raise AssertionError("material validator unexpectedly accepted missing VTF")


def run_deploy_guard_cases() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cf2_t07_deploy_") as temporary:
        root = Path(temporary)
        game_root = root / "game"
        addons = game_root / "migi/csgo/addons"
        addons.mkdir(parents=True)
        previous_game_dir = pipeline.game_dir
        previous_package = pipeline.cmd_package
        previous_project_root = pipeline.PROJECT_ROOT
        try:
            pipeline.game_dir = lambda: str(game_root)
            pipeline.cmd_package = lambda *_args, **_kwargs: 0
            pipeline.PROJECT_ROOT = root
            manifest = {
                "profile_id": "Prototype-01",
                "outputs": {
                    "staging_root": "work/m4a1_s_bornbeast/p4_prototype_01/staging",
                    "package_manifest": "work/m4a1_s_bornbeast/p4_prototype_01/staging/package_manifest.json",
                    "deploy_report": "work/m4a1_s_bornbeast/p4_prototype_01/deploy_report.json",
                },
            }
            manifest_path = root / "manifest.json"
            write_json(manifest_path, manifest)
            staging = root / manifest["outputs"]["staging_root"]
            staging.mkdir(parents=True)
            (staging / "package_manifest.json").write_text("{}\n", encoding="utf-8")
            no_target_code = pipeline.cmd_deploy(manifest, manifest_path, SimpleNamespace(migi_addon=None, allow_custom_deploy_path=False))
            results.append({"name": "deploy_without_target", "expected_stage": "deploy_guard", "exit_code": no_target_code, "passed": no_target_code != 0, "failed_gates": ["explicit_target_required"]})

            target = addons / "different_content"
            target.mkdir()
            (target / "dummy.txt").write_text("must-not-be-overwritten", encoding="utf-8")
            different_code = pipeline.cmd_deploy(manifest, manifest_path, SimpleNamespace(migi_addon=str(target), allow_custom_deploy_path=True))
            results.append({"name": "deploy_different_existing_content", "expected_stage": "deploy_guard", "exit_code": different_code, "passed": different_code != 0 and (target / "dummy.txt").read_text(encoding="utf-8") == "must-not-be-overwritten", "failed_gates": ["different_content_rejected"]})
        finally:
            pipeline.game_dir = previous_game_dir
            pipeline.cmd_package = previous_package
            pipeline.PROJECT_ROOT = previous_project_root
    return results


def semantic_snapshot(run_root: Path) -> dict[str, Any]:
    def obj_snapshot(path: Path) -> dict[str, Any]:
        value = validate_p4_t05.parse_obj_semantics(path)
        value.pop("path", None)
        value.pop("sha256", None)
        return value

    reference = read_json(run_root / "compiled_decompiled/reference_report.json")
    return {
        "b3": obj_snapshot(run_root / "b3_raw/PV-M4A1_S_BornBeast_Classic.obj"),
        "c1": obj_snapshot(run_root / "c1_weapon_only/weapon_only/PV-M4A1_S_BornBeast_Classic_weapon_only.obj"),
        "c3": obj_snapshot(run_root / "c3_aligned/PV-M4A1_S_BornBeast_Classic_c3_aligned.obj"),
        "reference_semantics": {
            "bones": reference.get("bones"),
            "sequences": reference.get("sequences"),
            "attachments": reference.get("attachments"),
            "materials": reference.get("materials"),
            "mesh_bounds": reference.get("bounds", {}).get("smd_mesh_bounds"),
        },
    }


def run_build_once() -> tuple[int, str, str]:
    command = [sys.executable, str(SCRIPTS_DIR / "weapon_port/pipeline.py"), "build", "--manifest", str(MANIFEST_PATH)]
    result = subprocess.run(command, capture_output=True, text=True, cwd=PROJECT_ROOT, check=False)
    run_id = ""
    match = re.search(r"run (run_[0-9_]+)", result.stdout)
    if match:
        run_id = match.group(1)
    if not run_id:
        try:
            run_id = read_json(P4_WORK / "build_report.json").get("upstream", {}).get("run_id", "")
        except Exception:
            run_id = ""
    return result.returncode, run_id, (result.stdout + "\n" + result.stderr)[-4000:]


def run_reproducibility() -> dict[str, Any]:
    first_code, first_id, first_log = run_build_once()
    first_root = current_run_root() if first_code == 0 else None
    second_code, second_id, second_log = run_build_once()
    second_root = current_run_root() if second_code == 0 else None
    snapshot_equal = False
    first_snapshot: dict[str, Any] = {}
    second_snapshot: dict[str, Any] = {}
    if first_root and second_root:
        first_snapshot = semantic_snapshot(first_root)
        second_snapshot = semantic_snapshot(second_root)
        snapshot_equal = first_snapshot == second_snapshot
    return {
        "schema": "cf2.p4.reproducibility-report.v1",
        "task_id": "P4-T07",
        "runs": [
            {"run_id": first_id, "exit_code": first_code, "run_root": str(first_root) if first_root else None, "log_tail": first_log},
            {"run_id": second_id, "exit_code": second_code, "run_root": str(second_root) if second_root else None, "log_tail": second_log},
        ],
        "semantic_snapshot_equal": snapshot_equal,
        "semantic_snapshot": {"run_1": first_snapshot, "run_2": second_snapshot},
        "raw_byte_policy": {
            "required": "semantic equality of B3/C1/C3 OBJ and Source 1 roundtrip structures",
            "allowed_differences": ["compiler-generated binary bytes may differ; compare model header, skeleton, sequences, attachments, material and triangle semantics"],
        },
        "pass": first_code == 0 and second_code == 0 and first_id != second_id and snapshot_equal,
    }


def main() -> int:
    negative: list[dict[str, Any]] = []
    negative.append(run_contract_mutation("ltb_hash", lambda m: m["inputs"]["cf_ltb_source"].update(sha256="0" * 64)))
    negative.append(run_shadow_mutation("b3_triangle", "b3_semantics", mutate_b3_obj("triangle")))
    negative.append(run_shadow_mutation("b3_group", "b3_semantics", mutate_b3_obj("group")))
    negative.append(run_shadow_mutation("b3_uv_index", "b3_semantics", mutate_b3_obj("uv")))
    negative.append(run_shadow_mutation("b3_missing_normal", "b3_semantics", mutate_b3_obj("normal")))
    negative.append(run_shadow_mutation("mapping_parent_clip_swap", "smd_manifest_bone_corners", mutate_mapping))
    negative.append(run_shadow_mutation("c3_matrix_convention", "c3_matrix_and_semantics", mutate_matrix))
    negative.append(run_shadow_mutation("c3_negative_determinant", "c3_matrix_and_semantics", mutate_determinant))
    negative.append(run_shadow_mutation("sequence_name_same_count", "sequence_names_and_count", mutate_roundtrip("sequence")))
    negative.append(run_shadow_mutation("attachment_bone_same_count", "attachment_names_and_bones", mutate_roundtrip("attachment")))
    negative.append(run_shadow_mutation("missing_sw_vtx", "complete_binary_set", mutate_missing_binary("v_rif_m4a1.sw.vtx")))
    negative.append(run_shadow_mutation("missing_ani", "complete_binary_set", mutate_missing_binary("v_rif_m4a1.ani")))
    negative.append(run_shadow_mutation("missing_vtf_material_closure", "material_closure", mutate_material))
    negative.append(run_contract_mutation("final_cf_material", lambda m: m.update(final_cf_material=True)))
    negative.append(run_contract_mutation("output_repo_root", lambda m: m["outputs"].update(build_root="work")))
    negative.extend(run_deploy_guard_cases())

    negative_report = {
        "schema": RUNNER_SCHEMA,
        "task_id": "P4-T07",
        "mutation_count": len(negative),
        "passed_mutations": sum(1 for item in negative if item.get("passed")),
        "failed_mutations": [item["name"] for item in negative if not item.get("passed")],
        "mutations": negative,
        "isolation": "temporary shadow project for artifact mutations; deploy guards use temporary game root; no active addon touched",
        "pass": all(item.get("passed") for item in negative),
    }
    write_json(REPORT_DIR / "negative_test_report.json", negative_report)

    repro = run_reproducibility()
    write_json(REPORT_DIR / "reproducibility_report.json", repro)

    summary = {
        "negative_pass": negative_report["pass"],
        "negative_count": len(negative),
        "reproducibility_pass": repro["pass"],
        "run_ids": [item["run_id"] for item in repro["runs"]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if negative_report["pass"] and repro["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
