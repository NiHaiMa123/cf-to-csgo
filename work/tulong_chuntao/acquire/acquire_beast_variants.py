# -*- coding: utf-8 -*-
"""Pull candidate Kukri_Beast diffuse variants (NobleGold, QV) for comparison."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent / "verified_root"

WANT = {
    "ModelTextures/PLAYERVIEW/PV-Kukri_Beast_NobleGold.DTX",
    "ModelTextures/PLAYERVIEW/PV-Kukri_Beast_SS.DTX",
    "ModelTextures/WEAPONS/QV-Kukri_Beast.DTX",
    "ModelTextures/PLAYERVIEW/PV-Kukri_RoyalDragon5.DTX",
    "ModelTextures/PLAYERVIEW/pv-kukri_RoyalDragon.DTX",
}


def main() -> int:
    got = set()
    for ip in extract_all.discover_index_archives(str(CF)):
        try:
            ents = extract_all.read_index_entries(ip)
        except Exception:
            continue
        for e in ents:
            p = e["full_path"].replace("\\", "/")
            if p in WANT and is_complete_directory_md5(e.get("md5")):
                data, _prov = read_verified_payload(ip, e)
                dest = OUT / p
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                print("OK", p, len(data))
                got.add(p)
    print("missing", WANT - got)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
