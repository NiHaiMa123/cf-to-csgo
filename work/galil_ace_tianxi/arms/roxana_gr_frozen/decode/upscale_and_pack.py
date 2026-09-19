# -*- coding: utf-8 -*-
"""4x Roxana GR hand/arm diffuse (no native HD exists) and pack BGRA8888 VTF."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

_REPO = Path(r"D:\project\cf_to_csgo")
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

GAME = Path(_paths.game_dir())
VTFCMD = _REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
DEC = Path(__file__).resolve().parent
WORK = _REPO / "work" / "galil_ace_tianxi"
UP = DEC / "up"
MAT_REL = Path("materials/models/weapons/v_models/cf_tianxi")
ISOLATED = WORK / "native_vm" / "isolated_game" / "csgo" / MAT_REL
STAGING = WORK / "addon" / MAT_REL
MIGI = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1" / MAT_REL

COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

PAIRS = (
    ("FVIEW_HAND_Roxana_GR.png", "cf_roxana_hand_gr.vtf"),
    ("FVIEW_ARM_Roxana_GR.png", "cf_roxana_arm_gr.vtf"),
)


def comfy_upscale(img: Path, prefix: str, timeout=400) -> Path:
    cached = UP / ("4x_" + img.name)
    if cached.is_file():
        print("cached", cached)
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


def vtfcmd(src: Path, dest: Path, fmt: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(src), "-output", str(dest.parent),
           "-format", fmt, "-version", "7.4",
           "-flag", "TRILINEAR", "-flag", "ANISOTROPIC"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    produced = dest.parent / (src.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed {src.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def main() -> int:
    UP.mkdir(parents=True, exist_ok=True)
    for src_name, vtf_name in PAIRS:
        src = DEC / src_name
        up = comfy_upscale(src, "roxana_" + src.stem.lower())
        im = Image.open(up)
        if im.size != (2048, 2048):
            im = im.resize((2048, 2048), Image.LANCZOS)
            outp = UP / (src.stem + "_2048.png")
            im.save(outp)
            up = outp
            print("resized", up, im.size)
        else:
            print("keep 2048", up)
        for root in (ISOLATED, STAGING, MIGI):
            dest = root / vtf_name
            vtfcmd(up, dest, "bgra8888")
            print("vtf", dest, dest.stat().st_size)

    def files(root: Path):
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*") if p.is_file()}
    staging = WORK / "addon"
    migi = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1"
    A, B = files(staging), files(migi)
    mismatch = sorted(k for k in set(A) & set(B) if A[k] != B[k])
    extra = sorted(set(B) - set(A))
    missing = sorted(set(A) - set(B))
    print(f"A/B {len(A)}/{len(B)} missing={len(missing)} extra={len(extra)} mismatch={len(mismatch)}")
    if missing or extra or mismatch:
        raise SystemExit((missing[:10], extra[:10], mismatch[:10]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
