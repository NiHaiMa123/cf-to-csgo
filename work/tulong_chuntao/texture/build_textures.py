# -*- coding: utf-8 -*-
"""P4 — 屠龙-春桃 diffuse 4x + A.8.1 Phong VMT (no envmap)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
WORK = REPO / "work" / "tulong_chuntao"
DEC = WORK / "decode"
OUT = WORK / "texture"
UP = OUT / "up"
STAGING = WORK / "addon" / "materials" / "models" / "weapons" / "v_models" / "cf_tulong"
MAT = "models/weapons/v_models/cf_tulong"

COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

DIFFUSE = DEC / "PV-Kukri_Beast_spring.png"
NORMAL = DEC / "maps" / "Kukri_Beast_Spring_N.PNG"


def comfy_upscale(img: Path, prefix: str, timeout=400) -> Path:
    cached = UP / ("4x_" + img.stem + ".png")
    if cached.is_file():
        print("cached", cached, Image.open(cached).size)
        return cached
    urllib.request.urlopen(COMFY + "/system_stats", timeout=5)
    COMFY_IN.mkdir(parents=True, exist_ok=True)
    shutil.copy(img, COMFY_IN / img.name)
    wf = {
        "1": {"class_type": "LoadImage", "inputs": {"image": img.name}},
        "2": {"class_type": "UpscaleModelLoader",
              "inputs": {"model_name": "RealESRGAN_x4plus.pth"}},
        "3": {"class_type": "ImageUpscaleWithModel",
              "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": prefix, "images": ["3", 0]}},
    }
    req = urllib.request.Request(
        COMFY + "/prompt", data=json.dumps({"prompt": wf}).encode(),
        headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    print("queued", prefix, pid)
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = json.loads(urllib.request.urlopen(COMFY + "/history/" + pid).read())
        if pid in h and h[pid].get("status", {}).get("completed"):
            for node in h[pid]["outputs"].values():
                for im in node.get("images", []):
                    src = COMFY_OUT / im["filename"]
                    if src.is_file():
                        cached.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(src, cached)
                        print("saved", cached, Image.open(cached).size)
                        return cached
            raise RuntimeError(f"no output image for {prefix}")
        time.sleep(2)
    raise TimeoutError(prefix)


def vtfcmd(src: Path, dest: Path, fmt: str, flags: tuple[str, ...] = ("TRILINEAR", "ANISOTROPIC")):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(src), "-output", str(dest.parent),
           "-format", fmt, "-version", "7.4"]
    for fl in flags:
        cmd += ["-flag", fl]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    produced = dest.parent / (src.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {src.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def gun_vmt() -> str:
    return f'''"VertexLitGeneric"
{{
	"$basetexture" "{MAT}/cf_kukri_spring"
	"$phong" "1"
	"$halflambert" "1"
	"$phongexponent" "48"
	"$phongboost" "8"
	"$phongfresnelranges" "[0.05 0.45 1]"
	"$phongalbedotint" "1"
	"$nocull" "0"
}}
'''


def main() -> int:
    UP.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    up = comfy_upscale(DIFFUSE, "tulong_chuntao")
    im = Image.open(up)
    if im.size != (2048, 2048):
        im = im.resize((2048, 2048), Image.LANCZOS)
        outp = UP / "kukri_spring_2048.png"
        im.save(outp)
        used = outp
        print("resized", used, im.size)
    else:
        used = up
        print("keep 2048", used)
    vtfcmd(used, STAGING / "cf_kukri_spring.vtf", "bgra8888")
    vtfcmd(NORMAL, STAGING / "cf_kukri_spring_n.vtf", "dxt5",
           ("TRILINEAR", "ANISOTROPIC", "NORMAL"))
    (STAGING / "cf_kukri_spring.vmt").write_text(gun_vmt(), encoding="utf-8")
    report = {
        "diffuse_src": str(DIFFUSE),
        "upscaled": str(used),
        "up_size": list(Image.open(used).size),
        "vmt": "phong 48/8 Half-Lambert no envmap/bumpmap",
        "staging": str(STAGING),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("wrote", STAGING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
