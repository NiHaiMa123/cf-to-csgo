"""Read a REZ entry from a hash-verified main-file or numbered-part candidate.

Current RF017 samples repurpose the legacy `time` field as a part number.
Never infer that routing solely from the field name: require the directory
MD5 to match the exact candidate bytes. Inputs are only opened for reading.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

NUMBERED_PART_NAME = re.compile(
    r"^(?P<stem>.+)_(?P<part>[0-9]+)(?P<suffix>\.[^.]+)$",
    re.IGNORECASE,
)
MD5_HEX = re.compile(r"[0-9a-f]{32}")


def is_complete_directory_md5(value: object) -> bool:
    return bool(MD5_HEX.fullmatch(str(value or "").lower()))


def is_numbered_part_file(path: Path) -> bool:
    """True when `stem_N.ext` sits beside an index file `stem.ext`."""
    path = Path(path)
    match = NUMBERED_PART_NAME.fullmatch(path.name)
    if not match or not path.parent.is_dir():
        return False
    sibling_name = f"{match['stem']}{match['suffix']}"
    siblings = [
        item
        for item in path.parent.iterdir()
        if item.is_file() and item.name.casefold() == sibling_name.casefold()
    ]
    return len(siblings) == 1


def numbered_part_filename(index_path: Path, part: int) -> str:
    index_path = Path(index_path)
    return f"{index_path.stem}_{part}{index_path.suffix}"


def list_candidate_paths(index_path: Path, part: int) -> list[Path]:
    index_path = Path(index_path)
    candidates = [index_path]
    if part <= 0:
        return candidates
    name = numbered_part_filename(index_path, part)
    siblings = [
        item
        for item in index_path.parent.iterdir()
        if item.is_file() and item.name.casefold() == name.casefold()
    ]
    if len(siblings) > 1:
        raise ValueError("Ambiguous numbered-part filename")
    candidates.extend(siblings)
    return candidates


def read_verified_payload(index_path: Path, entry: dict, max_bytes: int = 64 * 1024 * 1024):
    index_path = Path(index_path)
    offset, size = int(entry["data_offset"]), int(entry["size"])
    part = int(entry["time"])
    expected = str(entry.get("md5", "")).lower()
    if not is_complete_directory_md5(expected):
        raise ValueError("A complete directory MD5 is required")
    if offset < 0 or not 0 <= size <= max_bytes:
        raise ValueError("Invalid or oversized payload range")
    candidates = list_candidate_paths(index_path, part)
    attempts, matches = [], []
    for path in candidates:
        length = path.stat().st_size
        row = {"path": str(path), "length": length, "range_ok": offset + size <= length}
        if row["range_ok"]:
            with path.open("rb") as handle:
                handle.seek(offset)
                data = handle.read(size)
            actual = hashlib.md5(data).hexdigest()
            row.update(actual_bytes=len(data), md5=actual, md5_match=len(data) == size and actual == expected)
            if row["md5_match"]:
                matches.append((path, data))
        attempts.append(row)
    if len(matches) != 1:
        raise ValueError(f"Expected one MD5-verified payload candidate, found {len(matches)}: {attempts}")
    source, data = matches[0]
    return data, {
        "logical_path": entry["full_path"], "index_archive": str(index_path),
        "payload_file": str(source), "legacy_time_field": part,
        "offset": offset, "size": size, "directory_md5": expected,
        "sha256": hashlib.sha256(data).hexdigest(), "candidate_checks": attempts,
        "routing": "numbered_part" if source != index_path else "main_file",
    }
