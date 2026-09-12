#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N04-B — Bounded RIP-relative xref of N04-A format/prefix strings."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
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
    "runtime_acquisition/n04b_pe_xref"
)
N04A = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04a_pe_string_hits/scan.json"
)

# N04-A recorded RVAs (verified against SHA below).
TARGETS = [
    {
        "relative": "x64/CShell_x64.dll",
        "label": "specularmap_sprintf",
        "text": r"modeltextures\SpecularMap\%s",
        "rva": 0x54C8F38,
        "file_offset": 88887352,
        "sha256": "d0020ee7ef3eecaf21335b733ba89cceb8bc5a731bdb483ac9b1c9fc40ea3a96",
    },
    {
        "relative": "x64/crossfire.exe",
        "label": "weaponshader_dir",
        "text": r"MODELTEXTURES\Shader\WeaponShader\\",
        "rva": 0x5A12A0,
        "file_offset": 5896672,
        "sha256": "9c0816400a6b25f83f3b8c56717001eddf978f15503d9b3f7cdb3ea281df25e7",
    },
]

BUTE_KEYS = (
    "StandardName",
    "PViewSkinFileName",
    "SpecularMapName",
    "LightCorrectionLegacyShader",
    "PViewModelFileName",
    "RenderStyleFileName",
)
NEAR_CODE = 0x100
NEAR_RDATA = 512
MAX_XREFS = 32
MAX_NEAR_STRINGS = 24


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def parse_pe(data: bytes) -> dict:
    if data[:2] != b"MZ":
        raise ValueError("not MZ")
    pe_off = struct.unpack_from("<I", data, 60)[0]
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValueError("not PE")
    machine, nsec, _, _, _, opt_size, _ = struct.unpack_from("<HHIIIHH", data, pe_off + 4)
    opt = pe_off + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x20B:
        image_base = struct.unpack_from("<Q", data, opt + 24)[0]
    else:
        image_base = struct.unpack_from("<I", data, opt + 28)[0]
    sec_off = opt + opt_size
    sections = []
    for i in range(nsec):
        off = sec_off + i * 40
        raw_name = data[off : off + 8].split(b"\x00", 1)[0]
        name = raw_name.decode("latin-1", errors="replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        chars = struct.unpack_from("<I", data, off + 36)[0]
        sections.append(
            {
                "name": name,
                "va": va,
                "vsize": vsize,
                "raw_ptr": raw_ptr,
                "raw_size": raw_size,
                "executable": bool(chars & 0x20000000),
            }
        )
    return {"machine": machine, "image_base": image_base, "sections": sections}


def rva_to_off(sections: list[dict], rva: int) -> int | None:
    best = None
    best_size = None
    for sec in sections:
        if not (sec["va"] <= rva < sec["va"] + sec["vsize"]):
            continue
        delta = rva - sec["va"]
        if delta >= sec["raw_size"]:
            continue
        if best_size is None or sec["vsize"] < best_size:
            best = sec["raw_ptr"] + delta
            best_size = sec["vsize"]
    return best


def off_to_rva(sections: list[dict], offset: int) -> int | None:
    for sec in sections:
        if sec["raw_ptr"] <= offset < sec["raw_ptr"] + max(sec["raw_size"], 1):
            return sec["va"] + (offset - sec["raw_ptr"])
    return None


def cstring_at(data: bytes, offset: int, limit: int = 240) -> str | None:
    if offset < 0 or offset >= len(data):
        return None
    end = data.find(b"\x00", offset, offset + limit)
    if end < 0:
        end = min(len(data), offset + limit)
    raw = data[offset:end]
    if not raw or any(b < 32 or b >= 127 for b in raw):
        return None
    return raw.decode("ascii")


def rdata_cluster(data: bytes, offset: int, radius: int) -> list[str]:
    lo = max(0, offset - radius)
    hi = min(len(data), offset + radius)
    chunk = data[lo:hi]
    out = []
    start = 0
    for i, b in enumerate(chunk + b"\x00"):
        if b == 0:
            piece = chunk[start:i]
            start = i + 1
            if 4 <= len(piece) <= 240 and all(32 <= x < 127 for x in piece):
                out.append(piece.decode("ascii"))
    # unique preserve order
    seen = set()
    uniq = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq[:40]


def _iter_rip_rel(data: bytes, sec: dict, opcode: int, kind: str):
    start = sec["raw_ptr"]
    end = sec["raw_ptr"] + sec["raw_size"]
    needle = bytes([opcode])
    i = start
    while True:
        i = data.find(needle, i, end)
        if i < 0 or i + 5 > end:
            break
        op_off = i
        instr_start = i
        if i > start and 0x40 <= data[i - 1] <= 0x4F:
            instr_start = i - 1
        modrm = data[op_off + 1] if op_off + 1 < end else 0
        if (modrm & 0xC7) != 0x05 or op_off + 6 > end:
            i += 1
            continue
        rel = struct.unpack_from("<i", data, op_off + 2)[0]
        instr_len = (op_off + 6) - instr_start
        end_off = instr_start + instr_len
        end_rva = sec["va"] + (end_off - sec["raw_ptr"])
        target = end_rva + rel
        yield instr_start, instr_len, target, data[instr_start : instr_start + instr_len].hex(), kind
        i = op_off + 1


def iter_rip_rel_lea(data: bytes, sec: dict):
    yield from _iter_rip_rel(data, sec, 0x8D, "lea")
    yield from _iter_rip_rel(data, sec, 0x8B, "mov_rip")


def nearby_string_leas(data: bytes, sections: list[dict], xref_off: int) -> list[dict]:
    lo = max(0, xref_off - NEAR_CODE)
    hi = min(len(data), xref_off + NEAR_CODE)
    found = []
    i = lo
    while i + 7 < hi and len(found) < MAX_NEAR_STRINGS:
        b = data[i]
        op_off = i
        if 0x40 <= b <= 0x4F and i + 1 < hi and data[i + 1] == 0x8D:
            op_off = i + 1
        elif b == 0x8D:
            op_off = i
        else:
            i += 1
            continue
        if op_off + 5 >= hi:
            break
        if data[op_off] != 0x8D or (data[op_off + 1] & 0xC7) != 0x05:
            i += 1
            continue
        rel = struct.unpack_from("<i", data, op_off + 2)[0]
        instr_len = (op_off + 6) - i
        end_off = i + instr_len
        end_rva = off_to_rva(sections, end_off)
        if end_rva is None:
            i += 1
            continue
        target = end_rva + rel
        toff = rva_to_off(sections, target)
        text = cstring_at(data, toff) if toff is not None else None
        if text:
            found.append({"rva": target, "text": text[:200]})
        i = op_off + 1
    # unique by text
    seen = set()
    uniq = []
    for item in found:
        if item["text"] in seen:
            continue
        seen.add(item["text"])
        uniq.append(item)
    return uniq


def cluster_has_bute(strings: list[str]) -> list[str]:
    hit = []
    blob = " ".join(strings)
    for key in BUTE_KEYS:
        if key in blob:
            hit.append(key)
    return hit


def should_scan_section(sec: dict) -> bool:
    if sec["raw_size"] == 0:
        return False
    if sec["executable"] or sec["name"] in {".text", ".std"} or sec["name"].startswith(".std"):
        return True
    return False


def build_lea_index(data: bytes, pe: dict) -> dict[int, list]:
    index: dict[int, list] = {}
    for sec in pe["sections"]:
        if not should_scan_section(sec):
            continue
        for off, ilen, dest, hx, kind in iter_rip_rel_lea(data, sec):
            bucket = index.setdefault(dest, [])
            if len(bucket) >= MAX_XREFS:
                continue
            bucket.append(
                {
                    "kind": kind,
                    "file_offset": off,
                    "rva": off_to_rva(pe["sections"], off),
                    "hex": hx,
                    "instr_len": ilen,
                }
            )
    return index


def scan_target(data: bytes, pe: dict, target: dict, lea_index: dict[int, list]) -> dict:
    sections = pe["sections"]
    string_off = target["file_offset"]
    string_rva = off_to_rva(sections, string_off)
    expected = target["text"].rstrip("\\")
    actual = cstring_at(data, string_off) or ""
    cluster = rdata_cluster(data, string_off, NEAR_RDATA)
    raw_xrefs = list(lea_index.get(string_rva or -1, []))
    xrefs = []
    for item in raw_xrefs:
        near = nearby_string_leas(data, sections, item["file_offset"])
        rec = dict(item)
        rec["nearby_strings"] = near
        rec["nearby_bute_keys"] = cluster_has_bute([n["text"] for n in near])
        xrefs.append(rec)

    va = pe["image_base"] + (string_rva or 0)
    needle = struct.pack("<Q", va)
    abs_hits = []
    start = 0
    while len(abs_hits) < 16:
        pos = data.find(needle, start)
        if pos < 0:
            break
        abs_hits.append({"file_offset": pos, "rva": off_to_rva(sections, pos)})
        start = pos + 1
    rva32_count = data.count(struct.pack("<I", string_rva or 0)) if string_rva else 0

    cluster_xrefs = []
    for s in cluster[:20]:
        pos = data.find(s.encode("ascii") + b"\x00", max(0, string_off - NEAR_RDATA), string_off + NEAR_RDATA)
        if pos < 0:
            continue
        srva = off_to_rva(sections, pos)
        n = len(lea_index.get(srva or -1, []))
        cluster_xrefs.append({"text": s[:120], "rva": srva, "rip_xref_count": n})

    near_keys_code = sorted({k for x in xrefs for k in x["nearby_bute_keys"]})
    return {
        "label": target["label"],
        "relative": target["relative"],
        "expected_text": target["text"],
        "actual_text": actual,
        "text_matches": expected.lower() in actual.lower(),
        "string_rva": string_rva,
        "n04a_rva": target["rva"],
        "rdata_cluster": cluster,
        "rdata_cluster_bute_keys": cluster_has_bute(cluster),
        "cluster_string_xrefs": cluster_xrefs,
        "rip_xrefs": xrefs,
        "rip_xref_count": len(xrefs),
        "absolute_va_ptrs": abs_hits,
        "rva32_immediate_count": rva32_count,
        "code_nearby_bute_keys": near_keys_code,
    }


def classify(results: list[dict]) -> str:
    any_xref = any(r["rip_xref_count"] > 0 or r["absolute_va_ptrs"] for r in results)
    near = any(r["code_nearby_bute_keys"] for r in results)
    if not any_xref:
        return "NO_XREF"
    if near:
        return "XREF_NEAR_BUTE_KEYS"
    return "XREF_FOUND_UNRELATED"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    n04a = json.loads(N04A.read_text(encoding="utf-8")) if N04A.exists() else {}
    results = []
    errors = []
    for target in TARGETS:
        path = CF / target["relative"].replace("/", os.sep)
        if not path.exists():
            errors.append({"relative": target["relative"], "error": "missing"})
            continue
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != target["sha256"]:
            errors.append({"relative": target["relative"], "error": "sha_mismatch", "got": sha})
            del data
            continue
        pe = parse_pe(data)
        lea_index = build_lea_index(data, pe)
        rec = scan_target(data, pe, target, lea_index)
        rec["sha256"] = sha
        rec["image_base"] = pe["image_base"]
        rec["section_count"] = len(pe["sections"])
        rec["lea_index_targets"] = len(lea_index)
        results.append(rec)
        del data
        del lea_index

    if errors and not results:
        status = "REWORK_REQUIRED"
    else:
        status = classify(results)

    report = {
        "schema": "cf2.p4m01.n04b-pe-xref.v1",
        "generated_at_utc": now(),
        "status": status,
        "jupiter_note": "public Jupiter model/renderstyle load binds LTB/texture indices and TEXTURE1; it does not name WeaponShader/*.CFG or AlphaMap/*.TGA paths. CF delta is these path strings in CShell/crossfire.exe.",
        "n04a_status": n04a.get("status"),
        "results": results,
        "errors": errors,
        "note": "No PE copied into the repo. No disassembly database committed.",
    }
    (OUT / "xref.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "targets": len(results), "errors": len(errors)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
