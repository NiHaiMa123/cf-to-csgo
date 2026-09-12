"""Minimal REZ writer for numbered-part resolver tests."""
from __future__ import annotations

import hashlib
import struct
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "material_recovery"))
import rez_keys  # noqa: E402

HEADER_SIZE = 168


def rez_encode(buf: bytes, pos: int) -> bytes:
    out = bytearray(len(buf))
    for i, value in enumerate(buf):
        encoded = (value - 73) & 0xFF
        encoded = (~(rez_keys.REZ_KEYS[(pos + i) % len(rez_keys.REZ_KEYS)] ^ encoded)) & 0xFF
        out[i] = encoded
    return bytes(out)


def _pack_name(name: str) -> bytes:
    encoded = name.encode("ascii")
    return struct.pack("<I", len(encoded)) + encoded


def file_entry(stem: str, extension: str, offset: int, size: int, time: int, md5: str, file_id: int = 1) -> bytes:
    ext = extension.encode("ascii")[:4][::-1].ljust(4, b"\0")
    return (
        struct.pack("<i", 0)
        + struct.pack("<iiii", offset, size, time, file_id)
        + ext
        + struct.pack("<i", 0)
        + _pack_name(stem)
        + b"\0\0"
        + md5.encode("ascii").ljust(32, b"\0")[:32]
    )


def dir_entry(name: str, table_offset: int, table_size: int) -> bytes:
    return struct.pack("<i", 1) + struct.pack("<iii", table_offset, table_size, 0) + _pack_name(name) + b"\0"


def header(root_pos: int, root_size: int) -> bytes:
    blob = bytearray(HEADER_SIZE)
    blob[0] = 0x0D
    blob[1] = 0x0A
    blob[62] = 0x0D
    blob[63] = 0x0A
    blob[124] = 0x0D
    blob[125] = 0x0A
    blob[126] = 0x1A
    struct.pack_into("<i", blob, 127, 1)
    struct.pack_into("<i", blob, 131, root_pos)
    struct.pack_into("<i", blob, 135, root_size)
    return bytes(blob)


def write_rez(index_path: Path, files: list[dict]) -> Path:
    """Write an index REZ and any numbered-part payload files.

    File dict keys: full_path, data, time, offset, optional md5,
    optional in_index (default True), optional write_part (default not in_index).
    """
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in files:
        logical = str(item["full_path"]).replace("\\", "/").strip("/")
        parent, name = ("", logical) if "/" not in logical else logical.rsplit("/", 1)
        grouped[parent].append({**item, "logical": logical, "name": name})

    directories = [name for name in grouped if name]
    dir_plain = {
        directory: b"".join(_encode_file(item) for item in grouped[directory])
        for directory in directories
    }
    root_files_plain = b"".join(_encode_file(item) for item in grouped.get("", []))

    root_pos = HEADER_SIZE
    cursor = root_pos
    # Root table size depends on directory entries, whose offsets are assigned next.
    dir_offsets: dict[str, int] = {}
    placeholder_root = b"".join(dir_entry(name, 0, len(dir_plain[name])) for name in directories) + root_files_plain
    cursor += len(placeholder_root)
    for name in directories:
        dir_offsets[name] = cursor
        cursor += len(dir_plain[name])

    root_plain = b"".join(
        dir_entry(name, dir_offsets[name], len(dir_plain[name])) for name in directories
    ) + root_files_plain

    in_index_end = cursor
    for item in files:
        if item.get("in_index", True):
            in_index_end = max(in_index_end, item["offset"] + len(item["data"]))

    blob = bytearray(in_index_end)
    blob[:HEADER_SIZE] = header(root_pos, len(root_plain))
    encoded_root = rez_encode(root_plain, root_pos)
    blob[root_pos:root_pos + len(encoded_root)] = encoded_root
    for name in directories:
        encoded = rez_encode(dir_plain[name], dir_offsets[name])
        start = dir_offsets[name]
        blob[start:start + len(encoded)] = encoded
    for item in files:
        if item.get("in_index", True):
            start = item["offset"]
            blob[start:start + len(item["data"])] = item["data"]
    index_path.write_bytes(bytes(blob))

    parts: dict[int, bytearray] = {}
    for item in files:
        write_part = item.get("write_part", not item.get("in_index", True))
        if not write_part:
            continue
        part = int(item["time"])
        end = item["offset"] + len(item["data"])
        buf = parts.setdefault(part, bytearray())
        if len(buf) < end:
            buf.extend(b"\0" * (end - len(buf)))
        buf[item["offset"]:end] = item["data"]
    for part, buf in parts.items():
        index_path.with_name(f"{index_path.stem}_{part}{index_path.suffix}").write_bytes(bytes(buf))
    return index_path


def _encode_file(item: dict) -> bytes:
    stem, ext = item["name"].rsplit(".", 1)
    md5 = item.get("md5") or hashlib.md5(item["data"]).hexdigest()
    return file_entry(stem, ext, item["offset"], len(item["data"]), item["time"], md5)
