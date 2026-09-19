"""Bake CF specular energy into the viewmodel basetexture and deploy.

Game Phong/envmap on this viewmodel did not respond. Blender/CF formula
shows gold lives in SpecularMap. This puts that gold into $basetexture so
CS:GO actually paints it. VMTs use the Tianxi A.8.1 Phong recipe as a
bonus if the engine shades it; the bake does not depend on Phong.

Does not touch models, UV, hands, sounds, or the normal map.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"D:/project/cf_to_csgo")
FIX = ROOT / "work/mauser_libra/material_rendering_fix"
MV2 = ROOT / "work/mauser_libra/material_v2"
UP = MV2 / "upscale"
OUT = FIX / "bake_spec_to_base"
FROZEN = FIX / "baseline/20260919T094033.420908Z_ef5ce185/addon_v2"
A = ROOT / "work/mauser_libra/addon_v2"
B = Path(r"D:/steam/steamapps/common/csgo legacy/migi/csgo/addons/p_cf_mauser_libra_p1")
VTFCMD = ROOT / "tools/VTFEdit/VTFCmd.exe"
MAT = Path("materials/models/weapons/v_models/cf_mauser")
VMT_NAME = "cf_mauser_libra"
CHUNK = 1024 * 1024

GUN_VMTS = [
    "cf_mauser_libra.vmt",
    "cf_mauser_libra_r0.vmt",
    "cf_mauser_libra_r1.vmt",
    "cf_mauser_libra_r2.vmt",
    "cf_mauser_libra_r3.vmt",
    "cf_mauser_libra_r4.vmt",
    "cf_mauser_libra_r5.vmt",
]

VMT_TEXT = '''"VertexLitGeneric"
{
	"$basetexture" "models/weapons/v_models/cf_mauser/cf_mauser_libra"
	"$bumpmap" "models/weapons/v_models/cf_mauser/cf_mauser_libra_n"
	"$halflambert" "1"
	"$phong" "1"
	"$phongexponent" "48"
	"$phongboost" "8"
	"$phongfresnelranges" "[0.05 0.45 1]"
	"$phongalbedotint" "1"
	"$nocull" "0"
}
'''


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    out = {}
    for dirpath, _, files in os.walk(root):
        for name in files:
            p = Path(dirpath) / name
            out[p.relative_to(root).as_posix()] = sha(p)
    return out


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(stat.S_IWRITE | stat.S_IREAD)
    path.write_bytes(data)


def bake_png() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    diff = np.asarray(Image.open(UP / "diffuse_2048.png").convert("RGB"), np.float32) / 255.0
    spec = np.asarray(Image.open(UP / "specular_2048.png").convert("RGB"), np.float32) / 255.0
    # CF: albedo is weakly lit; spec is the champagne metal (SpecularPower~1, broad).
    rgb = np.clip(diff * 0.25 + spec, 0.0, 1.0)
    rgba = np.dstack([rgb, np.ones(rgb.shape[:2], np.float32)])
    png = OUT / "cf_mauser_libra_baked.png"
    Image.fromarray(np.uint8(np.round(rgba * 255.0)), "RGBA").save(png)
    Image.fromarray(np.uint8(np.round(rgb * 255.0)), "RGB").save(OUT / "cf_mauser_libra_baked_rgb.png")
    return png


def make_vtf(png: Path) -> Path:
    dest = OUT / "cf_mauser_libra.vtf"
    cmd = [str(VTFCMD), "-file", str(png), "-output", str(OUT),
           "-format", "bgra8888", "-alphaformat", "bgra8888",
           "-version", "7.4", "-flag", "TRILINEAR", "-flag", "ANISOTROPIC"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = OUT / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed: {proc.stderr or proc.stdout}")
    if produced != dest:
        if dest.exists():
            dest.chmod(stat.S_IWRITE | stat.S_IREAD)
        produced.replace(dest)
    return dest


def deploy(vtf: Path) -> dict:
    rel_vtf = (MAT / "cf_mauser_libra.vtf").as_posix()
    vtf_bytes = vtf.read_bytes()
    changed = {rel_vtf: hashlib.sha256(vtf_bytes).hexdigest()}
    for root in (A, B):
        write_bytes(root / rel_vtf, vtf_bytes)
        for name in GUN_VMTS:
            rel = (MAT / name).as_posix()
            write_bytes(root / Path(*rel.split("/")), VMT_TEXT.encode("ascii"))
            changed[rel] = hashlib.sha256(VMT_TEXT.encode("ascii")).hexdigest()
    a, b, frozen = inventory(A), inventory(B), inventory(FROZEN)
    if a != b:
        mismatch = sorted(k for k in a if a.get(k) != b.get(k))
        raise RuntimeError(f"A/B mismatch after deploy: {mismatch}")
    protected = [k for k in frozen if k not in changed]
    drifted = [k for k in protected if a.get(k) != frozen[k]]
    if drifted:
        raise RuntimeError(f"Protected files drifted: {drifted}")
    return {
        "changed": changed,
        "files": len(a),
        "ab_equal": True,
        "protected_match_frozen": True,
        "vtf_bytes": len(vtf_bytes),
        "vtf_sha256": changed[rel_vtf],
        "bake": "clip(diffuse*0.25 + specular)",
        "vmt": "Tianxi A.8.1 phong on all gun slots; no envmap; no alphamask; gold is in basetexture",
        "next": "User MIGI REBUILD, then same three Mirage shots.",
    }


def main() -> int:
    png = bake_png()
    vtf = make_vtf(png)
    evidence = deploy(vtf)
    (OUT / "deploy_manifest.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "png": str(png),
        "vtf_sha256": evidence["vtf_sha256"],
        "vtf_bytes": evidence["vtf_bytes"],
        "ab_equal": True,
        "changed": list(evidence["changed"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
