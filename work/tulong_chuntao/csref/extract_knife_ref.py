# -*- coding: utf-8 -*-
"""P3a — extract stock CS:GO default CT/T knife viewmodels + soundscript."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import vpk  # type: ignore
except ImportError as exc:
    raise SystemExit("Python package 'vpk' is required") from exc

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
from _paths import game_dir, project_dir  # noqa: E402

GAME = Path(game_dir())
OUT = Path(__file__).resolve().parent
SRC = OUT / "source_vpk"
DEC = OUT / "decompiled_stock"
CROWBAR = Path(project_dir()) / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe"

MODELS = (
    "models/weapons/v_knife_default_ct.mdl",
    "models/weapons/v_knife_default_ct.vvd",
    "models/weapons/v_knife_default_ct.dx90.vtx",
    "models/weapons/v_knife_default_ct.dx80.vtx",
    "models/weapons/v_knife_default_ct.sw.vtx",
    "models/weapons/v_knife_default_ct.ani",
    "models/weapons/v_knife_default_t.mdl",
    "models/weapons/v_knife_default_t.vvd",
    "models/weapons/v_knife_default_t.dx90.vtx",
    "models/weapons/v_knife_default_t.dx80.vtx",
    "models/weapons/v_knife_default_t.sw.vtx",
    "models/weapons/v_knife_default_t.ani",
)
SOUNDSCRIPTS = (
    "scripts/game_sounds_weapons.txt",
)


def main() -> int:
    pak = vpk.open(str(GAME / "csgo" / "pak01_dir.vpk"))
    extracted, missing = [], []
    for rel in MODELS + SOUNDSCRIPTS:
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

    wtxt = ""
    f = SRC / "scripts/game_sounds_weapons.txt"
    if f.is_file():
        wtxt = f.read_text(encoding="utf-8", errors="replace")
    knife_sounds = {}
    if wtxt:
        for m in re.finditer(r'"(Weapon_Knife[^"]*)"\s*\{([^}]*)\}', wtxt, re.I | re.S):
            name, body = m.group(1), m.group(2)
            waves = re.findall(r'"([^"]+\.wav)"', body, re.I)
            knife_sounds[name] = {"waves": waves}
        (OUT / "knife_soundscript.json").write_text(
            json.dumps(knife_sounds, indent=1), encoding="utf-8")
        print(f"[ref] knife soundscript entries: {list(knife_sounds)}")

    if DEC.exists():
        shutil.rmtree(DEC)
    DEC.mkdir(parents=True, exist_ok=True)
    for stem in ("v_knife_default_ct", "v_knife_default_t"):
        mdl = SRC / "models" / "weapons" / f"{stem}.mdl"
        dest = DEC / stem
        dest.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [str(CROWBAR), str(mdl), str(dest)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        (OUT / f"crowbar_{stem}.log").write_text(
            (proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"Crowbar failed {stem}: {(proc.stderr or proc.stdout or '')[:500]}")
        qcs = list(dest.rglob("*.qc"))
        print(f"[ref] decompiled {stem} qc={ [p.name for p in qcs] }")
        for qc in qcs:
            text = qc.read_text(encoding="utf-8", errors="replace")
            seqs = re.findall(r'\$sequence\s+"([^"]+)"', text)
            acts = re.findall(r'activity\s+"([^"]+)"', text, re.I)
            print(f"      sequences={seqs}")
            print(f"      activities={acts}")

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": {"weapon": "default knife CT+T"},
        "files": extracted,
        "missing": missing,
        "sounds": list(knife_sounds),
    }
    (OUT / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[ref] extracted={len(extracted)} missing={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
