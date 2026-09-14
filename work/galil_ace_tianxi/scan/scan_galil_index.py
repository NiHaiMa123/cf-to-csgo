# -*- coding: utf-8 -*-
"""Scan all CF REZ index archives for Galil ACE / Tianxi related entries.

Read-only: only parses index directory records, never touches payloads.
Outputs work/galil_ace_tianxi/scan/galil_index_hits.json
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
OUT = Path(__file__).resolve().parent / "galil_index_hits.json"

TOKEN_RE = re.compile(r"GALIL|ASTRA|TIANXI|SKYRAID|SKY_ATTACK|SKYATTACK", re.I)
# GBK bytes for the Chinese display name appear only inside Bute payloads;
# index names are ASCII, so token regex on filename is the primary signal.


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    hits = []
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
            if TOKEN_RE.search(e["full_path"]):
                hits.append({
                    "archive": label,
                    "index_archive": index_path,
                    "full_path": e["full_path"],
                    "size": e["size"],
                    "time": e["time"],
                    "md5": e.get("md5") or "",
                    "md5_complete": is_complete_directory_md5(e.get("md5")),
                })
    hits.sort(key=lambda h: (h["full_path"].upper(), h["archive"]))
    doc = {
        "cf_dir": str(CF),
        "index_archives": len(indexes),
        "total_entries": total,
        "hit_count": len(hits),
        "errors": errors,
        "hits": hits,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"indexes={len(indexes)} entries={total} hits={len(hits)} errors={len(errors)}")
    for h in hits:
        print(f"  {h['archive']:>16}  {h['full_path']}  ({h['size']}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
