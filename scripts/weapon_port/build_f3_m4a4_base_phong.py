# -*- coding: utf-8 -*-
"""Build a conservative Source 1 base + scalar-phong BornBeast material stage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
D3_BUILD = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "d3_r1_full"
BUILD = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f3_base_phong"
WORK = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials"
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
    required = [
        D3_BUILD / "addon",
        D3_BUILD / "source1" / "v_rif_m4a1.qc",
        D3_BUILD / "source1" / "cf_bornbeast_full_m4a4.smd",
        VTFCMD,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing F3 inputs: " + ", ".join(missing))

    decode = subprocess.run([sys.executable, str(DECODE_SCRIPT)], cwd=PROJECT_ROOT, check=False)
    if decode.returncode != 0:
        raise SystemExit("material decode failed")
    decoded = WORK / "decoded"
    base_scalar = Image.open(decoded / "bornbeast_alpha_g_scalar.png").convert("L")
    specular_scalar = Image.open(decoded / "bornbeast_specular_r_scalar.png").convert("L")
    base_lut = [round(((value / 255.0) ** 0.55) * 255.0) for value in range(256)]
    base = base_scalar.point(base_lut)
    rgba = Image.merge("RGBA", (base, base, base, specular_scalar))
    source_png = WORK / "derived" / "bornbeast_f3_base_specular_rgba.png"
    source_png.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(source_png)

    if BUILD.exists():
        shutil.rmtree(BUILD)
    addon = BUILD / "addon"
    source = BUILD / "source1"
    shutil.copytree(D3_BUILD / "addon", addon)
    shutil.copytree(D3_BUILD / "source1", source)
    material_dir = addon / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    material_dir.mkdir(parents=True, exist_ok=True)

    process = subprocess.run(
        [str(VTFCMD), "-file", str(source_png), "-output", str(material_dir), "-format", "dxt5", "-version", "7.4"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (WORK / "f3_vtfcmd.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (WORK / "f3_vtfcmd.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    generated = material_dir / f"{source_png.stem}.vtf"
    target_vtf = material_dir / "rif_m4a1.vtf"
    if process.returncode != 0 or not generated.is_file():
        raise SystemExit("F3 VTFCmd failed; inspect f3_vtfcmd logs")
    generated.replace(target_vtf)
    exponent = material_dir / "rif_m4a1_exponent.vtf"
    if exponent.exists():
        exponent.unlink()
    vmt = material_dir / "rif_m4a1.vmt"
    vmt.write_text(
        '"VertexLitGeneric"\n{\n'
        '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
        '\t"$phong" "1"\n'
        '\t"$basemapalphaphongmask" "1"\n'
        '\t"$phongboost" "0.6"\n'
        '\t"$phongexponent" "18"\n'
        '\t"$phongfresnelranges" "[0.2 0.5 1.0]"\n'
        '\t"$phongdisablehalflambert" "1"\n'
        '}\n',
        encoding="utf-8",
    )

    closure_report = WORK / "f3_material_closure_report.json"
    validate = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--qc", str(source / "v_rif_m4a1.qc"),
            "--smd", str(source / "cf_bornbeast_full_m4a4.smd"),
            "--addon", str(addon),
            "--report", str(closure_report),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if validate.returncode != 0:
        raise SystemExit("F3 material closure failed")

    deployment: dict[str, object] = {"migi_deployed": False}
    if args.deploy_migi:
        target = (args.migi_addon or Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_f3_base_phong_tmp")).resolve()
        if target.exists():
            source_files = {p.relative_to(addon).as_posix(): sha256(p) for p in addon.rglob("*") if p.is_file()}
            target_files = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob("*") if p.is_file()}
            if source_files != target_files:
                raise SystemExit(f"refusing to overwrite non-identical MIGI addon: {target}")
        else:
            shutil.copytree(addon, target)
        deployment = {"migi_deployed": True, "migi_addon": str(target), "game_files_modified": False}

    report = {
        "schema": "cf2.m4a4.f3-base-phong.v1",
        "status": "staged_conservative_base_and_scalar_phong",
        "base_model": "D3 R1 full, user-confirmed",
        "source_texture": {
            "path": str(source_png),
            "sha256": sha256(source_png),
            "rgb": "gamma-0.55 lift of corrected AlphaMap G scalar",
            "alpha": "corrected SpecularMap R scalar",
        },
        "source1": {
            "vtf": str(target_vtf),
            "vtf_sha256": sha256(target_vtf),
            "format": "DXT5 RGBA, basemap alpha used as phong mask",
            "vmt": str(vmt),
            "phong": {"boost": 0.6, "exponent": 18, "fresnel_ranges": [0.2, 0.5, 1.0]},
        },
        "material_closure_report": str(closure_report),
        "deployment": deployment,
        "deferred": [
            "Normal-B is scalar and is not enabled as $bumpmap.",
            "PV DTX red energy, CFG lookup strip, selfillum and animated proxies are not enabled.",
            "This remains a Source 1 approximation, not a final CF shader recreation.",
        ],
    }
    output = WORK / "f3_base_phong_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "deployment": deployment}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
