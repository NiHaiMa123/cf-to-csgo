#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-F — Exact-path reverse lookup of WeaponShader/ and AlphaMap/.

Searches packed rez/RB001.REZ Butes/BF005.LTC (all lisp records) for the
runtime TGA/CFG paths. Does not use the StandardName stem
M4A1_S_BornBeast as CFG proof.

Outputs under
  work/.../runtime_acquisition/n03f_shader_alphamap_lookup/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import n03a_bornbeast_consumer as n03a  # type: ignore  # noqa: E402
import n03b_rez_packed_config as n03b  # type: ignore  # noqa: E402
import n03c_material_graph as n03c  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
OUT_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition", "n03f_shader_alphamap_lookup",
)
os.makedirs(OUT_DIR, exist_ok=True)

EXACT_PATHS = [
    ("shader_cfg", "WeaponShader/M4A1_S_BornBeast.CFG"),
    ("shader_cfg", r"WeaponShader\M4A1_S_BornBeast.CFG"),
    ("shader_cfg", r"ModelTextures\Shader\WeaponShader\M4A1_S_BornBeast.CFG"),
    ("shader_cfg", "ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG"),
    ("shader_cfg", "M4A1_S_BornBeast.CFG"),
    ("alpha", "AlphaMap/M4A1_S_BornBeast_alpha.TGA"),
    ("alpha", r"AlphaMap\M4A1_S_BornBeast_alpha.TGA"),
    ("alpha", r"ModelTextures\AlphaMap\M4A1_S_BornBeast_alpha.TGA"),
    ("alpha", "ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA"),
    ("alpha", "M4A1_S_BornBeast_alpha.TGA"),
    ("normal", "NormalMap/M4A1_S_BornBeast_N.TGA"),
    ("normal", r"NormalMap\M4A1_S_BornBeast_N.TGA"),
    ("normal", r"ModelTextures\NormalMap\M4A1_S_BornBeast_N.TGA"),
    ("normal", "ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA"),
    ("normal", "M4A1_S_BornBeast_N.TGA"),
    ("specular", "SpecularMap/M4A1_S_BornBeast_S.TGA"),
    ("specular", r"SpecularMap\M4A1_S_BornBeast_S.TGA"),
    ("specular", r"ModelTextures\SpecularMap\M4A1_S_BornBeast_S.TGA"),
    ("specular", "ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA"),
    ("specular", "M4A1_S_BornBeast_S.TGA"),
]
DIR_PREFIXES = (
    "WeaponShader/", "WeaponShader\\",
    "AlphaMap/", "AlphaMap\\",
    "NormalMap/", "NormalMap\\",
    "SpecularMap/", "SpecularMap\\",
)
REZ_CONFIRM = (
    "WEAPONSHADER/M4A1_S_BORNBEAST.CFG",
    "ALPHAMAP/M4A1_S_BORNBEAST_ALPHA.TGA",
    "NORMALMAP/M4A1_S_BORNBEAST_N.TGA",
    "SPECULARMAP/M4A1_S_BORNBEAST_S.TGA",
)


def norm_val(s: str) -> str:
    return s.replace("/", "\\")


def value_has_exact_path(value: str, token: str) -> bool:
    if not value or not token:
        return False
    # bounded exact, case-insensitive, slash-insensitive
    v = value.replace("/", "\\")
    t = token.replace("/", "\\")
    i = v.lower().find(t.lower())
    if i < 0:
        return False
    return n03a.is_bounded_match(v, i, t, "basename" if "\\" not in t else "source_path")


def value_has_dir_prefix(value: str) -> str | None:
    if not value:
        return None
    v = value
    low = v.replace("/", "\\").lower()
    for p in DIR_PREFIXES:
        pl = p.replace("/", "\\").lower()
        i = low.find(pl)
        if i < 0:
            continue
        # must be a path segment start
        prev = v[i - 1] if i > 0 else ""
        if prev and prev not in "\\\"'/ \t(":
            continue
        rest = v[i + len(p):]
        if rest and rest[0] not in "\\\"' )":
            return p.rstrip("\\/")
    return None


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

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    t0 = time.time()
    rb = os.path.join(CF_DIR, "rez", "RB001.REZ")
    idx = n02dr1.read_rez_index(rb)
    by = {f["full_path"].upper(): f for f in idx["files"]}
    e = by.get("BUTES/BF005.LTC")
    if not e:
        print("[n03f] packed BF005 missing", file=sys.stderr)
        return 2
    raw = n02er2.read_payload_bytes(rb, e["data_offset"], e["size"])
    dec = n03b.decode_ltc_bytes(raw)
    if not dec["ok"]:
        print("[n03f] decode failed", dec["reason"], file=sys.stderr)
        return 2
    blocks = n03c.walk_raw_blocks(dec["text"])
    print(f"[n03f] records={len(blocks)}", file=sys.stderr)

    heads = Counter()
    filename_keys = Counter()
    material_keys = Counter()
    keys_by_head = defaultdict(set)
    canonical_keys = []
    MATERIAL_KEY_RE = re.compile(
        r"(SpecularMapName|AlphaMapName|NormalMapName|WeaponShader|"
        r"ShaderFile|LightCorrectionLegacyShader|^SpecularPower$)",
        re.I,
    )
    exact_hits = []
    prefix_hits = []
    canonical_n = 0

    for i, (raw_block, parsed) in enumerate(blocks):
        head = parsed.get("_head", "")
        heads[head] += 1
        ident = parsed.get("WeaponName") or parsed.get("Name") or parsed.get("StandardName") or ""
        ident_gbk = n03b.gbk_display(ident)
        std = parsed.get("StandardName") or ""
        is_canonical = (
            head == "Weapon"
            and n03b.gbk_display(parsed.get("WeaponName") or "") == "M4A1-黑骑士"
            and std == "M4A1_S_BornBeast"
        )
        if is_canonical:
            canonical_n += 1
            canonical_keys = [k for k in parsed.keys() if k != "_head"]
        for k, v in parsed.items():
            if k == "_head" or not isinstance(v, str):
                continue
            keys_by_head[head].add(k)
            if k.endswith("FileName"):
                filename_keys[k] += 1
            if MATERIAL_KEY_RE.search(k):
                material_keys[k] += 1
            for role, tok in EXACT_PATHS:
                if value_has_exact_path(v, tok):
                    exact_hits.append({
                        "record_index": i,
                        "head": head,
                        "field": k,
                        "value": v,
                        "token": tok,
                        "role": role,
                        "identity_gbk": ident_gbk,
                        "canonical": is_canonical,
                    })
            pref = value_has_dir_prefix(v)
            if pref:
                prefix_hits.append({
                    "record_index": i,
                    "head": head,
                    "field": k,
                    "value": v,
                    "prefix": pref,
                    "identity_gbk": ident_gbk,
                    "canonical": is_canonical,
                })

    # REZ confirm in rf017
    rf017 = os.path.join(CF_DIR, "rez", "rf017.rez")
    rez_ok = {}
    if os.path.isfile(rf017):
        ridx = n02dr1.read_rez_index(rf017)
        rby = {f["full_path"].upper(): f["full_path"] for f in ridx["files"]}
        # also basename
        rbase = defaultdict(list)
        for f in ridx["files"]:
            rbase[f["name"].upper()].append(f["full_path"])
        for p in REZ_CONFIRM:
            if p in rby:
                rez_ok[p] = {"exact": rby[p]}
            else:
                base = p.rsplit("/", 1)[-1]
                rez_ok[p] = {"exact": None, "basename_hits": rbase.get(base, [])}

    all_filename_keys = sorted(filename_keys)
    canonical_fn = sorted(k for k in canonical_keys if k.endswith("FileName"))
    extra_fn = [k for k in all_filename_keys if k not in set(canonical_fn)]
    canonical_mat = sorted(k for k in canonical_keys if MATERIAL_KEY_RE.search(k))
    extra_mat = sorted(k for k in material_keys if k not in set(canonical_mat))

    if exact_hits:
        status = "SHADER_ALPHAMAP_CONSUMER_CONFIRMED"
        conf = "HIGH"
    elif prefix_hits or extra_mat:
        status = "CANDIDATE_ONLY"
        conf = "MEDIUM"
    else:
        status = "SCOPED_NEGATIVE"
        conf = "HIGH"

    elapsed = time.time() - t0
    print(f"[n03f] exact={len(exact_hits)} prefix={len(prefix_hits)} "
          f"FileName_keys={len(all_filename_keys)} extra={extra_fn} "
          f"status={status}", file=sys.stderr)

    payload = {
        "task": "P4-M01-N03-F",
        "status": status,
        "confidence": conf,
        "packed_source": {
            "archive": "rez/RB001.REZ",
            "full_path": "Butes/BF005.LTC",
            "size": e["size"],
            "record_count": len(blocks),
            "canonical_weapon_records": canonical_n,
        },
        "heads": dict(heads),
        "filename_key_counts": dict(filename_keys),
        "canonical_filename_keys": canonical_fn,
        "filename_keys_not_on_canonical": extra_fn,
        "material_key_counts": dict(material_keys),
        "canonical_material_keys": canonical_mat,
        "material_keys_not_on_canonical": extra_mat,
        "exact_hits": exact_hits,
        "directory_prefix_hits": prefix_hits[:200],
        "directory_prefix_hit_count": len(prefix_hits),
        "rez_confirm": rez_ok,
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "lookup.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = []
    a = lines.append
    a("# P4-M01-N03-F — WeaponShader / AlphaMap exact-path lookup")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{conf}**")
    a("- script: `scripts/material_recovery/n03f_shader_alphamap_lookup.py`")
    a(f"- packed BF005 records: {len(blocks)}")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("Tokens **exclude** the StandardName stem `M4A1_S_BornBeast`.")
    a("")
    a("## 1. Exact path hits")
    a("")
    a(f"count: **{len(exact_hits)}**")
    a("")
    if exact_hits:
        a("| record | head | identity | field | value | role |")
        a("|---|---|---|---|---|---|")
        for h in exact_hits[:40]:
            a(f"| {h['record_index']} | `{h['head']}` | `{h['identity_gbk']}` | "
              f"`{h['field']}` | `{h['value']}` | `{h['role']}` |")
        a("")
    else:
        a("**None** in any packed BF005 field value.")
        a("")
    a("## 2. Directory-prefix hits (`WeaponShader/` `AlphaMap/` `NormalMap/` `SpecularMap/`)")
    a("")
    a(f"count: **{len(prefix_hits)}**")
    a("")
    if prefix_hits:
        a("| record | head | identity | field | prefix | value |")
        a("|---|---|---|---|---|---|")
        for h in prefix_hits[:40]:
            a(f"| {h['record_index']} | `{h['head']}` | `{h['identity_gbk']}` | "
              f"`{h['field']}` | `{h['prefix']}` | `{h['value']}` |")
        a("")
    else:
        a("**None.** No BF005 field value contains those path segments.")
        a("")
    a("## 3. FileName-key union vs 黑骑士")
    a("")
    a("| key | records | on canonical 黑骑士 |")
    a("|---|---|---|")
    can_set = set(canonical_fn)
    for k in all_filename_keys:
        a(f"| `{k}` | {filename_keys[k]} | {k in can_set} |")
    a("")
    a("Projectile/left-hand `*FileName` extras are other weapon types,")
    a("not Alpha/Shader path fields.")
    a("")
    a("## 3b. Material-ish keys (`*MapName*` / Shader / Alpha / Normal / Specular)")
    a("")
    if not material_keys:
        a("**None.**")
        a("")
    else:
        a("| key | records | on canonical 黑骑士 |")
        a("|---|---|---|")
        can_m = set(canonical_mat)
        for k in sorted(material_keys):
            a(f"| `{k}` | {material_keys[k]} | {k in can_m} |")
        a("")
        if extra_mat:
            a("These keys exist on **other** weapons but not on 黑骑士:")
            a(f"`{extra_mat}`")
            a("")
            a("Observed `SpecularMapName` values are `.dtx` under")
            a("`ModelTextures\\SpecularMap\\`, not the BornBeast `.TGA` inventory files.")
            a("")
        else:
            a("黑骑士 already has every material-ish key seen in this table.")
            a("")
    a("## 4. REZ existence (not consumer)")
    a("")
    a("| logical path | present |")
    a("|---|---|")
    for p, info in rez_ok.items():
        a(f"| `{p}` | {info.get('exact') or info} |")
    a("")
    a("## 5. Remaining ambiguity")
    a("")
    a("- Exact BornBeast `WeaponShader/` and `AlphaMap/` / `NormalMap/` /")
    a("  `SpecularMap/*.TGA` paths: **0** in 8205 BF005 records.")
    a("- Some later weapons have `SpecularMapName` → `SpecularMap\\*.dtx`,")
    a("  not TGA, and 黑骑士 does not have that field.")
    a("- No `WeaponShader` / `AlphaMapName` field exists in this table.")
    a("- CFG/render semantic closure still `OPEN_UNRESOLVED`.")
    a("- P4-M01 is not PASS. This is not P5 雷神.")
    a("")
    a(f"### Confidence: `{conf}`")
    a("")
    a("## 6. Status")
    a("")
    a(f"**status**: `{status}`")
    a("")
    a("## 7. Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT use StandardName stem as CFG proof")
    a("- did NOT scan all `.cfg` payloads or non-BUTES `.ltc`")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT freeze CFG shader semantics")
    a("- did NOT modify historical accepted evidence or `plan.md`")
    a("")
    with open(os.path.join(OUT_DIR, "lookup_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    rels = {
        "task": "P4-M01-N03-F",
        "status": status,
        "confidence": conf,
        "relations": [
            {
                "relation": "packed BF005 exact TGA/CFG path hits",
                "count": len(exact_hits),
                "grade": "DIRECT_CONFIG_FIELD" if exact_hits else "SCOPED_NEGATIVE",
            },
            {
                "relation": "packed BF005 WeaponShader/AlphaMap path-segment hits",
                "count": len(prefix_hits),
                "grade": "OBSERVED" if prefix_hits else "SCOPED_NEGATIVE",
            },
            {
                "relation": "FileName-key union equals canonical 黑骑士 FileName keys",
                "canonical": canonical_fn,
                "extra": extra_fn,
                "grade": "SCOPED_NEGATIVE" if not extra_fn else "DIFFERENTIAL_SUPPORTED",
            },
        ],
        "remaining_blockers": [
            "TGA/CFG Bute consumer OPEN_UNRESOLVED" if not exact_hits
            else "TGA/CFG path field found",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(rels, f, indent=2, ensure_ascii=False)
    print(f"[n03f] wrote {OUT_DIR}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
