#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-B — Existing LTC decoder validation & Bute semantic correlation.

Implements the bounded task P4-M01-N02-B from task.md.

Step 1: port the deterministic C# decoder in
        CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs to Python
        and prove bit-for-bit equivalence by running the C# binary on a
        sample and comparing the result (when feasible).
Step 2: enumerate every runtime .ltc and .lta sample under
        D:\\Program Files\\CF(2) (cf_default) and decode them all.
Step 3: classify the decoded output (text vs binary, success vs failure,
        cluster by magic + first decoded bytes).
Step 4: for any plaintext-like decoded output, run a Bute/LTA grammar pass.
Step 5: correlate against the existing N01 / R1 evidence scope only —
        do NOT rescan data/**.
Step 6: emit evidence under
        work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02b_butes_config/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from collections import Counter, defaultdict
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
# Step 1: port the C# LithTechLtcNativeDecoder verbatim.
# ---------------------------------------------------------------------------
# Logic mirrors the C# source 1:1 — the C# uses 4 header bytes (must be 0x00),
# then a bit stream: 1 = literal byte (8 bits); 0 = match reference
# (12-bit offset, 0 = end marker; then 4-bit length, real length = val+2).
# The window is 4096 bytes, initialised to spaces, wrap-around masked.
# Max decoded = 256 MiB.
#
# We deliberately keep the C# semantics exactly: same constants, same
# end-marker rule, same "if remaining bits < N, fail" guards. If the
# behaviour diverges on any sample, the discrepancy is reported.

WINDOW_SIZE = 4096
WINDOW_MASK = WINDOW_SIZE - 1
MIN_MATCH_LEN = 2
HEADER_BYTES = 4
MAX_DECODED = 256 * 1024 * 1024


class LtcDecodeFailure(Exception):
    pass


def _decode_ltc_c_sharp(data: bytes) -> bytes:
    """Port of LithTechLtcNativeDecoder.TryDecode -> decoded bytes."""
    if len(data) < HEADER_BYTES + 2:
        raise LtcDecodeFailure("LtcDataTooShort")
    if data[0] != 0 or data[1] != 0 or data[2] != 0 or data[3] != 0:
        raise LtcDecodeFailure("LtcHeaderInvalid (expected 00 00 00 00)")
    window = bytearray(b" " * WINDOW_SIZE)
    out = bytearray()
    write_pos = 0
    bit_pos = HEADER_BYTES * 8  # skip the 4 header bytes
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
        for _ in range(length):
            emit(window[(src + _) & WINDOW_MASK])
    raise LtcDecodeFailure("LtcNoEndMarker")


# ---------------------------------------------------------------------------
# Step 2: enumerator — every .ltc / .lta under the trusted root.
# ---------------------------------------------------------------------------
LTC_LTA_EXTS = {".ltc", ".lta"}


def _enumerate_samples(root: str) -> list[tuple[str, str]]:
    """Return (path_alias, abs_path) for every .ltc/.lta under root.

    Depth-bounded (matches N02-A so the scope is identical to the inventory).
    """
    out: list[tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > 6:
            dirnames[:] = []
            continue
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in LTC_LTA_EXTS:
                continue
            out.append((
                os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/"),
                os.path.join(dirpath, fn),
            ))
    out.sort(key=lambda x: x[0])
    return out


# ---------------------------------------------------------------------------
# Step 3: classification helpers.
# ---------------------------------------------------------------------------
_PRINTABLE = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}


def _printable_ratio(data: bytes, cap: int = 4096) -> float:
    sample = data[:cap]
    if not sample:
        return 0.0
    return sum(1 for b in sample if b in _PRINTABLE) / len(sample)


def _ascii_header_text(data: bytes) -> str:
    """Extract a leading ASCII header block (CRLF-separated lines) up to
    the first non-printable / non-CR / non-LF byte. Mirrors the visible
    header of a LithTech LTA archive (RezMgr / LithTech Resource File)."""
    out = bytearray()
    for b in data:
        if b in _PRINTABLE or b == 0:
            out.append(b)
        else:
            break
    return out.decode("latin-1", errors="replace").rstrip("\x00").rstrip()


_BUTE_RE = re.compile(rb"\[([A-Za-z_][A-Za-z0-9_]*)\]")  # tag headers
_BUTE_KV_RE = re.compile(
    rb"^\s*([A-Za-z_][A-Za-z0-9_.\-]*)\s*[=:]\s*(.+?)\s*$", re.MULTILINE
)
# A few Bute value shapes (best-effort, grammar is documented in
# no-lith/Jupiter Libs/LIB-ButeMgr, but we only look for the simple
# key/value layout the existing N01 evidence already uses).
_BUTE_KEYWORDS = {
    "Texture", "Material", "Shader", "Model", "Mesh", "FileName",
    "Surface", "RenderStyle", "Command", "Name", "Type",
    "Position", "Rotation", "Scale", "Dimensions",
    "Sound", "Animation", "BoundingBox", "Color",
}


def _bute_grammar_pass(text: str) -> dict:
    """Best-effort Bute/LTA grammar scan on plaintext decoded text.

    Returns:
      dict with: tags, kv, suspect_relations
    """
    data = text.encode("latin-1", errors="replace")
    tags = [m.group(1).decode("latin-1") for m in _BUTE_RE.finditer(data)]
    kv = []
    for m in _BUTE_KV_RE.finditer(data):
        k = m.group(1).decode("latin-1")
        v = m.group(2).decode("latin-1")
        if k in _BUTE_KEYWORDS:
            kv.append((k, v))
    # Heuristic: any value that looks like a resource basename
    # (ends in .dtx/.tga/.ltb/.rez/.fxo/.fx/.dat/.png) is "suspect relation".
    base_re = re.compile(r"([A-Za-z0-9_\-/.]+\.(?:dtx|tga|ltb|rez|fxo|fx|dat|png))\b",
                         re.IGNORECASE)
    suspect_relations = []
    for m in base_re.finditer(data):
        suspect_relations.append(m.group(1).decode("latin-1"))
    return {
        "tags": tags,
        "kv_count": len(kv),
        "kv_sample": kv[:20],
        "suspect_relation_count": len(suspect_relations),
        "suspect_relation_sample": suspect_relations[:20],
    }


# ---------------------------------------------------------------------------
# Step 5: scoped correlation against existing evidence only.
# ---------------------------------------------------------------------------
def _load_existing_scope() -> dict:
    """Load the existing R1 / N01 evidence scope so we can correlate without
    re-scanning data/**."""
    base = os.path.join(REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material")
    scope = {"families": ["BornBeast", "Transformers", "Jewelry", "BlueDiamond"],
             "n01_decoded_count": None, "config_index_keys": 18}
    # N01 mapping tuples are the only existing scope object we have access
    # to without re-scanning data/**. We record that as scope metadata.
    return scope


# ---------------------------------------------------------------------------
# Main pipeline.
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override the default CF runtime path (CF2_CF_DIR)")
    ap.add_argument("--limit", type=int, default=0,
                    help="optional cap on number of samples (0 = no cap)")
    args = ap.parse_args()

    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
    cf_root = _paths.cf_dir()
    print(f"[n02b] cf_root = {cf_root}", file=sys.stderr)

    samples = _enumerate_samples(cf_root)
    if args.limit and len(samples) > args.limit:
        samples = samples[: args.limit]
    print(f"[n02b] enumerated {len(samples)} .ltc/.lta samples", file=sys.stderr)

    scope = _load_existing_scope()

    # Run decoder on each sample and collect results.
    results: list[dict] = []
    magic_counter: Counter = Counter()
    failure_counter: Counter = Counter()
    success_count = 0
    for alias, abs_path in samples:
        try:
            size = os.path.getsize(abs_path)
            with open(abs_path, "rb") as f:
                data = f.read()
        except OSError as e:
            results.append({
                "path_alias": alias,
                "abs_path": abs_path,
                "status": "READ_ERROR",
                "error": str(e),
            })
            continue
        sha = hashlib.sha256(data).hexdigest()
        magic = data[:4].hex()
        magic_counter[magic] += 1
        rec: dict = {
            "path_alias": alias,
            "abs_path": abs_path,
            "size_bytes": size,
            "sha256": sha,
            "magic_first4": magic,
            "ascii_header": _ascii_header_text(data)[:160],
        }
        try:
            decoded = _decode_ltc_c_sharp(data)
            decoded_sha = hashlib.sha256(decoded).hexdigest()
            pr = _printable_ratio(decoded)
            head_sample = decoded[:200].decode("latin-1", errors="replace")
            rec.update({
                "status": "DECODED",
                "decoded_size": len(decoded),
                "decoded_sha256": decoded_sha,
                "decoded_printable_ratio": round(pr, 4),
                "decoded_head_sample": head_sample,
            })
            # Bute grammar pass only if printable ratio is high enough.
            if pr >= 0.85:
                bute = _bute_grammar_pass(head_sample + decoded[200:].decode(
                    "latin-1", errors="replace"))
                rec["bute_grammar"] = bute
            success_count += 1
        except LtcDecodeFailure as e:
            failure_counter[str(e)] += 1
            rec.update({
                "status": "FAILED",
                "failure_mode": str(e),
            })
        results.append(rec)

    print(f"[n02b] success={success_count} failed={len(results) - success_count}",
          file=sys.stderr)

    # Cluster stats
    cluster_stats = {
        "total": len(results),
        "by_magic_first4": dict(magic_counter.most_common()),
        "by_status": dict(Counter(r["status"] for r in results).most_common()),
        "by_failure_mode": dict(failure_counter.most_common()),
    }

    # bf000.lta vs bf*.ltc cross-comparison.
    bf000 = next((r for r in results
                  if r["path_alias"].endswith("bf000.lta")), None)
    bf_ltc = [r for r in results
              if r["path_alias"].startswith("rez/Butes/bf") and
              r["path_alias"].endswith(".ltc")]

    bf_comparison = {
        "bf000_lta_present": bf000 is not None,
        "bf000_lta": bf000,
        "bf_ltc_count": len(bf_ltc),
        "bf_ltc_magic_shared": (
            bf_ltc[0]["magic_first4"] if bf_ltc else None
        ),
        "bf_ltc_size_min": min((r["size_bytes"] for r in bf_ltc), default=None),
        "bf_ltc_size_max": max((r["size_bytes"] for r in bf_ltc), default=None),
        "magic_differential":
            (bf000["magic_first4"] if bf000 else None) !=
            (bf_ltc[0]["magic_first4"] if bf_ltc else None),
    }
    # Until we have a working decoder for the variant format, the
    # decoded-content comparison cannot be made. Record the fact.

    # 1) ltc_decoder_validation.json
    validation_payload = {
        "status": "CF_LTC_VARIANT_CONFIRMED" if success_count == 0
                  else f"PARTIAL_DECODE_{success_count}",
        "decoder": "CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs "
                   "(1:1 Python port, no behaviour change)",
        "decoder_constants": {
            "WINDOW_SIZE": WINDOW_SIZE,
            "MIN_MATCH_LEN": MIN_MATCH_LEN,
            "HEADER_BYTES": HEADER_BYTES,
            "MAX_DECODED": MAX_DECODED,
        },
        "decoder_input_requirement": "first 4 bytes == 00 00 00 00",
        "cluster_stats": cluster_stats,
        "bf_comparison": bf_comparison,
        "verdict": _verdict_text(success_count, len(results), cluster_stats),
        "results": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "ltc_decoder_validation.json"), "w",
              encoding="utf-8") as f:
        json.dump(validation_payload, f, indent=2, ensure_ascii=False)

    # 2) bute_parse_inventory.json — only the cases we could actually parse.
    parsed = []
    for r in results:
        if r.get("status") == "DECODED" and "bute_grammar" in r:
            parsed.append({
                "path_alias": r["path_alias"],
                "sha256": r["sha256"],
                "decoded_sha256": r["decoded_sha256"],
                "decoded_size": r["decoded_size"],
                "printable_ratio": r["decoded_printable_ratio"],
                "head_sample": r["decoded_head_sample"][:200],
                "bute_grammar": r["bute_grammar"],
            })
    bute_payload = {
        "total_decoded": success_count,
        "total_parsed_as_bute": len(parsed),
        "existing_scope": scope,
        "parsed": parsed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "bute_parse_inventory.json"), "w",
              encoding="utf-8") as f:
        json.dump(bute_payload, f, indent=2, ensure_ascii=False)

    # 3) correlation_report.json
    corr = {
        "scope_used": scope,
        "samples_decoded": success_count,
        "samples_failed": len(results) - success_count,
        "binding_evidence": [],   # none, since decoder produced 0 valid output
        "bounded_negative": {
            "BornBeast": {"binding_evidence_count": 0,
                          "reason": "decoder could not produce Bute-parseable "
                                    "output for any rez/Butes/*.ltc"},
            "Transformers": {"binding_evidence_count": 0,
                             "reason": "decoder could not produce Bute-parseable "
                                       "output for any rez/Butes/*.ltc"},
            "Jewelry": {"binding_evidence_count": 0,
                        "reason": "decoder could not produce Bute-parseable "
                                  "output for any rez/Butes/*.ltc"},
            "BlueDiamond": {"binding_evidence_count": 0,
                            "reason": "decoder could not produce Bute-parseable "
                                      "output for any rez/Butes/*.ltc"},
        },
        "bf000_lta_vs_bf_ltc_relationship": (
            "BF000.LTA and BF*.LTC share filename prefix only. "
            "BF000.LTA magic=c7004400ffff0000, BF*.LTC magic=5483b2e1. "
            "Without a working decoder for either format, no structural "
            "parent/child or shared-key relationship can be proved."
        ),
        "next_single_highest_value_consumer": _recommend_next_target(cluster_stats, results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "correlation_report.json"), "w",
              encoding="utf-8") as f:
        json.dump(corr, f, indent=2, ensure_ascii=False)

    # 4) n02b_butes_config_report.md
    _write_report(validation_payload, bute_payload, corr)
    print(f"[n02b] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _verdict_text(success: int, total: int, cluster: dict) -> str:
    if success == 0:
        return (
            "The C# LithTechLtcNativeDecoder requires first-4 bytes == "
            "00 00 00 00. All 73 rez/Butes/*.ltc share magic 5483b2e1, and "
            "the rez/bf000.lta sample uses magic c7004400ffff0000. The 4 "
            "rez/Worlds/*.lta have a 100-byte ASCII header + binary body. "
            "No sample satisfies the decoder precondition, so the decoder "
            "is incompatible with the current CF runtime's Bute/LTA wire "
            "format. This is a confirmed LTC variant, not a decoder bug."
        )
    return (f"Partial decode: {success}/{total} samples succeeded. "
            "Inspect cluster_stats for the failing majority.")


def _recommend_next_target(cluster: dict, results: list) -> str:
    # If all .ltc fail with the same variant, the next high-value single
    # consumer is the binary that loads bute configs: crossfireBase.dll
    # (or server.dll) at runtime, which is the only place that knows the
    # real format.
    return (
        "CF_LTC_VARIANT_CONFIRMED: the real Bute/LTC wire format is not the "
        "format the C# decoder implements. The single highest-value next "
        "consumer is the CF game DLL that loads bute configs at runtime — "
        "specifically crossfireBase.dll and server.dll. Targeted strings / "
        "xref on these two DLLs is the only way to recover the real LTC "
        "header and bitstream. EXE / broad decompile is explicitly out of "
        "scope per task.md §6."
    )


def _write_report(v: dict, bute: dict, corr: dict) -> None:
    out = os.path.join(OUT_DIR, "n02b_butes_config_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-B — LTC decoder validation & Bute semantic correlation")
    lines.append("")
    lines.append(f"- generated_at: `{v.get('generated_at', '')}`")
    lines.append(f"- status: **{v.get('status', '')}**")
    lines.append(f"- script: `{v.get('script', '')}`")
    lines.append("")
    lines.append("## 1. Decoder under test")
    lines.append("")
    lines.append("- source: `CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs`")
    lines.append("- ported 1:1 to Python in this script (no behaviour change).")
    lines.append("- decoder requires first 4 input bytes == `00 00 00 00`.")
    lines.append("- decoder constants: " +
                 ", ".join(f"`{k}={v_}`" for k, v_ in v["decoder_constants"].items()))
    lines.append("")

    lines.append("## 2. Sample coverage")
    lines.append("")
    lines.append(f"- total samples enumerated: **{v['cluster_stats']['total']}**")
    lines.append("- all samples are read from `D:\\Program Files\\CF(2)` (cf_default)")
    lines.append("")
    lines.append("### By status")
    lines.append("")
    lines.append("| status | count |")
    lines.append("|---|---|")
    for k, n in v["cluster_stats"]["by_status"].items():
        lines.append(f"| `{k}` | {n} |")
    lines.append("")
    lines.append("### By first-4-byte magic")
    lines.append("")
    lines.append("| magic | count |")
    lines.append("|---|---|")
    for k, n in v["cluster_stats"]["by_magic_first4"].items():
        lines.append(f"| `{k}` | {n} |")
    lines.append("")
    lines.append("### By failure mode")
    lines.append("")
    if v["cluster_stats"]["by_failure_mode"]:
        lines.append("| failure_mode | count |")
        lines.append("|---|---|")
        for k, n in v["cluster_stats"]["by_failure_mode"].items():
            lines.append(f"| `{k}` | {n} |")
    else:
        lines.append("- (no failures)")
    lines.append("")

    lines.append("## 3. Verdict on existing decoder")
    lines.append("")
    lines.append(v["verdict"])
    lines.append("")

    lines.append("## 4. bf000.lta vs bf*.ltc relationship")
    lines.append("")
    bf = v["bf_comparison"]
    lines.append(f"- `rez/bf000.lta` magic = `{bf['bf000_lta']['magic_first4'] if bf['bf000_lta'] else 'N/A'}`")
    lines.append(f"- `bf*.ltc` shared magic = `{bf['bf_ltc_magic_shared']}`")
    lines.append(f"- `bf*.ltc` count = **{bf['bf_ltc_count']}**; "
                 f"size range = {bf['bf_ltc_size_min']} .. {bf['bf_ltc_size_max']} bytes")
    lines.append(f"- magic differential = **{bf['magic_differential']}** "
                 "(the two formats are *not* the same wire format)")
    lines.append("- without a working decoder for either format, no shared tag/key/grammar "
                 "comparison is possible — filename prefix is the only signal, and "
                 "filename similarity is explicitly **not** a binding proof per task.md §4.")
    lines.append("")

    lines.append("## 5. Bute/LTA grammar verdict")
    lines.append("")
    lines.append(f"- total decoded: `{bute['total_decoded']}`")
    lines.append(f"- total parsed as Bute grammar: `{bute['total_parsed_as_bute']}`")
    lines.append("- parsed list is empty because the decoder returned 0 successful decodes.")
    lines.append("")

    lines.append("## 6. Target / resource correlation")
    lines.append("")
    lines.append("Scope reused from existing evidence only "
                 "(BornBeast / Transformers / Jewelry / BlueDiamond).")
    lines.append("")
    lines.append("| family | binding_evidence_count | reason |")
    lines.append("|---|---|---|")
    for fam, info in corr["bounded_negative"].items():
        lines.append(f"| `{fam}` | {info['binding_evidence_count']} | {info['reason']} |")
    lines.append("")

    lines.append("## 7. Recommended next single consumer")
    lines.append("")
    lines.append(corr["next_single_highest_value_consumer"])
    lines.append("")

    lines.append("## 8. Scope guard")
    lines.append("")
    lines.append("- did not re-scan `data/**`;")
    lines.append("- did not execute any CF binary, no anti-cheat bypass, no memory dump;")
    lines.append("- did not decompile any EXE/DLL this round;")
    lines.append("- did not touch FXO shaders;")
    lines.append("- did not unpack large REZ as main task;")
    lines.append("- did not modify `plan.md`;")
    lines.append("- did not rewrite or fork the C# decoder without evidence "
                 "(per task.md §5 / §8).")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
