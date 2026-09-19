#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-G — Dump LightCorrectionLegacyShader / SpecularMapName values."""
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
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import n03b_rez_packed_config as n03b  # type: ignore  # noqa: E402
import n03c_material_graph as n03c  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
OUT_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition", "n03g_legacy_shader_fields",
)
os.makedirs(OUT_DIR, exist_ok=True)

FIELDS = (
    "LightCorrectionLegacyShader",
    "SpecularMapName",
    "SpecularMapName2",
    "SpecularMapName3",
    "SpecularPower",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cf-dir", default=None)
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02dr1)
        importlib.reload(n02er2)

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    t0 = time.time()
    rb = os.path.join(CF_DIR, "rez", "RB001.REZ")
    idx = n02dr1.read_rez_index(rb)
    e = {f["full_path"].upper(): f for f in idx["files"]}.get("BUTES/BF005.LTC")
    if not e:
        return 2
    dec = n03b.decode_ltc_bytes(
        n02er2.read_payload_bytes(rb, e["data_offset"], e["size"])
    )
    if not dec["ok"]:
        return 2
    blocks = n03c.walk_raw_blocks(dec["text"])

    rows = []
    for i, (_raw, parsed) in enumerate(blocks):
        present = {k: parsed[k] for k in FIELDS if k in parsed and parsed[k] != ""}
        if not present:
            continue
        wn = parsed.get("WeaponName") or ""
        rows.append({
            "record_index": i,
            "head": parsed.get("_head", ""),
            "WeaponName": wn,
            "WeaponName_gbk": n03b.gbk_display(wn),
            "StandardName": parsed.get("StandardName") or "",
            "fields": present,
        })

    rf017 = os.path.join(CF_DIR, "rez", "rf017.rez")
    cfg_basenames = set()
    if os.path.isfile(rf017):
        ridx = n02dr1.read_rez_index(rf017)
        for f in ridx["files"]:
            fp = f["full_path"].replace("\\", "/").upper()
            if fp.startswith("WEAPONSHADER/") and f["name"].upper().endswith(".CFG"):
                cfg_basenames.add(os.path.splitext(f["name"])[0].upper())

    shader_vals = []
    cfg_exact = []
    for r in rows:
        v = r["fields"].get("LightCorrectionLegacyShader")
        if v is None:
            continue
        shader_vals.append(str(v))
        stem = os.path.splitext(os.path.basename(str(v).replace("\\", "/")))[0].upper()
        if stem and stem in cfg_basenames:
            cfg_exact.append({"weapon": r["WeaponName_gbk"], "value": v, "cfg_stem": stem})

    unique_shader = Counter(shader_vals)
    numeric_only = bool(shader_vals) and all(
        str(v).strip().lstrip("+-").replace(".", "", 1).isdigit()
        for v in unique_shader
    )
    if cfg_exact:
        status, conf = "LEGACY_SHADER_FIELD_IS_CFG_NAME", "HIGH"
    elif numeric_only:
        status, conf = "SCOPED_NEGATIVE", "HIGH"
    elif shader_vals:
        status, conf = "CANDIDATE_ONLY", "MEDIUM"
    else:
        status, conf = "SCOPED_NEGATIVE", "HIGH"

    elapsed = time.time() - t0
    print(f"[n03g] rows={len(rows)} shader_vals={len(shader_vals)} "
          f"cfg_exact={len(cfg_exact)} status={status}", file=sys.stderr)

    payload = {
        "task": "P4-M01-N03-G",
        "status": status,
        "confidence": conf,
        "rows": rows,
        "light_correction_value_counts": dict(unique_shader),
        "cfg_basename_exact_hits": cfg_exact,
        "weaponshader_cfg_stem_count": len(cfg_basenames),
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "field_dump.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = []
    a = lines.append
    a("# P4-M01-N03-G — LightCorrectionLegacyShader / SpecularMapName dump")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{conf}**")
    a(f"- records with any target field: {len(rows)}")
    a(f"- WeaponShader CFG stems in rf017: {len(cfg_basenames)}")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("## 1. LightCorrectionLegacyShader value counts")
    a("")
    if not unique_shader:
        a("**None.**")
        a("")
    else:
        a("| value | count | exact CFG stem in WeaponShader/ |")
        a("|---|---|---|")
        for v, n in unique_shader.most_common():
            stem = os.path.splitext(os.path.basename(v.replace("\\", "/")))[0].upper()
            a(f"| `{v}` | {n} | {stem in cfg_basenames} |")
        a("")
    a("## 2. Per-weapon dump")
    a("")
    a("| i | WeaponName | StandardName | LightCorrectionLegacyShader | SpecularMapName | SpecularPower |")
    a("|---|---|---|---|---|---|")
    for r in rows:
        f = r["fields"]
        a(f"| {r['record_index']} | `{r['WeaponName_gbk']}` | `{r['StandardName']}` | "
          f"`{f.get('LightCorrectionLegacyShader','')}` | "
          f"`{f.get('SpecularMapName','')}` | `{f.get('SpecularPower','')}` |")
    a("")
    a("黑骑士 / `M4A1_S_BornBeast` 不在此表中（字段缺失）。")
    a("")
    a("## 3. Remaining ambiguity")
    a("")
    a("- `LightCorrectionLegacyShader` is the integer flag `1`, not a CFG name.")
    a("- `SpecularMapName` is a `.dtx` path on later skins; 黑骑士 lacks it.")
    a("- Missing field on 黑骑士 is not proof of StandardName convention.")
    a("- P4-M01 is not PASS.")
    a("")
    a(f"**status**: `{status}`")
    a("")
    with open(os.path.join(OUT_DIR, "field_dump_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[n03g] wrote {OUT_DIR}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
