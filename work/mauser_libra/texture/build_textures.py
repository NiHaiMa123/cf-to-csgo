# -*- coding: utf-8 -*-
"""P4 — 毛瑟-天秤座 CFG/channel-aware Source material recovery."""
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

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import _paths  # noqa: E402
import cf_source_material  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
WORK = REPO / "work" / "mauser_libra"
DEC = WORK / "decode"
OUT = WORK / "texture"
UP = OUT / "up"
STAGING = WORK / "addon" / "materials" / "models" / "weapons" / "v_models" / "cf_mauser"
MAT = "models/weapons/v_models/cf_mauser"

COMFY = "http://127.0.0.1:8188"
COMFY_IN = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

DIFFUSE = DEC / "PV-M1896_Libra.png"
SPECULAR = DEC / "maps" / "M1896_Libra_S.TGA"
NORMAL = DEC / "maps" / "M1896_Libra_N.TGA"
ALPHA = DEC / "maps" / "M1896_Libra_alpha.TGA"
CUBEMAP = DEC / "maps" / "LobbyCube.DDS"
CFG = DEC / "maps" / "M1896_Libra.CFG"


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


def vtfcmd(src: Path, dest: Path, fmt: str,
           flags: tuple[str, ...] = ("TRILINEAR", "ANISOTROPIC"),
           nomip: bool = False):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(src), "-output", str(dest.parent),
           "-format", fmt, "-alphaformat", fmt, "-version", "7.4"]
    if nomip:
        cmd.append("-nomipmaps")
    for fl in flags:
        cmd += ["-flag", fl]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    produced = dest.parent / (src.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {src.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def dds_cubemap_to_vtf(dds: Path, vtf: Path) -> bool:
    import struct
    data = dds.read_bytes()
    if data[:4] != b"DDS ":
        return False
    height, width = struct.unpack("<II", data[12:20])
    mips = struct.unpack("<I", data[28:32])[0] or 1
    fourcc = data[84:88]
    caps2 = struct.unpack("<I", data[112:116])[0]
    formats = {b"DXT1": 13, b"DXT3": 14, b"DXT5": 15}
    if not caps2 & 0x200 or fourcc not in formats or mips != 1:
        return False
    block = 8 if fourcc == b"DXT1" else 16
    face_bytes = (width // 4) * (height // 4) * block
    if len(data) < 128 + 6 * face_bytes:
        return False
    body = data[128:128 + 6 * face_bytes] + data[128:128 + face_bytes]
    color = ((128 >> 3) << 11) | ((128 >> 2) << 5) | (128 >> 3)
    thumb = struct.pack("<HHI", color, color, 0) * 16
    header = bytearray(80)
    header[0:4] = b"VTF\x00"
    struct.pack_into("<II", header, 4, 7, 2)
    struct.pack_into("<I", header, 12, 80)
    struct.pack_into("<HH", header, 16, width, height)
    struct.pack_into("<I", header, 20, 0x4000)
    struct.pack_into("<HH", header, 24, 1, 0)
    struct.pack_into("<fff", header, 32, 0.5, 0.5, 0.5)
    struct.pack_into("<f", header, 48, 1.0)
    struct.pack_into("<I", header, 52, formats[fourcc])
    header[56] = 1
    struct.pack_into("<I", header, 57, 13)
    header[61] = 16
    header[62] = 16
    struct.pack_into("<H", header, 63, 1)
    vtf.parent.mkdir(parents=True, exist_ok=True)
    vtf.write_bytes(bytes(header) + thumb + body)
    return True


def channel_stats(image: Image.Image) -> dict:
    result = {}
    for name, band in zip(image.getbands(), image.split(), strict=True):
        hist = band.histogram()
        count = image.width * image.height
        result[name] = {
            "min": band.getextrema()[0],
            "max": band.getextrema()[1],
            "mean": sum(i * n for i, n in enumerate(hist)) / count,
        }
    return result


def build_source_maps(diffuse: Path, profile: dict) -> tuple[Path, Path, Path, Path, Path, dict]:
    size = (2048, 2048)
    spec = Image.open(SPECULAR).convert("RGB")
    alpha = Image.open(ALPHA).convert("RGB")
    rgba, response, lightwarp, env_overlay, proxy = cf_source_material.build_lit_specular_proxy(
        Image.open(diffuse), spec, alpha, profile, size, Image.open(CUBEMAP))
    diffuse_out = UP / "mauser_libra_rgba_2048.png"
    response_out = UP / "mauser_libra_spec_response.png"
    lightwarp_out = UP / "mauser_libra_lightwarp.png"
    env_overlay_out = UP / "mauser_libra_env_overlay.png"
    dummy_out = UP / "mauser_libra_emissive_dummy.png"
    rgba.save(diffuse_out)
    response.save(response_out)
    lightwarp.save(lightwarp_out)
    env_overlay.save(env_overlay_out)
    Image.new("RGBA", (4, 4), (255, 255, 255, 0)).save(dummy_out)
    return diffuse_out, response_out, lightwarp_out, env_overlay_out, dummy_out, {
        "specular": channel_stats(spec),
        "alpha": channel_stats(alpha),
        "source_response": channel_stats(response),
        "source_lightwarp": channel_stats(lightwarp),
        "source_env_overlay": channel_stats(env_overlay),
        "proxy": proxy,
    }


def gun_vmt(profile: dict) -> str:
    return cf_source_material.vertexlit_vmt(
        MAT, "cf_mauser_libra", "cf_mauser_libra_n",
        "cf_mauser_lightwarp", "cf_mauser_env_overlay",
        "cf_mauser_emissive_dummy", profile)


def main() -> int:
    UP.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    try:
        up = comfy_upscale(DIFFUSE, "mauser_libra")
    except Exception as e:  # noqa: BLE001
        print("comfy unavailable, PIL resize:", e)
        up = UP / "4x_PV-M1896_Libra.png"
        Image.open(DIFFUSE).convert("RGB").resize((2048, 2048), Image.LANCZOS).save(up)
    im = Image.open(up).convert("RGB")
    if im.size != (2048, 2048):
        im = im.resize((2048, 2048), Image.LANCZOS)
        outp = UP / "mauser_libra_2048.png"
        im.save(outp)
        used = outp
        print("resized", used, im.size)
    else:
        used = up
        print("keep", used, im.size)
    cfg = cf_source_material.parse_cfg(CFG)
    profile = cf_source_material.classify_player_view(cfg)
    diffuse_rgba, response_mask, lightwarp_map, env_overlay, dummy, map_stats = build_source_maps(used, profile)
    vtfcmd(diffuse_rgba, STAGING / "cf_mauser_libra.vtf", "bgra8888")
    vtfcmd(response_mask, STAGING / "cf_mauser_spec_response.vtf", "dxt1")
    vtfcmd(lightwarp_map, STAGING / "cf_mauser_lightwarp.vtf", "bgr888",
           ("POINTSAMPLE", "CLAMPS", "CLAMPT", "NOMIP", "NOLOD"), nomip=True)
    vtfcmd(env_overlay, STAGING / "cf_mauser_env_overlay.vtf", "bgr888")
    vtfcmd(dummy, STAGING / "cf_mauser_emissive_dummy.vtf", "bgra8888",
           ("POINTSAMPLE", "CLAMPS", "CLAMPT", "NOMIP", "NOLOD"), nomip=True)
    if NORMAL.is_file():
        vtfcmd(NORMAL, STAGING / "cf_mauser_libra_n.vtf", "dxt5",
               ("TRILINEAR", "ANISOTROPIC", "NORMAL"))
    cube_vtf = STAGING / "cf_mauser_lobbycube.vtf"
    if not dds_cubemap_to_vtf(CUBEMAP, cube_vtf):
        raise RuntimeError(f"unsupported cubemap DDS: {CUBEMAP}")
    (STAGING / "cf_mauser_libra.vmt").write_text(gun_vmt(profile), encoding="utf-8")
    report = {
        "diffuse_src": str(DIFFUSE),
        "upscaled": str(used),
        "source_diffuse": str(diffuse_rgba),
        "up_size": list(Image.open(used).size),
        "cfg": str(CFG),
        "shader_profile": profile,
        "channel_mapping": {
            "specular_rgb_x_alpha_g": "low-pass base alpha -> $basemapalphaphongmask",
            "specular_chromaticity": "$phongtint",
            "cubemap_rgb_x_alpha_b_x_env_brightness": "low-pass RGB -> $emissiveblendbasetexture (light-independent additive pass)",
            "stable_divided_by_stable_plus_directional": "$lightwarptexture dark-floor calibration",
            "lobby_cube_dds": "audited but not bound for transformed-Snell family",
        },
        "map_stats": map_stats,
        "source_approximation": {
            "runtime_envmap": False,
            "reason": "Source VertexLitGeneric cannot reproduce CF transformed reflect/refract cube rays",
            "cubemap_sha256": hashlib.sha256(CUBEMAP.read_bytes()).hexdigest(),
            "phong": {
                "exponent": profile["source_phong_exponent"],
                "boost": profile["source_phong_boost"],
                "tint": profile["source_phong_tint"],
                "fresnel_ranges": profile["source_phong_fresnel_ranges"],
                "albedo_tint": False,
            },
            "lighting_stability": {
                "mean": profile["source_stability_mean"],
                "source_lit_fraction": profile["source_lit_fraction"],
                "lightwarp_floor": profile["source_lightwarp_floor"],
                "lightwarp": "cf_mauser_lightwarp",
                "emissiveblend": {
                    "base_texture": "cf_mauser_env_overlay",
                    "strength": profile["source_emissive_strength"],
                    "role": "stable additive env-proxy pass; independent of scene direct light",
                },
            },
        },
        "staging": str(STAGING),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("wrote", STAGING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
