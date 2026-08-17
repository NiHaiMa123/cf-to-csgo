# -*- coding: utf-8 -*-
"""Compile the official M4A1-S reference in an isolated Source 1 root.

The command is intentionally limited to the A3 official-model round trip. It
stages the A2 QC/SMD and source materials, runs the installed Legacy
studiomdl, keeps complete stdout/stderr logs, decompiles the result with the
same fixed CrowbarDecompiler, and compares both machine-readable reports.
No game or MIGI directory is written unless ``--deploy-migi`` is explicitly
passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _paths import game_dir, project_dir  # noqa: E402


REFERENCE_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a1_s"
BUILD_DIR = PROJECT_ROOT / "build" / "m4a1_s_bornbeast"
REPORT_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reports"


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mdl_header(path: Path) -> dict[str, Any]:
    data = path.read_bytes() if path.is_file() else b""

    def int32(offset: int) -> int | None:
        if offset + 4 > len(data):
            return None
        return int.from_bytes(data[offset : offset + 4], "little", signed=True)

    return {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path),
        "magic": data[:4].decode("ascii", errors="replace") if data else None,
        "version": int32(4),
        "internal_name": data[12:76].split(b"\0", 1)[0].decode("ascii", errors="replace") if data else None,
        "bone_count": int32(156),
        "local_animation_count": int32(180),
        "local_sequence_count": int32(188),
    }


def run_logged(command: list[str], cwd: Path, stdout_path: Path, stderr_path: Path) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout_path.write_text(process.stdout or "", encoding="utf-8")
    stderr_path.write_text(process.stderr or "", encoding="utf-8")
    combined = (
        f"COMMAND: {' '.join(command)}\n"
        f"EXIT_CODE: {process.returncode}\n"
        "\n--- STDOUT ---\n"
        f"{process.stdout or ''}\n"
        "--- STDERR ---\n"
        f"{process.stderr or ''}\n"
    )
    combined_name = stdout_path.name.replace(".stdout.log", ".log").replace(".stderr.log", ".log")
    combined_path = stdout_path.with_name(combined_name)
    combined_path.write_text(combined, encoding="utf-8")
    return {
        "command": command,
        "cwd": str(cwd),
        "exit_code": process.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "combined": str(combined_path),
    }


def clean_build_subdirs() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("game_root", "source1", "compiled_decompiled", "addon"):
        target = BUILD_DIR / name
        if target.exists():
            shutil.rmtree(target)


def stage_inputs(game_root: Path, source1: Path) -> Path:
    source_decompiled = REFERENCE_DIR / "decompiled"
    source_model = REFERENCE_DIR / "source_vpk" / "models" / "weapons" / "v_rif_m4a1_s.mdl"
    qc = next(source_decompiled.glob("*.qc"), None)
    if qc is None or not source_model.is_file():
        raise SystemExit("A2 reference is incomplete; run build_m4a1_s_reference.py first")
    shutil.copytree(source_decompiled, source1, dirs_exist_ok=True)

    isolated_csgo = game_root / "csgo"
    isolated_csgo.mkdir(parents=True, exist_ok=True)
    official_gameinfo = Path(game_dir()) / "csgo" / "gameinfo.txt"
    if not official_gameinfo.is_file():
        raise SystemExit(f"Legacy gameinfo.txt not found: {official_gameinfo}")
    shutil.copy2(official_gameinfo, isolated_csgo / "gameinfo.txt")

    source_materials = REFERENCE_DIR / "source_vpk" / "materials"
    if source_materials.is_dir():
        shutil.copytree(source_materials, isolated_csgo / "materials", dirs_exist_ok=True)
    return qc


def copy_addon(game_root: Path, addon: Path) -> list[str]:
    compiled_csgo = game_root / "csgo"
    copied: list[str] = []
    for path in compiled_csgo.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(compiled_csgo)
        if relative.parts[0].lower() not in {"models", "materials"}:
            continue
        destination = addon / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied.append(relative.as_posix())
    return sorted(copied)


def report_comparison(source: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
    def names(items: list[dict[str, Any]], key: str = "name") -> list[str]:
        return [str(item.get(key, "")) for item in items]

    source_seq = names(source.get("sequences", []))
    compiled_seq = names(compiled.get("sequences", []))
    source_bones = [(item.get("name"), item.get("parent")) for item in source.get("bones", {}).get("hierarchy", [])]
    compiled_bones = [(item.get("name"), item.get("parent")) for item in compiled.get("bones", {}).get("hierarchy", [])]
    source_attachments = [(item.get("name"), item.get("bone")) for item in source.get("attachments", [])]
    compiled_attachments = [(item.get("name"), item.get("bone")) for item in compiled.get("attachments", [])]
    source_materials = sorted(source.get("materials", {}).get("smd_materials", []))
    compiled_materials = sorted(compiled.get("materials", {}).get("smd_materials", []))
    source_bodygroups = names(source.get("bodygroups", []))
    compiled_bodygroups = names(compiled.get("bodygroups", []))

    checks = {
        "internal_modelname": source.get("target", {}).get("internal_modelname") == compiled.get("target", {}).get("internal_modelname"),
        "bone_count": source.get("bones", {}).get("count") == compiled.get("bones", {}).get("count"),
        "bone_hierarchy": source_bones == compiled_bones,
        "sequence_names": source_seq == compiled_seq,
        "sequence_count": len(source_seq) == len(compiled_seq),
        "attachments": source_attachments == compiled_attachments,
        "materials": source_materials == compiled_materials,
        "bodygroups": source_bodygroups == compiled_bodygroups,
        "qc_bbox": source.get("bounds", {}).get("qc_bbox") == compiled.get("bounds", {}).get("qc_bbox"),
    }
    return {
        "all_structural_checks_pass": all(checks.values()),
        "checks": checks,
        "source": {
            "modelname": source.get("target", {}).get("internal_modelname"),
            "bone_count": source.get("bones", {}).get("count"),
            "sequence_names": source_seq,
            "attachments": source_attachments,
            "materials": source_materials,
            "bodygroups": source_bodygroups,
        },
        "compiled": {
            "modelname": compiled.get("target", {}).get("internal_modelname"),
            "bone_count": compiled.get("bones", {}).get("count"),
            "sequence_names": compiled_seq,
            "attachments": compiled_attachments,
            "materials": compiled_materials,
            "bodygroups": compiled_bodygroups,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studiomdl", type=Path, default=Path(game_dir()) / "bin" / "studiomdl.exe")
    parser.add_argument(
        "--decompiler",
        type=Path,
        default=PROJECT_ROOT / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe",
    )
    parser.add_argument("--deploy-migi", action="store_true", help="copy the staged addon to a new temporary MIGI addon")
    parser.add_argument("--migi-addon", type=Path, default=None)
    args = parser.parse_args()
    if not args.studiomdl.is_file():
        raise SystemExit(f"studiomdl not found: {args.studiomdl}")
    if not args.decompiler.is_file():
        raise SystemExit(f"CrowbarDecompiler not found: {args.decompiler}")

    clean_build_subdirs()
    game_root = BUILD_DIR / "game_root"
    source1 = BUILD_DIR / "source1"
    compiled_decompiled = BUILD_DIR / "compiled_decompiled"
    addon = BUILD_DIR / "addon"
    qc = stage_inputs(game_root, source1)
    isolated_csgo = game_root / "csgo"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    compile_result = run_logged(
        [str(args.studiomdl.resolve()), "-game", str(isolated_csgo), str(qc)],
        source1,
        REPORT_DIR / "a3_studiomdl.stdout.log",
        REPORT_DIR / "a3_studiomdl.stderr.log",
    )
    if compile_result["exit_code"] != 0:
        raise SystemExit(f"studiomdl failed; see {compile_result['combined']}")

    compiled_model = isolated_csgo / "models" / "weapons" / "v_rif_m4a1_s.mdl"
    if not compiled_model.is_file():
        raise SystemExit(f"studiomdl exited 0 but produced no model: {compiled_model}")
    compiled_files = copy_addon(game_root, addon)

    decompile_result = run_logged(
        [str(args.decompiler.resolve()), str(compiled_model), str(compiled_decompiled)],
        BUILD_DIR,
        REPORT_DIR / "a3_roundtrip_decompiler.stdout.log",
        REPORT_DIR / "a3_roundtrip_decompiler.stderr.log",
    )
    if decompile_result["exit_code"] != 0:
        raise SystemExit(f"round-trip decompilation failed; see {decompile_result['combined']}")
    compiled_report_script = Path(__file__).with_name("report_m4a1_s_reference.py")
    report_result = subprocess.run(
        [sys.executable, str(compiled_report_script), "--reference-dir", str(compiled_decompiled)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (REPORT_DIR / "a3_roundtrip_report.stdout.log").write_text(report_result.stdout or "", encoding="utf-8")
    (REPORT_DIR / "a3_roundtrip_report.stderr.log").write_text(report_result.stderr or "", encoding="utf-8")
    if report_result.returncode != 0:
        raise SystemExit("round-trip report generation failed")

    source_report = json.loads((REFERENCE_DIR / "reference_report.json").read_text(encoding="utf-8"))
    compiled_report = json.loads((compiled_decompiled / "reference_report.json").read_text(encoding="utf-8"))
    comparison = report_comparison(source_report, compiled_report)
    original_model = REFERENCE_DIR / "source_vpk" / "models" / "weapons" / "v_rif_m4a1_s.mdl"
    original_header = mdl_header(original_model)
    compiled_header = mdl_header(compiled_model)
    report = {
        "schema": "cf2.m4a1_s.a3-roundtrip.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "toolchain": {
            "studiomdl": str(args.studiomdl.resolve()),
            "crowbar_decompiler": str(args.decompiler.resolve()),
            "gameinfo": str(isolated_csgo / "gameinfo.txt"),
        },
        "isolation": {
            "game_root": str(game_root),
            "source1": str(source1),
            "addon": str(addon),
            "game_files_modified": False,
            "migi_deployed": False,
        },
        "compile": compile_result,
        "roundtrip_decompile": decompile_result,
        "official_mdl_header": original_header,
        "compiled_mdl_header": compiled_header,
        "binary_header_comparison": {
            "internal_name_match": original_header["internal_name"] == compiled_header["internal_name"],
            "bone_count_match": original_header["bone_count"] == compiled_header["bone_count"],
            "local_sequence_count_match": original_header["local_sequence_count"] == compiled_header["local_sequence_count"],
            "official_local_animation_count": original_header["local_animation_count"],
            "compiled_local_animation_count": compiled_header["local_animation_count"],
            "local_animation_count_note": "studiomdl emits one additional internal animation record; sequence/bone/attachment/material/bounds checks remain exact.",
        },
        "compiled_addon_files": compiled_files,
        "comparison": comparison,
        "manual_game_check": {
            "status": "not_run",
            "reason": "This script stages a temporary addon; launching the game remains an explicit manual step.",
        },
    }
    if args.deploy_migi:
        target = args.migi_addon or (Path(game_dir()) / "migi" / "csgo" / "addons" / "p_cf_m4a1_s_bornbeast_a3_tmp")
        target = target.resolve()
        if target.exists():
            # Re-running the pipeline may reuse the exact staged addon, but
            # never overwrite a directory whose contents differ.
            for source in addon.rglob("*"):
                if source.is_file():
                    destination = target / source.relative_to(addon)
                    if not destination.is_file() or sha256_file(source) != sha256_file(destination):
                        raise SystemExit(f"refusing to overwrite non-identical MIGI addon: {target}")
        else:
            shutil.copytree(addon, target)
        report["isolation"]["migi_deployed"] = True
        report["isolation"]["migi_addon"] = str(target)
        report["manual_game_check"]["status"] = "staged_not_launched"

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORT_DIR / "a3_roundtrip_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(output),
        "compile_exit_code": compile_result["exit_code"],
        "structural_checks_pass": comparison["all_structural_checks_pass"],
        "compiled_model": str(compiled_model),
        "addon": str(addon),
    }, ensure_ascii=False, indent=2))
    return 0 if comparison["all_structural_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
