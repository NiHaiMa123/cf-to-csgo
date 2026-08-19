# -*- coding: utf-8 -*-
"""Apply the frozen C3 matrix to a fresh C1 weapon-only OBJ.

This is intentionally not an ICP/fitting script.  It reads the already locked
matrix from the C3 manifest, applies one shared affine transform to every
weapon mesh, rotates/normals-normalizes without scale, preserves face order,
and compares the result to the historical C3 aligned OBJ only as a semantic
and numeric regression reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def affine(matrix: list[list[float]], point: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(
        sum(float(matrix[row][col]) * point[col] for col in range(3)) + float(matrix[row][3])
        for row in range(3)
    )


def normalize_rotation(matrix: list[list[float]], scale: float) -> list[list[float]]:
    if not isinstance(scale, (int, float)) or scale <= 0:
        raise ValueError("C3 uniform_scale must be positive")
    return [[float(matrix[row][col]) / float(scale) for col in range(3)] for row in range(3)]


def rotate_normal(rotation: list[list[float]], normal: tuple[float, float, float]) -> tuple[float, float, float]:
    value = tuple(sum(rotation[row][col] * normal[col] for col in range(3)) for row in range(3))
    length = math.sqrt(sum(component * component for component in value))
    return value if length == 0 else tuple(component / length for component in value)


def transform_lines(lines: list[str], matrix: list[list[float]], rotation: list[list[float]]) -> list[str]:
    transformed: list[str] = []
    for line in lines:
        if line.startswith("v "):
            values = tuple(float(value) for value in line.split()[1:4])
            if len(values) != 3:
                raise ValueError(f"invalid vertex line: {line}")
            transformed.append("v " + " ".join(f"{value:.9f}" for value in affine(matrix, values)))
        elif line.startswith("vn "):
            values = tuple(float(value) for value in line.split()[1:4])
            if len(values) != 3:
                raise ValueError(f"invalid normal line: {line}")
            transformed.append("vn " + " ".join(f"{value:.9f}" for value in rotate_normal(rotation, values)))
        else:
            transformed.append(line)
    return transformed


def obj_stats(lines: list[str]) -> dict[str, Any]:
    vertices = 0
    uvs = 0
    normals = 0
    faces = 0
    current_group = ""
    current_material = "rif_m4a1"
    groups: dict[str, dict[str, Any]] = {}
    positions: list[tuple[float, float, float]] = []
    for line in lines:
        if line.startswith("g "):
            current_group = line[2:].strip()
            groups.setdefault(current_group, {"triangles": 0, "material": current_material, "vertices": 0})
        elif line.startswith("usemtl "):
            current_material = line[7:].strip()
            if current_group:
                groups.setdefault(current_group, {"triangles": 0, "material": current_material, "vertices": 0})["material"] = current_material
        elif line.startswith("v "):
            point = tuple(float(value) for value in line.split()[1:4])
            positions.append(point)
            vertices += 1
            if current_group:
                groups.setdefault(current_group, {"triangles": 0, "material": current_material, "vertices": 0})["vertices"] += 1
        elif line.startswith("vt "):
            uvs += 1
        elif line.startswith("vn "):
            normals += 1
        elif line.startswith("f "):
            faces += 1
            if current_group:
                groups.setdefault(current_group, {"triangles": 0, "material": current_material, "vertices": 0})["triangles"] += 1
    return {
        "vertices": vertices,
        "uvs": uvs,
        "normals": normals,
        "triangles": faces,
        "group_count": len(groups),
        "groups": groups,
        "bounds": {
            "min": [min(point[index] for point in positions) for index in range(3)] if positions else None,
            "max": [max(point[index] for point in positions) for index in range(3)] if positions else None,
        },
    }


def position_values(lines: list[str], normals: bool = False) -> list[tuple[float, ...]]:
    prefix = "vn " if normals else "v "
    width = 3
    return [tuple(float(value) for value in line.split()[1:1 + width]) for line in lines if line.startswith(prefix)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--transform-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-aligned-obj", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=1e-5)
    args = parser.parse_args()

    input_obj = args.input.resolve()
    transform_manifest_path = args.transform_manifest.resolve()
    reference_obj = args.reference_aligned_obj.resolve()
    output_obj = args.output.resolve()
    report_path = args.report.resolve()
    failures: list[str] = []
    report: dict[str, Any] = {
        "schema": "cf2.p4.c3-fixed-transform.v1",
        "method": "frozen_matrix",
        "inputs": {
            "weapon_only_obj": str(input_obj),
            "weapon_only_obj_sha256": sha256(input_obj) if input_obj.is_file() else None,
            "transform_manifest": str(transform_manifest_path),
            "transform_manifest_sha256": sha256(transform_manifest_path) if transform_manifest_path.is_file() else None,
            "reference_aligned_obj": str(reference_obj),
            "reference_aligned_obj_sha256": sha256(reference_obj) if reference_obj.is_file() else None,
        },
        "policy": {
            "shared_transform": True,
            "per_mesh_normalization": False,
            "automatic_icp": False,
            "automatic_center_or_scale": False,
            "winding": "preserve",
            "normal_policy": "rotation only then normalize",
        },
        "tolerance": args.tolerance,
    }

    if not input_obj.is_file():
        failures.append(f"input OBJ not found: {input_obj}")
    if not transform_manifest_path.is_file():
        failures.append(f"transform manifest not found: {transform_manifest_path}")
    reference_available = reference_obj.is_file()
    report["reference_available"] = reference_available
    try:
        transform_data = json.loads(transform_manifest_path.read_text(encoding="utf-8"))
        matrix = transform_data["matrix_cf_to_source"]
        scale = transform_data["uniform_scale"]
        if not isinstance(matrix, list) or len(matrix) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in matrix):
            raise ValueError("matrix_cf_to_source must be 4x4")
        if matrix[3] != [0.0, 0.0, 0.0, 1.0] and matrix[3] != [0, 0, 0, 1]:
            raise ValueError("matrix_cf_to_source must be affine with final row [0,0,0,1]")
        if transform_data.get("matrix_convention") != "homogeneous column vector; p_source = matrix_cf_to_source @ [p_cf, 1]":
            raise ValueError("unexpected matrix convention")
        rotation = normalize_rotation(matrix, scale)
        determinant = (
            rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
            - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
            + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
        )
        if determinant <= 0:
            raise ValueError(f"C3 rotation determinant must be positive, got {determinant}")
        report["transform"] = {"matrix_cf_to_source": matrix, "uniform_scale": scale, "rotation_determinant": determinant}
    except Exception as exc:
        failures.append(f"invalid frozen C3 transform: {exc}")
        matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        rotation = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    transformed_lines: list[str] = []
    source_lines: list[str] = []
    reference_lines: list[str] = []
    if not failures or input_obj.is_file():
        source_lines = input_obj.read_text(encoding="utf-8").splitlines()
        transformed_lines = transform_lines(source_lines, matrix, rotation)
        if reference_available:
            reference_lines = reference_obj.read_text(encoding="utf-8").splitlines()
        source_stats = obj_stats(source_lines)
        transformed_stats = obj_stats(transformed_lines)
        reference_stats = obj_stats(reference_lines) if reference_lines else None
        report["source_stats"] = source_stats
        report["output_stats"] = transformed_stats
        report["reference_stats"] = reference_stats
        if len([g for g in transformed_stats["groups"] if "Fview-" in g]) != 0:
            failures.append("C1 weapon-only OBJ still contains CF arm groups")
        if transformed_stats["group_count"] != 9 or transformed_stats["triangles"] != 4008:
            failures.append("C3 output must contain exactly 9 weapon groups and 4008 triangles")
        if reference_stats is not None:
            if transformed_stats["vertices"] != reference_stats["vertices"] or transformed_stats["uvs"] != reference_stats["uvs"] or transformed_stats["normals"] != reference_stats["normals"] or transformed_stats["triangles"] != reference_stats["triangles"] or set(transformed_stats["groups"]) != set(reference_stats["groups"]):
                failures.append("C3 output semantic stats/groups differ from frozen aligned reference")
            output_vertices = position_values(transformed_lines)
            reference_vertices = position_values(reference_lines)
            if len(output_vertices) != len(reference_vertices):
                failures.append("C3 output vertex stream length differs from frozen aligned reference")
            else:
                max_position_error = max((max(abs(a - b) for a, b in zip(left, right)) for left, right in zip(output_vertices, reference_vertices)), default=0.0)
                report["comparison"] = {"max_position_error": max_position_error}
                if max_position_error > args.tolerance:
                    failures.append(f"C3 output max position error {max_position_error} exceeds tolerance {args.tolerance}")
        else:
            report["comparison"] = {
                "reference_available": False,
                "status": "skipped_reference_unavailable",
                "reason": "The frozen aligned OBJ is an optional regression reference; matrix and semantic gates still ran.",
            }
        if source_stats["group_count"] != 9 or source_stats["triangles"] != 4008:
            failures.append("C1 input must contain exactly 9 weapon groups and 4008 triangles")

    report["passed"] = not failures
    report["failures"] = failures
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not failures:
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        output_obj.write_text("\n".join(transformed_lines) + "\n", encoding="utf-8")
        source_mtl = input_obj.with_suffix(".mtl")
        if source_mtl.is_file():
            shutil.copy2(source_mtl, output_obj.with_suffix(".mtl"))
        print(json.dumps({"passed": True, "output": str(output_obj), "report": str(report_path)}, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"passed": False, "report": str(report_path), "failures": failures}, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
