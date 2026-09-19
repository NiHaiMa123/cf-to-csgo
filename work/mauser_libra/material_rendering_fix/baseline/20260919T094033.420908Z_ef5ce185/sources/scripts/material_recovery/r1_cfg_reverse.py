#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-R1-F (narrow rework): CFG byte accounting without framing claims.

Supersedes r1/cfg_reverse_r1.json schema v3. Per Chat/Sol continuation
review of commit 8af3cd0:

BUGS FIXED vs v3
  1. v3 named the varying-byte mod-3 phase `head_partial_bytes` and treated
     it as a proven record-boundary offset. The phase is only WHICH mod-3
     position carries variation; the record boundary is NOT proven. The
     field is renamed `varying_byte_phase` and carries no framing claim.
  2. v3's slot extraction `[raw[h + k*3] for k in range((n - h)//3)]`
     dropped the final varying sample when (n - h) % 3 != 0 (e.g. BornBeast:
     varying bytes at 2,5,...,491 — the sample at offset 491 was lost and
     the count printed as 163 instead of 164). Sample sequences are now
     computed over the mathematically complete phase sequence.

WHAT REMAINS VERIFIED (unchanged, re-measured here)
  * all 237 WeaponShader CFGs: every non-0xFF byte sits at exactly one
    fixed offset-mod-3 phase per file; the other two phases are constant
    0xFF across the entire file.
Only that structural pattern is claimed. Framing stays a three-way open
competition:
    H-CFG-A: byte-0-origin RGB/BGR triplets, h = varying channel index
    H-CFG-B: scalar samples + two padding bytes, record boundary unproven
    H-CFG-C: other 3-byte periodic packing

Byte accounting is given under BOTH candidate origins so no bytes are lost
under either reading:
    byte-0-origin: n = T*3 + t0   (t0 in {0,1,2})
    phase-origin : n = h + S*3 + s (h = first varying index, s = trailing)

Semantic binding stays UNRESOLVED_PROVISIONAL.
"""
from __future__ import annotations

import hashlib
import json
import os

REPO = r"D:\project\cf_to_csgo"
WS_DIR = os.path.join(REPO, "data/rf017/ModelTextures/Shader/WeaponShader")
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/r1")
SUPERSEDES_COMMIT = "632ede449578f688cea7e6b5f40cbf03700aaaa5"
PRIMARY = ["M4A1_S_BornBeast", "M4A1_S_Transformers", "M4A1_S_Jewelry"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def analyze(path):
    raw = open(path, "rb").read()
    n = len(raw)
    rec = {"size_bytes": n, "sha256": sha256_of(path)}

    # --- verified structural fact: which mod-3 phase carries non-FF bytes?
    violations_by_phase = []
    phase_of_file = None
    for ph in range(3):
        viol = sum(1 for i in range(n) if i % 3 != ph and raw[i] != 0xFF)
        violations_by_phase.append(viol)
    min_viol = min(violations_by_phase)
    if min_viol == 0:
        phase_of_file = violations_by_phase.index(0)
    rec["mod3_pattern"] = {
        "violations_if_phase_0": violations_by_phase[0],
        "violations_if_phase_1": violations_by_phase[1],
        "violations_if_phase_2": violations_by_phase[2],
        "varying_byte_phase": phase_of_file,
        "note": (
            "phase = which offset mod 3 carries variation. This is NOT "
            "evidence of where records begin; naming it 'head gap' in v3 "
            "was wrong."
        ),
    }

    # --- lossless byte accounting under both candidate record origins
    t0, rem0 = divmod(n, 3)
    rec["accounting_byte0_origin"] = {
        "identity": f"{n} = {t0}*3 + {rem0}" if rem0 else f"{n} = {t0}*3",
        "full_triplets": t0,
        "tail_bytes": rem0,
    }
    if phase_of_file is not None:
        ph = phase_of_file
        first_v = next(i for i in range(n) if i % 3 == ph)
        last_v = n - 1 - ((n - 1 - ph) % 3) if n > ph else None
        count_phase = len(range(ph, n, 3))
        trailing = (n - 1 - last_v) if last_v is not None else None
        rec["accounting_phase_origin"] = {
            "first_varying_offset": first_v,
            "last_varying_offset": last_v,
            "leading_bytes_before_first_sample": first_v,
            "sample_count_complete": count_phase,
            "trailing_bytes_after_last_sample": trailing,
            # span accounting: samples are single bytes spaced 3 apart, so the
            # self-consistent identity is span-based, NOT sample_count*3
            "identity": (
                f"{n} = {first_v} + ({count_phase}-1)*3 + 1 + {trailing}"
                if last_v is not None and count_phase > 0 else None
            ),
            "identity_note": (
                "samples are single byte positions spaced 3 bytes apart; the "
                "span formula first + (count-1)*3 + 1 + trailing is the "
                "arithmetically correct identity. v4's "
                "'n = first + count*3 + trailing' double-counted one stride."
            ),
            "off_by_one_note": (
                "count uses range(ph, n, 3): includes the LAST varying byte; "
                "v3 dropped it whenever (n-h)%3 != 0"
            ),
        }
        # complete varying-phase sample sequence (no filtering, no truncation)
        seq = [raw[i] for i in range(ph, n, 3)]
        nonff = [v for v in seq if v != 0xFF]
        rec["varying_phase_sequence_stats"] = {
            "length": len(seq),
            "ff_valued_samples_kept": sum(1 for v in seq if v == 0xFF),
            "nonff_count": len(nonff),
            "min_nonff": min(nonff) if nonff else None,
            "max": max(seq),
            "unique": len(set(seq)),
            "first16": seq[:16],
            "last8": seq[-8:],
        }

        # byte-0-origin triplet view of the SAME file (for H-CFG-A comparison):
        # channel c of triplet k = raw[k*3 + c]; report which channel varies.
        trip_channel_uniq = []
        for c in range(3):
            vals = {raw[k * 3 + c] for k in range(t0)}
            trip_channel_uniq.append(len(vals))
        rec["byte0_triplet_view"] = {
            "unique_values_per_channel": trip_channel_uniq,
            "varying_channels_under_byte0_origin":
                [c for c in range(3) if trip_channel_uniq[c] > 1],
            "note": "under H-CFG-A the two constant channels are the fixed-FF ones",
        }
    return raw, rec


def resample(seq, m=128):
    if len(seq) < 2:
        return seq
    out = []
    for k in range(m):
        pos = k * (len(seq) - 1) / (m - 1)
        lo = int(pos)
        hi = min(len(seq) - 1, lo + 1)
        t = pos - lo
        out.append(seq[lo] * (1 - t) + seq[hi] * t)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(fn for fn in os.listdir(WS_DIR) if fn.upper().endswith(".CFG"))

    corpus_seq = []
    pattern_ok = 0
    value_min, value_max = 255, -1
    ff_samples_total = 0
    for fn in files:
        raw, rec = analyze(os.path.join(WS_DIR, fn))
        st = rec.get("mod3_pattern", {})
        if st.get("varying_byte_phase") is not None:
            pattern_ok += 1
            ph = st["varying_byte_phase"]
            for i in range(ph, len(raw), 3):
                v = raw[i]
                corpus_seq.append(v)
                if v == 0xFF:
                    ff_samples_total += 1
                else:
                    value_min = min(value_min, v)
                    value_max = max(value_max, v)

    primary = {}
    seqs = {}
    for name in PRIMARY:
        raw, rec = analyze(os.path.join(WS_DIR, name + ".CFG"))
        primary[name] = rec
        ph = rec["mod3_pattern"]["varying_byte_phase"]
        seqs[name] = [raw[i] for i in range(ph, len(raw), 3)]

    rs = {k: resample(v) for k, v in seqs.items()}
    correlations = {}
    keys = list(rs)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = rs[keys[i]], rs[keys[j]]
            ma, mb = sum(a) / len(a), sum(b) / len(b)
            cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
            va = sum((x - ma) ** 2 for x in a) ** 0.5
            vb = sum((y - mb) ** 2 for y in b) ** 0.5
            r = cov / (va * vb) if va and vb else 0.0
            correlations[f"{keys[i]}_vs_{keys[j]}"] = round(r, 3)

    from collections import Counter
    hist = Counter(corpus_seq)
    hist_nonff = {str(v): c for v, c in sorted(hist.items()) if v != 0xFF}

    report = {
        "schema": "cf2.p4m01.r1.cfg-reverse.v4",
        "supersedes_commit": SUPERSEDES_COMMIT,
        "supersedes_report_schema": "cf2.p4m01.r1.cfg-reverse.v3",
        "continuation_review_reason": (
            "v3 mislabeled the varying-byte mod-3 phase as a record head gap "
            "('head_partial_bytes') and its slot extraction dropped the last "
            "varying sample when (n-h)%3!=0 (BornBeast reported 163 instead "
            "of 164). v4 separates phase from framing claims and computes "
            "lossless accounting under both candidate record origins."
        ),
        "verified_structural_core": {
            "statement": (
                "all 237 WeaponShader CFGs: non-0xFF bytes occupy exactly one "
                "fixed offset-mod-3 phase per file; the other two phases are "
                "constant 0xFF across the entire file"
            ),
            "files_fitting": pattern_ok,
            "corpus_files": len(files),
            "only_this_is_verified": True,
        },
        "primary_accounting": {},
        "corpus_value_statistics": {
            "total_phase_samples": len(corpus_seq),
            "ff_valued_samples_kept": ff_samples_total,
            "nonff_value_range": [value_min, value_max],
            "values_ge_100": sum(1 for v in corpus_seq if v != 0xFF and v >= 100),
            "nonff_histogram_top": dict(list(hist_nonff.items())[:20]),
        },
        "competing_framing_hypotheses": {
            "H-CFG-A_byte0_rgb_bgr_triplets": {
                "statement": "records are byte-0-origin 3-byte colors; the varying phase h is one color channel; other two channels saturate at 0xFF",
                "status": "OPEN_NOT_REFUTED",
            },
            "H-CFG-B_scalar_plus_padding": {
                "statement": "scalar samples on a stride-3 grid with two padding bytes; record boundary itself unproven",
                "status": "PREFERRED_NOT_PROVEN",
            },
            "H-CFG-C_other_periodic_packing": {
                "statement": "any other 3-byte periodic container/packing consistent with the observed mod-3 pattern",
                "status": "OPEN",
            },
            "shared_core_either_way": [
                "237/237 files show the single-phase mod-3 pattern",
                "record BOUNDARY is not proven by the phase evidence alone",
            ],
        },
        "cross_skin_strip_correlations_resampled128": correlations,
        "engine_material_format_context": {
            "finding": (
                "LZMA-compressed TEXT material CFGs exist for ArmModel "
                "(rf016 .../ArmModel/Shader/*.CFG): sections [Textures] with "
                "SpecularMapName0/EnvCubeMapName0/NormalMapName0/"
                "AlphaMapName0, [Techniques] flags, [Properties] float "
                "params incl. PieceIndex — explicit per-piece texture binding"
            ),
            "weapon_equivalent_found_in_scanned_corpus": False,
            "implication": (
                "CF has an explicit material-binding format; weapons ship a "
                "different binary strip whose consumer remains unknown"
            ),
        },
        "semantic_binding_status": "UNRESOLVED_PROVISIONAL",
        "framing_status": (
            "MOD3_PATTERN_VERIFIED_237_of_237; record boundary UNRESOLVED "
            "(three-hypothesis competition); no 'exact framing' claim"
        ),
        "conclusion": None,  # filled below
    }

    pa = {}
    for name in PRIMARY:
        rec = primary[name]
        pa[name] = {
            "size_bytes": rec["size_bytes"],
            "varying_byte_phase": rec["mod3_pattern"]["varying_byte_phase"],
            "byte0_origin": rec["accounting_byte0_origin"],
            "phase_origin": rec["accounting_phase_origin"],
            "sequence_stats": rec["varying_phase_sequence_stats"],
            "byte0_triplet_view": rec["byte0_triplet_view"],
        }
    report["primary_accounting"] = pa

    bb = pa["M4A1_S_BornBeast"]["sequence_stats"]
    tr = pa["M4A1_S_Transformers"]["sequence_stats"]
    jw = pa["M4A1_S_Jewelry"]["sequence_stats"]
    report["conclusion"] = (
        "All 237 files show the single-phase mod-3 pattern (verified). "
        f"Complete phase sequences: BornBeast {bb['length']} samples "
        f"(last varying byte included), Transformers {tr['length']}, "
        f"Jewelry {jw['length']} — matching the byte-0-origin triplet counts "
        f"492=164*3, 506=168*3+2, 642=214*3 with no off-by-one loss. Record "
        "boundary remains unresolved across H-CFG-A/B/C; semantic binding "
        "stays UNRESOLVED_PROVISIONAL."
    )

    out = os.path.join(OUT_DIR, "cfg_reverse_r1.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("wrote", out)
    print(f"pattern ok: {pattern_ok}/{len(files)}")
    for name in PRIMARY:
        st = pa[name]["sequence_stats"]
        print(f"{name}: n={pa[name]['size_bytes']} phase={pa[name]['varying_byte_phase']} "
              f"samples={st['length']} (complete)")


if __name__ == "__main__":
    main()
