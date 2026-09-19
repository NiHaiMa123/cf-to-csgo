#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N04-A — Exact-token string scan of authorized engine PEs."""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04a_pe_string_hits"
)
INVENTORY = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/artifact_inventory.json"
)

TARGETS = [
    "x64/CShell_x64.dll",
    "x64/crossfirebase.dll",
    "x64/crossfire_x64base.dll",
    "x64/crossfire.exe",
    "x64/server_x64.dll",
    "rez/Object_x64.lto",
    "rez/Object.lto",
]

TOKENS = [
    "WeaponShader",
    "AlphaMap",
    "NormalMap",
    "SpecularMap",
    "LightCorrectionLegacyShader",
    "PViewSkinFileName",
    "StandardName",
    "M4A1_S_BornBeast",
    "playerviewmesh",
    "PlayerViewMesh",
    "PLAYERVIEWMESH",
]

FORMAT_MARKERS = ("%s", "%S", "%hs", "%ls", "%ws")
PATH_MARKERS = (
    "WeaponShader\\",
    "WeaponShader/",
    "AlphaMap\\",
    "AlphaMap/",
    "NormalMap\\",
    "NormalMap/",
    "SpecularMap\\",
    "SpecularMap/",
)
MIN_ASCII = 4
CONTEXT = 32
MAX_HITS_PER_TOKEN_FILE = 40


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in counts.values()), 4)


def parse_pe_sections(data: bytes) -> dict:
    info = {
        "mz": data[:2] == b"MZ",
        "pe_offset": None,
        "machine": None,
        "sections": [],
        "import_rva": None,
        "packed_heuristic": False,
        "packed_reasons": [],
    }
    if len(data) < 64 or data[:2] != b"MZ":
        info["packed_reasons"].append("not_mz")
        return info
    pe_off = struct.unpack_from("<I", data, 60)[0]
    info["pe_offset"] = pe_off
    if pe_off + 24 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        info["packed_reasons"].append("no_pe_signature")
        return info
    machine, nsec, _, _, _, opt_size, _ = struct.unpack_from("<HHIIIHH", data, pe_off + 4)
    info["machine"] = hex(machine)
    opt_off = pe_off + 24
    magic = struct.unpack_from("<H", data, opt_off)[0] if opt_off + 2 <= len(data) else 0
    info["optional_magic"] = hex(magic)
    # DataDirectory[1] = imports. PE32 optional header 96, PE32+ 112 before dirs.
    dd_off = opt_off + (112 if magic == 0x20B else 96)
    if dd_off + 16 <= len(data):
        info["import_rva"] = struct.unpack_from("<I", data, dd_off + 8)[0]
    sec_off = opt_off + opt_size
    names = []
    for i in range(nsec):
        off = sec_off + i * 40
        if off + 40 > len(data):
            break
        raw_name = data[off : off + 8].split(b"\x00", 1)[0]
        name = raw_name.decode("latin-1", errors="replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        sample_end = min(len(data), raw_ptr + min(raw_size, 256 * 1024))
        sample = data[raw_ptr:sample_end] if raw_ptr < len(data) else b""
        info["sections"].append(
            {
                "name": name,
                "va": va,
                "vsize": vsize,
                "raw_ptr": raw_ptr,
                "raw_size": raw_size,
                "sample_entropy": entropy(sample) if sample else None,
            }
        )
        names.append(name.lower())
    packer_names = ("upx", "vmp", "themida", ".vmp", "aspack", "pec1", "pec2")
    if any(any(p in n for p in packer_names) for n in names):
        info["packed_heuristic"] = True
        info["packed_reasons"].append("packer_section_name")
    if info["sections"]:
        first = info["sections"][0]
        if (first.get("sample_entropy") or 0) >= 7.2:
            info["packed_heuristic"] = True
            info["packed_reasons"].append("first_section_entropy>=7.2")
    if not info["import_rva"]:
        info["packed_heuristic"] = True
        info["packed_reasons"].append("no_import_rva")
    return info


def offset_to_rva(sections: list[dict], offset: int) -> int | None:
    for sec in sections:
        raw_ptr = sec["raw_ptr"]
        raw_size = sec["raw_size"]
        if raw_ptr <= offset < raw_ptr + max(raw_size, 1):
            return sec["va"] + (offset - raw_ptr)
    return None


def printable_context(data: bytes, start: int, end: int) -> str:
    lo = max(0, start - CONTEXT)
    hi = min(len(data), end + CONTEXT)
    chunk = data[lo:hi]
    return "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)


def looks_format(text: str) -> bool:
    upper = text
    if any(m in upper for m in FORMAT_MARKERS):
        return True
    if any(m.lower() in text.lower() for m in PATH_MARKERS):
        return True
    return False


def scan_ascii(data: bytes, sections: list[dict]) -> list[dict]:
    hits: list[dict] = []
    counts: dict[str, int] = {}
    n = len(data)
    i = 0
    tokens_l = [(t, t.lower()) for t in TOKENS]
    while i < n:
        b = data[i]
        if 32 <= b < 127:
            j = i + 1
            while j < n and 32 <= data[j] < 127:
                j += 1
            if j - i >= MIN_ASCII:
                s = data[i:j].decode("ascii")
                sl = s.lower()
                for token, token_l in tokens_l:
                    if token_l not in sl:
                        continue
                    key = token
                    counts[key] = counts.get(key, 0) + 1
                    if counts[key] <= MAX_HITS_PER_TOKEN_FILE:
                        hits.append(
                            {
                                "token": token,
                                "encoding": "ascii",
                                "file_offset": i,
                                "rva": offset_to_rva(sections, i),
                                "text": s[:240],
                                "is_format_like": looks_format(s),
                                "context": printable_context(data, i, j),
                            }
                        )
            i = j
        else:
            i += 1
    return hits, counts


def scan_utf16le(data: bytes, sections: list[dict]) -> list[dict]:
    hits: list[dict] = []
    counts: dict[str, int] = {}
    n = len(data)
    i = 0
    tokens_l = [(t, t.lower()) for t in TOKENS]
    while i + 1 < n:
        lo, hi = data[i], data[i + 1]
        if 32 <= lo < 127 and hi == 0:
            chars = [lo]
            j = i + 2
            while j + 1 < n and 32 <= data[j] < 127 and data[j + 1] == 0:
                chars.append(data[j])
                j += 2
            if len(chars) >= MIN_ASCII:
                s = bytes(chars).decode("ascii")
                sl = s.lower()
                for token, token_l in tokens_l:
                    if token_l not in sl:
                        continue
                    key = token
                    counts[key] = counts.get(key, 0) + 1
                    if counts[key] <= MAX_HITS_PER_TOKEN_FILE:
                        hits.append(
                            {
                                "token": token,
                                "encoding": "utf16le",
                                "file_offset": i,
                                "rva": offset_to_rva(sections, i),
                                "text": s[:240],
                                "is_format_like": looks_format(s),
                                "context": printable_context(data, i, j),
                            }
                        )
            i = j
        else:
            i += 1
    return hits, counts


def inventory_sha(rel_posix: str) -> str | None:
    if not INVENTORY.exists():
        return None
    dump = json.loads(INVENTORY.read_text(encoding="utf-8"))
    needle = rel_posix.replace("\\", "/").lower()
    for row in dump.get("inventory") or []:
        alias = str(row.get("path_alias") or "").replace("\\", "/").lower()
        if alias == needle:
            return row.get("sha256")
    return None


def classify_file(pe: dict, hits: list[dict]) -> str:
    if pe.get("packed_heuristic") and not hits:
        return "packed_or_no_hit"
    if any(h.get("is_format_like") for h in hits):
        return "format_string_hit"
    if hits:
        return "token_hit_no_format"
    if pe.get("packed_heuristic"):
        return "packed_or_no_hit"
    return "no_hit"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    all_hits = []
    missing = []
    for rel in TARGETS:
        path = CF / rel.replace("/", os.sep)
        rec = {
            "relative": rel.replace("\\", "/"),
            "abs_present": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        if not path.exists() or path.stat().st_size <= 8:
            rec["status"] = "missing_or_stub"
            missing.append(rel)
            files.append(rec)
            continue
        data = path.read_bytes()
        rec["sha256"] = hashlib.sha256(data).hexdigest()
        rec["inventory_sha256"] = inventory_sha(rel)
        rec["sha_matches_inventory"] = rec["sha256"] == rec["inventory_sha256"]
        pe = parse_pe_sections(data)
        rec["pe"] = {
            "mz": pe["mz"],
            "machine": pe["machine"],
            "optional_magic": pe.get("optional_magic"),
            "import_rva": pe.get("import_rva"),
            "packed_heuristic": pe["packed_heuristic"],
            "packed_reasons": pe["packed_reasons"],
            "section_count": len(pe["sections"]),
            "sections": pe["sections"],
        }
        ascii_hits, ascii_counts = scan_ascii(data, pe["sections"])
        u16_hits, u16_counts = scan_utf16le(data, pe["sections"])
        hits = ascii_hits + u16_hits
        rec["hit_counts_ascii"] = ascii_counts
        rec["hit_counts_utf16le"] = u16_counts
        rec["hit_count"] = len(hits)
        rec["format_like_count"] = sum(1 for h in hits if h["is_format_like"])
        rec["class"] = classify_file(pe, hits)
        files.append(rec)
        for hit in hits:
            hit["relative"] = rec["relative"]
            all_hits.append(hit)
        del data

    format_hits = [h for h in all_hits if h["is_format_like"]]
    classes = Counter(f.get("class") for f in files if f.get("class"))
    if any(f.get("class") == "format_string_hit" for f in files):
        status = "FORMAT_STRING_HIT"
    elif any(f.get("class") == "token_hit_no_format" for f in files):
        status = "TOKEN_HIT_NO_FORMAT"
    elif missing and len(missing) == len(TARGETS):
        status = "REWORK_REQUIRED"
    else:
        status = "PACKED_OR_NO_HIT"

    report = {
        "schema": "cf2.p4m01.n04a-pe-string-hits.v1",
        "generated_at_utc": now(),
        "cf_root": str(CF),
        "status": status,
        "file_classes": dict(classes),
        "files": files,
        "format_like_hits": format_hits,
        "hit_count": len(all_hits),
        "hits_truncated_per_token": MAX_HITS_PER_TOKEN_FILE,
        "note": "PE binaries are not copied into the repo. Offsets are local-file only.",
    }
    (OUT / "hits.json").write_text(
        json.dumps({"hits": all_hits, "generated_at_utc": now()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "scan.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "files": len(files), "hits": len(all_hits), "format": len(format_hits)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
