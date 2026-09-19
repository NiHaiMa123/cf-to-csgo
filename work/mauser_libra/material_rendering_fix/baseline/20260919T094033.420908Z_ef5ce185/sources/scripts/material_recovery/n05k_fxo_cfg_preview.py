"""P4-M01-N05-K — Offline D3D9 preview of playerviewmesh.fxo with BornBeast CFG.

Renders the hypothesized technique on the verified PV weapon OBJ using
recovered maps. One shot keeps D3DX defaults, one shot writes BornBeast CFG
scalars. Does not attach CrossFire, does not deploy, does not announce PASS.

Repro:
  python scripts/material_recovery/n05k_fxo_cfg_preview.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05k_fxo_cfg_preview"
)
STAGING = DATA / "n05k_fxo_preview"
CFG = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/bornbeast_cfg.json"
)
PNG = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05f_source1_native_map/_png"
)
OBJ = DATA / "n05d_binding/obj_export/PV-M4A1_S_BornBeast.obj"
CUBE_CANDIDATES = [
    DATA / "rf017/ModelTextures/AlphaMap/Black_Shader03.DDS",
    DATA / "n05d_binding/Black_Shader03.DDS",
]
CUBE_SHA = "c4954419d59bea55b0f592957eab92fa623583d28158cbf84e95bacd233c4e92"
FXO_SHA = "d1672ba7e0a0f5b69e6a9520ec4ba0c6d4fb08b435aff1f3a3110af408bfb99c"
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def run_checked(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {proc.stderr or proc.stdout}")
    return proc


def find_fxo() -> Path:
    for path in (CF / "rez" / "Shader" / "playerviewmesh.fxo", CF / "Shader" / "playerviewmesh.fxo"):
        if path.is_file():
            return path
    raise FileNotFoundError("playerviewmesh.fxo not found")


def find_cube() -> Path:
    for path in CUBE_CANDIDATES:
        if path.is_file() and sha256_file(path) == CUBE_SHA:
            return path
    raise FileNotFoundError("verified Black_Shader03.DDS not found")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    run_checked([str(DOTNET), "build", str(REPO / "CFRezManager" / "CFRezManager.csproj"), "-c", "Debug"])
    source_fxo = find_fxo()
    fxo_sha = sha256_file(source_fxo)
    staged_fxo = STAGING / "playerviewmesh.fxo"
    staged_fxo.write_bytes(source_fxo.read_bytes())
    cube = find_cube()
    staged_cube = STAGING / "Black_Shader03.DDS"
    staged_cube.write_bytes(cube.read_bytes())
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    props = cfg["Properties"]
    config = {
        "fxo": str(staged_fxo),
        "obj": str(OBJ),
        "technique": "tPlayerViewMeshAlphaAproxSnellTransformedCube",
        "pass": 0,
        "width": 1280,
        "height": 720,
        "skip_groups": ["Fview-hand", "Fview-arm"],
        "textures": {
            "DiffuseMap": str(PNG / "diffuse.png"),
            "NormalMap": str(PNG / "normal.png"),
            "SpecularMap": str(PNG / "specular.png"),
            "AlphaMap": str(PNG / "alpha.png"),
            "CubeMap": str(staged_cube),
        },
        "shots": [
            {"name": "d3dx_defaults", "set": {}},
            {
                "name": "bornbeast_cfg",
                "set": {
                    "SpecularPower": float(props["SpecularPower"]),
                    "LightBrightness": float(props["LightBrightness"]),
                    "DiffuseBoost": float(props["DiffuseBoost"]),
                    "AmbientLightColor": float(props["AmbientLightColor"]),
                    "EnvCubeMapBrightness": float(props["EnvCubeMapBrightness"]),
                    "ReflectionIndex": float(props["ReflectionIndex"]),
                    "RefractionIndex": float(props["RefractionIndex"]),
                    "DiffuseMappingFactor": 1,
                    "NormalMappingFactor": 1,
                    "SpecularMappingFactor": 1,
                    "EnvCubeMappingFactor": 1,
                    "GlobalDiffuseAlpha": 1,
                },
            },
            {
                "name": "maps_on_mesh_studio",
                "set": {
                    "SpecularPower": 8,
                    "LightBrightness": 1,
                    "DiffuseBoost": 0.45,
                    "AmbientLightColor": 0.28,
                    "EnvCubeMapBrightness": 0.05,
                    "ReflectionIndex": 0,
                    "RefractionIndex": 0,
                    "DiffuseMappingFactor": 1,
                    "NormalMappingFactor": 1,
                    "SpecularMappingFactor": 1,
                    "EnvCubeMappingFactor": 0,
                    "GlobalDiffuseAlpha": 1,
                },
            },
        ],
    }
    config_path = OUT / "preview_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        run_checked([str(CFREZ_EXE), "--preview-fxo", str(config_path), str(OUT)])
        ok = True
        error = None
    except Exception as exc:
        ok = False
        error = str(exc)
    preview = {}
    preview_json = OUT / "preview.json"
    if preview_json.is_file():
        preview = json.loads(preview_json.read_text(encoding="utf-8"))
    result = "FXO_CFG_PREVIEW_RENDERED" if ok else "FXO_CFG_PREVIEW_FAILED"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-K",
        "result": result,
        "p4_m01": "INCOMPLETE",
        "final_cf_material": False,
        "fxo_sha256": fxo_sha,
        "fxo_sha_match": fxo_sha == FXO_SHA,
        "cube_sha256": sha256_file(staged_cube),
        "cube_sha_match": sha256_file(staged_cube) == CUBE_SHA,
        "ok": ok,
        "error": error,
        "preview": preview,
        "limitations": [
            "Self-built D3D9 device, not CrossFire runtime.",
            "Technique is still the EnvCubeUsage=2 name-level hypothesis.",
            "Camera/light are studio values, not CF's live light list.",
            "Rest-pose unskinned OBJ; hands omitted.",
            "CFG scalars were applied to this effect, not copied into Source VMT.",
            "Not a P4-M01 PASS.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shots = (preview.get("shots") if isinstance(preview, dict) else None) or []
    lines = [
        "# N05-K — Offline FXO preview with BornBeast CFG",
        "",
        f"Result: **{result}**. P4-M01 remains **INCOMPLETE**.",
        "",
        f"Technique `{config['technique']}` pass 0. FXO SHA match={report['fxo_sha_match']}. Cube SHA match={report['cube_sha_match']}.",
        "",
        "CFG `LightBrightness=0.01` makes `bornbeast_cfg.png` a near-silhouette (gun pixel median ~13). That file is not for identity inspection.",
        "",
        "`maps_on_mesh_studio.png` uses studio lights (not CFG) so the recovered maps can actually be seen. Crop is `maps_on_mesh_studio_crop.png`.",
        "",
    ]
    for shot in shots:
        lines.append(f"- `{shot.get('name')}`: `{shot.get('png')}`")
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    if error:
        lines += ["", "## Error", "", f"```\n{error}\n```"]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    inspect = crop_if_readable(OUT / "maps_on_mesh_studio.png", OUT / "maps_on_mesh_studio_crop.png")
    report["inspect"] = inspect
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result, "ok": ok, "out": str(OUT), "error": error, "inspect": inspect}, ensure_ascii=False))
    return 0 if ok else 1


def crop_if_readable(src: Path, dest: Path) -> dict:
    if not src.is_file():
        return {"ok": False, "error": "missing studio shot"}
    image = np.array(Image.open(src).convert("RGB"))
    bg = (image[:, :, 0] > 200) & (image[:, :, 1] > 200) & (image[:, :, 2] > 200)
    fg = ~bg
    if not fg.any():
        return {"ok": False, "error": "no foreground"}
    ys, xs = np.where(fg)
    pad = 16
    y0, y1 = max(0, int(ys.min()) - pad), min(image.shape[0], int(ys.max()) + pad + 1)
    x0, x1 = max(0, int(xs.min()) - pad), min(image.shape[1], int(xs.max()) + pad + 1)
    crop = image[y0:y1, x0:x1]
    Image.fromarray(crop).save(dest)
    lum = crop.astype(np.float32).mean(axis=2)
    cbg = (crop[:, :, 0] > 200) & (crop[:, :, 1] > 200) & (crop[:, :, 2] > 200)
    cfg = ~cbg
    median = float(np.median(lum[cfg])) if cfg.any() else 0.0
    return {
        "ok": median >= 40,
        "png": str(dest),
        "fg_median_lum": median,
        "fg_mean_rgb": crop[cfg].mean(axis=0).tolist() if cfg.any() else [],
        "bbox": [x0, y0, x1, y1],
    }


if __name__ == "__main__":
    raise SystemExit(main())
