# -*- coding: utf-8 -*-
"""Manifest Contract and Path Security Validator for P4 Prototype-01.

Enforces strict schema validation, input existence/hash checks, P4 security gates,
and output path containment strictly within allowed work/build subtrees.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ALLOWED_BUILD_SUBTREE = (PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "p4_prototype_01").resolve()
ALLOWED_WORK_SUBTREE = (PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "p4_prototype_01").resolve()

ALLOWED_TOP_LEVEL_KEYS = {
    "schema",
    "profile_id",
    "status",
    "final_target_identity",
    "final_cf_material",
    "runtime",
    "inputs",
    "toolchain",
    "transform",
    "mesh_bone_mapping",
    "material_policy",
    "expectations",
    "outputs",
}

ALLOWED_INPUT_ITEM_KEYS = {"path", "sha256", "role", "optional"}
ALLOWED_TOOL_ITEM_KEYS = {"path", "sha256", "role", "version"}
ALLOWED_RUNTIME_KEYS = {"slot", "modelname", "active_addon", "migi_write_policy"}
ALLOWED_MATERIAL_POLICY_KEYS = {"classification", "source_kind", "final_cf_material", "final_release_allowed", "purpose"}
ALLOWED_TRANSFORM_KEYS = {"manifest_ref", "matrix_convention", "source_space", "target_space", "normal_policy", "winding_policy"}
ALLOWED_MESH_MAP_KEYS = {"group", "bone_index", "bone", "static_fallback", "expected_triangles"}
ALLOWED_EXPECTATIONS_KEYS = {"aligned_obj", "runtime", "sequences", "attachments"}
ALLOWED_OUTPUT_KEYS = {
    "build_root",
    "addon",
    "p4_work_root",
    "check_report",
    "build_report",
    "validation_report",
    "manifest_contract_report",
    "material_closure_report",
    "package_manifest",
    "deploy_report",
    "package_root",
    "staging_root",
    "game_regression_report",
    "upstream_trace_report",
}

REQUIRED_TOP_LEVEL_KEYS = set(ALLOWED_TOP_LEVEL_KEYS)
REQUIRED_RUNTIME_KEYS = {"slot", "modelname", "active_addon", "migi_write_policy"}
REQUIRED_MATERIAL_POLICY_KEYS = set(ALLOWED_MATERIAL_POLICY_KEYS)
REQUIRED_TRANSFORM_KEYS = set(ALLOWED_TRANSFORM_KEYS)
REQUIRED_MESH_MAP_KEYS = set(ALLOWED_MESH_MAP_KEYS)
REQUIRED_EXPECTATIONS_KEYS = set(ALLOWED_EXPECTATIONS_KEYS)
REQUIRED_OUTPUT_KEYS = {
    "build_root",
    "addon",
    "p4_work_root",
    "manifest_contract_report",
    "check_report",
    "build_report",
    "validation_report",
    "material_closure_report",
    "package_manifest",
    "deploy_report",
    "package_root",
    "staging_root",
    "game_regression_report",
}

EXPECTED_STATUS = "active_technical_validation_sample"
EXPECTED_MATRIX_CONVENTION = "homogeneous column vector; p_source = matrix_cf_to_source @ [p_cf, 1]"
EXPECTED_SOURCE_SPACE = "raw CF LTB model coordinates"
EXPECTED_TARGET_SPACE = "official M4A4 Source 1 bind-pose SMD coordinates"
EXPECTED_NORMAL_POLICY = "rotation only then normalize"
EXPECTED_WINDING_POLICY = "preserve; positive determinant"
EXPECTED_RUNTIME_ADDON = "p_cf_bornbeast_m4a4_f4_recognizable_tmp"
EXPECTED_MIGI_WRITE_POLICY = "deploy_subcommand_only"
EXPECTED_SEQUENCE_NAMES = (
    "idle",
    "shoot1",
    "shoot2",
    "shoot3",
    "reload",
    "draw",
    "lookat01",
    "lookat01_prepare",
    "lookat01_loop",
)
EXPECTED_ATTACHMENT_MAP = {"1": "v_weapon.flash", "2": "v_weapon.shelleject"}
OUTPUT_FILE_KEYS = {
    "manifest_contract_report",
    "check_report",
    "build_report",
    "validation_report",
    "material_closure_report",
    "package_manifest",
    "deploy_report",
    "game_regression_report",
    "upstream_trace_report",
}


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def is_path_contained(target: Path, base_dir: Path) -> bool:
    try:
        target.relative_to(base_dir)
        return True
    except ValueError:
        return False


def _is_absolute_or_traversal(path_str: str) -> bool:
    p = Path(path_str)
    return (
        p.is_absolute()
        or path_str.startswith("/")
        or path_str.startswith("\\")
        or (len(path_str) > 1 and path_str[1] == ":")
        or ".." in p.parts
    )


def _resolve_repo_relative(path_str: str, label: str) -> tuple[Path | None, str | None]:
    if not isinstance(path_str, str) or not path_str.strip():
        return None, f"{label} must be a non-empty string"
    if _is_absolute_or_traversal(path_str):
        return None, f"{label} must be a repository-relative path without absolute/traversal components: '{path_str}'"
    resolved = (PROJECT_ROOT / Path(path_str)).resolve()
    if not is_path_contained(resolved, PROJECT_ROOT) or resolved == PROJECT_ROOT:
        return None, f"{label} resolves outside the repository: '{path_str}' -> '{resolved}'"
    return resolved, None


def _is_strictly_contained(target: Path, base_dir: Path) -> bool:
    return target != base_dir and is_path_contained(target, base_dir)


def validate_output_path(key: str, rel_path_str: str, *, allow_exact_base: bool = False) -> tuple[bool, str]:
    if not isinstance(rel_path_str, str) or not rel_path_str.strip():
        return False, f"Output '{key}' must be a non-empty string"
    
    p = Path(rel_path_str)
    if p.is_absolute() or rel_path_str.startswith("/") or rel_path_str.startswith("\\") or (len(rel_path_str) > 1 and rel_path_str[1] == ":"):
        return False, f"Output '{key}' must be a relative path, got absolute: '{rel_path_str}'"
    
    parts = p.parts
    if ".." in parts:
        return False, f"Output '{key}' contains forbidden parent traversal '..': '{rel_path_str}'"
    
    resolved = (PROJECT_ROOT / p).resolve()
    
    # Check if target is project root or root of build/work
    if resolved == PROJECT_ROOT:
        return False, f"Output '{key}' cannot point to repository root: '{rel_path_str}'"
    if resolved == (PROJECT_ROOT / "build").resolve():
        return False, f"Output '{key}' cannot point to 'build/' root: '{rel_path_str}'"
    if resolved == (PROJECT_ROOT / "work").resolve():
        return False, f"Output '{key}' cannot point to 'work/' root: '{rel_path_str}'"
    
    in_build = is_path_contained(resolved, ALLOWED_BUILD_SUBTREE)
    in_work = is_path_contained(resolved, ALLOWED_WORK_SUBTREE)
    
    if not (in_build or in_work):
        return False, (
            f"Output '{key}' resolved path '{resolved}' escapes allowed subtrees: "
            f"must be strictly inside '{ALLOWED_BUILD_SUBTREE}' or '{ALLOWED_WORK_SUBTREE}'"
        )

    if not allow_exact_base and resolved in {ALLOWED_BUILD_SUBTREE, ALLOWED_WORK_SUBTREE}:
        return False, f"Output '{key}' must be strictly inside an allowed subtree, not equal to its root: '{rel_path_str}'"
    
    return True, ""


def validate_manifest_contract(manifest_path: Path | str) -> tuple[bool, dict[str, Any]]:
    m_path = Path(manifest_path)
    if not m_path.is_absolute():
        m_path = (PROJECT_ROOT / m_path).resolve()

    errors: list[str] = []
    field_consumption: dict[str, str] = {}
    details: dict[str, Any] = {}

    if not m_path.is_file():
        errors.append(f"Manifest file does not exist: {m_path}")
        return False, {
            "schema": "cf2.p4.manifest-contract-report.v1",
            "task_id": "P4-T02",
            "manifest_path": str(m_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pass": False,
            "errors": errors,
            "details": details,
        }

    try:
        manifest: dict[str, Any] = json.loads(m_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Manifest is not valid JSON: {e}")
        return False, {
            "schema": "cf2.p4.manifest-contract-report.v1",
            "task_id": "P4-T02",
            "manifest_path": str(m_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pass": False,
            "errors": errors,
            "details": details,
        }

    if not isinstance(manifest, dict):
        errors.append("Manifest root must be a JSON object (dictionary)")
        return False, {
            "schema": "cf2.p4.manifest-contract-report.v1",
            "task_id": "P4-T02",
            "manifest_path": str(m_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pass": False,
            "errors": errors,
            "details": details,
        }

    # 1. Top-level schema is closed: missing and unknown keys are both errors.
    unknown_top_keys = set(manifest.keys()) - ALLOWED_TOP_LEVEL_KEYS
    missing_top_keys = REQUIRED_TOP_LEVEL_KEYS - set(manifest.keys())
    if unknown_top_keys:
        errors.append(f"Manifest contains unrecognized top-level fields: {sorted(unknown_top_keys)}")
    if missing_top_keys:
        errors.append(f"Manifest is missing required top-level fields: {sorted(missing_top_keys)}")

    # 2. Schema, profile_id, status
    if manifest.get("schema") != "cf2.m4a4.prototype-manifest.v1":
        errors.append(f"schema must be 'cf2.m4a4.prototype-manifest.v1', got: '{manifest.get('schema')}'")
    field_consumption["schema"] = {"consumer": "manifest_contract_schema_gate", "value": manifest.get("schema")}

    if manifest.get("profile_id") != "Prototype-01":
        errors.append(f"profile_id must be 'Prototype-01', got: '{manifest.get('profile_id')}'")
    field_consumption["profile_id"] = {"consumer": "all_p4_reports", "value": manifest.get("profile_id")}

    if manifest.get("status") != EXPECTED_STATUS:
        errors.append(f"status must be '{EXPECTED_STATUS}', got: '{manifest.get('status')}'")
    field_consumption["status"] = {"consumer": "manifest_contract", "value": manifest.get("status")}

    # 3. P4 Mandatory boolean flags
    if manifest.get("final_target_identity") is not False:
        errors.append(f"P4 contract requires final_target_identity=false, got: {manifest.get('final_target_identity')}")
    field_consumption["final_target_identity"] = {"consumer": "manifest_contract_and_package", "value": manifest.get("final_target_identity")}

    if manifest.get("final_cf_material") is not False:
        errors.append(f"P4 contract requires final_cf_material=false, got: {manifest.get('final_cf_material')}")
    field_consumption["final_cf_material"] = {"consumer": "manifest_contract_and_package", "value": manifest.get("final_cf_material")}

    # 4. Runtime
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be a dictionary")
    else:
        unknown_runtime_keys = set(runtime.keys()) - ALLOWED_RUNTIME_KEYS
        missing_runtime_keys = REQUIRED_RUNTIME_KEYS - set(runtime.keys())
        if unknown_runtime_keys:
            errors.append(f"runtime contains unrecognized keys: {sorted(unknown_runtime_keys)}")
        if missing_runtime_keys:
            errors.append(f"runtime is missing required keys: {sorted(missing_runtime_keys)}")
        if runtime.get("slot") != "m4a4":
            errors.append(f"runtime.slot must be 'm4a4', got: '{runtime.get('slot')}'")
        if runtime.get("modelname") != "weapons/v_rif_m4a1.mdl":
            errors.append(f"runtime.modelname must be 'weapons/v_rif_m4a1.mdl', got: '{runtime.get('modelname')}'")
        addon = runtime.get("active_addon")
        if not isinstance(addon, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", addon or "") or addon in {".", ".."}:
            errors.append("runtime.active_addon must be a single safe addon directory name")
        if runtime.get("active_addon") != EXPECTED_RUNTIME_ADDON:
            errors.append(f"runtime.active_addon must be '{EXPECTED_RUNTIME_ADDON}', got: '{runtime.get('active_addon')}'")
        if runtime.get("migi_write_policy") != EXPECTED_MIGI_WRITE_POLICY:
            errors.append(f"runtime.migi_write_policy must be '{EXPECTED_MIGI_WRITE_POLICY}', got: '{runtime.get('migi_write_policy')}'")
    field_consumption["runtime"] = {
        "consumer": "manifest_contract_and_pipeline_runtime_gate",
        "values": runtime if isinstance(runtime, dict) else None,
    }

    # 5. Material Policy
    mat_policy = manifest.get("material_policy")
    if not isinstance(mat_policy, dict):
        errors.append("material_policy must be a dictionary")
    else:
        unknown_mat_keys = set(mat_policy.keys()) - ALLOWED_MATERIAL_POLICY_KEYS
        missing_mat_keys = REQUIRED_MATERIAL_POLICY_KEYS - set(mat_policy.keys())
        if unknown_mat_keys:
            errors.append(f"material_policy contains unrecognized keys: {sorted(unknown_mat_keys)}")
        if missing_mat_keys:
            errors.append(f"material_policy is missing required keys: {sorted(missing_mat_keys)}")
        if mat_policy.get("classification") != "EXTERNAL_REFERENCE / PROTOTYPE MATERIAL":
            errors.append(f"material_policy.classification must be 'EXTERNAL_REFERENCE / PROTOTYPE MATERIAL', got: '{mat_policy.get('classification')}'")
        if mat_policy.get("source_kind") != "external_goldsrc_cs16_reference":
            errors.append("material_policy.source_kind must be 'external_goldsrc_cs16_reference'")
        if mat_policy.get("final_cf_material") is not False:
            errors.append(f"material_policy.final_cf_material must be false, got: {mat_policy.get('final_cf_material')}")
        if mat_policy.get("final_release_allowed") is not False:
            errors.append(f"material_policy.final_release_allowed must be false, got: {mat_policy.get('final_release_allowed')}")
        if not isinstance(mat_policy.get("purpose"), str) or not mat_policy.get("purpose", "").strip():
            errors.append("material_policy.purpose must be a non-empty string")
    field_consumption["material_policy"] = {
        "consumer": "manifest_contract_and_pipeline_material_gate",
        "values": mat_policy if isinstance(mat_policy, dict) else None,
    }

    # 6. Inputs validation (path, sha256, role)
    inputs = manifest.get("inputs")
    inputs_detail = {}
    if not isinstance(inputs, dict) or not inputs:
        errors.append("inputs must be a non-empty dictionary")
    else:
        for in_key, in_spec in inputs.items():
            if not isinstance(in_spec, dict):
                errors.append(f"input item '{in_key}' must be a dictionary")
                continue
            unknown_in_keys = set(in_spec.keys()) - ALLOWED_INPUT_ITEM_KEYS
            if unknown_in_keys:
                errors.append(f"input '{in_key}' contains unrecognized keys: {sorted(unknown_in_keys)}")
            
            in_path_str = in_spec.get("path")
            in_sha = in_spec.get("sha256")
            in_role = in_spec.get("role")
            in_optional = in_spec.get("optional", False)
            
            if not isinstance(in_path_str, str) or not in_path_str:
                errors.append(f"input '{in_key}' missing valid 'path'")
            if not isinstance(in_sha, str) or not re.match(r"^[0-9a-fA-F]{64}$", in_sha):
                errors.append(f"input '{in_key}' missing valid 64-char hex 'sha256'")
            if not isinstance(in_role, str) or not in_role.strip():
                errors.append(f"input '{in_key}' missing valid 'role'")
            if not isinstance(in_optional, bool):
                errors.append(f"input '{in_key}' optional must be boolean when supplied")
            
            in_path, path_error = _resolve_repo_relative(in_path_str, f"input '{in_key}.path'") if isinstance(in_path_str, str) else (None, f"input '{in_key}' missing valid 'path'")
            if path_error:
                errors.append(path_error)
            exists = in_path.is_file() if in_path else False
            actual_sha = compute_sha256(in_path) if exists else None
            sha_match = (actual_sha == in_sha) if exists and in_sha else False
            
            if not exists and not in_optional:
                errors.append(f"Input file not found on disk: '{in_key}' -> {in_path}")
            elif not sha_match:
                if exists:
                    errors.append(f"Input hash mismatch: '{in_key}' expected {in_sha}, got {actual_sha}")
            
            inputs_detail[in_key] = {
                "path": str(in_path) if in_path else None,
                "role": in_role,
                "optional": in_optional,
                "exists": exists,
                "expected_sha256": in_sha,
                "actual_sha256": actual_sha,
                "hash_match": sha_match,
            }
    field_consumption["inputs"] = {
        "consumer": "manifest_contract_hash_gate_and_pipeline_check",
        "keys": sorted(inputs_detail.keys()),
        "hashes_verified": all(item.get("hash_match") or item.get("optional") for item in inputs_detail.values()) if inputs_detail else False,
    }
    details["inputs"] = inputs_detail

    # 7. Toolchain validation (path, sha256 / role)
    toolchain = manifest.get("toolchain")
    tools_detail = {}
    if not isinstance(toolchain, dict) or not toolchain:
        errors.append("toolchain must be a non-empty dictionary")
    else:
        for t_key, t_spec in toolchain.items():
            if not isinstance(t_spec, dict):
                errors.append(f"toolchain item '{t_key}' must be a dictionary")
                continue
            unknown_t_keys = set(t_spec.keys()) - ALLOWED_TOOL_ITEM_KEYS
            required_t_keys = {"path", "role"}
            if unknown_t_keys:
                errors.append(f"toolchain '{t_key}' contains unrecognized keys: {sorted(unknown_t_keys)}")
            if not required_t_keys.issubset(t_spec.keys()):
                errors.append(f"toolchain '{t_key}' must contain path and role")
            
            t_path_str = t_spec.get("path")
            t_sha = t_spec.get("sha256")
            t_role = t_spec.get("role")
            
            if not isinstance(t_path_str, str) or not t_path_str:
                errors.append(f"toolchain '{t_key}' missing valid 'path'")
            if t_sha is None and not isinstance(t_spec.get("version"), str):
                errors.append(f"toolchain '{t_key}' must contain a version or sha256")
            if t_sha is not None and not isinstance(t_sha, str):
                errors.append(f"toolchain '{t_key}' has invalid 'sha256' type")
            if isinstance(t_sha, str) and not re.match(r"^[0-9a-fA-F]{64}$", t_sha):
                errors.append(f"toolchain '{t_key}' has invalid 'sha256' format")
            if "version" in t_spec and (not isinstance(t_spec.get("version"), str) or not t_spec.get("version", "").strip()):
                errors.append(f"toolchain '{t_key}' has invalid 'version'")
            if not isinstance(t_role, str) or not t_role.strip():
                errors.append(f"toolchain '{t_key}' missing valid 'role'")
            
            t_path, path_error = _resolve_repo_relative(t_path_str, f"toolchain '{t_key}.path'") if isinstance(t_path_str, str) else (None, f"toolchain '{t_key}' missing valid 'path'")
            if path_error:
                errors.append(path_error)
            exists = t_path.is_file() if t_path else False
            actual_sha = compute_sha256(t_path) if exists else None
            sha_match = (actual_sha == t_sha) if (exists and t_sha) else (exists if t_sha is None else False)
            
            if not exists:
                errors.append(f"Tool file not found: '{t_key}' -> {t_path}")
            elif t_sha and not sha_match:
                errors.append(f"Tool hash mismatch: '{t_key}' expected {t_sha}, got {actual_sha}")
            
            tools_detail[t_key] = {
                "path": str(t_path) if t_path else None,
                "role": t_role,
                "exists": exists,
                "expected_sha256": t_sha,
                "actual_sha256": actual_sha,
                "hash_match": sha_match,
            }
    field_consumption["toolchain"] = {
        "consumer": "manifest_contract_tool_provenance_gate",
        "keys": sorted(tools_detail.keys()),
        "hashes_or_versions_verified": all(item.get("hash_match") for item in tools_detail.values()) if tools_detail else False,
    }
    details["toolchain"] = tools_detail

    # 8. Transform
    transform = manifest.get("transform")
    if not isinstance(transform, dict):
        errors.append("transform must be a dictionary")
    else:
        unknown_tr_keys = set(transform.keys()) - ALLOWED_TRANSFORM_KEYS
        missing_tr_keys = REQUIRED_TRANSFORM_KEYS - set(transform.keys())
        if unknown_tr_keys:
            errors.append(f"transform contains unrecognized keys: {sorted(unknown_tr_keys)}")
        if missing_tr_keys:
            errors.append(f"transform is missing required keys: {sorted(missing_tr_keys)}")
        if not transform.get("manifest_ref"):
            errors.append("transform.manifest_ref is required")
        if transform.get("matrix_convention") != EXPECTED_MATRIX_CONVENTION:
            errors.append("transform.matrix_convention does not match the frozen C3 convention")
        if transform.get("source_space") != EXPECTED_SOURCE_SPACE:
            errors.append("transform.source_space does not match the frozen C3 source space")
        if transform.get("target_space") != EXPECTED_TARGET_SPACE:
            errors.append("transform.target_space does not match the frozen C3 target space")
        if transform.get("normal_policy") != EXPECTED_NORMAL_POLICY:
            errors.append("transform.normal_policy does not match the frozen C3 policy")
        if transform.get("winding_policy") != EXPECTED_WINDING_POLICY:
            errors.append("transform.winding_policy does not match the frozen C3 policy")
        ref_path, ref_error = _resolve_repo_relative(transform.get("manifest_ref"), "transform.manifest_ref") if isinstance(transform.get("manifest_ref"), str) else (None, "transform.manifest_ref must be a repository-relative path")
        if ref_error:
            errors.append(ref_error)
        alignment_input = inputs.get("alignment_manifest", {}).get("path") if isinstance(inputs, dict) else None
        if isinstance(alignment_input, str) and isinstance(transform.get("manifest_ref"), str) and Path(alignment_input).as_posix() != Path(transform["manifest_ref"]).as_posix():
            errors.append("transform.manifest_ref must exactly match inputs.alignment_manifest.path")
        if ref_path and ref_path.is_file():
            try:
                ref_data = json.loads(ref_path.read_text(encoding="utf-8"))
                matrix = ref_data.get("matrix_cf_to_source")
                if not isinstance(matrix, list) or len(matrix) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in matrix):
                    errors.append("transform manifest must contain a 4x4 matrix_cf_to_source")
                if ref_data.get("matrix_convention") != transform.get("matrix_convention"):
                    errors.append("transform.matrix_convention disagrees with referenced C3 manifest")
                if ref_data.get("normal_policy") != transform.get("normal_policy"):
                    errors.append("transform.normal_policy disagrees with referenced C3 manifest")
                ref_winding = ref_data.get("winding_policy")
                if not isinstance(ref_winding, str) or not ref_winding.lower().startswith("preserve") or "positive" not in ref_winding.lower():
                    errors.append("referenced C3 manifest must declare preserve winding with a positive determinant")
                if not isinstance(ref_data.get("rotation_determinant"), (int, float)) or ref_data.get("rotation_determinant") <= 0:
                    errors.append("referenced C3 manifest must declare a positive rotation_determinant")
            except Exception as exc:
                errors.append(f"transform.manifest_ref is not valid JSON: {exc}")
    field_consumption["transform"] = {
        "consumer": "manifest_contract_frozen_c3_transform_gate",
        "manifest_ref": transform.get("manifest_ref") if isinstance(transform, dict) else None,
        "policies": {k: transform.get(k) for k in ("matrix_convention", "source_space", "target_space", "normal_policy", "winding_policy")} if isinstance(transform, dict) else None,
    }

    # 9. Mesh Bone Mapping
    mesh_map = manifest.get("mesh_bone_mapping")
    canonical_bones_by_index: dict[int, str] = {}
    ref_input_path = inputs_detail.get("m4a4_reference_report", {}).get("path") if isinstance(inputs_detail, dict) else None
    if ref_input_path:
        try:
            ref_data = json.loads(Path(ref_input_path).read_text(encoding="utf-8"))
            hierarchy = ref_data.get("bones", {}).get("hierarchy", [])
            canonical_bones_by_index = {idx: item.get("name") for idx, item in enumerate(hierarchy) if isinstance(item, dict)}
            if len(canonical_bones_by_index) != 57:
                errors.append(f"M4A4 reference skeleton must contain 57 bones, got {len(canonical_bones_by_index)}")
        except Exception as exc:
            errors.append(f"Unable to load m4a4_reference_report for mesh mapping: {exc}")
    if not isinstance(mesh_map, list) or len(mesh_map) != 9:
        errors.append(f"mesh_bone_mapping must be a list of exactly 9 mesh group definitions, got: {len(mesh_map) if isinstance(mesh_map, list) else type(mesh_map)}")
    else:
        seen_groups: set[str] = set()
        for idx, item in enumerate(mesh_map):
            if not isinstance(item, dict):
                errors.append(f"mesh_bone_mapping[{idx}] must be a dictionary")
                continue
            unknown_m_keys = set(item.keys()) - ALLOWED_MESH_MAP_KEYS
            missing_m_keys = REQUIRED_MESH_MAP_KEYS - set(item.keys())
            if unknown_m_keys:
                errors.append(f"mesh_bone_mapping[{idx}] contains unrecognized keys: {sorted(unknown_m_keys)}")
            if missing_m_keys:
                errors.append(f"mesh_bone_mapping[{idx}] missing required keys: {sorted(missing_m_keys)}")
            group = item.get("group")
            bone_index = item.get("bone_index")
            bone = item.get("bone")
            fallback = item.get("static_fallback")
            triangles = item.get("expected_triangles")
            if not isinstance(group, str) or not group.strip():
                errors.append(f"mesh_bone_mapping[{idx}].group must be a non-empty string")
            elif group in seen_groups:
                errors.append(f"mesh_bone_mapping contains duplicate group '{group}'")
            else:
                seen_groups.add(group)
            if not isinstance(bone_index, int) or isinstance(bone_index, bool) or bone_index < 0:
                errors.append(f"mesh_bone_mapping[{idx}].bone_index must be a non-negative integer")
            elif canonical_bones_by_index and bone_index not in canonical_bones_by_index:
                errors.append(f"mesh_bone_mapping[{idx}].bone_index {bone_index} is outside the 57-bone reference")
            if not isinstance(bone, str) or not bone.strip():
                errors.append(f"mesh_bone_mapping[{idx}].bone must be a non-empty string")
            elif canonical_bones_by_index and isinstance(bone_index, int) and canonical_bones_by_index.get(bone_index) != bone:
                errors.append(f"mesh_bone_mapping[{idx}] bone/index mismatch: index {bone_index} is '{canonical_bones_by_index.get(bone_index)}', not '{bone}'")
            if not isinstance(fallback, bool):
                errors.append(f"mesh_bone_mapping[{idx}].static_fallback must be boolean")
            if not isinstance(triangles, int) or isinstance(triangles, bool) or triangles <= 0:
                errors.append(f"mesh_bone_mapping[{idx}].expected_triangles must be a positive integer")
    field_consumption["mesh_bone_mapping"] = {
        "consumer": "pipeline_check_and_build_smd_binding",
        "mesh_count": len(mesh_map) if isinstance(mesh_map, list) else None,
        "mapping": mesh_map if isinstance(mesh_map, list) else None,
    }

    # 10. Expectations
    exp = manifest.get("expectations")
    if not isinstance(exp, dict):
        errors.append("expectations must be a dictionary")
    else:
        unknown_exp_keys = set(exp.keys()) - ALLOWED_EXPECTATIONS_KEYS
        missing_exp_keys = REQUIRED_EXPECTATIONS_KEYS - set(exp.keys())
        if unknown_exp_keys:
            errors.append(f"expectations contains unrecognized keys: {sorted(unknown_exp_keys)}")
        if missing_exp_keys:
            errors.append(f"expectations is missing required keys: {sorted(missing_exp_keys)}")
        aligned = exp.get("aligned_obj")
        if not isinstance(aligned, dict):
            errors.append("expectations.aligned_obj must be a dictionary")
        else:
            required_aligned = {"vertices", "uvs", "normals", "triangles", "group_count"}
            unknown_aligned = set(aligned.keys()) - required_aligned
            missing_aligned = required_aligned - set(aligned.keys())
            if unknown_aligned:
                errors.append(f"expectations.aligned_obj contains unrecognized keys: {sorted(unknown_aligned)}")
            if missing_aligned:
                errors.append(f"expectations.aligned_obj is missing required keys: {sorted(missing_aligned)}")
            for name in required_aligned:
                value = aligned.get(name)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"expectations.aligned_obj.{name} must be a non-negative integer")
        runtime_exp = exp.get("runtime")
        if not isinstance(runtime_exp, dict):
            errors.append("expectations.runtime must be a dictionary")
        else:
            required_runtime_exp = {"bone_count", "sequence_count", "attachment_count", "material"}
            unknown_runtime_exp = set(runtime_exp.keys()) - required_runtime_exp
            missing_runtime_exp = required_runtime_exp - set(runtime_exp.keys())
            if unknown_runtime_exp:
                errors.append(f"expectations.runtime contains unrecognized keys: {sorted(unknown_runtime_exp)}")
            if missing_runtime_exp:
                errors.append(f"expectations.runtime is missing required keys: {sorted(missing_runtime_exp)}")
            for name in ("bone_count", "sequence_count", "attachment_count"):
                value = runtime_exp.get(name)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"expectations.runtime.{name} must be a non-negative integer")
            if runtime_exp.get("bone_count") != 57:
                errors.append("expectations.runtime.bone_count must be 57")
            if runtime_exp.get("sequence_count") != 9:
                errors.append("expectations.runtime.sequence_count must be 9")
            if runtime_exp.get("attachment_count") != 2:
                errors.append("expectations.runtime.attachment_count must be 2")
            if runtime_exp.get("material") != "rif_m4a1":
                errors.append("expectations.runtime.material must be 'rif_m4a1'")
        sequences = exp.get("sequences")
        if not isinstance(sequences, list) or tuple(sequences) != EXPECTED_SEQUENCE_NAMES:
            errors.append("expectations.sequences must exactly match the official 9-sequence M4A4 reference order")
        attachments = exp.get("attachments")
        if attachments != EXPECTED_ATTACHMENT_MAP:
            errors.append("expectations.attachments must exactly match flash/shelleject reference mapping")
    field_consumption["expectations"] = {
        "consumer": "pipeline_check_and_validate_roundtrip_gate",
        "values": exp if isinstance(exp, dict) else None,
    }

    # 11. Outputs Path Safety
    outputs = manifest.get("outputs")
    outputs_detail = {}
    if not isinstance(outputs, dict) or not outputs:
        errors.append("outputs must be a non-empty dictionary")
    else:
        unknown_out_keys = set(outputs.keys()) - ALLOWED_OUTPUT_KEYS
        missing_out_keys = REQUIRED_OUTPUT_KEYS - set(outputs.keys())
        if unknown_out_keys:
            errors.append(f"outputs contains unrecognized keys: {sorted(unknown_out_keys)}")
        if missing_out_keys:
            errors.append(f"outputs is missing required keys: {sorted(missing_out_keys)}")

        expected_paths = {
            "build_root": ALLOWED_BUILD_SUBTREE,
            "addon": ALLOWED_BUILD_SUBTREE / "addon",
            "p4_work_root": ALLOWED_WORK_SUBTREE,
            "manifest_contract_report": ALLOWED_WORK_SUBTREE / "manifest_contract_report.json",
            "check_report": ALLOWED_WORK_SUBTREE / "check_report.json",
            "build_report": ALLOWED_WORK_SUBTREE / "build_report.json",
            "validation_report": ALLOWED_WORK_SUBTREE / "validation_report.json",
            "material_closure_report": ALLOWED_WORK_SUBTREE / "material_closure_report.json",
            "package_manifest": ALLOWED_WORK_SUBTREE / "staging" / "package_manifest.json",
            "deploy_report": ALLOWED_WORK_SUBTREE / "deploy_report.json",
            "package_root": ALLOWED_WORK_SUBTREE / "package",
            "staging_root": ALLOWED_WORK_SUBTREE / "staging",
            "game_regression_report": ALLOWED_WORK_SUBTREE / "prototype_01_game_regression.json",
            "upstream_trace_report": ALLOWED_WORK_SUBTREE / "upstream_trace_report.json",
        }
        exact_base_keys = {"build_root", "p4_work_root"}
        for out_key, out_val in outputs.items():
            allow_exact = out_key in exact_base_keys
            ok, err_msg = validate_output_path(out_key, out_val, allow_exact_base=allow_exact)
            if not ok:
                errors.append(err_msg)
            resolved_p = (PROJECT_ROOT / out_val).resolve() if isinstance(out_val, str) else None
            expected = expected_paths.get(out_key)
            if resolved_p is not None and expected is not None and resolved_p != expected:
                errors.append(f"Output '{out_key}' must resolve exactly to '{expected}', got '{resolved_p}'")
            if resolved_p is not None and out_key in OUTPUT_FILE_KEYS and resolved_p.exists() and resolved_p.is_dir():
                errors.append(f"Output '{out_key}' must be a file path, but an existing directory was supplied: '{resolved_p}'")
            outputs_detail[out_key] = {
                "declared_path": out_val,
                "resolved_path": str(resolved_p) if resolved_p else None,
                "expected_path": str(expected) if expected else None,
                "is_valid_relative": ok,
                "inside_allowed_subtree": ok,
            }
    field_consumption["outputs"] = {
        "consumer": "pipeline_output_path_resolver_and_destructive_operation_guards",
        "keys": sorted(outputs_detail.keys()),
        "strict_expected_paths": True,
    }
    details["outputs"] = outputs_detail

    is_pass = len(errors) == 0
    report = {
        "schema": "cf2.p4.manifest-contract-report.v1",
        "task_id": "P4-T02",
        "profile_id": manifest.get("profile_id") if isinstance(manifest, dict) else None,
        "manifest_path": str(m_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass": is_pass,
        "errors": errors,
        "field_consumption_matrix": field_consumption,
        "details": details,
    }

    return is_pass, report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate manifest contract and path safety.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "prototype_01_manifest.json",
        help="Path to manifest JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to output manifest contract report JSON",
    )
    args = parser.parse_args()

    manifest_path = args.manifest
    passed, report = validate_manifest_contract(manifest_path)

    safe_default = ALLOWED_WORK_SUBTREE / "manifest_contract_report.json"
    out_path = args.output
    if out_path is not None:
        if out_path.is_absolute():
            print(f"[FAIL] --output must be a repository-relative P4 output path: {out_path}")
            return 1
        output_ok, output_error = validate_output_path("manifest_contract_report", str(out_path))
        if not output_ok:
            print(f"[FAIL] Refusing report output: {output_error}")
            return 1
        out_path = (PROJECT_ROOT / out_path).resolve()
    elif passed:
        # The current P4 contract fixes this report to the safe work subtree.
        out_path = safe_default
    else:
        # Invalid manifests never control where their failure report is written.
        out_path = safe_default

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if passed:
        print(f"[PASS] Manifest contract validation succeeded. Report: {out_path}")
        return 0
    else:
        print(f"[FAIL] Manifest contract validation failed with {len(report['errors'])} error(s):")
        for err in report["errors"]:
            print(f"  - {err}")
        print(f"Report written to: {out_path}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
