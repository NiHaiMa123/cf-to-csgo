# -*- coding: utf-8 -*-
"""Extract the official CS:GO Legacy M4A1-S first-person reference.

This is deliberately a small, reproducible, read-only VPK extraction step for
stage A2.  It never writes to the game directory and never consults the AK
reference addon.  Decompilation is kept as a separate explicit command because
the fixed CrowbarDecompiler binary is an external tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import vpk  # type: ignore
except ImportError as exc:  # pragma: no cover - exercised by the bundled runtime
    raise SystemExit("Python package 'vpk' is required; use the bundled workspace Python") from exc

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _paths import game_dir, project_dir  # noqa: E402


REFERENCE_FILES = (
    "models/weapons/v_rif_m4a1_s.mdl",
    "models/weapons/v_rif_m4a1_s.vvd",
    "models/weapons/v_rif_m4a1_s.dx90.vtx",
    "models/weapons/v_rif_m4a1_s.ani",
    "materials/models/weapons/v_models/rif_m4a1_s/rif_m4a1_s.vmt",
    "materials/models/weapons/v_models/rif_m4a1_s/rif_m4a1_s.vtf",
    "materials/models/weapons/v_models/rif_m4a1_s/rif_m4a1_s_exponent.vtf",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vpk",
        type=Path,
        default=Path(game_dir()) / "csgo" / "pak01_dir.vpk",
        help="official pak01_dir.vpk (default: CF2_GAME_DIR/csgo/pak01_dir.vpk)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(project_dir()) / "work" / "m4a1_s_bornbeast" / "reference_m4a1_s",
        help="reference output directory",
    )
    args = parser.parse_args()
    vpk_path = args.vpk.resolve()
    out_dir = args.out.resolve()
    if not vpk_path.is_file():
        raise SystemExit(f"official VPK not found: {vpk_path}")

    pak = vpk.open(str(vpk_path))
    source_dir = out_dir / "source_vpk"
    extracted: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in REFERENCE_FILES:
        try:
            payload = pak.get_file(relative).read()
        except Exception:
            missing.append(relative)
            continue
        destination = source_dir / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        extracted.append({
            "vpk_path": relative,
            "path": destination.relative_to(out_dir).as_posix(),
            "size_bytes": len(payload),
            "sha256": sha256_bytes(payload),
        })

    if missing:
        raise SystemExit("official VPK is missing required entries: " + ", ".join(missing))

    manifest = {
        "schema": "cf2.m4a1_s.reference-extraction.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "vpk": str(vpk_path),
            "vpk_size_bytes": vpk_path.stat().st_size,
            "vpk_mtime_ns": vpk_path.stat().st_mtime_ns,
            "game_dir": str(Path(game_dir()).resolve()),
        },
        "target": {
            "weapon": "M4A1-S",
            "modelname": "weapons/v_rif_m4a1_s.mdl",
            "first_person": True,
        },
        "files": extracted,
        "ak_reference_used": False,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
