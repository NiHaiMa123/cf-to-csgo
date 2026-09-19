"""P4-M01-N05-H — Non-frozen Source 1 diagnostic addon.

P4 compiled mesh + N05-F verified maps, wired to the MDL material path
`models/weapons/v_models/rif_m4a1`. Does not modify frozen addon files.
Parks the frozen folder outside MIGI addons so this diagnostic can load.
final_cf_material=false. Not a P4-M01 PASS.

Repro:
  python scripts/material_recovery/n05h_nonfrozen_native_addon.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
import sys

sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05h_nonfrozen_native_addon"
)
STAGING = OUT / "addon"
N05F = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05f_source1_native_map"
)
N05F_MAT = N05F / "materials/models/weapons/v_models/cf_bornbeast_native_diag"
P4_PACKAGE = REPO / "work/m4a1_s_bornbeast/p4_prototype_01/package"
ADDON_NAME = "p_cf_bornbeast_m4a4_n05h_native_diag"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
MIGI_ADDONS = GAME / "migi/csgo/addons"
PARK = GAME / "migi/csgo/_parked_addons"
MAT_REL = Path("materials/models/weapons/v_models/rif_m4a1")
MODEL_REL = Path("models/weapons")

EXPECTED_P4_MODELS = {
    "v_rif_m4a1.ani": "468bcad13c2a8ae26a26429a500c223ca9c438ae4b699e23c5c0989ef96c5ccc",
    "v_rif_m4a1.dx80.vtx": "a0fd546b637ba9a0820e8ef2cc5f5a8e0c9493532c9a0148d171e9784f10050f",
    "v_rif_m4a1.dx90.vtx": "74a726311f79bf029ac5c1db492f4f2408adcfe44fb3840e273722b73850cfee",
    "v_rif_m4a1.mdl": "3e38d73283ca7162d76822357687cffededf35078cf91fd32400264e84f24111",
    "v_rif_m4a1.sw.vtx": "bcaea069538db24fc39e2c83dacb84f1ac06c7235030f82144f7774e7ace7c9a",
    "v_rif_m4a1.vvd": "64245b10798ab1d78998a037a6f3c79b42aa50dbed903c74d80498964c9e1b13",
}

N05F_VTF = {
    "rif_m4a1.vtf": ("diffuse.vtf", "9ef395b18c64a48e23b41bbf690e2cda811d7bd60dc5146623b7de475f0db93d"),
    "rif_m4a1_normal.vtf": ("normal.vtf", "e325ef5684dbdd73bbf6d7d81087b4f5e3e0d1e660682b2be8e85990a36369bb"),
    "rif_m4a1_specular.vtf": ("specular.vtf", "d3b2989467a89608b1e45749cb4f6c113b444103a26156a736a067bb4cc6fa3f"),
    "rif_m4a1_alpha.vtf": ("alpha.vtf", "3ab8da06c207b8a4681961c501338277ee667ada7c1c0ea5ec1b66c295d1406b"),
    "rif_m4a1_cube.vtf": ("cube_face0.vtf", "67420865052458ab1724834bc0bd6382e79107fdfaf186598e1e491e44e5231e"),
}

VMT = '''"VertexLitGeneric"
{
	"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"
	"$bumpmap" "models/weapons/v_models/rif_m4a1/rif_m4a1_normal"
	"$phong" "1"
	"$phongexponent" "16"
	"$phongboost" "1"
	"$phongfresnelranges" "[0.05 0.5 1]"
	"$phongalbedotint" "1"
	"$envmap" "models/weapons/v_models/rif_m4a1/rif_m4a1_cube"
	"$normalmapalphaenvmapmask" "1"
	"$nocull" "0"
}
'''


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


def copy_verified(src: Path, dst: Path, expected: str) -> str:
    actual = sha256_file(src)
    if actual != expected:
        raise RuntimeError(f"hash mismatch {src}: {actual} != {expected}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied = sha256_file(dst)
    if copied != expected:
        raise RuntimeError(f"copy hash mismatch {dst}")
    return copied


def tree_hashes(root: Path) -> dict[str, str]:
    rows = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rows[path.relative_to(root).as_posix()] = sha256_file(path)
    return rows


def park_frozen() -> dict:
    frozen = MIGI_ADDONS / FROZEN_NAME
    parked = PARK / FROZEN_NAME
    result = {
        "frozen_src": str(frozen),
        "parked_dst": str(parked),
        "action": "absent",
        "frozen_modified": False,
    }
    if parked.exists() and not frozen.exists():
        result["action"] = "already_parked"
        return result
    if not frozen.exists():
        return result
    if parked.exists():
        raise RuntimeError(f"park destination already exists: {parked}")
    PARK.mkdir(parents=True, exist_ok=True)
    shutil.move(str(frozen), str(parked))
    result["action"] = "moved_outside_addons"
    result["note"] = "Frozen files were not edited; folder moved out of MIGI addons so N05-H can load."
    return result


def deploy_addon(staging_hashes: dict[str, str]) -> dict:
    target = MIGI_ADDONS / ADDON_NAME
    if target.exists():
        existing = tree_hashes(target)
        if existing == staging_hashes:
            return {"target": str(target), "action": "verified_existing", "hashes": existing}
        raise RuntimeError(f"refusing to overwrite different addon at {target}")
    target.mkdir(parents=True, exist_ok=True)
    for relative in staging_hashes:
        src = STAGING / relative
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    deployed = tree_hashes(target)
    if deployed != staging_hashes:
        raise RuntimeError("post-deploy hash mismatch")
    return {"target": str(target), "action": "created", "hashes": deployed}


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    STAGING.mkdir(parents=True)

    models_dir = STAGING / MODEL_REL
    mat_dir = STAGING / MAT_REL
    model_hashes = {}
    for name, expected in EXPECTED_P4_MODELS.items():
        model_hashes[name] = copy_verified(P4_PACKAGE / MODEL_REL / name, models_dir / name, expected)

    vtf_hashes = {}
    for dest_name, (src_name, expected) in N05F_VTF.items():
        vtf_hashes[dest_name] = copy_verified(N05F_MAT / src_name, mat_dir / dest_name, expected)

    vmt_path = mat_dir / "rif_m4a1.vmt"
    vmt_path.write_text(VMT.replace("\n", "\r\n"), encoding="ascii")
    staging_hashes = tree_hashes(STAGING)
    park = park_frozen()
    deploy = deploy_addon(staging_hashes)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-H",
        "result": "NONFROZEN_NATIVE_DIAGNOSTIC_DEPLOYED",
        "p4_m01": "INCOMPLETE",
        "final_cf_material": False,
        "frozen_addon_files_modified": False,
        "addon_name": ADDON_NAME,
        "staging": rel(STAGING),
        "model_hashes": model_hashes,
        "vtf_hashes": vtf_hashes,
        "vmt_sha256": sha256_file(vmt_path),
        "staging_hashes": staging_hashes,
        "park_frozen": park,
        "deploy": {k: v for k, v in deploy.items() if k != "hashes"} | {"file_count": len(deploy["hashes"])},
        "restore_frozen": f"move {PARK / FROZEN_NAME} back to {MIGI_ADDONS / FROZEN_NAME} and remove {MIGI_ADDONS / ADDON_NAME}",
        "notes": [
            "P4 mesh bytes are unchanged; only the material files differ from frozen.",
            "Prototype selfillum was not copied.",
            "$phongexponent 16 remains a diagnostic placeholder, not CFG SpecularPower.",
            "cube is first DDS face only.",
            "Do not treat in-game look as P4-M01 PASS.",
        ],
    }
    (OUT / "mapping.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# N05-H — Non-frozen native diagnostic addon",
                "",
                "Result: **NONFROZEN_NATIVE_DIAGNOSTIC_DEPLOYED**. P4-M01 remains **INCOMPLETE**. `final_cf_material=false`.",
                "",
                f"Addon: `{ADDON_NAME}`",
                f"Deploy: `{deploy['target']}` ({deploy['action']})",
                f"Frozen park: `{park['action']}`",
                "",
                "P4 compiled `v_rif_m4a1` mesh is reused byte-identical. Materials are N05-F verified VTFs renamed onto the MDL path `rif_m4a1`. Frozen addon files were not edited; the frozen folder was moved out of `migi/csgo/addons` so this diagnostic can load.",
                "",
                f"Restore frozen: `{report['restore_frozen']}`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": report["result"],
        "addon": ADDON_NAME,
        "deploy": deploy["action"],
        "park": park["action"],
        "out": rel(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
