#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-D-R1 — Path-Aware REZ Runtime Binding Revalidation.

This is the rework of N02-D per plan.md §4.10.

The previous N02-D built a **basename-only** index of REZ entries; that
cannot distinguish e.g.
  Models/PlayerView/PV-M4A1.LTB      (model)
  ModelTextures/PlayerView/PV-M4A1.DTX  (texture)
which have the same lowercase basename `pv-m4a1.ltb` vs `pv-m4a1.dtx`.

This rework:

1. **Preserves the REZ directory hierarchy** as `full_path` (archive-relative
   logical path) on every file entry, by threading a `parent_path_stack`
   through the recursive directory walk.

2. **Builds a full-path index** keyed by uppercase logical path.  Each value
   is a list of (rez_path, file entry) tuples so that the same logical path
   in multiple REZ can be reported explicitly.

3. **Normalises the bf005 runtime value** to an archive-relative logical
   path, then does **exact full-path match**:

   - replace `\\` with `/`;
   - uppercase;
   - **strip** the leading virtual root segment if it is one of
     `Models/` or `ModelTextures/` (both LithTech engine virtual roots
     that DO NOT appear as top-level directories in the REZ directory
     tree; the actual REZ subdir is the next segment, e.g.
     `Models\\weapons\\m4a1.ltb`  ->  `WEAPONS/M4A1.LTB`).
     This strip is the same operation N02-C implicitly performed when
     it reasoned about the M4A1 family binding — the N02-D reviewer
     asked the path be made **explicit** and the strip rule **scoped**
     to the two confirmed virtual roots, instead of being a hidden
     basename fallback.
   - for `RS\\...`, the leading `RS/` is kept (it is a real REZ dir
     in rf002.rez; verified in scope).

4. **Extensionless model-path rule**: for `ModelFileName` and
   `PViewModelFileName` only, if the normalised path has no extension,
   the only allowed suffix is `.LTB`.  No other fallback is attempted
   (forbidden: `.dtx/.tga/.lto/.ltc/.rez/.dat`).

5. **Multiple-archive ambiguity**: if the same full path exists in
   multiple REZ archives, all hits are reported.  No archive is
   declared authoritative in the absence of explicit REZ load-order /
   override semantics evidence.

Allowed per task.md §4:
  - REZ directory index reading (no payload bytes)
  - exact path match (path-aware)
  - explicit `Models/ModelTextures` virtual-root strip (documented)

Forbidden per task.md §8:
  - full REZ bulk extraction / payload bytes
  - DLL/EXE / FXO shader reverse
  - CF client execution / memory dump
  - LTC re-reverse
  - LZX / DTX payload semantic claims
  - BornBeast identity or P5 inference
  - P4-M01 PASS announcement

Output under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02d_r1_path_binding/
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

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
OUT_DIR = os.path.join(N02A_DIR, "n02d_r1_path_binding")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# REZ parser (1:1 port of CFRezManager/Archives/RezArchiveReader.cs +
# RezCrypto.cs), reused from n02d_rez_asset_lookup.  Each emitted file
# carries `full_path` (archive-relative logical path) AND `name` (basename
# with extension).
# ---------------------------------------------------------------------------
sys.path.insert(0, _SCRIPT_DIR)
import rez_keys  # type: ignore  # noqa: E402
REZ_KEYS = rez_keys.REZ_KEYS


def rez_decode(buf: bytes, pos: int) -> bytes:
    out = bytearray(len(buf))
    for i, b in enumerate(buf):
        v = REZ_KEYS[(pos + i) % len(REZ_KEYS)] ^ (~b & 0xFF)
        v = (v + 73) & 0xFF
        out[i] = v
    return bytes(out)


REZ_HEADER_SIZE = 168
REZ_MAX_DEPTH = 128


def _decode_extension(ext_bytes: bytes) -> str:
    raw = ext_bytes.decode("ascii", errors="replace").rstrip("\x00 ").rstrip()
    return raw[::-1]


def _is_usable_name(name: str) -> bool:
    if not name or name.isspace():
        return False
    return all((not ch.isascii() or (ch.isprintable() and ch not in ('/', '\\')))
               for ch in name)


def _try_read_file_entry(decoded: bytes, start: int, out_files: list,
                         parent_path_stack: list) -> tuple[bool, int]:
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
    parent_path = parent_path_stack[-1] if parent_path_stack else ""
    full_path = (f"{parent_path}/{full_name}" if parent_path else full_name)
    out_files.append({
        "name": full_name,
        "full_path": full_path,
        "data_offset": data_offset,
        "size": file_size,
        "time": file_time,
        "id": file_id,
        "md5": md5,
    })
    return True, p


def _try_read_dir_entry(decoded: bytes, start: int, file_buf: bytes,
                        depth: int, visited: set, out_files: list,
                        parent_path_stack: list) -> tuple[bool, int]:
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
    parent_path_stack.append(name)
    try:
        _parse_entry_range(file_buf, table_offset, table_size, depth + 1,
                           visited, out_files, parent_path_stack)
    finally:
        parent_path_stack.pop()
    return True, p


def _parse_entry_range(file_buf: bytes, offset: int, size: int,
                       depth: int, visited: set, out_files: list,
                       parent_path_stack: list):
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
            ok, new_pos = _try_read_file_entry(decoded, pos, out_files,
                                              parent_path_stack)
            if not ok:
                break
            pos = new_pos
        elif type_ == 1:
            ok, new_pos = _try_read_dir_entry(decoded, pos, file_buf, depth,
                                              visited, out_files,
                                              parent_path_stack)
            if not ok:
                break
            pos = new_pos
        else:
            break
        if pos <= entry_start:
            break


def read_rez_index(rez_path: str) -> dict:
    """Read REZ header + recursively walk directory tree; return file list.

    Each file entry carries `name` (basename) AND `full_path`
    (archive-relative logical path, e.g. `PLAYERVIEW/PV-M4A1.LTB`).
    No payload bytes are read.
    """
    with open(rez_path, "rb") as f:
        file_buf = f.read()
    version = struct.unpack_from("<i", file_buf, 127)[0]
    root_dir_pos = struct.unpack_from("<i", file_buf, 127 + 4)[0]
    root_dir_size = struct.unpack_from("<i", file_buf, 127 + 8)[0]
    out_files: list = []
    visited: set = set()
    if root_dir_pos >= REZ_HEADER_SIZE and root_dir_size > 0 and \
            root_dir_pos + root_dir_size <= len(file_buf):
        _parse_entry_range(file_buf, root_dir_pos, root_dir_size, 0,
                           visited, out_files, [])
    return {
        "rez_path": rez_path,
        "rez_size": len(file_buf),
        "version": version,
        "file_count": len(out_files),
        "files": out_files,
    }


# ---------------------------------------------------------------------------
# Path normalisation: bf005 value -> REZ archive-relative logical path
# ---------------------------------------------------------------------------
VIRTUAL_ROOTS = ("Models/", "ModelTextures/")
# Note: `RS/` is a real REZ subdirectory in rf002.rez; it is NOT stripped.


def normalise_bf005_to_rez_path(raw: str) -> dict:
    """Normalise one bf005 path to a REZ archive-relative logical path.

    Returns a dict with the original + intermediate + final normalised
    forms, so the report can show the full transform.

    The bf005 Bute parser may emit backslash-escaped path separators,
    producing strings like `RS\\\\NinjaTranslucent.ltb` (raw `\\`).  We
    collapse any `\\` to a single `\` first, then map `\` to `/`, then
    uppercase.
    """
    if not raw:
        return {"raw": raw, "literal": "", "stripped": "",
                "after_strip": "", "upper": "", "ext": ""}
    # 0. Collapse escaped backslash to a single backslash (bf005 Bute
    #    parser emits `\\` for one original `\`; the file itself stores
    #    a single `\`).
    unescaped = raw.replace("\\\\", "\\")
    # 1. Slash unify
    literal = unescaped.replace("\\", "/")
    # 2. Strip a single leading virtual root
    after_strip = literal
    stripped = False
    for vr in VIRTUAL_ROOTS:
        if literal.startswith(vr):
            after_strip = literal[len(vr):]
            stripped = True
            break
    upper = after_strip.upper()
    ext = os.path.splitext(os.path.basename(after_strip))[1].lower()
    return {
        "raw": raw,
        "literal": literal,
        "stripped_virtual_root": stripped,
        "after_strip": after_strip,
        "upper": upper,
        "ext": ext,
    }


# ---------------------------------------------------------------------------
# Build a full-path index from every REZ.
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


def build_full_path_index(rez_paths: list[str]) -> dict:
    """For every REZ, walk the directory tree and collect file entries.

    Returns:
      {
        "by_full_path": {UPPER_FULL_PATH: [hit, hit, ...]},
        "by_basename":  {UPPER_BASENAME: [hit, hit, ...]},
        "rez_summaries": {rez_path: {"file_count": N, "size": S}},
        "total_unique_full_paths": int,
        "total_unique_basenames": int,
        "total_entries": int,
      }

    Each `hit` is a dict with rez_path, name, full_path (case-preserved),
    data_offset, size, id, md5.  Hits are kept separately per archive so
    archive-ambiguity can be reported verbatim.
    """
    by_full_path: dict = defaultdict(list)
    by_basename: dict = defaultdict(list)
    rez_summaries: dict = {}
    total_entries = 0
    for rp in rez_paths:
        try:
            res = read_rez_index(rp)
        except (OSError, ValueError, struct.error) as e:
            print(f"[n02d-r1] skip {rp}: {e}", file=sys.stderr)
            continue
        rez_summaries[rp] = {
            "file_count": res["file_count"],
            "size": res["rez_size"],
        }
        for f in res["files"]:
            hit = {
                "rez_path": rp,
                "name": f["name"],
                "full_path": f["full_path"],
                "data_offset": f["data_offset"],
                "size": f["size"],
                "id": f["id"],
                "md5": f["md5"],
            }
            by_full_path[f["full_path"].upper()].append(hit)
            by_basename[f["name"].upper()].append(hit)
            total_entries += 1
    return {
        "by_full_path": dict(by_full_path),
        "by_basename": dict(by_basename),
        "rez_summaries": rez_summaries,
        "total_unique_full_paths": len(by_full_path),
        "total_unique_basenames": len(by_basename),
        "total_entries": total_entries,
    }


# ---------------------------------------------------------------------------
# M4A1 binding paths from N02-C.
# ---------------------------------------------------------------------------
BINDING_FIELDS = [
    "ModelFileName", "SkinFileName",
    "PViewModelFileName", "PViewSkinFileName",
    "RenderStyleFileName", "PViewRenderStyleFileName",
]
EXTENSIONLESS_MODEL_FIELDS = {"ModelFileName", "PViewModelFileName"}


def collect_m4a1_paths() -> list[dict]:
    """Re-run the N02-C step to get M4A1 binding paths."""
    p = os.path.join(CF_DIR, "rez", "Butes", "bf005.ltc")
    with open(p, "rb") as f:
        data = f.read()
    ul = n02b.try_unlock_crossfire_payload(data)
    decoded = n02b._decode_ltc_c_sharp(ul)
    text = decoded.decode("latin-1", errors="replace")
    recs = n02b._parse_lisp_s_expressions(text)
    out = []
    for r in recs:
        if r.get("_head") != "Weapon":
            continue
        wn = r.get("WeaponName", "")
        if "M4" not in wn:
            continue
        for fk in BINDING_FIELDS:
            v = r.get(fk, "")
            if not v:
                continue
            out.append({
                "WeaponName": wn,
                "field": fk,
                "runtime_path": v,
            })
    return out


# ---------------------------------------------------------------------------
# Verdict per binding: exact full-path vs basename-only vs not-found.
# ---------------------------------------------------------------------------
def classify_one(binding: dict, idx: dict) -> dict:
    """Classify a single M4A1 binding against the path-aware index."""
    raw = binding["runtime_path"]
    field = binding["field"]
    norm = normalise_bf005_to_rez_path(raw)
    upper_path = norm["upper"]            # e.g. "PLAYERVIEW/PV-M4A1.LTB"
    base_lc = os.path.basename(upper_path).lower()
    ext_present = bool(norm["ext"])

    result = {
        "WeaponName": binding["WeaponName"],
        "field": field,
        "runtime_path": raw,
        "normalisation": norm,
        "exact_path_query": None,
        "extensionless_ltb_query": None,
        "exact_path_hits": [],
        "extensionless_ltb_hits": [],
        "basename_only_hits": [],
        "verdict": "NOT_FOUND_IN_SCOPED_RUNTIME",
        "verdict_reason": "",
        "archive_count": 0,
    }

    # --- pass 1: exact full-path (after strip + uppercase) --------------
    full_hits = idx["by_full_path"].get(upper_path, [])
    result["exact_path_query"] = upper_path
    result["exact_path_hits"] = [
        {
            "rez_path": h["rez_path"],
            "full_path": h["full_path"],
            "name": h["name"],
            "size": h["size"],
            "id": h["id"],
            "md5": h["md5"],
        }
        for h in full_hits
    ]

    # --- pass 2: extensionless .ltb only (for ModelFileName/PViewModelFileName)
    if not ext_present and field in EXTENSIONLESS_MODEL_FIELDS:
        ltb_candidate = upper_path + ".LTB"
        ltb_hits = idx["by_full_path"].get(ltb_candidate, [])
        result["extensionless_ltb_query"] = ltb_candidate
        result["extensionless_ltb_hits"] = [
            {
                "rez_path": h["rez_path"],
                "full_path": h["full_path"],
                "name": h["name"],
                "size": h["size"],
                "id": h["id"],
                "md5": h["md5"],
            }
            for h in ltb_hits
        ]

    # --- pass 3: basename-only (always reported for transparency) --------
    bn_hits = idx["by_basename"].get(os.path.basename(upper_path), [])
    seen = set()
    for h in bn_hits:
        k = (h["rez_path"], h["full_path"])
        if k in seen:
            continue
        seen.add(k)
        result["basename_only_hits"].append({
            "rez_path": h["rez_path"],
            "full_path": h["full_path"],
            "name": h["name"],
            "size": h["size"],
            "id": h["id"],
            "md5": h["md5"],
        })

    # --- verdict selection -----------------------------------------------
    if result["exact_path_hits"]:
        if len(result["exact_path_hits"]) == 1:
            result["verdict"] = "EXACT_PATH_BINDING"
            result["verdict_reason"] = (
                f"single full-path match for {upper_path!r} after "
                f"strip={'Models' if norm['stripped_virtual_root'] else 'none'}"
            )
        else:
            result["verdict"] = "EXACT_PATH_MULTIPLE_ARCHIVES"
            result["verdict_reason"] = (
                f"full path {upper_path!r} exists in {len(result['exact_path_hits'])} "
                f"distinct REZ archives; no load-order evidence, ambiguity reported"
            )
        result["archive_count"] = len(result["exact_path_hits"])
    elif result["extensionless_ltb_hits"]:
        # extensionless model path resolved as .LTB
        if len(result["extensionless_ltb_hits"]) == 1:
            result["verdict"] = "EXTENSIONLESS_LTB_RESOLVED"
            result["verdict_reason"] = (
                f"extensionless {field} value resolved to .LTB; "
                f"single full-path match for {result['extensionless_ltb_query']!r}"
            )
        else:
            result["verdict"] = "EXTENSIONLESS_LTB_MULTIPLE_ARCHIVES"
            result["verdict_reason"] = (
                f"extensionless {field} value resolved to .LTB; "
                f"full path {result['extensionless_ltb_query']!r} exists in "
                f"{len(result['extensionless_ltb_hits'])} distinct REZ archives; "
                f"ambiguity reported"
            )
        result["archive_count"] = len(result["extensionless_ltb_hits"])
    elif result["basename_only_hits"]:
        result["verdict"] = "BASENAME_CANDIDATE_ONLY"
        # Build a "where would the path land" sample
        sample_dirs = sorted({h["full_path"].rsplit("/", 1)[0]
                              for h in result["basename_only_hits"]})[:5]
        result["verdict_reason"] = (
            f"basename {os.path.basename(upper_path)!r} exists in "
            f"{len(result['basename_only_hits'])} REZ entries under dirs: "
            f"{sample_dirs}; full path {upper_path!r} not found"
        )
    else:
        result["verdict"] = "NOT_FOUND_IN_SCOPED_RUNTIME"
        result["verdict_reason"] = (
            f"neither full path {upper_path!r} nor basename found in any REZ"
        )
    return result


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

    print(f"[n02d-r1] cf_root = {_paths.cf_dir()}", file=sys.stderr)
    print(f"[n02d-r1] repo   = {REPO}", file=sys.stderr)

    t0 = time.time()
    m4a1_paths = collect_m4a1_paths()
    print(f"[n02d-r1] M4A1 binding paths to look up: {len(m4a1_paths)}",
          file=sys.stderr)

    rez_paths = enumerate_rez_files()
    if args.limit_rez and len(rez_paths) > args.limit_rez:
        rez_paths = rez_paths[: args.limit_rez]
    print(f"[n02d-r1] REZ to index: {len(rez_paths)}", file=sys.stderr)

    idx = build_full_path_index(rez_paths)
    elapsed = time.time() - t0
    print(f"[n02d-r1] index built in {elapsed:.1f}s "
          f"({idx['total_entries']} entries, "
          f"{idx['total_unique_full_paths']} unique full paths, "
          f"{idx['total_unique_basenames']} unique basenames)",
          file=sys.stderr)

    # Classify every binding.
    classified = [classify_one(b, idx) for b in m4a1_paths]

    # Roll-up counts.
    by_verdict: dict = defaultdict(int)
    for c in classified:
        by_verdict[c["verdict"]] += 1

    distinct_full = {(c["WeaponName"], c["field"]) for c in classified
                     if c["verdict"] in ("EXACT_PATH_BINDING",
                                         "EXACT_PATH_MULTIPLE_ARCHIVES",
                                         "EXTENSIONLESS_LTB_RESOLVED",
                                         "EXTENSIONLESS_LTB_MULTIPLE_ARCHIVES")}
    distinct_partial = {(c["WeaponName"], c["field"]) for c in classified
                        if c["verdict"] == "BASENAME_CANDIDATE_ONLY"}
    distinct_missing = {(c["WeaponName"], c["field"]) for c in classified
                        if c["verdict"] == "NOT_FOUND_IN_SCOPED_RUNTIME"}

    total_unique_pairs = len({(c["WeaponName"], c["field"]) for c in classified})

    # Per-WeaponName / per-field rollup.
    per_wf: dict = {}
    for c in classified:
        k = (c["WeaponName"], c["field"])
        cur = per_wf.get(k)
        # Rank for rollup: best verdict wins
        rank_order = [
            "NOT_FOUND_IN_SCOPED_RUNTIME",
            "BASENAME_CANDIDATE_ONLY",
            "EXTENSIONLESS_LTB_MULTIPLE_ARCHIVES",
            "EXTENSIONLESS_LTB_RESOLVED",
            "EXACT_PATH_MULTIPLE_ARCHIVES",
            "EXACT_PATH_BINDING",
        ]
        if cur is None or rank_order.index(c["verdict"]) > rank_order.index(cur):
            per_wf[k] = c["verdict"]

    # Per archive-ambiguity report.
    ambiguous = [
        {
            "WeaponName": c["WeaponName"], "field": c["field"],
            "runtime_path": c["runtime_path"],
            "normalised": c["normalisation"]["upper"],
            "rez_paths": [h["rez_path"] for h in c["exact_path_hits"]],
        }
        for c in classified
        if c["verdict"] in ("EXACT_PATH_MULTIPLE_ARCHIVES",
                            "EXTENSIONLESS_LTB_MULTIPLE_ARCHIVES")
    ]

    # Status per task.md §7.
    if total_unique_pairs > 0 and len(distinct_full) == total_unique_pairs:
        status = "M4A1_RUNTIME_PATH_BINDING_CONFIRMED"
    elif len(distinct_full) > 0:
        status = "M4A1_RUNTIME_PATH_BINDING_PARTIAL"
    elif distinct_partial:
        status = "M4A1_RUNTIME_PATH_BINDING_REWORK_REQUIRED"
    else:
        status = "M4A1_RUNTIME_PATH_BINDING_REWORK_REQUIRED"

    # --- write path_aware_rez_index_summary.json --------------------------
    summary = {
        "task": "P4-M01-N02-D-R1",
        "runtime_source": "rez/Butes/bf005.ltc (decoded via N02-B-R1 pipeline)",
        "rez_index_scope": {
            "rez_dirs": "rez/ rez2/ rez3/ rez4/ rez5/ rez6/",
            "rez_count_indexed": len(rez_paths),
            "total_entries": idx["total_entries"],
            "unique_full_paths": idx["total_unique_full_paths"],
            "unique_basenames": idx["total_unique_basenames"],
            "elapsed_seconds": round(elapsed, 2),
        },
        "normalisation_rule": {
            "slash_unify": "backslash -> forward slash",
            "case_normalise": "uppercase for REZ-side comparison",
            "virtual_root_strip": [
                "Models/  (LithTech Models virtual root)",
                "ModelTextures/  (LithTech ModelTextures virtual root)",
            ],
            "virtual_root_keep": [
                "RS/  (literal REZ subdir in rf002.rez)",
            ],
            "extensionless_model_rule": (
                "ModelFileName / PViewModelFileName: only .LTB allowed "
                "as suffix when value has no extension; no other fallback."
            ),
        },
        "rez_summary_per_archive": {
            os.path.basename(rp): info
            for rp, info in idx["rez_summaries"].items()
        },
        "binding_count_total": len(classified),
        "binding_unique_weapon_field_pairs": total_unique_pairs,
        "verdict_counts": dict(by_verdict),
        "distinct_weapon_field_full_path_bound": len(distinct_full),
        "distinct_weapon_field_basename_only": len(distinct_partial),
        "distinct_weapon_field_missing": len(distinct_missing),
        "archive_ambiguity_count": len(ambiguous),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "path_aware_rez_index_summary.json"),
              "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # --- write runtime_path_binding.json ---------------------------------
    binding_payload = {
        "status": status,
        "runtime_source": "rez/Butes/bf005.ltc (decoded via N02-B-R1 pipeline)",
        "rez_index_scope": {
            "rez_count_indexed": len(rez_paths),
            "total_entries": idx["total_entries"],
            "unique_full_paths": idx["total_unique_full_paths"],
            "unique_basenames": idx["total_unique_basenames"],
            "elapsed_seconds": round(elapsed, 2),
        },
        "normalisation_rule": summary["normalisation_rule"],
        "summary": {
            "binding_count": len(classified),
            "unique_weapon_field_pairs": total_unique_pairs,
            "verdict_counts": dict(by_verdict),
            "distinct_weapon_field_full_path_bound": len(distinct_full),
            "distinct_weapon_field_basename_only": len(distinct_partial),
            "distinct_weapon_field_missing": len(distinct_missing),
        },
        "archive_ambiguity": ambiguous,
        "per_weapon_field_verdict": [
            {"WeaponName": w, "field": f, "verdict": v}
            for (w, f), v in sorted(per_wf.items())
        ],
        "bindings": classified,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "runtime_path_binding.json"),
              "w", encoding="utf-8") as f:
        json.dump(binding_payload, f, indent=2, ensure_ascii=False)

    # --- write path_binding_report.md ------------------------------------
    _write_report(classified, summary, per_wf, ambiguous, status, idx)
    print(f"[n02d-r1] status = {status}", file=sys.stderr)
    print(f"[n02d-r1] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_report(classified, summary, per_wf, ambiguous, status, idx):
    out = os.path.join(OUT_DIR, "path_binding_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-D-R1 — Path-Aware REZ Runtime Binding Revalidation")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02d_r1_path_aware_rez_binding.py`")
    lines.append(f"- runtime source: `rez/Butes/bf005.ltc` (decoded via N02-B-R1 pipeline)")
    lines.append("")

    # --- 1. Scope & rule ------------------------------------------------
    lines.append("## 1. Scope & path-normalisation rule")
    lines.append("")
    lines.append("This is a rework of N02-D per plan.md §4.10.  The previous")
    lines.append("N02-D built a basename-only index and could not distinguish")
    lines.append("e.g. `Models/PlayerView/PV-M4A1.LTB` from")
    lines.append("`ModelTextures/PlayerView/PV-M4A1.DTX`.  This rework")
    lines.append("preserves the full REZ directory hierarchy and binds the")
    lines.append("bf005 runtime path to an **archive-relative logical path**")
    lines.append("by exact match.")
    lines.append("")
    lines.append("Normalisation rules (in order):")
    lines.append("")
    lines.append("1. backslash -> forward slash")
    lines.append("2. strip a **single** leading virtual root if it is one of:")
    lines.append("   - `Models/` — LithTech engine `Models` virtual root")
    lines.append("   - `ModelTextures/` — LithTech engine `ModelTextures` virtual root")
    lines.append("   Both are confirmed absent as top-level REZ directories in")
    lines.append("   the RF016 / RF017 / rf002 inventory.")
    lines.append("3. `RS/` is **kept** (it is a literal REZ subdir in rf002.rez).")
    lines.append("4. uppercase for REZ-side comparison (REZ entries are upper-case).")
    lines.append("5. extensionless `ModelFileName` / `PViewModelFileName` ->")
    lines.append("   only `.LTB` is attempted as suffix.  No `.dtx/.tga/.lto/")
    lines.append(".ltc/.rez/.dat` fallback (forbidden per task.md §4.3).")
    lines.append("")
    lines.append("Multi-archive hits are reported explicitly; no archive is")
    lines.append("declared authoritative without explicit load-order evidence.")
    lines.append("")

    # --- 2. Index scope -------------------------------------------------
    scope = summary["rez_index_scope"]
    lines.append("## 2. REZ index scope")
    lines.append("")
    lines.append(f"- REZ directories: `{scope['rez_dirs']}`")
    lines.append(f"- REZ files indexed: **{scope['rez_count_indexed']}**")
    lines.append(f"- total file entries: **{scope['total_entries']:,}**")
    lines.append(f"- unique full paths: **{scope['unique_full_paths']:,}**")
    lines.append(f"- unique basenames: **{scope['unique_basenames']:,}**")
    lines.append(f"- index build time: {scope['elapsed_seconds']:.1f}s")
    lines.append("")

    # --- 3. Verdict counts ---------------------------------------------
    lines.append("## 3. Verdict counts")
    lines.append("")
    lines.append("| verdict | count | meaning |")
    lines.append("|---|---|---|")
    verdict_meaning = {
        "EXACT_PATH_BINDING": "single full-path match after normalisation",
        "EXACT_PATH_MULTIPLE_ARCHIVES": "full path exists in >=2 distinct REZ",
        "EXTENSIONLESS_LTB_RESOLVED":
            "extensionless model value -> .LTB single full-path match",
        "EXTENSIONLESS_LTB_MULTIPLE_ARCHIVES":
            "extensionless model value -> .LTB in >=2 distinct REZ",
        "BASENAME_CANDIDATE_ONLY":
            "basename exists but full path does not",
        "NOT_FOUND_IN_SCOPED_RUNTIME":
            "neither full path nor basename found",
    }
    for verdict, count in sorted(summary["verdict_counts"].items(),
                                 key=lambda kv: -kv[1]):
        meaning = verdict_meaning.get(verdict, "—")
        lines.append(f"| `{verdict}` | {count} | {meaning} |")
    lines.append("")

    # --- 4. Distinct (Weapon, field) coverage -------------------------
    s = summary
    lines.append("## 4. Distinct (WeaponName, field) coverage")
    lines.append("")
    lines.append(f"- total unique (WeaponName, field) pairs: "
                 f"**{s['binding_unique_weapon_field_pairs']}**")
    lines.append(f"- full-path bound (after virtual-root strip): "
                 f"**{s['distinct_weapon_field_full_path_bound']}**")
    lines.append(f"- basename-only (not full-path): "
                 f"**{s['distinct_weapon_field_basename_only']}**")
    lines.append(f"- missing entirely: "
                 f"**{s['distinct_weapon_field_missing']}**")
    lines.append(f"- archive-ambiguity cases: "
                 f"**{s['archive_ambiguity_count']}**")
    lines.append("")

    # --- 5. Per-binding table -----------------------------------------
    lines.append("## 5. Per-binding path-aware lookup")
    lines.append("")
    lines.append("| WeaponName | field | runtime_path | normalised | verdict | archive_count |")
    lines.append("|---|---|---|---|---|---|")
    for c in classified:
        n = c["normalisation"]["upper"]
        v = c["verdict"]
        ac = c["archive_count"]
        lines.append(
            f"| `{c['WeaponName']}` | `{c['field']}` | "
            f"`{c['runtime_path']}` | `{n}` | {v} | {ac} |"
        )
    lines.append("")

    # --- 6. Archive ambiguity -----------------------------------------
    lines.append("## 6. Archive ambiguity (same full path in multiple REZ)")
    lines.append("")
    if not ambiguous:
        lines.append("- none — every full-path-bound hit was in a single REZ.")
    else:
        lines.append("| WeaponName | field | runtime_path | normalised | distinct REZ |")
        lines.append("|---|---|---|---|---|")
        for a in ambiguous:
            rez_basenames = sorted({os.path.basename(p) for p in a["rez_paths"]})
            lines.append(
                f"| `{a['WeaponName']}` | `{a['field']}` | "
                f"`{a['runtime_path']}` | `{a['normalised']}` | "
                f"{', '.join(rez_basenames)} |"
            )
    lines.append("")

    # --- 7. Per-(Weapon, field) verdict rollup ------------------------
    lines.append("## 7. Per-(WeaponName, field) verdict rollup")
    lines.append("")
    lines.append("| WeaponName | field | best verdict |")
    lines.append("|---|---|---|")
    for (wn, fk), verdict in sorted(per_wf.items()):
        lines.append(f"| `{wn}` | `{fk}` | {verdict} |")
    lines.append("")

    # --- 8. Status & next investigation --------------------------------
    lines.append("## 8. Status & next investigation")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    if status == "M4A1_RUNTIME_PATH_BINDING_CONFIRMED":
        lines.append("- every M4A1 binding path used in N02-C resolves to a")
        lines.append("  full archive-relative logical path in the current CF")
        lines.append("  runtime REZ set after the documented virtual-root strip.")
        lines.append("- The next single highest-value consumer is **bounded")
        lines.append("  payload SHA collection** for the matching entry: read")
        lines.append("  just the bytes at `data_offset` for `size` bytes,")
        lines.append("  hash them, and compare to any P4 / N01 extracted")
        lines.append("  artifact. The full file is not needed.")
    elif status == "M4A1_RUNTIME_PATH_BINDING_PARTIAL":
        lines.append("- some M4A1 binding paths resolve to full archive-")
        lines.append("  relative logical paths, others do not.  See section 5")
        lines.append("  for the per-binding list and section 4 for distinct")
        lines.append("  (WeaponName, field) coverage.")
    else:
        lines.append("- basename-only hits could not be promoted to full-")
        lines.append("  path matches.  This is a bounded negative; the")
        lines.append("  previous N02-D conclusion that the binding was")
        lines.append("  'direct runtime artifact' cannot be retained without")
        lines.append("  this rework passing.")
    lines.append("")

    # --- 9. Scope guard -----------------------------------------------
    lines.append("## 9. Scope guard")
    lines.append("")
    lines.append("- did NOT extract any REZ payload bytes")
    lines.append("- did NOT decompile or strings/xref any EXE / DLL")
    lines.append("- did NOT reverse any FXO shader")
    lines.append("- did NOT run any CF client / runtime binary")
    lines.append("- did NOT modify `plan.md`")
    lines.append("- did NOT re-do LTC format reverse")
    lines.append("- did NOT explain or reverse LZX")
    lines.append("- did NOT treat basename similarity as path binding proof")
    lines.append("- did NOT announce P4-M01 PASS; did NOT enter P5 identity")
    lines.append("  confirmation")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
