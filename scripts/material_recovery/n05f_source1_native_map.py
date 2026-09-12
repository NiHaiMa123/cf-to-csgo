"""P4-M01-N05-F — Independent Source 1 VTF/VMT diagnostic from verified CF pixels.

Does not modify the P4 frozen addon, does not deploy, and does not set
final_cf_material true. CF CFG scalars are recorded beside the VMT; they are
not copied as Source 1 phong/envmap numbers.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05f_source1_native_map"
)
MAT = OUT / "materials" / "models" / "weapons" / "v_models" / "cf_bornbeast_native_diag"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
N05C = REPO / "work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05c_verified_reader_integration"
N05D = REPO / "work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05d_binding_uv_cube"
CFG = REPO / "work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery/bornbeast_cfg.json"
MATERIAL_ROOT = "models/weapons/v_models/cf_bornbeast_native_diag"

SOURCES = {
    "diffuse": N05D / "bornbeast_pv_dtx.png",
    "normal": N05C / "bornbeast_normal_tga.png",
    "specular": N05C / "bornbeast_specular_tga.png",
    "alpha": N05C / "bornbeast_alpha_tga.png",
    "cube_face0": N05D / "Black_Shader03_cube.png",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def vtfcmd(png: Path, dest_name: str, fmt: str) -> dict:
    MAT.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(MAT), "-format", fmt, "-version", "7.4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    generated = MAT / f"{png.stem}.vtf"
    target = MAT / dest_name
    if proc.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed {png}: {proc.stderr or proc.stdout}")
    if generated != target:
        if target.exists():
            target.unlink()
        generated.replace(target)
    return {
        "png": rel(png),
        "png_sha256": sha256_file(png),
        "vtf": rel(target),
        "vtf_sha256": sha256_file(target),
        "format": fmt,
        "png_size": list(Image.open(png).size),
        "vtf_bytes": target.stat().st_size,
    }


def write_vmt() -> Path:
    path = MAT / "cf_bornbeast_native_diag.vmt"
    text = f'''"VertexLitGeneric"
{{
	"$basetexture" "{MATERIAL_ROOT}/diffuse"
	"$bumpmap" "{MATERIAL_ROOT}/normal"
	"$phong" "1"
	"$phongexponent" "16"
	"$phongboost" "1"
	"$phongfresnelranges" "[0.05 0.5 1]"
	"$phongalbedotint" "1"
	"$envmap" "{MATERIAL_ROOT}/cube_face0"
	"$normalmapalphaenvmapmask" "1"
	"$nocull" "0"
}}
'''
    path.write_text(text.replace("\n", "\r\n"), encoding="ascii")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = [name for name, path in SOURCES.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing verified PNGs: {missing}")
    if not VTFCMD.is_file():
        raise FileNotFoundError(VTFCMD)

    prepared = {}
    tmp = OUT / "_png"
    tmp.mkdir(exist_ok=True)
    for name, source in SOURCES.items():
        image = Image.open(source).convert("RGB")
        png = tmp / f"{name}.png"
        image.save(png)
        prepared[name] = png

    vtfs = {
        "diffuse": vtfcmd(prepared["diffuse"], "diffuse.vtf", "dxt1"),
        "normal": vtfcmd(prepared["normal"], "normal.vtf", "dxt5"),
        "specular": vtfcmd(prepared["specular"], "specular.vtf", "dxt1"),
        "alpha": vtfcmd(prepared["alpha"], "alpha.vtf", "dxt1"),
        "cube_face0": vtfcmd(prepared["cube_face0"], "cube_face0.vtf", "dxt1"),
    }
    vmt = write_vmt()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-F",
        "result": "SOURCE1_NATIVE_DIAGNOSTIC_PACKAGED",
        "p4_m01": "INCOMPLETE",
        "final_cf_material": False,
        "deployed": False,
        "frozen_addon_modified": False,
        "vmt": rel(vmt),
        "vtfs": vtfs,
        "cf_cfg_recorded_not_copied": cfg,
        "notes": [
            "Source 1 $phongexponent 16 is a diagnostic placeholder, not CFG SpecularPower=1.",
            "cube_face0 is the first DDS face only, not a full cubemap object.",
            "Alpha/specular VTFs are stored but not all wired into the VertexLitGeneric contract.",
            "Do not deploy over p_cf_bornbeast_m4a4_p4_frozen_noop_01.",
        ],
    }
    (OUT / "mapping.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(
        "\n".join([
            "# N05-F — Source 1 native diagnostic map",
            "",
            "Result: **SOURCE1_NATIVE_DIAGNOSTIC_PACKAGED**. P4-M01 remains **INCOMPLETE**. `final_cf_material=false`. Frozen addon untouched, not deployed.",
            "",
            f"VMT: `{rel(vmt)}`",
            "",
            "| Map | VTF | PNG SHA |",
            "|---|---|---|",
            *[f"| {name} | `{row['vtf']}` | `{row['png_sha256'][:12]}…` |" for name, row in vtfs.items()],
            "",
            "CFG scalars are recorded in mapping.json and were not copied as Source 1 numbers.",
            "",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"result": report["result"], "vmt": rel(vmt), "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
