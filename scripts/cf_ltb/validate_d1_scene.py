#!/usr/bin/env python3
"""Validate the saved D1 Blender scene report without requiring Blender."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_COLLECTIONS = {"REFERENCE", "CF_WEAPON", "CSGO_ARMS", "EXPORT", "GUIDES"}
EXPECTED_EXPORT_OBJECTS = {
    "EXPORT_M4A1S_BornBeast",
    "EXPORT_M4A1S_BornBeast01",
    "EXPORT_M4A1S_BornBeast02",
    "EXPORT_M4A1S_BornBeast03",
    "EXPORT_M4A1S_BornBeast04",
    "EXPORT_M4A1S_BornBeast05",
    "EXPORT_M4A1S_BornBeast06",
    "EXPORT_M4A1S_BornBeast07",
    "EXPORT_M4A1S_BornBeast08",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    if not str(report.get("status", "")).startswith("PASS_"):
        failures.append(f"D1 builder status is not PASS: {report.get('status')}")
    tools = report.get("tools", {})
    if tools.get("blender") != "4.5.12 LTS":
        failures.append(f"unexpected Blender version: {tools.get('blender')}")
    if tools.get("blender_source_tools") != "3.4.3":
        failures.append(f"unexpected Blender Source Tools version: {tools.get('blender_source_tools')}")

    config = report.get("scene_configuration", {})
    if config.get("unit_system") != "NONE" or config.get("scale_length") != 1.0:
        failures.append("scene must use unitless Source units at scale_length 1.0")
    if config.get("up_axis") != "Z" or config.get("export_axis_contract") != "Z_UP_SMD":
        failures.append("scene/export axis contract is not Z-up SMD")
    if config.get("object_transforms_applied") is not True:
        failures.append("EXPORT object transforms are not applied")

    collections = report.get("collections", {})
    if set(collections) != REQUIRED_COLLECTIONS:
        failures.append(f"collection set differs: {sorted(collections)}")
    export_objects = collections.get("EXPORT", [])
    if len(export_objects) != 9:
        failures.append(f"EXPORT object count {len(export_objects)} != 9")
    if set(export_objects) != EXPECTED_EXPORT_OBJECTS:
        failures.append("EXPORT names are not stable/canonical; stale Blender datablocks may not have been purged")
    if any("Fview-" in name for name in export_objects):
        failures.append("CF hand/arm object leaked into EXPORT")

    skeleton = report.get("canonical_skeleton", {})
    if skeleton.get("bone_count") != 58 or skeleton.get("exact_name_parent_match") is not True:
        failures.append("official armature is not an exact 58-bone canonical match")
    bindings = report.get("r1_rigid_bindings", {})
    if set(bindings) != {name.removeprefix("EXPORT_") for name in EXPECTED_EXPORT_OBJECTS}:
        failures.append("R1 rigid binding set does not exactly cover all nine weapon meshes")
    for mesh, binding in bindings.items():
        if binding.get("weight") != 1.0 or binding.get("vertex_count", 0) <= 0:
            failures.append(f"{mesh}: R1 rigid binding is not 100% for every vertex")

    totals = report.get("geometry", {}).get("totals", {})
    expected_counts = {"vertices": 3633, "faces": 4008, "duplicate_vertices_merged": 13, "faces_removed": 0}
    for key, expected in expected_counts.items():
        if totals.get(key) != expected:
            failures.append(f"geometry {key} {totals.get(key)} != {expected}")
    for key in ("zero_area_geometry_faces", "zero_length_loop_normals", "complex_nonmanifold_edges"):
        if totals.get(key) != 0:
            failures.append(f"geometry blocker remains: {key}={totals.get(key)}")
    if totals.get("zero_area_uv_faces") != 16:
        failures.append("reviewed zero-area UV count changed; investigate rather than silently deleting faces")

    outputs = report.get("outputs", {})
    for label in ("blend", "preview"):
        path_value = outputs.get(label)
        expected_hash = outputs.get(label + "_sha256")
        if not path_value:
            failures.append(f"missing {label} output path")
            continue
        path = Path(path_value)
        if not path.is_file():
            failures.append(f"missing {label} artifact: {path}")
        elif sha256(path) != expected_hash:
            failures.append(f"{label} SHA-256 differs from D1 report")

    result = {
        "schema": "cf2.m4a1_s.d1-validation.v1",
        "report": str(report_path),
        "passed": not failures,
        "export_objects": len(export_objects),
        "bone_count": skeleton.get("bone_count"),
        "geometry_totals": totals,
        "known_advisories": report.get("advisories", []),
        "failures": failures,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
