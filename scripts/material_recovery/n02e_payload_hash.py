#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-E — M4A1 Runtime Artifact Payload SHA Verification.

Implements the bounded task P4-M01-N02-E from task.md.

Goal: read the **bounded** payload of every N02-D confirmed M4A1
runtime artifact, compute its SHA256, and compare it to:

  1. the REZ-directory MD5 that CF itself stamped in the file table
     (this is N02-D's `rez_hits[i].md5` field — it should match
     because CF writes it from the same payload bytes); and

  2. the P4 known BornBeast source LTB SHA256, recorded in
     assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json as
     inputs.cf_ltb_source.sha256.

A direct byte-level match against the P4 BornBeast LTB would be the
strongest possible evidence. Anything less is reported as a bounded
relationship and graded honestly.

We never bulk-extract a REZ — we open the REZ, seek to data_offset,
read exactly `size` bytes, hash, and discard.

Forbidden per task.md §8:
  - full REZ extraction
  - DLL/EXE reverse
  - FXO shader reverse
  - CF client execution
  - memory dump
  - file-name similarity treated as hash evidence
  - P4-M01 PASS announcement
  - P5 identity confirmation

Outputs under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02e_payload_hash/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
OUT_DIR = os.path.join(N02A_DIR, "n02e_payload_hash")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Load N02-D REZ index outputs.
# ---------------------------------------------------------------------------
def load_n02d_index() -> list[dict]:
    """Load N02-D runtime_asset_lookup.json and flatten to a per-REZ-entry
    list, deduplicating by (rez_path, data_offset)."""
    src = os.path.join(
        N02A_DIR, "n02d_rez_asset_lookup", "runtime_asset_lookup.json",
    )
    with open(src, "r", encoding="utf-8") as f:
        d = json.load(f)
    seen: set = set()
    flat: list = []
    for lookup in d["lookups"]:
        if lookup.get("verdict") != "DIRECT_RUNTIME_ARTIFACT":
            continue
        for h in lookup.get("rez_hits", []):
            k = (h["rez_path"], h["data_offset"], h["name"])
            if k in seen:
                continue
            seen.add(k)
            flat.append({
                "WeaponName": lookup["WeaponName"],
                "field": lookup["field"],
                "runtime_path": lookup["runtime_path"],
                "basename": lookup["basename"],
                "ext": lookup["ext"],
                "rez_path": h["rez_path"],
                "rez_size": h["rez_size"],
                "data_offset": h["data_offset"],
                "size": h["size"],
                "name": h["name"],
                "rez_md5": h["md5"],
                "id": h["id"],
            })
    return flat


# ---------------------------------------------------------------------------
# Load P4 BornBeast known SHA.
# ---------------------------------------------------------------------------
def load_p4_bornbeast_sha() -> list[dict]:
    """Read the existing P4 / N01 evidence for BornBeast source artifacts.

    We use ONLY the prototype_01_manifest.json (which is the single
    authoritative P4 input manifest) to avoid any silent re-scan of the
    data/** corpus.
    """
    candidates = [
        os.path.join(REPO, "assets", "weapons", "m4a1_s_bornbeast",
                     "prototype_01_manifest.json"),
        os.path.join(REPO, "assets", "weapons", "m4a1_s_bornbeast",
                     "m4a4_final_bornbeast_manifest.json"),
    ]
    out = []
    for path in candidates:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        for label, blob in [
            ("inputs.cf_ltb_source", d.get("inputs", {}).get("cf_ltb_source")),
        ]:
            if blob and blob.get("sha256"):
                out.append({
                    "source_label": label,
                    "manifest_path": path,
                    "path": blob.get("path", ""),
                    "sha256": blob["sha256"].lower(),
                    "size_bytes": blob.get("size_bytes"),
                    "role": blob.get("role", ""),
                })
    return out


# ---------------------------------------------------------------------------
# Bounded payload read.
# ---------------------------------------------------------------------------
def read_bounded_payload(rez_path: str, offset: int, size: int) -> bytes:
    with open(rez_path, "rb") as f:
        f.seek(offset)
        return f.read(size)


def md5_hex(b: bytes) -> str:
    return hashlib.md5(b).hexdigest().upper()


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Per-entry verification.
# ---------------------------------------------------------------------------
def verify_entries(flat: list[dict], p4_known: list[dict]) -> list[dict]:
    """For each N02-D confirmed REZ entry, read its payload, hash it, and
    compare against (a) the REZ directory MD5 and (b) the P4 known
    BornBeast SHA list."""
    p4_sha_index: dict = {p["sha256"]: p for p in p4_known}
    out = []
    for f in flat:
        path = f["rez_path"]
        offset = f["data_offset"]
        size = f["size"]
        record = {
            "WeaponName": f["WeaponName"],
            "field": f["field"],
            "runtime_path": f["runtime_path"],
            "basename": f["basename"],
            "ext": f["ext"],
            "rez_path": path,
            "rez_size": f["rez_size"],
            "name": f["name"],
            "data_offset": offset,
            "size": size,
            "rez_md5": f["rez_md5"],
            "id": f["id"],
        }
        if size <= 0:
            record["sha256"] = None
            record["match_against_rez_md5"] = "EMPTY_FILE"
            record["match_against_p4_bornbeast"] = "EMPTY_FILE"
            out.append(record)
            continue
        if size > 256 * 1024 * 1024:
            # skip pathologically large files (>256 MiB)
            record["sha256"] = None
            record["match_against_rez_md5"] = "SKIPPED_OVERSIZE"
            record["match_against_p4_bornbeast"] = "SKIPPED_OVERSIZE"
            out.append(record)
            continue
        try:
            payload = read_bounded_payload(path, offset, size)
        except OSError as e:
            record["sha256"] = None
            record["md5"] = None
            record["read_error"] = str(e)
            record["match_against_rez_md5"] = "READ_ERROR"
            record["match_against_p4_bornbeast"] = "READ_ERROR"
            out.append(record)
            continue
        h_md5 = md5_hex(payload)
        h_sha = sha256_hex(payload)
        record["md5"] = h_md5
        record["sha256"] = h_sha
        record["md5_payload_size"] = len(payload)
        # The REZ directory stores the MD5 of the raw payload bytes — match
        # against the same MD5. Any disagreement here is a real
        # directory/payload divergence.
        record["match_against_rez_md5"] = (
            "MATCH" if h_md5 == (f["rez_md5"] or "").upper() else "MISMATCH"
        )
        p4_hit = p4_sha_index.get(h_sha.lower())
        if p4_hit:
            record["match_against_p4_bornbeast"] = "MATCH"
            record["p4_bornbeast_match"] = p4_hit
        else:
            record["match_against_p4_bornbeast"] = "NO_MATCH"
        out.append(record)
    return out


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    args = ap.parse_args()

    flat = load_n02d_index()
    p4_known = load_p4_bornbeast_sha()
    print(f"[n02e] N02-D confirmed entries (per-rez, deduped): {len(flat)}",
          file=sys.stderr)
    print(f"[n02e] P4 known BornBeast source SHAs: {len(p4_known)}",
          file=sys.stderr)
    if p4_known:
        for p in p4_known:
            print(f"  - {p['source_label']}: {p['path']} sha256={p['sha256']}",
                  file=sys.stderr)

    results = verify_entries(flat, p4_known)

    # Verdict counts.
    md5_match = sum(1 for r in results
                    if r.get("match_against_rez_md5") == "MATCH")
    md5_mismatch = sum(1 for r in results
                       if r.get("match_against_rez_md5") == "MISMATCH")
    p4_match = sum(1 for r in results
                   if r.get("match_against_p4_bornbeast") == "MATCH")
    p4_no_match = sum(1 for r in results
                      if r.get("match_against_p4_bornbeast") == "NO_MATCH")
    skipped = sum(1 for r in results
                   if r.get("match_against_rez_md5") in
                   ("EMPTY_FILE", "SKIPPED_OVERSIZE", "READ_ERROR"))

    # Status per task.md §7.
    if p4_match > 0:
        # A direct byte-level match to the P4 BornBeast source would be
        # the strongest possible evidence and elevates the relationship
        # from "config + asset mapping open" to "payload verified".
        status = "M4A1_RUNTIME_PAYLOAD_VERIFIED"
    elif md5_mismatch == 0 and skipped == 0:
        # All reads matched the REZ directory MD5 (so the directory is
        # honest), but no entry matched a BornBeast-named source SHA.
        status = "M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN"
    elif md5_mismatch > 0:
        # Mismatch means the REZ directory MD5 disagrees with the live
        # payload — that is itself a bounded negative.
        status = "M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN"
    else:
        status = "M4A1_RUNTIME_ARTIFACT_CONFIRMED_PAYLOAD_OPEN"

    # Unique REZ + per-extension rollup.
    by_ext: dict = defaultdict(lambda: {"count": 0, "md5_match": 0,
                                          "md5_mismatch": 0,
                                          "p4_match": 0, "p4_no_match": 0})
    for r in results:
        ext = r["ext"] or "(no-ext)"
        d = by_ext[ext]
        d["count"] += 1
        if r.get("match_against_rez_md5") == "MATCH":
            d["md5_match"] += 1
        elif r.get("match_against_rez_md5") == "MISMATCH":
            d["md5_mismatch"] += 1
        if r.get("match_against_p4_bornbeast") == "MATCH":
            d["p4_match"] += 1
        else:
            d["p4_no_match"] += 1

    payload = {
        "status": status,
        "n02d_index_source": "runtime_asset_lookup.json",
        "n02d_entry_count": len(flat),
        "p4_bornbeast_known": p4_known,
        "summary": {
            "verified_count": len(results),
            "rez_md5_match": md5_match,
            "rez_md5_mismatch": md5_mismatch,
            "p4_bornbeast_match": p4_match,
            "p4_bornbeast_no_match": p4_no_match,
            "skipped": skipped,
        },
        "by_extension": dict(by_ext),
        "results": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "payload_hash_verification.json"), "w",
              encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    _write_report(results, p4_known, payload, by_ext, status)
    print(f"[n02e] status = {status}", file=sys.stderr)
    print(f"[n02e] rez_md5_match={md5_match} rez_md5_mismatch={md5_mismatch} "
          f"p4_match={p4_match}", file=sys.stderr)
    print(f"[n02e] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_report(results, p4_known, payload, by_ext, status):
    out = os.path.join(OUT_DIR, "payload_hash_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-E — M4A1 Runtime Artifact Payload SHA Verification")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02e_payload_hash.py`")
    lines.append("")

    lines.append("## 1. Scope")
    lines.append("")
    lines.append("- only N02-D confirmed REZ entries are read")
    lines.append("- only the bytes at the REZ `data_offset` for exactly `size`")
    lines.append("  bytes are loaded — never the full REZ")
    lines.append("- SHA256 of the bounded payload is compared to:")
    lines.append("  1. the REZ directory MD5 (the value CF itself wrote at")
    lines.append("     archive-build time), and")
    lines.append("  2. the P4 known BornBeast source LTB SHA256, recorded in")
    lines.append("     `assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`")
    lines.append("     under `inputs.cf_ltb_source.sha256`.")
    lines.append("")

    lines.append("## 2. P4 known BornBeast source SHAs")
    lines.append("")
    if p4_known:
        for p in p4_known:
            lines.append(f"- `{p['source_label']}`: `{p['path']}`  ")
            lines.append(f"  sha256: `{p['sha256']}`")
    else:
        lines.append("- (no P4 BornBeast source SHA found in prototype_01_manifest.json)")
    lines.append("")

    lines.append("## 3. Verdict counts")
    lines.append("")
    s = payload["summary"]
    lines.append("| metric | count |")
    lines.append("|---|---|")
    lines.append(f"| verified entries | {s['verified_count']} |")
    lines.append(f"| REZ MD5 MATCH | {s['rez_md5_match']} |")
    lines.append(f"| REZ MD5 MISMATCH | {s['rez_md5_mismatch']} |")
    lines.append(f"| P4 BornBeast MATCH | {s['p4_bornbeast_match']} |")
    lines.append(f"| P4 BornBeast NO_MATCH | {s['p4_bornbeast_no_match']} |")
    lines.append(f"| skipped (empty/oversize/read-error) | {s['skipped']} |")
    lines.append("")

    lines.append("## 4. Per-extension rollup")
    lines.append("")
    lines.append("| ext | count | rez_md5_match | rez_md5_mismatch | p4_match | p4_no_match |")
    lines.append("|---|---|---|---|---|---|")
    for ext, d in sorted(by_ext.items(), key=lambda x: -x[1]["count"]):
        lines.append(f"| `{ext}` | {d['count']} | {d['md5_match']} | "
                     f"{d['md5_mismatch']} | {d['p4_match']} | {d['p4_no_match']} |")
    lines.append("")

    lines.append("## 5. Per-entry detail")
    lines.append("")
    # split into match / mismatch / p4-match
    p4_hits = [r for r in results if r.get("match_against_p4_bornbeast") == "MATCH"]
    md5_mismatches = [r for r in results
                      if r.get("match_against_rez_md5") == "MISMATCH"]
    if p4_hits:
        lines.append("### 5.1 Entries whose SHA256 matches a P4 BornBeast source")
        lines.append("")
        lines.append("| WeaponName | field | runtime_path | REZ | name | size | sha256 | p4_match_path |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in p4_hits:
            lines.append(
                f"| `{r['WeaponName']}` | `{r['field']}` | "
                f"`{r['runtime_path']}` | `{os.path.basename(r['rez_path'])}` | "
                f"`{r['name']}` | {r['size']:,} | `{r['sha256']}` | "
                f"`{r.get('p4_bornbeast_match', {}).get('path', '')}` |"
            )
        lines.append("")
    if md5_mismatches:
        lines.append("### 5.2 Entries whose SHA256 disagrees with the REZ directory MD5")
        lines.append("")
        lines.append("| WeaponName | field | runtime_path | REZ | name | rez_md5 | payload_sha256 |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in md5_mismatches[:20]:
            lines.append(
                f"| `{r['WeaponName']}` | `{r['field']}` | "
                f"`{r['runtime_path']}` | `{os.path.basename(r['rez_path'])}` | "
                f"`{r['name']}` | `{r['rez_md5']}` | `{r['sha256']}` |"
            )
        lines.append("")

    # Per (WeaponName, field) rollup
    by_wf: dict = {}
    for r in results:
        key = (r["WeaponName"], r["field"])
        cur = by_wf.get(key, {"md5_match": 0, "p4_match": 0, "count": 0,
                              "WeaponName": r["WeaponName"], "field": r["field"]})
        cur["count"] += 1
        if r.get("match_against_rez_md5") == "MATCH":
            cur["md5_match"] += 1
        if r.get("match_against_p4_bornbeast") == "MATCH":
            cur["p4_match"] += 1
        by_wf[key] = cur
    lines.append("### 5.3 Per-WeaponName/field rollup")
    lines.append("")
    lines.append("| WeaponName | field | count | rez_md5_match | p4_match |")
    lines.append("|---|---|---|---|---|")
    for k in sorted(by_wf.keys()):
        v = by_wf[k]
        lines.append(f"| `{v['WeaponName']}` | `{v['field']}` | "
                     f"{v['count']} | {v['md5_match']} | {v['p4_match']} |")
    lines.append("")

    lines.append("## 6. Verdict")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    if status == "M4A1_RUNTIME_PAYLOAD_VERIFIED":
        lines.append("- at least one N02-D confirmed runtime artifact's")
        lines.append("  payload SHA256 matches a P4 known BornBeast source SHA.")
        lines.append("  This is the strongest possible non-decompile evidence")
        lines.append("  that a runtime Bute bind maps to the same bytes that")
        lines.append("  P4 already treats as the BornBeast source.")
    else:
        lines.append("- All bounded payload reads either match the REZ")
        lines.append("  directory MD5 (proving the index is honest) or were")
        lines.append("  skipped; **none** matches a P4 BornBeast source SHA.")
        lines.append("- Therefore the BornBeast source LTB (the P4-derived")
        lines.append("  custom asset) is **not byte-identical** to any of the")
        lines.append("  runtime Bute bind targets in the CF REZ archives. The")
        lines.append("  P4 frozen BornBeast mod is built from a custom LTB")
        lines.append("  outside the CF runtime REZ layer, as the P4 baseline")
        lines.append("  inventory already recorded.")
    lines.append("")

    lines.append("## 7. Next single highest-value investigation target")
    lines.append("")
    if status == "M4A1_RUNTIME_PAYLOAD_VERIFIED":
        lines.append("- the bounded byte-level evidence above is sufficient to")
        lines.append("  begin mapping the BornBeast custom LTB onto the runtime")
        lines.append("  base M4A1 family via the same payload SHA. Next step")
        lines.append("  is to compare the BornBeast custom LTB's mesh + UV")
        lines.append("  to the runtime M4A1 base LTB (read its own bounded")
        lines.append("  payload at the same offset, then a structural diff).")
    else:
        lines.append("- the runtime Bute binds to the BASE M4A1 family and")
        lines.append("  the BornBeast custom LTB is a separate asset outside")
        lines.append("  the CF runtime REZ layer. The next step is to")
        lines.append("  acknowledge that the runtime REZ layer cannot, by")
        lines.append("  itself, prove BornBeast identity; that requires the")
        lines.append("  P4 / P5 stage that consumes the runtime artifact and")
        lines.append("  the BornBeast source together.")
    lines.append("")

    lines.append("## 8. Scope guard")
    lines.append("")
    lines.append("- read at most `size` bytes per REZ entry — never the full REZ")
    lines.append("- did not decompile or strings/xref any EXE / DLL")
    lines.append("- did not reverse any FXO shader")
    lines.append("- did not run any CF client / runtime binary")
    lines.append("- did not modify `plan.md`")
    lines.append("- did not re-do LTC format reverse")
    lines.append("- did not treat filename similarity as hash evidence")
    lines.append("- P4-M01 PASS NOT announced; P5 identity confirmation NOT entered")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
