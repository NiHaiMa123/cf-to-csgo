# -*- coding: utf-8 -*-
"""P7 — rebuild migi/csgo/pak01_*.vpk with the new addon baked in.

Replicates MIGI's UPDATE step headlessly:
  1. extract current pak01_dir.vpk into a staging tree (keeps every byte of
     the existing mod set — migi-data files + all p_* addon contents)
  2. overlay work/galil_ace_tianxi/addon contents (v_rif_galilar model,
     cf_tianxi materials, galilar sounds)
  3. add p_cf_tianxi_galilar_p1 to addons.json
  4. repack with the bundled vpk.exe (produces pak01_dir.vpk + pak01_NNN.vpk)
  5. verify the new files are readable from the rebuilt dir VPK

Backs up the old pak01_*.vpk under work/galil_ace_tianxi/deploy/pak01_backup/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

import vpk  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
WORK = REPO / "work" / "galil_ace_tianxi"
STAGE = WORK / "deploy" / "pak01"          # pack root (named pak01 -> pak01_dir.vpk)
BACKUP = WORK / "deploy" / "pak01_backup"
ADDON_SRC = WORK / "addon"
MIGI_CSGO = GAME / "migi" / "csgo"
VPK_EXE = REPO / "migi_tools" / "migi.exe_extracted" / "migi-data" / "utils" / "vpk.exe"
ADDON_NAME = "p_cf_tianxi_galilar_p1"

OLD_PAKS = [MIGI_CSGO / f"pak01_{i:03d}.vpk" for i in range(4)] + [MIGI_CSGO / "pak01_dir.vpk"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    # --- extract current pak ---
    pak = vpk.open(str(MIGI_CSGO / "pak01_dir.vpk"))
    entries = list(pak)
    print(f"pak entries={len(entries)}")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    for name in entries:
        data = pak[name].read()
        dst = STAGE / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)

    # --- overlay new addon (addon contents merge at pak root) ---
    added = []
    for f in sorted(ADDON_SRC.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(ADDON_SRC).as_posix()
        dst = STAGE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        added.append(rel)

    # --- update addons.json ---
    addons_path = STAGE / "addons.json"
    addons = json.loads(addons_path.read_text(encoding="utf-8"))
    entry = f"./migi/csgo/addons\\{ADDON_NAME}\\"
    if entry not in addons:
        addons.append(entry)
    addons_path.write_text(json.dumps(addons), encoding="utf-8")
    print(f"overlaid {len(added)} files; addons.json now has {len(addons)} addons")

    # --- repack ---
    pack_cwd = STAGE.parent
    for old in pack_cwd.glob("pak01_*.vpk"):
        old.unlink()
    proc = subprocess.run([str(VPK_EXE), "-M", str(STAGE)], cwd=str(pack_cwd),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=600)
    print("vpk rc=", proc.returncode, (proc.stdout or "")[-400:], (proc.stderr or "")[-400:])
    new_dir = pack_cwd / "pak01_dir.vpk"
    if not new_dir.is_file():
        raise RuntimeError("vpk.exe produced no pak01_dir.vpk")

    # --- verify new entries exist in rebuilt dir vpk ---
    check = vpk.open(str(new_dir))
    missing = [rel for rel in added if rel not in check]
    if missing:
        raise RuntimeError(f"missing in rebuilt pak: {missing[:5]}")

    # --- backup old + swap in new ---
    BACKUP.mkdir(parents=True, exist_ok=True)
    for p in OLD_PAKS:
        if p.is_file():
            shutil.copy2(p, BACKUP / p.name)
    for newf in sorted(pack_cwd.glob("pak01_*.vpk")):
        shutil.copy2(newf, MIGI_CSGO / newf.name)

    manifest = {
        "addon": ADDON_NAME,
        "added_files": added,
        "added_sha256": {rel: sha256(STAGE / rel) for rel in added},
        "backup": [str(BACKUP / p.name) for p in OLD_PAKS if (BACKUP / p.name).exists()],
        "deployed": [str(MIGI_CSGO / f.name) for f in sorted(pack_cwd.glob("pak01_*.vpk"))],
    }
    (WORK / "deploy" / "pak_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("[p7] pak rebuilt + deployed:", len(manifest["deployed"]), "vpk files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
