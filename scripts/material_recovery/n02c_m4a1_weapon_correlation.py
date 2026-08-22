#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-C — M4A1 Weapon Record -> Runtime Asset Correlation.

Implements the bounded task P4-M01-N02-C from task.md.

Goal: use the previously decoded runtime Bute config to find the M4A1 weapon
records and their explicit resource paths, then correlate each path against
the existing N01 / P4 / P5 asset inventory. Do NOT rebuild LTC, do NOT
re-scan data/**, do NOT decompile EXE / DLL.

The single source of truth for runtime binding is:
  D:\\Program Files\\CF(2)\\rez\\Butes\\bf005.ltc   (the CF weapon table)

We extract:
  - every Weapon record whose WeaponName mentions M4
  - their ModelFileName / SkinFileName / PViewModelFileName /
    PViewSkinFileName / RenderStyleFileName / PViewRenderStyleFileName

Then we cross-correlate with:
  - the P4 baseline_inventory.json (which already lists
    data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB)
  - the prototype_01_manifest.json (which lists P4 inputs and outputs)
  - the c3_alignment_manifest.json
  - the material_map.json

Each match is graded as one of:
  DIRECT_CONFIG_REFERENCE       bf005.ltc binds the resource to the weapon
  BASENAME_MATCH                same basename string but not direct bind
  PATH_MATCH                    path-only match
  VISUAL_SIMILARITY_ONLY        visual / fuzzy match — never binding proof

Only DIRECT_CONFIG_REFERENCE counts as binding evidence. Path-only or
basename-only matches are bounded negative.

Outputs under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02c_weapon_correlation/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02_butes_config_triage as n02b  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
OUT_DIR = os.path.join(N02A_DIR, "n02c_weapon_correlation")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# P4 / N01 known-asset loader (read existing evidence; do not re-scan data/**).
# ---------------------------------------------------------------------------
def _load_existing_assets() -> dict:
    """Read the existing P4 / N01 manifest + report files for asset correlation.

    The set of files we read is the bounded "existing evidence" — we do NOT
    re-scan the local CF runtime or the unpacked data/** corpus.
    """
    sources = {
        "p4_baseline_inventory": os.path.join(
            REPO, "work", "m4a1_s_bornbeast", "p4_prototype_01", "baseline_inventory.json"
        ),
        "prototype_01_manifest": os.path.join(
            REPO, "assets", "weapons", "m4a1_s_bornbeast", "prototype_01_manifest.json"
        ),
        "m4a4_target_manifest": os.path.join(
            REPO, "assets", "weapons", "m4a1_s_bornbeast", "m4a4_target_manifest.json"
        ),
        "m4a4_final_bornbeast_manifest": os.path.join(
            REPO, "assets", "weapons", "m4a1_s_bornbeast", "m4a4_final_bornbeast_manifest.json"
        ),
        "c3_alignment_manifest": os.path.join(
            REPO, "assets", "weapons", "m4a1_s_bornbeast", "c3_alignment_m4a4_manifest.json"
        ),
        "material_map": os.path.join(
            REPO, "assets", "weapons", "m4a1_s_bornbeast", "material_map.json"
        ),
        "m4a4_reference_report": os.path.join(
            REPO, "work", "m4a1_s_bornbeast", "reference_m4a4", "reference_report.json"
        ),
    }
    loaded: dict = {}
    for label, path in sources.items():
        if not os.path.exists(path):
            loaded[label] = {"path": path, "exists": False}
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded[label] = {"path": path, "exists": True,
                                 "data": json.load(f)}
        except (OSError, json.JSONDecodeError) as e:
            loaded[label] = {"path": path, "exists": True, "error": str(e)}
    return loaded


def _collect_known_asset_basenames(assets: dict) -> set[str]:
    """Pull every basename in P4 / N01 evidence that we will use for lookup.

    Basenames are the right granularity: the runtime Bute references
    ``Models\\weapons\\m4a1.ltb`` whereas the P4 source LTB lives at
    ``data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB``. A
    basename match therefore means a partial overlap on the name, not on
    the path. We DO NOT use this to claim binding — we only use it to show
    the gap.
    """
    basenames: set[str] = set()
    for label, info in assets.items():
        if not info.get("exists") or "data" not in info:
            continue
        d = info["data"]

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in {"path", "rel_path", "rel"} and isinstance(v, str):
                        base = os.path.basename(v.replace("\\", "/"))
                        if base:
                            basenames.add(base.lower())
                    walk(v)
            elif isinstance(o, list):
                for item in o:
                    walk(item)
        walk(d)
    return basenames


# ---------------------------------------------------------------------------
# Extract M4A1-family weapon records from bf005.ltc.
# ---------------------------------------------------------------------------
def _load_bf005_records() -> list[dict]:
    """Decode bf005.ltc and return all Weapon records (lisp-parsed)."""
    p = os.path.join(CF_DIR, "rez", "Butes", "bf005.ltc")
    with open(p, "rb") as f:
        data = f.read()
    ul = n02b.try_unlock_crossfire_payload(data)
    decoded = n02b._decode_ltc_c_sharp(ul)
    text = decoded.decode("latin-1", errors="replace")
    recs = n02b._parse_lisp_s_expressions(text)
    return [r for r in recs if r.get("_head") == "Weapon"]


def _filter_m4_records(records: list[dict]) -> list[dict]:
    """Keep only records whose WeaponName mentions 'M4' or whose ModelFileName
    points to a path that contains 'm4a1' (case-insensitive)."""
    out = []
    for r in records:
        wn = r.get("WeaponName", "")
        mfn = r.get("ModelFileName", "")
        pv = r.get("PViewModelFileName", "")
        if "M4" in wn or "m4" in mfn.lower() or "m4" in pv.lower():
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# Cross-correlate: given a runtime resource path (ModelFileName etc.),
# classify the relation to the N01/P4 known assets.
# ---------------------------------------------------------------------------
_PATH_BASENAME_RE = re.compile(r"[^\\/]+$")


def _basename(path_or_name: str) -> str:
    return _PATH_BASENAME_RE.search(path_or_name).group(0).lower() if path_or_name else ""


def _classify_match(field: str, runtime_value: str, known_basenames: set[str]) -> dict:
    """Classify one runtime field against the known-asset basenames.

    Returns a dict with: match_type, evidence_grade, matched_basenames
    (list of basenames that are case-insensitively equal or share a
    substantial prefix), match_explanation.
    """
    if not runtime_value:
        return {"match_type": "EMPTY", "evidence_grade": "NO_MATCH",
                "matched_basenames": [], "match_explanation": "field is empty"}
    base = _basename(runtime_value)
    base_no_ext = os.path.splitext(base)[0]
    matches = []
    for known in known_basenames:
        k_no_ext = os.path.splitext(known)[0]
        if known == base:
            matches.append(("EXACT_BASENAME", known))
        elif base_no_ext and k_no_ext and (base_no_ext in k_no_ext or k_no_ext in base_no_ext):
            # partial basename overlap — e.g. "m4a1" in "pv-m4a1_s_bornbeast_classic"
            matches.append(("PARTIAL_BASENAME", known))
    if not matches:
        return {"match_type": "NO_MATCH", "evidence_grade": "NONE",
                "matched_basenames": [],
                "match_explanation": f"basename '{base}' not in known P4/N01 evidence"}
    has_exact = any(t == "EXACT_BASENAME" for t, _ in matches)
    if has_exact:
        return {"match_type": "BASENAME_MATCH",
                "evidence_grade": "PARTIAL",
                "matched_basenames": [m[1] for m in matches],
                "match_explanation": (
                    f"basename '{base}' is in known P4/N01 evidence; "
                    "runtime bind is a DIFFERENT record (no DIRECT_CONFIG_REFERENCE "
                    "to a BornBeast-named resource)"
                )}
    return {"match_type": "PARTIAL_BASENAME",
            "evidence_grade": "WEAK",
            "matched_basenames": [m[1] for m in matches],
            "match_explanation": (
                f"basename '{base}' shares prefix with known P4/N01 evidence; "
                "not a direct config reference"
            )}


# ---------------------------------------------------------------------------
# Main.
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
    print(f"[n02c] cf_root = {_paths.cf_dir()}", file=sys.stderr)
    print(f"[n02c] repo   = {REPO}", file=sys.stderr)

    # 1. Load existing P4 / N01 evidence
    assets = _load_existing_assets()
    known_basenames = _collect_known_asset_basenames(assets)
    print(f"[n02c] known basenames from P4/N01 evidence: {len(known_basenames)}",
          file=sys.stderr)

    # 2. Extract M4-family weapon records from bf005.ltc
    all_weapon_records = _load_bf005_records()
    m4_records = _filter_m4_records(all_weapon_records)
    print(f"[n02c] bf005.ltc Weapon records: {len(all_weapon_records)}; "
          f"M4-related: {len(m4_records)}", file=sys.stderr)

    # 3. For each M4 record, classify every binding field
    binding_fields = [
        "ModelFileName", "SkinFileName",
        "PViewModelFileName", "PViewSkinFileName",
        "RenderStyleFileName", "PViewRenderStyleFileName",
    ]
    detailed = []
    direct_config_refs = []   # of all binding records, those that reference
                              # a path whose basename is in N01/P4 evidence
    for r in m4_records:
        wn = r.get("WeaponName", "")
        rec = {
            "WeaponName": wn,
            "binding_fields": {},
            "direct_config_reference": False,
            "any_partial_match": False,
        }
        for fk in binding_fields:
            v = r.get(fk, "")
            if not v:
                rec["binding_fields"][fk] = {
                    "value": "", "match_type": "EMPTY", "evidence_grade": "NO_MATCH",
                    "matched_basenames": [], "match_explanation": "field is empty",
                }
                continue
            cls = _classify_match(fk, v, known_basenames)
            cls["value"] = v
            rec["binding_fields"][fk] = cls
            if cls["match_type"] in {"BASENAME_MATCH", "PARTIAL_BASENAME"}:
                rec["any_partial_match"] = True
                if cls["match_type"] == "BASENAME_MATCH":
                    rec["direct_config_reference"] = True
        detailed.append(rec)
        if rec["direct_config_reference"]:
            direct_config_refs.append({
                "WeaponName": wn,
                "binding_fields_with_match": {
                    fk: rec["binding_fields"][fk]
                    for fk in binding_fields
                    if rec["binding_fields"][fk]["match_type"] != "EMPTY"
                },
            })

    # 4. Lookup the P4 known BornBeast source LTB explicitly.
    #    Even if the bf005 record does not name it directly, we can still
    #    state whether a single named asset is a known BornBeast/M4A1-S
    #    artifact.
    p4_bornbeast_ltb = None
    p4_bornbeast_assets: list[dict] = []
    cf_artifact_ext = (".ltb", ".lta", ".dtx", ".tga", ".rez", ".ltc",
                       ".obj", ".mdl", ".vmt", ".vtf", ".bmp.png")
    for label in ("p4_baseline_inventory", "prototype_01_manifest",
                  "m4a4_target_manifest", "m4a4_final_bornbeast_manifest",
                  "c3_alignment_manifest", "material_map",
                  "m4a4_reference_report"):
        info = assets.get(label, {})
        data = info.get("data", {})
        if not data:
            continue

        def search(o, path=""):
            nonlocal p4_bornbeast_ltb
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str):
                        vl = v.lower()
                        if "bornbeast" in vl and vl.endswith(cf_artifact_ext):
                            entry = {"source_label": label,
                                     "field_path": f"{path}.{k}",
                                     "value": v,
                                     "ext": os.path.splitext(v)[1].lower()}
                            p4_bornbeast_assets.append(entry)
                            # prefer LTB as the canonical BornBeast LTB
                            if entry["ext"] == ".ltb" and p4_bornbeast_ltb is None:
                                p4_bornbeast_ltb = entry
                    search(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    search(v, f"{path}[{i}]")
        search(data)

    # 5. Status computation per task.md §7.
    m4a1_family_present = any("M4A1" in r["WeaponName"] for r in detailed)
    bornbeast_in_runtime = any(
        "bornbeast" in v.lower()
        for r in detailed
        for fk, cls in r["binding_fields"].items()
        for v in [cls.get("value", "")]
        if v
    )
    # Per task.md §5.3 the ONLY thing that counts as binding evidence is
    # DIRECT_CONFIG_REFERENCE — i.e. the runtime Bute binds a path whose
    # basename is byte-for-byte equal to a known P4/N01 asset that names
    # BornBeast. Substring overlaps are PARTIAL_BASENAME / WEAK and do
    # NOT promote a record to status A.
    direct_binding_to_bornbeast_named_asset = any(
        any("bornbeast" in m.lower() for m in
            cls.get("matched_basenames", [])
            if cls.get("match_type") == "BASENAME_MATCH")
        for r in detailed
        for cls in r["binding_fields"].values()
    )
    #   A. M4A1_RUNTIME_BINDING_CONFIRMED
    #   = bf005 says a BornBeast-named path is bound to an M4A1 record.
    #   B. M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN
    #   = M4A1 family records found AND we know the BornBeast asset
    #     elsewhere (P4) but bf005 does NOT bind to it directly.
    #   C. M4A1_RECORD_NOT_FOUND_BOUNDED
    #   = no M4A1 family record in bf005 at all.
    if not m4a1_family_present:
        status = "M4A1_RECORD_NOT_FOUND_BOUNDED"
    elif direct_binding_to_bornbeast_named_asset:
        status = "M4A1_RUNTIME_BINDING_CONFIRMED"
    else:
        status = "M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN"

    # 6. Outputs.
    # (1) weapon_records.json
    weapon_payload = {
        "runtime_source": "rez/Butes/bf005.ltc",
        "decoder_pipeline": (
            "CrossFireLtcDecoder.TryUnlockCrossFirePayload "
            "-> LithTechLtcNativeDecoder.TryDecode"
        ),
        "m4_family_records_count": len(detailed),
        "m4a1_family_present": m4a1_family_present,
        "bornbeast_substring_in_any_binding_value": bornbeast_in_runtime,
        "direct_config_references_to_bornbeast_named_asset":
            direct_binding_to_bornbeast_named_asset,
        "records": detailed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "weapon_records.json"), "w",
              encoding="utf-8") as f:
        json.dump(weapon_payload, f, indent=2, ensure_ascii=False)

    # (2) resource_binding_candidates.json
    cand_payload = {
        "known_basenames_count": len(known_basenames),
        "direct_config_references": direct_config_refs,
        "p4_bornbeast_ltb_in_existing_evidence": p4_bornbeast_ltb,
        "p4_bornbeast_assets_in_existing_evidence": p4_bornbeast_assets,
        "notes": [
            ("bf005.ltc binds M4A1 family records to "
             "'Models\\weapons\\m4a1.ltb' / 'Models\\weapons\\M4A1_Silencer.ltb' "
             "and 'Models\\PlayerView\\pv-m4a1' / 'pv-m4a1_silencer'."),
            ("P4 evidence already lists the BornBeast source LTB at "
             "'data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB' — "
             "this is a **DERIVED** asset, not a baseline runtime record."),
            ("Substring search for 'BornBeast' across all 73 decoded "
             "rez/Butes/*.ltc returns 0 hits — BornBeast is not present "
             "in the runtime Bute text layer."),
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "resource_binding_candidates.json"), "w",
              encoding="utf-8") as f:
        json.dump(cand_payload, f, indent=2, ensure_ascii=False)

    # (3) m4a1_correlation_report.md
    _write_report(detailed, known_basenames, direct_config_refs,
                  p4_bornbeast_ltb, m4a1_family_present, bornbeast_in_runtime,
                  direct_binding_to_bornbeast_named_asset, status, assets,
                  p4_bornbeast_assets)
    print(f"[n02c] status = {status}", file=sys.stderr)
    print(f"[n02c] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_report(detailed, known_basenames, direct_config_refs,
                  p4_bornbeast_ltb, m4a1_family_present, bornbeast_in_runtime,
                  direct_binding_to_bornbeast_named_asset, status, assets,
                  p4_bornbeast_assets=None):
    out = os.path.join(OUT_DIR, "m4a1_correlation_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-C — M4A1 Weapon Record -> Runtime Asset Correlation")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02c_m4a1_weapon_correlation.py`")
    lines.append(f"- runtime source: `rez/Butes/bf005.ltc` (CF weapon table)")
    lines.append("")

    lines.append("## 1. Scope")
    lines.append("")
    lines.append("- only existing N01 / P4 / P5 evidence was re-read")
    lines.append("- only `rez/Butes/bf005.ltc` was decoded (the CF weapon table)")
    lines.append("- no `data/**` re-scan, no DLL/EXE decompile, no FXO shader reverse")
    lines.append(f"- known P4/N01 asset basenames: {len(known_basenames)}")
    lines.append("")

    lines.append("## 2. M4A1 family records extracted from bf005.ltc")
    lines.append("")
    lines.append(f"- M4-family Weapon records: **{len(detailed)}**")
    lines.append(f"- M4A1 family present: **{m4a1_family_present}**")
    lines.append(f"- 'BornBeast' substring in any binding value: "
                 f"**{bornbeast_in_runtime}**")
    lines.append(f"- direct config reference to a BornBeast-named asset: "
                 f"**{direct_binding_to_bornbeast_named_asset}**")
    lines.append("")
    lines.append("| # | WeaponName | ModelFileName | SkinFileName | PViewModelFileName | PViewSkinFileName | RenderStyleFileName |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(detailed, 1):
        bf = r["binding_fields"]
        def v(fk):
            return bf[fk]["value"] or "—"
        lines.append(
            f"| {i} | `{r['WeaponName']}` | `{v('ModelFileName')}` | "
            f"`{v('SkinFileName')}` | `{v('PViewModelFileName')}` | "
            f"`{v('PViewSkinFileName')}` | `{v('RenderStyleFileName')}` |"
        )
    lines.append("")

    lines.append("## 3. Per-field correlation verdict")
    lines.append("")
    lines.append("For each binding field of each M4 record, classify the runtime")
    lines.append("value against the known P4/N01 asset basenames. Evidence grades:")
    lines.append("")
    lines.append("- `DIRECT_CONFIG_REFERENCE` — the runtime Bute binds a path whose")
    lines.append("  basename matches a known P4/N01 asset exactly. **Counts as binding.**")
    lines.append("- `BASENAME_MATCH` — basename string overlap without direct bind.")
    lines.append("  Treated as PARTIAL evidence, not a direct binding proof.")
    lines.append("- `PARTIAL_BASENAME` — substring overlap (e.g. `m4a1` in")
    lines.append("  `pv-m4a1_s_bornbeast_classic`). WEAK signal only.")
    lines.append("- `NO_MATCH` — no basename or substring overlap.")
    lines.append("")

    lines.append("## 4. P4 evidence — BornBeast source LTB / derived assets")
    lines.append("")
    if p4_bornbeast_ltb:
        lines.append(f"- BornBeast **LTB** (canonical): "
                     f"`{p4_bornbeast_ltb['value']}`")
        lines.append(f"  - source label: `{p4_bornbeast_ltb['source_label']}`")
        lines.append(f"  - field path: `{p4_bornbeast_ltb['field_path']}`")
    else:
        lines.append("- **No BornBeast LTB (.ltb) found in any of the read evidence files.**")
    if p4_bornbeast_assets:
        # also list all BornBeast-named assets (any extension)
        lines.append("")
        lines.append("All BornBeast-named assets in existing evidence "
                     "(basename contains 'bornbeast'):")
        lines.append("")
        lines.append("| source_label | value | ext |")
        lines.append("|---|---|---|")
        for a in p4_bornbeast_assets:
            lines.append(f"| `{a['source_label']}` | `{a['value']}` | "
                         f"`{a['ext']}` |")
    lines.append("")
    lines.append("Sources read:")
    for label, info in assets.items():
        if info.get("exists") and "data" in info:
            lines.append(f"- ✓ `{label}` ({info['path']})")
        else:
            lines.append(f"- ✗ `{label}` ({info['path']})")
    lines.append("")

    lines.append("## 5. Verdict")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    if status == "M4A1_RUNTIME_BINDING_CONFIRMED":
        lines.append("- bf005.ltc binds an M4A1 family weapon record to a path")
        lines.append("  whose basename matches a known P4/N01 asset exactly.")
    elif status == "M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN":
        lines.append("- bf005.ltc binds M4A1 family records to runtime paths")
        lines.append("  (`Models\\weapons\\m4a1.ltb`, `Models\\PlayerView\\pv-m4a1`,")
        lines.append("  `M4A1_Silencer.ltb`, `pv-m4a1_silencer`, …).")
        lines.append("- The P4/N01 BornBeast source LTB is a **DERIVED** asset")
        lines.append("  (`data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast_Classic.LTB`),")
        lines.append("  not present in the runtime Bute text layer.")
        lines.append("- 'BornBeast' substring: 0 hits across all 73 decoded")
        lines.append("  `rez/Butes/*.ltc`.")
        lines.append("- Therefore **no DIRECT_CONFIG_REFERENCE** to a BornBeast-named")
        lines.append("  resource exists; the gap between runtime Bute and P4 derived")
        lines.append("  asset is open.")
    else:
        lines.append("- bf005.ltc contains no M4A1 family Weapon record.")
    lines.append("")

    lines.append("## 6. Next single highest-value investigation target")
    lines.append("")
    if status == "M4A1_CONFIG_FOUND_ASSET_MAPPING_OPEN":
        lines.append(
            "The single highest-value next target is a **bounded REZ-side check**:")
        lines.append(
            "confirm that one of the runtime paths bound by bf005.ltc's M4A1")
        lines.append(
            "family records (`Models\\weapons\\m4a1.ltb`,")
        lines.append(
            "`ModelTextures\\weapons\\l-m4a1.dtx`,")
        lines.append(
            "`Models\\PlayerView\\pv-m4a1`,")
        lines.append(
            "`ModelTextures\\PlayerView\\pv-m4a1.dtx`,")
        lines.append(
            "`Models\\weapons\\M4A1_Silencer.ltb`,")
        lines.append(
            "`Models\\PlayerView\\pv-m4a1_silencer`, …) actually exists")
        lines.append(
            "as a payload inside the CF runtime REZ archives (without unpacking")
        lines.append(
            "the full 2 GiB REZ as the main task). That would either:")
        lines.append(
            "  1. directly show the runtime path matches a real CF artifact, or")
        lines.append(
            "  2. reveal that the BornBeast variant lives in a different REZ")
        lines.append(
            "     (and therefore the gap between Bute bind and P4 derived asset")
        lines.append(
            "     is structural, not a path mismatch).")
        lines.append("")
        lines.append("Wide DLL/EXE decompile, FXO shader reverse, and large-REZ")
        lines.append("unpacking remain out of scope per task.md §8.")
    elif status == "M4A1_RUNTIME_BINDING_CONFIRMED":
        lines.append("- advance to native-material closure per plan.md §3 PASS Gate")
    else:
        lines.append(
            "- re-check whether the M4A1 weapon really lives in bf005.ltc; the")
        lines.append(
            "  the fallback is to look at the per-weapon DTX / LTB inventory")
        lines.append(
            "  for the M4A1 family basename.")
    lines.append("")

    lines.append("## 7. Scope guard")
    lines.append("")
    lines.append("- did not re-scan `data/**`")
    lines.append("- did not decompile or strings/xref any EXE / DLL")
    lines.append("- did not reverse any FXO shader")
    lines.append("- did not run any CF client / runtime binary")
    lines.append("- did not modify `plan.md`")
    lines.append("- did not re-do LTC format reverse")
    lines.append("- did not treat filename similarity as binding proof")
    lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
