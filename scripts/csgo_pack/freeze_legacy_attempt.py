# -*- coding: utf-8 -*-
"""Freeze the 2026-08-17 M4A1-S legacy attempt as a read-only report.

This script intentionally only reads the project and the known deployed addon.
It never deletes, copies, compiles, or modifies game assets.  Re-running it
updates the report with fresh hashes while preserving the failed artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reports" / "legacy_attempt_20260817.json"

LOCAL_FAILURE_DIR = PROJECT_ROOT / "data" / "out" / "decompiled_m4a1_bornbeast"
LOCAL_AK_REFERENCE_DIR = PROJECT_ROOT / "data" / "out" / "decompiled_ak47_beast"
DEPLOYED_M4_DIR = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a1_bornbeast_4k")
DEPLOYED_AK_DIR = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_ak47_beast_4k")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, display_path: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": display_path or str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_directory": path.is_dir(),
    }
    if path.is_file():
        record["size_bytes"] = path.stat().st_size
        record["sha256"] = sha256_file(path)
    return record


def directory_inventory(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix().lower()):
        if path.is_file():
            entries.append(file_record(path, path.relative_to(directory).as_posix()))
    return entries


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def obj_stats(path: Path) -> dict[str, Any]:
    lines = read_lines(path)
    vertices = sum(line.startswith("v ") for line in lines)
    uvs = sum(line.startswith("vt ") for line in lines)
    normals = sum(line.startswith("vn ") for line in lines)
    faces = sum(line.startswith("f ") for line in lines)
    groups = [line[2:].strip() for line in lines if line.startswith("g ")]
    materials = Counter(line[7:].strip() for line in lines if line.startswith("usemtl "))
    return {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path),
        "vertices": vertices,
        "uvs": uvs,
        "normals": normals,
        "faces": faces,
        "groups": groups,
        "material_usage": dict(sorted(materials.items())),
    }


def smd_stats(path: Path) -> dict[str, Any]:
    lines = read_lines(path)
    stats: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path),
        "nodes": 0,
        "triangles": 0,
        "material_usage": {},
        "vertex_bone_usage": {},
    }
    try:
        nodes_start = lines.index("nodes")
    except ValueError:
        nodes_start = -1
    if nodes_start >= 0:
        for line in lines[nodes_start + 1 :]:
            if line == "end":
                break
            if line.strip():
                stats["nodes"] += 1

    try:
        triangles_start = lines.index("triangles")
    except ValueError:
        triangles_start = -1
    materials: Counter[str] = Counter()
    bones: Counter[str] = Counter()
    if triangles_start >= 0:
        index = triangles_start + 1
        while index < len(lines):
            material = lines[index].strip()
            if material == "end":
                break
            if not material:
                index += 1
                continue
            materials[material] += 1
            index += 1
            for _ in range(3):
                if index >= len(lines):
                    break
                fields = lines[index].split()
                if fields:
                    bones[fields[0]] += 1
                index += 1
            stats["triangles"] += 1
    stats["material_usage"] = dict(sorted(materials.items()))
    stats["vertex_bone_usage"] = dict(sorted(bones.items(), key=lambda item: int(item[0])))
    return stats


def mdl_stats(path: Path) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path),
    }
    if not path.is_file():
        return stats
    data = path.read_bytes()

    def int32(offset: int) -> int | None:
        if offset + 4 > len(data):
            return None
        return int.from_bytes(data[offset : offset + 4], "little", signed=True)

    stats.update(
        {
            "magic": data[:4].decode("ascii", errors="replace"),
            "version": int32(4),
            "internal_name": data[12:76].split(b"\0", 1)[0].decode("ascii", errors="replace"),
            "flags": int32(152),
            "bone_count": int32(156),
            "bone_index": int32(160),
            "hitbox_set_count": int32(172),
            "local_animation_count": int32(180),
            "local_sequence_count": int32(188),
        }
    )
    return stats


def hash_comparison(left: Path, right: Path) -> dict[str, Any]:
    left_hash = sha256_file(left)
    right_hash = sha256_file(right)
    return {
        "left": str(left),
        "right": str(right),
        "left_exists": left_hash is not None,
        "right_exists": right_hash is not None,
        "left_sha256": left_hash,
        "right_sha256": right_hash,
        "same_sha256": left_hash is not None and left_hash == right_hash,
    }


def main() -> int:
    local_failure_files = directory_inventory(LOCAL_FAILURE_DIR)
    deployed_m4_files = directory_inventory(DEPLOYED_M4_DIR)
    deployed_ak_files = directory_inventory(DEPLOYED_AK_DIR)

    m4_smd = LOCAL_FAILURE_DIR / "PV-M4A1-BornBeast.smd"
    hands_smd = LOCAL_FAILURE_DIR / "csgo_hands.smd"
    ak_smd = LOCAL_AK_REFERENCE_DIR / "PV-AK-47-Beast.smd"
    m4_obj = PROJECT_ROOT / "data" / "out" / "PV-M4A1_S_BornBeast_Classic.obj"

    m4_models = [
        DEPLOYED_M4_DIR / "models" / "weapons" / "v_rif_m4a1_s.mdl",
        DEPLOYED_M4_DIR / "models" / "weapons" / "v_rif_m4a1.mdl",
    ]
    comparison_models = [
        DEPLOYED_AK_DIR / "models" / "weapons" / "v_rif_ak47.mdl",
    ]

    comparisons = [
        hash_comparison(
            LOCAL_AK_REFERENCE_DIR / "v_rif_ak47_anims" / "ak47_idle.smd",
            LOCAL_FAILURE_DIR / "v_rif_ak47_anims" / "ak47_idle.smd",
        ),
        hash_comparison(
            DEPLOYED_AK_DIR / "models" / "weapons" / "w_rif_ak47.mdl",
            DEPLOYED_M4_DIR / "models" / "weapons" / "w_rif_m4a1.mdl",
        ),
    ]

    accidental_outputs = [
        PROJECT_ROOT / "--out",
        PROJECT_ROOT / "--out.mtl",
        PROJECT_ROOT / "--out_textures",
    ]

    report: dict[str, Any] = {
        "report_version": 1,
        "report_id": "legacy_attempt_20260817",
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "scope": {
            "weapon_id": "m4a1_s_bornbeast_classic",
            "target_slot": "m4a1_s",
            "purpose": "Freeze current failed attempt before rebuilding; read-only inventory.",
            "deletion_performed": False,
            "game_files_modified": False,
        },
        "legacy_script": {
            "path": str(PROJECT_ROOT / "scripts" / "csgo_pack" / "deploy_cf_m4a1_bornbeast_migi.py"),
            "status": "legacy_unsafe",
            "release_entrypoint": False,
            "reason": [
                "copies AK models and renames them to M4A1-S/M4A4",
                "copies AK sound directory as M4 audio",
                "writes directly to the Steam MIGI addon directory",
                "suppresses studiomdl/VTFCmd output",
            ],
        },
        "local_failure_directory": {
            "path": str(LOCAL_FAILURE_DIR),
            "exists": LOCAL_FAILURE_DIR.is_dir(),
            "files": local_failure_files,
        },
        "deployed_addons": {
            "m4a1_bornbeast": {
                "path": str(DEPLOYED_M4_DIR),
                "exists": DEPLOYED_M4_DIR.is_dir(),
                "files": deployed_m4_files,
            },
            "ak47_reference": {
                "path": str(DEPLOYED_AK_DIR),
                "exists": DEPLOYED_AK_DIR.is_dir(),
                "files": deployed_ak_files,
            },
        },
        "model_headers": [mdl_stats(path) for path in [*m4_models, *comparison_models]],
        "source_structure": {
            "m4_obj": obj_stats(m4_obj),
            "m4_smd": smd_stats(m4_smd),
            "csgo_hands_smd": smd_stats(hands_smd),
            "ak_reference_smd": smd_stats(ak_smd),
            "bones_define_qci": file_record(LOCAL_FAILURE_DIR / "bones_define.qci"),
        },
        "hash_comparisons": comparisons,
        "accidental_root_outputs": {
            "cleanup_action": "deferred_no_files_deleted",
            "entries": [file_record(path) for path in accidental_outputs],
        },
        "verification_notes": [
            "Current M4 compiled MDLs are expected to report 5 bones and 6 local sequences.",
            "The copied idle animation and dropped world model comparisons are recorded above.",
            "The report itself is generated under work/m4a1_s_bornbeast/reports and does not alter source or game assets.",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Legacy attempt report written: {REPORT_PATH}")
    print(f"[INFO] Local failure files: {len(local_failure_files)}")
    print(f"[INFO] Deployed M4 files: {len(deployed_m4_files)}")
    print(f"[INFO] Deployed AK reference files: {len(deployed_ak_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
