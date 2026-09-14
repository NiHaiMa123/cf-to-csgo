# -*- coding: utf-8 -*-
"""P0 — recover verified GalilACE_PhantomBeast (天袭) assets from CF REZ.

Every file goes through read_verified_payload (shard routing + directory
MD5). Files land in work/galil_ace_tianxi/acquire/verified_root/<REZ path>
with an acquisition manifest of sha256 + provenance. Read-only on game dir.
"""
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

WANTED = [
    "Models/PLAYERVIEW/PV-GalilACE_PhantomBeast.LTB",
    "ModelTextures/PLAYERVIEW/PV-GalilACE_PhantomBeast.DTX",
    "ModelTextures/Shader/WeaponShader/GalilACE_PhantomBeast.CFG",
    "ModelTextures/SpecularMap/GalilACE_PhantomBeast_S.PNG",
    "ModelTextures/NormalMap/GalilACE_PhantomBeast_N.PNG",
    "ModelTextures/AlphaMap/GalilACE_PhantomBeast_A.PNG",
    # native sound wavs (base, non-Chg set)
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_Shoot_1.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_ClipOut.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_ClipIn.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_Select.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_Chg.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_Obv.WAV",
    "SND/WEAPON/GalilACE_PhantomBeast/GalilACEPhantomB_ATT.WAV",
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
                # prefer the hit whose archive is highest-numbered (newest content wins)
                found[k] = (index_path, e)
    manifest = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "files": [], "missing": []}
    for k, w in wanted.items():
        if k not in found:
            manifest["missing"].append(w)
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
        manifest["files"].append({
            "rez_path": e["full_path"],
            "archive": arc,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "routing": prov["routing"],
            "payload_file": prov["payload_file"],
            "local_path": str(dest.relative_to(OUT)).replace("\\", "/"),
        })
        print(f"[acq] {e['full_path']}  <- {arc}  {len(data)}B  sha256={manifest['files'][-1]['sha256'][:12]}")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"recovered={len(manifest['files'])} missing={len(manifest['missing'])}")
    if manifest["missing"]:
        print("MISSING:", *manifest["missing"], sep="\n  ")
    return 0 if not manifest["missing"] else 1


if __name__ == "__main__":
    sys.exit(main())
