# -*- coding: utf-8 -*-
"""Build an isolated M4A4 addon using the decoded CF mask as a UV debug material."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
D3_BUILD = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "d3_r1_full"
BUILD = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f1_material_debug"
MATERIAL_WORK = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials"
DECODE_SCRIPT = Path(__file__).with_name("decode_bornbeast_materials.py")
VALIDATOR = Path(__file__).with_name("validate_materials.py")
VTFCMD = PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deploy-migi", action="store_true")
    parser.add_argument("--migi-addon", type=Path)
    args = parser.parse_args()
    required = [D3_BUILD / "addon", D3_BUILD / "source1" / "v_rif_m4a1.qc", D3_BUILD / "source1" / "cf_bornbeast_full_m4a4.smd", VTFCMD]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing F1 inputs: " + ", ".join(missing))

    decode = subprocess.run([sys.executable, str(DECODE_SCRIPT)], cwd=PROJECT_ROOT, check=False)
    if decode.returncode != 0:
        raise SystemExit("material decode failed")
    debug_png = MATERIAL_WORK / "decoded" / "bornbeast_alpha_min_debug.png"

    if BUILD.exists():
        shutil.rmtree(BUILD)
    addon = BUILD / "addon"
    source = BUILD / "source1"
    shutil.copytree(D3_BUILD / "addon", addon)
    shutil.copytree(D3_BUILD / "source1", source)
    material_dir = addon / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    material_dir.mkdir(parents=True, exist_ok=True)

    process = subprocess.run(
        [str(VTFCMD), "-file", str(debug_png), "-output", str(material_dir), "-format", "dxt1", "-version", "7.4"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (MATERIAL_WORK / "f1_vtfcmd.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (MATERIAL_WORK / "f1_vtfcmd.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    generated = material_dir / f"{debug_png.stem}.vtf"
    target_vtf = material_dir / "rif_m4a1.vtf"
    if process.returncode != 0 or not generated.is_file():
        raise SystemExit("VTFCmd failed; inspect work/m4a1_s_bornbeast/materials/f1_vtfcmd logs")
    generated.replace(target_vtf)
    exponent = material_dir / "rif_m4a1_exponent.vtf"
    if exponent.exists():
        exponent.unlink()
    vmt = material_dir / "rif_m4a1.vmt"
    vmt.write_text(
        '"VertexLitGeneric"\n{\n'
        '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
        '\t"$phong" "0"\n'
        '\t"$envmap" ""\n'
        '}\n',
        encoding="utf-8",
    )

    closure_report = MATERIAL_WORK / "f1_material_closure_report.json"
    validate = subprocess.run(
        [sys.executable, str(VALIDATOR), "--qc", str(source / "v_rif_m4a1.qc"), "--smd", str(source / "cf_bornbeast_full_m4a4.smd"), "--addon", str(addon), "--report", str(closure_report)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if validate.returncode != 0:
        raise SystemExit("F1 material reference closure failed")

    deployment: dict[str, object] = {"migi_deployed": False}
    if args.deploy_migi:
        target = (args.migi_addon or Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_f1_material_debug_tmp")).resolve()
        if target.exists():
            source_files = {p.relative_to(addon).as_posix(): sha256(p) for p in addon.rglob("*") if p.is_file()}
            target_files = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob("*") if p.is_file()}
            if source_files != target_files:
                raise SystemExit(f"refusing to overwrite non-identical MIGI addon: {target}")
        else:
            shutil.copytree(addon, target)
        deployment = {"migi_deployed": True, "migi_addon": str(target), "game_files_modified": False}

    report = {
        "schema": "cf2.m4a4.f1-material-debug.v1",
        "status": "staged_for_uv_and_surface_visibility_only",
        "base_model": "D3 R1 full, user-confirmed",
        "source_decode_report": str(MATERIAL_WORK / "material_decode_report.json"),
        "debug_texture": {"path": str(debug_png), "sha256": sha256(debug_png), "final_material": False},
        "source1": {"vmt": str(vmt), "vtf": str(target_vtf), "vtf_sha256": sha256(target_vtf)},
        "material_closure_report": str(closure_report),
        "deployment": deployment,
        "limitations": [
            "The base texture is a gamma-lifted per-pixel minimum of the CF AlphaMap channels.",
            "Normal, specular, shader CFG and animated PV DTX are intentionally not enabled.",
            "This build tests UV alignment and surface completeness, not final CF shader fidelity.",
        ],
    }
    report_path = MATERIAL_WORK / "f1_material_debug_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "addon": str(addon), "deployment": deployment}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
