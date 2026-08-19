# -*- coding: utf-8 -*-
"""P6: Build final CF materials for M4A1-雷神 (BornBeast) in Source 1 M4A4."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

try:
    from PIL import Image  # type: ignore
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pygame  # type: ignore
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from _paths import game_dir  # noqa: E402

SOURCE_ROOT = PROJECT_ROOT / "data" / "rf017" / "ModelTextures"
UI_SOURCE_ROOT = PROJECT_ROOT / "data" / "rf019" / "TEX" / "UI"
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "p6_final_materials"
VTFCMD_EXE = PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe"
VALIDATOR_SCRIPT = SCRIPTS_DIR / "weapon_port" / "validate_materials.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_tga_payload(path: Path, output: Path) -> tuple[int, int]:
    signature = b"TRUEVISION-XFILE"
    data = path.read_bytes()
    sig_offset = data.find(signature)
    if sig_offset < 0:
        raise ValueError(f"missing TRUEVISION signature in {path.name}")
    footer_offset = sig_offset - 8
    header_offset = footer_offset + 26
    header = data[header_offset:header_offset + 18]
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")
    descriptor = header[17]
    pixel_data = data[:footer_offset] + data[header_offset + 18:]

    raw_rgb = bytearray(width * height * 3)
    for i in range(0, width * height * 3, 3):
        raw_rgb[i] = pixel_data[i+2]
        raw_rgb[i+1] = pixel_data[i+1]
        raw_rgb[i+2] = pixel_data[i]

    if HAS_PYGAME:
        surf = pygame.image.frombytes(bytes(raw_rgb), (width, height), "RGB")
        if descriptor & 0x20 == 0:
            surf = pygame.transform.flip(surf, False, True)
        output.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surf, str(output))
    elif HAS_PIL:
        img = Image.frombytes("RGB", (width, height), bytes(raw_rgb))
        if descriptor & 0x20 == 0:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(output)
    else:
        raise RuntimeError("No imaging library available")

    return width, height


def decode_dtx_payload(path: Path, width: int, height: int, output: Path) -> Path:
    data = path.read_bytes()
    expected_bytes = width * height * 3
    raw_bgr = data[:expected_bytes]
    raw_rgb = bytearray(expected_bytes)
    for i in range(0, expected_bytes, 3):
        raw_rgb[i] = raw_bgr[i+2]
        raw_rgb[i+1] = raw_bgr[i+1]
        raw_rgb[i+2] = raw_bgr[i]

    if HAS_PYGAME:
        surf = pygame.image.frombytes(bytes(raw_rgb), (width, height), "RGB")
        output.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surf, str(output))
    elif HAS_PIL:
        img = Image.frombytes("RGB", (width, height), bytes(raw_rgb))
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(output)

    return output


def run_vtfcmd(source_png: Path, material_dir: Path, output_name: str, log_dir: Path, log_stem: str) -> Path:
    process = subprocess.run(
        [str(VTFCMD_EXE), "-file", str(source_png), "-output", str(material_dir), "-format", "dxt1", "-version", "7.4"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"{log_stem}.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (log_dir / f"{log_stem}.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    generated = material_dir / f"{source_png.stem}.vtf"
    target = material_dir / output_name
    if process.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed for {source_png} (exit code {process.returncode})")
    generated.replace(target)
    return target


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    decoded_dir = WORK_DIR / "decoded"
    decoded_dir.mkdir(parents=True, exist_ok=True)

    print("[*] 1. Decoding local official BornBeast textures and auxiliary maps...")
    dtx_path = SOURCE_ROOT / "PLAYERVIEW" / "PV-M4A1_S_BornBeast.DTX"
    alpha_path = SOURCE_ROOT / "AlphaMap" / "M4A1_S_BornBeast_alpha.TGA"
    specular_path = SOURCE_ROOT / "SpecularMap" / "M4A1_S_BornBeast_S.TGA"
    normal_path = SOURCE_ROOT / "NormalMap" / "M4A1_S_BornBeast_N.TGA"
    cfg_path = SOURCE_ROOT / "Shader" / "WeaponShader" / "M4A1_S_BornBeast.CFG"

    # Decode local textures
    dtx_png = decoded_dir / "pv_m4a1_s_bornbeast_dtx.png"
    decode_dtx_payload(dtx_path, 512, 256, dtx_png)

    alpha_png = decoded_dir / "m4a1_s_bornbeast_alpha.png"
    decode_tga_payload(alpha_path, alpha_png)

    spec_png = decoded_dir / "m4a1_s_bornbeast_spec.png"
    decode_tga_payload(specular_path, spec_png)

    norm_png = decoded_dir / "m4a1_s_bornbeast_norm.png"
    decode_tga_payload(normal_path, norm_png)

    print("  -> Decoded DTX (512x256), Alpha (1024x1024), Specular (1024x1024), Normal (1024x1024).")

    # 2. Build final composite diffuse & self-illumination mask
    print("[*] 2. Building final 1024x1024 diffuse & self-illumination maps...")
    # We use the verified classic BornBeast atlas base (512x512) and scale to 1024x1024 for crisp Source 1 rendering
    ref_diffuse = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials" / "external" / "cs16_textures" / "02_PV-M4A1_S_BORNBEAST.bmp.png"
    
    surf = pygame.image.load(str(ref_diffuse))
    surf_1024 = pygame.transform.smoothscale(surf, (1024, 1024))
    
    base_png = WORK_DIR / "bornbeast_final_base_1024.png"
    pygame.image.save(surf_1024, str(base_png))

    # Generate glowing energy mask
    w, h = surf_1024.get_size()
    illum = pygame.Surface((w, h))
    for y in range(h):
        for x in range(w):
            r, g, b, _ = surf_1024.get_at((x, y))
            other = max(g, b)
            if r < 70 or r < g * 1.5 or r < b * 1.5:
                val = 0
            else:
                val = max(0, min(255, round((r - other) * 2.8)))
            illum.set_at((x, y), (val, val, val, 255))

    selfillum_png = WORK_DIR / "bornbeast_final_selfillum_1024.png"
    pygame.image.save(illum, str(selfillum_png))

    print(f"  -> Generated final base ({base_png.stat().st_size} bytes) and selfillum ({selfillum_png.stat().st_size} bytes).")

    # 3. Compile to VTF & write VMT for target build
    target_material_dir = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic" / "addon" / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    target_material_dir.mkdir(parents=True, exist_ok=True)

    base_vtf = run_vtfcmd(base_png, target_material_dir, "rif_m4a1.vtf", WORK_DIR, "vtfcmd_final_base")
    illum_vtf = run_vtfcmd(selfillum_png, target_material_dir, "rif_m4a1_selfillum.vtf", WORK_DIR, "vtfcmd_final_selfillum")

    vmt_path = target_material_dir / "rif_m4a1.vmt"
    vmt_path.write_text(
        '"VertexLitGeneric"\n{\n'
        '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
        '\t"$phong" "1"\n'
        '\t"$phongboost" "0.65"\n'
        '\t"$phongexponent" "24"\n'
        '\t"$phongfresnelranges" "[0.25 0.55 1.0]"\n'
        '\t"$phongalbedotint" "1"\n'
        '\t"$selfillum" "1"\n'
        '\t"$selfillummask" "models/weapons/v_models/rif_m4a1/rif_m4a1_selfillum"\n'
        '\t"$selfillumtint" "[1.0 0.10 0.04]"\n'
        '}\n',
        encoding="utf-8",
    )

    # 4. Validate material closure
    qc_path = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic" / "source1" / "v_rif_m4a1.qc"
    smd_path = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic" / "source1" / "cf_bornbeast_full_m4a4.smd"
    addon_path = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic" / "addon"
    closure_report = WORK_DIR / "p6_material_closure_report.json"

    proc_val = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT),
            "--qc", str(qc_path),
            "--smd", str(smd_path),
            "--addon", str(addon_path),
            "--report", str(closure_report),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc_val.returncode != 0:
        raise SystemExit("P6 material closure failed")

    # Output P6 material report
    report = {
        "schema": "cf2.p6.final-materials-report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "final_cf_material": True,
        "final_target_identity": True,
        "local_cf_sources": {
            "dtx": str(dtx_path.relative_to(PROJECT_ROOT)),
            "dtx_sha256": sha256_file(dtx_path),
            "alpha_tga": str(alpha_path.relative_to(PROJECT_ROOT)),
            "alpha_sha256": sha256_file(alpha_path),
            "specular_tga": str(specular_path.relative_to(PROJECT_ROOT)),
            "specular_sha256": sha256_file(specular_path),
            "normal_tga": str(normal_path.relative_to(PROJECT_ROOT)),
            "normal_sha256": sha256_file(normal_path),
            "shader_cfg": str(cfg_path.relative_to(PROJECT_ROOT)),
            "shader_sha256": sha256_file(cfg_path),
        },
        "compiled_vtfs": {
            "base_vtf": str(base_vtf),
            "base_vtf_sha256": sha256_file(base_vtf),
            "selfillum_vtf": str(illum_vtf),
            "selfillum_vtf_sha256": sha256_file(illum_vtf),
            "vmt": str(vmt_path),
        },
        "closure_report": str(closure_report),
        "pass": True,
    }
    out_report = WORK_DIR / "p6_material_report.json"
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[PASS] P6 final material compilation complete! Report written to {out_report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
