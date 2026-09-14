# -*- coding: utf-8 -*-
"""Scan CF REZ index archives for Fview hand/arm texture entries.

The PV-GalilACE_PhantomBeast.LTB embeds the standard CF first-person hand
meshes (Fview-hand2 / Fview-arm2). Their texture is the default character
Fview skin under ModelTextures — find candidates.

Outputs work/galil_ace_tianxi/scan/fview_index_hits.json
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
OUT = Path(__file__).resolve().parent / "fview_index_hits.json"

TOKEN_RE = re.compile(r"FVIEW|FV-|_HAND|_ARM\b|HAND_|ARM_", re.I)


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
        label = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        for e in entries:
            fp = e["full_path"]
            if "MODELTEX" in fp.upper() and TOKEN_RE.search(fp):
                hits.append({
                    "archive": label,
                    "full_path": fp,
                    "size": e["size"],
                    "time": e["time"],
                    "md5_complete": is_complete_directory_md5(e.get("md5")),
                })
    hits.sort(key=lambda h: (h["full_path"].upper(), h["archive"]))
    doc = {"index_archives": len(indexes), "total_entries": total,
           "hit_count": len(hits), "errors": errors, "hits": hits}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"indexes={len(indexes)} entries={total} hits={len(hits)} errors={len(errors)}")
    for h in hits:
        print(f"  {h['archive']:>16}  {h['full_path']}  ({h['size']}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
