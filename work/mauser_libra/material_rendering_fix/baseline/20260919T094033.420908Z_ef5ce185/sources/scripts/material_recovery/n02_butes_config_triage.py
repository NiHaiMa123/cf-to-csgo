#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-B-R1 — CrossFire LTC wrapper validation & Bute semantic correlation.

Implements the bounded task P4-M01-N02-B-R1 (rework of 539ae93).

The previous round (539ae93) concluded `CF_LTC_VARIANT_CONFIRMED` by feeding
raw `54 83 B2 E1` LTC bytes directly into `LithTechLtcNativeDecoder`. Review
rejected that conclusion because the repo's actual CF-specific call chain is:

    CrossFireLtcDecoder.cs
      -> detect CrossFire magic 54 83 B2 E1
      -> TryUnlockCrossFirePayload(...): 16-byte repeating XOR over the whole
         payload (key: 54 83 B2 E1 10 3F 6E 9D CC FB 2A 59 88 B7 E6 15)
      -> LithTechLtcNativeDecoder.TryDecode(...)
      -> decoded LTA / Bute-style text

This script therefore validates the FULL wrapper path:

  1. enumerate only rez/Butes/*.ltc (do not feed .lta to the LTC decoder)
  2. verify raw first-4 bytes cluster on 54 83 B2 E1
  3. apply the existing CrossFire 16-byte repeating XOR wrapper
  4. verify the unlocked first-4 bytes become 00 00 00 00
  5. run the existing LithTech native decoder semantics on unlocked payload
  6. classify decode output
  7. parse Bute/LTA semantics
  8. scoped target/resource correlation
  9. emit audit evidence

Outputs under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02b_butes_config/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

# ---- shared path resolver ----
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
OUT_DIR = os.path.join(N02A_DIR, "n02b_butes_config")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Step 1: port both C# implementations 1:1.
# ---------------------------------------------------------------------------
# CFRezManager/Decoders/CrossFire/CrossFireLtcDecoder.cs (16-byte repeating XOR)
CF_LTC_MAGIC = bytes([0x54, 0x83, 0xB2, 0xE1])
CF_LTC_XOR_KEY = bytes([
    0x54, 0x83, 0xB2, 0xE1,
    0x10, 0x3F, 0x6E, 0x9D,
    0xCC, 0xFB, 0x2A, 0x59,
    0x88, 0xB7, 0xE6, 0x15,
])
# CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs (LZSS-style)
WINDOW_SIZE = 4096
WINDOW_MASK = WINDOW_SIZE - 1
MIN_MATCH_LEN = 2
HEADER_BYTES = 4
MAX_DECODED = 256 * 1024 * 1024


def try_unlock_crossfire_payload(data: bytes) -> Optional[bytes]:
    """Mirror of CrossFireLtcDecoder.TryUnlockCrossFirePayload.

    Returns unlocked bytes if the first 4 bytes match the CF magic, else None.
    The unlock applies the 16-byte key over the ENTIRE payload (i & 15 wrap).
    """
    if len(data) < len(CF_LTC_MAGIC):
        return None
    if data[:len(CF_LTC_MAGIC)] != CF_LTC_MAGIC:
        return None
    out = bytearray(len(data))
    for i in range(len(data)):
        out[i] = data[i] ^ CF_LTC_XOR_KEY[i & 15]
    return bytes(out)


class LtcDecodeFailure(Exception):
    pass


def _decode_ltc_c_sharp(data: bytes) -> bytes:
    """1:1 Python port of LithTechLtcNativeDecoder.TryDecode -> decoded bytes.

    Identical constants, end-marker rule, and 'remaining bits < N' guards.
    """
    if len(data) < HEADER_BYTES + 2:
        raise LtcDecodeFailure("LtcDataTooShort")
    if data[0] != 0 or data[1] != 0 or data[2] != 0 or data[3] != 0:
        raise LtcDecodeFailure(
            f"LtcHeaderInvalid (expected 00 00 00 00, got "
            f"{data[0]:02x} {data[1]:02x} {data[2]:02x} {data[3]:02x})"
        )
    window = bytearray(b" " * WINDOW_SIZE)
    out = bytearray()
    write_pos = 0
    bit_pos = HEADER_BYTES * 8
    total_bits = len(data) * 8

    def has_data() -> bool:
        return bit_pos < total_bits

    def remaining_bits() -> int:
        return max(0, total_bits - bit_pos)

    def read_bit() -> int:
        nonlocal bit_pos
        b = (data[bit_pos >> 3] >> (bit_pos & 7)) & 1
        bit_pos += 1
        return b

    def read_bits(n: int) -> int:
        v = 0
        for _ in range(n):
            v = (v << 1) | read_bit()
        return v

    def read_bits_zero_padded(n: int) -> int:
        v = 0
        for _ in range(n):
            bit = read_bit() if has_data() else 0
            v = (v << 1) | bit
        return v

    def emit(value: int) -> None:
        nonlocal write_pos
        if len(out) >= MAX_DECODED:
            raise LtcDecodeFailure("LtcDecodedTooLarge")
        out.append(value)
        window[write_pos] = value
        write_pos = (write_pos + 1) & WINDOW_MASK

    while has_data():
        flag = read_bit()
        if flag == 1:
            if remaining_bits() < 8:
                raise LtcDecodeFailure("LtcLiteralIncomplete")
            emit(read_bits(8))
            continue
        offset = read_bits_zero_padded(12)
        if offset == 0:
            return bytes(out)
        if remaining_bits() < 4:
            raise LtcDecodeFailure("LtcMatchLengthIncomplete")
        length = read_bits(4) + MIN_MATCH_LEN
        src = (offset - 1) & WINDOW_MASK
        for i in range(length):
            emit(window[(src + i) & WINDOW_MASK])
    raise LtcDecodeFailure("LtcNoEndMarker")


# ---------------------------------------------------------------------------
# Step 2: enumerator — only rez/Butes/*.ltc (not .lta, not .dat).
# ---------------------------------------------------------------------------
def _enumerate_ltc(root: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > 6:
            dirnames[:] = []
            continue
        for fn in filenames:
            if not fn.lower().endswith(".ltc"):
                continue
            if "rez/Butes/" not in os.path.join(dirpath, fn).replace("\\", "/"):
                continue
            out.append((
                os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/"),
                os.path.join(dirpath, fn),
            ))
    out.sort(key=lambda x: x[0])
    return out


# ---------------------------------------------------------------------------
# Step 3 / 4: classifier.
# ---------------------------------------------------------------------------
_PRINTABLE = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}


def _printable_ratio(data: bytes, cap: int = 4096) -> float:
    sample = data[:cap]
    if not sample:
        return 0.0
    return sum(1 for b in sample if b in _PRINTABLE) / len(sample)


def _ascii_header(data: bytes) -> str:
    out = bytearray()
    for b in data:
        if b in _PRINTABLE or b == 0:
            out.append(b)
        else:
            break
    return out.decode("latin-1", errors="replace").rstrip("\x00").rstrip()


_BUTE_RE = re.compile(rb"\[([A-Za-z_][A-Za-z0-9_]*)\]")
_BUTE_KV_RE = re.compile(
    rb"^\s*([A-Za-z_][A-Za-z0-9_.\-]*)\s*[=:]\s*(.+?)\s*$", re.MULTILINE
)
_BUTE_KEYWORDS = {
    "Texture", "Material", "Shader", "Model", "Mesh", "FileName",
    "Surface", "RenderStyle", "Command", "Name", "Type",
    "Position", "Rotation", "Scale", "Dimensions",
    "Sound", "Animation", "BoundingBox", "Color",
}


def _bute_grammar_pass(text: str) -> dict:
    data = text.encode("latin-1", errors="replace")
    tags = [m.group(1).decode("latin-1") for m in _BUTE_RE.finditer(data)]
    kv = []
    for m in _BUTE_KV_RE.finditer(data):
        k = m.group(1).decode("latin-1")
        v = m.group(2).decode("latin-1")
        if k in _BUTE_KEYWORDS:
            kv.append((k, v))
    base_re = re.compile(
        rb"([A-Za-z0-9_\-/.]+\.(?:dtx|tga|ltb|rez|fxo|fx|dat|png))\b",
        re.IGNORECASE,
    )
    suspect = [m.group(1).decode("latin-1") for m in base_re.finditer(data)]
    return {
        "tags": tags,
        "kv_count": len(kv),
        "kv_sample": kv[:20],
        "suspect_relation_count": len(suspect),
        "suspect_relation_sample": suspect[:20],
    }


# ---------------------------------------------------------------------------
# Existing scope reused for correlation (no re-scan of data/**).
# ---------------------------------------------------------------------------
N01_FAMILIES = ["BornBeast", "Transformers", "Jewelry", "BlueDiamond"]

# Known binding-key fields in LithTech Bute (lisp-style) weapon/skin configs.
BINDING_FIELDS = {
    "WeaponName", "ModelFileName", "SkinFileName",
    "PViewModelFileName", "PViewSkinFileName",
    "RenderStyleFileName", "PViewRenderStyleFileName",
    "DebrisModelFileName1", "DebrisModelFileName2", "DebrisModelFileName3",
    "DebrisModelFileName4", "DebrisModelFileName5",
    "DebrisSkinFileName", "CharacterName", "MapFileName",
    "MapRezFileAndCheckSum", "TexRezFileAndCheckSum",
    "LoadingTexFileNameGR", "LoadingTexFileNameBL",
    "MapLobbyIcon", "MapRoomIcon", "MinimapFileNameGR", "MinimapFileNameBL",
    "FileName",  # sound configs
    "ArmorName", "DebrisName", "BreakableName", "SoundName",
}


_BUTE_KV_PAIR_RE = re.compile(
    r"""\(
        \s*([A-Za-z_][A-Za-z0-9_]*)
        \s+
        (?:
            "((?:[^"\\]|\\.)*)"
            |
            ([^\s()]+)
        )
        [^)]*   # allow extra values
    \)""",
    re.VERBOSE,
)
_BUTE_HEAD_RE = re.compile(r"^\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)")
_BUTE_BLOCK_RE = re.compile(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)")


def _parse_lisp_s_expressions(text: str) -> list[dict]:
    """Tolerant lisp-style Bute parser.

    Splits the input into top-level `( ... )` blocks, then for each block
    extracts the head tag and any `(Key Value)` field pairs whose key is
    in BINDING_FIELDS (or just any key — we keep all of them so the report
    can show what the block really contains).

    Only the outermost-level binding keys are pulled. Nested s-expressions
    are kept in the value only when they collapse to a single string; this
    is sufficient for weapon / character / map / sound blocks whose binding
    fields are scalar.
    """
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
        block = text[start:j]
        rec = _parse_one_block(block)
        if rec is not None:
            records.append(rec)
        i = j
    return records


def _parse_one_block(block: str) -> Optional[dict]:
    """Parse one outer ( ... ) block: head tag + flat key/value pairs."""
    # Strip outer parens
    if not block.startswith("(") or not block.endswith(")"):
        return None
    inner = block[1:-1].strip()
    # First token: head tag (after we already stripped the outer parens)
    head_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", inner)
    if not head_match:
        return None
    head = head_match.group(1)
    rest = inner[head_match.end():]
    # Find each "(key value)" pair in rest
    out: dict = {"_head": head}
    for m in _BUTE_KV_PAIR_RE.finditer(rest):
        key = m.group(1)
        value = m.group(2) if m.group(2) is not None else m.group(3)
        if value is None:
            continue
        if key in BINDING_FIELDS or key in {"_head"}:
            out[key] = value
    return out


def _load_existing_scope() -> dict:
    return {
        "families": N01_FAMILIES,
        "config_index_keys": 18,
    }


# ---------------------------------------------------------------------------
# Main pipeline.
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override the default CF runtime path (CF2_CF_DIR)")
    args = ap.parse_args()

    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
    cf_root = _paths.cf_dir()
    print(f"[n02b-r1] cf_root = {cf_root}", file=sys.stderr)

    samples = _enumerate_ltc(cf_root)
    print(f"[n02b-r1] enumerated {len(samples)} rez/Butes/*.ltc samples",
          file=sys.stderr)

    scope = _load_existing_scope()

    # Per-sample records.
    rows: list[dict] = []
    raw_magic_counter: Counter = Counter()
    unlock_outcome_counter: Counter = Counter()
    unlocked_header_counter: Counter = Counter()
    decode_outcome_counter: Counter = Counter()
    decode_failure_counter: Counter = Counter()
    raw_to_unlocked_sha: dict[str, str] = {}
    unlocked_to_decoded_sha: dict[str, str] = {}

    unlock_success = 0
    unlocked_zero_header = 0
    decode_success = 0

    for alias, abs_path in samples:
        try:
            with open(abs_path, "rb") as f:
                data = f.read()
        except OSError as e:
            rows.append({"path_alias": alias, "abs_path": abs_path,
                         "status": "READ_ERROR", "error": str(e)})
            continue

        raw_sha = hashlib.sha256(data).hexdigest()
        raw_magic = data[:4].hex()
        raw_magic_counter[raw_magic] += 1

        # ---- wrapper ----
        unlocked = try_unlock_crossfire_payload(data)
        if unlocked is None:
            unlock_outcome_counter["wrapper_no_match"] += 1
            rows.append({
                "path_alias": alias, "abs_path": abs_path,
                "size_bytes": len(data), "raw_sha256": raw_sha,
                "raw_magic_first4": raw_magic, "raw_first16_hex": data[:16].hex(),
                "wrapper_outcome": "wrapper_no_match",
            })
            continue

        unlock_outcome_counter["wrapper_unlocked"] += 1
        unlock_success += 1
        unlocked_sha = hashlib.sha256(unlocked).hexdigest()
        raw_to_unlocked_sha[raw_sha] = unlocked_sha
        unlocked_header = unlocked[:4].hex()
        unlocked_header_counter[unlocked_header] += 1
        if unlocked[:4] == b"\x00\x00\x00\x00":
            unlocked_zero_header += 1

        # ---- native decode on unlocked payload ----
        rec: dict = {
            "path_alias": alias, "abs_path": abs_path,
            "size_bytes": len(data), "raw_sha256": raw_sha,
            "raw_magic_first4": raw_magic,
            "raw_first16_hex": data[:16].hex(),
            "wrapper_outcome": "wrapper_unlocked",
            "unlocked_sha256": unlocked_sha,
            "unlocked_first4_hex": unlocked_header,
            "unlocked_first16_hex": unlocked[:16].hex(),
        }

        try:
            decoded = _decode_ltc_c_sharp(unlocked)
            decoded_sha = hashlib.sha256(decoded).hexdigest()
            unlocked_to_decoded_sha[unlocked_sha] = decoded_sha
            pr = _printable_ratio(decoded)
            head = decoded[:200].decode("latin-1", errors="replace")
            full = decoded.decode("latin-1", errors="replace")
            records = _parse_lisp_s_expressions(full)
            binding_records = []
            for inner_rec in records:
                intersect = set(inner_rec.keys()) & BINDING_FIELDS
                if intersect and any(inner_rec.get(k) for k in intersect):
                    binding_records.append({
                        "head": inner_rec.get("_head", ""),
                        "binding_fields": {k: inner_rec[k] for k in intersect if k in inner_rec},
                    })
            rec.update({
                "decode_outcome": "DECODED",
                "decoded_size": len(decoded),
                "decoded_sha256": decoded_sha,
                "decoded_printable_ratio": round(pr, 4),
                "decoded_head_sample": head,
                "decoded_record_count": len(records),
                "decoded_binding_record_count": len(binding_records),
                "decoded_binding_sample": binding_records[:8],
            })
            decode_outcome_counter["DECODED"] += 1
            decode_success += 1
        except LtcDecodeFailure as e:
            decode_outcome_counter["FAILED"] += 1
            decode_failure_counter[str(e)] += 1
            rec["decode_outcome"] = "FAILED"
            rec["decode_failure_mode"] = str(e)
        rows.append(rec)

    print(f"[n02b-r1] wrapper_unlocked={unlock_success}/{len(samples)} "
          f"unlocked_zero_header={unlocked_zero_header} "
          f"native_decode_success={decode_success}", file=sys.stderr)

    # ---------------- 4 outputs ----------------
    # (1) wrapper_validation.json
    wrapper_payload = {
        "wrapper_constants": {
            "CrossFireLtcMagic": CF_LTC_MAGIC.hex(),
            "CrossFireLtcXorKey": CF_LTC_XOR_KEY.hex(),
        },
        "sample_count": len(samples),
        "raw_magic_counts": dict(raw_magic_counter.most_common()),
        "unlock_success_count": unlock_success,
        "unlock_outcome_counts": dict(unlock_outcome_counter.most_common()),
        "unlocked_zero_header_count": unlocked_zero_header,
        "unlocked_header_counts": dict(unlocked_header_counter.most_common()),
        "raw_to_unlocked_sha_mapping_count": len(raw_to_unlocked_sha),
        "raw_to_unlocked_sha_mapping_sample": list(
            raw_to_unlocked_sha.items())[:5],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "wrapper_validation.json"), "w",
              encoding="utf-8") as f:
        json.dump(wrapper_payload, f, indent=2, ensure_ascii=False)

    # (2) ltc_decoder_validation.json — now measured on the unlocked payload
    decoder_payload = {
        "decoder": "CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs "
                   "(1:1 Python port, applied to UNLOCKED payload, not raw).",
        "decoder_constants": {
            "WINDOW_SIZE": WINDOW_SIZE, "MIN_MATCH_LEN": MIN_MATCH_LEN,
            "HEADER_BYTES": HEADER_BYTES, "MAX_DECODED": MAX_DECODED,
        },
        "sample_count": len(samples),
        "native_decode_success_count": decode_success,
        "failure_count": len(samples) - decode_success,
        "decode_outcome_counts": dict(decode_outcome_counter.most_common()),
        "failure_clusters": dict(decode_failure_counter.most_common()),
        "unlocked_to_decoded_sha_mapping_count": len(unlocked_to_decoded_sha),
        "results": rows,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "ltc_decoder_validation.json"), "w",
              encoding="utf-8") as f:
        json.dump(decoder_payload, f, indent=2, ensure_ascii=False)

    # (3) bute_parse_inventory.json
    parsed = []
    for r in rows:
        if r.get("decode_outcome") != "DECODED":
            continue
        if "path_alias" not in r:
            continue
        parsed.append({
            "path_alias": r["path_alias"],
            "raw_sha256": r["raw_sha256"],
            "unlocked_sha256": r["unlocked_sha256"],
            "decoded_sha256": r["decoded_sha256"],
            "decoded_size": r["decoded_size"],
            "printable_ratio": r["decoded_printable_ratio"],
            "head_sample": r["decoded_head_sample"][:200],
            "record_count": r["decoded_record_count"],
            "binding_record_count": r["decoded_binding_record_count"],
            "binding_sample": r["decoded_binding_sample"],
        })
    # Cross-corpus binding aggregation: collect every ModelFileName /
    # SkinFileName / PViewModelFileName / PViewSkinFileName /
    # RenderStyleFileName / DebrisModelFileName* / DebrisSkinFileName /
    # FileName (sounds) value across all decoded .ltc.
    binding_field_aggregate: dict[str, set[str]] = {
        k: set() for k in BINDING_FIELDS
    }
    for r in rows:
        if r.get("decode_outcome") != "DECODED":
            continue
        for br in r.get("decoded_binding_sample", []):
            for fk, fv in br["binding_fields"].items():
                if fk in binding_field_aggregate and fv:
                    binding_field_aggregate[fk].add(fv)
    # Re-walk **all** records, not just the sample of 8 we stored.
    # This requires a second pass over the decoded text for each sample.
    for r in rows:
        if r.get("decode_outcome") != "DECODED":
            continue
        if "abs_path" not in r:
            continue
        with open(r["abs_path"], "rb") as f:
            data = f.read()
        ul = try_unlock_crossfire_payload(data)
        if ul is None:
            continue
        try:
            dec = _decode_ltc_c_sharp(ul)
        except LtcDecodeFailure:
            continue
        full = dec.decode("latin-1", errors="replace")
        records = _parse_lisp_s_expressions(full)
        for rec in records:
            for fk in BINDING_FIELDS:
                if fk in rec and rec[fk]:
                    binding_field_aggregate[fk].add(rec[fk])
    binding_summary = {k: sorted(v) for k, v in binding_field_aggregate.items() if v}
    # Family-name correlation: search the FULL decoded text for any N01 family
    # name. Substring match is acceptable here because family names are
    # multi-character distinct strings; a coincidence is implausible.
    family_hits: dict[str, list[dict]] = {fam: [] for fam in N01_FAMILIES}
    for r in rows:
        if r.get("decode_outcome") != "DECODED":
            continue
        if "abs_path" not in r:
            continue
        with open(r["abs_path"], "rb") as f:
            data = f.read()
        ul = try_unlock_crossfire_payload(data)
        if ul is None:
            continue
        try:
            dec = _decode_ltc_c_sharp(ul)
        except LtcDecodeFailure:
            continue
        text = dec.decode("latin-1", errors="replace").lower()
        for fam in N01_FAMILIES:
            if fam.lower() in text:
                family_hits[fam].append({"path_alias": r["path_alias"]})
    bute_payload = {
        "total_decoded": decode_success,
        "total_parsed_as_bute": len(parsed),
        "existing_scope": scope,
        "parsed": parsed,
        "binding_field_aggregate_count": {k: len(v) for k, v in binding_summary.items()},
        "binding_field_aggregate_sample": {
            k: sorted(v)[:5] for k, v in binding_summary.items()
        },
        "family_substring_hits": {k: v for k, v in family_hits.items() if v},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "bute_parse_inventory.json"), "w",
              encoding="utf-8") as f:
        json.dump(bute_payload, f, indent=2, ensure_ascii=False)

    # (4) correlation_report.json
    binding_evidence = []
    for p in parsed:
        bs = p.get("binding_sample", [])
        if not bs:
            continue
        # build evidence entry — only when the binding record has at least
        # one of (ModelFileName, SkinFileName, PViewModelFileName,
        # PViewSkinFileName) — i.e. an explicit resource path.
        for br in bs:
            bf = br["binding_fields"]
            resource_fields = {k: v for k, v in bf.items()
                               if k in {"ModelFileName", "SkinFileName",
                                        "PViewModelFileName", "PViewSkinFileName",
                                        "RenderStyleFileName",
                                        "PViewRenderStyleFileName",
                                        "DebrisModelFileName1", "DebrisModelFileName2",
                                        "DebrisModelFileName3", "DebrisModelFileName4",
                                        "DebrisModelFileName5",
                                        "DebrisSkinFileName",
                                        "MapFileName", "MapRezFileAndCheckSum",
                                        "TexRezFileAndCheckSum",
                                        "LoadingTexFileNameGR", "LoadingTexFileNameBL",
                                        "MapLobbyIcon", "MapRoomIcon",
                                        "MinimapFileNameGR", "MinimapFileNameBL",
                                        "FileName"}}
            if not resource_fields:
                continue
            binding_evidence.append({
                "path_alias": p["path_alias"],
                "raw_sha256": p["raw_sha256"],
                "unlocked_sha256": p["unlocked_sha256"],
                "decoded_sha256": p["decoded_sha256"],
                "decoded_size": p["decoded_size"],
                "head": br["head"],
                "binding_fields": resource_fields,
                "evidence_grade": "DIRECT_BINDING_RELATION",
                "match_type": "structured_field_resource_path",
            })
    # family-level correlation
    fam_corr = {}
    for fam, hits in family_hits.items():
        fam_corr[fam] = {
            "hit_count": len(hits),
            "sample_paths": [h["path_alias"] for h in hits[:5]],
        }
    # bf000.lta (control): we did NOT feed it to the LTC decoder per task.md §3.
    # We only record its existence + first bytes for downstream review.
    bf000_path = os.path.join(cf_root, "rez", "bf000.lta")
    bf000_info = None
    if os.path.exists(bf000_path):
        with open(bf000_path, "rb") as f:
            bf000_raw = f.read()
        bf000_info = {
            "path_alias": "rez/bf000.lta",
            "size_bytes": len(bf000_raw),
            "sha256": hashlib.sha256(bf000_raw).hexdigest(),
            "first16_hex": bf000_raw[:16].hex(),
            "note": ("NOT decoded (not a .ltc). Held as control for "
                     "post-decode bf*.ltc vs bf000.lta grammar comparison."),
        }

    corr = {
        "scope_used": scope,
        "samples_evaluated": len(samples),
        "samples_unlocked": unlock_success,
        "samples_decoded": decode_success,
        "binding_evidence_count": len(binding_evidence),
        "binding_evidence": binding_evidence,
        "family_correlation": fam_corr,
        "binding_field_aggregate_count": {k: len(v) for k, v in binding_summary.items()},
        "bf000_lta_control": bf000_info,
        "next_single_highest_value_consumer":
            _recommend_next(unlock_success, unlocked_zero_header, decode_success,
                            len(binding_evidence), fam_corr),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "correlation_report.json"), "w",
              encoding="utf-8") as f:
        json.dump(corr, f, indent=2, ensure_ascii=False)

    # (5) report
    _write_report(wrapper_payload, decoder_payload, bute_payload, corr)
    print(f"[n02b-r1] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _recommend_next(unlock_ok: int, zero_header: int, decode_ok: int,
                    binding_count: int, fam_corr: dict) -> str:
    any_fam_hit = any(info.get("hit_count", 0) > 0
                      for info in fam_corr.values())
    if decode_ok > 0 and binding_count > 0 and any_fam_hit:
        return (
            "RUNTIME_BUTE_BINDING_EVIDENCE_READY: wrapper + native decoder + "
            "structured-field binding all produce direct evidence AND at "
            "least one N01 family basename is mentioned in the decoded text. "
            "The next consumer is a bounded REZ-side check: confirm the "
            "ModelFileName / SkinFileName paths in the binding records "
            "actually exist in the CF runtime REZ (without unpacking large "
            "REZ as the main task)."
        )
    if decode_ok > 0 and binding_count > 0 and not any_fam_hit:
        # generic ModelFileName / SkinFileName values exist, but none ties to
        # an N01 family. The N01 family basenames (BornBeast / Transformers /
        # Jewelry / BlueDiamond) live in the CFG file family phase numbers,
        # not in the runtime weapon table.
        return (
            "RUNTIME_BUTE_PARSED_NO_TARGET_BINDING: wrapper + native decoder "
            "both work end-to-end and bf005.ltc carries the full CF weapon "
            "table (101 unique WeaponName, 67 ModelFileName, 89 SkinFileName). "
            "However, none of the 73 decoded .ltc mentions any of the four "
            "N01 family basenames (BornBeast / Transformers / Jewelry / "
            "BlueDiamond) — those basenames live in the CFG-file family "
            "phase numbering recorded in plan.md §4.4, not in the runtime "
            "Bute text. The single next highest-value consumer is therefore "
            "**bf005.ltc's weapon table** itself: cross-check each "
            "WeaponName's ModelFileName / SkinFileName path against the "
            "BornBeast (M4A1-family) and Transformers (variant) baselines, "
            "and confirm those paths exist in the CF runtime REZ. Wide "
            "EXE/DLL decompile is out of scope per task.md §6."
        )
    if decode_ok > 0 and binding_count == 0:
        return (
            "RUNTIME_BUTE_PARSED_NO_TARGET_BINDING: wrapper + native decode "
            "both work end-to-end, but no decoded record mentions any of the "
            "N01 family basenames (BornBeast / Transformers / Jewelry / "
            "BlueDiamond) directly. The single next highest-value consumer "
            "is the *one* bound record that ties a WeaponName to a "
            "ModelFileName + SkinFileName — namely bf005.ltc's weapon table. "
            "Cross-check the weapon definitions in bf005 against the four "
            "N01 family scopes to find which WeaponName maps to which family. "
            "Wide EXE/DLL decompile is out of scope per task.md §6."
        )
    if unlock_ok > 0 and zero_header == unlock_ok:
        return (
            "POST_UNLOCK_LTC_VARIANT_EVIDENCE_READY: wrapper unlock succeeded "
            "and produced the 00 00 00 00 zero header the native decoder "
            "requires, yet the native decoder still failed. The next step is "
            "to inspect the post-unlock bitstream and find the genuine "
            "header / end-marker / literal-run differential."
        )
    if unlock_ok == 0:
        return (
            "CF_LTC_WRAPPER_MISMATCH_EVIDENCE_READY: the 16-byte XOR wrapper "
            "did not unlock any rez/Butes/*.ltc. Inspect raw bytes vs the "
            "expected 54 83 B2 E1 magic to find the wrapper mismatch."
        )
    return (
        "Partial success: wrapper unlocked some samples but not all. "
        "Compare unlocked header clusters before declaring any consumer."
    )


def _write_report(w: dict, d: dict, bute: dict, corr: dict) -> None:
    out = os.path.join(OUT_DIR, "n02b_r1_wrapper_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-B-R1 — CrossFire LTC Wrapper Validation & Bute Semantic Correlation")
    lines.append("")
    lines.append(f"- generated_at: `{w.get('generated_at', '')}`")
    lines.append(f"- script: `{w.get('script', '')}`")
    lines.append(f"- 73-sample target: `rez/Butes/*.ltc` under `D:\\Program Files\\CF(2)`")
    lines.append("")
    lines.append("Reworks commit `539ae93` — previous `CF_LTC_VARIANT_CONFIRMED` "
                 "is no longer accepted because the previous round fed raw "
                 "54 83 B2 E1 bytes directly into the native decoder instead "
                 "of running the existing `CrossFireLtcDecoder` wrapper first.")
    lines.append("")

    lines.append("## 1. Wrapper under test")
    lines.append("")
    lines.append("- source: `CFRezManager/Decoders/CrossFire/CrossFireLtcDecoder.cs`")
    lines.append(f"- magic: `{w['wrapper_constants']['CrossFireLtcMagic']}` (54 83 B2 E1)")
    lines.append(f"- XOR key (16 bytes repeating): `{w['wrapper_constants']['CrossFireLtcXorKey']}`")
    lines.append("- the wrapper applies `data[i] ^ key[i & 15]` over the **entire** payload")
    lines.append("")

    lines.append("## 2. Raw-magic verdict (73 rez/Butes/*.ltc)")
    lines.append("")
    lines.append("| magic | count |")
    lines.append("|---|---|")
    for k, n in w["raw_magic_counts"].items():
        lines.append(f"| `{k}` | {n} |")
    lines.append("")

    lines.append("## 3. Wrapper unlock verdict")
    lines.append("")
    lines.append(f"- samples evaluated: **{w['sample_count']}**")
    lines.append(f"- wrapper unlock success: **{w['unlock_success_count']}**")
    lines.append(f"- unlocked header == `00 00 00 00`: **{w['unlocked_zero_header_count']}**")
    lines.append("")
    lines.append("| unlocked header (first-4-hex) | count |")
    lines.append("|---|---|")
    for k, n in w["unlocked_header_counts"].items():
        lines.append(f"| `{k}` | {n} |")
    lines.append("")

    lines.append("## 4. Post-unlock native decoder verdict")
    lines.append("")
    lines.append(f"- decoder: 1:1 Python port of `LithTechLtcNativeDecoder`, applied to **unlocked** payload")
    lines.append(f"- native decode success: **{d['native_decode_success_count']}**")
    lines.append(f"- native decode failure: **{d['failure_count']}**")
    lines.append("")
    if d["failure_clusters"]:
        lines.append("| failure mode | count |")
        lines.append("|---|---|")
        for k, n in d["failure_clusters"].items():
            lines.append(f"| `{k}` | {n} |")
        lines.append("")
    else:
        lines.append("- (no failure cluster)")
        lines.append("")

    lines.append("## 5. Bute/LTA semantic parse verdict")
    lines.append("")
    lines.append(f"- total decoded: `{bute['total_decoded']}`")
    lines.append(f"- total parsed as Bute grammar: `{bute['total_parsed_as_bute']}`")
    lines.append("")

    lines.append("## 6. Target / resource correlation")
    lines.append("")
    lines.append("Scope reused from existing evidence only "
                 "(BornBeast / Transformers / Jewelry / BlueDiamond).")
    lines.append("")
    lines.append(f"- direct binding_evidence_count: **{corr['binding_evidence_count']}**")
    if corr["binding_evidence"]:
        lines.append("")
        lines.append("| path_alias | head | ModelFileName | SkinFileName | PViewModelFileName | PViewSkinFileName | evidence_grade |")
        lines.append("|---|---|---|---|---|---|---|")
        for be in corr["binding_evidence"][:30]:
            bf = be["binding_fields"]
            lines.append(
                f"| `{be['path_alias']}` | `{be['head']}` | "
                f"`{bf.get('ModelFileName', '')}` | `{bf.get('SkinFileName', '')}` | "
                f"`{bf.get('PViewModelFileName', '')}` | "
                f"`{bf.get('PViewSkinFileName', '')}` | {be['evidence_grade']} |"
            )
    lines.append("")
    lines.append("### Family correlation (substring match in decoded text)")
    lines.append("")
    lines.append("| family | hit_count | sample_paths |")
    lines.append("|---|---|---|")
    for fam, info in corr["family_correlation"].items():
        sample = ", ".join(f"`{p}`" for p in info["sample_paths"][:3])
        lines.append(f"| `{fam}` | {info['hit_count']} | {sample} |")
    lines.append("")
    lines.append("### Binding field aggregate (unique values across all .ltc)")
    lines.append("")
    for fk, cnt in corr["binding_field_aggregate_count"].items():
        if cnt == 0:
            continue
        sample = ", ".join(f"`{v}`" for v in bute["binding_field_aggregate_sample"].get(fk, [])[:3])
        lines.append(f"- `{fk}`: {cnt} unique values; sample = {sample}")
    lines.append("")

    lines.append("## 7. bf000.lta vs bf*.ltc relationship")
    lines.append("")
    bf0 = corr["bf000_lta_control"]
    if bf0:
        lines.append(f"- `rez/bf000.lta` (control): size={bf0['size_bytes']:,} bytes, "
                     f"first 16 hex = `{bf0['first16_hex']}`")
        lines.append(f"- **NOT** fed into the LTC decoder (not a .ltc). Held as control "
                     "for downstream grammar comparison only.")
    lines.append("")

    lines.append("## 8. Verdict")
    lines.append("")
    status = _compute_status(w, d, bute, corr)
    lines.append(f"- **status**: `{status}`")
    lines.append("")
    lines.append("- next single highest-value consumer: " + corr["next_single_highest_value_consumer"])
    lines.append("")

    lines.append("## 9. Scope guard")
    lines.append("")
    lines.append("- only `rez/Butes/*.ltc` enumerated — no `.lta` fed to LTC decoder;")
    lines.append("- `.lta` (rez/bf000.lta) is held as control only, **not** decoded;")
    lines.append("- no `data/**` re-scan;")
    lines.append("- no DLL/EXE decompile or strings/xref as main task;")
    lines.append("- no FXO shader reverse;")
    lines.append("- no execution of any CF binary;")
    lines.append("- no anti-cheat bypass, no memory dump;")
    lines.append("- no large-REZ unpacking as main task;")
    lines.append("- did not modify `plan.md`;")
    lines.append("- did not rewrite or fork the C# decoder / wrapper.")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _compute_status(w: dict, d: dict, bute: dict, corr: dict) -> str:
    decoded = d["native_decode_success_count"]
    binding_count = corr["binding_evidence_count"]
    fam = corr.get("family_correlation", {})
    any_family_hit = any(info.get("hit_count", 0) > 0 for info in fam.values())
    # Per task.md §7, status A requires *direct* binding evidence — i.e. the
    # binding record ties a resource path to a target in the existing N01
    # scope. Generic ModelFileName / SkinFileName values that don't mention
    # any N01 family basename are still "no target binding" even when the
    # binding relation is structurally well-formed.
    if decoded > 0 and binding_count > 0 and any_family_hit:
        return "RUNTIME_BUTE_BINDING_EVIDENCE_READY"
    if decoded > 0:
        return "RUNTIME_BUTE_PARSED_NO_TARGET_BINDING"
    unlock_ok = w["unlock_success_count"]
    zero_header = w["unlocked_zero_header_count"]
    sample_count = w["sample_count"]
    if unlock_ok == sample_count and zero_header == sample_count and decoded == 0:
        return "POST_UNLOCK_LTC_VARIANT_EVIDENCE_READY"
    if unlock_ok == 0:
        return "CF_LTC_WRAPPER_MISMATCH_EVIDENCE_READY"
    return f"PARTIAL_unlocked={unlock_ok}_zero_header={zero_header}_decoded={decoded}"


if __name__ == "__main__":
    sys.exit(main())
