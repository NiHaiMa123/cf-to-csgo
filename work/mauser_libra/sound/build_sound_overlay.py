# -*- coding: utf-8 -*-
"""毛瑟-天秤座 P6 — CF Mauser sounds on the CS:GO Glock slot.

Unlike the Galil (FMOD Weapon.bank), Mauser PCM lives in
SND/WEAPON/Mauser/*.WAV — the 'encrypted' container is just LZMA-alone
compressed RIFF (first byte 0x5D), decoded in probe_snd_wav.py. All clips
are already 44.1 kHz mono PCM16 -> written verbatim onto the vanilla
Weapon_Glock.* wave paths inside addon p_cf_mauser_libra_p1.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import shutil
import sys
import wave
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())

WORK = REPO / "work" / "mauser_libra"
OUT = WORK / "sound"
RAW = OUT / "raw"
PCM = OUT / "pcm"
STAGING = WORK / "addon"
LOG = OUT / "logs"
ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_mauser_libra_p1"

# REZ SND paths (LZMA-compressed RIFF) -> logical name
SOURCES = {
    "Mauser_Shoot_1": "SND/WEAPON/Mauser/Mauser_Shoot_1.WAV",
    "Mauser_Select": "SND/WEAPON/Mauser/Mauser_Select.WAV",
    "Mauser_ClipOut": "SND/WEAPON/Mauser/Mauser_ClipOut.WAV",
    "Mauser_ClipIn": "SND/WEAPON/Mauser/Mauser_ClipIn.WAV",
    "CoinSelect": "SND/WEAPON/M14EBR_Taurus/M14EBR_Taurus_CoinSelect.WAV",
    "CoinReload": "SND/WEAPON/M14EBR_Taurus/M14EBR_Taurus_CoinReload.WAV",
}

# CS:GO wave path <- pcm source name
WIRE = [
    ("sound/weapons/glock18/glock_01.wav", "Mauser_Shoot_1"),
    ("sound/weapons/glock18/glock_02.wav", "Mauser_Shoot_1"),
    ("sound/weapons/glock18/glock18-1-distant.wav", "Mauser_Shoot_1"),
    ("sound/weapons/glock18/glock_clipout.wav", "Mauser_ClipOut"),
    ("sound/weapons/glock18/glock_clipin.wav", "Mauser_ClipIn"),
    ("sound/weapons/glock18/glock_draw.wav", "Mauser_Select"),
    ("sound/weapons/glock18/glock_slideback.wav", "CoinSelect"),
    ("sound/weapons/glock18/glock_sliderelease.wav", "CoinReload"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    for d in (OUT, RAW, PCM, STAGING, LOG):
        d.mkdir(parents=True, exist_ok=True)

    wanted = {v.upper(): k for k, v in SOURCES.items()}
    found = {}
    for idx in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(idx)
        except Exception:
            continue
        for e in entries:
            fp = e["full_path"].replace("\\", "/")
            if fp.upper() in wanted and is_complete_directory_md5(e.get("md5")):
                found[fp.upper()] = (idx, e)

    report = {"sources": {}, "wired": []}
    missing = []
    for upath, name in wanted.items():
        if upath not in found:
            missing.append(upath)
            continue
        idx, e = found[upath]
        data, prov = read_verified_payload(idx, e)
        raw = RAW / f"{name}.wav"
        raw.write_bytes(data)
        dec = lzma.decompress(data, format=lzma.FORMAT_ALONE) if data[:1] == b"\x5d" else data
        if dec[:4] != b"RIFF":
            raise RuntimeError(f"{name}: decoded payload is not RIFF ({dec[:8]!r})")
        pcm = PCM / f"{name}.wav"
        pcm.write_bytes(dec)
        with wave.open(str(pcm), "rb") as w:
            secs = w.getnframes() / w.getframerate()
            ok = w.getframerate() == 44100 and w.getsampwidth() == 2 and w.getnchannels() == 1
            if not ok:
                raise RuntimeError(f"{name}: unexpected fmt {w.getframerate()}Hz ch={w.getnchannels()} sw={w.getsampwidth()}")
        report["sources"][name] = {
            "rez": upath, "bytes_packed": len(data), "seconds": round(secs, 3),
            "sha256": sha256(pcm),
        }
        print(f"[p6] {name}: {len(data)}B -> {len(dec)}B RIFF {secs:.2f}s")
    if missing:
        raise RuntimeError(f"missing SND entries: {missing}")

    for wave_rel, src in WIRE:
        dst = STAGING / wave_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCM / f"{src}.wav", dst)
        report["wired"].append({"wave": wave_rel, "from": src, "sha256": sha256(dst)})
        addon_dst = ADDON / wave_rel
        addon_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCM / f"{src}.wav", addon_dst)

    (OUT / "sound_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[p6] wired", len(report["wired"]), "waves ->", ADDON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
