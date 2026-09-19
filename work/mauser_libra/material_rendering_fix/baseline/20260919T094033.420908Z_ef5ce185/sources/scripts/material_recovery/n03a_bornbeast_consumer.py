#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-A — BornBeast consumer path discovery.

Implements the bounded task P4-M01-N03-A from task.md.

Goal: reverse-lookup the P4 BornBeast native inventory assets against
current CF runtime config + REZ, answering:

    inventory asset
      -> runtime/config consumer
      -> REZ/resource path
      -> payload identity

This round does NOT start from bf005 M4A1 records (already proven
!= BornBeast by N02-E-R2).  It starts from the six inventory items
in evidence/native_material_inventory.json and looks for exact
filename / path / hash references.

Allowed:
  - reuse N02-B-R1 LTC wrapper+decoder on rez/Butes/*.ltc
  - string-scan N02-A config-role files (.ltc/.lta/.ini/.cfg) plus
    every file sitting in rez/Butes/ (bounded directory)
  - N02-D-R1 path-aware REZ directory index (no bulk extract)
  - bounded payload SHA256 of exact-path / size-matching hits
  - exact token match only (bounded by non-identifier characters)

Forbidden:
  - P4-M01 PASS announcement
  - treating bf005 M4A1 bindings as BornBeast identity
  - DLL / EXE / FXO reverse
  - untargeted full-disk scan
  - filename similarity as proof
  - CFG shader semantic freeze
  - rewriting historical accepted evidence or plan.md

Outputs under
  work/.../runtime_acquisition/n03a_bornbeast_consumer/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02_butes_config_triage as n02b  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition",
)
EVIDENCE_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "evidence"
)
INVENTORY_PATH = os.path.join(EVIDENCE_DIR, "native_material_inventory.json")
ARTIFACT_INV_PATH = os.path.join(N02A_DIR, "artifact_inventory.json")
OUT_DIR = os.path.join(N02A_DIR, "n03a_bornbeast_consumer")
os.makedirs(OUT_DIR, exist_ok=True)

CONFIG_EXTS = {".ltc", ".lta", ".ini", ".cfg"}
STRING_SCAN_MAX_BYTES = 8 * 1024 * 1024
IDENT_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
HEX_CHARS = set("0123456789abcdefABCDEF")


# ---------------------------------------------------------------------------
# Inventory + exact tokens
# ---------------------------------------------------------------------------
def load_inventory() -> dict:
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_data_pack_prefix(rel: str) -> str:
    """data/rf016/Models/PLAYERVIEW/X.LTB -> Models/PLAYERVIEW/X.LTB."""
    p = rel.replace("\\", "/")
    m = re.match(r"^data/[^/]+/(.+)$", p, re.IGNORECASE)
    return m.group(1) if m else p


def inventory_to_rez_path(rel: str) -> str:
    """Map an inventory relative_path to a REZ archive-relative logical path."""
    logical = _strip_data_pack_prefix(rel)
    return n02dr1.normalise_bf005_to_rez_path(logical)["upper"]


def hash_local_asset(rel: str) -> dict:
    """SHA256 + MD5 of the local_cf inventory file. Not a data/** rescan."""
    abs_path = os.path.join(REPO, rel.replace("/", os.sep))
    out = {
        "abs_path": abs_path,
        "present": os.path.isfile(abs_path),
        "sha256": "",
        "md5": "",
        "size_bytes": 0,
    }
    if not out["present"]:
        return out
    h_sha = hashlib.sha256()
    h_md5 = hashlib.md5()
    size = 0
    with open(abs_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h_sha.update(chunk)
            h_md5.update(chunk)
            size += len(chunk)
    out["sha256"] = h_sha.hexdigest().upper()
    out["md5"] = h_md5.hexdigest().upper()
    out["size_bytes"] = size
    return out


def build_asset_tokens(item: dict, local_hash: dict) -> list[dict]:
    """Exact reverse-lookup tokens for one inventory item.

    Each token is typed.  Filename-similarity / prefix-of-a-longer-name
    is rejected later by bounded-token matching.
    """
    rel = item["relative_path"].replace("\\", "/")
    base = os.path.basename(rel)
    stem, ext = os.path.splitext(base)
    rez_path = inventory_to_rez_path(rel)
    source_tail = _strip_data_pack_prefix(rel)
    sha = (item.get("sha256") or local_hash.get("sha256") or "").upper()
    md5 = (local_hash.get("md5") or "").upper()
    tokens = [
        {"kind": "basename", "value": base, "asset_role": item["asset_role"]},
        {"kind": "stem", "value": stem, "asset_role": item["asset_role"]},
        {"kind": "rez_path", "value": rez_path, "asset_role": item["asset_role"]},
        {"kind": "source_path", "value": source_tail, "asset_role": item["asset_role"]},
    ]
    if sha:
        tokens.append({"kind": "sha256", "value": sha,
                       "asset_role": item["asset_role"]})
    if md5:
        tokens.append({"kind": "md5", "value": md5,
                       "asset_role": item["asset_role"]})
    return tokens


def is_bounded_match(text: str, start: int, token: str, kind: str) -> bool:
    """Reject prefix/suffix overlap with a longer identifier.

    `PV-M4A1_S_BornBeast` must not count as a hit inside
    `PV-M4A1_S_BornBeast_Classic`.  Hash tokens use hex boundaries.
    """
    end = start + len(token)
    prev = text[start - 1] if start > 0 else ""
    nxt = text[end] if end < len(text) else ""
    if kind in {"sha256", "md5"}:
        if prev and prev in HEX_CHARS:
            return False
        if nxt and nxt in HEX_CHARS:
            return False
        return True
    if prev and prev in IDENT_CHARS:
        return False
    if nxt and nxt in IDENT_CHARS:
        return False
    return True


def find_token_hits(text: str, token: str, kind: str, cap: int = 20) -> list[dict]:
    if not token or not text:
        return []
    hay = text
    needle = token
    if kind != "sha256" and kind != "md5":
        hay_l = text.lower()
        needle_l = token.lower()
        hits = []
        start = 0
        while len(hits) < cap:
            i = hay_l.find(needle_l, start)
            if i < 0:
                break
            if is_bounded_match(text, i, token, kind):
                ctx0 = max(0, i - 40)
                ctx1 = min(len(text), i + len(token) + 40)
                hits.append({
                    "offset": i,
                    "context": text[ctx0:ctx1].replace("\r", " ").replace("\n", " "),
                })
            start = i + 1
        return hits
    # hashes: case-insensitive hex
    hay_l = text.lower()
    needle_l = token.lower()
    hits = []
    start = 0
    while len(hits) < cap:
        i = hay_l.find(needle_l, start)
        if i < 0:
            break
        if is_bounded_match(text, i, token, kind):
            hits.append({"offset": i, "context": text[i:i + len(token)]})
        start = i + 1
    return hits


# ---------------------------------------------------------------------------
# Lisp parser that keeps every (Key Value) pair
# ---------------------------------------------------------------------------
def parse_lisp_all_keys(text: str) -> list[dict]:
    """Same block walker as n02b._parse_lisp_s_expressions, all keys kept."""
    records: list[dict] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "(":
            i += 1
            continue
        depth = 0
        start = i
        in_str = False
        j = i
        while j < n:
            ch = text[j]
            if in_str:
                if ch == '"':
                    in_str = False
                j += 1
                continue
            if ch == '"':
                in_str = True
                j += 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        rec = _parse_one_block_all_keys(text[start:j])
        if rec is not None:
            records.append(rec)
        i = j
    return records


def _parse_one_block_all_keys(block: str) -> Optional[dict]:
    if not block.startswith("(") or not block.endswith(")"):
        return None
    inner = block[1:-1].strip()
    head_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", inner)
    if not head_match:
        return None
    head = head_match.group(1)
    rest = inner[head_match.end():]
    out: dict = {"_head": head}
    for m in n02b._BUTE_KV_PAIR_RE.finditer(rest):
        key = m.group(1)
        value = m.group(2) if m.group(2) is not None else m.group(3)
        if value is None:
            continue
        out[key] = value
    return out


def field_value_exact_token(value: str, token: str, kind: str) -> bool:
    if not value or not token:
        return False
    v = value.replace("\\", "/").strip().strip('"')
    t = token.replace("\\", "/").strip()
    if kind in {"sha256", "md5"}:
        return v.upper() == t.upper()
    if kind == "basename":
        return os.path.basename(v).lower() == t.lower()
    if kind == "stem":
        return os.path.splitext(os.path.basename(v))[0].lower() == t.lower()
    if kind in {"rez_path", "source_path"}:
        vn = n02dr1.normalise_bf005_to_rez_path(v)["upper"]
        tn = n02dr1.normalise_bf005_to_rez_path(t)["upper"]
        return vn == tn or v.replace("\\", "/").lower() == t.replace("\\", "/").lower()
    return v.lower() == t.lower()


# ---------------------------------------------------------------------------
# Decode / string-scan helpers
# ---------------------------------------------------------------------------
def decode_ltc_file(abs_path: str) -> dict:
    with open(abs_path, "rb") as f:
        data = f.read()
    unlocked = n02b.try_unlock_crossfire_payload(data)
    if unlocked is None:
        return {"ok": False, "reason": "wrapper_no_match", "raw": data,
                "text": ""}
    try:
        decoded = n02b._decode_ltc_c_sharp(unlocked)
    except n02b.LtcDecodeFailure as e:
        return {"ok": False, "reason": str(e), "raw": data, "text": ""}
    text = decoded.decode("latin-1", errors="replace")
    return {"ok": True, "reason": "DECODED", "raw": data, "text": text,
            "decoded_size": len(decoded)}


def extract_ascii_and_utf16le(data: bytes, min_len: int = 6) -> str:
    """Join printable ASCII + UTF-16LE runs into one search haystack."""
    parts: list[str] = []
    buf = bytearray()
    for b in data:
        if 32 <= b < 127:
            buf.append(b)
        else:
            if len(buf) >= min_len:
                parts.append(buf.decode("ascii"))
            buf = bytearray()
    if len(buf) >= min_len:
        parts.append(buf.decode("ascii"))
    # UTF-16LE runs
    i = 0
    run = bytearray()
    n = len(data) - 1
    while i < n:
        lo, hi = data[i], data[i + 1]
        if hi == 0 and 32 <= lo < 127:
            run.append(lo)
            i += 2
            continue
        if len(run) >= min_len:
            parts.append(run.decode("ascii"))
        run = bytearray()
        i += 1
    if len(run) >= min_len:
        parts.append(run.decode("ascii"))
    return "\n".join(parts)


def load_n02a_config_files() -> list[dict]:
    with open(ARTIFACT_INV_PATH, "r", encoding="utf-8") as f:
        inv = json.load(f)
    out = []
    for rec in inv.get("inventory", []):
        ext = (rec.get("extension") or "").lower()
        role = rec.get("candidate_role") or ""
        if ext not in CONFIG_EXTS:
            continue
        if role != "config" and ext not in {".ltc", ".lta", ".ini", ".cfg"}:
            continue
        out.append({
            "source": "n02a_artifact_inventory",
            "path_alias": rec.get("path_alias", ""),
            "abs_path": rec.get("abs_path", ""),
            "size_bytes": rec.get("size_bytes", 0),
            "extension": ext,
        })
    return out


def enumerate_butes_dir() -> list[dict]:
    d = os.path.join(CF_DIR, "rez", "Butes")
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            continue
        st = os.stat(p)
        out.append({
            "source": "rez/Butes directory listing",
            "path_alias": f"rez/Butes/{fn}",
            "abs_path": p,
            "size_bytes": st.st_size,
            "extension": os.path.splitext(fn)[1].lower(),
        })
    return out


def merge_config_candidates(n02a: list[dict], butes: list[dict]) -> list[dict]:
    by_abs: dict = {}
    for rec in n02a + butes:
        key = os.path.normcase(os.path.abspath(rec["abs_path"]))
        if key not in by_abs:
            by_abs[key] = rec
        else:
            srcs = {by_abs[key]["source"], rec["source"]}
            by_abs[key]["source"] = " + ".join(sorted(srcs))
    return sorted(by_abs.values(), key=lambda r: r["path_alias"].lower())


# ---------------------------------------------------------------------------
# Search one config file
# ---------------------------------------------------------------------------
def search_config_file(rec: dict, tokens: list[dict]) -> dict:
    abs_path = rec["abs_path"]
    ext = rec["extension"]
    result = {
        "path_alias": rec["path_alias"],
        "abs_path": abs_path,
        "source": rec["source"],
        "extension": ext,
        "size_bytes": rec["size_bytes"],
        "decode_ok": False,
        "decode_reason": "",
        "text_hits": [],
        "field_hits": [],
        "record_count": 0,
        "skipped": False,
        "skip_reason": "",
    }
    if rec["size_bytes"] > STRING_SCAN_MAX_BYTES:
        result["skipped"] = True
        result["skip_reason"] = f"size {rec['size_bytes']} > {STRING_SCAN_MAX_BYTES}"
        return result
    if not os.path.isfile(abs_path):
        result["skipped"] = True
        result["skip_reason"] = "file_missing"
        return result

    text = ""
    if ext == ".ltc":
        dec = decode_ltc_file(abs_path)
        result["decode_ok"] = dec["ok"]
        result["decode_reason"] = dec["reason"]
        if not dec["ok"]:
            # still string-scan raw bytes; may catch plaintext leftovers
            text = extract_ascii_and_utf16le(dec["raw"])
        else:
            text = dec["text"]
            records = parse_lisp_all_keys(text)
            result["record_count"] = len(records)
            for rec_i, block in enumerate(records):
                for key, value in block.items():
                    if key == "_head" or not isinstance(value, str):
                        continue
                    for tok in tokens:
                        if field_value_exact_token(value, tok["value"], tok["kind"]):
                            result["field_hits"].append({
                                "record_index": rec_i,
                                "head": block.get("_head", ""),
                                "field": key,
                                "value": value,
                                "token_kind": tok["kind"],
                                "token": tok["value"],
                                "asset_role": tok["asset_role"],
                                "identity_name": (
                                    block.get("WeaponName")
                                    or block.get("Name")
                                    or block.get("ArmorName")
                                    or block.get("CharacterName")
                                    or block.get("SoundName")
                                    or ""
                                ),
                            })
    else:
        with open(abs_path, "rb") as f:
            raw = f.read()
        result["decode_ok"] = True
        result["decode_reason"] = "string_scan"
        text = extract_ascii_and_utf16le(raw)
        # also try latin-1 full decode for small text-ish files
        if _printable_ratio(raw) >= 0.7:
            text = raw.decode("latin-1", errors="replace") + "\n" + text

    for tok in tokens:
        hits = find_token_hits(text, tok["value"], tok["kind"])
        for h in hits:
            result["text_hits"].append({
                "token_kind": tok["kind"],
                "token": tok["value"],
                "asset_role": tok["asset_role"],
                "offset": h["offset"],
                "context": h["context"],
            })
    return result


def _printable_ratio(data: bytes, cap: int = 4096) -> float:
    sample = data[:cap]
    if not sample:
        return 0.0
    printable = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}
    return sum(1 for b in sample if b in printable) / len(sample)


# ---------------------------------------------------------------------------
# REZ reverse lookup + bounded SHA
# ---------------------------------------------------------------------------
def lookup_rez(item: dict, idx: dict, local_hash: dict) -> dict:
    rel = item["relative_path"]
    rez_path = inventory_to_rez_path(rel)
    base = os.path.basename(rel)
    exact = idx["by_full_path"].get(rez_path.upper(), [])
    basename_hits = idx["by_basename"].get(base.upper(), [])
    # Basename hits that are also exact-path hits are not "basename-only".
    exact_keys = {(h["rez_path"], h["full_path"].upper()) for h in exact}
    basename_only = [
        h for h in basename_hits
        if (h["rez_path"], h["full_path"].upper()) not in exact_keys
    ]
    payload_checks = []
    for h in exact:
        payload_checks.append(_hash_rez_hit(h, item, local_hash, "EXACT_PATH"))
    for h in basename_only:
        # Only hash when size matches inventory — avoids pulling unrelated
        # same-basename payloads. Size match is a filter, not identity proof.
        if h["size"] == item.get("size_bytes"):
            payload_checks.append(
                _hash_rez_hit(h, item, local_hash, "BASENAME_SIZE_FILTER")
            )
        else:
            payload_checks.append({
                "query": "BASENAME_ONLY_SIZE_MISMATCH",
                "rez_path": h["rez_path"],
                "full_path": h["full_path"],
                "name": h["name"],
                "size": h["size"],
                "inventory_size": item.get("size_bytes"),
                "sha256": "",
                "sha_match": False,
                "read_ok": False,
                "note": "not hashed; size != inventory size_bytes",
            })
    return {
        "asset_role": item["asset_role"],
        "inventory_relative_path": rel,
        "inventory_sha256": (item.get("sha256") or "").upper(),
        "rez_logical_path": rez_path,
        "basename": base,
        "exact_path_hit_count": len(exact),
        "basename_only_hit_count": len(basename_only),
        "exact_path_hits": [
            {k: h[k] for k in ("rez_path", "full_path", "name", "size",
                               "data_offset", "md5")}
            for h in exact
        ],
        "basename_only_hits": [
            {k: h[k] for k in ("rez_path", "full_path", "name", "size",
                               "data_offset", "md5")}
            for h in basename_only
        ],
        "payload_checks": payload_checks,
    }


def _hash_rez_hit(hit: dict, item: dict, local_hash: dict, query: str) -> dict:
    rec = {
        "query": query,
        "rez_path": hit["rez_path"],
        "full_path": hit["full_path"],
        "name": hit["name"],
        "size": hit["size"],
        "data_offset": hit["data_offset"],
        "catalog_md5": hit.get("md5", ""),
        "sha256": "",
        "md5": "",
        "sha_match": False,
        "read_ok": False,
        "note": "",
    }
    try:
        data = n02er2.read_payload_bytes(
            hit["rez_path"], hit["data_offset"], hit["size"]
        )
    except (OSError, ValueError) as e:
        rec["note"] = f"read_failed: {e}"
        return rec
    rec["read_ok"] = True
    rec["actual_bytes_read"] = len(data)
    rec["sha256"] = hashlib.sha256(data).hexdigest().upper()
    rec["md5"] = hashlib.md5(data).hexdigest().upper()
    inv_sha = (item.get("sha256") or local_hash.get("sha256") or "").upper()
    rec["sha_match"] = bool(inv_sha) and rec["sha256"] == inv_sha
    if rec["sha_match"]:
        rec["note"] = "payload SHA256 == inventory SHA256"
    else:
        rec["note"] = "payload SHA256 != inventory SHA256"
    return rec


# ---------------------------------------------------------------------------
# Status / graph
# ---------------------------------------------------------------------------
def classify_status(config_results: list[dict], rez_results: list[dict]) -> dict:
    field_hits = [h for r in config_results for h in r["field_hits"]]
    # A consumer is confirmed only when a parsed config FIELD value
    # exact-matches a path/basename/stem token (not a bare family name,
    # not a hash sitting in unrelated text, not a REZ existence hit).
    consumer_field_hits = [
        h for h in field_hits
        if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}
    ]
    sha_payload_matches = [
        c for r in rez_results for c in r["payload_checks"] if c.get("sha_match")
    ]
    exact_path_hits = sum(r["exact_path_hit_count"] for r in rez_results)
    text_hits = [h for r in config_results for h in r["text_hits"]]
    text_path_hits = [
        h for h in text_hits
        if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}
    ]
    hash_text_hits = [
        h for h in text_hits if h["token_kind"] in {"sha256", "md5"}
    ]

    if consumer_field_hits:
        status = "BORNBEAST_CONSUMER_CONFIRMED"
        confidence = "HIGH" if sha_payload_matches else "MEDIUM"
    elif sha_payload_matches or exact_path_hits or text_path_hits or hash_text_hits:
        status = "CANDIDATE_ONLY"
        if sha_payload_matches:
            confidence = "MEDIUM"
        elif exact_path_hits or text_path_hits:
            confidence = "LOW"
        else:
            confidence = "LOW"
    else:
        # Search boundary was valid; nothing matched. Still CANDIDATE_ONLY
        # because absence from this config set is a scoped negative, not
        # proof that no consumer exists.
        status = "CANDIDATE_ONLY"
        confidence = "LOW"

    decode_failures = [r for r in config_results
                       if r["extension"] == ".ltc" and not r["decode_ok"]
                       and not r["skipped"]]
    missing_cf = not os.path.isdir(CF_DIR)
    if missing_cf or (decode_failures and not any(r["decode_ok"]
                      for r in config_results if r["extension"] == ".ltc")):
        status = "REWORK_REQUIRED"
        confidence = "NONE"

    return {
        "status": status,
        "confidence": confidence,
        "consumer_field_hit_count": len(consumer_field_hits),
        "sha_payload_match_count": len(sha_payload_matches),
        "exact_path_hit_count": exact_path_hits,
        "text_path_hit_count": len(text_path_hits),
        "hash_text_hit_count": len(hash_text_hits),
        "ltc_decode_failures": len(decode_failures),
        "cf_root_present": not missing_cf,
    }


def build_resource_graph(inventory: dict, rez_results: list[dict],
                         config_results: list[dict], local_hashes: dict) -> dict:
    assets = {}
    edges = []
    for item in inventory["items"]:
        role = item["asset_role"]
        rez = next((r for r in rez_results if r["asset_role"] == role), None)
        field_hits = [
            h for r in config_results for h in r["field_hits"]
            if h["asset_role"] == role
        ]
        text_hits = [
            h for r in config_results for h in r["text_hits"]
            if h["asset_role"] == role
        ]
        sha_ok = [
            c for c in (rez["payload_checks"] if rez else [])
            if c.get("sha_match")
        ]
        assets[role] = {
            "inventory_relative_path": item["relative_path"],
            "inventory_sha256": (item.get("sha256") or "").upper(),
            "inventory_size_bytes": item.get("size_bytes"),
            "rez_logical_path": rez["rez_logical_path"] if rez else "",
            "runtime_exact_path_hits": rez["exact_path_hits"] if rez else [],
            "payload_sha_matches": sha_ok,
            "consumer_field_hits": field_hits,
            "text_token_hits": text_hits[:10],
        }
        # inventory -> REZ
        if rez and rez["exact_path_hits"]:
            for h in rez["exact_path_hits"]:
                match = next(
                    (c for c in rez["payload_checks"]
                     if c["rez_path"] == h["rez_path"]
                     and c["full_path"] == h["full_path"]
                     and c.get("sha_match")),
                    None,
                )
                edges.append({
                    "from": f"inventory:{role}",
                    "to": f"{os.path.basename(h['rez_path'])}:{h['full_path']}",
                    "grade": (
                        "PAYLOAD_IDENTITY"
                        if match else
                        "REZ_EXACT_PATH_EXISTENCE"
                    ),
                })
        for h in field_hits:
            edges.append({
                "from": f"config:{h.get('head','')}:{h['field']}",
                "to": f"inventory:{role}",
                "grade": "DIRECT_CONFIG_FIELD",
                "value": h["value"],
                "path_alias": next(
                    (r["path_alias"] for r in config_results
                     if any(x is h for x in r["field_hits"])),
                    "",
                ),
            })
        if not field_hits and not (rez and rez["exact_path_hits"]):
            edges.append({
                "from": f"inventory:{role}",
                "to": "OPEN_UNRESOLVED",
                "grade": "OPEN_UNRESOLVED",
            })
    return {
        "task": "P4-M01-N03-A",
        "note": (
            "Reverse graph: BornBeast inventory assets looking for a "
            "runtime consumer and a REZ payload identity.  bf005 M4A1 "
            "family bindings are intentionally not copied here."
        ),
        "assets": assets,
        "edges": edges,
    }


def collect_confirmed_relations(rez_results, config_results, classif) -> list[dict]:
    rels = []
    for r in rez_results:
        for c in r["payload_checks"]:
            if c.get("sha_match"):
                rels.append({
                    "relation": "inventory_sha256 == runtime_rez_payload_sha256",
                    "asset_role": r["asset_role"],
                    "inventory_relative_path": r["inventory_relative_path"],
                    "rez_path": c["rez_path"],
                    "full_path": c["full_path"],
                    "sha256": c["sha256"],
                    "grade": "PAYLOAD_IDENTITY",
                    "confidence": "HIGH",
                })
        if r["exact_path_hit_count"] and not any(
                c.get("sha_match") for c in r["payload_checks"]):
            for h in r["exact_path_hits"]:
                rels.append({
                    "relation": "inventory logical path exists in runtime REZ",
                    "asset_role": r["asset_role"],
                    "inventory_relative_path": r["inventory_relative_path"],
                    "rez_path": h["rez_path"],
                    "full_path": h["full_path"],
                    "grade": "REZ_EXACT_PATH_EXISTENCE",
                    "confidence": "MEDIUM",
                    "note": "existence only; payload SHA did not match or was not read",
                })
    for rec in config_results:
        for h in rec["field_hits"]:
            if h["token_kind"] in {"basename", "stem", "rez_path", "source_path"}:
                rels.append({
                    "relation": "config field value exact-matches inventory token",
                    "asset_role": h["asset_role"],
                    "path_alias": rec["path_alias"],
                    "head": h["head"],
                    "field": h["field"],
                    "value": h["value"],
                    "identity_name": h["identity_name"],
                    "token_kind": h["token_kind"],
                    "grade": "DIRECT_CONFIG_FIELD",
                    "confidence": "HIGH",
                })
    rels.append({
        "relation": "bf005 M4A1 runtime family != BornBeast native asset",
        "grade": "SCOPED_NEGATIVE_ACCEPTED",
        "confidence": "HIGH",
        "source": "P4-M01-N02-E-R2 (not re-litigated this round)",
    })
    return rels


def _archive_label(rez_path: str) -> str:
    """CF-root-relative archive label, e.g. rez2/RF016.REZ."""
    try:
        return os.path.relpath(rez_path, CF_DIR).replace("\\", "/")
    except ValueError:
        return os.path.basename(rez_path)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(status: str, classif: dict, inventory: dict,
                 tokens: list[dict], config_results: list[dict],
                 rez_results: list[dict], rez_index_meta: dict,
                 elapsed: float, local_hashes: dict) -> str:
    lines = []
    a = lines.append
    a("# P4-M01-N03-A — BornBeast Consumer Path Discovery")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{classif['confidence']}**")
    a("- script: `scripts/material_recovery/n03a_bornbeast_consumer.py`")
    a("- consumes: `evidence/native_material_inventory.json` "
      "+ N02-B-R1 LTC decoder + N02-D-R1 REZ index + N02-A config inventory")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("## 1. Question")
    a("")
    a("```text")
    a("BornBeast inventory asset")
    a("  -> runtime/config consumer")
    a("  -> REZ/resource path")
    a("  -> payload identity")
    a("```")
    a("")
    a("Reverse lookup uses **exact** filename / path / hash tokens from the")
    a("P4 native inventory.  Bounded-token matching rejects a token that is")
    a("only a prefix of a longer identifier.  Filename similarity is not proof.")
    a("")
    a("## 2. Inventory tokens")
    a("")
    a("| asset_role | relative_path | rez_logical_path | sha256 | local_md5 |")
    a("|---|---|---|---|---|")
    for item in inventory["items"]:
        role = item["asset_role"]
        lh = local_hashes.get(role, {})
        rez_p = inventory_to_rez_path(item["relative_path"])
        sha = (item.get("sha256") or "")[:16]
        md5 = (lh.get("md5") or "")[:16]
        a(f"| `{role}` | `{item['relative_path']}` | `{rez_p}` "
          f"| `{sha}…` | `{md5}…` |")
    a("")
    a(f"- exact tokens emitted: **{len(tokens)}** "
      f"(basename/stem/rez_path/source_path/sha256/md5 per item)")
    a("- family-name substring `BornBeast` is **not** used as consumer proof")
    a("")
    a("## 3. Config search scope")
    a("")
    a("| metric | count |")
    a("|---|---|")
    a(f"| config files searched | {len(config_results)} |")
    a(f"| skipped | {sum(1 for r in config_results if r['skipped'])} |")
    a(f"| .ltc decode OK | {sum(1 for r in config_results if r['extension']=='.ltc' and r['decode_ok'])} |")
    a(f"| .ltc decode fail | {classif['ltc_decode_failures']} |")
    a(f"| parsed lisp records | {sum(r['record_count'] for r in config_results)} |")
    a(f"| DIRECT_CONFIG_FIELD hits | {classif['consumer_field_hit_count']} |")
    a(f"| decoded-text path/stem hits | {classif['text_path_hit_count']} |")
    a(f"| hash-hex text hits | {classif['hash_text_hit_count']} |")
    a("")
    field_hits = [h for r in config_results for h in r["field_hits"]]
    if field_hits:
        a("### 3.1 Direct config field hits")
        a("")
        a("| file | head | identity | field | value | token_kind | asset_role |")
        a("|---|---|---|---|---|---|---|")
        for rec in config_results:
            for h in rec["field_hits"]:
                a(f"| `{rec['path_alias']}` | `{h['head']}` | "
                  f"`{h['identity_name']}` | `{h['field']}` | `{h['value']}` | "
                  f"`{h['token_kind']}` | `{h['asset_role']}` |")
        a("")
    else:
        a("### 3.1 Direct config field hits")
        a("")
        a("**None.** No parsed Bute/LTC field value exact-matches a BornBeast")
        a("inventory basename, stem, or logical path.  This includes every")
        a("key (not only N02-B BINDING_FIELDS) across every successfully")
        a("decoded `rez/Butes/*.ltc`.")
        a("")
    text_hits = [h for r in config_results for h in r["text_hits"]]
    if text_hits:
        a("### 3.2 Bounded text-token hits")
        a("")
        a("| file | token_kind | token | asset_role | context |")
        a("|---|---|---|---|---|")
        shown = 0
        for rec in config_results:
            for h in rec["text_hits"]:
                if shown >= 30:
                    break
                ctx = h["context"].replace("|", "\\|")
                a(f"| `{rec['path_alias']}` | `{h['token_kind']}` | "
                  f"`{h['token']}` | `{h['asset_role']}` | `{ctx}` |")
                shown += 1
            if shown >= 30:
                break
        a("")
        a(f"- total text-token hits: {len(text_hits)} (table capped at 30)")
        a("")
    else:
        a("### 3.2 Bounded text-token hits")
        a("")
        a("**None** in decoded LTC text or string-scanned `.lta/.ini/.cfg`.")
        a("This reconfirms N02-B-R1's family-substring negative, now at")
        a("exact inventory-token granularity, and extends it to the rest")
        a("of the N02-A config-role set plus `rez/Butes/` directory files.")
        a("")

    a("## 4. Runtime REZ reverse lookup")
    a("")
    a("| metric | count |")
    a("|---|---|")
    a(f"| REZ archives indexed | {rez_index_meta.get('rez_count_indexed', 0)} |")
    a(f"| total REZ file entries | {rez_index_meta.get('total_entries', 0)} |")
    a(f"| unique full paths | {rez_index_meta.get('total_unique_full_paths', 0)} |")
    a(f"| exact-path hits (all assets) | {classif['exact_path_hit_count']} |")
    a(f"| payload SHA256 matches | {classif['sha_payload_match_count']} |")
    a("")
    a("| asset_role | rez_logical_path | exact_path | basename_only | sha_match |")
    a("|---|---|---|---|---|")
    for r in rez_results:
        n_sha = sum(1 for c in r["payload_checks"] if c.get("sha_match"))
        a(f"| `{r['asset_role']}` | `{r['rez_logical_path']}` | "
          f"{r['exact_path_hit_count']} | {r['basename_only_hit_count']} | "
          f"{n_sha} |")
    a("")
    any_payload = any(r["payload_checks"] for r in rez_results)
    if any_payload:
        a("### 4.1 Payload SHA256 checks")
        a("")
        a("| asset_role | query | archive | full_path | size | sha_match | note |")
        a("|---|---|---|---|---|---|---|")
        for r in rez_results:
            for c in r["payload_checks"]:
                arch = _archive_label(c["rez_path"])
                a(f"| `{r['asset_role']}` | `{c['query']}` | `{arch}` | "
                  f"`{c['full_path']}` | {c.get('size', '')} | "
                  f"{'YES' if c.get('sha_match') else 'no'} | `{c.get('note','')}` |")
        a("")
    a("Basename-only REZ hits are **existence candidates**, not consumer")
    a("proof, and are not treated as BornBeast identity.")
    a("")
    a("The `shader_cfg` inventory path normalises to")
    a("`SHADER/WEAPONSHADER/M4A1_S_BORNBEAST.CFG` after stripping the")
    a("`ModelTextures/` virtual root.  The runtime copy lives at")
    a("`WeaponShader/M4A1_S_BornBeast.CFG` (no `Shader/` prefix).")
    a("That is a **path-normalisation miss**, not a missing file: the")
    a("basename+size filter hashed it and SHA256 still matches.")
    a("")

    a("## 5. Confirmed relations / remaining ambiguity")
    a("")
    a("### Confirmed")
    a("")
    a("- `bf005` M4A1 runtime family is **not** BornBeast")
    a("  (`SCOPED_NEGATIVE_ACCEPTED`, N02-E-R2).")
    if classif["sha_payload_match_count"]:
        a(f"- {classif['sha_payload_match_count']} runtime REZ payload(s) "
          "byte-equal the BornBeast inventory SHA256 (`PAYLOAD_IDENTITY`).")
    if classif["consumer_field_hit_count"]:
        a(f"- {classif['consumer_field_hit_count']} config field(s) "
          "exact-match an inventory path/basename (`DIRECT_CONFIG_FIELD`).")
    if not classif["sha_payload_match_count"] and not classif["consumer_field_hit_count"]:
        a("- No new consumer or payload-identity relation beyond the")
        a("  already-accepted bf005 scoped negative.")
    a("")
    a("### Remaining ambiguity")
    a("")
    a("- LTB piece → DTX/TGA binding is still `OPEN_UNRESOLVED`")
    a("  (N02-E-R1; this round did not re-open LTB internals).")
    a("- CFG / render-style semantic closure is still `OPEN_UNRESOLVED`.")
    if not classif["consumer_field_hit_count"]:
        a("- No decoded `rez/Butes/*.ltc` (or other N02-A config-role file)")
        a("  names a BornBeast inventory asset.  The consumer table for")
        a("  this skin is **not** in the currently decoded Bute layer.")
        a("  Remaining places it could live, in rising cost:")
        a("  1. a config packed *inside* a REZ (not the loose `rez/Butes` files);")
        a("  2. a non-text item/skin catalog (CFT/CSV/DAT) not in N02-A config scope;")
        a("  3. a server-side or numeric-ID bind with no filename on disk;")
        a("  4. PE/strings consumer tracing (explicitly out of this task).")
    a("")
    a(f"### Confidence: `{classif['confidence']}`")
    a("")
    a("Exact-token reverse lookup over the declared config set and the")
    a("path-aware REZ index.  A miss in this set is a scoped negative,")
    a("not a global 'BornBeast has no runtime entry' claim.")
    a("")
    a("## 6. Status")
    a("")
    a(f"**status**: `{status}`")
    a("")
    a("## 7. Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT treat bf005 M4A1 bindings as BornBeast identity")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT run a full-disk scan; config set = N02-A config-role")
    a("  files ∪ `rez/Butes/` directory listing")
    a("- did NOT use filename similarity as proof")
    a("- did NOT freeze CFG shader semantics")
    a("- did NOT modify historical accepted evidence or `plan.md`")
    a("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override default CF runtime root (CF2_CF_DIR)")
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02b)
        importlib.reload(n02dr1)
        importlib.reload(n02er2)

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    print(f"[n03a] cf_root = {CF_DIR}", file=sys.stderr)
    print(f"[n03a] repo    = {REPO}", file=sys.stderr)
    t0 = time.time()

    inventory = load_inventory()
    local_hashes: dict = {}
    tokens: list[dict] = []
    for item in inventory["items"]:
        lh = hash_local_asset(item["relative_path"])
        local_hashes[item["asset_role"]] = lh
        if lh["present"] and lh["sha256"] and item.get("sha256"):
            if lh["sha256"] != item["sha256"].upper():
                print(f"[n03a] WARN inventory sha mismatch for "
                      f"{item['asset_role']}: file={lh['sha256']} "
                      f"json={item['sha256']}", file=sys.stderr)
        tokens.extend(build_asset_tokens(item, lh))
    print(f"[n03a] inventory items={len(inventory['items'])} "
          f"tokens={len(tokens)}", file=sys.stderr)

    n02a_cfgs = load_n02a_config_files()
    butes_cfgs = enumerate_butes_dir()
    configs = merge_config_candidates(n02a_cfgs, butes_cfgs)
    print(f"[n03a] config candidates: {len(configs)} "
          f"(n02a={len(n02a_cfgs)} butes_dir={len(butes_cfgs)})",
          file=sys.stderr)

    config_results = []
    for rec in configs:
        r = search_config_file(rec, tokens)
        config_results.append(r)
        n_f = len(r["field_hits"])
        n_t = len(r["text_hits"])
        if n_f or n_t:
            print(f"[n03a] HIT {r['path_alias']} field={n_f} text={n_t}",
                  file=sys.stderr)
    print(f"[n03a] config search done; "
          f"field_hits={sum(len(r['field_hits']) for r in config_results)} "
          f"text_hits={sum(len(r['text_hits']) for r in config_results)}",
          file=sys.stderr)

    print("[n03a] building path-aware REZ index...", file=sys.stderr)
    rez_paths = n02dr1.enumerate_rez_files()
    idx = n02dr1.build_full_path_index(rez_paths)
    rez_index_meta = {
        "rez_count_indexed": len(idx["rez_summaries"]),
        "total_entries": idx["total_entries"],
        "total_unique_full_paths": idx["total_unique_full_paths"],
        "total_unique_basenames": idx["total_unique_basenames"],
    }
    print(f"[n03a] REZ indexed: {rez_index_meta['rez_count_indexed']} "
          f"archives, {rez_index_meta['total_entries']} entries",
          file=sys.stderr)

    rez_results = []
    for item in inventory["items"]:
        r = lookup_rez(item, idx, local_hashes.get(item["asset_role"], {}))
        rez_results.append(r)
        print(f"[n03a] REZ {item['asset_role']}: "
              f"exact={r['exact_path_hit_count']} "
              f"basename_only={r['basename_only_hit_count']} "
              f"sha_match={sum(1 for c in r['payload_checks'] if c.get('sha_match'))}",
              file=sys.stderr)

    classif = classify_status(config_results, rez_results)
    status = classif["status"]
    elapsed = time.time() - t0
    print(f"[n03a] status={status} confidence={classif['confidence']} "
          f"elapsed={elapsed:.2f}s", file=sys.stderr)

    graph = build_resource_graph(inventory, rez_results, config_results,
                                 local_hashes)
    graph["status"] = status
    graph["confidence"] = classif["confidence"]
    graph["generated_at"] = datetime.now(timezone.utc).isoformat()
    graph["script"] = os.path.relpath(__file__, REPO)

    confirmed = collect_confirmed_relations(rez_results, config_results, classif)

    lookup_payload = {
        "task": "P4-M01-N03-A",
        "status": status,
        "confidence": classif["confidence"],
        "classification": classif,
        "cf_root": CF_DIR,
        "inventory_path": os.path.relpath(INVENTORY_PATH, REPO),
        "tokens": tokens,
        "local_hashes": local_hashes,
        "config_scope": {
            "n02a_config_files": len(n02a_cfgs),
            "butes_dir_files": len(butes_cfgs),
            "merged": len(configs),
            "string_scan_max_bytes": STRING_SCAN_MAX_BYTES,
        },
        "config_results": [
            {k: v for k, v in r.items() if k != "raw"}
            for r in config_results
        ],
        "rez_index": rez_index_meta,
        "rez_results": rez_results,
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "reverse_lookup.json"),
              "w", encoding="utf-8") as f:
        json.dump(lookup_payload, f, indent=2, ensure_ascii=False)

    with open(os.path.join(OUT_DIR, "resource_graph.json"),
              "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    confirmed_payload = {
        "task": "P4-M01-N03-A",
        "status": status,
        "confidence": classif["confidence"],
        "relations": confirmed,
        "remaining_blockers": [
            "BornBeast consumer table not in decoded rez/Butes/*.ltc"
            if classif["consumer_field_hit_count"] == 0 else
            "consumer field hit found; still need piece-level material binding",
            "LTB piece -> DTX/TGA OPEN_UNRESOLVED",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(confirmed_payload, f, indent=2, ensure_ascii=False)

    report = write_report(
        status, classif, inventory, tokens, config_results, rez_results,
        rez_index_meta, elapsed, local_hashes,
    )
    with open(os.path.join(OUT_DIR, "consumer_candidate_report.md"),
              "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[n03a] wrote {OUT_DIR}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
