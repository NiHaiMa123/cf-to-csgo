# -*- coding: utf-8 -*-
"""Decode Nini GR arm LTB/DTX and 4x the diffuse (no native HD hunt)."""
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
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import n05a_decoder_provenance_audit as n05a  # noqa: E402

WORK = _REPO / "work" / "galil_ace_tianxi"
ACQ = WORK / "acquire" / "verified_root"
DEC = Path(__file__).resolve().parent
UP = DEC / "up"
CFREZ = _REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"

COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

LTB = ACQ / "Models" / "PLAYERVIEW" / "ArmModel" / "Arm_Nini_GR.LTB"
DTX = {
    "FVIEW_HAND_Nini_GR.png": ACQ / "ModelTextures" / "PLAYERVIEW" / "FVIEW_HAND_Nini_GR.DTX",
    "FVIEW_ARM_Nini_GR.png": ACQ / "ModelTextures" / "PLAYERVIEW" / "FVIEW_ARM_Nini_GR.DTX",
}
MAPS = [
    ACQ / "ModelTextures" / "NormalMap" / "FVIEW_HAND_Nini_GR_N.PNG",
    ACQ / "ModelTextures" / "NormalMap" / "FVIEW_ARM_Nini_GR_N.PNG",
    ACQ / "ModelTextures" / "SpecularMap" / "FVIEW_HAND_Nini_GR_S.PNG",
    ACQ / "ModelTextures" / "SpecularMap" / "FVIEW_ARM_Nini_GR_S.PNG",
    ACQ / "ModelTextures" / "AlphaMap" / "FVIEW_HAND_Nini_GR_A.PNG",
    ACQ / "ModelTextures" / "AlphaMap" / "FVIEW_ARM_Nini_GR_A.PNG",
    ACQ / "ModelTextures" / "Shader" / "AdvancedShader" / "Arm_Nini_GR_Piece0.CFG",
    ACQ / "ModelTextures" / "Shader" / "AdvancedShader" / "Arm_Nini_GR_Piece1.CFG",
]


def dump_skin() -> None:
    if not CFREZ.is_file():
        raise FileNotFoundError(CFREZ)
    if not LTB.is_file():
        raise FileNotFoundError(LTB)
    skin_out = DEC / "cf_skin_nini_gr.json"
    proc = subprocess.run(
        [str(CFREZ), "--dump-ltb-skin", "--input", str(LTB), "--output", str(skin_out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    print("dump-ltb-skin:", (proc.stdout or proc.stderr).strip()[:600])
    if proc.returncode != 0 or not skin_out.is_file():
        raise RuntimeError(f"dump-ltb-skin failed: {proc.stderr}")
    skin = json.loads(skin_out.read_text(encoding="utf-8"))
    print(f"skin meshes={len(skin['meshes'])} nodes={len(skin['skeleton'])}")
    for n in skin["skeleton"]:
        print(f"  bone {n['index']:02d} {n['name']}")
    for m in skin["meshes"]:
        print(f"  mesh {m['name']}: v={m['vertex_count']} tri={len(m['triangles'])//3}")


def decode_dtx() -> None:
    DEC.mkdir(parents=True, exist_ok=True)
    for png_name, dtx_path in DTX.items():
        data = dtx_path.read_bytes()
        res = n05a.decode_repo_pixels(data)
        if not res.get("ok"):
            raise RuntimeError(f"DTX decode failed {dtx_path.name}: {res.get('reason')}")
        out = DEC / png_name
        res["image"].save(out)
        print(f"dtx {dtx_path.name} -> {out.name} {res['image'].size} "
              f"fmt={res.get('format')} bytes={len(data)}")
    for p in MAPS:
        if p.is_file():
            shutil.copy2(p, DEC / p.name)
            print("copied", p.name, p.stat().st_size)
        else:
            print("MISSING map", p)


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


def upscale_diffuse() -> None:
    UP.mkdir(parents=True, exist_ok=True)
    report = {"character": "Nini GR", "files": []}
    for src_name in DTX:
        src = DEC / src_name
        up = comfy_upscale(src, "nini_" + src.stem.lower())
        im = Image.open(up)
        if im.size != (2048, 2048):
            im = im.resize((2048, 2048), Image.LANCZOS)
            outp = UP / (src.stem + "_2048.png")
            im.save(outp)
            # keep both the raw 4x and the 2048 the VM builder consumes
            shutil.copy2(outp, UP / ("4x_" + src.stem + ".png"))
            print("resized", outp, im.size)
            used = outp
        else:
            used = up
            print("keep 2048", used)
        report["files"].append({
            "src": src.name,
            "src_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "src_size": list(Image.open(src).size),
            "up_path": used.name,
            "up_size": list(Image.open(used).size),
        })
    (DEC / "upscale_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    DEC.mkdir(parents=True, exist_ok=True)
    dump_skin()
    decode_dtx()
    upscale_diffuse()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
