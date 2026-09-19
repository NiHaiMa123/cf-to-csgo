# -*- coding: utf-8 -*-
"""Scan CF REZ indexes for 屠龙 / 春桃 / DragonBlade related entries.

Read-only: index directory records only, never touches payloads.
Output: work/tulong_chuntao/scan/index_hits.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent / "index_hits.json"

# Filename tokens. 春桃 is usually a suffix on DragonBlade / Soul-DragonBlade.
TOKEN_RE = re.compile(
    r"DRAGONBLADE|DRAGON_BLADE|TULONG|TU_LONG|CHUNTAO|CHUN_TAO|"
    r"SPRINGPEACH|SPRING_PEACH|PEACHBLOSSOM|PEACH_BLOSSOM|"
    r"SOUL[_-]?DRAGON|HUN[_-]?DRAGON",
    re.I,
)
# Keep a secondary pass for PEACH/SPRING only on melee-ish paths.
MELEE_RE = re.compile(r"KNIFE|BLADE|KUKRI|DAGGER|SWORD|AXE|MELEE|PLAYERVIEW|WEAPON", re.I)
PEACH_RE = re.compile(r"PEACH|CHUNTAO|SPRINGPEACH|TAOHUA|MEIHUA", re.I)


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    hits = []
    peach_hits = []
    errors = []
    total = 0
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception as exc:  # noqa: BLE001
            errors.append({"index": index_path, "error": str(exc)})
            continue
        total += len(entries)
        try:
            label = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        except ValueError:
            label = index_path
        for e in entries:
            fp = e["full_path"]
            rec = {
                "archive": label,
                "index_archive": index_path,
                "full_path": fp,
                "size": e["size"],
                "time": e["time"],
                "md5": e.get("md5") or "",
                "md5_complete": is_complete_directory_md5(e.get("md5")),
            }
            if TOKEN_RE.search(fp):
                hits.append(rec)
            elif PEACH_RE.search(fp) and MELEE_RE.search(fp):
                peach_hits.append(rec)
    hits.sort(key=lambda h: (h["full_path"].upper(), h["archive"]))
    peach_hits.sort(key=lambda h: (h["full_path"].upper(), h["archive"]))
    doc = {
        "cf_dir": str(CF),
        "index_archives": len(indexes),
        "total_entries": total,
        "hit_count": len(hits),
        "peach_melee_count": len(peach_hits),
        "errors": errors,
        "hits": hits,
        "peach_melee": peach_hits,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"indexes={len(indexes)} entries={total} hits={len(hits)} peach_melee={len(peach_hits)} errors={len(errors)}")
    print("--- primary ---")
    for h in hits:
        print(f"  {h['archive']:>20}  {h['full_path']}  ({h['size']}B)")
    print("--- peach/melee ---")
    for h in peach_hits:
        print(f"  {h['archive']:>20}  {h['full_path']}  ({h['size']}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
