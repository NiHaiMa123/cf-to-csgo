# -*- coding: utf-8 -*-
"""P3a — extract stock CS:GO Galil AR first-person reference + soundscript.

Pulls v_rif_galilar model files and galilar material/soundscript entries
from csgo/pak01_dir.vpk into work/galil_ace_tianxi/csref/source_vpk/.
Read-only on the game install.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import vpk  # type: ignore
except ImportError as exc:
    raise SystemExit("Python package 'vpk' is required") from exc

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
from _paths import game_dir  # noqa: E402

GAME = Path(game_dir())
OUT = Path(__file__).resolve().parent
SRC = OUT / "source_vpk"

MODEL_FILES = (
    "models/weapons/v_rif_galilar.mdl",
    "models/weapons/v_rif_galilar.vvd",
    "models/weapons/v_rif_galilar.dx90.vtx",
    "models/weapons/v_rif_galilar.ani",
    "models/weapons/v_rif_galilar.phy",
    "models/weapons/v_rif_galilar.sw.vtx",
    "models/weapons/v_rif_galilar.dx80.vtx",
)
SOUNDSCRIPTS = (
    "scripts/game_sounds_weapons.txt",
    "scripts/game_sounds.txt",
)


def main() -> int:
    pak = vpk.open(str(GAME / "csgo" / "pak01_dir.vpk"))
    extracted, missing = [], []
    for rel in MODEL_FILES + SOUNDSCRIPTS:
        try:
            payload = pak.get_file(rel).read()
        except Exception:
            missing.append(rel)
            continue
        dest = SRC / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        extracted.append({"vpk_path": rel, "size": len(payload),
                          "sha256": hashlib.sha256(payload).hexdigest()})
        print(f"[ref] {rel}  {len(payload)}B")

    # find galilar material dir names from mdl + list sound entries
    notes = {"missing": missing}
    wtxt = ""
    for cand in SOUNDSCRIPTS:
        f = SRC / cand
        if f.is_file():
            wtxt = f.read_text(encoding="utf-8", errors="replace")
            break
    galil_sounds = {}
    if wtxt:
        for m in re.finditer(r'"(Weapon_[^"]*galil[^"]*)"\s*\{([^}]*)\}', wtxt, re.I | re.S):
            name, body = m.group(1), m.group(2)
            waves = re.findall(r'"([^"]*galil[^"]*\.wav)"', body, re.I)
            galil_sounds[name] = {"waves": waves}
        (OUT / "galilar_soundscript.json").write_text(
            json.dumps(galil_sounds, indent=1), encoding="utf-8")
        print(f"[ref] soundscript entries: {list(galil_sounds)}")
        # also pull the referenced stock wavs for comparison
        for name, info in galil_sounds.items():
            for wv in info["waves"]:
                clean = wv.lstrip("`)~@#^*>!<&")
                rel = "sound/" + clean
                try:
                    payload = pak.get_file(rel).read()
                except Exception:
                    continue
                dest = SRC / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(payload)
        notes["galil_sounds"] = galil_sounds

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": {"weapon": "Galil AR", "modelname": "weapons/v_rif_galilar.mdl"},
        "files": extracted,
        "missing": missing,
        **notes,
    }
    (OUT / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[ref] extracted={len(extracted)} missing={missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
