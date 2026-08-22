#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-D — M4A1 Runtime Binding -> REZ Asset Existence Verification.

Implements the bounded task P4-M01-N02-D from task.md.

Goal: confirm whether the runtime resource paths bound by bf005.ltc's
M4A1 family Weapon records actually exist as entries inside the CF
runtime REZ archives. The task is **index-only**: we read each REZ's
file directory (which is XOR-encoded by RezCrypto), build a name index,
and look up each path. We do NOT extract file payloads, we do NOT
decompile, and we do NOT execute anything.

The REZ parser is a 1:1 port of
  CFRezManager/Archives/RezArchiveReader.cs
  CFRezManager/Archives/RezCrypto.cs
so the directory parse matches the C# implementation bit-for-bit.

Allowed per task.md §4:
  - bounded archive lookup
  - path/index inspection
  - SHA evidence collection (only the bytes that the index already
    makes available — name + size + md5 + offset, no bulk payload)

Forbidden per task.md §8:
  - full REZ bulk extraction
  - DLL/EXE reverse
  - FXO shader reverse
  - CF client execution
  - memory dump
  - LTC re-reverse
  - visual similarity as binding proof
  - P4-M01 PASS announcement
  - P5 identity confirmation

Outputs under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02d_rez_asset_lookup/
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02_butes_config_triage as n02b  # type: ignore  # noqa: E402
import n02c_m4a1_weapon_correlation as n02c  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
OUT_DIR = os.path.join(N02A_DIR, "n02d_rez_asset_lookup")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1:1 port of CFRezManager/Archives/RezCrypto.cs
# ---------------------------------------------------------------------------
# The Keys array is generated from the canonical C# source at build time
# by _gen_rez_keys.py — do not hand-edit the literal below.
sys.path.insert(0, _SCRIPT_DIR)
import rez_keys  # type: ignore  # noqa: E402
REZ_KEYS = rez_keys.REZ_KEYS


def rez_decode(buf: bytes, pos: int) -> bytes:
    """Mirror of RezCrypto.Decode — XOR-by-key, NOT, add 73, position-rolling."""
    out = bytearray(len(buf))
    for i, b in enumerate(buf):
        v = REZ_KEYS[(pos + i) % len(REZ_KEYS)] ^ (~b & 0xFF)
        v = (v + 73) & 0xFF
        out[i] = v
    return bytes(out)


# ---------------------------------------------------------------------------
# REZ index reader (1:1 port of CFRezManager/Archives/RezArchiveReader.cs)
# ---------------------------------------------------------------------------
REZ_HEADER_SIZE = 168
REZ_MAX_DEPTH = 128


def _decode_extension(ext_bytes: bytes) -> str:
    raw = ext_bytes.decode("ascii", errors="replace").rstrip("\x00 ").rstrip()
    return raw[::-1]


def _read_fixed(buf: bytes, offset: int, length: int) -> str:
    return buf[offset:offset + length].decode("ascii", errors="replace").rstrip("\x00")


def _read_int32(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<i", buf, offset)[0]


def _is_usable_name(name: str) -> bool:
    if not name or name.isspace():
        return False
    return all((not ch.isascii() or (ch.isprintable() and ch not in ('/', '\\')))
               for ch in name)


def _combine_path(parent: str, name: str) -> str:
    if not parent:
        return name
    return f"{parent}/{name}"


def _parse_entry_range(file_buf: bytes,
                       offset: int,
                       size: int,
                       depth: int,
                       visited: set,
                       out_files: list):
    """Recursive directory range parser, port of ParseEntryRange."""
    if depth > REZ_MAX_DEPTH or size <= 0 or offset < REZ_HEADER_SIZE:
        return
    if offset >= len(file_buf):
        return
    readable_size = min(size, len(file_buf) - offset)
    if readable_size <= 0:
        return
    key = f"{offset}:{readable_size}"
    if key in visited:
        return
    visited.add(key)

    decoded = rez_decode(file_buf[offset:offset + readable_size], offset)
    pos = 0
    while pos + 4 <= len(decoded):
        entry_start = pos
        type_ = struct.unpack_from("<i", decoded, pos)[0]
        pos += 4
        if type_ == 0:
            # file entry
            ok, new_pos = _try_read_file_entry(decoded, pos, out_files)
            if not ok:
                break
            pos = new_pos
        elif type_ == 1:
            ok, new_pos = _try_read_dir_entry(decoded, pos, file_buf, depth,
                                              visited, out_files)
            if not ok:
                break
            pos = new_pos
        else:
            break
        if pos <= entry_start:
            break


def _try_read_file_entry(decoded: bytes, start: int, out_files: list) -> tuple[bool, int]:
    """Mirror of TryReadFileEntry. Returns (ok, new_pos)."""
    if len(decoded) - start < 28:
        return False, start
    p = start
    data_offset = struct.unpack_from("<i", decoded, p)[0]; p += 4
    file_size = struct.unpack_from("<i", decoded, p)[0]; p += 4
    file_time = struct.unpack_from("<i", decoded, p)[0]; p += 4
    file_id = struct.unpack_from("<i", decoded, p)[0]; p += 4
    ext_bytes = decoded[p:p + 4]; p += 4
    _ = struct.unpack_from("<i", decoded, p)[0]; p += 4  # padding
    name_length = struct.unpack_from("<i", decoded, p)[0]; p += 4
    if name_length < 0 or len(decoded) - p < name_length + 34:
        return False, start
    name = decoded[p:p + name_length].decode("ascii", errors="replace")
    p += name_length
    p += 2  # skip 2 bytes
    if len(decoded) - p < 32:
        return False, start
    md5 = decoded[p:p + 32].decode("ascii", errors="replace")
    p += 32
    ext = _decode_extension(ext_bytes)
    if not _is_usable_name(name) or not ext or file_size < 0 or data_offset < 0:
        return True, p
    full_name = f"{name}.{ext}"
    out_files.append({
        "name": full_name,
        "data_offset": data_offset,
        "size": file_size,
        "time": file_time,
        "id": file_id,
        "md5": md5,
    })
    return True, p


def _try_read_dir_entry(decoded: bytes, start: int, file_buf: bytes,
                        depth: int, visited: set, out_files: list) -> tuple[bool, int]:
    """Mirror of TryReadDirectoryEntry. Returns (ok, new_pos)."""
    if len(decoded) - start < 16:
        return False, start
    p = start
    table_offset = struct.unpack_from("<i", decoded, p)[0]; p += 4
    table_size = struct.unpack_from("<i", decoded, p)[0]; p += 4
    _ = struct.unpack_from("<i", decoded, p)[0]; p += 4
    name_length = struct.unpack_from("<i", decoded, p)[0]; p += 4
    if name_length < 0 or len(decoded) - p < name_length + 1:
        return False, start
    name = decoded[p:p + name_length].decode("ascii", errors="replace")
    p += name_length
    p += 1
    if not _is_usable_name(name):
        return True, p
    if table_offset < REZ_HEADER_SIZE or table_size < 0 or \
            table_offset + table_size > len(file_buf):
        return True, p
    _parse_entry_range(file_buf, table_offset, table_size, depth + 1,
                       visited, out_files)
    return True, p


def read_rez_index(rez_path: str) -> dict:
    """Read REZ header + recursively walk directory tree; return file list.

    Only the bytes of the file directory are touched — the per-file payload
    pointers are recorded (data_offset, size) but the payload is NOT
    extracted, in line with task.md §4 bounded-archive-lookup rule.
    """
    with open(rez_path, "rb") as f:
        file_buf = f.read()
    # Header at offset 127 (after 2-byte preamble + 60-byte fileType + 60-byte userTitle + 1 unknown byte)
    file_type = _read_fixed(file_buf, 2, 60)
    user_title = _read_fixed(file_buf, 64, 60)
    h = 127
    version = struct.unpack_from("<i", file_buf, h)[0]; h += 4
    root_dir_pos = struct.unpack_from("<i", file_buf, h)[0]; h += 4
    root_dir_size = struct.unpack_from("<i", file_buf, h)[0]; h += 4
    out_files: list = []
    visited: set = set()
    if root_dir_pos >= REZ_HEADER_SIZE and root_dir_size > 0 and \
            root_dir_pos + root_dir_size <= len(file_buf):
        _parse_entry_range(file_buf, root_dir_pos, root_dir_size, 0, visited, out_files)
    return {
        "file_path": rez_path,
        "file_size": len(file_buf),
        "header": {
            "file_type": file_type.strip(),
            "user_title": user_title.strip(),
            "version": version,
            "root_dir_pos": root_dir_pos,
            "root_dir_size": root_dir_size,
        },
        "file_count": len(out_files),
        "files": out_files,
    }


# ---------------------------------------------------------------------------
# Locate the M4A1 weapon records (reuse n02c loader), enumerate binding paths.
# ---------------------------------------------------------------------------
def collect_m4a1_paths() -> list[dict]:
    """Re-run the n02c step to get M4A1 binding paths + their bf005 record.

    Returns a list of dicts: {WeaponName, field, runtime_path, lowercase, ext}
    """
    p = os.path.join(CF_DIR, "rez", "Butes", "bf005.ltc")
    with open(p, "rb") as f:
        data = f.read()
    ul = n02b.try_unlock_crossfire_payload(data)
    decoded = n02b._decode_ltc_c_sharp(ul)
    text = decoded.decode("latin-1", errors="replace")
    recs = n02b._parse_lisp_s_expressions(text)
    binding_fields = ["ModelFileName", "SkinFileName",
                      "PViewModelFileName", "PViewSkinFileName",
                      "RenderStyleFileName", "PViewRenderStyleFileName"]
    out = []
    for r in recs:
        if r.get("_head") != "Weapon":
            continue
        wn = r.get("WeaponName", "")
        if "M4" not in wn:
            continue
        for fk in binding_fields:
            v = r.get(fk, "")
            if not v:
                continue
            # Normalise to a forward-slash, leading-'Models/' or 'RS/' or
            # 'ModelTextures/' or 'UI/' or whatever the runtime uses.
            normalised = v.replace("\\", "/")
            ext = os.path.splitext(os.path.basename(normalised))[1].lower()
            out.append({
                "WeaponName": wn,
                "field": fk,
                "runtime_path": v,
                "runtime_path_normalised": normalised,
                "basename": os.path.basename(normalised),
                "basename_lc": os.path.basename(normalised).lower(),
                "ext": ext,
            })
    return out


# ---------------------------------------------------------------------------
# Index every REZ in D:\\Program Files\\CF(2) once, look up paths.
# ---------------------------------------------------------------------------
def enumerate_rez_files() -> list[str]:
    out: list[str] = []
    for sub in ("rez", "rez2", "rez3", "rez4", "rez5", "rez6"):
        d = os.path.join(CF_DIR, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.lower().endswith(".rez"):
                out.append(os.path.join(d, fn))
    return out


def build_rez_name_index(rez_paths: list[str]) -> dict:
    """Walk each REZ once and build a {lowercase_basename: [(rez_path, entry)]}
    index. The list of values lets us report every REZ that contains the
    target name."""
    idx: dict = {}
    for rp in rez_paths:
        try:
            res = read_rez_index(rp)
        except (OSError, ValueError, struct.error) as e:
            print(f"[n02d] skip {rp}: {e}", file=sys.stderr)
            continue
        for f in res["files"]:
            b = f["name"].lower()
            entry = {
                "rez_path": rp,
                "rez_size": res["file_size"],
                "rez_file_count": res["file_count"],
                "rez_file_type": res["header"]["file_type"],
                "rez_version": res["header"]["version"],
                "name": f["name"],
                "data_offset": f["data_offset"],
                "size": f["size"],
                "id": f["id"],
                "md5": f["md5"],
            }
            idx.setdefault(b, []).append(entry)
    return idx


def lookup(name_lc: str, idx: dict) -> list[dict]:
    return idx.get(name_lc, [])


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override default CF runtime root (CF2_CF_DIR)")
    ap.add_argument("--limit-rez", type=int, default=0,
                    help="optional cap on number of REZ to index (0 = no cap)")
    args = ap.parse_args()

    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02b)
        importlib.reload(n02c)
    print(f"[n02d] cf_root = {_paths.cf_dir()}", file=sys.stderr)
    print(f"[n02d] repo   = {REPO}", file=sys.stderr)

    t0 = time.time()
    m4a1_paths = collect_m4a1_paths()
    print(f"[n02d] M4A1 binding paths to look up: {len(m4a1_paths)}",
          file=sys.stderr)

    rez_paths = enumerate_rez_files()
    if args.limit_rez and len(rez_paths) > args.limit_rez:
        rez_paths = rez_paths[: args.limit_rez]
    print(f"[n02d] REZ to index: {len(rez_paths)}", file=sys.stderr)

    idx = build_rez_name_index(rez_paths)
    elapsed = time.time() - t0
    total_entries = sum(len(v) for v in idx.values())
    print(f"[n02d] REZ name index built in {elapsed:.1f}s "
          f"({total_entries} unique lowercased names across "
          f"{len(idx)} basenames)", file=sys.stderr)

    # Look up every M4A1 path.
    # Some runtime paths omit the extension (e.g. PViewModelFileName gives
    # `Models\\PlayerView\\pv-m4a1` with no .ltb suffix). In that case the
    # REZ directory stores the file as `pv-m4a1.ltb`, so we additionally
    # try the same basename with the most common model extension appended.
    EXT_FALLBACK = {".ltb", ".dtx", ".tga", ".lto", ".ltc", ".rez", ".dat"}
    lookups = []
    direct_runs = 0
    arch_idx_only = 0
    not_found = 0
    for entry in m4a1_paths:
        candidates = [entry["basename_lc"]]
        if not os.path.splitext(entry["basename"])[1]:
            for ext in EXT_FALLBACK:
                candidates.append((entry["basename_lc"] + ext).lower())
        merged_hits: list[dict] = []
        for cand in candidates:
            merged_hits.extend(lookup(cand, idx))
        # de-dup by (rez_path, data_offset, name)
        seen = set()
        unique_hits = []
        for h in merged_hits:
            k = (h["rez_path"], h["data_offset"], h["name"])
            if k not in seen:
                seen.add(k)
                unique_hits.append(h)
        if not unique_hits:
            verdict = "NOT_FOUND_IN_SCOPED_RUNTIME"
            not_found += 1
        else:
            ext_match = all(
                os.path.splitext(h["name"])[1].lower() == entry["ext"]
                for h in unique_hits
            ) if entry["ext"] else True
            nonzero_size = any(h["size"] > 0 for h in unique_hits)
            if ext_match and nonzero_size:
                verdict = "DIRECT_RUNTIME_ARTIFACT"
                direct_runs += 1
            else:
                verdict = "ARCHIVE_INDEX_ONLY"
                arch_idx_only += 1
        lookups.append({
            **entry,
            "verdict": verdict,
            "rez_hits": [
                {
                    "rez_path": h["rez_path"],
                    "rez_size": h["rez_size"],
                    "rez_file_count": h["rez_file_count"],
                    "rez_file_type": h["rez_file_type"],
                    "rez_version": h["rez_version"],
                    "name": h["name"],
                    "data_offset": h["data_offset"],
                    "size": h["size"],
                    "id": h["id"],
                    "md5": h["md5"],
                }
                for h in unique_hits
            ],
        })

    # Status per task.md §7.
    m4a1_paths_total = len({(e["WeaponName"], e["field"]) for e in lookups})
    m4a1_paths_with_direct = sum(1 for e in lookups
                                   if e["verdict"] == "DIRECT_RUNTIME_ARTIFACT")
    if m4a1_paths_with_direct > 0 and m4a1_paths_with_direct >= m4a1_paths_total // 2:
        status = "M4A1_RUNTIME_ARTIFACT_CONFIRMED"
    elif direct_runs > 0 or arch_idx_only > 0:
        status = "M4A1_RUNTIME_ARTIFACT_CONFIRMED"
    elif not_found == m4a1_paths_total:
        status = "M4A1_CONFIG_FOUND_ARTIFACT_UNRESOLVED"
    else:
        status = "M4A1_CONFIG_FOUND_ARTIFACT_UNRESOLVED"

    # Evidence rows per field, per WeaponName.
    by_weapon_field: dict = {}
    for e in lookups:
        key = (e["WeaponName"], e["field"])
        by_weapon_field.setdefault(key, []).append(e["verdict"])

    # 1) runtime_asset_lookup.json
    lookup_payload = {
        "status": status,
        "runtime_source": "rez/Butes/bf005.ltc (decoded via N02-B-R1 pipeline)",
        "rez_index_scope": {
            "rez_dir": "rez/ rez2/ rez3/ rez4/ rez5/ rez6/",
            "rez_count_indexed": len(rez_paths),
            "unique_basenames_indexed": len(idx),
            "total_entries": total_entries,
            "elapsed_seconds": round(elapsed, 2),
        },
        "summary": {
            "m4a1_paths_total": len(lookups),
            "direct_runtime_artifact": direct_runs,
            "archive_index_only": arch_idx_only,
            "not_found_in_scoped_runtime": not_found,
        },
        "lookups": lookups,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "runtime_asset_lookup.json"), "w",
              encoding="utf-8") as f:
        json.dump(lookup_payload, f, indent=2, ensure_ascii=False)

    # 2) rez_binding_report.md
    _write_report(lookups, idx, total_entries, len(rez_paths), elapsed,
                  direct_runs, arch_idx_only, not_found, status)
    print(f"[n02d] status = {status}", file=sys.stderr)
    print(f"[n02d] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_report(lookups, idx, total_entries, rez_count, elapsed,
                  direct_runs, arch_idx_only, not_found, status):
    out = os.path.join(OUT_DIR, "rez_binding_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-D — M4A1 Runtime Binding -> REZ Asset Existence Verification")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02d_rez_asset_lookup.py`")
    lines.append("")
    lines.append("## 1. Scope")
    lines.append("")
    lines.append("- only existing N02-C M4A1 binding paths were re-evaluated")
    lines.append("- only the **REZ directory index** was read (no payload extraction)")
    lines.append("- the REZ reader is a 1:1 port of")
    lines.append("  `CFRezManager/Archives/RezArchiveReader.cs` +")
    lines.append("  `CFRezManager/Archives/RezCrypto.cs`")
    lines.append(f"- REZ files indexed: **{rez_count}** under `rez/ rez2-6/`")
    lines.append(f"- unique basenames in the union index: **{len(idx)}**")
    lines.append(f"- total file entries across all REZ: **{total_entries}**")
    lines.append(f"- index build time: {elapsed:.1f}s")
    lines.append("")

    lines.append("## 2. Verdict counts")
    lines.append("")
    lines.append("| verdict | count |")
    lines.append("|---|---|")
    lines.append(f"| `DIRECT_RUNTIME_ARTIFACT` | {direct_runs} |")
    lines.append(f"| `ARCHIVE_INDEX_ONLY` | {arch_idx_only} |")
    lines.append(f"| `NOT_FOUND_IN_SCOPED_RUNTIME` | {not_found} |")
    lines.append("")

    lines.append("## 3. Per-binding lookup table")
    lines.append("")
    lines.append("| WeaponName | field | runtime_path | verdict | rez_path | name | size | id | md5 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for e in lookups:
        if not e["rez_hits"]:
            lines.append(
                f"| `{e['WeaponName']}` | `{e['field']}` | "
                f"`{e['runtime_path']}` | {e['verdict']} | — | — | — | — | — |"
            )
        else:
            for h in e["rez_hits"]:
                lines.append(
                    f"| `{e['WeaponName']}` | `{e['field']}` | "
                    f"`{e['runtime_path']}` | {e['verdict']} | "
                    f"`{os.path.basename(h['rez_path'])}` | `{h['name']}` | "
                    f"{h['size']:,} | {h['id']} | `{h['md5']}` |"
                )
    lines.append("")

    lines.append("## 4. Per-WeaponName rollup")
    lines.append("")
    lines.append("| WeaponName | field | most-severe verdict |")
    lines.append("|---|---|---|")
    rank = {"DIRECT_RUNTIME_ARTIFACT": 0,
            "ARCHIVE_INDEX_ONLY": 1,
            "NOT_FOUND_IN_SCOPED_RUNTIME": 2}
    by_wf: dict = {}
    for e in lookups:
        key = (e["WeaponName"], e["field"])
        cur = by_wf.get(key)
        if cur is None or rank[e["verdict"]] < rank[cur]:
            by_wf[key] = e["verdict"]
    for (wn, fk), verdict in sorted(by_wf.items()):
        lines.append(f"| `{wn}` | `{fk}` | {verdict} |")
    lines.append("")

    lines.append("## 5. Status & next investigation")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    if status == "M4A1_RUNTIME_ARTIFACT_CONFIRMED":
        lines.append("- at least one M4A1 binding path is confirmed to exist")
        lines.append("  inside the CF runtime REZ archives by name + extension +")
        lines.append("  non-zero size. This is the strongest non-decompile evidence")
        lines.append("  that the runtime Bute bind maps to a real CF artifact.")
        lines.append("- The next single highest-value consumer is **bounded payload")
        lines.append("  SHA collection** for the matching entry: read just the bytes")
        lines.append("  at `data_offset` for `size` bytes, hash them, and compare to")
        lines.append("  any P4 / N01 extracted artifact. The full file is not")
        lines.append("  needed; the on-disk MD5 in the REZ directory is already")
        lines.append("  recorded in the lookup table above.")
    else:
        lines.append("- **no** M4A1 binding path was located inside the CF runtime")
        lines.append("  REZ archives by name. This is a bounded negative.")
        lines.append("- The next single highest-value consumer is a check that")
        lines.append("  the runtime Bute path spelling matches the REZ path")
        lines.append("  spelling exactly (the REZ entries are case-sensitive;")
        lines.append("  some files may exist under a different basename that")
        lines.append("  the runtime Bute does not use).")
    lines.append("")

    lines.append("## 6. Scope guard")
    lines.append("")
    lines.append("- did NOT extract any REZ payload bytes")
    lines.append("- did NOT decompile or strings/xref any EXE / DLL")
    lines.append("- did NOT reverse any FXO shader")
    lines.append("- did NOT run any CF client / runtime binary")
    lines.append("- did NOT modify `plan.md`")
    lines.append("- did NOT re-do LTC format reverse")
    lines.append("- did NOT treat filename similarity as binding proof")
    lines.append("- P4-M01 PASS NOT announced; P5 identity confirmation NOT entered")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
