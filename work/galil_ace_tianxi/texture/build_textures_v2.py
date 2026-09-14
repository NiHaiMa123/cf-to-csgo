# -*- coding: utf-8 -*-
"""Galil ACE-天袭 texture pass v3 — 4x diffuse + CF gold envcube + selfillum.

v2 problem: uniform envmap (mask = _S luminance, mostly bright) + halflambert
produced a grey film with no metal. v3:
  - _S with $envmapcontrast 1 -> only genuinely bright regions reflect
  - CF Gold_map01.DDS cubemap as $envmap (authentic VVIP gold reflection;
    falls back to env_cubemap if DDS->VTF fails)
  - _M overlay-alpha mask -> $selfillummask (blue energy lines glow)
  - halflambert removed (contrast back)

Iteration without restart: files are staged to addon/ AND dropped loose into
migi/csgo/materials/... (gameinfo mounts the dir -> loose beats pak).
In-game: `sv_cheats 1; mat_reloadallmaterials`.
Final packaging still = addon dir + user-run MIGI UPDATE.
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
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
CF = Path(_paths.cf_dir())
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"

WORK = REPO / "work" / "galil_ace_tianxi"
DEC = WORK / "decode"
OUT = WORK / "texture"
UP = OUT / "up"
SRC = OUT / "src"
ADDON = WORK / "addon" / "materials" / "models" / "weapons" / "v_models" / "cf_tianxi"
LOOSE = GAME / "migi" / "csgo" / "materials" / "models" / "weapons" / "v_models" / "cf_tianxi"

MAT = "models/weapons/v_models/cf_tianxi"
COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

GUN_DIFFUSE = DEC / "PV-GalilACE_PhantomBeast.png"
GUN_S = DEC / "maps" / "GalilACE_PhantomBeast_S.PNG"
GUN_N = DEC / "maps" / "GalilACE_PhantomBeast_N.PNG"
GUN_M = SRC / "ModelTextures" / "AlphaMap" / "GalilACE_PhantomBeast_M.PNG"
GOLD_DDS = SRC / "ModelTextures" / "EnvCubeMap" / "Gold_map01.DDS"

EXTRA_WANTED = [
    "ModelTextures/AlphaMap/GalilACE_PhantomBeast_M.PNG",
    "ModelTextures/EnvCubeMap/Gold_map01.DDS",
    "ModelTextures/OVERLAYMAP/Blue.PNG",
]


def extract_extra() -> dict:
    """Pull _M mask / gold cubemap / Blue overlay from REZ (md5-verified)."""
    wanted = {w.replace("\\", "/").upper(): w for w in EXTRA_WANTED}
    found = {}
    for index_path in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            k = e["full_path"].replace("\\", "/").upper()
            if k in wanted and is_complete_directory_md5(e.get("md5")):
                found[k] = (index_path, e)
    out = {}
    for k, w in wanted.items():
        if k not in found:
            out[w] = "MISSING"
            continue
        data, _prov = read_verified_payload(*found[k])
        dest = SRC / w.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        out[w] = f"{len(data)}B"
    return out


def vtfcmd(src: Path, dest: Path, fmt: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(src), "-output", str(dest.parent),
         "-format", fmt, "-version", "7.4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = dest.parent / (src.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {src.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def vtf_framecount(path: Path) -> int:
    data = path.read_bytes()
    return int.from_bytes(data[16:18], "little") if len(data) > 20 else 0


def comfy_upscale(img: Path, prefix: str, timeout=300) -> Path | None:
    cached = UP / ("4x_" + img.name)
    if cached.is_file():
        return cached
    try:
        urllib.request.urlopen(COMFY + "/system_stats", timeout=3)
    except Exception:
        return None
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
                        cached.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(src, cached)
                        return cached
            return None
        time.sleep(2)
    return None


def rgba_luminance_alpha(src: Path, dst: Path) -> Path:
    """RGB kept, alpha = luminance (or native alpha preserved if present)."""
    from PIL import Image
    im = Image.open(src)
    if "A" not in im.getbands():
        im = im.convert("RGB")
        im.putalpha(im.convert("L"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


def gun_vmt(envmap: str) -> str:
    return f'''"VertexLitGeneric"
{{
	"$basetexture" "{MAT}/cf_galilace_pb"
	"$bumpmap" "{MAT}/cf_galilace_pb_n"
	"$phong" "1"
	"$phongexponenttexture" "{MAT}/cf_galilace_pb_s"
	"$phongboost" "2"
	"$phongfresnelranges" "[0.1 0.45 1]"
	"$phongalbedotint" "1"
	"$envmap" "{envmap}"
	"$envmapmask" "{MAT}/cf_galilace_pb_s"
	"$envmapcontrast" "1"
	"$envmapsaturation" "1"
	"$envmaptint" "[0.6 0.55 0.5]"
	"$envmapfresnel" "1"
	"$envmapFresnelMinMaxExp" "[0 0.7 3]"
	"$selfillum" "1"
	"$selfillummask" "{MAT}/cf_galilace_pb_m"
	"$selfillumtint" "[0.35 0.6 1.0]"
	"$rimlight" "1"
	"$rimlightexponent" "12"
	"$rimlightboost" "0.35"
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
	"$nocull" "0"
}}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"extracted": extract_extra(), "files": []}

    diffuse = comfy_upscale(GUN_DIFFUSE, "galilace_diffuse") or GUN_DIFFUSE
    report["diffuse_src"] = str(diffuse)

    s_mask = rgba_luminance_alpha(GUN_S, OUT / "galilace_pb_s_rgba.png")
    m_mask = None
    if GUN_M.is_file():
        m_mask = rgba_luminance_alpha(GUN_M, OUT / "galilace_pb_m_rgba.png")

    # Gold_map01.DDS -> VTFCmd only converts face0 (frames=1, not a cubemap);
    # proper repack is a TODO. For now use map env_cubemap (stock convention).
    envmap = "env_cubemap"
    report["envmap"] = envmap

    vtfcmd(diffuse, ADDON / "cf_galilace_pb.vtf", "dxt1")
    vtfcmd(GUN_N, ADDON / "cf_galilace_pb_n.vtf", "dxt5")
    vtfcmd(s_mask, ADDON / "cf_galilace_pb_s.vtf", "dxt5")
    if m_mask:
        vtfcmd(m_mask, ADDON / "cf_galilace_pb_m.vtf", "dxt5")

    vmt = gun_vmt(envmap)
    if not m_mask:  # no glow mask -> drop selfillum block
        vmt = "\n".join(l for l in vmt.splitlines() if "selfillum" not in l) + "\n"
    (ADDON / "cf_galilace_pb.vmt").write_text(vmt, encoding="utf-8")
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
    print("\n[texture v3] DONE — in-game: sv_cheats 1; mat_reloadallmaterials")


if __name__ == "__main__":
    main()
