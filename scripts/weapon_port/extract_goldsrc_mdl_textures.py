"""Extract embedded 8-bit palette textures from a GoldSrc studio MDL (v10)."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image


HEADER_MIN = 204
TEXTURE_STRUCT_SIZE = 80


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(raw: bytes, index: int) -> str:
    name = raw.split(b"\0", 1)[0].decode("latin-1", errors="replace").strip()
    if not name:
        name = f"texture_{index:02d}"
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in name)


def extract(mdl: Path, output_dir: Path, report_path: Path) -> dict:
    data = mdl.read_bytes()
    if len(data) < HEADER_MIN or data[:4] != b"IDST":
        raise ValueError("not a GoldSrc studio MDL")

    version = struct.unpack_from("<i", data, 4)[0]
    declared_length = struct.unpack_from("<i", data, 72)[0]
    texture_count, texture_offset = struct.unpack_from("<ii", data, 180)
    if version != 10:
        raise ValueError(f"unsupported GoldSrc MDL version: {version}")
    if declared_length != len(data):
        raise ValueError(f"declared length {declared_length} != file length {len(data)}")
    if not 0 < texture_count <= 256:
        raise ValueError(f"invalid embedded texture count: {texture_count}")
    if texture_offset < HEADER_MIN or texture_offset + texture_count * TEXTURE_STRUCT_SIZE > len(data):
        raise ValueError("texture table is outside the MDL")

    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index in range(texture_count):
        entry = texture_offset + index * TEXTURE_STRUCT_SIZE
        name = safe_name(data[entry : entry + 64], index)
        flags, width, height, pixels_offset = struct.unpack_from("<iiii", data, entry + 64)
        if width <= 0 or height <= 0 or width * height > 64 * 1024 * 1024:
            raise ValueError(f"{name}: invalid dimensions {width}x{height}")

        pixel_bytes = width * height
        palette_offset = pixels_offset + pixel_bytes
        palette_bytes = 256 * 3
        if pixels_offset < 0 or palette_offset + palette_bytes > len(data):
            raise ValueError(f"{name}: indexed pixels/palette are outside the MDL")

        indexed = data[pixels_offset : pixels_offset + pixel_bytes]
        palette = data[palette_offset : palette_offset + palette_bytes]
        image = Image.frombytes("P", (width, height), indexed)
        image.putpalette(palette)
        image = image.convert("RGBA")
        output = output_dir / f"{index:02d}_{name}.png"
        image.save(output)
        records.append(
            {
                "index": index,
                "name": name,
                "flags": flags,
                "size": [width, height],
                "pixels_offset": pixels_offset,
                "output": output.as_posix(),
                "sha256": sha256(output),
            }
        )

    report = {
        "schema": "cf2.goldsrc-mdl-texture-extract.v1",
        "source": mdl.as_posix(),
        "source_sha256": sha256(mdl),
        "version": version,
        "declared_length": declared_length,
        "texture_count": texture_count,
        "textures": records,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mdl", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = extract(args.mdl.resolve(), args.output_dir.resolve(), args.report.resolve())
    print(json.dumps({"texture_count": report["texture_count"], "report": str(args.report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
