# -*- coding: utf-8 -*-
"""Galil ACE-天袭 texture pass v7 — albedo-colored metal + sparse selfillum.

v6 removed noise but map cubemap reflection stayed visible in shadow and washed
the weapon white. v7 disables envmap/rimlight completely: metallic response is
albedo-tinted Phong, so gold/blue highlights inherit the weapon's own diffuse
color and remain coupled to viewmodel lighting. Glow still uses sparse _M G/B.

Iteration loop: rebuild into staging + real MIGI addon -> verify hashes -> user
runs MIGI REBUILD -> verify packed hashes -> in-game check.
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
MIGI_ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1" / "materials" / "models" / "weapons" / "v_models" / "cf_tianxi"
# Loose files under migi/csgo do NOT override pak. Build into the tracked
# staging addon, copy to the real MIGI addon, then the user runs REBUILD.

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


def vtf_framecount(path: Path) -> int:
    data = path.read_bytes()
    return int.from_bytes(data[16:18], "little") if len(data) > 20 else 0


def dds_cubemap_to_vtf(dds: Path, vtf: Path) -> bool:
    """Repack a no-mip cubemap DDS (DXT1/DXT3/DXT5, 6 faces) into a VTF 7.2
    cubemap. DDS stores face-major blocks; VTF stores mip-major/face-minor —
    with 1 mip level the byte order is identical, so this is a pure repack."""
    import struct
    d = dds.read_bytes()
    if d[:4] != b"DDS ":
        return False
    h, w = struct.unpack("<II", d[12:20])
    mips = struct.unpack("<I", d[28:32])[0] or 1
    fourcc = d[84:88]
    caps2 = struct.unpack("<I", d[112:116])[0]
    if not (caps2 & 0x200):  # DDSCAPS2_CUBEMAP
        return False
    fmt_map = {b"DXT1": 13, b"DXT3": 14, b"DXT5": 15}
    if fourcc not in fmt_map or mips != 1:
        return False
    blk = 8 if fourcc == b"DXT1" else 16
    face_bytes = (w // 4) * (h // 4) * blk
    if len(d) < 128 + 6 * face_bytes:
        return False
    # VTF ENVMAP cubemaps carry a 7th spheremap slice — pad with face0.
    body = d[128:128 + 6 * face_bytes] + d[128:128 + face_bytes]

    # 16x16 DXT1 thumbnail, solid gold block (rgb565 ~ #c8a850)
    def rgb565(r, g, b):
        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    c = rgb565(200, 168, 80)
    thumb = struct.pack("<HHI", c, c, 0) * 16

    hdr = bytearray(80)
    hdr[0:4] = b"VTF\x00"
    struct.pack_into("<II", hdr, 4, 7, 2)          # version 7.2
    struct.pack_into("<I", hdr, 12, 80)            # header size
    struct.pack_into("<HH", hdr, 16, w, h)
    struct.pack_into("<I", hdr, 20, 0x4000)        # TEXTUREFLAGS_ENVMAP
    struct.pack_into("<HH", hdr, 24, 1, 0)         # frames=1, firstFrame=0
    struct.pack_into("<fff", hdr, 32, 0.5, 0.5, 0.5)
    struct.pack_into("<f", hdr, 48, 1.0)           # bumpmap scale
    struct.pack_into("<I", hdr, 52, fmt_map[fourcc])
    hdr[56] = 1                                    # mip count
    struct.pack_into("<I", hdr, 57, 13)            # lowres = DXT1
    hdr[61] = 16
    hdr[62] = 16
    struct.pack_into("<H", hdr, 63, 1)             # depth
    vtf.parent.mkdir(parents=True, exist_ok=True)
    vtf.write_bytes(bytes(hdr) + thumb + body)
    return True


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


def build_env_mask(src: Path, dst: Path) -> Path:
    from PIL import Image, ImageFilter, ImageOps
    mask = ImageOps.grayscale(Image.open(src).convert("RGB"))
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    mask = mask.point(lambda x: max(0, min(255, (x - 12) * 2)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    mask.convert("RGB").save(dst)
    return dst


def build_selfillum_mask(src: Path, dst: Path) -> Path:
    from PIL import Image, ImageChops, ImageFilter
    im = Image.open(src).convert("RGB")
    mask = ImageChops.lighter(im.getchannel("G"), im.getchannel("B"))
    mask = mask.point(lambda x: max(0, min(255, (x - 8) * 3)))
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    dst.parent.mkdir(parents=True, exist_ok=True)
    mask.convert("RGB").save(dst)
    return dst


def gun_vmt() -> str:
    return f'''"VertexLitGeneric"
{{
	"$basetexture" "{MAT}/cf_galilace_pb"
	"$bumpmap" "{MAT}/cf_galilace_pb_n"
	"$phong" "1"
	"$phongexponent" "48"
	"$phongboost" "2"
	"$phongfresnelranges" "[0.05 0.45 1]"
	"$phongalbedotint" "1"
	"$selfillum" "1"
	"$selfillummask" "{MAT}/cf_galilace_pb_m"
	"$selfillumtint" "[0.1 0.25 0.65]"
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

    m_mask = None
    if GUN_M.is_file():
        m_mask = build_selfillum_mask(GUN_M, OUT / "galilace_pb_m.png")

    report["envmap"] = "disabled; albedo-tinted phong only"

    # Diffuse: uncompressed BGRA8888 at 2048 — kills DXT block jaggies
    # (DXT1/5 share the same color blocks; resolution still 2x native 1024).
    dif_small = OUT / "galilace_pb_2048.png"
    if diffuse.is_file():
        from PIL import Image
        im = Image.open(diffuse)
        if im.width != 2048:
            im = im.resize((2048, 2048), Image.LANCZOS)
        im.save(dif_small)
        diffuse = dif_small
    vtfcmd(diffuse, ADDON / "cf_galilace_pb.vtf", "bgra8888")
    vtfcmd(GUN_N, ADDON / "cf_galilace_pb_n.vtf", "dxt5",
           flags=("TRILINEAR", "ANISOTROPIC", "NORMAL"))
    if m_mask:
        vtfcmd(m_mask, ADDON / "cf_galilace_pb_m.vtf", "bgra8888")

    vmt = gun_vmt()
    if not m_mask:  # no glow mask -> drop selfillum block
        vmt = "\n".join(l for l in vmt.splitlines() if "selfillum" not in l) + "\n"
    (ADDON / "cf_galilace_pb.vmt").write_text(vmt, encoding="utf-8")
    for name in ("cf_foxhand_bl", "cf_foxarm_bl"):
        (ADDON / f"{name}.vmt").write_text(ARM_VMT.format(MAT, name), encoding="utf-8")

    MIGI_ADDON.mkdir(parents=True, exist_ok=True)
    for f in sorted(ADDON.iterdir()):
        shutil.copy2(f, MIGI_ADDON / f.name)
        report["files"].append(f.name)
    report["migi_addon_dir"] = str(MIGI_ADDON)
    (OUT / "report_v2.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n[texture v7] DONE — MIGI addon staged; user must click REBUILD")


if __name__ == "__main__":
    main()
