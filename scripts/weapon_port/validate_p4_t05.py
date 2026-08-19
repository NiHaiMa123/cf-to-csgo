# -*- coding: utf-8 -*-
"""P4-T05 semantic validation gates for the Prototype-01 pipeline.

This validator consumes only the current manifest, T03 upstream trace, T04
build report and their fresh run artifacts.  It deliberately does not infer
success from file existence alone: every gate records expected values,
observed values, a boolean result and evidence paths.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import pipeline as p  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def field(record: dict[str, Any], name: str, default: Any = None) -> Any:
    if name in record:
        return record[name]
    pascal = name[0].upper() + name[1:]
    if pascal in record:
        return record[pascal]
    snake = ""
    for char in name:
        snake += f"_{char.lower()}" if char.isupper() else char
    return record.get(snake, default)


def parse_smd_nodes(path: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    in_nodes = False
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.lower() == "nodes":
            in_nodes = True
            continue
        if in_nodes and line.lower() == "end":
            break
        if not in_nodes:
            continue
        match = re.match(r"(-?\d+)\s+\"([^\"]+)\"\s+(-?\d+)$", line)
        if match:
            nodes.append({"index": int(match.group(1)), "name": match.group(2), "parent_index": int(match.group(3))})
    return nodes


def parse_qc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    model_match = re.search(r'\$modelname\s+"([^\"]+)"', text, flags=re.IGNORECASE)
    studio_match = re.search(r'\bstudio\s+"([^\"]+)"', text, flags=re.IGNORECASE)
    cdmaterials = re.findall(r'\$cdmaterials\s+"([^\"]+)"', text, flags=re.IGNORECASE)
    sequences = re.findall(r'\$sequence\s+"([^\"]+)"', text, flags=re.IGNORECASE)
    attachments: list[dict[str, Any]] = []
    for match in re.finditer(r'\$attachment\s+"([^\"]+)"\s+"([^\"]+)"([^\r\n]*)', text, flags=re.IGNORECASE):
        tail = " ".join(match.group(3).split())
        attachments.append({"name": match.group(1), "bone": match.group(2), "tail": tail})
    return {
        "path": str(path.resolve()),
        "sha256": p.artifact_hash(path),
        "modelname": model_match.group(1) if model_match else None,
        "studio": studio_match.group(1) if studio_match else None,
        "cdmaterials": cdmaterials,
        "sequences": sequences,
        "attachments": attachments,
    }


def parse_obj_semantics(path: Path) -> dict[str, Any]:
    vertices = 0
    uvs = 0
    normals = 0
    triangles = 0
    invalid_faces = 0
    current_group = ""
    current_material = ""
    groups: dict[str, dict[str, Any]] = {}

    def ensure_group(name: str) -> dict[str, Any]:
        return groups.setdefault(name, {"vertices": 0, "uvs": 0, "normals": 0, "triangles": 0, "material_slots": []})

    def parse_index(value: str, total: int) -> int | None:
        try:
            number = int(value)
        except ValueError:
            return None
        if number < 0:
            number = total + number + 1
        return number if 1 <= number <= total else None

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "g":
            current_group = parts[1] if len(parts) > 1 else ""
            ensure_group(current_group)
        elif parts[0] == "usemtl":
            current_material = parts[1] if len(parts) > 1 else ""
            if current_group and current_material not in ensure_group(current_group)["material_slots"]:
                ensure_group(current_group)["material_slots"].append(current_material)
        elif parts[0] == "v":
            vertices += 1
            if current_group:
                ensure_group(current_group)["vertices"] += 1
        elif parts[0] == "vt":
            uvs += 1
            if current_group:
                ensure_group(current_group)["uvs"] += 1
        elif parts[0] == "vn":
            normals += 1
            if current_group:
                ensure_group(current_group)["normals"] += 1
        elif parts[0] == "f":
            triangles += 1
            if current_group:
                group = ensure_group(current_group)
                group["triangles"] += 1
                if current_material and current_material not in group["material_slots"]:
                    group["material_slots"].append(current_material)
            tokens = parts[1:]
            if len(tokens) != 3:
                invalid_faces += 1
                continue
            for token in tokens:
                refs = token.split("/")
                if len(refs) != 3 or not refs[0] or not refs[1] or not refs[2]:
                    invalid_faces += 1
                    continue
                if parse_index(refs[0], vertices) is None or parse_index(refs[1], uvs) is None or parse_index(refs[2], normals) is None:
                    invalid_faces += 1

    return {
        "path": str(path.resolve()),
        "sha256": p.artifact_hash(path),
        "vertices": vertices,
        "uvs": uvs,
        "normals": normals,
        "triangles": triangles,
        "group_count": len(groups),
        "groups": {name: groups[name] for name in sorted(groups)},
        "material_slots": sorted({slot for group in groups.values() for slot in group["material_slots"]}),
        "invalid_faces": invalid_faces,
    }


def tree_file_hashes(root: Path, exclude_names: set[str] | None = None) -> dict[str, dict[str, Any]]:
    exclude_names = exclude_names or set()
    if not root.is_dir():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in exclude_names:
            result[path.relative_to(root).as_posix()] = {
                "size_bytes": path.stat().st_size,
                "sha256": p.sha256_file(path),
            }
    return result


def add_gate(gates: dict[str, Any], name: str, expected: Any, actual: Any, passed: bool, evidence: list[str] | None = None, status: str = "checked") -> None:
    gates[name] = {
        "expected": expected,
        "actual": actual,
        "pass": bool(passed),
        "status": status,
        "evidence": evidence or [],
    }


def safe_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(value).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    report_path = args.report.resolve()
    manifest = load_json(manifest_path)
    gates: dict[str, Any] = {}
    errors: list[str] = []
    evidence_root = report_path.parent

    def gate(name: str, expected: Any, actual: Any, passed: bool, evidence: list[Path] | None = None, status: str = "checked") -> None:
        evidence_text = [str(path.resolve()) for path in evidence or []]
        add_gate(gates, name, expected, actual, passed, evidence_text, status)
        if not passed:
            errors.append(name)

    build_report_path = p.resolve_proj_path(manifest["outputs"]["build_report"])
    trace_path = p.resolve_proj_path(manifest["outputs"]["upstream_trace_report"])
    check_report_path = p.resolve_proj_path(manifest["outputs"]["check_report"])
    material_report_path = p.resolve_proj_path(manifest["outputs"]["material_closure_report"])
    build_root = p.resolve_proj_path(manifest["outputs"]["build_root"])
    addon = p.resolve_proj_path(manifest["outputs"]["addon"])
    staging = p.resolve_proj_path(manifest["outputs"]["staging_root"])
    reference_dir = p.resolve_proj_path("work/m4a1_s_bornbeast/reference_m4a4")
    reference_smd = reference_dir / "decompiled" / "v_m4a1_model.smd"
    reference_qc = reference_dir / "decompiled" / "v_rif_m4a1.qc"
    source1 = build_root / "source1"
    qc_path = source1 / "v_rif_m4a1.qc"
    smd_path = source1 / "cf_bornbeast_full_m4a4.smd"

    build = load_json(build_report_path) if build_report_path.is_file() else {}
    trace = load_json(trace_path) if trace_path.is_file() else {}
    build_run_root = safe_path(build.get("upstream", {}).get("run_root"))
    trace_run_root = safe_path(trace.get("run_root"))
    current_run_root = build_run_root or trace_run_root

    # 1. Current-run dependency chain and hashes.
    chain_actual = {
        "manifest_sha256": p.sha256_file(manifest_path) if manifest_path.is_file() else None,
        "build_report_exists": build_report_path.is_file(),
        "trace_exists": trace_path.is_file(),
        "build_pass": build.get("pass"),
        "trace_pass": trace.get("passed"),
        "run_id_match": bool(build.get("upstream", {}).get("run_id") == trace.get("run_id")),
        "run_root_match": bool(build_run_root and trace_run_root and build_run_root == trace_run_root),
        "step_exit_codes": [step.get("exit_code") for step in trace.get("steps", [])],
        "trace_output_hashes": {},
    }
    trace_hash_pass = True
    for name, record in trace.get("outputs", {}).items():
        path = safe_path(record.get("path")) if isinstance(record, dict) else None
        actual_hash = p.artifact_hash(path) if path else None
        chain_actual["trace_output_hashes"][name] = actual_hash
        if actual_hash != record.get("sha256"):
            trace_hash_pass = False
    chain_pass = (
        chain_actual["build_report_exists"]
        and chain_actual["trace_exists"]
        and chain_actual["build_pass"] is True
        and chain_actual["trace_pass"] is True
        and chain_actual["run_id_match"]
        and chain_actual["run_root_match"]
        and bool(chain_actual["step_exit_codes"])
        and all(code == 0 for code in chain_actual["step_exit_codes"])
        and trace_hash_pass
        and bool(current_run_root and current_run_root.is_dir())
    )
    gate("dependency_chain", {"task": "P4-T03", "all_trace_steps_exit": 0, "fresh_run": True}, chain_actual, chain_pass, [build_report_path, trace_path])

    # 2. Fresh B3 exporter report and OBJ semantics.
    b3_obj = current_run_root / "b3_raw" / "PV-M4A1_S_BornBeast_Classic.obj" if current_run_root else Path()
    b3_report = b3_obj.with_name(b3_obj.stem + "_export_report.json") if b3_obj else Path()
    b3_roundtrip = current_run_root / "b3_roundtrip_report.json" if current_run_root else Path()
    b3_actual = parse_obj_semantics(b3_obj) if b3_obj.is_file() else {}
    b3_export = load_json(b3_report) if b3_report.is_file() else {}
    b3_meshes = field(b3_export, "meshes", []) or []
    b3_expected_groups = [field(mesh, "groupName") for mesh in b3_meshes]
    b3_expected_group_stats = {
        field(mesh, "groupName"): {
            "triangles": field(mesh, "triangleCount"),
            "vertices": field(mesh, "vertexCount"),
            "uvs": field(mesh, "vertexCount"),
            "normals": field(mesh, "normalCount"),
            "material_slots": [field(mesh, "materialName")],
        }
        for mesh in b3_meshes
    }
    b3_actual_groups = sorted(b3_actual.get("groups", {}).keys())
    b3_stats_pass = bool(b3_obj.is_file()) and (
        b3_actual.get("vertices") == field(field(b3_export, "totals", {}), "vertexCount")
        and b3_actual.get("uvs") == field(field(b3_export, "totals", {}), "uvCount")
        and b3_actual.get("normals") == field(field(b3_export, "totals", {}), "normalCount")
        and b3_actual.get("triangles") == field(field(b3_export, "totals", {}), "triangleCount")
        and b3_actual_groups == sorted(b3_expected_groups)
        and b3_actual.get("invalid_faces") == 0
        and all(b3_actual["groups"].get(group) == stats for group, stats in b3_expected_group_stats.items())
    )
    gate("b3_semantics", {"groups": b3_expected_groups, "totals": field(b3_export, "totals", {})}, b3_actual, b3_stats_pass, [b3_obj, b3_report, b3_roundtrip])

    # 3. Fresh C1 weapon-only semantics and exact arm exclusion.
    c1_report = current_run_root / "c1_weapon_only" / "PV-M4A1_S_BornBeast_Classic_c1_split_report.json" if current_run_root else Path()
    c1_data = load_json(c1_report) if c1_report.is_file() else {}
    c1_obj = current_run_root / "c1_weapon_only" / "weapon_only" / "PV-M4A1_S_BornBeast_Classic_weapon_only.obj" if current_run_root else Path()
    c1_actual = parse_obj_semantics(c1_obj) if c1_obj.is_file() else {}
    expected_mapping = manifest.get("mesh_bone_mapping", [])
    expected_groups = [item["group"] for item in expected_mapping]
    c1_records = c1_data.get("weapon_only", [])
    c1_expected_group_stats = {
        record.get("group"): {
            "triangles": record.get("triangles"),
            "vertices": record.get("vertices"),
            "uvs": record.get("uvs"),
            "normals": record.get("normals"),
            "material_slots": [record.get("material")],
        }
        for record in c1_records
    }
    c1_actual_groups = sorted(c1_actual.get("groups", {}).keys())
    c1_pass = (
        c1_obj.is_file()
        and c1_data.get("weapon_only_mesh_count") == 9
        and c1_data.get("cf_arms_optional_mesh_count") == 2
        and sorted(record.get("group") for record in c1_records) == sorted(expected_groups)
        and c1_actual_groups == sorted(expected_groups)
        and c1_actual.get("invalid_faces") == 0
        and c1_actual.get("vertices") == manifest["expectations"]["aligned_obj"]["vertices"]
        and c1_actual.get("uvs") == manifest["expectations"]["aligned_obj"]["uvs"]
        and c1_actual.get("normals") == manifest["expectations"]["aligned_obj"]["normals"]
        and c1_actual.get("triangles") == manifest["expectations"]["aligned_obj"]["triangles"]
        and all(c1_actual["groups"].get(group) == stats for group, stats in c1_expected_group_stats.items())
        and {record.get("group") for record in c1_data.get("cf_arms_optional", [])} == {
            "PV-M4A1_S_BornBeast_Classic_Fview-hand2",
            "PV-M4A1_S_BornBeast_Classic_Fview-arm2",
        }
        and not any("Fview-" in group for group in c1_actual_groups)
    )
    gate("c1_weapon_only_semantics", {"groups": expected_groups, "aligned_obj": manifest["expectations"]["aligned_obj"]}, c1_actual, c1_pass, [c1_obj, c1_report])

    # 4. Frozen C3 matrix/policy and output semantics.
    c3_report = current_run_root / "c3_aligned" / "c3_fixed_transform_report.json" if current_run_root else Path()
    c3_data = load_json(c3_report) if c3_report.is_file() else {}
    alignment_path = p.resolve_proj_path(manifest["inputs"]["alignment_manifest"]["path"])
    alignment = load_json(alignment_path) if alignment_path.is_file() else {}
    c3_output = current_run_root / "c3_aligned" / "PV-M4A1_S_BornBeast_Classic_c3_aligned.obj" if current_run_root else Path()
    c3_actual = parse_obj_semantics(c3_output) if c3_output.is_file() else {}
    c3_policy_actual = c3_data.get("policy", {})
    c3_policy_expected = {
        "automatic_icp": False,
        "automatic_center_or_scale": False,
        "per_mesh_normalization": False,
        "winding": "preserve",
        "normal_policy": manifest["transform"]["normal_policy"],
    }
    c3_policy_pass = all(c3_policy_actual.get(key) == value for key, value in c3_policy_expected.items())
    c3_transform_actual = c3_data.get("transform", {})
    c3_transform_pass = (
        c3_transform_actual.get("matrix_cf_to_source") == alignment.get("matrix_cf_to_source")
        and c3_transform_actual.get("uniform_scale") == alignment.get("uniform_scale")
        and float(c3_transform_actual.get("rotation_determinant", 0)) > 0
        and alignment.get("matrix_convention") == manifest["transform"]["matrix_convention"]
        and alignment.get("normal_policy") == manifest["transform"]["normal_policy"]
        and str(alignment.get("winding_policy", "")).lower().startswith("preserve")
        and "determinant" in str(alignment.get("winding_policy", "")).lower()
    )
    c3_stats_expected = manifest["expectations"]["aligned_obj"]
    c3_stats_pass = all(c3_actual.get(key) == value for key, value in c3_stats_expected.items()) and c3_actual.get("invalid_faces") == 0
    c3_pass = c3_report.is_file() and c3_data.get("passed") is True and c3_policy_pass and c3_transform_pass and c3_stats_pass
    gate("c3_matrix_and_semantics", {"policy": c3_policy_expected, "transform": alignment, "stats": c3_stats_expected}, {"policy": c3_policy_actual, "transform": c3_transform_actual, "stats": c3_actual, "comparison": c3_data.get("comparison")}, c3_pass, [alignment_path, c3_report, c3_output])

    # 5. Fresh SMD skeleton nodes against the official M4A4 reference.
    actual_nodes = parse_smd_nodes(smd_path) if smd_path.is_file() else []
    expected_nodes = parse_smd_nodes(reference_smd) if reference_smd.is_file() else []
    skeleton_pass = actual_nodes == expected_nodes and len(actual_nodes) == manifest["expectations"]["runtime"]["bone_count"]
    gate("smd_skeleton", {"node_count": len(expected_nodes), "nodes": expected_nodes}, {"node_count": len(actual_nodes), "nodes": actual_nodes}, skeleton_pass, [smd_path, reference_smd])

    # 6. Manifest-derived primary bone corner distribution.
    mapping_actual = build.get("mesh_bone_mapping", [])
    expected_corners: Counter[int] = Counter()
    for item in expected_mapping:
        expected_corners[item["bone_index"]] += int(item["expected_triangles"]) * 3
    smd_actual_corners = p.smd_primary_bone_counts(smd_path) if smd_path.is_file() else {}
    mapping_pass = (
        mapping_actual
        and smd_actual_corners == dict(sorted(expected_corners.items()))
        and all(item.get("triangles") == manifest_item["expected_triangles"] for item, manifest_item in zip(mapping_actual, expected_mapping, strict=False))
        and all(item.get("corners") == manifest_item["expected_triangles"] * 3 for item, manifest_item in zip(mapping_actual, expected_mapping, strict=False))
    )
    gate("smd_manifest_bone_corners", {"mapping": expected_mapping, "primary_corners": dict(sorted(expected_corners.items()))}, {"mapping": mapping_actual, "primary_corners": smd_actual_corners}, bool(mapping_pass), [build_report_path, smd_path])

    # 7. QC contract and sequence/attachment semantics.
    actual_qc = parse_qc(qc_path) if qc_path.is_file() else {}
    reference_qc_data = parse_qc(reference_qc) if reference_qc.is_file() else {}
    expected_modelname = manifest["runtime"]["modelname"]
    qc_model_pass = actual_qc.get("modelname", "").replace("\\", "/") == expected_modelname
    gate("qc_modelname", expected_modelname, actual_qc.get("modelname"), qc_model_pass, [qc_path])
    qc_body_pass = actual_qc.get("studio") == "cf_bornbeast_full_m4a4.smd"
    gate("qc_body_smd_and_material_path", {"body_smd": "cf_bornbeast_full_m4a4.smd", "cdmaterials": reference_qc_data.get("cdmaterials")}, {"body_smd": actual_qc.get("studio"), "cdmaterials": actual_qc.get("cdmaterials")}, qc_body_pass and actual_qc.get("cdmaterials") == reference_qc_data.get("cdmaterials"), [qc_path, reference_qc])
    expected_sequences = manifest["expectations"]["sequences"]
    roundtrip_path = current_run_root / "compiled_decompiled" / "reference_report.json" if current_run_root else Path()
    roundtrip = load_json(roundtrip_path) if roundtrip_path.is_file() else {}
    roundtrip_sequences = [item.get("name") for item in roundtrip.get("sequences", [])]
    sequence_pass = actual_qc.get("sequences") == expected_sequences and roundtrip_sequences == expected_sequences
    gate("sequence_names_and_count", expected_sequences, {"qc": actual_qc.get("sequences"), "roundtrip": roundtrip_sequences}, sequence_pass, [qc_path, roundtrip_path])
    expected_attachments = [{"name": str(name), "bone": bone} for name, bone in manifest["expectations"]["attachments"].items()]
    actual_attachments = [{"name": item["name"], "bone": item["bone"]} for item in actual_qc.get("attachments", [])]
    reference_attachments = [{"name": item["name"], "bone": item["bone"]} for item in reference_qc_data.get("attachments", [])]
    roundtrip_attachments = [{"name": str(item.get("name")), "bone": item.get("bone")} for item in roundtrip.get("attachments", [])]
    attachment_pass = actual_attachments == expected_attachments and reference_attachments == expected_attachments and roundtrip_attachments == expected_attachments
    gate("attachment_names_and_bones", expected_attachments, {"qc": actual_attachments, "reference": reference_attachments, "roundtrip": roundtrip_attachments}, attachment_pass, [qc_path, reference_qc, roundtrip_path])

    # 8. Complete Source 1 binary set.
    binary_names = [
        "v_rif_m4a1.mdl",
        "v_rif_m4a1.vvd",
        "v_rif_m4a1.ani",
        "v_rif_m4a1.dx80.vtx",
        "v_rif_m4a1.dx90.vtx",
        "v_rif_m4a1.sw.vtx",
    ]
    binary_actual = {name: (addon / "models" / "weapons" / name).is_file() for name in binary_names}
    gate("complete_binary_set", {name: True for name in binary_names}, binary_actual, all(binary_actual.values()), [addon / "models" / "weapons"])

    # 9. MDL header and Crowbar roundtrip semantic summary.
    mdl_path = addon / "models" / "weapons" / "v_rif_m4a1.mdl"
    header = p.mdl_header(mdl_path) if mdl_path.is_file() else {}
    mesh_summary = (roundtrip.get("bounds", {}).get("smd_mesh_bounds") or [{}])[0]
    mdl_expected = {
        "internal_name": "weapons\\v_rif_m4a1.mdl",
        "bone_count": manifest["expectations"]["runtime"]["bone_count"],
        "local_sequence_count": manifest["expectations"]["runtime"]["sequence_count"],
        "attachment_count": manifest["expectations"]["runtime"]["attachment_count"],
        "material": manifest["expectations"]["runtime"]["material"],
        "triangle_count": manifest["expectations"]["aligned_obj"]["triangles"],
    }
    mdl_actual = {
        "internal_name": header.get("internal_name"),
        "bone_count": header.get("bone_count"),
        "local_sequence_count": header.get("local_sequence_count"),
        "attachment_count": len(roundtrip.get("attachments", [])),
        "material": (roundtrip.get("materials", {}).get("smd_materials") or [None])[0],
        "triangle_count": mesh_summary.get("triangle_count"),
    }
    mdl_pass = all(mdl_actual.get(key) == value for key, value in mdl_expected.items())
    gate("mdl_and_roundtrip_semantics", mdl_expected, mdl_actual, mdl_pass, [mdl_path, roundtrip_path])

    # 10. SMD -> QC -> VMT -> VTF closure.
    material_report = load_json(material_report_path) if material_report_path.is_file() else {}
    material_pass = material_report.get("pass") is True and all(item.get("pass") is True for item in material_report.get("closure", []))
    gate("material_closure", {"pass": True, "all_vmt_vtf_references_exist": True}, material_report, material_pass, [material_report_path, qc_path, smd_path])

    # 11. Prototype provenance flags.
    policy_expected = {
        "final_target_identity": False,
        "final_cf_material": False,
        "classification": "EXTERNAL_REFERENCE / PROTOTYPE MATERIAL",
    }
    policy_actual = {
        "final_target_identity": manifest.get("final_target_identity"),
        "final_cf_material": manifest.get("final_cf_material"),
        "classification": manifest.get("material_policy", {}).get("classification"),
        "build_report_policy": build.get("material_policy", {}).get("classification"),
    }
    policy_pass = policy_actual["final_target_identity"] is False and policy_actual["final_cf_material"] is False and policy_actual["classification"] == policy_expected["classification"] and policy_actual["build_report_policy"] == policy_expected["classification"]
    gate("prototype_material_provenance", policy_expected, policy_actual, policy_pass, [manifest_path, build_report_path])

    # 12. Build addon vs staging.  A missing staging is explicitly deferred
    # to P4-T06 package; a present but different staging is a hard failure.
    addon_hashes = tree_file_hashes(addon, {"package_manifest.json"})
    staging_hashes = tree_file_hashes(staging, {"package_manifest.json"})
    if staging.is_dir() and staging_hashes:
        staging_pass = addon_hashes == staging_hashes
        staging_status = "checked"
    else:
        staging_pass = True
        staging_status = "deferred_until_package"
    gate("addon_staging_hashes", {"files": addon_hashes, "status": "equal_when_staging_exists"}, {"addon": addon_hashes, "staging": staging_hashes}, staging_pass, [addon, staging], staging_status)

    report = {
        "schema": "cf2.p4.validation-report.v2",
        "task_id": "P4-T05",
        "profile_id": manifest.get("profile_id"),
        "manifest": str(manifest_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": build.get("upstream", {}).get("run_id"),
        "pass": not errors,
        "errors": errors,
        "gates": gates,
        "legacy_checks": {
            "check_report": str(check_report_path),
            "material_closure_report": str(material_report_path),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"], "failed_gates": errors}, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
