# -*- coding: utf-8 -*-
"""Build a recognizable classic BornBeast material for the M4A4 runtime port."""

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
BUILD = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic"
WORK = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials"
EXTERNAL = WORK / "external"
SOURCE_ARCHIVE = EXTERNAL / "m4a1_s_bornbeast_cs16.rar"
SOURCE_DIFFUSE = EXTERNAL / "cs16_textures" / "02_PV-M4A1_S_BORNBEAST.bmp.png"
EXTRACT_REPORT = EXTERNAL / "cs16_texture_extract_report.json"
VALIDATOR = Path(__file__).with_name("validate_materials.py")
VTFCMD = PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe"
SOURCE_PAGE = "https://www.gamemodd.com/cs/skinsweapons/ak47/1082-m4a1-s-born-beast.html"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_vtfcmd(source: Path, material_dir: Path, output_name: str, log_stem: str) -> Path:
    process = subprocess.run(
        [str(VTFCMD), "-file", str(source), "-output", str(material_dir), "-format", "dxt1", "-version", "7.4"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (WORK / f"{log_stem}.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (WORK / f"{log_stem}.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    generated = material_dir / f"{source.stem}.vtf"
    target = material_dir / output_name
    if process.returncode != 0 or not generated.is_file():
        raise SystemExit(f"VTFCmd failed for {source}; inspect {log_stem} logs")
    generated.replace(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deploy-migi", action="store_true")
    parser.add_argument("--migi-addon", type=Path)
    args = parser.parse_args()

    required = [
        D3_BUILD / "addon",
        D3_BUILD / "source1" / "v_rif_m4a1.qc",
        D3_BUILD / "source1" / "cf_bornbeast_full_m4a4.smd",
        SOURCE_DIFFUSE,
        SOURCE_ARCHIVE,
        EXTRACT_REPORT,
        VTFCMD,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing F4 inputs: " + ", ".join(missing))

    extraction = json.loads(EXTRACT_REPORT.read_text(encoding="utf-8"))
    expected = next((entry for entry in extraction["textures"] if entry["name"] == "PV-M4A1_S_BORNBEAST.bmp"), None)
    if expected is None or sha256(SOURCE_DIFFUSE) != expected["sha256"]:
        raise SystemExit("external classic diffuse does not match the audited extraction report")

    source_rgb = Image.open(SOURCE_DIFFUSE).convert("RGB")
    if source_rgb.size != (512, 512):
        raise SystemExit(f"unexpected classic diffuse size: {source_rgb.size}")
    derived_dir = WORK / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    base_png = derived_dir / "bornbeast_f4_classic_base.png"
    source_rgb.save(base_png)

    mask_values = []
    for red, green, blue in source_rgb.get_flattened_data():
        other = max(green, blue)
        if red < 72 or red < green * 1.55 or red < blue * 1.55:
            mask_values.append(0)
        else:
            mask_values.append(max(0, min(255, round((red - other) * 2.75))))
    selfillum = Image.new("L", source_rgb.size)
    selfillum.putdata(mask_values)
    selfillum_png = derived_dir / "bornbeast_f4_red_selfillum_mask.png"
    selfillum.save(selfillum_png)

    if BUILD.exists():
        shutil.rmtree(BUILD)
    addon = BUILD / "addon"
    source = BUILD / "source1"
    shutil.copytree(D3_BUILD / "addon", addon)
    shutil.copytree(D3_BUILD / "source1", source)
    material_dir = addon / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    material_dir.mkdir(parents=True, exist_ok=True)
    for old in material_dir.glob("*.vtf"):
        old.unlink()

    base_vtf = run_vtfcmd(base_png, material_dir, "rif_m4a1.vtf", "f4_base_vtfcmd")
    selfillum_vtf = run_vtfcmd(
        selfillum_png, material_dir, "rif_m4a1_selfillum.vtf", "f4_selfillum_vtfcmd"
    )
    vmt = material_dir / "rif_m4a1.vmt"
    vmt.write_text(
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

    closure_report = WORK / "f4_material_closure_report.json"
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
        raise SystemExit("F4 material closure failed")

    deployment: dict[str, object] = {"migi_deployed": False}
    if args.deploy_migi:
        target = (
            args.migi_addon
            or Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_bornbeast_m4a4_f4_recognizable_tmp")
        ).resolve()
        if target.exists():
            source_files = {path.relative_to(addon).as_posix(): sha256(path) for path in addon.rglob("*") if path.is_file()}
            target_files = {path.relative_to(target).as_posix(): sha256(path) for path in target.rglob("*") if path.is_file()}
            if source_files != target_files:
                raise SystemExit(f"refusing to overwrite non-identical MIGI addon: {target}")
        else:
            shutil.copytree(addon, target)
        deployment = {"migi_deployed": True, "migi_addon": str(target), "game_files_modified": False}

    report = {
        "schema": "cf2.m4a4.f4-recognizable-classic.v1",
        "status": "staged_recognizable_classic_diffuse_red_selfillum",
        "base_model": "D3 R1 full, user-confirmed",
        "external_source": {
            "page": SOURCE_PAGE,
            "credits_as_published": ["Smilegate", "Nexon"],
            "download_archive": str(SOURCE_ARCHIVE),
            "download_sha256": sha256(SOURCE_ARCHIVE),
            "extraction_report": str(EXTRACT_REPORT),
            "diffuse": str(SOURCE_DIFFUSE),
            "diffuse_sha256": sha256(SOURCE_DIFFUSE),
            "usage": "material reference/recovery only; external model and animation are not used",
        },
        "source1": {
            "base_vtf": str(base_vtf),
            "base_vtf_sha256": sha256(base_vtf),
            "selfillum_mask_vtf": str(selfillum_vtf),
            "selfillum_mask_vtf_sha256": sha256(selfillum_vtf),
            "vmt": str(vmt),
            "phong": {"boost": 0.55, "exponent": 22},
        },
        "material_closure_report": str(closure_report),
        "deployment": deployment,
        "deferred": [
            "Animated breathing/pulsing remains deferred; the red layer is static self-illumination.",
            "The CF WeaponShader lookup and malformed local auxiliary maps are not used.",
            "This stage targets immediate visual recognition, not pixel-identical CF shader recreation.",
        ],
    }
    report_path = WORK / "f4_recognizable_classic_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "deployment": deployment}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
