# -*- coding: utf-8 -*-
"""Find canonical Bute Weapon records for GalilACE variants.

Decodes packed Bute .LTC configs (n02b unlock + LZ decode) recovered through
the MD5-verified shard reader, then prints every record mentioning GALILACE
with its key fields. Read-only on game data.

Output: work/galil_ace_tianxi/scan/bute_galilace.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
import n02_butes_config_triage as n02b  # noqa: E402
import n03a_bornbeast_consumer as n03a  # noqa: E402
import n03b_rez_packed_config as n03b  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent / "bute_galilace.json"

INTEREST = ("GALILACE", "GALIL", "MICRO GALIL", "MICRO-GALIL")


def gbk(v):
    return n03b.gbk_display(str(v)) if isinstance(v, str) else v


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    docs = {"records": [], "decode_failures": [], "scanned_configs": 0}
    seen = set()
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            full = e["full_path"].upper()
            if not (full.endswith(".LTC") and ("BUTES" in full or "TABLE" in full)):
                continue
            if e["size"] > 32 * 1024 * 1024:
                continue
            key = (e.get("md5") or "", full)
            if key in seen:
                continue
            seen.add(key)
            if not is_complete_directory_md5(e.get("md5")):
                continue
            try:
                data, prov = read_verified_payload(index_path, e)
            except Exception as exc:  # noqa: BLE001
                docs["decode_failures"].append({"path": e["full_path"], "err": str(exc)})
                continue
            unlocked = n02b.try_unlock_crossfire_payload(data)
            if unlocked is None:
                continue
            try:
                decoded = n02b._decode_ltc_c_sharp(unlocked)
            except Exception as exc:  # noqa: BLE001
                docs["decode_failures"].append({"path": e["full_path"], "err": f"ltc:{exc}"})
                continue
            text = decoded.decode("latin-1", errors="replace")
            docs["scanned_configs"] += 1
            records = n03a.parse_lisp_all_keys(text)
            for i, block in enumerate(records):
                joined = " ".join(str(v) for v in block.values() if isinstance(v, str)).upper()
                if "GALIL" not in joined:
                    continue
                name = str(block.get("WeaponName") or block.get("Name") or "")
                std = str(block.get("StandardName") or "")
                row = {
                    "source": e["full_path"],
                    "record_index": i,
                    "head": block.get("_head", ""),
                    "WeaponName": name,
                    "WeaponName_gbk": gbk(name),
                    "StandardName": std,
                    "fields": {},
                }
                hit = False
                for k, v in block.items():
                    if k == "_head" or not isinstance(v, str):
                        continue
                    if any(t in v.upper() for t in INTEREST) or any(
                        t in k for t in ("FileName", "Sound", "Anim", "RenderStyle", "WeaponName", "StandardName", "GViewAnim", "Icon")
                    ):
                        row["fields"][k] = v
                        row["fields"][k + "_gbk"] = gbk(v)
                    if any(t in v.upper() for t in INTEREST) or "GALIL" in name.upper() or "GALIL" in std.upper():
                        hit = True
                if hit:
                    docs["records"].append(row)
    OUT.write_text(json.dumps(docs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scanned={docs['scanned_configs']} records={len(docs['records'])} fails={len(docs['decode_failures'])}")
    for r in docs["records"]:
        print("=" * 70)
        print(f"{r['source']} #{r['record_index']} head={r['head']}")
        print(f"  WeaponName={r['WeaponName_gbk']}  StandardName={r['StandardName']}")
        for k, v in r["fields"].items():
            if k.endswith("_gbk"):
                continue
            print(f"    {k} = {r['fields'].get(k + '_gbk', v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
