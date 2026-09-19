# -*- coding: utf-8 -*-
"""Acquire 传说女帝-保卫者 (Roxana GR) first-person arm assets."""
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
MANIFEST = OUT / "roxana_gr_acquisition.json"

WANTED = [
    "Models/PLAYERVIEW/ArmModel/Arm_Roxana_GR.LTB",
    "ModelTextures/PLAYERVIEW/FVIEW_HAND_Roxana_GR.DTX",
    "ModelTextures/PLAYERVIEW/FVIEW_ARM_Roxana_GR.DTX",
    "ModelTextures/NormalMap/FVIEW_HAND_Roxana_GR_N.PNG",
    "ModelTextures/NormalMap/FVIEW_ARM_Roxana_GR_N.PNG",
    "ModelTextures/SpecularMap/FVIEW_HAND_Roxana_GR_S.PNG",
    "ModelTextures/SpecularMap/FVIEW_ARM_Roxana_GR_S.PNG",
    "ModelTextures/AlphaMap/FVIEW_HAND_Roxana_GR_A.PNG",
    "ModelTextures/AlphaMap/FVIEW_ARM_Roxana_GR_A.PNG",
]


def key(p: str) -> str:
    return p.replace("\\", "/").upper()


def main() -> int:
    indexes = extract_all.discover_index_archives(str(CF))
    wanted = {key(w): w for w in WANTED}
    found: dict[str, tuple[str, dict]] = {}
    extras = []
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            fp = e["full_path"].replace("\\", "/")
            k = key(fp)
            if "ROXANA" in k.upper() and ("ARM" in k.upper() or "FVIEW" in k.upper() or "HAND" in k.upper()):
                extras.append(fp)
            if k in wanted and is_complete_directory_md5(e.get("md5")):
                found[k] = (index_path, e)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "character": "Roxana GR / 传说女帝-保卫者",
        "files": [],
        "missing": [],
        "roxana_related": sorted(set(extras)),
    }
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
        try:
            arc = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        except ValueError:
            arc = index_path
        rec = {
            "path": e["full_path"].replace("\\", "/"),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "md5": e.get("md5"),
            "archive": arc,
            "provenance": prov,
        }
        manifest["files"].append(rec)
        print("OK", rec["path"], rec["bytes"])
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("missing", manifest["missing"])
    print("related count", len(manifest["roxana_related"]))
    for p in manifest["roxana_related"]:
        if "ArmModel" in p or p.endswith(".LTB"):
            print(" LTB/ARM", p)
    return 0 if not manifest["missing"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
