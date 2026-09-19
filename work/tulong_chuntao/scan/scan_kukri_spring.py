# -*- coding: utf-8 -*-
"""List all Kukri_Beast / Spring related REZ entries."""
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
OUT = Path(__file__).resolve().parent / "kukri_spring_hits.json"
TOKEN_RE = re.compile(r"KUKRI_BEAST", re.I)
SPRING_RE = re.compile(r"SPRING", re.I)


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    hits = []
    spring = []
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        try:
            label = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        except ValueError:
            label = index_path
        for e in entries:
            fp = e["full_path"]
            if not TOKEN_RE.search(fp):
                continue
            rec = {
                "archive": label,
                "full_path": fp,
                "size": e["size"],
                "md5": e.get("md5") or "",
                "md5_complete": is_complete_directory_md5(e.get("md5")),
            }
            hits.append(rec)
            if SPRING_RE.search(fp):
                spring.append(rec)
    spring.sort(key=lambda h: h["full_path"].upper())
    hits.sort(key=lambda h: h["full_path"].upper())
    OUT.write_text(json.dumps({
        "kukri_beast_count": len(hits),
        "spring_count": len(spring),
        "spring": spring,
        "hits": hits,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"kukri_beast={len(hits)} spring={len(spring)}")
    print("--- SPRING ---")
    for h in spring:
        print(f"  {h['archive']:>18}  {h['full_path']}  ({h['size']}B md5={h['md5_complete']})")
    print("--- PV/DTX/CFG/N/S/A (canonical, no BL/GR/WOMAN) ---")
    for h in hits:
        fp = h["full_path"].replace("\\", "/")
        u = fp.upper()
        if any(x in u for x in ("_BL", "_GR", "_WOMAN")):
            continue
        if any(x in u for x in ("PLAYERVIEW", "WEAPONSHADER", "NORMALMAP", "SPECULAR", "ALPHAMAP", "SND/", "FMOD")):
            print(f"  {h['archive']:>18}  {fp}  ({h['size']}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
