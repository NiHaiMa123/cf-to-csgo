#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N04-D — Extra static analysis of packed x64/crossfire.exe."""
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
import n04b_pe_xref as n04b  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04d_packed_crossfire_static"
)
REL = "x64/crossfire.exe"
EXPECT_SHA = "9c0816400a6b25f83f3b8c56717001eddf978f15503d9b3f7cdb3ea281df25e7"
WEAPON_OFF = 5896672
WEAPON_TEXT = r"MODELTEXTURES\Shader\WeaponShader\\"

NEEDLES = [
    b"WeaponShader",
    b"AlphaMap",
    b"NormalMap",
    b"SpecularMap",
    b".CFG",
    b".cfg",
    b"%s.CFG",
    b"%s.cfg",
    b"playerviewmesh",
    b"PlayerViewMesh",
]

FILTER = (
    "shader",
    "texture",
    "alphamap",
    "normalmap",
    "specular",
    "weapon",
    ".cfg",
    ".tga",
    ".dtx",
    "playerview",
    "sampler",
    "%s",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in counts.values()), 4)


def parse_imports(data: bytes, pe: dict) -> list[str]:
    names: list[str] = []
    # Optional header DataDirectory[1] Import
    pe_off = struct.unpack_from("<I", data, 60)[0]
    opt = pe_off + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    if dd + 16 > len(data):
        return names
    imp_rva, imp_size = struct.unpack_from("<II", data, dd + 8)
    if not imp_rva:
        return names
    off = n04b.rva_to_off(pe["sections"], imp_rva)
    if off is None:
        return names
    while off + 20 <= len(data):
        lookup, _, _, name_rva, _ = struct.unpack_from("<IIIII", data, off)
        if lookup == 0 and name_rva == 0:
            break
        noff = n04b.rva_to_off(pe["sections"], name_rva)
        if noff is not None:
            end = data.find(b"\x00", noff, noff + 80)
            if end > noff:
                names.append(data[noff:end].decode("ascii", errors="replace"))
        off += 20
        if len(names) >= 40:
            break
    return names


def parse_entry(data: bytes) -> dict:
    pe_off = struct.unpack_from("<I", data, 60)[0]
    opt = pe_off + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    ep = struct.unpack_from("<I", data, opt + 16)[0]
    image_base = struct.unpack_from("<Q", data, opt + 24)[0] if magic == 0x20B else struct.unpack_from("<I", data, opt + 28)[0]
    return {"entry_rva": ep, "image_base": image_base, "magic": hex(magic)}


def extract_ascii(data: bytes, min_len: int = 6) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    i = 0
    n = len(data)
    while i < n:
        if 32 <= data[i] < 127:
            j = i + 1
            while j < n and 32 <= data[j] < 127:
                j += 1
            if j - i >= min_len:
                out.append((i, data[i:j].decode("ascii")))
            i = j
        else:
            i += 1
    return out


def xor_scan(data: bytes) -> list[dict]:
    hits = []
    for key in range(1, 256):
        for needle in NEEDLES:
            enc = bytes(b ^ key for b in needle)
            start = 0
            found = 0
            while found < 5:
                pos = data.find(enc, start)
                if pos < 0:
                    break
                ctx = bytes(b ^ key for b in data[max(0, pos - 16) : pos + len(needle) + 16])
                printable = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
                hits.append(
                    {
                        "xor_key": key,
                        "needle": needle.decode("ascii"),
                        "file_offset": pos,
                        "context_xored": printable,
                    }
                )
                found += 1
                start = pos + 1
        if len(hits) >= 80:
            break
    return hits


def filter_strings(items: list[tuple[int, str]]) -> list[dict]:
    out = []
    for off, s in items:
        sl = s.lower()
        if any(k in sl for k in FILTER):
            out.append(
                {
                    "file_offset": off,
                    "text": s[:240],
                    "has_format": ("%s" in s) or ("%S" in s),
                    "has_path": ("\\" in s) or ("/" in s),
                }
            )
    return out[:200]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    path = CF / REL.replace("/", os.sep)
    if not path.exists():
        (OUT / "scan.json").write_text(json.dumps({"status": "REWORK_REQUIRED", "error": "missing"}, indent=2), encoding="utf-8")
        print('{"status":"REWORK_REQUIRED"}')
        return 1
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECT_SHA:
        (OUT / "scan.json").write_text(
            json.dumps({"status": "REWORK_REQUIRED", "error": "sha_mismatch", "got": sha}, indent=2),
            encoding="utf-8",
        )
        print('{"status":"REWORK_REQUIRED"}')
        return 1

    pe = n04b.parse_pe(data)
    hdr = parse_entry(data)
    imports = parse_imports(data, pe)
    overlay_off = max((s["raw_ptr"] + s["raw_size"] for s in pe["sections"]), default=len(data))
    overlay = max(0, len(data) - overlay_off)

    sections = []
    for i, s in enumerate(pe["sections"]):
        blob = data[s["raw_ptr"] : s["raw_ptr"] + s["raw_size"]]
        sections.append(
            {
                "index": i,
                "name": s["name"],
                "va": s["va"],
                "vsize": s["vsize"],
                "raw_ptr": s["raw_ptr"],
                "raw_size": s["raw_size"],
                "executable": s["executable"],
                "entropy": entropy(blob[: min(len(blob), 256 * 1024)]),
            }
        )

    # strings from lower-entropy sections
    low_strings: list[tuple[int, str]] = []
    for s in pe["sections"]:
        blob = data[s["raw_ptr"] : s["raw_ptr"] + s["raw_size"]]
        ent = entropy(blob[: min(len(blob), 256 * 1024)])
        if ent <= 6.2:
            for off, text in extract_ascii(blob, 6):
                low_strings.append((s["raw_ptr"] + off, text))

    filtered = filter_strings(low_strings)
    format_hits = [x for x in filtered if x["has_format"] and any(k in x["text"].lower() for k in ("shader", "map", "cfg", "tga", "dtx", "texture"))]

    xor_hits = xor_scan(data)
    # plaintext XOR key 0 is excluded; drop hits that are just the known plaintext island
    xor_hits = [h for h in xor_hits if h["xor_key"] != 0]

    lea_index = n04b.build_lea_index(data, pe)
    lea_strings = []
    for dest, refs in lea_index.items():
        toff = n04b.rva_to_off(pe["sections"], dest)
        text = n04b.cstring_at(data, toff) if toff is not None else None
        if not text:
            continue
        sl = text.lower()
        if any(k in sl for k in FILTER):
            lea_strings.append({"rva": dest, "text": text[:200], "xref_count": len(refs)})
    lea_strings.sort(key=lambda x: -x["xref_count"])

    weapon_rva = n04b.off_to_rva(pe["sections"], WEAPON_OFF)
    va = (hdr["image_base"] + weapon_rva) if weapon_rva is not None else 0
    ptr64 = data.count(struct.pack("<Q", va)) if va else 0
    ptr32 = data.count(struct.pack("<I", weapon_rva)) if weapon_rva else 0
    lea_weapon = len(lea_index.get(weapon_rva or -1, []))

    island = n04b.rdata_cluster(data, WEAPON_OFF, 1024)

    cfg_formats = [x for x in filtered if ".cfg" in x["text"].lower() or "%s.cfg" in x["text"].lower()]
    weapon_formats = [x for x in filtered if "weaponshader" in x["text"].lower()]

    if any(x["has_format"] and "weaponshader" in x["text"].lower() for x in filtered) or lea_weapon or ptr64:
        status = "FORMAT_OR_XREF_HIT"
    elif weapon_formats and not lea_weapon and not ptr64:
        status = "STRING_ISLAND_ONLY"
    else:
        status = "PACKED_OPAQUE"

    report = {
        "schema": "cf2.p4m01.n04d-packed-crossfire-static.v1",
        "generated_at_utc": now(),
        "status": status,
        "file": REL,
        "sha256": sha,
        "size_bytes": len(data),
        "entry_rva": hdr["entry_rva"],
        "image_base": hdr["image_base"],
        "imports": imports,
        "overlay_bytes": overlay,
        "sections": sections,
        "weaponshader": {
            "file_offset": WEAPON_OFF,
            "rva": weapon_rva,
            "text": n04b.cstring_at(data, WEAPON_OFF),
            "lea_xrefs": lea_weapon,
            "ptr64_count": ptr64,
            "ptr32_count": ptr32,
            "island_1024": island,
        },
        "filtered_low_entropy_strings": filtered,
        "format_like_filtered": format_hits,
        "cfg_strings": cfg_formats,
        "weaponshader_strings": weapon_formats,
        "xor_hits": xor_hits[:40],
        "xor_hit_count": len(xor_hits),
        "lea_interesting_strings": lea_strings[:80],
        "lea_index_targets": len(lea_index),
        "note": "No unpacker executed. PE not copied into the repo.",
    }
    (OUT / "scan.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "imports": len(imports),
                "filtered": len(filtered),
                "format": len(format_hits),
                "xor": len(xor_hits),
                "lea_weapon": lea_weapon,
                "ptr64": ptr64,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
