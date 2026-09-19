# -*- coding: utf-8 -*-
"""Acquire base 屠龙 (Kukri_Beast) texture set — same verified REZ path as
acquire_assets.py, minus the spring skin."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent
ROOT = OUT / "verified_root"
MANIFEST = OUT / "acquisition_beast.json"

WANTED = [
    "ModelTextures/PLAYERVIEW/PV-Kukri_Beast.DTX",
    "ModelTextures/Shader/WeaponShader/Kukri_Beast.CFG",
    "ModelTextures/SpecularMap/Kukri_Beast_s.PNG",
    "ModelTextures/NormalMap/Kukri_Beast_N.PNG",
    "ModelTextures/AlphaMap/Kukri_Beast_alpha.PNG",
]


def key(p: str) -> str:
    return p.replace("\\", "/").upper()


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    wanted = {key(w): w for w in WANTED}
    found: dict[str, tuple[str, dict]] = {}
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            k = key(e["full_path"])
            if k in wanted and is_complete_directory_md5(e.get("md5")):
                found[k] = (index_path, e)
    manifest = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "weapon": "屠龙 (base)", "files": [], "missing": []}
    for k, w in wanted.items():
        if k not in found:
            manifest["missing"].append(w)
            print("MISSING", w)
            continue
        index_path, e = found[k]
        data, prov = read_verified_payload(index_path, e)
        dest = ROOT / e["full_path"].replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        rec = {"path": e["full_path"].replace("\\", "/"), "bytes": len(data),
               "sha256": hashlib.sha256(data).hexdigest(),
               "md5": e.get("md5"), "provenance": prov}
        manifest["files"].append(rec)
        print("OK", rec["path"], rec["bytes"], rec["sha256"][:16])
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print("missing", manifest["missing"])
    return 0 if not manifest["missing"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
