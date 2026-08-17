# -*- coding: utf-8 -*-
"""
LEGACY / UNSAFE — retained only as an audit reference; not a release entrypoint.

This file was the failed Antigravity deployment attempt.  It copies AK-47
models/animations/audio and renames them as M4A1-S/M4A4 assets, writes directly
to the Steam MIGI addon directory, and suppresses compiler output.  Do not run
it for deployment.  The replacement pipeline will be added under
``scripts/weapon_port/`` and will build into an isolated staging directory.
"""

import os
import shutil
import subprocess
from pathlib import Path


LEGACY_UNSAFE = True
LEGACY_REASON = (
    "This deployment script is frozen as a failed reference. "
    "It is not a valid M4A1-S/M4A4 build pipeline."
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_OUT = BASE_DIR / "data" / "out"
TOOLS_DIR = BASE_DIR / "tools"
VTF_CMD = TOOLS_DIR / "VTFEdit" / "VTFCmd.exe"

CSGO_MIGI_ADDONS = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons")
MOD_NAME = "p_cf_m4a1_bornbeast_4k"
TARGET_MOD_DIR = CSGO_MIGI_ADDONS / MOD_NAME

def build_m4a1_textures(dest_mat_dir: Path):
    dest_mat_dir.mkdir(parents=True, exist_ok=True)
    
    diffuse_png = DATA_OUT / "PV_M4A1_S_BornBeast_UltraHD_4K.png"
    normal_png = DATA_OUT / "PV_M4A1_S_BornBeast_Normal_4K.png"
    
    # 1. 4K Base Texture
    if diffuse_png.exists() and VTF_CMD.exists():
        print("  [+] Compiling M4A1-雷神 4K Base Texture...")
        cmd = [str(VTF_CMD), "-file", str(diffuse_png), "-output", str(dest_mat_dir), "-format", "dxt5", "-version", "7.4", "-resize"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        gen_vtf = dest_mat_dir / (diffuse_png.stem + ".vtf")
        target_vtf = dest_mat_dir / "PV-M4A1_S_BornBeast.vtf"
        if gen_vtf.exists():
            if target_vtf.exists(): os.remove(target_vtf)
            gen_vtf.rename(target_vtf)
            
    # 2. 4K Normal Map
    if normal_png.exists() and VTF_CMD.exists():
        print("  [+] Compiling M4A1-雷神 4K Normal Map...")
        cmd = [str(VTF_CMD), "-file", str(normal_png), "-output", str(dest_mat_dir), "-format", "dxt5", "-flag", "NORMAL", "-version", "7.4", "-resize"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        gen_norm_vtf = dest_mat_dir / (normal_png.stem + ".vtf")
        target_norm_vtf = dest_mat_dir / "PV-M4A1_S_BornBeast_N.vtf"
        if gen_norm_vtf.exists():
            if target_norm_vtf.exists(): os.remove(target_norm_vtf)
            gen_norm_vtf.rename(target_norm_vtf)

    # 3. Master VMT for M4A1-雷神 (Cyan laser crystal & brushed titanium receiver)
    vmt_content = '''"VertexLitGeneric"
{
    "$basetexture" "models\\v_models\\weapons\\m4a1_bornbeast\\PV-M4A1_S_BornBeast"
    "$bumpmap" "models\\v_models\\weapons\\m4a1_bornbeast\\PV-M4A1_S_BornBeast_N"
    "$nodiffusebumplighting" "0"

    "$phong" "1"
    "$phongboost" "4.0"
    "$phongexponent" "50"
    "$phongfresnelranges" "[0.5 1.5 3.0]"
    "$phongalbedotint" "1"

    "$envmap" "env_cubemap"
    "$envmaptint" "[0.15 0.18 0.22]"
    "$envmapfresnel" "1"
    "$envmapFresnelMinMaxExp" "[0.0 1.0 2.0]"

    "$rimlight" "1"
    "$rimlightexponent" "35"
    "$rimlightboost" "1.5"

    "$nocull" "1"
}
'''
    (dest_mat_dir / "pv-m4a1_s_bornbeast.vmt").write_text(vmt_content, encoding="utf-8")
    
    # Also write to rif_m4a1_s material path so CS:GO stock overrides map directly
    alt_mat_dir = TARGET_MOD_DIR / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1_s"
    alt_mat_dir.mkdir(parents=True, exist_ok=True)
    (alt_mat_dir / "m4a1_s.vmt").write_text(vmt_content, encoding="utf-8")
    if (dest_mat_dir / "PV-M4A1_S_BornBeast.vtf").exists():
        shutil.copy2(dest_mat_dir / "PV-M4A1_S_BornBeast.vtf", alt_mat_dir / "m4a1_s.vtf")
    if (dest_mat_dir / "PV-M4A1_S_BornBeast_N.vtf").exists():
        shutil.copy2(dest_mat_dir / "PV-M4A1_S_BornBeast_N.vtf", alt_mat_dir / "m4a1_s_normal.vtf")

def deploy_m4a1_models(dest_models_dir: Path):
    dest_models_dir.mkdir(parents=True, exist_ok=True)
    
    # Source model from p_cf_ak47_beast_4k or game compiled directory
    src_models = Path(r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_ak47_beast_4k\models\weapons")
    if not src_models.exists() or not (src_models / "v_rif_ak47.mdl").exists():
        src_models = Path(r"D:\steam\steamapps\common\csgo legacy\csgo\models\weapons")
        
    if src_models.exists():
        src_mdl = src_models / "v_rif_ak47.mdl"
        src_vvd = src_models / "v_rif_ak47.vvd"
        src_vtx = src_models / "v_rif_ak47.dx90.vtx"
        
        # Deploy to both M4A1-S (消音) and M4A4
        for prefix in ["v_rif_m4a1_s", "v_rif_m4a1"]:
            if src_mdl.exists(): shutil.copy2(src_mdl, dest_models_dir / f"{prefix}.mdl")
            if src_vvd.exists(): shutil.copy2(src_vvd, dest_models_dir / f"{prefix}.vvd")
            if src_vtx.exists(): shutil.copy2(src_vtx, dest_models_dir / f"{prefix}.dx90.vtx")
            
        for prefix in ["w_rif_m4a1_s", "w_rif_m4a1"]:
            src_w = src_models / "w_rif_ak47.mdl"
            if src_w.exists():
                shutil.copy2(src_w, dest_models_dir / f"{prefix}.mdl")

def deploy_m4a1_sounds(dest_sound_dir: Path):
    dest_sound_dir.mkdir(parents=True, exist_ok=True)
    src_sound_dir = DATA_OUT / "sound" / "weapons" / "ak47"
    if src_sound_dir.exists():
        for f in os.listdir(src_sound_dir):
            if f.endswith(".wav"):
                shutil.copy2(src_sound_dir / f, dest_sound_dir / f)

def main():
    if LEGACY_UNSAFE:
        raise SystemExit(
            "LEGACY/UNSAFE: deployment blocked. "
            "Use the future scripts/weapon_port pipeline after validation."
        )

    print(f"[+] Deploying CF M4A1-Born Beast (雷神) 4K MIGI Mod to: {TARGET_MOD_DIR}")
    
    mat_dir = TARGET_MOD_DIR / "materials" / "models" / "v_models" / "weapons" / "m4a1_bornbeast"
    mod_dir = TARGET_MOD_DIR / "models" / "weapons"
    snd_dir = TARGET_MOD_DIR / "sound" / "weapons" / "m4a1"
    
    build_m4a1_textures(mat_dir)
    print("  [OK] M4A1-雷神 4K PBR Textures & Cyan Laser Shaders Built")
    
    deploy_m4a1_models(mod_dir)
    print("  [OK] M4A1-S / M4A4 Weapon Models Deployed")
    
    deploy_m4a1_sounds(snd_dir)
    print("  [OK] Standard 44.1kHz Audio Kit Deployed")
    
    print("\n[SUCCESS] CF M4A1-雷神 (4K 次世代版) 已成功部署至 CS:GO MIGI 模组库！")

if __name__ == "__main__":
    main()
