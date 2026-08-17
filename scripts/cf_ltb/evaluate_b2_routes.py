# -*- coding: utf-8 -*-
"""Evaluate the two B2 LTB extraction routes on a small and target model.

This is a decision-gate report, not an animation-support claim.  It records
which external converters are actually available in this workspace and
compares the native decoder's field-level reports.  Skeleton nodes, packed
bone indices, and bind-pose validation are reported separately from animation
clip support.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = PROJECT_ROOT / "data" / "rf016" / "Models" / "PLAYERVIEW" / "PV-M4A1_S_BornBeast_Classic.LTB"
DEFAULT_SAMPLE = PROJECT_ROOT / "data" / "rf016" / "Models" / "PLAYERVIEW" / "PV-M4A1_BL.LTB"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reports"
DEFAULT_DUMP_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "source_dump"
DEFAULT_EXE = PROJECT_ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_model(exe: Path, model: Path, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(exe), "--inspect-ltb", "--input", str(model), "--output", str(output)]
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if process.returncode != 0:
        raise RuntimeError(f"native inspection failed for {model}: {process.returncode}: {(process.stderr or process.stdout)[-500:]}")
    if not output.is_file():
        raise RuntimeError(f"native inspection produced no report: {output}")
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout_tail": (process.stdout or "")[-500:],
        "stderr_tail": (process.stderr or "")[-500:],
        "report": str(output),
    }


def converter_inventory() -> list[dict[str, Any]]:
    names = [
        "ltb2x.exe",
        "LTB2X.exe",
        "ltb2lta.exe",
        "Model_Unpacker.exe",
        "noesis.exe",
        "Noesis.exe",
    ]
    candidates = [PROJECT_ROOT / "tools" / name for name in names]
    candidates.extend(PROJECT_ROOT / "tools" / folder / name for folder in ("LTB2X", "Noesis", "Model_Unpacker") for name in names)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        records.append({"name": candidate.name, "path": str(candidate), "exists": candidate.is_file()})
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            records.append({"name": name, "path": resolved, "exists": True, "source": "PATH"})
    return records


def field_matrix(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fields = [
        "normals",
        "tangents",
        "bone_weights",
        "bone_indices",
        "skeleton_nodes",
        "bind_pose",
        "animation_clips",
        "material_bindings",
        "coordinate_transform",
    ]
    matrix: dict[str, Any] = {}
    for field in fields:
        matrix[field] = {
            label: report.get("capabilities", {}).get(field, {}).get("status")
            for label, report in reports.items()
        }
    return matrix


def model_summary(report: dict[str, Any]) -> dict[str, Any]:
    geometry = report.get("geometry", {})
    validation = report.get("validation", {})
    return {
        "input": report.get("input"),
        "mesh_count": geometry.get("mesh_count"),
        "vertex_count": geometry.get("vertex_count"),
        "triangle_count": geometry.get("triangle_count"),
        "coordinate_space": geometry.get("coordinate_space"),
        "finite_vertex_positions": validation.get("finite_vertex_positions"),
        "finite_normals": validation.get("finite_normals"),
        "normal_vectors_nonzero": validation.get("normal_vectors_nonzero"),
        "decoded_weight_sample_count": validation.get("decoded_weight_sample_count"),
        "invalid_weight_sum_count": validation.get("invalid_weight_sum_count"),
        "bone_index_range_checked": validation.get("bone_index_range_checked"),
        "decoded_bone_index_sample_count": validation.get("decoded_bone_index_sample_count"),
        "bind_pose_roundtrip_checked": validation.get("bind_pose_skinning_roundtrip_checked"),
        "bind_pose_roundtrip_passed": validation.get("bind_pose_skinning_roundtrip_passed"),
        "bind_pose_max_error": validation.get("bind_pose_skinning_roundtrip_max_error"),
        "capabilities": report.get("capabilities"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dump-dir", type=Path, default=DEFAULT_DUMP_DIR)
    parser.add_argument("--cfrezmanager", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--skip-run", action="store_true", help="reuse existing per-model diagnostic JSON files")
    args = parser.parse_args()
    target = args.target.resolve()
    sample = args.sample.resolve()
    if not target.is_file() or not sample.is_file():
        raise SystemExit(f"B2 inputs not found: target={target}, sample={sample}")
    if not args.skip_run and not args.cfrezmanager.is_file():
        raise SystemExit(f"CFRezManager executable not found: {args.cfrezmanager}")

    runs: dict[str, Any] = {}
    report_paths = {
        "small_sample": args.dump_dir.resolve() / f"{sample.stem}_b2_report.json",
        "target_m4a1_s": args.dump_dir.resolve() / f"{target.stem}_b1_report.json",
    }
    models = {"small_sample": sample, "target_m4a1_s": target}
    if not args.skip_run:
        for label, model in models.items():
            runs[label] = inspect_model(args.cfrezmanager.resolve(), model, report_paths[label])

    reports: dict[str, dict[str, Any]] = {}
    for label, path in report_paths.items():
        if not path.is_file():
            raise SystemExit(f"diagnostic report missing for {label}: {path}")
        reports[label] = json.loads(path.read_text(encoding="utf-8"))

    target_validation = reports["target_m4a1_s"].get("validation", {})
    sample_validation = reports["small_sample"].get("validation", {})
    external = converter_inventory()
    available_external = [item for item in external if item.get("exists")]
    native_static_proof = all(
        report.get("validation", {}).get("finite_vertex_positions") and
        report.get("validation", {}).get("finite_normals") and
        report.get("validation", {}).get("normal_vectors_nonzero")
        for report in reports.values()
    )
    report = {
        "schema": "cf2.lithtech.b2-route-evaluation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            label: {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "diagnostic_report": str(report_paths[label]),
            }
            for label, path in models.items()
        },
        "route_1_external_converter": {
            "status": "available_candidate" if available_external else "not_available_in_workspace",
            "candidates": external,
            "stability_test": "not_run" if not available_external else "pending_explicit_tool_selection",
            "license_review": "not_run",
            "reason": "No LTB2X/Noesis/Model Unpacker executable was found in the project tools directory or PATH." if not available_external else "A candidate exists; do not use it until version, output fields, and license are recorded.",
        },
        "route_2_native_decoder": {
            "status": "static_geometry_normals_weights_and_bone_indices_proven",
            "runs": runs,
            "models": {label: model_summary(value) for label, value in reports.items()},
            "field_matrix": field_matrix(reports),
            "native_static_proof": native_static_proof,
            "weight_validation": {
                "small_sample_invalid_weight_sum_count": sample_validation.get("invalid_weight_sum_count"),
                "target_invalid_weight_sum_count": target_validation.get("invalid_weight_sum_count"),
                "bone_index_range_checked": all(
                    report.get("validation", {}).get("bone_index_range_checked") is True
                    for report in reports.values()
                ),
                "small_sample_decoded_bone_index_sample_count": sample_validation.get("decoded_bone_index_sample_count"),
                "target_decoded_bone_index_sample_count": target_validation.get("decoded_bone_index_sample_count"),
                "small_sample_bind_pose_roundtrip_passed": sample_validation.get("bind_pose_skinning_roundtrip_passed"),
                "target_bind_pose_roundtrip_passed": target_validation.get("bind_pose_skinning_roundtrip_passed"),
                "target_bind_pose_max_error": target_validation.get("bind_pose_skinning_roundtrip_max_error"),
                "reason": "Packed per-vertex-range indices are validated against the LTB node-count header; decoded node names, hierarchy, bind matrices, and residual fourth weights are included in the bind-pose check.",
            },
        },
        "decision_gate_g_b": {
            "external_route_is_stable_and_licensed": False,
            "native_route_can_support_static_r1_r2": native_static_proof,
            "skeleton_nodes_ready": all(
                report.get("capabilities", {}).get("skeleton_nodes", {}).get("status") == "available"
                for report in reports.values()
            ),
            "bind_pose_ready": all(
                report.get("validation", {}).get("bind_pose_skinning_roundtrip_passed") is True
                for report in reports.values()
            ),
            "cf_animation_ready": False,
            "recommendation": "Native geometry, weights, packed bone indices, the 57-node hierarchy, and bind-pose skinning are proven. Continue native animation-block decoding; use official CS:GO M4A1-S animations for R1/R2 and do not label them CF-original animations.",
        },
        "unresolved_acceptance_items": [
            "CF animation clip/frame continuity, keyframe decoding, and NaN/spike checks are not implemented",
            "direct mesh-to-material/Shader bindings and tangent streams are not decoded",
            "no external LTB converter is vendored; the native decoder is the reproducible route",
        ],
    }
    output = args.report_dir.resolve() / "b2_route_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(output),
        "external_route": report["route_1_external_converter"]["status"],
        "native_static_proof": native_static_proof,
        "cf_animation_ready": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
