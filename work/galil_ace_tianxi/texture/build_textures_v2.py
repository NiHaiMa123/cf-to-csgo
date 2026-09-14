# -*- coding: utf-8 -*-
"""Galil ACE-天袭 texture pass v2 — ComfyUI 4x diffuse + envmap/phong VMT.

Inputs
  decode/PV-GalilACE_PhantomBeast.png          native 1024 diffuse
  decode/maps/GalilACE_PhantomBeast_S.PNG      env-tint/spec map -> exponent+envmask
  decode/maps/GalilACE_PhantomBeast_N.PNG      normal (re-encoded unchanged)

Pipeline
  1. ComfyUI (127.0.0.1:8188) RealESRGAN_x4plus: diffuse 1024 -> 4096.
     Falls back to native PNG if ComfyUI is unreachable.
  2. _S -> RGBA png (alpha = luminance) so the mask survives whether the
     shader reads envmap/exponent masks from RGB or alpha. DXT5.
  3. VTFCmd -> VTF 7.4; diffuse dxt1, normal/s dxt5.
  4. VMT v2: env_cubemap + envmapmask(_S) + phongexponenttexture(_S)
     + phongalbedotint + halflambert + rimlight — closer to CF CFG intent
     (EnvCubeMapBrightness=3, SpecularMappingEnabled, SpecularHighlight=0.7).
  5. Stage into addon/ AND drop loose copies into migi/csgo/materials/...
     Loose files outrank pak entries, so `mat_reloadallmaterials` in console
     iterates without restart. Final packaging still = addon + MIGI UPDATE.

Report -> texture/report_v2.json
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"

WORK = REPO / "work" / "galil_ace_tianxi"
DEC = WORK / "decode"
OUT = WORK / "texture"
UP = OUT / "up"
ADDON = WORK / "addon" / "materials" / "models" / "weapons" / "v_models" / "cf_tianxi"
LOOSE = GAME / "migi" / "csgo" / "materials" / "models" / "weapons" / "v_models" / "cf_tianxi"

MAT = "models/weapons/v_models/cf_tianxi"
COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

GUN_DIFFUSE = DEC / "PV-GalilACE_PhantomBeast.png"
GUN_S = DEC / "maps" / "GalilACE_PhantomBeast_S.PNG"
GUN_N = DEC / "maps" / "GalilACE_PhantomBeast_N.PNG"


def vtfcmd(png: Path, dest: Path, fmt: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(dest.parent),
         "-format", fmt, "-version", "7.4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = dest.parent / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {png.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def comfy_alive() -> bool:
    try:
        urllib.request.urlopen(COMFY + "/system_stats", timeout=3)
        return True
    except Exception:
        return False


def comfy_upscale(img: Path, prefix: str, timeout=300) -> Path | None:
    """4x RealESRGAN via ComfyUI; returns output png path or None."""
    shutil.copy(img, COMFY_IN / img.name)
    wf = {
        "1": {"class_type": "LoadImage", "inputs": {"image": img.name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x4plus.pth"}},
        "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["3", 0]}},
    }
    req = urllib.request.Request(
        COMFY + "/prompt", data=json.dumps({"prompt": wf}).encode(),
        headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = json.loads(urllib.request.urlopen(COMFY + "/history/" + pid).read())
        if pid in h and h[pid].get("status", {}).get("completed"):
            for node in h[pid]["outputs"].values():
                for im in node.get("images", []):
                    src = COMFY_OUT / im["filename"]
                    if src.is_file():
                        dst = UP / ("4x_" + img.name)
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(src, dst)
                        return dst
            return None
        time.sleep(2)
    return None


def mask_with_luminance_alpha(src: Path, dst: Path) -> Path:
    """_S -> RGBA png, alpha channel = luminance(_S)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    lum = im.convert("L")
    im.putalpha(lum)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


GUN_VMT = '''"VertexLitGeneric"
{{
	"$basetexture" "{0}/cf_galilace_pb"
	"$bumpmap" "{0}/cf_galilace_pb_n"
	"$phong" "1"
	"$phongexponenttexture" "{0}/cf_galilace_pb_s"
	"$phongboost" "1"
	"$phongfresnelranges" "[0.2 0.6 1]"
	"$phongalbedotint" "1"
	"$envmap" "env_cubemap"
	"$envmapmask" "{0}/cf_galilace_pb_s"
	"$envmaptint" "[0.55 0.55 0.7]"
	"$envmapfresnel" "1"
	"$halflambert" "1"
	"$rimlight" "1"
	"$rimlightexponent" "10"
	"$rimlightboost" "0.4"
	"$nocull" "0"
}}
'''

ARM_VMT = '''"VertexLitGeneric"
{{
	"$basetexture" "{0}/{1}"
	"$bumpmap" "{0}/{1}_n"
	"$phong" "1"
	"$phongexponent" "8"
	"$phongboost" "0.6"
	"$phongfresnelranges" "[0.1 0.5 1]"
	"$phongalbedotint" "1"
	"$halflambert" "1"
	"$nocull" "0"
}}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"comfy": False, "files": []}

    diffuse = GUN_DIFFUSE
    if comfy_alive():
        up = comfy_upscale(GUN_DIFFUSE, "galilace_diffuse")
        if up:
            diffuse = up
            report["comfy"] = True
            report["upscaled"] = up.name
    report["diffuse_src"] = str(diffuse)

    s_mask = OUT / "galilace_pb_s_mask.png"
    try:
        mask_with_luminance_alpha(GUN_S, s_mask)
        report["mask_alpha"] = True
    except ImportError:
        s_mask = GUN_S
        report["mask_alpha"] = False

    vtfcmd(diffuse, ADDON / "cf_galilace_pb.vtf", "dxt1")
    vtfcmd(GUN_N, ADDON / "cf_galilace_pb_n.vtf", "dxt5")
    vtfcmd(s_mask, ADDON / "cf_galilace_pb_s.vtf", "dxt5")

    (ADDON / "cf_galilace_pb.vmt").write_text(GUN_VMT.format(MAT), encoding="utf-8")
    for name in ("cf_foxhand_bl", "cf_foxarm_bl"):
        (ADDON / f"{name}.vmt").write_text(ARM_VMT.format(MAT, name), encoding="utf-8")

    LOOSE.mkdir(parents=True, exist_ok=True)
    for f in sorted(ADDON.iterdir()):
        shutil.copy(f, LOOSE / f.name)
        report["files"].append(f.name)

    report["loose_dir"] = str(LOOSE)
    (OUT / "report_v2.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n[texture v2] DONE — in-game: sv_cheats 1; mat_reloadallmaterials")


if __name__ == "__main__":
    main()
