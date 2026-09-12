"""Read a REZ entry from a hash-verified main-file or numbered-part candidate.

Current RF017 samples repurpose the legacy `time` field as a part number.
Never infer that routing solely from the field name: require the directory
MD5 to match the exact candidate bytes. Inputs are only opened for reading.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


def read_verified_payload(index_path: Path, entry: dict, max_bytes: int = 64 * 1024 * 1024):
    index_path = Path(index_path)
    offset, size = int(entry["data_offset"]), int(entry["size"])
    part = int(entry["time"])
    expected = str(entry.get("md5", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{32}", expected):
        raise ValueError("A complete directory MD5 is required")
    if offset < 0 or not 0 <= size <= max_bytes:
        raise ValueError("Invalid or oversized payload range")
    candidates = [index_path]
    if part > 0:
        name = f"{index_path.stem}_{part}{index_path.suffix}"
        siblings = [p for p in index_path.parent.iterdir() if p.name.casefold() == name.casefold() and p.is_file()]
        if len(siblings) > 1:
            raise ValueError("Ambiguous numbered-part filename")
        candidates.extend(siblings)
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
