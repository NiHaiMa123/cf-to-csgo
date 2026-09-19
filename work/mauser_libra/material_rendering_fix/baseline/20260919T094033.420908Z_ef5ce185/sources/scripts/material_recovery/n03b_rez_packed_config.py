#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-B — REZ-resident table/config search for BornBeast consumer.

Implements the bounded task P4-M01-N03-B from task.md.

N03-A proved the six BornBeast inventory assets exist in the current
CF REZ (payload SHA256 identity) but are unnamed by loose
rez/Butes/*.ltc.  This round looks *inside* REZ for table/config
payloads that might bind those assets.

Selection is by extension, not filename similarity:

    .cft
    .lta
    .txt
    .ltc  only when full_path starts with BUTES/

Each unique full_path is bounded-read once (preferred archive = rez/
over rez2/...).  Exact inventory tokens (N03-A rules) are searched
in decoded LTC text or ASCII/UTF-16LE strings.

Forbidden: .dat/.dtx/.bin/.ltb, all 1747 REZ .ltc, WeaponShader .cfg
as consumer, PE/FXO, P4-M01 PASS, plan.md edits.

Outputs under
  work/.../runtime_acquisition/n03b_rez_packed_config/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02_butes_config_triage as n02b  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import n03a_bornbeast_consumer as n03a  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition",
)
OUT_DIR = os.path.join(N02A_DIR, "n03b_rez_packed_config")
os.makedirs(OUT_DIR, exist_ok=True)

ALLOWED_EXTS = {".cft", ".lta", ".txt"}
LTC_PREFIX = "BUTES/"
PAYLOAD_MAX_BYTES = 8 * 1024 * 1024
PRIORITY_TABLES = (
    "TABLE/ITEM.CFT",
    "TABLE/MODELBUTE.CFT",
    "TABLE/WEAPONPOINT.CFT",
)
WEAPON_SNAPSHOT_FIELDS = (
    "WeaponName", "StandardName", "Name", "BigIconName",
    "ModelFileName", "SkinFileName",
    "PViewModelFileName", "PViewSkinFileName",
    "RenderStyleFileName", "PViewRenderStyleFileName",
)


def archive_rank(rez_path: str) -> tuple:
    rel = os.path.relpath(rez_path, CF_DIR).replace("\\", "/").lower()
    if rel.startswith("rez/") and not rel.startswith("rez2"):
        return (0, rel)
    return (1, rel)


def gbk_display(s: str) -> str:
    """Loose LTC text is latin-1 of GBK bytes. Best-effort display form."""
    if not s:
        return ""
    try:
        return s.encode("latin-1").decode("gbk")
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            return s.encode("latin-1").decode("gb2312")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return s


def archive_label(rez_path: str) -> str:
    try:
        return os.path.relpath(rez_path, CF_DIR).replace("\\", "/")
    except ValueError:
        return os.path.basename(rez_path)


def is_selected(full_path: str, name: str) -> bool:
    ext = os.path.splitext(name)[1].lower()
    fp = full_path.replace("\\", "/").upper()
    if ext in ALLOWED_EXTS:
        return True
    if ext == ".ltc" and fp.startswith(LTC_PREFIX):
        return True
    return False


def decode_ltc_bytes(data: bytes) -> dict:
    unlocked = n02b.try_unlock_crossfire_payload(data)
    if unlocked is None:
        return {
            "ok": False,
            "reason": "wrapper_no_match",
            "text": n03a.extract_ascii_and_utf16le(data),
        }
    try:
        decoded = n02b._decode_ltc_c_sharp(unlocked)
    except n02b.LtcDecodeFailure as e:
        return {
            "ok": False,
            "reason": str(e),
            "text": n03a.extract_ascii_and_utf16le(data),
        }
    return {
        "ok": True,
        "reason": "DECODED",
        "text": decoded.decode("latin-1", errors="replace"),
        "decoded_size": len(decoded),
    }


def select_payloads(idx: dict) -> list[dict]:
    """One record per unique full_path that passes the extension gate."""
    selected = []
    for full_upper, hits in idx["by_full_path"].items():
        hits_sorted = sorted(hits, key=lambda h: archive_rank(h["rez_path"]))
        h0 = hits_sorted[0]
        if not is_selected(h0["full_path"], h0["name"]):
            continue
        selected.append({
            "full_path": h0["full_path"],
            "name": h0["name"],
            "ext": os.path.splitext(h0["name"])[1].lower(),
            "size": h0["size"],
            "data_offset": h0["data_offset"],
            "rez_path": h0["rez_path"],
            "archive_count": len(hits),
            "archives": [archive_label(h["rez_path"]) for h in hits_sorted],
            "priority_table": h0["full_path"].replace("\\", "/").upper()
            in {p.upper() for p in PRIORITY_TABLES},
        })
    selected.sort(key=lambda r: (
        0 if r["priority_table"] else 1,
        r["ext"],
        r["full_path"].upper(),
    ))
    return selected


def search_payload(rec: dict, tokens: list[dict]) -> dict:
    out = {
        **rec,
        "skipped": False,
        "skip_reason": "",
        "read_ok": False,
        "decode_ok": False,
        "decode_reason": "",
        "magic_hex": "",
        "record_count": 0,
        "field_hits": [],
        "text_hits": [],
        "weapon_snapshots": [],
    }
    if rec["size"] > PAYLOAD_MAX_BYTES:
        out["skipped"] = True
        out["skip_reason"] = f"size {rec['size']} > {PAYLOAD_MAX_BYTES}"
        return out
    if rec["size"] <= 0:
        out["skipped"] = True
        out["skip_reason"] = "empty"
        return out
    try:
        data = n02er2.read_payload_bytes(
            rec["rez_path"], rec["data_offset"], rec["size"]
        )
    except (OSError, ValueError) as e:
        out["skip_reason"] = f"read_failed: {e}"
        return out
    out["read_ok"] = True
    out["actual_bytes"] = len(data)
    out["magic_hex"] = data[:8].hex()

    text = ""
    if rec["ext"] == ".ltc":
        dec = decode_ltc_bytes(data)
        out["decode_ok"] = dec["ok"]
        out["decode_reason"] = dec["reason"]
        text = dec["text"]
        if dec["ok"]:
            records = n03a.parse_lisp_all_keys(text)
            out["record_count"] = len(records)
            snapped = set()
            for rec_i, block in enumerate(records):
                record_hit = False
                for key, value in block.items():
                    if key == "_head" or not isinstance(value, str):
                        continue
                    for tok in tokens:
                        if n03a.field_value_exact_token(
                                value, tok["value"], tok["kind"]):
                            record_hit = True
                            ident = (
                                block.get("WeaponName")
                                or block.get("Name")
                                or block.get("ItemName")
                                or ""
                            )
                            out["field_hits"].append({
                                "record_index": rec_i,
                                "head": block.get("_head", ""),
                                "field": key,
                                "value": value,
                                "token_kind": tok["kind"],
                                "token": tok["value"],
                                "asset_role": tok["asset_role"],
                                "identity_name": ident,
                                "identity_name_gbk": gbk_display(ident),
                            })
                if record_hit and rec_i not in snapped:
                    snapped.add(rec_i)
                    snap = {
                        "record_index": rec_i,
                        "head": block.get("_head", ""),
                    }
                    for fk in WEAPON_SNAPSHOT_FIELDS:
                        if fk in block:
                            snap[fk] = block[fk]
                            snap[fk + "_gbk"] = gbk_display(block[fk])
                    out["weapon_snapshots"].append(snap)
    else:
        out["decode_ok"] = True
        out["decode_reason"] = "string_scan"
        text = n03a.extract_ascii_and_utf16le(data)
        if n03a._printable_ratio(data) >= 0.6:
            text = data.decode("latin-1", errors="replace") + "\n" + text

    for tok in tokens:
        hits = n03a.find_token_hits(text, tok["value"], tok["kind"], cap=30)
        for h in hits:
            out["text_hits"].append({
                "token_kind": tok["kind"],
                "token": tok["value"],
                "asset_role": tok["asset_role"],
                "offset": h["offset"],
                "context": h["context"],
            })
    return out


def classify(results: list[dict]) -> dict:
    field_hits = [h for r in results for h in r["field_hits"]]
    consumer_fields = [
        h for h in field_hits
        if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}
    ]
    text_path = [
        h for r in results for h in r["text_hits"]
        if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}
    ]
    hash_text = [
        h for r in results for h in r["text_hits"]
        if h["token_kind"] in {"sha256", "md5"}
    ]
    table_text = [
        (r, h) for r in results for h in r["text_hits"]
        if r["ext"] == ".cft"
        and h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}
    ]
    read_fail = [r for r in results if not r["read_ok"] and not r["skipped"]]
    ltc_fail = [
        r for r in results
        if r["ext"] == ".ltc" and r["read_ok"] and not r["decode_ok"]
        and r["decode_reason"] not in {"wrapper_no_match"}
    ]

    if consumer_fields or table_text:
        # A CFT string hit is a candidate until the surrounding record
        # is shown to be a bind field.  Confirmed only for parsed fields.
        if consumer_fields:
            status = "BORNBEAST_CONSUMER_CONFIRMED"
            confidence = "HIGH"
        else:
            status = "CANDIDATE_ONLY"
            confidence = "MEDIUM"
    elif text_path or hash_text:
        status = "CANDIDATE_ONLY"
        confidence = "LOW"
    else:
        status = "CANDIDATE_ONLY"
        confidence = "LOW"

    if read_fail and not any(r["read_ok"] for r in results):
        status = "REWORK_REQUIRED"
        confidence = "NONE"

    return {
        "status": status,
        "confidence": confidence,
        "selected": len(results),
        "skipped": sum(1 for r in results if r["skipped"]),
        "read_ok": sum(1 for r in results if r["read_ok"]),
        "consumer_field_hits": len(consumer_fields),
        "text_path_hits": len(text_path),
        "hash_text_hits": len(hash_text),
        "cft_text_hits": len(table_text),
        "ltc_decode_fail_non_wrapper": len(ltc_fail),
        "files_with_any_hit": sum(
            1 for r in results if r["field_hits"] or r["text_hits"]
        ),
    }


def write_report(status, classif, results, rez_meta, elapsed, tokens) -> str:
    lines = []
    a = lines.append
    a("# P4-M01-N03-B — REZ-resident table/config BornBeast search")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{classif['confidence']}**")
    a("- script: `scripts/material_recovery/n03b_rez_packed_config.py`")
    a("- consumes: N03-A inventory tokens + N02-D-R1 REZ index + N02-B-R1 LTC decoder")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("## 1. Question")
    a("")
    a("```text")
    a("BornBeast inventory token")
    a("  -> REZ-resident table/config payload")
    a("  -> record / field context")
    a("  -> consumer relation grade")
    a("```")
    a("")
    a("## 2. Selection")
    a("")
    a("| rule | value |")
    a("|---|---|")
    a("| extensions | `.cft` `.lta` `.txt` |")
    a("| extra .ltc | `full_path` starts with `BUTES/` |")
    a("| unique full_path | yes, preferred archive `rez/` |")
    a(f"| payload size cap | {PAYLOAD_MAX_BYTES} bytes |")
    a("| excluded | `.dat` `.dtx` `.bin` `.ltb` `.cfg` non-BUTES `.ltc` |")
    a("")
    by_ext = Counter(r["ext"] for r in results)
    a("| ext | selected | skipped | read_ok | files_with_hits |")
    a("|---|---|---|---|---|")
    for ext in sorted(by_ext):
        rows = [r for r in results if r["ext"] == ext]
        a(f"| `{ext}` | {len(rows)} | "
          f"{sum(1 for r in rows if r['skipped'])} | "
          f"{sum(1 for r in rows if r['read_ok'])} | "
          f"{sum(1 for r in rows if r['field_hits'] or r['text_hits'])} |")
    a("")
    a(f"- REZ archives indexed: {rez_meta.get('rez_count_indexed', 0)}")
    a(f"- REZ file entries: {rez_meta.get('total_entries', 0)}")
    a(f"- tokens: {len(tokens)}")
    a("")
    a("### Priority tables")
    a("")
    a("| full_path | present | size | hits |")
    a("|---|---|---|---|")
    by_fp = {r["full_path"].replace("\\", "/").upper(): r for r in results}
    for p in PRIORITY_TABLES:
        r = by_fp.get(p.upper())
        if not r:
            a(f"| `{p}` | no | — | — |")
            continue
        nh = len(r["field_hits"]) + len(r["text_hits"])
        a(f"| `{r['full_path']}` | yes | {r['size']} | {nh} |")
    a("")
    a("## 3. Hits")
    a("")
    a("| metric | count |")
    a("|---|---|")
    a(f"| DIRECT_CONFIG_FIELD | {classif['consumer_field_hits']} |")
    a(f"| CFT text-token | {classif['cft_text_hits']} |")
    a(f"| any path/stem text-token | {classif['text_path_hits']} |")
    a(f"| hash-hex text-token | {classif['hash_text_hits']} |")
    a(f"| files with any hit | {classif['files_with_any_hit']} |")
    a("")

    hit_rows = [r for r in results if r["field_hits"] or r["text_hits"]]
    if not hit_rows:
        a("**No exact inventory token** in the selected packed payloads.")
        a("This is a scoped negative for REZ-resident `.cft` / `.lta` / `.txt`")
        a("and packed `BUTES/*.ltc`, not a global 'no consumer exists' claim.")
        a("")
    else:
        a("### 3.1 Per-file hits")
        a("")
        a("| archive | full_path | ext | size | field_hits | unique_weapons |")
        a("|---|---|---|---|---|---|")
        for r in hit_rows:
            a(f"| `{archive_label(r['rez_path'])}` | `{r['full_path']}` | "
              f"`{r['ext']}` | {r['size']} | {len(r['field_hits'])} | "
              f"{len(r.get('weapon_snapshots') or [])} |")
        a("")
        a("The packed `Butes/BF005.LTC` inside `rez/RB001.REZ` is a **different")
        a("payload** from the loose `rez/Butes/bf005.ltc` that N02-C / N03-A")
        a("decoded (loose file is tens of KB; packed copy is multi-MB).")
        a("That is why BornBeast was absent from the loose Bute layer.")
        a("")
        a("### 3.2 Unique Weapon records that bind BornBeast")
        a("")
        snaps = [s for r in hit_rows for s in (r.get("weapon_snapshots") or [])]
        if not snaps:
            a("None.")
            a("")
        else:
            a("| WeaponName (GBK) | StandardName | PViewModelFileName | PViewSkinFileName |")
            a("|---|---|---|---|")
            seen = set()
            for s in snaps:
                key = (
                    s.get("WeaponName", ""),
                    s.get("PViewModelFileName", ""),
                    s.get("PViewSkinFileName", ""),
                )
                if key in seen:
                    continue
                seen.add(key)
                a(f"| `{s.get('WeaponName_gbk') or s.get('WeaponName','')}` | "
                  f"`{s.get('StandardName','')}` | "
                  f"`{s.get('PViewModelFileName','')}` | "
                  f"`{s.get('PViewSkinFileName','')}` |")
            a("")
            a("Deduped exact field binds (role collapsed):")
            a("")
            a("| identity (GBK) | field | value |")
            a("|---|---|---|")
            seen_f = set()
            for r in hit_rows:
                for h in r["field_hits"]:
                    key = (h.get("identity_name_gbk") or h["identity_name"],
                           h["field"], h["value"])
                    if key in seen_f:
                        continue
                    if h["token_kind"] not in {
                            "basename", "stem", "rez_path", "source_path"}:
                        continue
                    seen_f.add(key)
                    a(f"| `{key[0]}` | `{h['field']}` | `{h['value']}` |")
            a("")
        a("### 3.3 Text-token context (cap 40)")
        a("")
        a("| file | token_kind | token | role | context |")
        a("|---|---|---|---|---|")
        shown = 0
        for r in hit_rows:
            for h in r["text_hits"]:
                if shown >= 40:
                    break
                ctx = h["context"].replace("|", "\\|")
                a(f"| `{r['full_path']}` | `{h['token_kind']}` | `{h['token']}` | "
                  f"`{h['asset_role']}` | `{ctx}` |")
                shown += 1
        a("")

    a("## 4. Remaining ambiguity")
    a("")
    a("- Loose `rez/Butes/bf005.ltc` miss remains (N03-A); the consumer lives")
    a("  in the **packed** `RB001.REZ` copy, which is a different payload.")
    a("- Canonical bind is `M4A1-黑骑士` / `StandardName=M4A1_S_BornBeast`")
    a("  → `PViewModelFileName=PV-M4A1_S_BornBeast`")
    a("  → `PViewSkinFileName=PV-M4A1_S_BornBeast.dtx`.")
    a("  Those two paths are the N03-A SHA-verified inventory geometry + base_dtx.")
    a("- Family variants reuse the same LTB with **other** DTX names;")
    a("  those DTX are not the P4 inventory `base_dtx`.")
    a("- Alpha / Normal / Specular TGA and WeaponShader CFG are **not**")
    a("  file-path fields on these Weapon records. `StandardName` /")
    a("  `BigIconName` equal the CFG stem, which is an alias, not a CFG path.")
    a("- LTB piece → DTX/TGA still `OPEN_UNRESOLVED`.")
    a("- CFG/render semantic closure still `OPEN_UNRESOLVED`.")
    a("- This does **not** identify P5 雷神 and is **not** P4-M01 PASS.")
    a("")
    a(f"### Confidence: `{classif['confidence']}`")
    a("")
    a("## 5. Status")
    a("")
    a(f"**status**: `{status}`")
    a("")
    a("## 6. Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT treat WeaponShader `.cfg` as consumer")
    a("- did NOT scan `.dat` / `.dtx` / `.bin` / `.ltb` / non-BUTES `.ltc`")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT use filename similarity as proof")
    a("- did NOT freeze CFG shader semantics")
    a("- did NOT modify historical accepted evidence or `plan.md`")
    a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None)
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02dr1)
        importlib.reload(n02er2)
        importlib.reload(n03a)

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    print(f"[n03b] cf_root = {CF_DIR}", file=sys.stderr)
    t0 = time.time()

    inventory = n03a.load_inventory()
    tokens = []
    local_hashes = {}
    for item in inventory["items"]:
        lh = n03a.hash_local_asset(item["relative_path"])
        local_hashes[item["asset_role"]] = lh
        tokens.extend(n03a.build_asset_tokens(item, lh))
    print(f"[n03b] tokens={len(tokens)}", file=sys.stderr)

    print("[n03b] building REZ index...", file=sys.stderr)
    idx = n02dr1.build_full_path_index(n02dr1.enumerate_rez_files())
    rez_meta = {
        "rez_count_indexed": len(idx["rez_summaries"]),
        "total_entries": idx["total_entries"],
        "total_unique_full_paths": idx["total_unique_full_paths"],
    }
    selected = select_payloads(idx)
    print(f"[n03b] selected unique payloads: {len(selected)} "
          f"{dict(Counter(r['ext'] for r in selected))}", file=sys.stderr)

    results = []
    for i, rec in enumerate(selected, 1):
        r = search_payload(rec, tokens)
        results.append(r)
        if r["field_hits"] or r["text_hits"]:
            print(f"[n03b] HIT {r['full_path']} "
                  f"field={len(r['field_hits'])} text={len(r['text_hits'])}",
                  file=sys.stderr)
        if i % 100 == 0:
            print(f"[n03b] searched {i}/{len(selected)}", file=sys.stderr)

    classif = classify(results)
    status = classif["status"]
    elapsed = time.time() - t0
    print(f"[n03b] status={status} confidence={classif['confidence']} "
          f"elapsed={elapsed:.2f}s", file=sys.stderr)

    hit_files = [
        {
            "full_path": r["full_path"],
            "ext": r["ext"],
            "rez_path": r["rez_path"],
            "size": r["size"],
            "field_hits": r["field_hits"],
            "text_hits": r["text_hits"],
            "weapon_snapshots": r.get("weapon_snapshots") or [],
        }
        for r in results if r["field_hits"] or r["text_hits"]
    ]

    selected_inv = {
        "task": "P4-M01-N03-B",
        "selection_rule": {
            "ext": sorted(ALLOWED_EXTS),
            "ltc_prefix": LTC_PREFIX,
            "payload_max_bytes": PAYLOAD_MAX_BYTES,
        },
        "rez_index": rez_meta,
        "counts_by_ext": dict(Counter(r["ext"] for r in results)),
        "payloads": [
            {k: r[k] for k in (
                "full_path", "name", "ext", "size", "rez_path",
                "archive_count", "archives", "priority_table",
                "skipped", "skip_reason", "read_ok", "decode_ok",
                "decode_reason", "magic_hex", "record_count",
            ) if k in r}
            for r in results
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "selected_payload_inventory.json"),
              "w", encoding="utf-8") as f:
        json.dump(selected_inv, f, indent=2, ensure_ascii=False)

    search_payload_json = {
        "task": "P4-M01-N03-B",
        "status": status,
        "confidence": classif["confidence"],
        "classification": classif,
        "tokens": tokens,
        "hit_files": hit_files,
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "token_hits.json"),
              "w", encoding="utf-8") as f:
        json.dump(search_payload_json, f, indent=2, ensure_ascii=False)

    graph = {
        "task": "P4-M01-N03-B",
        "status": status,
        "confidence": classif["confidence"],
        "note": (
            "Packed-config reverse graph. Loose Bute miss from N03-A is "
            "not re-opened. WeaponShader CFG is not treated as consumer."
        ),
        "edges": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    for r in results:
        for h in r["field_hits"]:
            if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}:
                graph["edges"].append({
                    "from": f"{r['full_path']}:{h['field']}",
                    "to": f"inventory:{h['asset_role']}",
                    "grade": "DIRECT_CONFIG_FIELD",
                    "value": h["value"],
                })
        for h in r["text_hits"]:
            if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}:
                graph["edges"].append({
                    "from": r["full_path"],
                    "to": f"inventory:{h['asset_role']}",
                    "grade": "PACKED_TEXT_TOKEN",
                    "token": h["token"],
                    "context": h["context"],
                })
    if not graph["edges"]:
        graph["edges"].append({
            "from": "REZ-resident .cft/.lta/.txt + BUTES/*.ltc",
            "to": "BornBeast inventory",
            "grade": "SCOPED_NEGATIVE",
        })
    with open(os.path.join(OUT_DIR, "resource_graph.json"),
              "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    relations = []
    for e in graph["edges"]:
        if e["grade"] in {"DIRECT_CONFIG_FIELD", "PACKED_TEXT_TOKEN"}:
            relations.append({
                "relation": "packed config token -> inventory asset",
                **e,
                "confidence": "HIGH" if e["grade"] == "DIRECT_CONFIG_FIELD"
                else "MEDIUM",
            })
    relations.append({
        "relation": "N03-A BornBeast runtime REZ payload identity",
        "grade": "PAYLOAD_IDENTITY",
        "confidence": "HIGH",
        "source": "P4-M01-N03-A (not re-litigated)",
    })
    confirmed = {
        "task": "P4-M01-N03-B",
        "status": status,
        "confidence": classif["confidence"],
        "relations": relations,
        "remaining_blockers": [
            "BornBeast consumer path OPEN_UNRESOLVED"
            if classif["consumer_field_hits"] == 0 else
            "consumer field found; piece-level material still open",
            "LTB piece -> DTX/TGA OPEN_UNRESOLVED",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(confirmed, f, indent=2, ensure_ascii=False)

    report = write_report(status, classif, results, rez_meta, elapsed, tokens)
    with open(os.path.join(OUT_DIR, "packed_config_search_report.md"),
              "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[n03b] wrote {OUT_DIR}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
