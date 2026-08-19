# -*- coding: utf-8 -*-
"""Generate authentic M4A1-雷神 (BornBeast) Silver & Cyan-Blue materials."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import pygame

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "p6_final_materials"
VTFCMD_EXE = PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe"
TARGET_MATERIAL_DIR = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "f4_recognizable_classic" / "addon" / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
DEPLOY_DIR = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final\materials\models\weapons\v_models\rif_m4a1")


def main() -> int:
    pygame.init()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

    ref_diffuse = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials" / "external" / "cs16_textures" / "02_PV-M4A1_S_BORNBEAST.bmp.png"
    surf = pygame.image.load(str(ref_diffuse))
    surf_1024 = pygame.transform.smoothscale(surf, (1024, 1024))
    w, h = surf_1024.get_size()

    # Create true BornBeast diffuse: Silver body + Bright Cyan/Blue Energy Accents
    diffuse_surf = pygame.Surface((w, h))
    illum_surf = pygame.Surface((w, h))

    for y in range(h):
        for x in range(w):
            r, g, b, _ = surf_1024.get_at((x, y))

            # Detect red glowing regions (the dragon eye, energy chamber, light bars)
            is_energy = (r > 80 and r > g * 1.4 and r > b * 1.4)

            if is_energy:
                # Transform red energy into authentic BornBeast Electric Cyan/Blue:
                intensity = r / 255.0
                new_r = int(min(255, 40 * intensity + 20))
                new_g = int(min(255, 210 * intensity + 30))
                new_b = int(min(255, 255 * intensity))
                diffuse_surf.set_at((x, y), (new_r, new_g, new_b, 255))

                illum_val = int(min(255, 255 * intensity))
                illum_surf.set_at((x, y), (illum_val, illum_val, illum_val, 255))
            else:
                # Enhance body with metallic silver/gunmetal highlights
                # Lift darker parts to clean silver/gunmetal
                lum = int(0.299 * r + 0.587 * g + 0.114 * b)
                # Boost brightness of metal plates
                silver_val = min(235, int(lum * 1.15 + 15))
                # Keep subtle cool steel tint
                diffuse_surf.set_at((x, y), (silver_val, silver_val, int(min(255, silver_val * 1.05)), 255))
                illum_surf.set_at((x, y), (0, 0, 0, 255))

    out_base_png = WORK_DIR / "bornbeast_true_blue_base.png"
    out_illum_png = WORK_DIR / "bornbeast_true_blue_selfillum.png"
    pygame.image.save(diffuse_surf, str(out_base_png))
    pygame.image.save(illum_surf, str(out_illum_png))

    print(f"[*] Generated true BornBeast textures (base: {out_base_png.stat().st_size}, illum: {out_illum_png.stat().st_size})")

    # Run VTFCmd to compile VTFs
    for out_dir in [TARGET_MATERIAL_DIR, DEPLOY_DIR]:
        subprocess.run([str(VTFCMD_EXE), "-file", str(out_base_png), "-output", str(out_dir), "-format", "dxt1", "-version", "7.4"], check=True)
        gen_base = out_dir / f"{out_base_png.stem}.vtf"
        target_base = out_dir / "rif_m4a1.vtf"
        if gen_base.exists():
            if target_base.exists():
                target_base.unlink()
            gen_base.rename(target_base)

        subprocess.run([str(VTFCMD_EXE), "-file", str(out_illum_png), "-output", str(out_dir), "-format", "dxt1", "-version", "7.4"], check=True)
        gen_illum = out_dir / f"{out_illum_png.stem}.vtf"
        target_illum = out_dir / "rif_m4a1_selfillum.vtf"
        if gen_illum.exists():
            if target_illum.exists():
                target_illum.unlink()
            gen_illum.rename(target_illum)

        # Write VMT with Cyan/Blue self illumination
        vmt_text = (
            '"VertexLitGeneric"\n{\n'
            '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
            '\t"$phong" "1"\n'
            '\t"$phongboost" "0.75"\n'
            '\t"$phongexponent" "28"\n'
            '\t"$phongfresnelranges" "[0.3 0.6 1.0]"\n'
            '\t"$phongalbedotint" "1"\n'
            '\t"$selfillum" "1"\n'
            '\t"$selfillummask" "models/weapons/v_models/rif_m4a1/rif_m4a1_selfillum"\n'
            '\t"$selfillumtint" "[0.25 0.85 1.0]"\n'
            '}\n'
        )
        (out_dir / "rif_m4a1.vmt").write_text(vmt_text, encoding="utf-8")
        print(f"[*] Updated materials in {out_dir}")

    # Copy comparison sheet to artifact directory
    artifact_dir = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\e38afcad-92d4-47f8-80dc-cbb40a0b7bda")
    pygame.image.save(diffuse_surf, str(artifact_dir / "bornbeast_true_blue_preview.png"))

    print("[PASS] True BornBeast silver & cyan-blue material deployed!")
    return 0


if __name__ == "__main__":
    main()
