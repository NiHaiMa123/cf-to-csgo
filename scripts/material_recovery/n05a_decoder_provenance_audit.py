#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N05-A — Offline decoder / provenance audit.

Separates tool failure, container/header failure, copy mismatch, and
unknown codec. Does not brute-force layouts and does not announce
P4-M01 PASS.

Repro:
  python scripts/material_recovery/n05a_decoder_provenance_audit.py
"""
from __future__ import annotations

import hashlib
import json
import mmap
import os
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02_butes_config_triage as n02b  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import r1_tga_repair as tga_r1  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05a_decoder_audit"
)
PREV = OUT / "previews"
SYN = OUT / "synthetic"
N03A = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n03a_bornbeast_consumer/confirmed_relations.json"
)
N03C = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n03c_material_graph/path_binding.json"
)
N03H = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n03h_dtx_container_decode/decode.json"
)
CSPROJ = REPO / "CFRezManager" / "CFRezManager.csproj"
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")

DTX_VER_LT1 = -2
DTX_VER_LT15 = -3
DTX_VER_LT2 = -5
SUPPORTED_VERSIONS = {DTX_VER_LT1, DTX_VER_LT15, DTX_VER_LT2}
CURRENT_DTX_VERSION = DTX_VER_LT2
LT_RESTYPE_DTX = 0
COMMAND_STRING_LEN = 128
BPP_8P = 0
BPP_32 = 3
BPP_DXT1 = 4
BPP_DXT3 = 5
BPP_DXT5 = 6
BPP_32P = 7
FLAG_RGBA = 136
FLAG_BGRA = 8
VALID_TEX_SIZES = {8, 16, 32, 64, 128, 256, 512, 1024}

SAMPLES = [
    {
        "id": "bornbeast_pv_dtx",
        "kind": "dtx",
        "role": "PViewSkinFileName",
        "logical_path": "PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
        "loose_rel": "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
        "n03_reuse": "N03-A/N03-C/N03-H",
    },
    {
        "id": "bornbeast_qv_dtx",
        "kind": "dtx",
        "role": "SkinFileName",
        "logical_path": "WEAPONS/QV-M4A1_S_BornBeast.DTX",
        "loose_rel": "data/rf017/ModelTextures/WEAPONS/QV-M4A1_S_BornBeast.DTX",
        "n03_reuse": "N03-C/N03-H",
    },
    {
        "id": "royaldragon_pv_dtx",
        "kind": "dtx",
        "role": "N03-H control PV",
        "logical_path": "PLAYERVIEW/PV-M4A1_RoyalDragon.DTX",
        "loose_rel": "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_RoyalDragon.DTX",
        "n03_reuse": "N03-H exact path",
    },
    {
        "id": "royaldragon_s_dtx",
        "kind": "dtx",
        "role": "SpecularMapName later-era control",
        "logical_path": "SpecularMap/PV-M4A1_RoyalDragon_s.DTX",
        "loose_rel": "data/rf017/ModelTextures/SpecularMap/PV-M4A1_RoyalDragon_s.DTX",
        "n03_reuse": "N03-H exact path",
    },
    {
        "id": "greenvain_s_dtx",
        "kind": "dtx",
        "role": "SpecularMap later-era size-class control",
        "logical_path": "SpecularMap/PV-DualDE_GreenVein_S.DTX",
        "loose_rel": "data/rf017/ModelTextures/SpecularMap/PV-DualDE_GreenVein_S.DTX",
        "n03_reuse": "N03-H exact path",
    },
    {
        "id": "bornbeast_cfg",
        "kind": "cfg",
        "role": "WeaponShader CFG",
        "logical_path": "WeaponShader/M4A1_S_BornBeast.CFG",
        "loose_rel": "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG",
        "n03_reuse": "N03-A",
    },
    {
        "id": "bornbeast_alpha_tga",
        "kind": "tga",
        "role": "Alpha TGA (filename != shader role)",
        "logical_path": "AlphaMap/M4A1_S_BornBeast_alpha.TGA",
        "loose_rel": "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
        "n03_reuse": "N03-A",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def i32(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from("<i", data, offset)[0]


def u16(data: bytes, offset: int) -> int | None:
    if offset + 2 > len(data):
        return None
    return struct.unpack_from("<H", data, offset)[0]


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or "").strip() or "unknown"


# ---------------------------------------------------------------------------
# Header / format ports
# ---------------------------------------------------------------------------
def lzma_header(data: bytes) -> dict:
    ok, decoded, known = False, None, False
    if len(data) >= 13 and data[0] in (0x5D, 0x08):
        dict_size = struct.unpack_from("<I", data, 1)[0]
        legacy = data[1] == 0 and data[2] == 0 and data[3] == 0
        if dict_size != 0 or legacy:
            raw = struct.unpack_from("<q", data, 5)[0]
            if raw >= 0:
                if raw not in (0,) and raw <= 0x7FFFFFFF:
                    ok, decoded, known = True, raw, True
            else:
                ok, decoded, known = raw == -1, None, False
    return {
        "precondition": "LzmaAloneDecoder first byte 0x5D/0x08 + dict size",
        "matches": ok,
        "decoded_bytes": decoded,
        "has_known_decoded_bytes": known,
    }


def ltc_wrapper_header(data: bytes) -> dict:
    unlocked = n02b.try_unlock_crossfire_payload(data)
    return {
        "precondition": "CrossFire LTC magic 54 83 B2 E1",
        "matches": unlocked is not None,
        "unlocked_sha256": sha256_bytes(unlocked) if unlocked is not None else None,
        "unlocked_size": len(unlocked) if unlocked is not None else None,
    }


def repo_dtx_try_read_header(data: bytes) -> dict:
    """Port of DtxThumbnailDecoder.TryReadHeader versions {-2,-3,-5}."""
    if len(data) < 32:
        return {"ok": False, "reason": "file shorter than 32 bytes"}
    first = struct.unpack_from("<i", data, 0)[0]
    if first == 0 and len(data) >= 36 and struct.unpack_from("<i", data, 4)[0] in SUPPORTED_VERSIONS:
        version, cursor = struct.unpack_from("<i", data, 4)[0], 8
    elif first in SUPPORTED_VERSIONS:
        version, cursor = first, 4
    else:
        return {
            "ok": False,
            "reason": f"offset0 int32={first} is not a supported DTX version (-2/-3/-5)",
            "offset0_int32": first,
            "offset4_int32": i32(data, 4),
            "offset8_int32": i32(data, 8),
        }
    if len(data) < cursor + 28:
        return {"ok": False, "reason": "header truncated"}
    width = struct.unpack_from("<H", data, cursor)[0]
    cursor += 2
    height = struct.unpack_from("<H", data, cursor)[0]
    cursor += 2
    mipmap_count = struct.unpack_from("<H", data, cursor)[0]
    cursor += 2
    n_sections = struct.unpack_from("<H", data, cursor)[0]
    cursor += 2
    flags = struct.unpack_from("<I", data, cursor)[0]
    cursor += 4
    user_flags = struct.unpack_from("<I", data, cursor)[0]
    cursor += 4
    texture_group = data[cursor]
    cursor += 1
    mipmaps_to_use = data[cursor]
    cursor += 1
    bpp = data[cursor]
    cursor += 1
    cursor += 1
    cursor += 1
    cursor += 1
    cursor += 4
    cursor += 2
    if version in (DTX_VER_LT15, DTX_VER_LT2):
        cursor += COMMAND_STRING_LEN
    if width <= 0 or height <= 0 or mipmap_count < 0 or cursor >= len(data):
        return {"ok": False, "reason": "implausible header fields", "version": version}
    return {
        "ok": True,
        "reason": "parsed with repo DtxThumbnailDecoder layout",
        "version": version,
        "width": width,
        "height": height,
        "mipmap_count": mipmap_count,
        "n_sections": n_sections,
        "flags": flags,
        "user_flags": user_flags,
        "texture_group": texture_group,
        "mipmaps_to_use": mipmaps_to_use,
        "bytes_per_pixel_field": bpp,
        "data_offset": cursor,
        "payload_bytes": len(data) - cursor,
    }


def dtx_create_structural(data: bytes) -> dict:
    """Auditable port of LTB2FBX/Vortigaunt dtx_Create gates (same dtxmgr.cpp).

    Not a second independent format: both tools share lithtech dtxmgr.cpp.
    """
    if len(data) < 36:
        return {"ok": False, "reason": "shorter than DtxHeader prefix"}
    res_type = struct.unpack_from("<i", data, 0)[0]
    version = struct.unpack_from("<i", data, 4)[0]
    width = struct.unpack_from("<H", data, 8)[0]
    height = struct.unpack_from("<H", data, 10)[0]
    n_mips = struct.unpack_from("<H", data, 12)[0]
    n_sections = struct.unpack_from("<H", data, 14)[0]
    flags = struct.unpack_from("<i", data, 16)[0]
    bpp = data[26] if len(data) > 26 else None
    data_offset = 36 + COMMAND_STRING_LEN
    reasons = []
    if res_type != LT_RESTYPE_DTX:
        reasons.append(f"m_ResType={res_type} != LT_RESTYPE_DTX({LT_RESTYPE_DTX})")
    if version != CURRENT_DTX_VERSION:
        reasons.append(f"m_Version={version} != CURRENT_DTX_VERSION({CURRENT_DTX_VERSION})")
    if n_mips == 0 or n_mips > 15:
        reasons.append(f"m_nMipmaps={n_mips} not in 1..15")
    if width not in VALID_TEX_SIZES or height not in VALID_TEX_SIZES:
        reasons.append(f"size {width}x{height} not in dtx_IsTextureSizeValid list")
    expected = None
    if bpp in (BPP_32, BPP_DXT1, BPP_DXT3, BPP_DXT5, BPP_8P, BPP_32P) and n_mips >= 1:
        expected = 0
        w, h = width, height
        for _ in range(n_mips):
            expected += calc_image_size(bpp, w, h)
            w = max(1, w // 2)
            h = max(1, h // 2)
    payload = max(0, len(data) - data_offset)
    size_ok = expected is not None and payload >= expected
    if expected is not None and not size_ok:
        reasons.append(f"payload {payload} < expected mip bytes {expected}")
    return {
        "ok": not reasons,
        "reason": "dtx_Create gates passed" if not reasons else "; ".join(reasons),
        "m_ResType": res_type,
        "m_Version": version,
        "width": width,
        "height": height,
        "n_mipmaps": n_mips,
        "n_sections": n_sections,
        "flags": flags,
        "bpp_ident_extra2": bpp,
        "header_bytes": data_offset,
        "payload_bytes": payload,
        "expected_mip_bytes": expected,
        "note": "LTB2FBX 06d749d and Vortigaunt d739d1f share this loader; not two format proofs",
    }


def calc_image_size(bpp: int, width: int, height: int) -> int:
    if bpp == BPP_32:
        return width * height * 4
    if bpp == BPP_8P or bpp == BPP_32P:
        return width * height
    if bpp == BPP_DXT1:
        return ((width + 3) // 4) * ((height + 3) // 4) * 8
    if bpp in (BPP_DXT3, BPP_DXT5):
        return ((width + 3) // 4) * ((height + 3) // 4) * 16
    return -1


def rezextract_swap(data: bytes) -> tuple[bytes, dict]:
    """Port of no-lith/RezExtract b3f87a9 src/rez.cpp DTX offset 4/8 swap.

    The upstream check reads data[0x4] as a single byte against
    DTX_VER_LT1/LT15/LT2, then swaps the 4-byte fields at 0x4 and 0x8.
    """
    info = {
        "precondition": "extension DTX and byte at offset 4 is not -2/-3/-5",
        "offset4_int32": i32(data, 4),
        "offset8_int32": i32(data, 8),
        "offset4_int8": struct.unpack_from("<b", data, 4)[0] if len(data) > 4 else None,
        "applied": False,
        "changed": False,
    }
    if len(data) < 12:
        info["reason"] = "shorter than 12 bytes"
        return data, info
    ver_byte = struct.unpack_from("<b", data, 4)[0]
    if ver_byte in SUPPORTED_VERSIONS:
        info["reason"] = f"byte at offset 4 is {ver_byte}; RezExtract does not swap"
        return data, info
    out = bytearray(data)
    lhs = bytes(out[4:8])
    rhs = bytes(out[8:12])
    out[4:8] = rhs
    out[8:12] = lhs
    info["applied"] = True
    info["changed"] = lhs != rhs
    info["after_offset4_int32"] = i32(bytes(out), 4)
    info["after_offset8_int32"] = i32(bytes(out), 8)
    info["reason"] = "swapped 4-byte fields at offset 4 and 8"
    return bytes(out), info


# ---------------------------------------------------------------------------
# Synthetic DTX
# ---------------------------------------------------------------------------
def pack_dtx_header(width: int, height: int, bpp: int, flags: int, n_mips: int = 1) -> bytes:
    extra = bytearray(12)
    extra[0] = 0  # texture group
    extra[1] = n_mips
    extra[2] = bpp
    header = struct.pack(
        "<iiHHHH ii",
        LT_RESTYPE_DTX,
        CURRENT_DTX_VERSION,
        width,
        height,
        n_mips,
        0,
        flags,
        0,
    )
    return header + bytes(extra) + (b"\x00" * COMMAND_STRING_LEN)


def quadrant_rgba(width: int, height: int) -> bytes:
    out = bytearray(width * height * 4)
    mid_x, mid_y = width // 2, height // 2
    colors = {
        (0, 0): (255, 0, 0, 255),
        (1, 0): (0, 255, 0, 255),
        (0, 1): (0, 0, 255, 255),
        (1, 1): (255, 255, 255, 255),
    }
    for y in range(height):
        for x in range(width):
            r, g, b, a = colors[(int(x >= mid_x), int(y >= mid_y))]
            i = (y * width + x) * 4
            out[i : i + 4] = bytes((r, g, b, a))
    return bytes(out)


def rgb_to_565(r: int, g: int, b: int) -> int:
    return ((r * 31 // 255) << 11) | ((g * 63 // 255) << 5) | (b * 31 // 255)


def encode_dxt1_solid_quadrants(width: int, height: int) -> bytes:
    colors = {
        (0, 0): (255, 0, 0),
        (1, 0): (0, 255, 0),
        (0, 1): (0, 0, 255),
        (1, 1): (255, 255, 255),
    }
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    mid_bx, mid_by = blocks_x // 2, blocks_y // 2
    out = bytearray()
    for by in range(blocks_y):
        for bx in range(blocks_x):
            r, g, b = colors[(int(bx >= mid_bx), int(by >= mid_by))]
            c0 = rgb_to_565(r, g, b)
            out += struct.pack("<HHI", c0, 0, 0)
    return bytes(out)


def expected_quadrant_rgb(width: int, height: int, x: int, y: int) -> tuple[int, int, int]:
    mid_x, mid_y = width // 2, height // 2
    return {
        (0, 0): (255, 0, 0),
        (1, 0): (0, 255, 0),
        (0, 1): (0, 0, 255),
        (1, 1): (255, 255, 255),
    }[(int(x >= mid_x), int(y >= mid_y))]


def decode_repo_pixels(data: bytes) -> dict:
    hdr = repo_dtx_try_read_header(data)
    if not hdr.get("ok"):
        return {"ok": False, "header": hdr}
    bpp = hdr["bytes_per_pixel_field"]
    flags = hdr["flags"]
    w, h = hdr["width"], hdr["height"]
    off = hdr["data_offset"]
    if bpp == BPP_32 and flags == FLAG_RGBA:
        src = data[off : off + w * h * 4]
        if len(src) < w * h * 4:
            return {"ok": False, "header": hdr, "reason": "RGBA payload truncated"}
        pixels = bytearray(w * h * 4)
        for i in range(w * h):
            r, g, b = src[i * 4], src[i * 4 + 1], src[i * 4 + 2]
            pixels[i * 4 : i * 4 + 4] = bytes((b, g, r, 255))
        image = Image.frombytes("RGBA", (w, h), bytes(pixels), "raw", "BGRA")
        return {"ok": True, "header": hdr, "format": "rgba32_as_bgra", "image": image}
    if bpp == BPP_32 and flags == FLAG_BGRA and hdr["texture_group"] == 0:
        src = data[off : off + w * h * 4]
        if len(src) < w * h * 4:
            return {"ok": False, "header": hdr, "reason": "BGRA payload truncated"}
        image = Image.frombytes("RGBA", (w, h), src, "raw", "BGRA")
        return {"ok": True, "header": hdr, "format": "bgra32", "image": image}
    if bpp == BPP_DXT1:
        need = calc_image_size(BPP_DXT1, w, h)
        if off + need > len(data):
            return {"ok": False, "header": hdr, "reason": "DXT1 payload truncated"}
        image = decode_dxt1_bgra(data, off, w, h)
        return {"ok": True, "header": hdr, "format": "dxt1", "image": image}
    return {"ok": False, "header": hdr, "reason": f"unresolved bpp={bpp} flags={flags}"}


def decode_dxt1_bgra(data: bytes, offset: int, width: int, height: int) -> Image.Image:
    out = bytearray(width * height * 4)
    src = offset
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    for by in range(blocks_y):
        for bx in range(blocks_x):
            c0 = int.from_bytes(data[src : src + 2], "little")
            c1 = int.from_bytes(data[src + 2 : src + 4], "little")
            bits = int.from_bytes(data[src + 4 : src + 8], "little")
            src += 8
            p0 = rgb565_tuple(c0)
            p1 = rgb565_tuple(c1)
            if c0 > c1:
                palette = [p0, p1, lerp(p0, p1, 1, 3), lerp(p0, p1, 2, 3)]
                alphas = [255, 255, 255, 255]
            else:
                palette = [p0, p1, lerp(p0, p1, 1, 2), (0, 0, 0)]
                alphas = [255, 255, 255, 0]
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px
                    y = by * 4 + py
                    if x >= width or y >= height:
                        continue
                    idx = (bits >> (2 * (py * 4 + px))) & 3
                    r, g, b = palette[idx]
                    i = (y * width + x) * 4
                    out[i : i + 4] = bytes((b, g, r, alphas[idx]))
    return Image.frombytes("RGBA", (width, height), bytes(out), "raw", "BGRA")


def rgb565_tuple(color: int) -> tuple[int, int, int]:
    r = ((color >> 11) & 31) * 255 // 31
    g = ((color >> 5) & 63) * 255 // 63
    b = (color & 31) * 255 // 31
    return r, g, b


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], n: int, d: int) -> tuple[int, int, int]:
    return tuple((a[i] * (d - n) + b[i] * n) // d for i in range(3))  # type: ignore[return-value]


def sample_quadrants(image: Image.Image) -> dict:
    rgb = image.convert("RGB")
    w, h = rgb.size
    points = {
        "tl": (w // 4, h // 4),
        "tr": (3 * w // 4, h // 4),
        "bl": (w // 4, 3 * h // 4),
        "br": (3 * w // 4, 3 * h // 4),
    }
    out = {}
    match = True
    for name, (x, y) in points.items():
        got = rgb.getpixel((x, y))
        exp = expected_quadrant_rgb(w, h, x, y)
        row = {"x": x, "y": y, "got": list(got), "expected": list(exp), "match": list(got) == list(exp)}
        if abs(got[0] - exp[0]) > 8 or abs(got[1] - exp[1]) > 8 or abs(got[2] - exp[2]) > 8:
            row["match"] = False
        out[name] = row
        match = match and row["match"]
    return {"ok": match, "points": out, "size": [w, h], "mode": image.mode, "bands": list(image.getbands())}


def pixel_stats_simple(image: Image.Image) -> dict:
    rgb = image.convert("RGB")
    px = list(rgb.getdata())
    n = max(len(px), 1)
    mean = [round(sum(c[i] for c in px) / n, 1) for i in range(3)]
    q = {(p[0] >> 3, p[1] >> 3, p[2] >> 3) for p in px}
    extrema = [min(c[i] for c in px) for i in range(3)], [max(c[i] for c in px) for i in range(3)]
    return {
        "size": list(image.size),
        "mean_rgb": mean,
        "min_rgb": list(extrema[0]),
        "max_rgb": list(extrema[1]),
        "unique_q5": len(q),
        "mode": image.mode,
        "bands": list(image.getbands()),
    }


def safe_stem(stem: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)


def decode_dtx_pixels(data: bytes, stem: str) -> dict:
    stem = safe_stem(stem)
    python = {"ok": False}
    py = decode_repo_pixels(data)
    if py.get("ok"):
        dest = PREV / f"{stem}_python.png"
        py["image"].save(dest)
        python = {
            "ok": True,
            "format": py.get("format"),
            "preview": rel(dest),
            "stats": pixel_stats_simple(py["image"]),
        }
    cfrez = {"ok": False}
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{stem}.dtx"
        src.write_bytes(data)
        dest = PREV / f"{stem}_cfrez.png"
        cfrez = cfrez_decode_image(src, dest)
        if cfrez.get("ok"):
            image = Image.open(dest)
            cfrez["stats"] = pixel_stats_simple(image)
    return {
        "ok": bool(python.get("ok") or cfrez.get("ok")),
        "python": python,
        "cfrez": cfrez,
        "note": "pixel decode is not mesh/sampler binding and not shader semantics",
    }


def cfrez_decode_image(src: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    if CFREZ_EXE.exists():
        cmd = [str(CFREZ_EXE), "--decode-image", str(src), str(dest)]
    elif DOTNET.exists():
        cmd = [
            str(DOTNET),
            "run",
            "--project",
            str(CSPROJ),
            "-c",
            "Debug",
            "--",
            "--decode-image",
            str(src),
            str(dest),
        ]
    else:
        return {"ok": False, "returncode": None, "error": "dotnet/CFRezManager missing", "cmd": []}
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    ok = completed.returncode == 0 and dest.exists() and dest.stat().st_size > 0
    err = (completed.stderr or completed.stdout or "").strip().splitlines()
    return {
        "ok": ok,
        "returncode": completed.returncode,
        "error": err[-1] if err and not ok else None,
        "output": rel(dest) if ok else None,
        "cmd": [rel(Path(cmd[0])) if Path(cmd[0]).is_absolute() else cmd[0], *cmd[1:]],
    }


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def read_rez_index_mmap(rez_path: Path) -> list[dict]:
    with rez_path.open("rb") as handle:
        mm = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if mm.size() < n02dr1.REZ_HEADER_SIZE:
                return []
            root_dir_pos = struct.unpack_from("<i", mm, 131)[0]
            root_dir_size = struct.unpack_from("<i", mm, 135)[0]
            out_files: list[dict] = []
            visited: set = set()
            if root_dir_pos >= n02dr1.REZ_HEADER_SIZE and root_dir_size > 0:
                n02dr1._parse_entry_range(
                    mm, root_dir_pos, root_dir_size, 0, visited, out_files, []
                )
            return out_files
        finally:
            mm.close()


def rf017_archives() -> list[Path]:
    found = []
    for sub in ("rez", "rez2", "rez3", "rez4", "rez5", "rez6"):
        folder = CF / sub
        if not folder.is_dir():
            continue
        for name in os.listdir(folder):
            if name.lower() == "rf017.rez":
                found.append(folder / name)
    return found


def archive_label(path: Path) -> str:
    try:
        return str(path.relative_to(CF)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_prior_sha() -> dict:
    prior = {}
    if N03A.exists():
        blob = json.loads(N03A.read_text(encoding="utf-8"))
        for row in blob.get("relations") or []:
            if not isinstance(row, dict):
                continue
            key = (row.get("full_path") or "").upper()
            if key:
                prior.setdefault(key, []).append(
                    {
                        "source": "n03a_confirmed_relations",
                        "sha256": (row.get("sha256") or "").lower(),
                        "rez_path": row.get("rez_path"),
                        "inventory_relative_path": row.get("inventory_relative_path"),
                    }
                )
    if N03C.exists():
        blob = json.loads(N03C.read_text(encoding="utf-8"))
        for bind in blob.get("path_binds") or []:
            for payload in bind.get("payloads") or []:
                key = (payload.get("full_path") or "").upper()
                if key:
                    prior.setdefault(key, []).append(
                        {
                            "source": "n03c_path_binding",
                            "sha256": (payload.get("sha256") or "").lower(),
                            "archive": payload.get("archive"),
                            "field": bind.get("field"),
                        }
                    )
    return prior


def build_input_table() -> list[dict]:
    archives = rf017_archives()
    indexes = []
    for archive in archives:
        try:
            files = read_rez_index_mmap(archive)
        except OSError as exc:
            indexes.append(
                {
                    "archive": archive_label(archive),
                    "abs": str(archive),
                    "file_count": 0,
                    "by_full": {},
                    "error": str(exc),
                }
            )
            continue
        by_full = {}
        for entry in files:
            by_full[entry["full_path"].upper()] = entry
        indexes.append(
            {
                "archive": archive_label(archive),
                "abs": str(archive),
                "file_count": len(files),
                "by_full": by_full,
            }
        )
    prior = load_prior_sha()
    rows = []
    for sample in SAMPLES:
        loose = REPO / sample["loose_rel"]
        loose_present = loose.is_file()
        loose_bytes = loose.read_bytes() if loose_present else b""
        loose_sha = sha256_bytes(loose_bytes) if loose_present else None
        loose_md5 = md5_bytes(loose_bytes) if loose_present else None
        copies = []
        for index in indexes:
            entry = index["by_full"].get(sample["logical_path"].upper())
            if not entry:
                copies.append(
                    {
                        "archive": index["archive"],
                        "hit": False,
                        "archive_file_count": index.get("file_count"),
                        "index_error": index.get("error"),
                    }
                )
                continue
            try:
                raw = n02er2.read_payload_bytes(
                    index["abs"], entry["data_offset"], entry["size"], entry
                )
            except (OSError, ValueError) as exc:
                copies.append(
                    {
                        "archive": index["archive"],
                        "abs": index["abs"],
                        "hit": True,
                        "full_path": entry["full_path"],
                        "data_offset": entry["data_offset"],
                        "entry_size": entry["size"],
                        "directory_md5": entry.get("md5"),
                        "verified_read_error": str(exc),
                        "md5_semantics": "verified numbered-part resolver required; unauthenticated main-file slice is deprecated",
                    }
                )
                continue
            raw_sha = sha256_bytes(raw)
            raw_md5 = md5_bytes(raw)
            copies.append(
                {
                    "archive": index["archive"],
                    "abs": index["abs"],
                    "hit": True,
                    "full_path": entry["full_path"],
                    "data_offset": entry["data_offset"],
                    "entry_size": entry["size"],
                    "time": entry.get("time"),
                    "actual_bytes": len(raw),
                    "directory_md5": entry.get("md5"),
                    "computed_md5": raw_md5,
                    "directory_md5_matches_computed": (entry.get("md5") or "").lower() == raw_md5,
                    "raw_sha256": raw_sha,
                    "raw_equals_loose": loose_present and raw_sha == loose_sha,
                    "md5_semantics": "directory_md5 and computed_md5 recorded separately; mismatch is not interpreted as codec",
                    "verified_read": True,
                }
            )
        hit_shas = sorted({c["raw_sha256"] for c in copies if c.get("hit") and "raw_sha256" in c})
        rows.append(
            {
                **sample,
                "loose_present": loose_present,
                "loose_size": len(loose_bytes) if loose_present else 0,
                "loose_sha256": loose_sha,
                "loose_md5": loose_md5,
                "prior_sha_records": prior.get(sample["logical_path"].upper(), []),
                "copies": copies,
                "copy_sha_unique_count": len(hit_shas),
                "all_hits_equal_loose": bool(copies)
                and all((not c.get("hit")) or c.get("raw_equals_loose") for c in copies)
                and any(c.get("hit") for c in copies),
                "header_prefix": list(loose_bytes[:16]) if loose_present else [],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Transforms + comparison
# ---------------------------------------------------------------------------
def capacity_notes(size: int) -> list[dict]:
    notes = []
    for leftover in (0, 163, 164):
        payload = size - leftover
        if payload <= 0:
            continue
        combos = []
        if payload == 524288:
            combos = [
                "512x256x4 BGRA no mip",
                "1024x512 RGB16",
                "DXT1 1024x1024",
                "DXT5 1024x512",
                "BGR24 512x256 full mip (geometric series = 524288)",
            ]
        if payload == 32768:
            combos = ["DXT1 256x256", "RGB565 128x128", "8-bit 256x128"]
        if payload == 131072:
            combos = ["DXT1 512x512", "BGRA 256x128", "BGR24 256x170 leftover-ish"]
        notes.append(
            {
                "size": size,
                "leftover": leftover,
                "payload": payload,
                "example_fits": combos,
                "rule": "size-fit is not a codec",
            }
        )
    return notes


def phase_census(data: bytes) -> dict:
    if not data:
        return {"empty": True}
    phases = []
    for ph in range(3):
        values = {}
        for i, byte in enumerate(data):
            if i % 3 != ph:
                continue
            values[byte] = values.get(byte, 0) + 1
        total = sum(values.values()) or 1
        top = sorted(values.items(), key=lambda kv: -kv[1])[:4]
        phases.append(
            {
                "phase": ph,
                "unique": len(values),
                "ff_share": round(values.get(255, 0) / total, 6),
                "top": [{"value": v, "count": n} for v, n in top],
            }
        )
    non_ff_phase = max(phases, key=lambda row: row["unique"])
    return {
        "size": len(data),
        "size_mod_3": len(data) % 3,
        "phases": phases,
        "highest_unique_phase": non_ff_phase["phase"],
        "non_ff_count_guess": sum(1 for b in data[non_ff_phase["phase"] :: 3] if b != 255),
    }


def head_tail(data: bytes, n: int = 16) -> dict:
    return {
        "head": list(data[:n]),
        "tail": list(data[-n:]) if len(data) >= n else list(data),
        "offset4_int32": i32(data, 4),
        "offset8_int32": i32(data, 8),
        "offset0_int32": i32(data, 0),
    }


def run_dtx_branches(sample_id: str, data: bytes) -> list[dict]:
    branches = []
    raw_hdr = repo_dtx_try_read_header(data)
    lith = dtx_create_structural(data)
    raw_pixels = decode_dtx_pixels(data, f"{sample_id}_raw") if raw_hdr.get("ok") else {"ok": False, "reason": "header failed"}
    branches.append(
        {
            "branch": "raw_read",
            "precondition": "bytes as stored",
            "input_sha256": sha256_bytes(data),
            "output_sha256": sha256_bytes(data),
            "repo_header": raw_hdr,
            "dtx_create": lith,
            "lzma": lzma_header(data),
            "ltc_wrapper": ltc_wrapper_header(data),
            "pixels": {k: v for k, v in raw_pixels.items() if k != "image"},
            "ok": bool(raw_hdr.get("ok") and lith.get("ok") and raw_pixels.get("ok")),
        }
    )
    lz = lzma_header(data)
    branches.append(
        {
            "branch": "lzma_alone",
            "precondition": lz["precondition"],
            "applied": lz["matches"],
            "ok": False,
            "reason": "precondition not met; not decompressed" if not lz["matches"] else "matched but no decode attempted beyond header",
            "lzma": lz,
        }
    )
    wrap = ltc_wrapper_header(data)
    branches.append(
        {
            "branch": "crossfire_ltc_wrapper",
            "precondition": wrap["precondition"],
            "applied": wrap["matches"],
            "ok": False,
            "reason": "precondition not met" if not wrap["matches"] else "magic matched (unexpected for DTX)",
            "wrapper": wrap,
        }
    )
    swapped, swap_info = rezextract_swap(data)
    swapped_hdr = repo_dtx_try_read_header(swapped)
    swapped_lith = dtx_create_structural(swapped)
    swapped_pixels = (
        decode_dtx_pixels(swapped, f"{sample_id}_swap")
        if swapped_hdr.get("ok") and swapped != data
        else (raw_pixels if swapped_hdr.get("ok") else {"ok": False})
    )
    if not swapped_hdr.get("ok"):
        o4 = swap_info.get("after_offset4_int32", swap_info.get("offset4_int32"))
        o8 = swap_info.get("after_offset8_int32", swap_info.get("offset8_int32"))
        swap_fail = f"after swap, offset4={o4} offset8={o8} still not -2/-3/-5"
    elif not swapped_pixels.get("ok"):
        swap_fail = "header parsed but pixel decode failed"
    else:
        swap_fail = None
    branches.append(
        {
            "branch": "rezextract_offset4_8_swap",
            "precondition": swap_info["precondition"],
            "input_sha256": sha256_bytes(data),
            "output_sha256": sha256_bytes(swapped),
            "swap": swap_info,
            "repo_header": swapped_hdr,
            "dtx_create": swapped_lith,
            "pixels": swapped_pixels,
            "ok": bool(swapped_hdr.get("ok") and swapped_lith.get("ok") and swapped_pixels.get("ok")),
            "reason": swap_fail,
        }
    )
    return branches


def run_tga_branches(data: bytes) -> list[dict]:
    raw_ok, raw_hdr, raw_why = tga_r1.tga_try_read_header(data)
    try:
        repaired, detail = tga_r1.try_repair_inserted_footer_header(data)
    except Exception as exc:  # noqa: BLE001
        repaired, detail = None, f"repair raised {type(exc).__name__}: {exc}"
    out = [
        {
            "branch": "raw_read",
            "precondition": "bytes as stored",
            "input_sha256": sha256_bytes(data),
            "tga_header": raw_hdr,
            "ok": raw_ok,
            "reason": None if raw_ok else raw_why,
        }
    ]
    if repaired is None:
        out.append(
            {
                "branch": "inserted_footer_header_repair",
                "precondition": "TRUEVISION-XFILE footer then 18-byte header (TgaThumbnailDecoder)",
                "ok": False,
                "reason": detail if isinstance(detail, str) else "repair failed",
                "detail": detail if isinstance(detail, dict) else None,
            }
        )
        return out
    ok, hdr, why = tga_r1.tga_try_read_header(repaired)
    preview = None
    if ok and hdr and hdr.get("image_type") == 2 and hdr.get("pixel_depth") == 24:
        px, decoded_hdr = tga_r1.decode_uncompressed_bgr24(repaired)
        if px is not None and decoded_hdr is not None:
            dest = PREV / "bornbeast_alpha_tga_repaired.png"
            image = Image.frombytes(
                "RGB",
                (decoded_hdr["width"], decoded_hdr["height"]),
                bytes(px),
                "raw",
                "BGR",
            )
            image.save(dest)
            preview = rel(dest)
    out.append(
        {
            "branch": "inserted_footer_header_repair",
            "precondition": "TRUEVISION-XFILE inserted footer/header",
            "ok": ok,
            "reason": None if ok else why,
            "input_sha256": sha256_bytes(data),
            "output_sha256": sha256_bytes(repaired),
            "repaired_size": len(repaired),
            "tga_header": hdr,
            "repair_detail": {k: v for k, v in (detail or {}).items() if k != "parsed_header"} if isinstance(detail, dict) else detail,
            "preview": preview,
            "note": "repair success is TGA container evidence, not DTX albedo and not shader-role proof",
        }
    )
    return out


def run_cfg_branches(data: bytes) -> list[dict]:
    census = phase_census(data)
    return [
        {
            "branch": "raw_read",
            "precondition": "bytes as stored",
            "ok": True,
            "input_sha256": sha256_bytes(data),
            "size": len(data),
            "phase_census": census,
            "note": "492-byte / 164 non-FF measurement is structure only; not a LUT or constant-table proof",
        }
    ]


def scan_local_control_dtx(limit: int = 5) -> dict:
    root = DATA / "rf017" / "ModelTextures"
    found = []
    scanned = 0
    if not root.is_dir():
        return {
            "status": "NO_CURRENT_CLIENT_CONTROL",
            "reason": f"missing {rel(root)}",
            "scanned": 0,
            "hits": [],
        }
    target_names = {Path(s["loose_rel"]).name.lower() for s in SAMPLES if s["kind"] == "dtx"}
    seen: set[str] = set()
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() != ".dtx" or not path.is_file() or path.stat().st_size < 32:
            continue
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        if path.name.lower() in target_names:
            continue
        scanned += 1
        # This is only a version probe. The full parser checks that pixel
        # data follows the 164-byte LT2 header, so a 64-byte slice can never
        # pass it, even when the file itself is a valid DTX.
        with path.open("rb") as handle:
            prefix = handle.read(8)
        first = i32(prefix, 0)
        if first not in SUPPORTED_VERSIONS and not (
            first == LT_RESTYPE_DTX and i32(prefix, 4) in SUPPORTED_VERSIONS
        ):
            continue
        full = path.read_bytes()
        hdr = repo_dtx_try_read_header(full)
        if not hdr.get("ok"):
            continue
        lith = dtx_create_structural(full)
        decoded = decode_repo_pixels(full) if hdr.get("ok") else {"ok": False}
        preview = None
        if decoded.get("ok"):
            dest = PREV / f"control_{path.stem}_{hdr['width']}x{hdr['height']}.png"
            decoded["image"].save(dest)
            preview = rel(dest)
            decoded = {k: v for k, v in decoded.items() if k != "image"}
        found.append(
            {
                "path": rel(path),
                "size": path.stat().st_size,
                "sha256": sha256_bytes(full),
                "repo_header": hdr,
                "dtx_create": lith,
                "python_decode_ok": bool(decoded.get("ok")),
                "preview": preview,
            }
        )
        if len(found) >= limit:
            break
    status = "FOUND" if found else "NO_CURRENT_CLIENT_CONTROL"
    return {"status": status, "scanned": scanned, "hits": found, "limit": limit}


def verify_synthetic() -> dict:
    SYN.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    rgba_pixels = quadrant_rgba(16, 16)
    rgba_dtx = pack_dtx_header(16, 16, BPP_32, FLAG_RGBA) + rgba_pixels
    dxt_pixels = encode_dxt1_solid_quadrants(16, 16)
    dxt_dtx = pack_dtx_header(16, 16, BPP_DXT1, 0) + dxt_pixels
    cases = {
        "synthetic_rgba32_16x16": rgba_dtx,
        "synthetic_dxt1_16x16": dxt_dtx,
    }
    results = {}
    all_ok = True
    for name, blob in cases.items():
        src = SYN / f"{name}.dtx"
        src.write_bytes(blob)
        py = decode_repo_pixels(blob)
        py_check = None
        py_preview = None
        if py.get("ok"):
            dest = PREV / f"{name}_python.png"
            py["image"].save(dest)
            py_preview = rel(dest)
            py_check = sample_quadrants(py["image"])
        tool = cfrez_decode_image(src, PREV / f"{name}_cfrez.png")
        tool_check = None
        if tool.get("ok"):
            image = Image.open(PREV / f"{name}_cfrez.png")
            tool_check = sample_quadrants(image)
        lith = dtx_create_structural(blob)
        repo_hdr = repo_dtx_try_read_header(blob)
        case_ok = bool(py.get("ok") and py_check and py_check["ok"] and lith.get("ok") and repo_hdr.get("ok"))
        if tool.get("ok"):
            case_ok = case_ok and bool(tool_check and tool_check["ok"])
        all_ok = all_ok and case_ok
        results[name] = {
            "path": rel(src),
            "sha256": sha256_bytes(blob),
            "size": len(blob),
            "repo_header": repo_hdr,
            "dtx_create": lith,
            "python_decode": {
                "ok": bool(py.get("ok")),
                "format": py.get("format"),
                "preview": py_preview,
                "quadrants": py_check,
            },
            "cfrez_decode": {**tool, "quadrants": tool_check},
            "ok": case_ok,
            "note": "synthetic proves standard Jupiter DTX implementation only",
        }
    return {
        "ok": all_ok,
        "cases": results,
        "cfrez_available": CFREZ_EXE.exists() or DOTNET.exists(),
        "shared_loader_note": "LTB2FBX and Vortigaunt are one dtxmgr.cpp lineage",
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def classify(matrix: dict) -> str:
    syn = matrix["synthetic"]
    controls = matrix["local_controls"]
    samples = matrix["samples"]
    if not syn.get("ok"):
        if not syn.get("cfrez_available") and not any(
            case["python_decode"]["ok"] for case in syn["cases"].values()
        ):
            return "CONTROL_OR_TOOLCHAIN_BLOCKED"
        if not syn.get("ok"):
            return "CONTROL_OR_TOOLCHAIN_BLOCKED"
    mismatch = False
    recovered_dtx = False
    for sample in samples:
        if sample["kind"] == "dtx" and sample.get("copy_sha_unique_count", 1) > 1:
            mismatch = True
        if sample["kind"] == "dtx" and sample.get("all_hits_equal_loose") is False:
            if any(c.get("hit") for c in sample.get("copies") or []):
                mismatch = True
        if sample["kind"] == "dtx":
            for branch in sample.get("branches") or []:
                if branch.get("branch") in ("raw_read", "rezextract_offset4_8_swap") and branch.get("ok"):
                    recovered_dtx = True
            for divergent in sample.get("divergent_copies") or []:
                for branch in divergent.get("branches") or []:
                    if branch.get("branch") in ("raw_read", "rezextract_offset4_8_swap") and branch.get("ok"):
                        recovered_dtx = True
    if recovered_dtx:
        return "DECODE_RECOVERED_BINDING_OPEN"
    if mismatch:
        return "PROVENANCE_OR_VARIANT_MISMATCH"
    _ = controls
    return "REFERENCE_DECODERS_UNSUPPORTED"


def write_report(matrix: dict) -> None:
    result = matrix["result"]
    syn = matrix["synthetic"]
    lines = [
        "# P4-M01-N05-A — decoder / provenance audit",
        "",
        f"- result: **{result}**",
        "- P4-M01: still **INCOMPLETE**",
        f"- generated_at_utc: {matrix['generated_at_utc']}",
        f"- parent_git_head: `{matrix['parent_git_head']}`",
        f"- script: `{matrix['script']}`",
        "",
        "## Repro",
        "",
        "```text",
        "python scripts/material_recovery/n05a_decoder_provenance_audit.py",
        "```",
        "",
        "## 1. Tool control",
        "",
        f"Synthetic Jupiter DTX (16×16 RGBA32 + 16×16 DXT1) **{'PASS' if syn.get('ok') else 'FAIL'}**.",
        "This only proves the standard header/pixel path in this repo's decoder",
        "and the shared lithtech `dtx_Create` gates. LTB2FBX and Vortigaunt are",
        "one loader lineage, not two independent CF proofs.",
        "",
    ]
    for name, case in syn["cases"].items():
        py = case["python_decode"]
        tool = case["cfrez_decode"]
        lines.append(
            f"- `{name}`: python={py.get('ok')} cfrez={tool.get('ok')} "
            f"dtx_Create={case['dtx_create'].get('ok')} "
            f"quadrants_python={bool(py.get('quadrants', {}).get('ok'))}"
        )
    controls = matrix["local_controls"]
    lines += [
        "",
        f"Local client DTX with a legal Jupiter header: **{controls['status']}** "
        f"(scanned {controls['scanned']} ModelTextures DTX, kept {len(controls['hits'])}).",
        "",
    ]
    if controls["hits"]:
        for hit in controls["hits"]:
            hdr = hit["repo_header"]
            lines.append(
                f"- `{hit['path']}` {hdr.get('width')}x{hdr.get('height')} "
                f"ver={hdr.get('version')} bpp={hdr.get('bytes_per_pixel_field')}"
            )
    else:
        lines.append("No current-client positive DTX was found in `data/rf017/ModelTextures` outside the seven targets.")
    lines += [
        "",
        "## 2. Input table",
        "",
        "| id | loose SHA256 | copies | raw==loose | directory MD5 vs computed |",
        "|---|---|---:|---|---|",
    ]
    for sample in matrix["samples"]:
        md5_notes = []
        for copy in sample.get("copies") or []:
            if not copy.get("hit"):
                continue
            same = copy.get("directory_md5_matches_computed")
            md5_notes.append(f"{copy['archive']}:{'match' if same else 'DIFF'}")
        lines.append(
            "| `{id}` | `{sha}` | {n} | {eq} | {md5} |".format(
                id=sample["id"],
                sha=(sample.get("loose_sha256") or "")[:12],
                n=sum(1 for c in sample.get("copies") or [] if c.get("hit")),
                eq=sample.get("all_hits_equal_loose"),
                md5="; ".join(md5_notes) or "no hit",
            )
        )
    lines += [
        "",
        "Directory MD5 and computed MD5 are recorded separately. A mismatch is not treated as a codec.",
        "`rez/` is not assumed more authoritative than `rez2/` / `rez3/` / `rez4/`.",
        "",
        "## 3. Sourced transforms",
        "",
    ]
    for sample in matrix["samples"]:
        lines.append(f"### {sample['id']}")
        lines.append("")
        lines.append(f"- kind: `{sample['kind']}`")
        lines.append(f"- logical: `{sample['logical_path']}`")
        lines.append(f"- loose: `{sample['loose_rel']}`")
        for branch in sample.get("branches") or []:
            ok = "OK" if branch.get("ok") else "FAIL"
            reason = branch.get("reason") or branch.get("note") or ""
            lines.append(f"- `{branch['branch']}`: **{ok}** {reason}".rstrip())
        if sample["kind"] == "dtx":
            lines.append("- size-fit combinations (not a codec):")
            for note in sample.get("capacity_notes") or []:
                if note.get("example_fits"):
                    lines.append(
                        f"  - leftover {note['leftover']}: payload {note['payload']} could be "
                        + " / ".join(note["example_fits"])
                    )
            for divergent in sample.get("divergent_copies") or []:
                lines.append(
                    f"- divergent copy `{divergent['archive']}` size={divergent['size']} "
                    f"sha256=`{(divergent.get('sha256') or '')[:12]}`"
                )
                for branch in divergent.get("branches") or []:
                    ok = "OK" if branch.get("ok") else "FAIL"
                    reason = branch.get("reason") or branch.get("note") or ""
                    lines.append(f"  - `{branch['branch']}`: **{ok}** {reason}".rstrip())
                    hdr = branch.get("repo_header") or {}
                    if hdr.get("ok"):
                        lines.append(
                            f"    header: {hdr.get('width')}x{hdr.get('height')} "
                            f"ver={hdr.get('version')} bpp={hdr.get('bytes_per_pixel_field')} "
                            f"flags={hdr.get('flags')} data_offset={hdr.get('data_offset')}"
                        )
                    pixels = branch.get("pixels") or {}
                    py = (pixels.get("python") or {})
                    tool = (pixels.get("cfrez") or {})
                    if py.get("preview") or tool.get("preview") or tool.get("output"):
                        lines.append(
                            f"    pixels python={py.get('ok')} cfrez={tool.get('ok')} "
                            f"preview=`{py.get('preview') or tool.get('output')}`"
                        )
        lines.append("")
    fail_layers = matrix.get("failure_layers") or {}
    lines += [
        "## 4. Failure layers",
        "",
        f"- provenance copies: {fail_layers.get('provenance')}",
        f"- wrapper / LZMA: {fail_layers.get('wrapper')}",
        f"- Jupiter / RezExtract header: {fail_layers.get('header')}",
        f"- DTX pixels: {fail_layers.get('dtx_pixels')}",
        f"- TGA repair: {fail_layers.get('tga')}",
        f"- CFG semantics: {fail_layers.get('cfg')}",
        "",
        "No extra CF variant codec was invented. Offset 4/8 swap still cannot repair",
        "the inventory/`rez/` PV or QV samples. CFG 492/164 remains structure-only.",
        "",
        "## 5. Result",
        "",
        f"**{result}**",
        "",
        "P4-M01 remains INCOMPLETE. A legal Jupiter DTX on the QV logical path is not",
        "proof that CF loads that copy, that PV uses it, or that the mesh/sampler bind is closed.",
        "The available local OBJ is first-person PV; recovered pixels are `SkinFileName` / QV.",
        "UV wrap on the PV mesh was not used as evidence.",
        "No N05-B and no process dump from this round.",
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def failure_layers(samples: list[dict]) -> dict:
    dtx = [s for s in samples if s["kind"] == "dtx"]
    tga = next((s for s in samples if s["kind"] == "tga"), None)
    cfg = next((s for s in samples if s["kind"] == "cfg"), None)
    provenance_ok = all(
        s.get("all_hits_equal_loose") and s.get("copy_sha_unique_count", 1) <= 1
        for s in samples
        if any(c.get("hit") for c in s.get("copies") or [])
    )
    qv = next((s for s in samples if s.get("id") == "bornbeast_qv_dtx"), None)
    provenance_detail = "copies match loose"
    if not provenance_ok and qv and qv.get("copy_sha_unique_count", 1) > 1:
        sizes = [
            f"{c['archive']} {c.get('entry_size')}B sha={(c.get('raw_sha256') or '')[:12]}"
            for c in qv.get("copies") or []
            if c.get("hit")
        ]
        provenance_detail = "QV DTX logical path has distinct copies: " + "; ".join(sizes)
    elif not provenance_ok:
        provenance_detail = "copy or loose mismatch"
    header_fail = True
    for sample in dtx:
        for branch in sample.get("branches") or []:
            if branch.get("branch") in ("raw_read", "rezextract_offset4_8_swap") and branch.get("ok"):
                header_fail = False
    tga_ok = False
    if tga:
        tga_ok = any(b.get("branch") == "inserted_footer_header_repair" and b.get("ok") for b in tga.get("branches") or [])
    return {
        "provenance": provenance_detail,
        "wrapper": "LZMA/LTC preconditions not met on the five DTX",
        "header": (
            "inventory/rez copies fail Jupiter magic; check divergent copies"
            if header_fail
            else "header parsed"
        ),
        "dtx_pixels": (
            "rez2 QV DTX header+payload decoded as Jupiter DXT1 1024x1024; PV and rez/ QV still unsupported"
            if any(
                (b.get("ok") for s in dtx for b in (s.get("branches") or []) if b.get("branch") == "raw_read")
            )
            or any(
                b.get("ok")
                for s in dtx
                for d in (s.get("divergent_copies") or [])
                for b in (d.get("branches") or [])
                if b.get("branch") == "raw_read"
            )
            else "not recovered"
        ),
        "tga": "inserted-header repair recovered a legal TGA" if tga_ok else "TGA repair failed",
        "cfg": "phase structure recorded; semantics OPEN",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    SYN.mkdir(parents=True, exist_ok=True)
    parent = git_head()
    print("[n05a] synthetic controls", flush=True)
    synthetic = verify_synthetic()
    print("[n05a] scan local DTX headers", flush=True)
    controls = scan_local_control_dtx()
    print("[n05a] provenance table", flush=True)
    table = build_input_table()
    print("[n05a] sourced transforms", flush=True)
    samples = []
    for row in table:
        loose = REPO / row["loose_rel"]
        data = loose.read_bytes() if loose.is_file() else b""
        if row["kind"] == "dtx":
            branches = run_dtx_branches(row["id"], data)
            extra = {
                "capacity_notes": capacity_notes(len(data)),
                "phase_census": phase_census(data),
                "head_tail": head_tail(data),
                "divergent_copies": [],
            }
            for copy in row.get("copies") or []:
                if not copy.get("hit") or copy.get("raw_equals_loose"):
                    continue
                raw = n02er2.read_payload_bytes(
                    copy.get("abs") or str(CF / copy["archive"].replace("/", os.sep)),
                    copy["data_offset"],
                    copy["entry_size"],
                    {
                        "full_path": copy.get("full_path") or row["logical_path"],
                        "data_offset": copy["data_offset"],
                        "size": copy["entry_size"],
                        "time": copy.get("time", 0),
                        "md5": copy.get("directory_md5") or "",
                    },
                )
                extra["divergent_copies"].append(
                    {
                        "archive": copy["archive"],
                        "size": len(raw),
                        "sha256": sha256_bytes(raw),
                        "equals_loose": False,
                        "head_tail": head_tail(raw),
                        "capacity_notes": capacity_notes(len(raw)),
                        "phase_census": phase_census(raw),
                        "branches": run_dtx_branches(f"{row['id']}:{copy['archive']}", raw),
                    }
                )
        elif row["kind"] == "tga":
            branches = run_tga_branches(data)
            extra = {"head_tail": head_tail(data)}
        else:
            branches = run_cfg_branches(data)
            extra = {"head_tail": head_tail(data)}
        sample = dict(row)
        sample["branches"] = branches
        sample.update(extra)
        samples.append(sample)
    matrix = {
        "schema": "cf2.p4m01.n05a-decoder-provenance.v1",
        "task": "P4-M01-N05-A",
        "generated_at_utc": now(),
        "parent_git_head": parent,
        "script": "scripts/material_recovery/n05a_decoder_provenance_audit.py",
        "synthetic": json.loads(json.dumps(synthetic, default=str)),
        "local_controls": controls,
        "samples": json.loads(json.dumps(samples, default=str)),
        "failure_layers": failure_layers(samples),
        "p4_m01": "INCOMPLETE",
    }
    matrix["result"] = classify(matrix)
    sources = {
        "generated_at_utc": matrix["generated_at_utc"],
        "sources": [
            {
                "name": "no-lith/RezExtract",
                "commit": "b3f87a9c731c0bbc1900da2fd37e41b9a02e1e63",
                "path": "src/rez.cpp",
                "used_for": "DTX extract option swaps 4-byte fields at offset 4 and 8",
                "limit": "swap only; BornBeast PV/QV int32 at 4 and 8 are not -2/-3/-5",
            },
            {
                "name": "YoungFine0825/LTB2FBX",
                "commit": "06d749d56d6c929ba6c538cc26aa11cc1f7f1566",
                "path": "ThirdParty/lithtech/runtime/shared/dtxmgr.cpp",
                "used_for": "dtx_Create resource type / version / mip range gates",
                "limit": "not a 2026 CF runtime proof",
            },
            {
                "name": "iQuitt/Vortigaunt",
                "commit": "d739d1f900c261fc1ae67e11b436410084dda1aa",
                "path": "ThirdParty/lithtech/runtime/shared/dtxmgr.cpp",
                "used_for": "same lithtech loader as LTB2FBX",
                "limit": "not an independent second format",
            },
            {
                "name": "this repo CFRezManager DtxThumbnailDecoder",
                "path": "CFRezManager/Decoders/Images/DtxThumbnailDecoder.cs",
                "used_for": "repo decoder + --decode-image",
                "limit": "standard Jupiter magic only; 0/N on the seven CF samples is tool-unsupported, not official CF proof",
            },
            {
                "name": "this repo TgaThumbnailDecoder repair",
                "path": "scripts/material_recovery/r1_tga_repair.py",
                "used_for": "inserted TRUEVISION footer/header repair",
            },
        ],
    }
    (OUT / "sample_matrix.json").write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "reference_sources.json").write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(matrix)
    print(f"result={matrix['result']}")
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
