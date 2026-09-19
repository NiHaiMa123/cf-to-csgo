# -*- coding: utf-8 -*-
"""Scan CF REZ indexes for Peach/ChunTao/Floral/Flower filenames."""
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
OUT = Path(__file__).resolve().parent / "peach_all_hits.json"
TOKEN_RE = re.compile(
    r"PEACH|CHUNTAO|CHUN_TAO|SPRINGPEACH|TAOHUA|FLORAL|FLOWER_|"
    r"BLOSSOM|_SPRING(?!DOLL)|CHUNTAO|MEIHUA",
    re.I,
)


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    hits = []
    total = 0
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        total += len(entries)
        try:
            label = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        except ValueError:
            label = index_path
        for e in entries:
            if TOKEN_RE.search(e["full_path"]):
                hits.append({
                    "archive": label,
                    "full_path": e["full_path"],
                    "size": e["size"],
                    "md5_complete": is_complete_directory_md5(e.get("md5")),
                })
    hits.sort(key=lambda h: h["full_path"].upper())
    OUT.write_text(json.dumps({"total": total, "hit_count": len(hits), "hits": hits}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"entries={total} hits={len(hits)}")
    for h in hits:
        print(f"  {h['archive']:>18}  {h['full_path']}  ({h['size']}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
