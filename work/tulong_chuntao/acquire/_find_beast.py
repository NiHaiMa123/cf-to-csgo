# -*- coding: utf-8 -*-
"""Locate base Kukri_Beast (non-spring) assets inside CF REZ indexes."""
from __future__ import annotations

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


def main() -> int:
    idxs = extract_all.discover_index_archives(str(CF))
    print("indexes", len(idxs))
    for ip in idxs:
        try:
            ents = extract_all.read_index_entries(ip)
        except Exception:
            continue
        for e in ents:
            p = e["full_path"].replace("\\", "/")
            up = p.upper()
            if "KUKRI_BEAST" in up and "SPRING" not in up:
                ok = is_complete_directory_md5(e.get("md5"))
                print(("OK " if ok else "BAD"), p, "|", Path(ip).name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
