"""P4-M01-N05-J — Formula-backed channel wiring on the non-frozen diagnostic addon.

Applies the N05-I observed AlphaMap split:
  R = opacity (this BornBeast TGA is identically 255, so unused)
  G = spec mix (identically 255, so unused as a mask texture)
  B = cube mix (spatial; used as $envmapmask)

Does not copy CFG scalars into Source phong/envmap numbers.
Does not modify frozen addon files. Replaces the N05-H diagnostic folder.
final_cf_material=false. Not a P4-M01 PASS.

Repro:
  python scripts/material_recovery/n05j_formula_channel_addon.py
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

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05j_formula_channel_addon"
)
STAGING = OUT / "addon"
PNG_DIR = OUT / "_png"
N05F = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05f_source1_native_map"
)
N05F_MAT = N05F / "materials/models/weapons/v_models/cf_bornbeast_native_diag"
N05C_ALPHA = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05c_verified_reader_integration/bornbeast_alpha_tga.png"
)
P4_PACKAGE = REPO / "work/m4a1_s_bornbeast/p4_prototype_01/package"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
ADDON_NAME = "p_cf_bornbeast_m4a4_n05j_formula_diag"
PREV_ADDON = "p_cf_bornbeast_m4a4_n05h_native_diag"
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
	"$envmapmask" "models/weapons/v_models/rif_m4a1/rif_m4a1_envmask"
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


def channel_stats(image: Image.Image) -> dict:
    rows = {}
    for name, band in zip(image.getbands(), image.split(), strict=True):
        extrema = band.getextrema()
        hist = band.histogram()
        total = image.size[0] * image.size[1]
        mean = sum(index * count for index, count in enumerate(hist)) / total
        rows[name] = {"min": extrema[0], "max": extrema[1], "mean": mean}
    return rows


def vtfcmd(png: Path, dest: Path, fmt: str) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(dest.parent), "-format", fmt, "-version", "7.4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    generated = dest.parent / f"{png.stem}.vtf"
    if proc.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed {png}: {proc.stderr or proc.stdout}")
    if generated != dest:
        if dest.exists():
            dest.unlink()
        generated.replace(dest)
    return {
        "png": rel(png),
        "png_sha256": sha256_file(png),
        "vtf": rel(dest),
        "vtf_sha256": sha256_file(dest),
        "format": fmt,
        "png_size": list(Image.open(png).size),
        "vtf_bytes": dest.stat().st_size,
    }


def remove_previous_diagnostic() -> dict:
    previous = MIGI_ADDONS / PREV_ADDON
    if not previous.exists():
        return {"target": str(previous), "action": "absent"}
    shutil.rmtree(previous)
    return {"target": str(previous), "action": "removed"}


def deploy_addon(staging_hashes: dict[str, str]) -> dict:
    target = MIGI_ADDONS / ADDON_NAME
    if target.exists():
        existing = tree_hashes(target)
        if existing == staging_hashes:
            return {"target": str(target), "action": "verified_existing", "hashes": existing}
        shutil.rmtree(target)
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


def frozen_status() -> dict:
    frozen = MIGI_ADDONS / FROZEN_NAME
    parked = PARK / FROZEN_NAME
    return {
        "frozen_in_addons": frozen.exists(),
        "frozen_parked": parked.exists(),
        "frozen_modified": False,
        "parked_dst": str(parked),
    }


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    STAGING.mkdir(parents=True)
    PNG_DIR.mkdir(parents=True)

    alpha = Image.open(N05C_ALPHA).convert("RGB")
    stats = channel_stats(alpha)
    _r, _g, blue = alpha.split()
    envmask = Image.merge("RGB", (blue, blue, blue))
    envmask_png = PNG_DIR / "envmask_from_alpha_b.png"
    envmask.save(envmask_png)

    models_dir = STAGING / MODEL_REL
    mat_dir = STAGING / MAT_REL
    model_hashes = {}
    for name, expected in EXPECTED_P4_MODELS.items():
        model_hashes[name] = copy_verified(P4_PACKAGE / MODEL_REL / name, models_dir / name, expected)

    vtf_hashes = {}
    for dest_name, (src_name, expected) in N05F_VTF.items():
        vtf_hashes[dest_name] = copy_verified(N05F_MAT / src_name, mat_dir / dest_name, expected)
    envmask_info = vtfcmd(envmask_png, mat_dir / "rif_m4a1_envmask.vtf", "dxt1")
    vtf_hashes["rif_m4a1_envmask.vtf"] = envmask_info["vtf_sha256"]

    vmt_path = mat_dir / "rif_m4a1.vmt"
    vmt_path.write_text(VMT.replace("\n", "\r\n"), encoding="ascii")
    staging_hashes = tree_hashes(STAGING)
    previous = remove_previous_diagnostic()
    frozen = frozen_status()
    if frozen["frozen_in_addons"]:
        raise RuntimeError("frozen addon is still in MIGI addons; refuse to deploy a second v_rif_m4a1")
    deploy = deploy_addon(staging_hashes)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-J",
        "result": "FORMULA_CHANNEL_DIAGNOSTIC_DEPLOYED",
        "p4_m01": "INCOMPLETE",
        "final_cf_material": False,
        "frozen_addon_files_modified": False,
        "addon_name": ADDON_NAME,
        "staging": rel(STAGING),
        "alpha_source": rel(N05C_ALPHA),
        "alpha_channel_stats": stats,
        "envmask": envmask_info,
        "model_hashes": model_hashes,
        "vtf_hashes": vtf_hashes,
        "vmt_sha256": sha256_file(vmt_path),
        "staging_hashes": staging_hashes,
        "previous_diagnostic": previous,
        "park_frozen": frozen,
        "deploy": {k: v for k, v in deploy.items() if k != "hashes"} | {"file_count": len(deploy["hashes"])},
        "restore_frozen": (
            f"move {PARK / FROZEN_NAME} back to {MIGI_ADDONS / FROZEN_NAME} "
            f"and remove {MIGI_ADDONS / ADDON_NAME}"
        ),
        "notes": [
            "N05-I observed AlphaMap.b multiplies the cubemap; this VMT uses it as $envmapmask.",
            "N05-H $normalmapalphaenvmapmask was the wrong mask source and was removed.",
            "BornBeast Alpha.r and Alpha.g are identically 255, so they are not stored as extra mask VTFs.",
            "$phongexponent 16 remains a diagnostic placeholder, not SpecularPower*0.25.",
            "cube is still first DDS face only.",
            "Do not treat in-game look as P4-M01 PASS.",
        ],
    }
    (OUT / "mapping.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# N05-J — Formula-backed AlphaMap.b envmask",
                "",
                "Result: **FORMULA_CHANNEL_DIAGNOSTIC_DEPLOYED**. P4-M01 remains **INCOMPLETE**. `final_cf_material=false`.",
                "",
                f"Addon: `{ADDON_NAME}`",
                f"Deploy: `{deploy['target']}` ({deploy['action']})",
                f"Previous N05-H addon: `{previous['action']}`",
                f"Frozen parked: `{frozen['frozen_parked']}`",
                "",
                "N05-I compiled PS uses AlphaMap.r as opacity, .g as spec mix, .b as cube mix. This BornBeast TGA has R=G=255 everywhere; only B varies (mean ~10.8 / 255). The diagnostic VMT therefore wires `$envmapmask` from B and drops `$normalmapalphaenvmapmask`.",
                "",
                "`$phongexponent 16` is still a placeholder. CFG `SpecularPower*0.25` was not copied. Cube is still face0.",
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
        "previous": previous["action"],
        "alpha": stats,
        "out": rel(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
