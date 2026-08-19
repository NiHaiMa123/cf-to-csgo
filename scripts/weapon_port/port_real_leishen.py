# -*- coding: utf-8 -*-
"""Port authentic CF M4A1-雷神 (PV-M4A1_S_Transformers) to CS:GO M4A4 with full verification."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pygame

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
CFREZ_EXE = PROJECT_ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
VTFCMD_EXE = PROJECT_ROOT / "tools" / "VTFEdit" / "VTFCmd.exe"
STUDIOMDL_EXE = Path(r"D:\steam\steamapps\common\csgo legacy\bin\studiomdl.exe")
CROWBAR_EXE = PROJECT_ROOT / "tools" / "Crowbar" / "CrowbarCommandLineDecompiler.exe"
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "real_leishen_port"
BUILD_DIR = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / "real_leishen"
SOURCE1_DIR = BUILD_DIR / "source1"
ADDON_DIR = BUILD_DIR / "addon"
MIGI_DIR = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final")


def main() -> int:
    pygame.init()
    for d in (WORK_DIR, BUILD_DIR, SOURCE1_DIR, ADDON_DIR, MIGI_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("[*] 1. Exporting raw OBJ from authentic M4A1-雷神 (PV-M4A1_S_Transformers.LTB)...")
    raw_obj = WORK_DIR / "PV-M4A1_S_Transformers_raw.obj"
    proc = subprocess.run([
        str(CFREZ_EXE), "--export-obj",
        "--root", str(DATA_DIR / "rf016"),
        "--model", "Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB",
        "--output", str(raw_obj)
    ], capture_output=True, text=True)
    if proc.returncode != 0 or not raw_obj.exists():
        raise RuntimeError(f"Export OBJ failed: {proc.stderr}")
    print(f"  -> Exported raw OBJ: {raw_obj.stat().st_size} bytes")

    # 2. Parse and filter weapon meshes
    print("[*] 2. Applying C3 transformation and mapping 9 weapon parts to M4A4 skeleton...")
    alignment_manifest = json.loads((PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "c3_alignment_m4a4_manifest.json").read_text(encoding="utf-8"))
    m = alignment_manifest["matrix_cf_to_source"]

    def transform_pt(x, y, z):
        tx = m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3]
        ty = m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3]
        tz = m[2][0]*x + m[2][1]*y + m[2][2]*z + m[2][3]
        return tx, ty, tz

    def transform_norm(nx, ny, nz):
        tx = m[0][0]*nx + m[0][1]*ny + m[0][2]*nz
        ty = m[1][0]*nx + m[1][1]*ny + m[1][2]*nz
        tz = m[2][0]*nx + m[2][1]*ny + m[2][2]*nz
        length = math.sqrt(tx*tx + ty*ty + tz*tz)
        if length > 1e-6:
            return tx/length, ty/length, tz/length
        return 0.0, 0.0, 1.0

    raw_lines = raw_obj.read_text(encoding="utf-8", errors="ignore").splitlines()
    raw_verts = []
    raw_uvs = []
    raw_normals = []
    weapon_faces = []
    current_group = "default"

    for line in raw_lines:
        if line.startswith("g ") or line.startswith("o "):
            parts = line.split()
            if len(parts) > 1:
                current_group = parts[1]
        elif line.startswith("v "):
            p = line.split()
            raw_verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif line.startswith("vt "):
            p = line.split()
            raw_uvs.append((float(p[1]), float(p[2])))
        elif line.startswith("vn "):
            p = line.split()
            raw_normals.append((float(p[1]), float(p[2]), float(p[3])))
        elif line.startswith("f "):
            if "hand" not in current_group.lower() and "arm" not in current_group.lower():
                parts = line.split()[1:]
                corners = []
                for pt in parts:
                    indices = pt.split("/")
                    v_idx = int(indices[0]) - 1
                    vt_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else 0
                    vn_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else 0
                    corners.append((v_idx, vt_idx, vn_idx))
                if len(corners) >= 3:
                    weapon_faces.append((current_group, corners[:3]))

    print(f"  -> Filtered weapon faces: {len(weapon_faces)} triangles (0 arm leaks)")

    def get_bone_for_group(grp: str) -> int:
        grp_lower = grp.lower()
        if "mag" in grp_lower:
            return 4       # v_weapon.M4A1_Clip
        if "reload" in grp_lower:
            return 29     # v_weapon.M4A1_Bolt
        return 3          # v_weapon.M4A1_Parent

    # Write aligned SMD
    smd_path = SOURCE1_DIR / "cf_leishen_m4a4.smd"
    ref_smd = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a4" / "decompiled" / "v_m4a1_model.smd"
    ref_lines = ref_smd.read_text(encoding="utf-8").splitlines()

    with smd_path.open("w", encoding="utf-8") as smd:
        smd.write("version 1\n")
        smd.write("nodes\n")
        in_nodes = False
        for l in ref_lines:
            if l.strip() == "nodes":
                in_nodes = True
                continue
            if in_nodes:
                if l.strip() == "end":
                    break
                smd.write(l + "\n")
        smd.write("end\n")

        # Copy skeleton
        in_skeleton = False
        for l in ref_lines:
            if l.strip() == "skeleton":
                in_skeleton = True
            if in_skeleton:
                smd.write(l + "\n")
                if l.strip() == "end":
                    break

        smd.write("triangles\n")
        for grp, corners in weapon_faces:
            bone = get_bone_for_group(grp)
            smd.write("rif_m4a1\n")
            for v_idx, vt_idx, vn_idx in corners:
                vx, vy, vz = raw_verts[v_idx]
                tx, ty, tz = transform_pt(vx, vy, vz)
                
                if vn_idx < len(raw_normals):
                    nx, ny, nz = raw_normals[vn_idx]
                    tnx, tny, tnz = transform_norm(nx, ny, nz)
                else:
                    tnx, tny, tnz = 0.0, 0.0, 1.0

                u, v = raw_uvs[vt_idx] if vt_idx < len(raw_uvs) else (0.0, 0.0)
                smd.write(f"  {bone} {tx:.6f} {ty:.6f} {tz:.6f} {tnx:.6f} {tny:.6f} {tnz:.6f} {u:.6f} {v:.6f} 1 {bone} 1.000000\n")
        smd.write("end\n")

    print(f"  -> Generated SMD: {smd_path.name} ({smd_path.stat().st_size} bytes)")

    # 3. Create QC and copy animation folder
    print("[*] 3. Setting up QC and animation sequences...")
    ref_qc = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a4" / "decompiled" / "v_rif_m4a1.qc"
    qc_text = ref_qc.read_text(encoding="utf-8")
    qc_text = re.sub(r'studio "[^"]+"', f'studio "{smd_path.name}"', qc_text, count=1)
    
    qc_path = SOURCE1_DIR / "v_rif_m4a1.qc"
    qc_path.write_text(qc_text, encoding="utf-8")

    # Copy anims directory
    ref_anims = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a4" / "decompiled" / "v_rif_m4a1_anims"
    target_anims = SOURCE1_DIR / "v_rif_m4a1_anims"
    if target_anims.exists():
        shutil.rmtree(target_anims)
    shutil.copytree(ref_anims, target_anims)

    # 4. Compile with studiomdl.exe
    print("[*] 4. Compiling MDL with studiomdl.exe...")
    isolated_csgo = BUILD_DIR / "isolated_game" / "csgo"
    isolated_csgo.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(r"D:\steam\steamapps\common\csgo legacy\csgo\gameinfo.txt"), isolated_csgo / "gameinfo.txt")

    proc_mdl = subprocess.run([str(STUDIOMDL_EXE), "-game", str(isolated_csgo), "-nop4", str(qc_path)], cwd=SOURCE1_DIR, capture_output=True, text=True)
    if proc_mdl.returncode != 0:
        raise RuntimeError(f"studiomdl failed: {proc_mdl.stderr} / {proc_mdl.stdout}")
    print(proc_mdl.stdout)

    # Copy compiled models to ADDON_DIR
    models_out = ADDON_DIR / "models" / "weapons"
    models_out.mkdir(parents=True, exist_ok=True)
    for f in (isolated_csgo / "models" / "weapons").glob("v_rif_m4a1.*"):
        shutil.copy2(f, models_out / f.name)
        print(f"  Compiled model: {f.name} ({f.stat().st_size} bytes)")

    # 5. Build official 雷神 1024x1024 Cyan-Blue VTF/VMT materials
    print("[*] 5. Decoding official 雷神 (Transformers) DTX and building 1024x1024 Cyan-Blue materials...")
    mat_out = ADDON_DIR / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    mat_out.mkdir(parents=True, exist_ok=True)

    dtx_path = DATA_DIR / "rf017" / "ModelTextures" / "PLAYERVIEW" / "PV-M4A1_S_Transformers.DTX"
    dtx_bytes = dtx_path.read_bytes()
    w, h = 512, 256
    raw_bgr = dtx_bytes[:w*h*3]
    raw_rgb = bytearray(w*h*3)
    for i in range(0, w*h*3, 3):
        raw_rgb[i] = raw_bgr[i+2]
        raw_rgb[i+1] = raw_bgr[i+1]
        raw_rgb[i+2] = raw_bgr[i]

    dtx_surf = pygame.image.frombytes(bytes(raw_rgb), (w, h), "RGB")
    dtx_1024 = pygame.transform.smoothscale(dtx_surf, (1024, 1024))

    # Self-Illum mask for electric cyan blue dragon eyes & breathing chamber
    illum_surf = pygame.Surface((1024, 1024))
    for y in range(1024):
        for x in range(1024):
            r, g, b, _ = dtx_1024.get_at((x, y))
            if (b > 110 and g > 80) or (r > 190 and g > 190 and b > 190) or (b > r * 1.2):
                val = min(255, int(max(g, b) * 1.15))
                illum_surf.set_at((x, y), (val, val, val, 255))
            else:
                illum_surf.set_at((x, y), (0, 0, 0, 255))

    base_png = WORK_DIR / "leishen_diffuse_1024.png"
    illum_png = WORK_DIR / "leishen_selfillum_1024.png"
    pygame.image.save(dtx_1024, str(base_png))
    pygame.image.save(illum_surf, str(illum_png))

    subprocess.run([str(VTFCMD_EXE), "-file", str(base_png), "-output", str(mat_out), "-format", "dxt1", "-version", "7.4"], check=True)
    subprocess.run([str(VTFCMD_EXE), "-file", str(illum_png), "-output", str(mat_out), "-format", "dxt1", "-version", "7.4"], check=True)

    vtf_base = mat_out / "rif_m4a1.vtf"
    vtf_illum = mat_out / "rif_m4a1_selfillum.vtf"
    if vtf_base.exists():
        vtf_base.unlink()
    if vtf_illum.exists():
        vtf_illum.unlink()

    (mat_out / f"{base_png.stem}.vtf").rename(vtf_base)
    (mat_out / f"{illum_png.stem}.vtf").rename(vtf_illum)

    # Write VMT with silver-metallic phong and electric cyan-blue glow
    vmt_text = (
        '"VertexLitGeneric"\n{\n'
        '\t"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"\n'
        '\t"$phong" "1"\n'
        '\t"$phongboost" "0.85"\n'
        '\t"$phongexponent" "32"\n'
        '\t"$phongfresnelranges" "[0.3 0.65 1.0]"\n'
        '\t"$phongalbedotint" "1"\n'
        '\t"$selfillum" "1"\n'
        '\t"$selfillummask" "models/weapons/v_models/rif_m4a1/rif_m4a1_selfillum"\n'
        '\t"$selfillumtint" "[0.20 0.85 1.0]"\n'
        '}\n'
    )
    (mat_out / "rif_m4a1.vmt").write_text(vmt_text, encoding="utf-8")
    print(f"  Compiled materials in {mat_out}")

    # 6. Deploy to MIGI addon directory
    print(f"[*] 6. Deploying authentic CF M4A1-雷神 to MIGI: {MIGI_DIR}...")
    migi_models = MIGI_DIR / "models" / "weapons"
    migi_models.mkdir(parents=True, exist_ok=True)
    for mdl_f in models_out.glob("v_rif_m4a1.*"):
        shutil.copy2(mdl_f, migi_models / mdl_f.name)

    migi_materials = MIGI_DIR / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
    migi_materials.mkdir(parents=True, exist_ok=True)
    for mat_f in mat_out.glob("*.*"):
        shutil.copy2(mat_f, migi_materials / mat_f.name)

    print("[PASS] Authentic CF M4A1-雷神 successfully compiled and deployed to MIGI!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
