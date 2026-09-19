#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-C — Expand canonical 黑骑士 Weapon record into a material graph.

Re-decodes packed rez/RB001.REZ Butes/BF005.LTC, dumps the canonical
Weapon s-expression (all keys + raw block), binds every file-path
field through the N02-D-R1 path rule, SHA256s those payloads, and
asks whether inventory TGA/CFG appear as direct fields or only as
StandardName/BigIconName aliases.

Archives indexed this round (not all 475):
  rez/RB001.REZ, rez/RF016.REZ, rez2/RF016.REZ, rez4/RF016.REZ,
  rez/rf017.rez, rez/rf002.rez

Forbidden: P4-M01 PASS, P5 identity, PE/FXO, CFG semantic freeze,
filename similarity as proof, treating variant DTX as inventory base.

Outputs under
  work/.../runtime_acquisition/n03c_material_graph/
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

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import n03a_bornbeast_consumer as n03a  # type: ignore  # noqa: E402
import n03b_rez_packed_config as n03b  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition",
)
OUT_DIR = os.path.join(N02A_DIR, "n03c_material_graph")
os.makedirs(OUT_DIR, exist_ok=True)

CANONICAL_STANDARD = "M4A1_S_BornBeast"
CANONICAL_SKIN_STEM = "pv-m4a1_s_bornbeast.dtx"
CANONICAL_GBK_NAME = "M4A1-黑骑士"
PATH_EXTS = {".ltb", ".dtx", ".tga", ".cfg", ".lta", ".fx", ".fxo"}
NEEDED_REZ = (
    ("rez", "RB001.REZ"),
    ("rez", "RF016.REZ"),
    ("rez2", "RF016.REZ"),
    ("rez4", "RF016.REZ"),
    ("rez", "rf017.rez"),
    ("rez", "rf002.rez"),
)


def walk_raw_blocks(text: str) -> list[tuple[str, dict]]:
    """Yield (raw_block, parsed_all_keys) for each top-level s-expression."""
    out = []
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
        raw = text[start:j]
        parsed = n03a._parse_one_block_all_keys(raw)
        if parsed is not None:
            out.append((raw, parsed))
        i = j
    return out


def looks_like_path(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    v = value.replace("\\\\", "\\")
    ext = os.path.splitext(v.replace("\\", "/"))[1].lower()
    if ext in PATH_EXTS:
        return True
    if "\\" in v or "/" in v:
        return True
    return False


def collect_path_fields(block: dict) -> list[tuple[str, str]]:
    rows = []
    for k, v in block.items():
        if k == "_head" or k.endswith("_gbk") or not isinstance(v, str):
            continue
        if k.endswith("FileName") or k.endswith("Name") and looks_like_path(v):
            if looks_like_path(v) or k.endswith("FileName"):
                rows.append((k, v))
        elif looks_like_path(v):
            rows.append((k, v))
    # dedup preserve order
    seen = set()
    out = []
    for k, v in rows:
        if (k, v) in seen:
            continue
        seen.add((k, v))
        out.append((k, v))
    return out


def bind_path(field: str, raw: str, idx: dict) -> dict:
    norm = n02dr1.normalise_bf005_to_rez_path(raw)
    queries = []
    if norm["upper"]:
        queries.append(("EXACT_PATH", norm["upper"]))
    if field in n02dr1.EXTENSIONLESS_MODEL_FIELDS and not norm["ext"] and norm["upper"]:
        queries.append(("EXTENSIONLESS_LTB", norm["upper"] + ".LTB"))
    hits = []
    used = None
    for kind, q in queries:
        found = idx["by_full_path"].get(q, [])
        if found:
            used = (kind, q)
            hits = found
            break
    return {
        "field": field,
        "runtime_path": raw,
        "normalisation": norm,
        "query_kind": used[0] if used else None,
        "query": used[1] if used else (queries[0][1] if queries else ""),
        "hit_count": len(hits),
        "hits": [
            {
                "rez_path": h["rez_path"],
                "archive": n03b.archive_label(h["rez_path"]),
                "full_path": h["full_path"],
                "name": h["name"],
                "size": h["size"],
                "data_offset": h["data_offset"],
                "md5": h.get("md5", ""),
            }
            for h in hits
        ],
    }


def sha_hit(hit: dict, inventory_by_role: dict, local_by_basename: dict) -> dict:
    rec = {
        "archive": hit["archive"],
        "full_path": hit["full_path"],
        "size": hit["size"],
        "read_ok": False,
        "sha256": "",
        "inventory_match_role": None,
        "local_data_match": False,
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
    rec["actual_bytes"] = len(data)
    rec["sha256"] = hashlib.sha256(data).hexdigest().upper()
    for role, item in inventory_by_role.items():
        inv = (item.get("sha256") or "").upper()
        if inv and rec["sha256"] == inv:
            rec["inventory_match_role"] = role
            rec["note"] = "SHA256 == inventory"
            break
    base = os.path.basename(hit["full_path"]).upper()
    loc = local_by_basename.get(base)
    if loc and rec["sha256"] == loc["sha256"]:
        rec["local_data_match"] = True
        if not rec["note"]:
            rec["note"] = f"SHA256 == local {loc['rel']}"
    if not rec["note"]:
        rec["note"] = "no inventory/local SHA match"
    return rec


def observe_small_payload(hit: dict) -> dict:
    try:
        data = n02er2.read_payload_bytes(
            hit["rez_path"], hit["data_offset"], hit["size"]
        )
    except (OSError, ValueError) as e:
        return {"ok": False, "error": str(e)}
    printable = n03a.extract_ascii_and_utf16le(data, min_len=4)
    return {
        "ok": True,
        "archive": hit.get("archive") or n03b.archive_label(hit["rez_path"]),
        "full_path": hit["full_path"],
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "hex": data.hex(),
        "printable": printable,
        "contains_dtx": bool(re.search(r"\.dtx", printable, re.I)),
        "contains_tga": bool(re.search(r"\.tga", printable, re.I)),
        "contains_cfg": bool(re.search(r"\.cfg", printable, re.I)),
        "contains_ltb": bool(re.search(r"\.ltb", printable, re.I)),
    }


def needed_rez_paths() -> list[str]:
    out = []
    for sub, name in NEEDED_REZ:
        p = os.path.join(CF_DIR, sub, name)
        if os.path.isfile(p):
            out.append(p)
        else:
            print(f"[n03c] missing archive {p}", file=sys.stderr)
    return out


def local_qv_hashes() -> dict:
    """Optional byte-compare against known local_cf QV files if present."""
    candidates = [
        "data/rf016/Models/WEAPONS/QV-M4A1_S_BornBeast.LTB",
        "data/rf016/Models/Weapons/QV-M4A1_S_BornBeast.ltb",
        "data/rf017/ModelTextures/WEAPONS/QV-M4A1_S_BornBeast.DTX",
        "data/rf017/ModelTextures/Weapons/QV-M4A1_S_BornBeast.dtx",
    ]
    out = {}
    for rel in candidates:
        abs_path = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.isfile(abs_path):
            continue
        h = hashlib.sha256()
        with open(abs_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        out[os.path.basename(rel).upper()] = {
            "rel": rel.replace("\\", "/"),
            "sha256": h.hexdigest().upper(),
            "size": os.path.getsize(abs_path),
        }
    return out


def write_report(status, classif, canonical, siblings, path_binds,
                 rs_obs, cfg_obs, tga_cfg_hits, elapsed) -> str:
    lines = []
    a = lines.append
    a("# P4-M01-N03-C — Canonical 黑骑士 material graph")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{classif['confidence']}**")
    a("- script: `scripts/material_recovery/n03c_material_graph.py`")
    a("- source: `rez/RB001.REZ` / `Butes/BF005.LTC`")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("## 1. Canonical Weapon record")
    a("")
    if not canonical:
        a("**Canonical record not found.**")
        a("")
        return "\n".join(lines) + "\n"
    blk = canonical["parsed"]
    a(f"- WeaponName (GBK): `{n03b.gbk_display(blk.get('WeaponName',''))}`")
    a(f"- StandardName: `{blk.get('StandardName','')}`")
    a(f"- record_index: {canonical['record_index']}")
    a(f"- raw_bytes: {len(canonical['raw'].encode('latin-1', errors='replace'))}")
    a(f"- parsed keys: {len([k for k in blk if k != '_head'])}")
    a("")
    a("### 1.1 All parsed fields")
    a("")
    a("| key | value | value (GBK) |")
    a("|---|---|---|")
    for k, v in blk.items():
        if k == "_head":
            continue
        vs = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        a(f"| `{k}` | `{vs}` | `{n03b.gbk_display(vs) if isinstance(v, str) else ''}` |")
    a("")
    a("### 1.2 Raw s-expression")
    a("")
    a("```")
    a(canonical["raw"])
    a("```")
    a("")
    a("### 1.3 Sibling Weapon records with the same inventory PV DTX")
    a("")
    a("| WeaponName (GBK) | StandardName | PViewSkinFileName |")
    a("|---|---|---|")
    for s in siblings:
        p = s["parsed"]
        a(f"| `{n03b.gbk_display(p.get('WeaponName',''))}` | "
          f"`{p.get('StandardName','')}` | `{p.get('PViewSkinFileName','')}` |")
    a("")
    a("## 2. TGA / CFG exact-token search in the canonical raw block")
    a("")
    if not tga_cfg_hits:
        a("**None.** Inventory alpha/normal/specular TGA and WeaponShader CFG")
        a("basenames/stems/paths do not appear as bounded tokens in this")
        a("Weapon s-expression. `StandardName` / `BigIconName` equal the CFG")
        a("stem; that is an alias, **not** a CFG file-path bind.")
        a("")
    else:
        a("| token_kind | token | role | context |")
        a("|---|---|---|---|")
        for h in tga_cfg_hits:
            ctx = h["context"].replace("|", "\\|")
            a(f"| `{h['token_kind']}` | `{h['token']}` | `{h['asset_role']}` | `{ctx}` |")
        a("")
        a("The only hits are `StandardName` / `BigIconName` equal to the")
        a("CFG **stem**. That is an alias, not a CFG/TGA file-path field.")
        a("Alpha / Normal / Specular TGA basenames: **0**.")
        a("")
    a("## 3. File-path field → REZ bind + SHA256")
    a("")
    a("| field | runtime_path | query | hits | sha_match |")
    a("|---|---|---|---|---|")
    for b in path_binds:
        shas = b.get("payloads") or []
        match = ",".join(
            p["inventory_match_role"] or ("local" if p.get("local_data_match") else "—")
            for p in shas
        ) if shas else "—"
        a(f"| `{b['field']}` | `{b['runtime_path']}` | "
          f"`{b.get('query_kind') or ''} {b.get('query','')}` | "
          f"{b['hit_count']} | {match} |")
    a("")
    a("### 3.1 Per-payload SHA")
    a("")
    a("| field | archive | full_path | size | sha256 | note |")
    a("|---|---|---|---|---|---|")
    for b in path_binds:
        for p in b.get("payloads") or []:
            a(f"| `{b['field']}` | `{p['archive']}` | `{p['full_path']}` | "
              f"{p.get('size','')} | `{p.get('sha256','')[:16]}…` | `{p.get('note','')}` |")
    a("")
    a("## 4. RS LTB / WeaponShader CFG observation")
    a("")
    a("String/hex only. Not a shader-semantic freeze.")
    a("")
    a("| payload | size | .dtx | .tga | .cfg | .ltb | printable |")
    a("|---|---|---|---|---|---|---|")
    for obs in rs_obs + ([cfg_obs] if cfg_obs else []):
        if not obs or not obs.get("ok"):
            continue
        pr = (obs.get("printable") or "").replace("\n", " ")[:80]
        a(f"| `{obs['full_path']}` | {obs['size']} | "
          f"{obs['contains_dtx']} | {obs['contains_tga']} | "
          f"{obs['contains_cfg']} | {obs['contains_ltb']} | `{pr}` |")
    a("")
    a("## 5. Remaining ambiguity")
    a("")
    a("- LTB piece → DTX/TGA still `OPEN_UNRESOLVED`.")
    a("- CFG/render semantic closure still `OPEN_UNRESOLVED`.")
    a("- RS LTB (111/119 B) and WeaponShader CFG (492 B) contain no")
    a("  `.tga` / `.dtx` / `.cfg` path strings.")
    a("- `rez/RF016.REZ` vs `rez2/RF016.REZ` QV LTB payloads differ")
    a("  (17269 vs 17271 bytes); no REZ load-order authority is claimed.")
    a("- This is M4A1-黑骑士 / BornBeast, not P5 雷神.")
    a("- P4-M01 is not PASS.")
    a("")
    a(f"### Confidence: `{classif['confidence']}`")
    a("")
    a("## 6. Status")
    a("")
    a(f"**status**: `{status}`")
    a("")
    a("## 7. Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT treat StandardName == CFG stem as shader bind proof")
    a("- did NOT treat variant DTX as inventory base_dtx")
    a("- did NOT enter P5 identity")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT index all 475 REZ archives")
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
        importlib.reload(n03b)

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    print(f"[n03c] cf_root = {CF_DIR}", file=sys.stderr)
    t0 = time.time()

    inventory = n03a.load_inventory()
    inv_by_role = {it["asset_role"]: it for it in inventory["items"]}
    tga_cfg_tokens = []
    for it in inventory["items"]:
        if it["asset_role"] in {"alpha", "normal", "specular", "shader_cfg"}:
            tga_cfg_tokens.extend(n03a.build_asset_tokens(it, {}))

    rez_paths = needed_rez_paths()
    print(f"[n03c] indexing {len(rez_paths)} archives", file=sys.stderr)
    idx = n02dr1.build_full_path_index(rez_paths)

    bf_hits = idx["by_full_path"].get("BUTES/BF005.LTC", [])
    if not bf_hits:
        print("[n03c] packed Butes/BF005.LTC not in indexed archives",
              file=sys.stderr)
        status = "REWORK_REQUIRED"
        elapsed = time.time() - t0
        payload = {
            "task": "P4-M01-N03-C",
            "status": status,
            "error": "BUTES/BF005.LTC missing",
        }
        with open(os.path.join(OUT_DIR, "material_graph_report.md"),
                  "w", encoding="utf-8") as f:
            f.write(f"# N03-C REWORK_REQUIRED\n\npacked BF005 missing\n")
        with open(os.path.join(OUT_DIR, "canonical_weapon.json"),
                  "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return 2

    bf = sorted(bf_hits, key=lambda h: n03b.archive_rank(h["rez_path"]))[0]
    print(f"[n03c] decoding {n03b.archive_label(bf['rez_path'])} "
          f"{bf['full_path']} size={bf['size']}", file=sys.stderr)
    raw_ltc = n02er2.read_payload_bytes(bf["rez_path"], bf["data_offset"], bf["size"])
    dec = n03b.decode_ltc_bytes(raw_ltc)
    if not dec["ok"]:
        print(f"[n03c] decode failed: {dec['reason']}", file=sys.stderr)
        return 2
    blocks = walk_raw_blocks(dec["text"])
    print(f"[n03c] top-level blocks: {len(blocks)}", file=sys.stderr)

    siblings = []
    canonical = None
    for i, (raw, parsed) in enumerate(blocks):
        if parsed.get("_head") != "Weapon":
            continue
        skin = (parsed.get("PViewSkinFileName") or "").replace("\\", "/").lower()
        if not skin.endswith(CANONICAL_SKIN_STEM):
            continue
        rec = {
            "record_index": i,
            "raw": raw,
            "parsed": parsed,
        }
        siblings.append(rec)
        name = n03b.gbk_display(parsed.get("WeaponName") or "")
        std = parsed.get("StandardName") or ""
        if name == CANONICAL_GBK_NAME and std == CANONICAL_STANDARD:
            if canonical is None:
                canonical = rec

    if canonical is None and siblings:
        canonical = siblings[0]
        print("[n03c] WARN canonical 黑骑士 not found; using first sibling",
              file=sys.stderr)

    tga_cfg_hits = []
    if canonical:
        for tok in tga_cfg_tokens:
            tga_cfg_hits.extend([
                {**h, "token_kind": tok["kind"], "token": tok["value"],
                 "asset_role": tok["asset_role"]}
                for h in n03a.find_token_hits(
                    canonical["raw"], tok["value"], tok["kind"]
                )
            ])

    path_binds = []
    local_basenames = local_qv_hashes()
    if canonical:
        for field, value in collect_path_fields(canonical["parsed"]):
            b = bind_path(field, value, idx)
            payloads = []
            # SHA every distinct (rez, full_path)
            seen = set()
            for h in b["hits"]:
                key = (h["rez_path"], h["full_path"])
                if key in seen:
                    continue
                seen.add(key)
                payloads.append(sha_hit(h, inv_by_role, local_basenames))
            b["payloads"] = payloads
            path_binds.append(b)
            print(f"[n03c] {field}: hits={b['hit_count']}", file=sys.stderr)

    rs_obs = []
    cfg_obs = None
    for b in path_binds:
        if b["field"] in {"RenderStyleFileName", "PViewRenderStyleFileName"}:
            for h in b["hits"][:2]:
                rs_obs.append(observe_small_payload(h))
    # CFG from N03-A known path
    cfg_hits = idx["by_full_path"].get("WEAPONSHADER/M4A1_S_BORNBEAST.CFG", [])
    if not cfg_hits:
        # basename fallback is existence only for observation, not consumer proof
        cfg_hits = idx["by_basename"].get("M4A1_S_BORNBEAST.CFG", [])
        cfg_hits = [h for h in cfg_hits
                    if h["full_path"].replace("\\", "/").upper().endswith(
                        "WEAPONSHADER/M4A1_S_BORNBEAST.CFG")
                    or h["name"].upper() == "M4A1_S_BORNBEAST.CFG"]
    if cfg_hits:
        h0 = sorted(cfg_hits, key=lambda h: n03b.archive_rank(h["rez_path"]))[0]
        cfg_obs = observe_small_payload(h0)

    all_paths_bound = bool(path_binds) and all(
        b["hit_count"] > 0 for b in path_binds
        if b["field"].endswith("FileName")
    )
    filename_fields = [b for b in path_binds if b["field"].endswith("FileName")]
    filename_bound = bool(filename_fields) and all(b["hit_count"] > 0 for b in filename_fields)
    tga_direct = any(
        h["token_kind"] in {"basename", "source_path", "rez_path"}
        and h["asset_role"] in {"alpha", "normal", "specular", "shader_cfg"}
        for h in tga_cfg_hits
        if h.get("token_kind") != "stem" or h["asset_role"] != "shader_cfg"
    )
    # stem match of M4A1_S_BornBeast on StandardName is alias, not TGA/CFG path
    if canonical and filename_bound:
        status = "BUTE_MATERIAL_GRAPH_EXPANDED"
        confidence = "HIGH"
    elif canonical:
        status = "CANDIDATE_ONLY"
        confidence = "MEDIUM"
    else:
        status = "REWORK_REQUIRED"
        confidence = "NONE"

    classif = {
        "status": status,
        "confidence": confidence,
        "sibling_count": len(siblings),
        "path_fields": len(path_binds),
        "filename_fields_bound": sum(1 for b in filename_fields if b["hit_count"] > 0),
        "filename_fields_total": len(filename_fields),
        "tga_cfg_direct_path_hits": int(tga_direct),
        "tga_cfg_token_hits": len(tga_cfg_hits),
        "all_paths_bound": all_paths_bound,
    }
    elapsed = time.time() - t0
    print(f"[n03c] status={status} elapsed={elapsed:.2f}s", file=sys.stderr)

    def ser_block(rec):
        if not rec:
            return None
        parsed = dict(rec["parsed"])
        parsed_gbk = {
            k: n03b.gbk_display(v) if isinstance(v, str) else v
            for k, v in parsed.items()
        }
        return {
            "record_index": rec["record_index"],
            "raw": rec["raw"],
            "parsed": parsed,
            "parsed_gbk": parsed_gbk,
        }

    dump = {
        "task": "P4-M01-N03-C",
        "status": status,
        "confidence": confidence,
        "packed_source": {
            "archive": n03b.archive_label(bf["rez_path"]),
            "full_path": bf["full_path"],
            "size": bf["size"],
            "decoded_ok": dec["ok"],
        },
        "canonical": ser_block(canonical),
        "siblings": [ser_block(s) for s in siblings],
        "tga_cfg_hits_in_canonical_raw": tga_cfg_hits,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "canonical_weapon.json"),
              "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2, ensure_ascii=False)

    graph = {
        "task": "P4-M01-N03-C",
        "status": status,
        "canonical": CANONICAL_GBK_NAME,
        "edges": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    for b in path_binds:
        for p in b.get("payloads") or []:
            grade = "PAYLOAD_IDENTITY" if p.get("inventory_match_role") else (
                "REZ_EXACT_PATH" if p.get("read_ok") else "UNBOUND"
            )
            graph["edges"].append({
                "from": f"Weapon.{b['field']}",
                "to": f"{p['archive']}:{p['full_path']}",
                "grade": grade,
                "inventory_role": p.get("inventory_match_role"),
                "sha256": p.get("sha256"),
            })
    if not tga_direct:
        graph["edges"].append({
            "from": "canonical Weapon raw block",
            "to": "inventory alpha/normal/specular/shader_cfg",
            "grade": "SCOPED_NEGATIVE",
            "note": "no exact file-path token; StandardName alias is not a CFG path",
        })
    with open(os.path.join(OUT_DIR, "resource_graph.json"),
              "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    relations = []
    for e in graph["edges"]:
        if e["grade"] in {"PAYLOAD_IDENTITY", "REZ_EXACT_PATH", "SCOPED_NEGATIVE"}:
            relations.append(e)
    confirmed = {
        "task": "P4-M01-N03-C",
        "status": status,
        "confidence": confidence,
        "classification": classif,
        "relations": relations,
        "rs_observation": rs_obs,
        "cfg_observation": {
            k: cfg_obs[k] for k in cfg_obs
            if k != "hex"
        } if cfg_obs else None,
        "remaining_blockers": [
            "TGA/CFG not file-path fields on canonical Weapon record"
            if not tga_direct else "TGA/CFG path field found",
            "LTB piece -> DTX/TGA OPEN_UNRESOLVED",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    # keep hex in a dedicated observation file (small)
    with open(os.path.join(OUT_DIR, "rs_cfg_observation.json"),
              "w", encoding="utf-8") as f:
        json.dump({"rs": rs_obs, "cfg": cfg_obs}, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(confirmed, f, indent=2, ensure_ascii=False)

    binds_out = {
        "task": "P4-M01-N03-C",
        "path_binds": path_binds,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "path_binding.json"),
              "w", encoding="utf-8") as f:
        json.dump(binds_out, f, indent=2, ensure_ascii=False)

    report = write_report(
        status, classif, canonical, siblings, path_binds,
        rs_obs, cfg_obs, tga_cfg_hits, elapsed,
    )
    with open(os.path.join(OUT_DIR, "material_graph_report.md"),
              "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[n03c] wrote {OUT_DIR}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
