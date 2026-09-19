# -*- coding: utf-8 -*-
"""E1b — extract every resource referenced by the tianxi idle FX group
(plan.md §7 task 2), plus socket-donor candidates, via MD5-verified REZ
reads. Writes files under effects/discovery/assets/<REZ path> and an
asset_graph.json manifest.

Extra candidates beyond the group's own refs:
  FX/LTB/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_BODY_01.LTB  (full gun FX model;
                                                       socket-name donor?)
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent
ASSETS = OUT / "assets"
GROUP_JSON = OUT / "clientfx_group_pv_galilace_phantombeast_idle.json"

EXTRA_CANDIDATES = [
    "FX/LTB/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_BODY_01.LTB",
    "FX/LTB/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_BODY_01_SPEED.LTB",
    "FX/LTB/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_PARTS_CORE.LTB",
    "FX/LTB/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_SIDE_ELEC.LTB",
    "FX/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_SIMBOL_G.DTX",
    "FX/SGFX_BD_GUN_GALILACE_PHANTOMBEAST_SIMBOL_Y.DTX",
]


def key(p: str) -> str:
    return p.replace("\\", "/").upper()


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    group = json.loads(GROUP_JSON.read_text(encoding="utf-8"))

    wanted: dict[str, str] = {}
    for ref in group["fxf"]["resource_refs"]:
        ext, _, path = ref.partition("|")
        path = path.strip()
        if not path or path == "...":
            continue
        wanted[key(path)] = path.replace("\\", "/")
    for extra in EXTRA_CANDIDATES:
        wanted.setdefault(key(extra), extra)

    # index lookup: newest archive wins
    found: dict[str, tuple[str, dict]] = {}
    for index_path in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            k = key(e["full_path"])
            if k in wanted and is_complete_directory_md5(e.get("md5")):
                found[k] = (index_path, e)

    manifest = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "group": group["fxf"]["group"], "files": [], "missing": []}
    for k, rel in sorted(wanted.items()):
        if k not in found:
            manifest["missing"].append(rel)
            continue
        index_path, e = found[k]
        try:
            data, prov = read_verified_payload(index_path, e)
        except Exception as exc:  # noqa: BLE001
            manifest["missing"].append(f"{rel} (read failed: {exc})")
            continue
        dest = ASSETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        manifest["files"].append({
            "rez_path": rel,
            "archive": prov["index_archive"],
            "payload_file": prov["payload_file"],
            "offset": prov["offset"], "size": prov["size"],
            "md5": prov["directory_md5"], "sha256": prov["sha256"],
            "local_path": str(dest.relative_to(OUT)).replace("\\", "/"),
            "extra_candidate": rel in EXTRA_CANDIDATES,
        })

    (OUT / "asset_graph.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e1b] extracted {len(manifest['files'])} files, missing {len(manifest['missing'])}")
    for m in manifest["missing"]:
        print("  MISSING:", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
