# -*- coding: utf-8 -*-
"""Decode the headerless BornBeast texture payloads with explicit assumptions.

The extracted CF files are not standard DTX/TGA containers:

* the PV ``.DTX`` is an interleaved BGR24 512x256 base level followed by a
  complete BGR24 mip chain and 163 trailing bytes;
* the auxiliary ``.TGA`` files have their TRUEVISION footer and 18-byte TGA
  header inserted into the middle of an otherwise standard 1024x1024 BGR24
  pixel stream;
* the shader ``.CFG`` is retained as opaque binary evidence.

This decoder deliberately accepts only those exact layouts.  It must fail rather
than silently reinterpret a different texture as one of these formats.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "data" / "rf017" / "ModelTextures"
OUTPUT_ROOT = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials" / "decoded"
REPORT_PATH = OUTPUT_ROOT.parent / "material_decode_report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_bgr24_base_with_mips(path: Path, output: Path) -> dict[str, object]:
    width, height = 512, 256
    levels: list[dict[str, int]] = []
    cursor = 0
    level_width, level_height = width, height
    while True:
        byte_count = level_width * level_height * 3
        levels.append({"width": level_width, "height": level_height, "offset": cursor, "bytes": byte_count})
        cursor += byte_count
        if level_width == 1 and level_height == 1:
            break
        level_width = max(1, level_width // 2)
        level_height = max(1, level_height // 2)

    data = path.read_bytes()
    trailing = len(data) - cursor
    if trailing != 163:
        raise ValueError(f"unexpected PV DTX mip-chain/trailer layout: {len(data)} bytes, trailer {trailing}")
    base_bytes = levels[0]["bytes"]
    image = Image.frombytes("RGB", (width, height), data[:base_bytes], "raw", "BGR")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return {
        "source": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "source_sha256": sha256(path),
        "layout": "headerless_bgr24_512x256_complete_mip_chain_plus_163_trailing_bytes",
        "mip_levels": levels,
        "payload_bytes": cursor,
        "trailing_bytes": trailing,
        "output": str(output.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "output_sha256": sha256(output),
        "mode": image.mode,
        "size": list(image.size),
        "channel_extrema": [list(pair) for pair in image.getextrema()],
    }


def decode_inserted_footer_tga(path: Path, output: Path) -> dict[str, object]:
    signature = b"TRUEVISION-XFILE"
    data = path.read_bytes()
    signature_offset = data.find(signature)
    if signature_offset < 8 or data[signature_offset + len(signature):signature_offset + len(signature) + 2] != b".\0":
        raise ValueError(f"missing inserted TRUEVISION footer in {path.name}")
    footer_offset = signature_offset - 8
    header_offset = footer_offset + 26
    header = data[header_offset:header_offset + 18]
    if len(header) != 18 or header[2] != 2 or header[16] != 24:
        raise ValueError(f"unexpected inserted TGA header in {path.name}")
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")
    descriptor = header[17]
    pixel_data = data[:footer_offset] + data[header_offset + 18:]
    payload_size = width * height * 3
    if len(pixel_data) != payload_size:
        raise ValueError(f"repaired pixel payload is {len(pixel_data)} bytes, expected {payload_size}")
    image = Image.frombytes("RGB", (width, height), pixel_data, "raw", "BGR")
    if descriptor & 0x20 == 0:
        image = ImageOps.flip(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return {
        "source": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "source_sha256": sha256(path),
        "layout": "bgr24_pixels_split_around_inserted_truevision_footer_and_header",
        "payload_bytes": payload_size,
        "footer_offset": footer_offset,
        "header_offset": header_offset,
        "descriptor": descriptor,
        "output": str(output.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "output_sha256": sha256(output),
        "mode": image.mode,
        "size": list(image.size),
        "channel_extrema": [list(pair) for pair in image.getextrema()],
    }


def main() -> int:
    diffuse = SOURCE_ROOT / "PLAYERVIEW" / "PV-M4A1_S_BornBeast.DTX"
    auxiliaries = {
        "alpha": SOURCE_ROOT / "AlphaMap" / "M4A1_S_BornBeast_alpha.TGA",
        "normal": SOURCE_ROOT / "NormalMap" / "M4A1_S_BornBeast_N.TGA",
        "specular": SOURCE_ROOT / "SpecularMap" / "M4A1_S_BornBeast_S.TGA",
    }
    shader = SOURCE_ROOT / "Shader" / "WeaponShader" / "M4A1_S_BornBeast.CFG"
    for path in (diffuse, *auxiliaries.values(), shader):
        if not path.is_file():
            raise FileNotFoundError(path)

    decoded: dict[str, object] = {
        "diffuse": decode_bgr24_base_with_mips(
            diffuse, OUTPUT_ROOT / "bornbeast_diffuse_bgr.png"
        )
    }
    for role, path in auxiliaries.items():
        decoded[role] = decode_inserted_footer_tga(path, OUTPUT_ROOT / f"bornbeast_{role}_bgr.png")

    scalar_roles = {"alpha": "G", "normal": "B", "specular": "R"}
    derived_channels: dict[str, object] = {}
    for role, channel_name in scalar_roles.items():
        image = Image.open(OUTPUT_ROOT / f"bornbeast_{role}_bgr.png").convert("RGB")
        channel_index = "RGB".index(channel_name)
        scalar = image.split()[channel_index]
        scalar_path = OUTPUT_ROOT / f"bornbeast_{role}_{channel_name.lower()}_scalar.png"
        scalar.save(scalar_path)
        derived_channels[role] = {
            "source_channel": channel_name,
            "output": str(scalar_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "output_sha256": sha256(scalar_path),
        }

    minimum_mask = Image.open(OUTPUT_ROOT / "bornbeast_alpha_g_scalar.png").convert("L")
    visibility_lut = [round(((value / 255.0) ** 0.55) * 255.0) for value in range(256)]
    visibility_mask = minimum_mask.point(visibility_lut)
    debug_image = Image.merge("RGB", (visibility_mask, visibility_mask, visibility_mask))
    debug_path = OUTPUT_ROOT / "bornbeast_alpha_min_debug.png"
    debug_image.save(debug_path)

    cfg_data = shader.read_bytes()
    report = {
        "schema": "cf2.bornbeast.material-decode.v1",
        "status": "decoded_with_explicit_container_assumptions",
        "decoded": decoded,
        "derived_scalar_channels": derived_channels,
        "derived_debug": {
            "output": str(debug_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "output_sha256": sha256(debug_path),
            "derivation": "per-pixel minimum of decoded AlphaMap RGB, gamma 0.55 shadow lift; UV/surface visibility debug only",
            "final_material": False,
        },
        "shader_cfg": {
            "source": str(shader.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "source_sha256": sha256(shader),
            "bytes": len(cfg_data),
            "interpretation": "opaque_binary_not_text_not_yet_mapped_to_source1",
        },
        "excluded_candidates": [
            "data/out/PV_M4A1_S_BornBeast_Raw.png (incorrect raw reinterpretation)",
            "data/out/PV_M4A1_S_BornBeast_UltraHD_4K.png (legacy provenance)",
            "data/out/PV_M4A1_S_BornBeast_Normal_4K.png (legacy provenance)",
        ],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[PASS] decoded material set -> {OUTPUT_ROOT}")
    print(f"[PASS] report -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
