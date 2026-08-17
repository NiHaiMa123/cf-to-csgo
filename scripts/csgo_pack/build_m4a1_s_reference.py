# -*- coding: utf-8 -*-
"""Run the complete, fixed-tool A2 M4A1-S reference pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _paths import game_dir, project_dir  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vpk", type=Path, default=Path(game_dir()) / "csgo" / "pak01_dir.vpk")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(project_dir()) / "work" / "m4a1_s_bornbeast" / "reference_m4a1_s",
    )
    parser.add_argument(
        "--decompiler",
        type=Path,
        default=PROJECT_ROOT / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe",
    )
    args = parser.parse_args()
    out_dir = args.out.resolve()
    source_model = out_dir / "source_vpk" / "models" / "weapons" / "v_rif_m4a1_s.mdl"
    decompiled = out_dir / "decompiled"
    extract_script = Path(__file__).with_name("extract_m4a1_s_reference.py")
    report_script = Path(__file__).with_name("report_m4a1_s_reference.py")

    subprocess.run([sys.executable, str(extract_script), "--vpk", str(args.vpk), "--out", str(out_dir)], check=True)
    if not args.decompiler.is_file():
        raise SystemExit(f"fixed CrowbarDecompiler not found: {args.decompiler}")
    subprocess.run([str(args.decompiler.resolve()), str(source_model), str(decompiled)], check=True)
    subprocess.run([sys.executable, str(report_script), "--reference-dir", str(out_dir)], check=True)
    print(f"A2 reference pipeline complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
