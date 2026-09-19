# -*- coding: utf-8 -*-
"""Scan CF REZ indexes for 毛瑟 / 天秤座 / Mauser / Libra related entries.

Read-only: index directory records only, never touches payloads.
Output: work/mauser_libra/scan/index_hits.json
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

TOKEN_RE = re.compile(
    r"MAUSER|M1896|M_1896|LIBRA|TIANCHENG|TIAN_CHENG|C96|BROOMHANDLE",
    re.I,
)


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    hits = []
    total = 0
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {index_path}: {exc}")
            continue
        for e in entries:
            total += 1
            full = e["full_path"]
            if not TOKEN_RE.search(full):
                continue
            hits.append(
                {
                    "rez": str(index_path),
                    "path": full,
                    "size": e.get("size"),
                    "time": e.get("time"),
                    "md5_complete": bool(is_complete_directory_md5(e.get("md5"))),
                }
            )
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scanned={total} hits={len(hits)} -> {OUT}")
    for h in hits:
        print(f"  [{h['rez'].split('/')[-1]}] {h['path']}  size={h['size']} md5={h['md5_complete']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
