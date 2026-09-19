# -*- coding: utf-8 -*-
"""Acquire COP357-IronBeast2_Winter (雪域霜狐) assets from CF REZ."""
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
MANIFEST = OUT / "acquisition.json"

NAME = "Cop357_IronBeast2_Winter"
WANTED = [
    f"Models/PLAYERVIEW/PV-{NAME}.LTB",
    f"ModelTextures/PLAYERVIEW/PV-{NAME}.DTX",
    f"ModelTextures/Shader/WeaponShader/{NAME}.CFG",
    f"ModelTextures/SpecularMap/{NAME}_S.PNG",
    f"ModelTextures/NormalMap/{NAME}_N.PNG",
    f"ModelTextures/AlphaMap/{NAME}_A.PNG",
    "ModelTextures/EnvCubeMap/LobbyCube.DDS",
    f"Models/PLAYERVIEW/PV-{NAME}_BL.LTB",
    f"Models/PLAYERVIEW/PV-{NAME}_GR.LTB",
    f"Models/WEAPONS/QV-{NAME}.ltb",
    f"ModelTextures/WEAPONS/QV-{NAME}.DTX",
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
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "weapon": "COP357-雪域霜狐",
        "standard_name": NAME,
        "files": [], "missing": [],
    }
    for k, w in wanted.items():
        if k not in found:
            manifest["missing"].append(w)
            continue
        index_path, e = found[k]
        data, prov = read_verified_payload(index_path, e)
        dest = ROOT / w
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        try:
            arc = str(Path(index_path).relative_to(CF)).replace("\\", "/")
        except ValueError:
            arc = index_path
        manifest["files"].append({
            "path": w, "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "rez_archive": arc, "rez_path": e["full_path"],
            "payload_sha256": prov.get("payload_sha256"),
        })
        print(f"[ok] {w} {len(data)}B")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"[done] found={len(manifest['files'])} missing={manifest['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
