# -*- coding: utf-8 -*-
"""Merge the 雷神 model/material and sound overlays into one MIGI addon.

Canonical active addon: p_cf_leishen_m4a4_p6
Merged source: work/p5_leishen/p7/addon/sound/**
Retired active addon: p_cf_leishen_m4a4_p7_sound

The duplicate sound addon is removed from the active addons directory only
when its tree matches both the repository staging tree and the parked backup.
MIGI REBUILD remains a user action.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
MIGI = GAME / "migi" / "csgo"
ADDONS = MIGI / "addons"
PARKED = MIGI / "_parked_addons"

CANONICAL_NAME = "p_cf_leishen_m4a4_p6"
SOUND_NAME = "p_cf_leishen_m4a4_p7_sound"
CANONICAL = ADDONS / CANONICAL_NAME
SOUND_ACTIVE = ADDONS / SOUND_NAME
SOUND_PARKED = PARKED / SOUND_NAME
SOUND_STAGE = REPO / "work" / "p5_leishen" / "p7" / "addon"
MATERIAL_STAGE = REPO / "work" / "p5_leishen" / "p6" / "addon"
MATERIAL_REL = Path("materials/models/weapons/v_models/rif_m4a1/rif_m4a1.vmt")
REPORT = REPO / "work" / "p5_leishen" / "unified_addon.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def copy_tree(source: Path, target: Path) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def main() -> int:
    if not CANONICAL.is_dir():
        raise RuntimeError(f"canonical addon missing: {CANONICAL}")

    staged_sound = tree_hashes(SOUND_STAGE)
    if not staged_sound:
        raise RuntimeError(f"sound staging missing: {SOUND_STAGE}")

    active_sound = tree_hashes(SOUND_ACTIVE)
    parked_sound = tree_hashes(SOUND_PARKED)
    if active_sound and active_sound != staged_sound:
        raise RuntimeError("active sound addon differs from repository staging")
    if parked_sound and parked_sound != staged_sound:
        raise RuntimeError("parked sound backup differs from repository staging")
    if not active_sound and not parked_sound:
        raise RuntimeError("neither active nor parked sound addon exists")

    copy_tree(SOUND_STAGE, CANONICAL)
    material_source = MATERIAL_STAGE / MATERIAL_REL
    material_target = CANONICAL / MATERIAL_REL
    if not material_source.is_file():
        raise RuntimeError(f"material staging missing: {material_source}")
    material_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(material_source, material_target)

    canonical_hashes = tree_hashes(CANONICAL)
    merged_sound = {
        relative: canonical_hashes.get(relative)
        for relative in staged_sound
    }
    if merged_sound != staged_sound:
        raise RuntimeError("merged sound hashes do not match staging")
    if canonical_hashes.get(MATERIAL_REL.as_posix()) != sha256(material_source):
        raise RuntimeError("merged material hash does not match staging")

    if SOUND_ACTIVE.is_dir():
        if not SOUND_PARKED.exists():
            PARKED.mkdir(parents=True, exist_ok=True)
            shutil.copytree(SOUND_ACTIVE, SOUND_PARKED)
        shutil.rmtree(SOUND_ACTIVE)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_addon": CANONICAL_NAME,
        "retired_addon": SOUND_NAME,
        "canonical_file_count": len(canonical_hashes),
        "merged_sound_file_count": len(staged_sound),
        "material": MATERIAL_REL.as_posix(),
        "material_sha256": sha256(material_source),
        "sound_sha256": staged_sound,
        "active_sound_removed": not SOUND_ACTIVE.exists(),
        "parked_backup_verified": tree_hashes(SOUND_PARKED) == staged_sound,
        "migi_rebuild": "USER_REQUIRED",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\n[leishen merge] DONE — user must click MIGI REBUILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
