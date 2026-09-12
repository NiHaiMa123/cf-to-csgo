"""P4-M01-N05-E — Offline D3D9 effect inspect of playerviewmesh.fxo.

Loads the compiled effect on a self-built D3D9 device. Does not attach the
CF process, does not treat default values as BornBeast runtime selection,
and does not announce P4-M01 PASS.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    "runtime_acquisition/n05e_fxo_offline_inspect"
)
STAGING = DATA / "n05e_fxo"
CFG = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/bornbeast_cfg.json"
)
N04C = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04c_playerviewmesh_fxo/fxo_scan.json"
)
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")
N04C_SHA = "d227961370c480baf8a465f127b1ef6c52ff7936d4b31529c50b4e7074ecd1bd"

CFG_TO_HINTS = {
    "SpecularMapName2": ["SpecularMap", "SpecularMapSampler"],
    "EnvCubeMapName2": ["CubeMap", "EnvCube"],
    "NormalMapName2": ["NormalMap", "NormalMapSampler"],
    "AlphaMapName2": ["AlphaMap", "AlphaMapSampler"],
    "DiffuseMappingEnabled": ["Diffuse", "MapEnable"],
    "SpecularMappingEnabled": ["Specular", "MapEnable"],
    "EnvCubeMappingEnabled": ["Cube", "EnvCube", "MapEnable"],
    "NormalMappingEnabled": ["Normal", "MapEnable"],
    "LightBrightness": ["LightBrightness", "Brightness"],
    "EnvCubeMapBrightness": ["EnvCubeMapBrightness", "CubeMap", "Brightness"],
    "SpecularPower": ["SpecularPower"],
    "DiffuseBoost": ["DiffuseBoost"],
    "AmbientLightColor": ["Ambient"],
    "RefractionIndex": ["Refraction"],
    "ReflectionIndex": ["Reflection"],
    "EnvCubeUsage": ["EnvCubeUsage", "CubeMap"],
    "CubeMapTransformY": ["CubeMapTransform", "TransformY"],
}


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
    candidates = [
        CF / "rez" / "Shader" / "playerviewmesh.fxo",
        CF / "Shader" / "playerviewmesh.fxo",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("playerviewmesh.fxo not found as a loose file")


def match_cfg(parameters: list[dict], techniques: list[dict]) -> dict:
    names = [str(row.get("name") or "") for row in parameters]
    technique_names = [str(row.get("name") or "") for row in techniques]
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    mapping = {}
    for section, fields in cfg.items():
        for field, value in fields.items():
            hints = CFG_TO_HINTS.get(field, [field])
            hits = []
            for name in names + technique_names:
                upper = name.upper()
                if any(hint.upper() in upper for hint in hints):
                    hits.append(name)
            mapping[f"{section}.{field}"] = {
                "cfg_value": value,
                "hints": hints,
                "effect_name_hits": sorted(set(hits)),
                "matched": bool(hits),
                "note": "name overlap only; not runtime assignment proof",
            }
    return mapping


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    run_checked([str(DOTNET), "build", str(REPO / "CFRezManager" / "CFRezManager.csproj"), "-c", "Debug"])
    source = find_fxo()
    actual = sha256_file(source)
    staged = STAGING / "playerviewmesh.fxo"
    staged.write_bytes(source.read_bytes())
    inspect_path = OUT / "fxo_inspect.json"
    try:
        run_checked([str(CFREZ_EXE), "--inspect-fxo", str(staged), str(inspect_path)])
        inspect = json.loads(inspect_path.read_text(encoding="utf-8"))
        load_ok = True
        load_error = None
    except Exception as exc:
        inspect = None
        load_ok = False
        load_error = str(exc)
        inspect_path.write_text(json.dumps({"ok": False, "error": load_error}, indent=2) + "\n", encoding="utf-8")

    parameters = (inspect or {}).get("parameters") or []
    techniques = (inspect or {}).get("techniques") or []
    mapping = match_cfg(parameters, techniques) if load_ok else {}
    result = "FXO_EFFECT_ENUMERATED" if load_ok else "FXO_DEVICE_OR_EFFECT_LOAD_FAILED"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-E",
        "result": result,
        "p4_m01": "INCOMPLETE",
        "source": str(source),
        "sha256": actual,
        "n04c_sha256": N04C_SHA,
        "n04c_sha_match": actual == N04C_SHA,
        "load_ok": load_ok,
        "load_error": load_error,
        "parameter_count": len(parameters),
        "technique_count": len(techniques),
        "parameter_names": [row.get("name") for row in parameters],
        "technique_names": [row.get("name") for row in techniques],
        "cfg_name_overlap": mapping,
        "limitations": [
            "D3DX default values are not BornBeast runtime selection.",
            "Name overlap is not a sampler binding proof.",
            "This harness does not attach CrossFire or ACE.",
            "Raw FXO stays in data/n05e_fxo and is not committed.",
        ],
    }
    (OUT / "semantics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report)
    print(json.dumps({"result": result, "parameters": len(parameters), "techniques": len(techniques), "out": str(OUT)}, ensure_ascii=False))
    return 0 if load_ok else 1


def write_markdown(report: dict) -> None:
    lines = [
        "# N05-E — Offline playerviewmesh.fxo inspect",
        "",
        f"Result: **{report['result']}**. P4-M01 remains **INCOMPLETE**.",
        "",
        f"Source SHA256 `{report['sha256']}`. N04-C SHA match={report.get('n04c_sha_match')}. Load ok={report['load_ok']}.",
        "",
        f"Parameters: {report['parameter_count']}. Techniques: {report['technique_count']}.",
        "",
        "## CFG name overlap",
        "",
        "| CFG field | value | effect names |",
        "|---|---|---|",
    ]
    for key, row in (report.get("cfg_name_overlap") or {}).items():
        hits = ", ".join(f"`{name}`" for name in row.get("effect_name_hits") or []) or "—"
        lines.append(f"| `{key}` | `{row.get('cfg_value')}` | {hits} |")
    if report.get("load_error"):
        lines += ["", "## Load error", "", f"```\n{report['load_error']}\n```"]
    lines += ["", "## Limitations", ""]
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
