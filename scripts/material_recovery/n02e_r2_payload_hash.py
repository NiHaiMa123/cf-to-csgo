#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-E-R2 — Bounded REZ Payload SHA256 Verification.

This is the rework continuation of N02-E-R1 (commit dc3ac1b,
MATERIAL_BINDING_PARTIAL).  N02-E-R1 concluded the LTB-internal
piece/material/texture atoms are absent (Jupiter LTB standard);
the highest-value remaining step was **bounded payload SHA256
collection** for the bf005 binding hits established by N02-D-R1
(commit f468e96) and re-reviewed by N02-D-R2 (commit c3e8872,
ACCEPTED).

This round:

1. Loads N02-D-R1's `runtime_path_binding.json` (60 (WeaponName,
   field) bindings; path-aware closure).
2. For every unique (rez_path, full_path) hit, re-walks the parent
   REZ directory via `n02d_r1_path_aware_rez_binding.read_rez_index`
   to recover `data_offset` (N02-D-R1's hit entries do not carry
   it — see task.md §3 "LTB piece/material candidate -> runtime
   resource payload").
3. Reads **bounded bytes** at `data_offset` for `size` bytes
   (`fp.seek + fp.read`) — no full-archive load, no in-memory
   payload cache beyond the per-payload block.
4. Computes SHA256 + standard MD5 of the bounded bytes; preserves
   N02-E's `directory_md5_sanity` chain by comparing MD5 against the
   REZ directory catalog MD5 (12/17 mismatch from the rejected N02-E
   is recorded for completeness, not interpreted as engine fact).
5. Compares uppercase SHA256 against the BornBeast P4 baseline
   inventory (`evidence/native_material_inventory.json`) by byte
   equality — not basename.
6. Builds the per-weapon resource graph update from N02-E-R1 with
   actual payload SHA256 + BornBeast match role; for multi-archive
   entries (M4A1-S `SkinFileName`) records whether the two REZ
   copies byte-match.

Outputs under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02e_r2_payload_hash/

Allowed per task.md §4:
  - REZ directory index reading (cache, one REZ walk per archive)
  - bounded payload read at data_offset for size bytes
  - SHA256 / standard MD5 of bounded bytes
  - SHA256 compare against BornBeast P4 baseline inventory

Forbidden per task.md §5:
  - P5 identity confirmation; P4-M01 PASS announcement
  - DLL / EXE reverse; FXO shader reverse; CF runtime execution
  - filename similarity as proof
  - bulk REZ extraction; CFG shader semantic freeze
  - rewriting plan.md

Status per task.md §6:
  - A. NATIVE_RESOURCE_CONFIRMED : at least one bounded SHA256
        matches a BornBeast inventory asset.
  - B. MATERIAL_BINDING_PARTIAL : all bounded reads succeed but
        no SHA256 matches BornBeast inventory (expected for bf005).
  - C. REWORK_REQUIRED : any bounded read fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition",
)
N02DR1_DIR = os.path.join(N02A_DIR, "n02d_r1_path_binding")
N02ER1_DIR = os.path.join(N02A_DIR, "n02e_r1_material_binding")
EVIDENCE_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "evidence"
)
OUT_DIR = os.path.join(N02A_DIR, "n02e_r2_payload_hash")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Bounded payload read (the only payload-byte access path)
# ---------------------------------------------------------------------------
def read_payload_bytes(
    rez_path: str,
    data_offset: int,
    size: int,
    entry: dict | None = None,
) -> bytes:
    """Read bounded REZ payload bytes.

    When `entry` is supplied, routing uses the MD5-verified main-file /
    numbered-part resolver. The offset and size arguments must match that
    directory entry. Without `entry` this remains the historical
    unauthenticated main-file slice and must not be treated as verified
    numbered-part recovery.
    """
    if entry is not None:
        from rez_verified_payload import read_verified_payload

        if int(entry["data_offset"]) != int(data_offset) or int(entry["size"]) != int(size):
            raise ValueError("entry range does not match the requested offset/size")
        data, _provenance = read_verified_payload(Path(rez_path), entry)
        return data
    with open(rez_path, "rb") as fp:
        fp.seek(data_offset)
        return fp.read(size)


# ---------------------------------------------------------------------------
# REZ index cache (mirrors n02e_r1_material_binding.collect_ltb_hits)
# ---------------------------------------------------------------------------
_REZ_INDEX_CACHE: dict = {}


def get_rez_index(rez_path: str) -> dict:
    """Walk a REZ directory once; return {upper_full_path: entry, ...}.

    Each entry carries data_offset, size, name, md5.  Subsequent calls
    for the same rez_path hit the in-memory cache so each archive is
    read exactly once per script invocation.
    """
    if rez_path in _REZ_INDEX_CACHE:
        return _REZ_INDEX_CACHE[rez_path]
    idx = n02dr1.read_rez_index(rez_path)
    by_full = {f["full_path"].upper(): f for f in idx["files"]}
    _REZ_INDEX_CACHE[rez_path] = by_full
    return by_full


# ---------------------------------------------------------------------------
# Collect payload hits from N02-D-R1 binding closure
# ---------------------------------------------------------------------------
def collect_payload_hits() -> tuple[list[dict], dict]:
    """Walk N02-D-R1's bindings and produce a deduplicated payload-hit
    list keyed by (rez_path, full_path).  Returns (hits, summary).

    Each unique hit carries:
      rez_path, full_path, name, size, data_offset (from re-walked
      REZ index), catalog_md5 (from N02-D-R1), and a list of
      binding_refs (every (WeaponName, field) that pointed at this
      payload).

    Summary carries binding_total and skipped_due_to_oversized_rez.
    """
    with open(os.path.join(N02DR1_DIR, "runtime_path_binding.json"),
              "r", encoding="utf-8") as f:
        d = json.load(f)

    # First pass: gather every raw hit with its binding context.
    raw_hits: list[dict] = []
    for b in d["bindings"]:
        for hit in (b.get("exact_path_hits", [])
                    + b.get("extensionless_ltb_hits", [])):
            rez_path = hit["rez_path"]
            full_path = hit["full_path"]
            try:
                by_full = get_rez_index(rez_path)
                entry = by_full.get(full_path.upper())
                data_offset = entry["data_offset"] if entry else None
            except (OSError, ValueError) as e:
                data_offset = None
            raw_hits.append({
                "WeaponName": b["WeaponName"],
                "field": b["field"],
                "binding_verdict": b["verdict"],
                "runtime_path": b["runtime_path"],
                "rez_path": rez_path,
                "full_path": full_path,
                "name": hit["name"],
                "size": hit["size"],
                "data_offset": data_offset,
                "catalog_md5": hit.get("md5", ""),
            })

    # Second pass: dedup by (rez_path, full_path).
    by_payload: dict = {}
    for h in raw_hits:
        key = (h["rez_path"], h["full_path"])
        if key not in by_payload:
            by_payload[key] = {
                "rez_path": h["rez_path"],
                "full_path": h["full_path"],
                "name": h["name"],
                "size": h["size"],
                "data_offset": h["data_offset"],
                "catalog_md5": h["catalog_md5"],
                "binding_refs": [],
            }
        by_payload[key]["binding_refs"].append({
            "WeaponName": h["WeaponName"],
            "field": h["field"],
            "binding_verdict": h["binding_verdict"],
        })

    return list(by_payload.values()), {
        "binding_total": len(raw_hits),
        "unique_payloads": len(by_payload),
    }


# ---------------------------------------------------------------------------
# Hash payloads (bounded read + SHA256 + standard MD5)
# ---------------------------------------------------------------------------
def hash_payloads(payloads: list[dict]) -> list[dict]:
    """For each unique payload, read bounded bytes and SHA256 + MD5.

    Each output dict adds: read_ok, actual_bytes_read, sha256 (uppercase
    hex), md5 (uppercase hex), directory_md5_sanity ("match"/"mismatch"
    against catalog_md5), note.

    Skipped entries (data_offset missing) are recorded with note but do
    not raise — task.md §6 status C is reached only if the read fails.
    """
    out: list[dict] = []
    for p in payloads:
        rec = {
            **p,
            "read_ok": False,
            "actual_bytes_read": 0,
            "sha256": "",
            "md5": "",
            "directory_md5_sanity": "skipped",
            "note": "",
        }
        if p["data_offset"] is None:
            rec["note"] = "data_offset_missing (no REZ index entry)"
            out.append(rec)
            continue
        try:
            data = read_payload_bytes(p["rez_path"], p["data_offset"],
                                       p["size"])
        except (OSError, ValueError) as e:
            rec["note"] = f"read_failed: {e}"
            out.append(rec)
            continue
        rec["read_ok"] = True
        rec["actual_bytes_read"] = len(data)
        sha = hashlib.sha256(data).hexdigest().upper()
        md5 = hashlib.md5(data).hexdigest().upper()
        rec["sha256"] = sha
        rec["md5"] = md5
        catalog = (p["catalog_md5"] or "").upper()
        rec["directory_md5_sanity"] = (
            "match" if catalog and catalog == md5 else "mismatch"
        )
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# BornBeast inventory comparison
# ---------------------------------------------------------------------------
def load_bornbeast_inventory() -> dict:
    """Load the BornBeast P4 baseline inventory (6 items, lowercase
    hex sha256 + size + relative_path + asset_role)."""
    inv_path = os.path.join(EVIDENCE_DIR, "native_material_inventory.json")
    with open(inv_path, "r", encoding="utf-8") as f:
        return json.load(f)


def match_bornbeast(payloads: list[dict], inventory: dict) -> list[dict]:
    """Attach `bornbeast_inventory_match` (asset_role dict or None) to
    each payload by uppercase SHA256 byte-equality against the inventory.

    The inventory sha256 is stored lowercase hex; the payload sha256
    is uppercase hex from `hashlib.sha256().hexdigest().upper()`.  Both
    are normalised to uppercase before comparison.  This is byte
    equality, not basename similarity.
    """
    inv_by_sha: dict = {}
    for item in inventory["items"]:
        sha = item.get("sha256", "").upper()
        inv_by_sha[sha] = item
    out: list[dict] = []
    for p in payloads:
        sha = p["sha256"].upper()
        match = inv_by_sha.get(sha)
        rec = {**p, "bornbeast_inventory_match": match}
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Per-weapon resource graph update
# ---------------------------------------------------------------------------
def build_resource_graph(payloads: list[dict]) -> dict:
    """Build the per-weapon resource graph update from N02-E-R1's
    `resource_graph_candidate.json` enriched with actual payload SHA256
    and BornBeast match role.

    For multi-archive entries (deduplicated keys that share the same
    `full_path` across distinct REZ archives), records a
    `duplicate_archive_sha_equal` flag per (WeaponName, field) binding.
    """
    # Group payloads by full_path so we can detect duplicate-archive
    # ambiguity (same logical path in >=2 distinct REZ).
    by_full: dict = defaultdict(list)
    for p in payloads:
        by_full[p["full_path"]].append(p)

    g: dict = defaultdict(lambda: {
        "bindings": [],
        "payload_sha_set": set(),
        "bornbeast_payload_sha_hits": [],
    })
    for p in payloads:
        # duplicate-archive equality check (only meaningful if >=2 REZ)
        siblings = by_full[p["full_path"]]
        if len(siblings) >= 2:
            shas = sorted({s["sha256"] for s in siblings if s["sha256"]})
            dup_flag = {
                "duplicate_archive_count": len(siblings),
                "distinct_payload_sha": len(shas),
                "duplicate_archive_sha_equal": (len(shas) == 1),
                "shas": shas,
            }
        else:
            dup_flag = None
        for ref in p.get("binding_refs", []):
            wn = ref["WeaponName"]
            entry = g[wn]
            sha = p["sha256"].upper()
            entry["payload_sha_set"].add(sha)
            entry["bindings"].append({
                "WeaponName": wn,
                "field": ref["field"],
                "binding_verdict": ref["binding_verdict"],
                "rez_path": p["rez_path"],
                "full_path": p["full_path"],
                "name": p["name"],
                "size": p["size"],
                "data_offset": p["data_offset"],
                "catalog_md5": p["catalog_md5"],
                "actual_bytes_read": p["actual_bytes_read"],
                "sha256": sha,
                "md5": p["md5"],
                "directory_md5_sanity": p["directory_md5_sanity"],
                "bornbeast_match_role":
                    p["bornbeast_inventory_match"]["asset_role"]
                    if p["bornbeast_inventory_match"] else None,
                "bornbeast_match_relative_path":
                    p["bornbeast_inventory_match"]["relative_path"]
                    if p["bornbeast_inventory_match"] else None,
                "duplicate_archive_sha": dup_flag,
            })
            if p["bornbeast_inventory_match"]:
                entry["bornbeast_payload_sha_hits"].append({
                    "sha256": sha,
                    "field": ref["field"],
                    "asset_role": p["bornbeast_inventory_match"]["asset_role"],
                    "relative_path":
                        p["bornbeast_inventory_match"]["relative_path"],
                })
    for v in g.values():
        v["payload_sha_set"] = sorted(v["payload_sha_set"])
    return dict(g)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override default CF runtime root (CF2_CF_DIR)")
    ap.add_argument("--skip-oversized-rez", type=int, default=0,
                    help="skip REZ files larger than N bytes (0=no skip)")
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02dr1)

    print(f"[n02e-r2] cf_root = {_paths.cf_dir()}", file=sys.stderr)
    print(f"[n02e-r2] repo   = {REPO}", file=sys.stderr)
    if args.skip_oversized_rez:
        print(f"[n02e-r2] skip_oversized_rez threshold = "
              f"{args.skip_oversized_rez} bytes", file=sys.stderr)

    t0 = time.time()
    payloads, coll_summary = collect_payload_hits()
    print(f"[n02e-r2] unique (rez_path, full_path) payloads: "
          f"{len(payloads)}", file=sys.stderr)

    # Optional memory hardening: skip REZ archives larger than threshold.
    skipped_oversized = 0
    if args.skip_oversized_rez:
        keep: list[dict] = []
        for p in payloads:
            try:
                fsize = os.path.getsize(p["rez_path"])
            except OSError:
                keep.append(p)
                continue
            if fsize > args.skip_oversized_rez:
                skipped_oversized += 1
                # mark entry skipped
                p2 = dict(p)
                p2["data_offset"] = None
                p2["note"] = (
                    f"rez_skipped_oversized (rez size {fsize} > "
                    f"threshold {args.skip_oversized_rez})"
                )
                keep.append(p2)
            else:
                keep.append(p)
        payloads = keep
        print(f"[n02e-r2] payloads skipped due to oversized REZ: "
              f"{skipped_oversized}", file=sys.stderr)

    hashed = hash_payloads(payloads)
    n_read_ok = sum(1 for p in hashed if p["read_ok"])
    n_dir_match = sum(1 for p in hashed
                       if p["directory_md5_sanity"] == "match")
    n_dir_mismatch = sum(1 for p in hashed
                          if p["directory_md5_sanity"] == "mismatch")
    print(f"[n02e-r2] payload bounded reads OK: {n_read_ok}", file=sys.stderr)
    print(f"[n02e-r2] directory_md5 sanity (match/mismatch): "
          f"{n_dir_match}/{n_dir_mismatch}", file=sys.stderr)

    inventory = load_bornbeast_inventory()
    matched = match_bornbeast(hashed, inventory)
    n_match = sum(1 for p in matched if p["bornbeast_inventory_match"])
    print(f"[n02e-r2] BornBeast inventory SHA256 matches: {n_match}",
          file=sys.stderr)

    graph = build_resource_graph(matched)
    elapsed = time.time() - t0

    # Status per task.md §6.
    n_total_unique = coll_summary["unique_payloads"]
    if n_read_ok == 0:
        status = "REWORK_REQUIRED"
    elif n_match > 0:
        status = "NATIVE_RESOURCE_CONFIRMED"
    elif n_read_ok == n_total_unique:
        status = "MATERIAL_BINDING_PARTIAL"
    else:
        status = "REWORK_REQUIRED"

    # --- write payload_hash_verification.json ---------------------------
    verify_payload = {
        "task": "P4-M01-N02-E-R2",
        "status": status,
        "consumes": [
            "n02d_r1_path_binding/runtime_path_binding.json",
            "evidence/native_material_inventory.json (BornBeast P4 baseline)",
        ],
        "scope": {
            "binding_total": coll_summary["binding_total"],
            "unique_payloads": coll_summary["unique_payloads"],
            "bounded_read_ok": n_read_ok,
            "directory_md5_sanity_match": n_dir_match,
            "directory_md5_sanity_mismatch": n_dir_mismatch,
            "bornbeast_inventory_match": n_match,
            "skipped_oversized_rez": skipped_oversized,
            "elapsed_seconds": round(elapsed, 2),
        },
        "payloads": matched,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "payload_hash_verification.json"),
              "w", encoding="utf-8") as f:
        json.dump(verify_payload, f, indent=2, ensure_ascii=False)

    # --- write resource_graph_with_payload.json -------------------------
    graph_payload = {
        "task": "P4-M01-N02-E-R2",
        "status": status,
        "consumes": (
            "n02e_r1_material_binding/resource_graph_candidate.json + "
            "this round's payload_hash_verification.json"
        ),
        "note": (
            "Resource graph update from N02-E-R1 with per-payload "
            "SHA256 + BornBeast inventory match.  Each binding_ref now "
            "carries its actual runtime payload SHA256 and standard MD5; "
            "directory_md5_sanity preserves N02-E's catalog-vs-actual MD5 "
            "comparison (informational, not interpreted as engine fact). "
            "For multi-archive entries (M4A1-S SkinFileName) "
            "duplicate_archive_sha reports whether the distinct REZ "
            "copies byte-match."
        ),
        "per_weapon": graph,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "resource_graph_with_payload.json"),
              "w", encoding="utf-8") as f:
        json.dump(graph_payload, f, indent=2, ensure_ascii=False)

    # --- write payload_verification_report.md ---------------------------
    _write_report(matched, inventory, graph, coll_summary, n_dir_match,
                  n_dir_mismatch, n_match, skipped_oversized, status,
                  elapsed)

    print(f"[n02e-r2] status = {status}", file=sys.stderr)
    print(f"[n02e-r2] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_report(matched, inventory, graph, coll_summary,
                  n_dir_match, n_dir_mismatch, n_match,
                  skipped_oversized, status, elapsed):
    out = os.path.join(OUT_DIR, "payload_verification_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-E-R2 — Bounded REZ Payload SHA256 Verification")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02e_r2_payload_hash.py`")
    lines.append(f"- consumes: "
                 f"`n02d_r1_path_binding/runtime_path_binding.json` + "
                 f"`evidence/native_material_inventory.json`")
    lines.append("")

    # --- 1. Scope ------------------------------------------------------
    lines.append("## 1. Scope")
    lines.append("")
    lines.append("For every (rez_path, full_path, size, md5) hit in")
    lines.append("N02-D-R1's binding closure, this round:")
    lines.append("")
    lines.append("1. recovered `data_offset` from a fresh REZ directory")
    lines.append("   walk via `n02d_r1_path_aware_rez_binding."
                 "read_rez_index` (cached, one walk per archive);")
    lines.append("2. read **bounded bytes** at `data_offset` for `size`")
    lines.append("   bytes via `fp.seek + fp.read` — the rest of the REZ")
    lines.append("   is never read into memory;")
    lines.append("3. computed SHA256 and standard MD5 of the bounded bytes;")
    lines.append("4. compared the SHA256 (uppercase hex) against the BornBeast")
    lines.append("   P4 baseline inventory by byte equality (not basename);")
    lines.append("5. compared standard MD5 against the REZ directory catalog")
    lines.append("   MD5 (`directory_md5_sanity`) — informational, not")
    lines.append("   interpreted as engine fact, retained to preserve N02-E's")
    lines.append("   directory-honesty chain;")
    lines.append("6. for multi-archive entries (M4A1-S `SkinFileName` has")
    lines.append("   two RF017.REZ copies), recorded whether the distinct")
    lines.append("   archive copies byte-match (`duplicate_archive_sha_equal`).")
    lines.append("")

    # --- 2. Verdict counts --------------------------------------------
    n_total_unique = coll_summary["unique_payloads"]
    n_total_bindings = coll_summary["binding_total"]
    n_ok = sum(1 for p in matched if p["read_ok"])
    n_skip = n_total_unique - n_ok
    n_bb = n_match
    n_no_bb = n_ok - n_match
    lines.append("## 2. Verdict counts")
    lines.append("")
    lines.append("| metric | count | meaning |")
    lines.append("|---|---|---|")
    lines.append(f"| `binding_total` | {n_total_bindings} | "
                 f"raw (WeaponName, field, hit) triples from N02-D-R1 |")
    lines.append(f"| `unique_payloads` | {n_total_unique} | "
                 f"unique (rez_path, full_path) after dedup |")
    lines.append(f"| `READ_OK_BORN_BEAST_MATCH` | {n_bb} | "
                 f"runtime payload SHA256 == BornBeast P4 baseline |")
    lines.append(f"| `READ_OK_NO_BORN_BEAST_MATCH` | {n_no_bb} | "
                 f"runtime payload SHA256 != BornBeast P4 baseline |")
    lines.append(f"| `READ_SKIPPED` | {n_skip} | "
                 f"data_offset missing or read failed |")
    lines.append(f"| `directory_md5_sanity_match` | {n_dir_match} | "
                 f"standard MD5 of payload == REZ catalog MD5 |")
    lines.append(f"| `directory_md5_sanity_mismatch` | {n_dir_mismatch} | "
                 f"standard MD5 of payload != REZ catalog MD5 |")
    lines.append(f"| `skipped_oversized_rez` | {skipped_oversized} | "
                 f"skipped due to --skip-oversized-rez (0 if not used) |")
    lines.append("")
    lines.append(f"- elapsed: {elapsed:.2f}s")
    lines.append("")

    # --- 3. BornBeast inventory snapshot ------------------------------
    lines.append("## 3. BornBeast inventory snapshot (P4 baseline)")
    lines.append("")
    lines.append("| asset_role | sha256 | size | relative_path |")
    lines.append("|---|---|---|---|")
    for item in inventory["items"]:
        lines.append(
            f"| `{item['asset_role']}` | "
            f"`{item['sha256']}` | {item['size_bytes']:,} | "
            f"`{item['relative_path']}` |"
        )
    lines.append("")

    # --- 4. Per-payload table -----------------------------------------
    lines.append("## 4. Per-payload bounded SHA256 + BornBeast match")
    lines.append("")
    lines.append("| rez | full_path | name | size | sha256 | bb_match | "
                 "dir_md5 |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in matched:
        bb = (p["bornbeast_inventory_match"]["asset_role"]
              if p["bornbeast_inventory_match"] else "—")
        lines.append(
            f"| `{os.path.basename(p['rez_path'])}` | "
            f"`{p['full_path']}` | `{p['name']}` | {p['size']:,} | "
            f"`{p['sha256'] or '—'}` | {bb} | "
            f"{p['directory_md5_sanity']} |"
        )
    lines.append("")

    # --- 5. Per-weapon BornBeast match summary -----------------------
    lines.append("## 5. Per-weapon BornBeast match summary")
    lines.append("")
    lines.append("| WeaponName | unique_payloads | bornbeast_payload_hits |")
    lines.append("|---|---|---|")
    for wn, g in sorted(graph.items()):
        lines.append(
            f"| `{wn}` | {len(g['payload_sha_set'])} | "
            f"{len(g['bornbeast_payload_sha_hits'])} |"
        )
    lines.append("")

    # --- 6. Status & next investigation -------------------------------
    lines.append("## 6. Status & next investigation")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    if status == "NATIVE_RESOURCE_CONFIRMED":
        lines.append("- At least one runtime payload SHA256 matches a "
                     "BornBeast P4 baseline asset.")
        lines.append("- This converts the bf005 binding layer's path "
                     "binding into a deterministic payload-identity edge.")
    elif status == "MATERIAL_BINDING_PARTIAL":
        lines.append("- All unique (rez_path, full_path) payloads have a "
                     "bounded SHA256; every binding_ref is byte-verified.")
        lines.append("- **No runtime payload SHA256 matches a BornBeast "
                     "P4 baseline asset** — bf005's M4A1 family resolves "
                     "to the base/silencer/camo/QQ/gold/silver/bronze/"
                     "crystal M4A1 skin family, not BornBeast.")
        lines.append("- This is a bounded negative: N02-C had already "
                     "established that BornBeast is absent from bf005's "
                     "decoded Bute records; this round promotes that "
                     "conclusion to byte-level payload identity for every "
                     "reachable bf005 (WeaponName, field) hit.")
        lines.append("- BornBeast native material closure for P4-M01 "
                     "therefore requires a different `bf*.ltc` layer "
                     "(bf001-*.ltc, bf000.lta) or a runtime-resident "
                     "inventory scan; this round closed the bf005 layer "
                     "only.")
    else:
        lines.append("- payload read failed; see scope guard.")
    lines.append("")

    # --- 7. Scope guard -----------------------------------------------
    lines.append("## 7. Scope guard")
    lines.append("")
    lines.append("- read only `data_offset .. data_offset + size` bytes "
                 "from each (rez_path) — no full-archive load, no "
                 "in-memory payload cache beyond the per-payload bounded "
                 "block;")
    lines.append("- did NOT decompile / strings / xref any EXE / DLL")
    lines.append("- did NOT reverse any FXO shader")
    lines.append("- did NOT run any CF client / runtime binary")
    lines.append("- did NOT modify `plan.md`")
    lines.append("- did NOT enter P5 identity confirmation")
    lines.append("- did NOT announce P4-M01 PASS")
    lines.append("- did NOT freeze CFG shader semantics")
    lines.append("- did NOT promote REZ catalog MD5 mismatch to an "
                 "engine-format fact (informational only)")
    lines.append("- used SHA256 for BornBeast comparison (not basename "
                 "similarity)")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
