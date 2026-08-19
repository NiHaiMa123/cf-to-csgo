# -*- coding: utf-8 -*-
"""Universal single-entry pipeline for CF weapon -> CS:GO Legacy Source 1 porting.

Usage:
  python scripts/weapon_port/pipeline.py check    --manifest <prototype-manifest>
  python scripts/weapon_port/pipeline.py build    --manifest <prototype-manifest>
  python scripts/weapon_port/pipeline.py validate --manifest <prototype-manifest>
  python scripts/weapon_port/pipeline.py package  --manifest <prototype-manifest>
  python scripts/weapon_port/pipeline.py deploy   --manifest <prototype-manifest> --migi-addon <addon>
  python scripts/weapon_port/pipeline.py all      --manifest <prototype-manifest>
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

try:
    from PIL import Image  # type: ignore
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pygame  # type: ignore
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from _paths import game_dir  # noqa: E402
from weapon_port.validate_manifest_contract import (  # noqa: E402
    validate_manifest_contract,
    validate_output_path,
    is_path_contained,
    ALLOWED_BUILD_SUBTREE,
    ALLOWED_WORK_SUBTREE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_hash(path: Path) -> str | None:
    """Hash a file or a deterministic directory tree for run provenance."""
    resolved = path.resolve()
    if resolved.is_file():
        return sha256_file(resolved)
    if not resolved.is_dir():
        return None
    entries: list[dict[str, Any]] = []
    for child in sorted((p for p in resolved.rglob("*") if p.is_file()), key=lambda p: p.relative_to(resolved).as_posix()):
        entries.append({
            "path": child.relative_to(resolved).as_posix(),
            "sha256": sha256_file(child),
            "size": child.stat().st_size,
        })
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def artifact_hashes(paths: list[Path]) -> dict[str, str | None]:
    return {str(path.resolve()): artifact_hash(path) for path in paths}


PACKAGE_MANIFEST_NAME = "package_manifest.json"


def tree_file_entries(root: Path, excluded_names: set[str] | None = None) -> dict[str, dict[str, Any]]:
    """Return a deterministic relative-path -> size/hash map for a package tree."""
    excluded = excluded_names or set()
    if not root.is_dir():
        return {}
    entries: dict[str, dict[str, Any]] = {}
    for child in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        if child.name in excluded:
            continue
        rel = child.relative_to(root).as_posix()
        entries[rel] = {
            "size_bytes": child.stat().st_size,
            "sha256": sha256_file(child),
        }
    return entries


def entries_tree_hash(entries: dict[str, dict[str, Any]]) -> str:
    """Hash only the canonical payload entries, never a manifest that records this hash."""
    encoded = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def report_binding(path: Path, *, run_id: str | None = None) -> dict[str, Any]:
    """Load a report and return the immutable facts package/deploy must bind."""
    binding: dict[str, Any] = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path) if path.is_file() else None,
        "exists": path.is_file(),
    }
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        binding["profile_id"] = data.get("profile_id")
        binding["run_id"] = data.get("run_id") or data.get("upstream", {}).get("run_id")
        if run_id is not None and binding.get("run_id") is not None:
            binding["run_id_match"] = binding["run_id"] == run_id
    return binding


def package_run_binding(manifest: dict[str, Any], manifest_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Verify that all package inputs/reports describe the same current build run."""
    outputs = manifest.get("outputs", {})
    build_path = resolve_proj_path(outputs["build_report"])
    trace_path = resolve_proj_path(outputs["upstream_trace_report"])
    check_path = resolve_proj_path(outputs["check_report"])
    validation_path = resolve_proj_path(outputs["validation_report"])
    errors: list[str] = []

    def load(path: Path) -> dict[str, Any]:
        if not path.is_file():
            errors.append(f"required report is missing: {path}")
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"required report is not valid JSON: {path} ({exc})")
            return {}
        return value if isinstance(value, dict) else {}

    build = load(build_path)
    trace = load(trace_path)
    check = load(check_path)
    validation = load(validation_path)
    run_id = build.get("upstream", {}).get("run_id")
    manifest_abs = str(manifest_path.resolve())
    if not isinstance(run_id, str) or not run_id:
        errors.append("build report has no upstream.run_id")
    if build.get("profile_id") != manifest.get("profile_id"):
        errors.append("build report profile_id does not match manifest")
    if build.get("pass") is not True:
        errors.append("build report is not PASS")
    if trace.get("passed") is not True or trace.get("status") != "PASS":
        errors.append("upstream trace report is not PASS")
    if validation.get("pass") is not True:
        errors.append("P4 validation report is not PASS")
    if trace.get("run_id") != run_id:
        errors.append("build and upstream trace run_id do not match")
    if validation.get("run_id") != run_id:
        errors.append("build and validation run_id do not match")
    if build.get("upstream", {}).get("trace_report") != str(trace_path.resolve()):
        errors.append("build report does not point to the current upstream trace report")
    check_manifest = check.get("details", {}).get("manifest_contract", {}).get("manifest_path")
    if check.get("pass") is not True:
        errors.append("check report is not PASS")
    if check_manifest and str(Path(check_manifest).resolve()) != manifest_abs:
        errors.append("check report was generated for a different manifest")
    check_manifest_record = check.get("manifest", {})
    if check_manifest_record.get("path") and str(Path(check_manifest_record["path"]).resolve()) != manifest_abs:
        errors.append("check report manifest record points to a different manifest")
    if check_manifest_record.get("sha256") and check_manifest_record.get("sha256") != sha256_file(manifest_path):
        errors.append("check report manifest SHA-256 does not match the current manifest")
    if not errors:
        assert isinstance(run_id, str)
        binding = {
            "run_id": run_id,
            "manifest": report_binding(manifest_path),
            "reports": {
                "check": report_binding(check_path, run_id=run_id),
                "build": report_binding(build_path, run_id=run_id),
                "validate": report_binding(validation_path, run_id=run_id),
                "upstream_trace": report_binding(trace_path, run_id=run_id),
            },
        }
        return binding, []
    return None, errors


def obj_summary(path: Path) -> dict[str, Any]:
    """Collect stable OBJ semantics for the upstream trace report."""
    vertices = 0
    uvs = 0
    normals = 0
    triangles = 0
    groups: dict[str, dict[str, Any]] = {}
    current_group = ""
    current_material = "rif_m4a1"
    positions: list[tuple[float, float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "g":
            current_group = parts[1] if len(parts) > 1 else ""
            groups.setdefault(current_group, {"triangles": 0, "material_slots": []})
        elif parts[0] == "usemtl":
            current_material = parts[1] if len(parts) > 1 else "rif_m4a1"
            if current_group:
                slots = groups.setdefault(current_group, {"triangles": 0, "material_slots": []})["material_slots"]
                if current_material not in slots:
                    slots.append(current_material)
        elif parts[0] == "v":
            values = tuple(float(v) for v in parts[1:4])
            if len(values) != 3:
                raise ValueError(f"invalid OBJ vertex line in {path}: {raw}")
            vertices += 1
            positions.append(values)
        elif parts[0] == "vt":
            uvs += 1
        elif parts[0] == "vn":
            normals += 1
        elif parts[0] == "f":
            triangles += 1
            if current_group:
                groups.setdefault(current_group, {"triangles": 0, "material_slots": []})["triangles"] += 1
                slots = groups[current_group]["material_slots"]
                if current_material not in slots:
                    slots.append(current_material)
    return {
        "path": str(path.resolve()),
        "sha256": artifact_hash(path),
        "vertices": vertices,
        "uvs": uvs,
        "normals": normals,
        "triangles": triangles,
        "group_count": len(groups),
        "groups": {name: groups[name] for name in sorted(groups)},
        "material_slots": sorted({slot for group in groups.values() for slot in group["material_slots"]}),
        "bounds": {
            "min": [min(point[i] for point in positions) for i in range(3)] if positions else None,
            "max": [max(point[i] for point in positions) for i in range(3)] if positions else None,
        },
    }


def run_logged_step(
    command: list[str],
    cwd: Path,
    run_root: Path,
    name: str,
    input_paths: list[Path],
    output_paths: list[Path],
) -> dict[str, Any]:
    """Run one upstream command and persist stdout/stderr plus dependency hashes."""
    logs = run_root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout_path = logs / f"{name}.stdout.log"
    stderr_path = logs / f"{name}.stderr.log"
    stdout_path.write_text(proc.stdout or "", encoding="utf-8")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8")
    return {
        "name": name,
        "command": [str(item) for item in command],
        "cwd": str(cwd.resolve()),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": proc.returncode,
        "stdout_log": str(stdout_path.resolve()),
        "stderr_log": str(stderr_path.resolve()),
        "input_hashes": artifact_hashes(input_paths),
        "output_hashes": artifact_hashes(output_paths),
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }


def run_p4_upstream(manifest: dict[str, Any], p4_work_root: Path, manifest_path: Path) -> dict[str, Any]:
    """Regenerate B3 -> C1 -> C3 from the manifest LTB into a fresh run."""
    ltb_spec = manifest["inputs"]["cf_ltb_source"]
    mesh_map_spec = manifest["inputs"]["mesh_map"]
    transform_spec = manifest["inputs"]["alignment_manifest"]
    frozen_aligned_spec = manifest["inputs"]["aligned_obj"]
    ltb_path = resolve_proj_path(ltb_spec["path"])
    mesh_map_path = resolve_proj_path(mesh_map_spec["path"])
    transform_path = resolve_proj_path(transform_spec["path"])
    frozen_aligned_path = resolve_proj_path(frozen_aligned_spec["path"])
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S_%f")
    run_root = p4_work_root / "runs" / run_id
    b3_dir = run_root / "b3_raw"
    c1_dir = run_root / "c1_weapon_only"
    c3_dir = run_root / "c3_aligned"
    b3_dir.mkdir(parents=True, exist_ok=False)
    c1_dir.mkdir(parents=True, exist_ok=False)
    c3_dir.mkdir(parents=True, exist_ok=False)
    steps: list[dict[str, Any]] = []
    failures: list[str] = []
    raw_obj = b3_dir / f"{ltb_path.stem}.obj"
    export_report = b3_dir / f"{ltb_path.stem}_export_report.json"
    weapon_obj = c1_dir / "weapon_only" / f"{ltb_path.stem}_weapon_only.obj"
    c1_report = c1_dir / f"{ltb_path.stem}_c1_split_report.json"
    aligned_obj = c3_dir / f"{ltb_path.stem}_c3_aligned.obj"
    c3_report = c3_dir / "c3_fixed_transform_report.json"
    trace_path = resolve_proj_path(manifest["outputs"]["upstream_trace_report"])

    def require_file(path: Path, label: str) -> None:
        if not path.is_file():
            raise RuntimeError(f"{label} was not generated: {path}")

    try:
        require_file(ltb_path, "manifest LTB")
        require_file(mesh_map_path, "manifest C1 mesh map")
        require_file(transform_path, "manifest frozen C3 transform")
        tool_spec = manifest["toolchain"]["cfrezmanager"]
        cfrez_exe = resolve_proj_path(tool_spec["path"])
        require_file(cfrez_exe, "CFRezManager executable")
        root = resolve_proj_path("data/rf016")
        model_rel = ltb_path.relative_to(root).as_posix()
        export_command = [
            str(cfrez_exe), "--export-obj", "--raw-transform", "--root", str(root),
            "--model", model_rel, "--output", str(raw_obj),
        ]
        step = run_logged_step(export_command, PROJECT_ROOT, run_root, "b3_export", [ltb_path, cfrez_exe], [raw_obj, export_report])
        steps.append(step)
        if step["exit_code"] != 0:
            raise RuntimeError(f"CFRezManager failed with exit code {step['exit_code']}")
        require_file(raw_obj, "B3 raw OBJ")
        require_file(export_report, "B3 export report")

        b3_validator = SCRIPTS_DIR / "cf_ltb" / "validate_b3_obj_roundtrip.py"
        b3_step = run_logged_step(
            [sys.executable, str(b3_validator), "--report", str(export_report), "--obj", str(raw_obj)],
            PROJECT_ROOT, run_root, "b3_roundtrip", [b3_validator, raw_obj, export_report], [raw_obj],
        )
        steps.append(b3_step)
        b3_result = None
        if b3_step["stdout_tail"]:
            try:
                b3_result = json.loads(b3_step["stdout_tail"])
            except json.JSONDecodeError:
                b3_result = {"stdout": b3_step["stdout_tail"]}
        (run_root / "b3_roundtrip_report.json").write_text(json.dumps(b3_result or {"passed": b3_step["exit_code"] == 0}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if b3_step["exit_code"] != 0:
            raise RuntimeError("validate_b3_obj_roundtrip.py failed")

        splitter = SCRIPTS_DIR / "cf_ltb" / "split_c1_meshes.py"
        c1_step = run_logged_step(
            [sys.executable, str(splitter), "--obj", str(raw_obj), "--map", str(mesh_map_path), "--output-dir", str(c1_dir)],
            PROJECT_ROOT, run_root, "c1_split", [splitter, raw_obj, mesh_map_path], [c1_report, c1_dir],
        )
        steps.append(c1_step)
        if c1_step["exit_code"] != 0:
            raise RuntimeError("split_c1_meshes.py failed")
        require_file(weapon_obj, "fresh C1 weapon-only OBJ")
        require_file(c1_report, "fresh C1 split report")
        c1_data = json.loads(c1_report.read_text(encoding="utf-8"))
        weapon_groups = [item.get("group") for item in c1_data.get("weapon_only", [])]
        expected_groups = [item["group"] for item in manifest["mesh_bone_mapping"]]
        if len(weapon_groups) != 9 or set(weapon_groups) != set(expected_groups):
            raise RuntimeError(f"C1 weapon mesh set mismatch: got {weapon_groups}, expected set {expected_groups}")
        if any("Fview-" in str(group) for group in weapon_groups):
            raise RuntimeError("C1 weapon-only output contains a CF arm group")
        arm_groups = {str(item.get("group")) for item in c1_data.get("cf_arms_optional", [])}
        expected_arm_groups = {
            f"{ltb_path.stem}_Fview-hand2",
            f"{ltb_path.stem}_Fview-arm2",
        }
        if arm_groups != expected_arm_groups:
            raise RuntimeError(f"C1 excluded-arm set mismatch: got {sorted(arm_groups)}, expected {sorted(expected_arm_groups)}")

        fixed_transform = SCRIPTS_DIR / "cf_ltb" / "apply_c3_fixed_transform.py"
        c3_step = run_logged_step(
            [
                sys.executable, str(fixed_transform), "--input", str(weapon_obj),
                "--transform-manifest", str(transform_path), "--output", str(aligned_obj),
                "--reference-aligned-obj", str(frozen_aligned_path), "--report", str(c3_report),
            ],
            PROJECT_ROOT, run_root, "c3_fixed_transform", [fixed_transform, weapon_obj, transform_path, frozen_aligned_path], [aligned_obj, c3_report],
        )
        steps.append(c3_step)
        if c3_step["exit_code"] != 0:
            raise RuntimeError("frozen C3 transform/regression check failed")
        require_file(aligned_obj, "fresh C3 aligned OBJ")
    except Exception as exc:
        failures.append(str(exc))

    trace: dict[str, Any] = {
        "schema": "cf2.p4.upstream-trace.v1",
        "task": "P4-T03",
        "profile_id": manifest.get("profile_id"),
        "status": "PASS" if not failures else "FAIL",
        "passed": not failures,
        "run_id": run_id,
        "run_root": str(run_root.resolve()),
        "steps": steps,
        "failures": failures,
        "inputs": {
            "cf_ltb": {"path": str(ltb_path.resolve()), "sha256": artifact_hash(ltb_path)},
            "mesh_map": {"path": str(mesh_map_path.resolve()), "sha256": artifact_hash(mesh_map_path)},
            "alignment_manifest": {"path": str(transform_path.resolve()), "sha256": artifact_hash(transform_path)},
            "frozen_aligned_reference": {"path": str(frozen_aligned_path.resolve()), "sha256": artifact_hash(frozen_aligned_path)},
        },
        "outputs": {
            "b3_raw_obj": {"path": str(raw_obj.resolve()), "sha256": artifact_hash(raw_obj)},
            "b3_export_report": {"path": str(export_report.resolve()), "sha256": artifact_hash(export_report)},
            "c1_weapon_only_obj": {"path": str(weapon_obj.resolve()), "sha256": artifact_hash(weapon_obj)},
            "c1_split_report": {"path": str(c1_report.resolve()), "sha256": artifact_hash(c1_report)},
            "c3_aligned_obj": {"path": str(aligned_obj.resolve()), "sha256": artifact_hash(aligned_obj)},
            "c3_fixed_transform_report": {"path": str(c3_report.resolve()), "sha256": artifact_hash(c3_report)},
        },
        "semantic_stats": {},
        "policies": {
            "source_is_manifest_ltb": True,
            "fresh_run_outputs": True,
            "automatic_icp": False,
            "automatic_normalize": False,
            "per_mesh_center_scale": False,
            "implicit_winding_flip": False,
            "excluded_cf_arm_groups": ["Fview-hand2", "Fview-arm2"],
        },
    }
    for label, path in (("b3_raw", raw_obj), ("c1_weapon_only", weapon_obj), ("c3_aligned", aligned_obj)):
        if path.is_file():
            try:
                trace["semantic_stats"][label] = obj_summary(path)
            except Exception as exc:
                trace["semantic_stats"][label] = {"error": str(exc)}
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        print(f"[FAIL] P4-T03 upstream failed; trace written to {trace_path}")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print(f"[PASS] P4-T03 upstream regenerated run {run_id}; trace written to {trace_path}")
    return {"run_id": run_id, "run_root": run_root, "aligned_obj": aligned_obj, "trace_path": trace_path, "trace": trace}


def resolve_proj_path(rel_or_abs: str | Path) -> Path:
    p = Path(rel_or_abs)
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()


def _read_smd_pose(smd_path: Path) -> dict[int, str]:
    """Read one SMD skeleton pose as ``bone index -> transform suffix``.

    The transform suffix includes the leading whitespace and all six numeric
    values.  Keeping it verbatim avoids introducing a new coordinate,
    precision, or matrix convention into the build-time safety pass.
    """
    lines = smd_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    in_skeleton = False
    first_time_seen = False
    pose: dict[int, str] = {}
    bone_line = re.compile(r"^(\s*)(\d+)(\s+[^\r\n]*)(\r?\n)?$")
    for line in lines:
        token = line.strip().lower()
        if token == "skeleton":
            in_skeleton = True
            continue
        if in_skeleton and token == "triangles":
            break
        if not in_skeleton:
            continue
        if token.startswith("time "):
            if first_time_seen:
                break
            first_time_seen = True
            continue
        if not first_time_seen:
            continue
        match = bone_line.match(line)
        if match:
            pose[int(match.group(2))] = match.group(3)
    if len(pose) != 57:
        raise SystemExit(f"Expected 57 bones in idle SMD pose, found {len(pose)}: {smd_path}")
    return pose


def _neutralize_inspect_fingers(source1: Path) -> dict[str, Any]:
    """Create Inspect clips with official motion and idle finger transforms.

    The prior ``safe_idle_fallback`` made F appear to do nothing because all
    three look-at clips were replaced by the one-frame idle pose.  This pass
    preserves the official clip lengths, hand/weapon motion, and event frames,
    while replacing only the 30 finger-bone transforms with the known-safe
    idle pose.  Official reference files are never modified; the safe copies
    live only in the isolated build tree.
    """
    anim_dir = source1 / "v_rif_m4a1_anims"
    idle_pose = _read_smd_pose(anim_dir / "idle.smd")
    finger_indices = tuple(range(12, 27)) + tuple(range(30, 45))
    generated: list[dict[str, Any]] = []
    bone_line = re.compile(r"^(\s*)(\d+)(\s+[^\r\n]*)(\r?\n)?$")
    for filename in ("lookat01.smd", "lookat01_prepare.smd", "lookat01_loop.smd"):
        source = anim_dir / filename
        target = anim_dir / filename.replace(".smd", "_safe.smd")
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        in_skeleton = False
        replaced = 0
        output: list[str] = []
        for line in lines:
            token = line.strip().lower()
            if token == "skeleton":
                in_skeleton = True
            elif in_skeleton and token == "triangles":
                in_skeleton = False
            if in_skeleton:
                match = bone_line.match(line)
                if match and int(match.group(2)) in finger_indices:
                    bone_index = int(match.group(2))
                    newline = match.group(4) or ""
                    line = f"{match.group(1)}{bone_index}{idle_pose[bone_index]}{newline}"
                    replaced += 1
            output.append(line)
        if replaced == 0:
            raise SystemExit(f"Inspect safety pass changed no finger bones: {source}")
        target.write_text("".join(output), encoding="utf-8")
        generated.append({
            "source": filename,
            "output": target.name,
            "finger_lines_replaced": replaced,
        })
    return {
        "finger_bone_indices": list(finger_indices),
        "generated": generated,
    }


def apply_inspect_policy(qc_text: str, policy: str, source1: Path) -> tuple[str, dict[str, Any]]:
    """Apply an explicit Prototype Inspect policy without touching references."""
    if policy == "official":
        return qc_text, {"mode": "official", "replaced_sequences": []}
    if policy == "safe_idle_fallback":
        # Keep the old CLI spelling reproducible, but no longer produce a
        # no-op Inspect.  It now aliases the motion-preserving safety pass.
        policy = "safe_finger_neutralized"
    if policy != "safe_finger_neutralized":
        raise SystemExit(f"Unsupported Inspect policy: {policy}")

    safety_report = _neutralize_inspect_fingers(source1)
    replaced: list[str] = []
    for sequence_name in ("lookat01", "lookat01_prepare", "lookat01_loop"):
        pattern = re.compile(
            rf'(\$sequence\s+"{re.escape(sequence_name)}"\s*\{{\s*)"[^"]+\.smd"',
            flags=re.IGNORECASE,
        )

        def replacement(match: re.Match[str]) -> str:
            replaced.append(sequence_name)
            safe_name = f"v_rif_m4a1_anims\\{sequence_name}_safe.smd"
            return f'{match.group(1)}"{safe_name}"'

        qc_text, count = pattern.subn(replacement, qc_text, count=1)
        if count != 1:
            raise SystemExit(f"Inspect policy could not find QC sequence body: {sequence_name}")
    return qc_text, {
        "mode": policy,
        "replaced_sequences": replaced,
        **safety_report,
    }


def resolve_deploy_target(addon_arg: str | None, migi_addons_root: Path, allow_custom: bool = False) -> tuple[Path | None, str | None]:
    """Resolve a deploy target without permitting root/parent/name escapes."""
    if not addon_arg or not addon_arg.strip():
        return None, "Deploy requires explicit --migi-addon target folder name"
    raw = addon_arg.strip()
    root = migi_addons_root.resolve()
    has_path_syntax = Path(raw).is_absolute() or "/" in raw or "\\" in raw or ":" in raw
    if has_path_syntax:
        if not allow_custom:
            return None, f"Ordinary deploy only accepts a single folder name inside MIGI addons root ({root}). Got: '{raw}'"
        target = Path(raw).resolve()
        if target == root or not is_path_contained(target, root):
            return None, f"Deploy target '{target}' must be a strict descendant of MIGI addons root '{root}'"
        return target, None
    if raw in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", raw):
        return None, f"Ordinary deploy addon must be one safe directory name, got: '{raw}'"
    target = (root / raw).resolve()
    if target.parent != root or target == root:
        return None, f"Deploy target '{target}' must be a direct child of MIGI addons root '{root}'"
    return target, None


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    resolved = resolve_proj_path(manifest_path)
    if not resolved.is_file():
        raise SystemExit(f"Manifest not found: {resolved}")
    
    passed, report = validate_manifest_contract(resolved)
    if not passed:
        err_msg = "\n".join(f"  - {e}" for e in report["errors"])
        raise SystemExit(f"Manifest contract validation failed for {resolved}:\n{err_msg}")
    
    return json.loads(resolved.read_text(encoding="utf-8"))


def smd_prefix(reference_smd: Path) -> list[str]:
    lines = reference_smd.read_text(encoding="utf-8", errors="replace").splitlines()
    triangle_at = next(i for i, line in enumerate(lines) if line.strip().lower() == "triangles")
    return lines[:triangle_at]


def parse_obj(path: Path, selected_groups: tuple[str, ...]) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, str, list[tuple[int, int, int]]]],
]:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces: list[tuple[str, str, list[tuple[int, int, int]]]] = []
    group = ""
    material = "rif_m4a1"
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "vt":
            uvs.append(tuple(map(float, parts[1:3])))
        elif parts[0] == "vn":
            normals.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "g":
            group = parts[1] if len(parts) > 1 else ""
        elif parts[0] == "usemtl":
            material = parts[1] if len(parts) > 1 else "rif_m4a1"
        elif parts[0] == "f" and group in selected_groups:
            refs: list[tuple[int, int, int]] = []
            for token in parts[1:]:
                fields = token.split("/")
                if len(fields) != 3 or not all(fields):
                    raise ValueError(f"Pipeline requires v/vt/vn faces, got: {raw}")
                refs.append(tuple(int(value) - 1 for value in fields))
            if len(refs) != 3:
                raise ValueError(f"Pipeline requires triangulated OBJ, got {len(refs)} corners")
            faces.append((group, material, refs))
    if not faces:
        raise ValueError(f"Selected groups not found in OBJ: {selected_groups}")
    return vertices, uvs, normals, faces


def smd_primary_bone_counts(path: Path) -> dict[int, int]:
    counts: Counter[int] = Counter()
    in_triangles = False
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line == "triangles":
            in_triangles = True
            continue
        if in_triangles and line == "end":
            break
        fields = line.split()
        if in_triangles and len(fields) >= 9 and fields[0].lstrip("-").isdigit():
            counts[int(fields[0])] += 1
    return dict(sorted(counts.items()))


def smd_bone_motion(path: Path, bone_index: int) -> dict[str, Any]:
    samples: list[list[float]] = []
    in_skeleton = False
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line == "skeleton":
            in_skeleton = True
            continue
        if in_skeleton and line == "end":
            break
        fields = line.split()
        if in_skeleton and len(fields) >= 7 and fields[0].lstrip("-").isdigit() and int(fields[0]) == bone_index:
            samples.append([float(value) for value in fields[1:7]])
    if not samples:
        raise ValueError(f"bone {bone_index} has no samples in {path}")
    first = samples[0]
    max_delta = max(abs(value - first[index]) for sample in samples for index, value in enumerate(sample))
    return {
        "path": str(path),
        "bone_index": bone_index,
        "sample_count": len(samples),
        "max_component_delta": max_delta,
    }


def mdl_header(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    i32 = lambda offset: int.from_bytes(data[offset:offset + 4], "little", signed=True)
    return {
        "magic": data[:4].decode("ascii", errors="replace"),
        "version": i32(4),
        "internal_name": data[12:76].split(b"\0", 1)[0].decode("ascii", errors="replace"),
        "bone_count": i32(156),
        "local_animation_count": i32(180),
        "local_sequence_count": i32(188),
        "size_bytes": len(data),
        "sha256": sha256_file(path),
    }


def run_vtfcmd(vtfcmd_exe: Path, source_png: Path, material_dir: Path, output_name: str, log_dir: Path, log_stem: str) -> Path:
    process = subprocess.run(
        [str(vtfcmd_exe), "-file", str(source_png), "-output", str(material_dir), "-format", "dxt1", "-version", "7.4"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"{log_stem}.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (log_dir / f"{log_stem}.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    generated = material_dir / f"{source_png.stem}.vtf"
    target = material_dir / output_name
    if process.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed for {source_png} (exit code {process.returncode}); inspect {log_stem} logs")
    generated.replace(target)
    return target


def process_textures(source_diffuse: Path, derived_dir: Path) -> tuple[Path, Path]:
    derived_dir.mkdir(parents=True, exist_ok=True)
    base_png = derived_dir / "bornbeast_base.png"
    selfillum_png = derived_dir / "bornbeast_selfillum_mask.png"

    if HAS_PIL:
        source_rgb = Image.open(source_diffuse).convert("RGB")
        source_rgb.save(base_png)
        mask_values = []
        for r, g, b in source_rgb.getdata():
            other = max(g, b)
            if r < 72 or r < g * 1.55 or r < b * 1.55:
                mask_values.append(0)
            else:
                mask_values.append(max(0, min(255, round((r - other) * 2.75))))
        selfillum = Image.new("L", source_rgb.size)
        selfillum.putdata(mask_values)
        selfillum.save(selfillum_png)
    elif HAS_PYGAME:
        surf = pygame.image.load(str(source_diffuse))
        w, h = surf.get_size()
        illum = pygame.Surface((w, h))
        for y in range(h):
            for x in range(w):
                r, g, b, _ = surf.get_at((x, y))
                other = max(g, b)
                if r < 72 or r < g * 1.55 or r < b * 1.55:
                    val = 0
                else:
                    val = max(0, min(255, round((r - other) * 2.75)))
                illum.set_at((x, y), (val, val, val, 255))
        pygame.image.save(surf, str(base_png))
        pygame.image.save(illum, str(selfillum_png))
    else:
        raise SystemExit("Neither Pillow (PIL) nor pygame-ce is available for image processing.")

    return base_png, selfillum_png


# =========================================================================
# Subcommand: check
# =========================================================================
def cmd_check(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running pipeline 'check' for {manifest.get('profile_id')} ({manifest_path.name})...")
    report_items: dict[str, Any] = {}
    errors: list[str] = []

    # 1. Manifest Contract and Path Safety Validation
    contract_passed, contract_report = validate_manifest_contract(manifest_path)
    if not contract_passed:
        errors.extend(contract_report.get("errors", []))
    report_items["manifest_contract"] = contract_report

    # Save manifest contract report
    contract_rep_path = resolve_proj_path(manifest["outputs"].get("manifest_contract_report", "work/m4a1_s_bornbeast/p4_prototype_01/manifest_contract_report.json"))
    contract_rep_path.parent.mkdir(parents=True, exist_ok=True)
    contract_rep_path.write_text(json.dumps(contract_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_items["manifest_controls"] = {
        "status": manifest.get("status"),
        "runtime": manifest.get("runtime"),
        "material_policy": manifest.get("material_policy"),
        "transform": manifest.get("transform"),
        "expectations": manifest.get("expectations"),
        "mesh_bone_mapping": manifest.get("mesh_bone_mapping"),
        "outputs": manifest.get("outputs"),
    }

    # 2. Toolchain executable verification
    studiomdl_exe = args.studiomdl or resolve_proj_path(Path(game_dir()) / "bin" / "studiomdl.exe")
    decompiler_exe = args.decompiler or resolve_proj_path(PROJECT_ROOT / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe")
    vtfcmd_exe = args.vtfcmd or resolve_proj_path(PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe")

    tools_status = {
        "studiomdl": {"path": str(studiomdl_exe), "exists": studiomdl_exe.is_file()},
        "crowbar_decompiler": {"path": str(decompiler_exe), "exists": decompiler_exe.is_file()},
        "vtfcmd": {"path": str(vtfcmd_exe), "exists": vtfcmd_exe.is_file()},
    }
    for tool_name, t_spec in tools_status.items():
        if not t_spec["exists"]:
            errors.append(f"Required tool executable missing: {tool_name} -> {t_spec['path']}")
    report_items["toolchain_executables"] = tools_status

    # 3. Model topology & group check
    aligned_obj_path = resolve_proj_path(manifest["inputs"]["aligned_obj"]["path"])
    if aligned_obj_path.is_file():
        obj_text = aligned_obj_path.read_text(encoding="utf-8", errors="replace")
        v_count = len(re.findall(r"^v\s+", obj_text, re.MULTILINE))
        vt_count = len(re.findall(r"^vt\s+", obj_text, re.MULTILINE))
        vn_count = len(re.findall(r"^vn\s+", obj_text, re.MULTILINE))
        f_count = len(re.findall(r"^f\s+", obj_text, re.MULTILINE))
        groups_in_obj = set(re.findall(r"^g\s+(\S+)", obj_text, re.MULTILINE))
        group_triangle_counts: Counter[str] = Counter()
        group_materials: dict[str, set[str]] = {}
        current_group = None
        current_material = "rif_m4a1"
        for raw_line in obj_text.splitlines():
            parts = raw_line.split()
            if not parts:
                continue
            if parts[0] == "g":
                current_group = parts[1] if len(parts) > 1 else None
                group_materials.setdefault(current_group or "", set())
            elif parts[0] == "usemtl":
                current_material = parts[1] if len(parts) > 1 else "rif_m4a1"
            elif parts[0] == "f" and current_group:
                group_triangle_counts[current_group] += 1
                group_materials.setdefault(current_group, set()).add(current_material)

        exp = manifest.get("expectations", {}).get("aligned_obj", {})
        obj_match = (
            v_count == exp.get("vertices", 3646)
            and vt_count == exp.get("uvs", 3646)
            and vn_count == exp.get("normals", 3646)
            and f_count == exp.get("triangles", 4008)
            and len(groups_in_obj) == exp.get("group_count", 9)
        )
        if not obj_match:
            errors.append(f"OBJ counts mismatch: got v={v_count}, vt={vt_count}, vn={vn_count}, f={f_count}, groups={len(groups_in_obj)}")

        # Check that no CF view arm groups exist in weapon OBJ
        forbidden_arms = {"Fview-hand2", "Fview-arm2", "PV-M4A1_S_BornBeast_Classic_Fview-hand2", "PV-M4A1_S_BornBeast_Classic_Fview-arm2"}
        leaked_arms = forbidden_arms.intersection(groups_in_obj)
        if leaked_arms:
            errors.append(f"CF view arms leaked into weapon OBJ: {leaked_arms}")

        manifest_groups = {item["group"] for item in manifest["mesh_bone_mapping"]}
        if groups_in_obj != manifest_groups:
            errors.append(f"Groups in OBJ do not match manifest mesh_bone_mapping: {groups_in_obj ^ manifest_groups}")
        expected_group_triangles = {item["group"]: item["expected_triangles"] for item in manifest["mesh_bone_mapping"]}
        triangle_mismatches = {
            group: {"expected": expected_group_triangles.get(group), "actual": group_triangle_counts.get(group, 0)}
            for group in sorted(manifest_groups | groups_in_obj)
            if group_triangle_counts.get(group, 0) != expected_group_triangles.get(group)
        }
        if triangle_mismatches:
            errors.append(f"Per-group triangle counts mismatch manifest: {triangle_mismatches}")

        report_items["topology"] = {
            "vertices": v_count,
            "uvs": vt_count,
            "normals": vn_count,
            "triangles": f_count,
            "group_count": len(groups_in_obj),
            "groups": sorted(groups_in_obj),
            "group_triangle_counts": dict(sorted(group_triangle_counts.items())),
            "group_materials": {k: sorted(v) for k, v in sorted(group_materials.items())},
            "expected_group_triangles": expected_group_triangles,
            "triangle_mismatches": triangle_mismatches,
            "leaked_arms": sorted(leaked_arms),
            "pass": obj_match and not leaked_arms and not triangle_mismatches,
        }

    # 4. Canonical skeleton & Reference check
    ref_report_path = resolve_proj_path(manifest["inputs"]["m4a4_reference_report"]["path"])
    if ref_report_path.is_file():
        ref_data = json.loads(ref_report_path.read_text(encoding="utf-8"))
        canonical_bones = {b["name"] for b in ref_data.get("bones", {}).get("hierarchy", [])}
        for item in manifest["mesh_bone_mapping"]:
            if item["bone"] not in canonical_bones:
                errors.append(f"Mapped bone not in canonical M4A4 skeleton: {item['bone']}")
        report_items["skeleton"] = {
            "canonical_bone_count": len(canonical_bones),
            "target_slot": manifest.get("runtime", {}).get("slot"),
            "modelname": manifest.get("runtime", {}).get("modelname"),
        }

    is_pass = len(errors) == 0
    check_report = {
        "schema": "cf2.pipeline.check-report.v1",
        "profile_id": manifest.get("profile_id"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pass": is_pass,
        "errors": errors,
        "details": report_items,
    }

    out_path = resolve_proj_path(manifest["outputs"]["check_report"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(check_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if is_pass:
        print(f"[PASS] Pipeline check succeeded! Report written to {out_path}")
        return 0
    else:
        print(f"[FAIL] Pipeline check failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1


# =========================================================================
# Subcommand: build
# =========================================================================
def cmd_build(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running pipeline 'build' for {manifest.get('profile_id')}...")

    # Run check first
    check_exit = cmd_check(manifest, manifest_path, args)
    if check_exit != 0:
        print("[FAIL] Cannot build: pre-flight check failed.")
        return check_exit

    build_root = resolve_proj_path(manifest["outputs"]["build_root"])
    manifest_addon = resolve_proj_path(manifest["outputs"]["addon"])
    p4_work_root = resolve_proj_path(manifest["outputs"]["p4_work_root"])
    out_build_report = resolve_proj_path(manifest["outputs"]["build_report"])

    # Path safety assert
    if not is_path_contained(build_root, ALLOWED_BUILD_SUBTREE) or build_root == PROJECT_ROOT:
        raise SystemExit(f"Refusing build: build_root {build_root} escapes allowed subtree {ALLOWED_BUILD_SUBTREE}")
    if not is_path_contained(p4_work_root, ALLOWED_WORK_SUBTREE) or p4_work_root == PROJECT_ROOT:
        raise SystemExit(f"Refusing build: p4_work_root {p4_work_root} escapes allowed subtree {ALLOWED_WORK_SUBTREE}")

    p4_work_root.mkdir(parents=True, exist_ok=True)
    # Never leave a previous successful report/artifact tree that could be
    # mistaken for a failed current build.
    if out_build_report.exists():
        out_build_report.unlink()
    if build_root.exists():
        shutil.rmtree(build_root)

    studiomdl_exe = args.studiomdl or resolve_proj_path(Path(game_dir()) / "bin" / "studiomdl.exe")
    decompiler_exe = args.decompiler or resolve_proj_path(PROJECT_ROOT / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe")
    vtfcmd_exe = args.vtfcmd or resolve_proj_path(PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe")

    ref_dir = resolve_proj_path("work/m4a1_s_bornbeast/reference_m4a4")
    # P4-T03 is the build input boundary: never consume the historical aligned
    # OBJ as the model source.  Regenerate B3 -> C1 -> C3 into this run first;
    # the historical aligned OBJ is used only inside the C3 regression report.
    upstream = run_p4_upstream(manifest, p4_work_root, manifest_path)
    aligned_obj_path = upstream["aligned_obj"]
    run_root: Path = upstream["run_root"]
    reference_smd = ref_dir / "decompiled" / "v_m4a1_model.smd"

    # P4-T04 compiles only inside the current T03 run.  The manifest build
    # root is populated later as a fresh compatibility mirror for validate/
    # package; it is never used as a compiler input or working directory.
    source1 = run_root / "source1"
    isolated_game = run_root / "isolated_game"
    isolated_csgo = isolated_game / "csgo"
    addon = run_root / "addon"
    source1.mkdir(parents=True)
    isolated_csgo.mkdir(parents=True)
    addon.mkdir(parents=True)
    steps: list[dict[str, Any]] = []

    shutil.copytree(ref_dir / "decompiled", source1, dirs_exist_ok=True)
    shutil.copy2(Path(game_dir()) / "csgo" / "gameinfo.txt", isolated_csgo / "gameinfo.txt")
    shutil.copytree(ref_dir / "source_vpk" / "materials", isolated_csgo / "materials", dirs_exist_ok=True)

    # Generate SMD with bone bindings from manifest
    binding_map = {item["group"]: (item["bone_index"], item["bone"]) for item in manifest["mesh_bone_mapping"]}
    selected_groups = tuple(item["group"] for item in manifest["mesh_bone_mapping"])

    vertices, uvs, normals, faces = parse_obj(aligned_obj_path, selected_groups)
    smd_lines = smd_prefix(reference_smd)
    smd_lines.append("triangles")

    used_vertices: dict[str, set[int]] = {group: set() for group in selected_groups}
    triangle_counts: dict[str, int] = {group: 0 for group in selected_groups}
    corner_counts: dict[str, int] = {group: 0 for group in selected_groups}

    for group, _source_material, refs in faces:
        bone_index, _bone_name = binding_map[group]
        smd_lines.append("rif_m4a1")
        for vi, ti, ni in refs:
            pos = vertices[vi]
            norm = normals[ni]
            uv = uvs[ti]
            used_vertices[group].add(vi)
            smd_lines.append(
                f"  {bone_index} "
                + " ".join(f"{value:.9f}" for value in (*pos, *norm, uv[0], uv[1]))
                + f" 1 {bone_index} 1.000000"
            )
        triangle_counts[group] += 1
        corner_counts[group] += len(refs)
    smd_lines.append("end")

    mapping_mismatches = {
        item["group"]: {"expected": item["expected_triangles"], "actual": triangle_counts[item["group"]]}
        for item in manifest["mesh_bone_mapping"]
        if triangle_counts[item["group"]] != item["expected_triangles"]
    }
    if mapping_mismatches:
        raise SystemExit(f"Manifest mesh mapping triangle gate failed: {mapping_mismatches}")

    layer_smd_name = "cf_bornbeast_full_m4a4.smd"
    (source1 / layer_smd_name).write_text("\n".join(smd_lines) + "\n", encoding="utf-8")
    steps.append({
        "name": "generate_smd_from_manifest_mapping",
        "command": ["internal", "manifest.mesh_bone_mapping -> fresh C3 OBJ -> SMD"],
        "cwd": str(run_root.resolve()),
        "exit_code": 0,
        "input_hashes": {
            str(aligned_obj_path.resolve()): artifact_hash(aligned_obj_path),
            str(resolve_proj_path(manifest["inputs"]["m4a4_reference_report"]["path"])): artifact_hash(resolve_proj_path(manifest["inputs"]["m4a4_reference_report"]["path"])),
        },
        "output_hashes": {str((source1 / layer_smd_name).resolve()): artifact_hash(source1 / layer_smd_name)},
        "mesh_bone_mapping": [
            {
                "group": item["group"],
                "bone_index": item["bone_index"],
                "bone": item["bone"],
                "static_fallback": item["static_fallback"],
                "triangles": triangle_counts[item["group"]],
                "corners": corner_counts[item["group"]],
                "expected_triangles": item["expected_triangles"],
            }
            for item in manifest["mesh_bone_mapping"]
        ],
    })

    # Update QC
    qc_path = source1 / "v_rif_m4a1.qc"
    qc_text = qc_path.read_text(encoding="utf-8", errors="replace")
    qc_text, count = re.subn(r'studio\s+"v_m4a1_model\.smd"', f'studio "{layer_smd_name}"', qc_text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit("Failed to replace QC bodygroup reference exactly once.")
    inspect_policy = getattr(args, "inspect_policy", "official")
    qc_text, inspect_policy_report = apply_inspect_policy(qc_text, inspect_policy, source1)
    qc_path.write_text(qc_text, encoding="utf-8")

    expected_sequences = list(manifest["expectations"]["sequences"])
    actual_sequences = re.findall(r'\$sequence\s+"([^"]+)"', qc_text, flags=re.IGNORECASE)
    attachment_matches = re.findall(r'\$attachment\s+"([^"]+)"\s+"([^"]+)"', qc_text, flags=re.IGNORECASE)
    actual_attachments = {name: bone for name, bone in attachment_matches}
    expected_attachments = {str(key): value for key, value in manifest["expectations"]["attachments"].items()}
    qc_contract = {
        "modelname": {
            "expected": manifest["runtime"]["modelname"],
            "actual": (re.search(r'\$modelname\s+"([^"]+)"', qc_text, flags=re.IGNORECASE) or [None, None])[1],
        },
        "body_smd": {"expected": layer_smd_name, "actual": layer_smd_name},
        "cdmaterials": {
            "expected_contains": "models\\weapons\\V_models\\rif_m4a1\\",
            "actual": re.findall(r'\$cdmaterials\s+"([^"]+)"', qc_text, flags=re.IGNORECASE),
        },
        "sequences": {"expected": expected_sequences, "actual": actual_sequences},
        "attachments": {"expected": expected_attachments, "actual": actual_attachments},
    }
    qc_contract["pass"] = (
        qc_contract["modelname"]["actual"].replace("\\", "/") == manifest["runtime"]["modelname"]
        and qc_contract["cdmaterials"]["expected_contains"].lower() in qc_text.lower()
        and actual_sequences == expected_sequences
        and actual_attachments == expected_attachments
    )
    qc_contract["inspect_policy"] = inspect_policy_report
    if not qc_contract["pass"]:
        raise SystemExit(f"M4A4 QC contract mismatch: {qc_contract}")
    steps.append({
        "name": "generate_and_check_qc",
        "command": ["internal", "official M4A4 QC + manifest contract"],
        "cwd": str(source1.resolve()),
        "exit_code": 0,
        "input_hashes": {str((ref_dir / "decompiled" / "v_rif_m4a1.qc").resolve()): artifact_hash(ref_dir / "decompiled" / "v_rif_m4a1.qc")},
        "output_hashes": {str(qc_path.resolve()): artifact_hash(qc_path)},
        "qc_contract": qc_contract,
    })

    # Run studiomdl
    print("  -> Compiling MDL with studiomdl.exe...")
    compiled_mdl = isolated_csgo / "models" / "weapons" / "v_rif_m4a1.mdl"
    studiomdl_step = run_logged_step(
        [str(studiomdl_exe), "-game", str(isolated_csgo), str(qc_path)],
        source1,
        run_root,
        "studiomdl",
        [studiomdl_exe, qc_path, isolated_csgo / "gameinfo.txt"],
        [compiled_mdl],
    )
    steps.append(studiomdl_step)
    if studiomdl_step["exit_code"] != 0:
        raise SystemExit(f"studiomdl failed (exit code {studiomdl_step['exit_code']}); inspect {studiomdl_step['stderr_log']}")
    if not compiled_mdl.is_file():
        raise SystemExit(f"studiomdl exited 0 but {compiled_mdl} does not exist")

    # Copy compiled models into this run's addon only.
    copied_files: list[str] = []
    for path in isolated_csgo.rglob("*"):
        if path.is_file() and path.relative_to(isolated_csgo).parts[0].lower() in {"models", "materials"}:
            rel = path.relative_to(isolated_csgo)
            dest = addon / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            copied_files.append(rel.as_posix())

    # Compile material VTFs & VMT (Prototype Material Policy strictly)
    print("  -> Compiling prototype textures and materials...")
    material_dir = addon / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    material_dir.mkdir(parents=True, exist_ok=True)
    for old_vtf in material_dir.glob("*.vtf"):
        old_vtf.unlink()

    source_diffuse = resolve_proj_path(manifest["inputs"]["external_diffuse"]["path"])
    derived_dir = p4_work_root / "derived_textures"
    base_png, selfillum_png = process_textures(source_diffuse, derived_dir)
    steps.append({
        "name": "derive_prototype_textures",
        "command": ["internal", "process_textures", "EXTERNAL_REFERENCE / PROTOTYPE MATERIAL"],
        "cwd": str(p4_work_root.resolve()),
        "exit_code": 0,
        "input_hashes": {str(source_diffuse.resolve()): artifact_hash(source_diffuse)},
        "output_hashes": artifact_hashes([base_png, selfillum_png]),
    })

    def run_build_vtfcmd(source_png: Path, output_name: str, step_name: str) -> Path:
        generated = material_dir / f"{source_png.stem}.vtf"
        target = material_dir / output_name
        step = run_logged_step(
            [str(vtfcmd_exe), "-file", str(source_png), "-output", str(material_dir), "-format", "dxt1", "-version", "7.4"],
            PROJECT_ROOT,
            run_root,
            step_name,
            [vtfcmd_exe, source_png],
            [generated],
        )
        steps.append(step)
        if step["exit_code"] != 0 or not generated.is_file():
            raise SystemExit(f"VTFCmd failed for {source_png} (exit code {step['exit_code']}); inspect {step['stderr_log']}")
        generated.replace(target)
        step["renamed_output"] = str(target.resolve())
        step["renamed_output_sha256"] = artifact_hash(target)
        return target

    run_build_vtfcmd(base_png, "rif_m4a1.vtf", "vtfcmd_base")
    run_build_vtfcmd(selfillum_png, "rif_m4a1_selfillum.vtf", "vtfcmd_selfillum")

    vmt_path = material_dir / "rif_m4a1.vmt"
    vmt_path.write_text(
        '"VertexLitGeneric"\n{\n'
        '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
        '\t"$phong" "1"\n'
        '\t"$phongboost" "0.55"\n'
        '\t"$phongexponent" "22"\n'
        '\t"$phongfresnelranges" "[0.2 0.45 1.0]"\n'
        '\t"$phongalbedotint" "1"\n'
        '\t"$selfillum" "1"\n'
        '\t"$selfillummask" "models/weapons/v_models/rif_m4a1/rif_m4a1_selfillum"\n'
        '\t"$selfillumtint" "[1.0 0.08 0.035]"\n'
        '}\n',
        encoding="utf-8",
    )
    steps.append({
        "name": "write_prototype_vmt",
        "command": ["internal", "write VMT under EXTERNAL_REFERENCE / PROTOTYPE MATERIAL policy"],
        "cwd": str(run_root.resolve()),
        "exit_code": 0,
        "input_hashes": {},
        "output_hashes": {str(vmt_path.resolve()): artifact_hash(vmt_path)},
    })

    # Roundtrip decompile check
    print("  -> Running round-trip decompile verification...")
    roundtrip_dir = run_root / "compiled_decompiled"
    roundtrip_dir.mkdir(parents=True, exist_ok=True)
    decompile_step = run_logged_step(
        [str(decompiler_exe), str(compiled_mdl), str(roundtrip_dir)],
        run_root,
        run_root,
        "roundtrip_decompile",
        [decompiler_exe, compiled_mdl],
        [roundtrip_dir],
    )
    steps.append(decompile_step)
    if decompile_step["exit_code"] != 0:
        raise SystemExit(f"CrowbarDecompiler failed (exit code {decompile_step['exit_code']}); inspect {decompile_step['stderr_log']}")

    report_script = SCRIPTS_DIR / "csgo_pack" / "report_m4a1_s_reference.py"
    report_step = run_logged_step(
        [
            sys.executable,
            str(report_script),
            "--reference-dir", str(roundtrip_dir),
            "--weapon", "M4A4",
            "--expected-modelname", r"weapons\v_rif_m4a1.mdl",
            "--schema", "cf2.m4a4.pipeline-roundtrip.v1",
        ],
        run_root,
        run_root,
        "roundtrip_report",
        [report_script, roundtrip_dir],
        [roundtrip_dir / "reference_report.json"],
    )
    steps.append(report_step)
    if report_step["exit_code"] != 0:
        raise SystemExit(f"report_m4a1_s_reference.py failed on round-trip decompile; inspect {report_step['stderr_log']}")

    roundtrip_json = json.loads((roundtrip_dir / "reference_report.json").read_text(encoding="utf-8"))
    header_info = mdl_header(compiled_mdl)

    expected_primary_corners: Counter[int] = Counter()
    for item in manifest["mesh_bone_mapping"]:
        expected_primary_corners[item["bone_index"]] += corner_counts[item["group"]]
    actual_primary_corners = smd_primary_bone_counts(source1 / layer_smd_name)
    if actual_primary_corners != dict(sorted(expected_primary_corners.items())):
        raise SystemExit(
            f"Fresh SMD primary bone corner distribution mismatch: "
            f"got {actual_primary_corners}, expected {dict(sorted(expected_primary_corners.items()))}"
        )

    for step in steps:
        step.setdefault("stdout_log", None)
        step.setdefault("stderr_log", None)

    # Populate the historical build_root only after the isolated run has
    # succeeded.  These are fresh copies from this run, never inputs to it.
    build_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source1, build_root / "source1", dirs_exist_ok=True)
    shutil.copytree(isolated_game, build_root / "game_root", dirs_exist_ok=True)
    shutil.copytree(roundtrip_dir, build_root / "compiled_decompiled", dirs_exist_ok=True)
    shutil.copytree(addon, manifest_addon, dirs_exist_ok=True)

    build_outputs = [source1, isolated_game, addon, compiled_mdl, roundtrip_dir, manifest_addon]

    build_report = {
        "schema": "cf2.pipeline.build-report.v1",
        "profile_id": manifest.get("profile_id"),
        "manifest": {
            "path": str(manifest_path.resolve()),
            "sha256": sha256_file(manifest_path),
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "build_root": str(build_root),
        "addon_root": str(addon),
        "compatibility_mirror": {
            "build_root": str(build_root),
            "addon_root": str(manifest_addon),
            "source1": str((build_root / "source1").resolve()),
            "isolated_game": str((build_root / "game_root").resolve()),
            "source": "current run only",
        },
        "run_artifacts": {
            "run_root": str(run_root.resolve()),
            "source1": str(source1.resolve()),
            "isolated_game": str(isolated_game.resolve()),
            "addon": str(addon.resolve()),
            "hashes": artifact_hashes(build_outputs),
        },
        "upstream": {
            "task": "P4-T03",
            "run_id": upstream["run_id"],
            "run_root": str(upstream["run_root"]),
            "trace_report": str(upstream["trace_path"]),
            "aligned_obj": str(aligned_obj_path),
            "aligned_obj_sha256": artifact_hash(aligned_obj_path),
        },
        "compiled_mdl": header_info,
        "steps": steps,
        "mesh_bone_mapping": [
            {
                "group": item["group"],
                "bone_index": item["bone_index"],
                "bone": item["bone"],
                "static_fallback": item["static_fallback"],
                "triangles": triangle_counts[item["group"]],
                "corners": corner_counts[item["group"]],
                "used_vertex_count": len(used_vertices[item["group"]]),
                "expected_triangles": item["expected_triangles"],
            }
            for item in manifest["mesh_bone_mapping"]
        ],
        "primary_bone_corner_distribution": {
            "expected_from_manifest": dict(sorted(expected_primary_corners.items())),
            "actual_smd": actual_primary_corners,
        },
        "qc_contract": qc_contract,
        "inspect_policy": inspect_policy_report,
        "material_policy": manifest["material_policy"],
        "roundtrip_summary": {
            "internal_modelname": roundtrip_json["target"]["internal_modelname"],
            "bone_count": roundtrip_json["bones"]["count"],
            "sequence_count": len(roundtrip_json["sequences"]),
            "attachment_count": len(roundtrip_json["attachments"]),
            "materials": roundtrip_json["materials"]["smd_materials"],
        },
        "pass": True,
    }

    out_build_report.parent.mkdir(parents=True, exist_ok=True)
    out_build_report.write_text(json.dumps(build_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[PASS] Pipeline build succeeded! Report written to {out_build_report}")
    return 0


# =========================================================================
# Subcommand: validate
# =========================================================================
def cmd_validate(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running pipeline 'validate' for {manifest.get('profile_id')}...")
    validator_script = SCRIPTS_DIR / "weapon_port" / "validate_p4_t05.py"
    report_path = resolve_proj_path(manifest["outputs"]["validation_report"])
    proc = subprocess.run(
        [sys.executable, str(validator_script), "--manifest", str(manifest_path.resolve()), "--report", str(report_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode

    # Kept below only as historical implementation context; the authoritative
    # P4 validation is validate_p4_t05.py above.
    errors: list[str] = []
    checks: dict[str, Any] = {}

    build_root = resolve_proj_path(manifest["outputs"]["build_root"])
    addon = resolve_proj_path(manifest["outputs"]["addon"])
    p4_work_root = resolve_proj_path(manifest["outputs"]["p4_work_root"])
    source1 = build_root / "source1"
    qc_file = source1 / "v_rif_m4a1.qc"
    smd_file = source1 / "cf_bornbeast_full_m4a4.smd"

    # 1. Material closure validation
    closure_report_path = resolve_proj_path(manifest["outputs"]["material_closure_report"])
    validator_script = SCRIPTS_DIR / "weapon_port" / "validate_materials.py"
    proc_val_mat = subprocess.run(
        [
            sys.executable,
            str(validator_script),
            "--qc", str(qc_file),
            "--smd", str(smd_file),
            "--addon", str(addon),
            "--report", str(closure_report_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    mat_closure_pass = proc_val_mat.returncode == 0
    if not mat_closure_pass:
        errors.append("Material closure validation failed (SMD -> QC -> VMT -> VTF)")
    checks["material_closure"] = {"pass": mat_closure_pass, "report": str(closure_report_path)}

    # 2. Binary files existence
    mdl_path = addon / "models" / "weapons" / "v_rif_m4a1.mdl"
    vvd_path = addon / "models" / "weapons" / "v_rif_m4a1.vvd"
    vtx_path = addon / "models" / "weapons" / "v_rif_m4a1.dx90.vtx"

    binaries_exist = mdl_path.is_file() and vvd_path.is_file() and vtx_path.is_file()
    if not binaries_exist:
        errors.append(f"Missing compiled binary files in addon: mdl={mdl_path.is_file()}, vvd={vvd_path.is_file()}, vtx={vtx_path.is_file()}")
    checks["binaries"] = {
        "mdl_exists": mdl_path.is_file(),
        "vvd_exists": vvd_path.is_file(),
        "vtx_exists": vtx_path.is_file(),
        "pass": binaries_exist,
    }

    # 3. Model structure & bone distributions
    if mdl_path.is_file():
        header = mdl_header(mdl_path)
        header_ok = (
            header["internal_name"].replace("\\", "/").lower() == "weapons/v_rif_m4a1.mdl"
            and header["bone_count"] == 57
            and header["local_sequence_count"] == 9
        )
        if not header_ok:
            errors.append(f"MDL header mismatch: name={header['internal_name']}, bones={header['bone_count']}, sequences={header['local_sequence_count']}")
        checks["mdl_header"] = {"details": header, "pass": header_ok}

    roundtrip_mesh = build_root / "compiled_decompiled" / "cf_bornbeast_full_m4a4.smd"
    if roundtrip_mesh.is_file():
        primary_bones = smd_primary_bone_counts(roundtrip_mesh)
        expected_bones = {3: 11553, 4: 108, 29: 363}
        bones_ok = primary_bones == expected_bones
        if not bones_ok:
            errors.append(f"Roundtrip primary bone corners mismatch: got {primary_bones}, expected {expected_bones}")
        checks["bone_corners"] = {"actual": primary_bones, "expected": expected_bones, "pass": bones_ok}

    # 4. Bone animation semantics
    ref_dir = resolve_proj_path("work/m4a1_s_bornbeast/reference_m4a4/decompiled/v_rif_m4a1_anims")
    clip_idle = smd_bone_motion(ref_dir / "idle.smd", 4)
    clip_reload = smd_bone_motion(ref_dir / "reload.smd", 4)
    bolt_idle = smd_bone_motion(ref_dir / "idle.smd", 29)
    bolt_draw = smd_bone_motion(ref_dir / "draw.smd", 29)
    bolt_fire = smd_bone_motion(ref_dir / "shoot1.smd", 29)

    anim_ok = (
        clip_idle["max_component_delta"] <= 1e-6
        and clip_reload["max_component_delta"] > 0.1
        and bolt_idle["max_component_delta"] <= 1e-6
        and bolt_fire["max_component_delta"] <= 1e-6
        and bolt_draw["max_component_delta"] > 0.1
    )
    if not anim_ok:
        errors.append("Bone animation motion semantics check failed")
    checks["animation_semantics"] = {
        "clip_idle_delta": clip_idle["max_component_delta"],
        "clip_reload_delta": clip_reload["max_component_delta"],
        "bolt_idle_delta": bolt_idle["max_component_delta"],
        "bolt_fire_delta": bolt_fire["max_component_delta"],
        "bolt_draw_delta": bolt_draw["max_component_delta"],
        "pass": anim_ok,
    }

    # 5. Policy flags check
    is_prototype = (
        manifest.get("final_target_identity") is False
        and manifest.get("final_cf_material") is False
        and manifest.get("material_policy", {}).get("classification") == "EXTERNAL_REFERENCE / PROTOTYPE MATERIAL"
    )
    if not is_prototype:
        errors.append(f"Manifest policy flags must strictly represent Prototype: final_target_identity={manifest.get('final_target_identity')}, final_cf_material={manifest.get('final_cf_material')}, classification={manifest.get('material_policy', {}).get('classification')}")
    checks["policy_flags"] = {"pass": is_prototype, "is_prototype": is_prototype}

    is_pass = len(errors) == 0
    validation_report = {
        "schema": "cf2.pipeline.validation-report.v1",
        "profile_id": manifest.get("profile_id"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pass": is_pass,
        "errors": errors,
        "checks": checks,
    }

    out_val_report = resolve_proj_path(manifest["outputs"]["validation_report"])
    out_val_report.parent.mkdir(parents=True, exist_ok=True)
    out_val_report.write_text(json.dumps(validation_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if is_pass:
        print(f"[PASS] Pipeline validation succeeded! Report written to {out_val_report}")
        return 0
    else:
        print(f"[FAIL] Pipeline validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1


# =========================================================================
# Subcommand: package
# =========================================================================
def cmd_package(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running pipeline 'package' for {manifest.get('profile_id')}...")

    addon = resolve_proj_path(manifest["outputs"]["addon"])
    staging_root = resolve_proj_path(manifest["outputs"]["staging_root"])
    package_root = resolve_proj_path(manifest["outputs"]["package_root"])
    out_manifest = resolve_proj_path(manifest["outputs"]["package_manifest"])
    deploy_report_path = resolve_proj_path(manifest["outputs"]["deploy_report"])

    # Path safety assert
    for label, path in (("staging_root", staging_root), ("package_root", package_root), ("package_manifest", out_manifest), ("deploy_report", deploy_report_path)):
        if not is_path_contained(path, ALLOWED_WORK_SUBTREE) or path == PROJECT_ROOT:
            raise SystemExit(f"Refusing package: {label} {path} escapes allowed subtree {ALLOWED_WORK_SUBTREE}")
    if not addon.is_dir() or not tree_file_entries(addon, {PACKAGE_MANIFEST_NAME}):
        print(f"[FAIL] Cannot package: addon is missing or empty: {addon}")
        return 1

    # Package is a rebuild boundary.  Remove only generated P4 package roots so
    # a stale staging tree cannot be mistaken for the current build.
    if staging_root.exists():
        shutil.rmtree(staging_root)
    if package_root.exists():
        shutil.rmtree(package_root)
    if deploy_report_path.exists():
        deploy_report_path.unlink()

    check_exit = cmd_check(manifest, manifest_path, args)
    if check_exit != 0:
        print("[FAIL] Cannot package: pre-flight check failed.")
        return check_exit
    val_exit = cmd_validate(manifest, manifest_path, args)
    if val_exit != 0:
        print("[FAIL] Cannot package: validation failed.")
        return val_exit

    run_binding, binding_errors = package_run_binding(manifest, manifest_path)
    if run_binding is None:
        print("[FAIL] Cannot package: report/run binding failed:")
        for error in binding_errors:
            print(f"  - {error}")
        return 1

    staging_root.mkdir(parents=True, exist_ok=True)
    package_root.mkdir(parents=True, exist_ok=True)

    shutil.copytree(addon, package_root, dirs_exist_ok=True)
    # The MIGI staging is derived from the project package, never from a
    # separately assembled or previously deployed directory.
    shutil.copytree(package_root, staging_root, dirs_exist_ok=True)

    # package_manifest.json is deliberately excluded from payload hashes: a
    # manifest that records its own hash would be circular.  The policy and
    # the manifest's external SHA-256 are recorded in deploy_report instead.
    source_entries = tree_file_entries(addon, {PACKAGE_MANIFEST_NAME})
    staged_entries = tree_file_entries(staging_root, {PACKAGE_MANIFEST_NAME})
    package_entries = tree_file_entries(package_root, {PACKAGE_MANIFEST_NAME})
    if source_entries != staged_entries or source_entries != package_entries:
        print("[FAIL] Package copy changed payload content before manifest creation.")
        return 1
    staged_files = [
        {"relative_path": rel, **entry}
        for rel, entry in sorted(staged_entries.items())
    ]
    payload_hash = entries_tree_hash(staged_entries)

    package_manifest = {
        "schema": "cf2.pipeline.package-manifest.v2",
        "profile_id": manifest.get("profile_id"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_binding": run_binding,
        "source_addon": {
            "path": str(addon.resolve()),
            "file_count": len(source_entries),
            "payload_tree_sha256": entries_tree_hash(source_entries),
        },
        "final_target_identity": manifest.get("final_target_identity", False),
        "final_cf_material": manifest.get("final_cf_material", False),
        "material_classification": manifest.get("material_policy", {}).get("classification"),
        "runtime_slot": manifest.get("runtime", {}).get("slot"),
        "payload": {
            "file_count": len(staged_entries),
            "tree_sha256": payload_hash,
            "package_manifest_excluded": True,
            "excluded_names": [PACKAGE_MANIFEST_NAME],
            "hash_policy": "canonical relative path, size_bytes and sha256; manifest excluded to avoid self-reference",
        },
        "package_roots": {
            "package_root": {"path": str(package_root.resolve()), "payload_tree_sha256": entries_tree_hash(package_entries)},
            "staging_root": {"path": str(staging_root.resolve()), "payload_tree_sha256": entries_tree_hash(staged_entries)},
            "payload_hashes_equal": package_entries == staged_entries,
        },
        "file_count": len(staged_files),
        "files": staged_files,
        "self_hash_policy": {
            "included_in_payload_file_set": False,
            "sha256_recorded_after_write": "deploy_report.json when deploy executes",
            "reason": "including package_manifest.json in its own file list would create a circular hash; deploy_report records the written manifest hash externally",
        },
    }

    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest_text = json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n"
    out_manifest.write_text(manifest_text, encoding="utf-8")

    # Also copy package_manifest into package_root
    (package_root / PACKAGE_MANIFEST_NAME).write_text(manifest_text, encoding="utf-8")

    if out_manifest.read_bytes() != (staging_root / PACKAGE_MANIFEST_NAME).read_bytes():
        print("[FAIL] Staging package_manifest.json is not identical to the declared manifest.")
        return 1
    print(f"[PASS] Package staging completed ({len(staged_files)} payload files). Manifest written to {out_manifest}")
    return 0


# =========================================================================
# Subcommand: deploy
# =========================================================================
def cmd_deploy(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running pipeline 'deploy' for {manifest.get('profile_id')}...")

    migi_addons_root = (Path(game_dir()) / "migi" / "csgo" / "addons").resolve()
    target_dir, target_error = resolve_deploy_target(
        args.migi_addon,
        migi_addons_root,
        allow_custom=getattr(args, "allow_custom_deploy_path", False),
    )
    if target_error:
        print(f"[FAIL] {target_error}")
        return 1
    assert target_dir is not None

    pkg_exit = cmd_package(manifest, manifest_path, args)
    if pkg_exit != 0:
        print("[FAIL] Cannot deploy: packaging failed.")
        return pkg_exit

    staging_root = resolve_proj_path(manifest["outputs"]["staging_root"])
    package_manifest_path = resolve_proj_path(manifest["outputs"]["package_manifest"])
    deploy_report_path = resolve_proj_path(manifest["outputs"]["deploy_report"])
    print(f"  -> Deploy target directory: {target_dir}")

    staging_entries = tree_file_entries(staging_root, {PACKAGE_MANIFEST_NAME})
    staging_hashes = {rel: entry["sha256"] for rel, entry in staging_entries.items()}
    package_manifest_hash = sha256_file(package_manifest_path) if package_manifest_path.is_file() else None

    def write_deploy_report(*, passed: bool, action: str, reason: str | None, before: dict[str, str], after: dict[str, str]) -> None:
        report = {
            "schema": "cf2.pipeline.deploy-report.v1",
            "task_id": "P4-T06",
            "profile_id": manifest.get("profile_id"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pass": passed,
            "action": action,
            "reason": reason,
            "target": str(target_dir),
            "staging_root": str(staging_root),
            "package_manifest": {
                "path": str(package_manifest_path),
                "sha256": package_manifest_hash,
            },
            "payload_hash_policy": {
                "package_manifest_excluded": True,
                "excluded_names": [PACKAGE_MANIFEST_NAME],
            },
            "run_binding": json.loads(package_manifest_path.read_text(encoding="utf-8")).get("run_binding", {}) if package_manifest_path.is_file() else {},
            "staging": {"file_count": len(staging_hashes), "hashes": staging_hashes},
            "target_before": {"file_count": len(before), "hashes": before},
            "target_after": {"file_count": len(after), "hashes": after},
            "post_deploy_hashes_match": after == staging_hashes,
        }
        deploy_report_path.parent.mkdir(parents=True, exist_ok=True)
        deploy_report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if target_dir.exists():
        if not target_dir.is_dir():
            write_deploy_report(passed=False, action="rejected", reason="target_is_not_directory", before={}, after={})
            print(f"[FAIL] Refusing to deploy over a non-directory target: {target_dir}")
            return 1
        target_entries = tree_file_entries(target_dir, {PACKAGE_MANIFEST_NAME})
        target_hashes = {rel: entry["sha256"] for rel, entry in target_entries.items()}
        if staging_hashes != target_hashes:
            write_deploy_report(passed=False, action="rejected", reason="different_content", before=target_hashes, after=target_hashes)
            print(f"[FAIL] Refusing to overwrite non-identical existing MIGI addon at: {target_dir}")
            return 1
        write_deploy_report(passed=True, action="verified_existing", reason=None, before=target_hashes, after=target_hashes)
        print("  -> Existing MIGI addon is identical to staging package; deployment verified.")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        for rel, _hash in staging_hashes.items():
            src_file = staging_root / rel
            dst_file = target_dir / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
        
        # Re-verify deployed files from the target, not from copy() success.
        deployed_entries = tree_file_entries(target_dir, {PACKAGE_MANIFEST_NAME})
        deployed_hashes = {rel: entry["sha256"] for rel, entry in deployed_entries.items()}
        if deployed_hashes != staging_hashes:
            write_deploy_report(passed=False, action="created_then_rejected", reason="post_deploy_hash_mismatch", before={}, after=deployed_hashes)
            print("[FAIL] Post-deployment hash verification failed!")
            return 1
        write_deploy_report(passed=True, action="created", reason=None, before={}, after=deployed_hashes)
        print(f"  -> Deployed {len(staging_hashes)} files to {target_dir} and verified hashes.")

    print(f"[PASS] Safe deployment completed to {target_dir}. Game core files untouched.")
    return 0


# =========================================================================
# Subcommand: all
# =========================================================================
def cmd_all(manifest: dict[str, Any], manifest_path: Path, args: argparse.Namespace) -> int:
    print(f"[*] Running entire pipeline for {manifest.get('profile_id')} (check -> build -> validate -> package)...")
    for step_fn in (cmd_check, cmd_build, cmd_validate, cmd_package):
        res = step_fn(manifest, manifest_path, args)
        if res != 0:
            return res
    print(f"[PASS] All pipeline steps completed successfully for {manifest.get('profile_id')}!")
    return 0


# =========================================================================
# Entrypoint
# =========================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "prototype_01_manifest.json",
        help="Path to weapon build manifest JSON",
    )
    common.add_argument("--studiomdl", type=Path, help="Path to studiomdl.exe")
    common.add_argument("--decompiler", type=Path, help="Path to CrowbarDecompiler executable")
    common.add_argument("--vtfcmd", type=Path, help="Path to VTFCmd.exe")
    common.add_argument(
        "--inspect-policy",
        choices=("official", "safe_finger_neutralized", "safe_idle_fallback"),
        default="official",
        help="Inspect/lookat animation policy; safe_finger_neutralized preserves motion while neutralizing finger bones (safe_idle_fallback is a legacy alias)",
    )

    subparsers.add_parser("check", parents=[common], help="Validate inputs and manifest contract without building")
    subparsers.add_parser("build", parents=[common], help="Execute clean deterministic Source 1 compile and material generation")
    subparsers.add_parser("validate", parents=[common], help="Execute post-build automated gates and material closure")
    subparsers.add_parser("package", parents=[common], help="Create staging distribution package and manifest")

    deploy_parser = subparsers.add_parser("deploy", parents=[common], help="Deploy to MIGI addon directory safely")
    deploy_parser.add_argument("--migi-addon", type=str, help="Target MIGI addon folder name (e.g. p_cf_bornbeast_m4a4_p4_review_01)")
    deploy_parser.add_argument("--allow-custom-deploy-path", action="store_true", help="Allow custom deploy path within MIGI addons root")

    subparsers.add_parser("all", parents=[common], help="Run check, build, validate, package sequentially")

    args = parser.parse_args()
    manifest_path = args.manifest
    manifest = load_manifest(manifest_path)

    handlers = {
        "check": cmd_check,
        "build": cmd_build,
        "validate": cmd_validate,
        "package": cmd_package,
        "deploy": cmd_deploy,
        "all": cmd_all,
    }

    handler = handlers.get(args.subcommand)
    if not handler:
        parser.print_help()
        return 1

    return handler(manifest, manifest_path, args)


if __name__ == "__main__":
    sys.exit(main())
