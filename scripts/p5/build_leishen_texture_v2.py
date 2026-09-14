# -*- coding: utf-8 -*-
"""Build a sharper, brighter M4A1-雷神 diffuse and deploy it to one addon.

Pipeline: native 1024 diffuse -> ComfyUI RealESRGAN 4x -> 2048 Lanczos ->
gamma/brightness/color correction -> uncompressed BGRA8888 VTF.
The normal map is intentionally left at its native 1024 resolution.
MIGI REBUILD remains a user action.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageStat

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"

WORK = REPO / "work" / "p5_leishen"
SOURCE = WORK / "p6" / "_png" / "diffuse_rgb.png"
OUT = WORK / "texture_v2"
UP = OUT / "up"
CORRECTED = OUT / "leishen_diffuse_2048.png"
STAGING = WORK / "p6" / "addon" / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"
MIGI_ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_leishen_m4a4_p6" / "materials" / "models" / "weapons" / "v_models" / "rif_m4a1"

COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

GAMMA = 0.72
BRIGHTNESS = 1.08
COLOR = 1.08
CONTRAST = 1.03

VMT = '''"VertexLitGeneric"
{
	"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"
	"$bumpmap" "models/weapons/v_models/rif_m4a1/rif_m4a1_normal"
	"$phong" "1"
	"$phongexponent" "48"
	"$phongboost" "2"
	"$phongfresnelranges" "[0.05 0.45 1]"
	"$phongalbedotint" "1"
	"$nocull" "0"
}
'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_stats(path: Path) -> dict:
    image = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(image)
    return {
        "size": list(image.size),
        "mean_rgb": [round(value, 3) for value in stat.mean],
        "extrema": [list(value) for value in image.getextrema()],
    }


def comfy_upscale(source: Path, timeout: int = 300) -> Path:
    cached = UP / "4x_leishen_diffuse.png"
    if cached.is_file():
        return cached
    urllib.request.urlopen(COMFY + "/system_stats", timeout=3)
    input_name = "leishen_diffuse_rgb.png"
    shutil.copy2(source, COMFY_IN / input_name)
    workflow = {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x4plus.pth"}},
        "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"filename_prefix": "leishen_diffuse", "images": ["3", 0]}},
    }
    request = urllib.request.Request(
        COMFY + "/prompt",
        data=json.dumps({"prompt": workflow}).encode(),
        headers={"Content-Type": "application/json"},
    )
    prompt_id = json.loads(urllib.request.urlopen(request).read())["prompt_id"]
    started = time.time()
    while time.time() - started < timeout:
        history = json.loads(urllib.request.urlopen(COMFY + "/history/" + prompt_id).read())
        if prompt_id in history and history[prompt_id].get("status", {}).get("completed"):
            for node in history[prompt_id]["outputs"].values():
                for output in node.get("images", []):
                    result = COMFY_OUT / output["filename"]
                    if result.is_file():
                        cached.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(result, cached)
                        return cached
            break
        time.sleep(2)
    raise RuntimeError("ComfyUI did not produce the 雷神 diffuse")


def correct_diffuse(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)
    lut = [min(255, round(255 * ((value / 255) ** GAMMA) * BRIGHTNESS)) for value in range(256)]
    image = image.point(lut * 3)
    image = ImageEnhance.Color(image).enhance(COLOR)
    image = ImageEnhance.Contrast(image).enhance(CONTRAST)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def build_vtf(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(VTFCMD), "-file", str(source), "-output", str(destination.parent),
        "-format", "bgra8888", "-version", "7.4",
        "-flag", "TRILINEAR", "-flag", "ANISOTROPIC",
    ]
    process = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    generated = destination.parent / f"{source.stem}.vtf"
    if process.returncode != 0 or not generated.is_file():
        raise RuntimeError(process.stderr or process.stdout or "VTFCmd failed")
    if generated != destination:
        generated.replace(destination)


def main() -> int:
    if not SOURCE.is_file():
        raise RuntimeError(f"missing decoded diffuse: {SOURCE}")
    if not MIGI_ADDON.is_dir():
        raise RuntimeError(f"missing unified MIGI addon: {MIGI_ADDON}")

    upscaled = comfy_upscale(SOURCE)
    correct_diffuse(upscaled, CORRECTED)

    staged_vtf = STAGING / "rif_m4a1.vtf"
    staged_vmt = STAGING / "rif_m4a1.vmt"
    build_vtf(CORRECTED, staged_vtf)
    staged_vmt.write_text(VMT, encoding="utf-8")

    for source in (staged_vtf, staged_vmt):
        destination = MIGI_ADDON / source.name
        shutil.copy2(source, destination)
        if sha256(source) != sha256(destination):
            raise RuntimeError(f"staging/MIGI addon mismatch: {source.name}")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "LEISHEN_TEXTURE_V2_STAGED",
        "source": image_stats(SOURCE),
        "upscaled": image_stats(upscaled),
        "corrected": image_stats(CORRECTED),
        "tone": {
            "gamma": GAMMA,
            "brightness": BRIGHTNESS,
            "color": COLOR,
            "contrast": CONTRAST,
        },
        "vtf": {
            "format": "BGRA8888",
            "size": [2048, 2048],
            "sha256": sha256(staged_vtf),
            "bytes": staged_vtf.stat().st_size,
        },
        "vmt_sha256": sha256(staged_vmt),
        "staging_addon": str(STAGING),
        "migi_addon": str(MIGI_ADDON),
        "ab_hash_verified": True,
        "migi_rebuild": "USER_REQUIRED",
    }
    (OUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\n[leishen texture v2] DONE — user must click MIGI REBUILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
