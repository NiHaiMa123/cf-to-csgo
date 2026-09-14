# -*- coding: utf-8 -*-
"""Galil ACE-天袭 P6 — CF original sounds on the CS:GO Galil slot.

Sound streams live in rez/FMODStudio/Weapon/Weapon.bank (FSB5, Custom
Vorbis, 48 kHz mono) as GalilACEPhantomB_* streams — decoded via vgmstream,
resampled to 44100 Hz 16-bit PCM via ffmpeg, then written onto the vanilla
Weapon_GalilAR.* wave paths inside addon p_cf_tianxi_galilar_p1.

The SND/WEAPON/GalilACE_PhantomBeast/*.WAV files in REZ are a separate
encrypted container and are NOT used.

Stock-retained (not overridden, documented in report):
  galil_boltback.wav / galil_boltforward.wav — CF marks no bolt events;
  stock mechanical sounds stay until a runtime retime.
  weapons/movement*.wav — shared foley used by WeaponMove1-3 (must stay
  stock, overriding would affect every weapon).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())
VGM = Path(_paths.vgmstream())

WORK = REPO / "work" / "galil_ace_tianxi"
OUT = WORK / "sound"
RAW = OUT / "raw"
PCM = OUT / "pcm"
STAGING = WORK / "addon"
LOG = OUT / "logs"
BANK = CF / "rez" / "FMODStudio" / "Weapon" / "Weapon.bank"
ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1"

# stream name -> subsong index in Weapon.bank (enumerated 2026-09-14)
STREAMS = {
    "GalilACEPhantomB_Shoot_1": 483,
    "GalilACEPhantomB_Shoot_1_R": 408,
    "GalilACEPhantomB_ClipOut": 100,
    "GalilACEPhantomB_ClipIn": 425,
    "GalilACEPhantomB_Select": 331,
    "GalilACEPhantomB_Chg": 402,
    "GalilACEPhantomB_Obv": 55,
    "GalilACEPhantomB_ATT": 190,
}

# CS:GO wave path <- pcm source name
WIRE = [
    ("sound/weapons/galilar/galil_01.wav", "GalilACEPhantomB_Shoot_1"),
    ("sound/weapons/galilar/galil_02.wav", "GalilACEPhantomB_Shoot_1"),
    ("sound/weapons/galilar/galil_03.wav", "GalilACEPhantomB_Shoot_1"),
    ("sound/weapons/galilar/galil_04.wav", "GalilACEPhantomB_Shoot_1"),
    ("sound/weapons/galilar/galil_distant.wav", "GalilACEPhantomB_Shoot_1_R"),
    ("sound/weapons/galilar/galil_clipout.wav", "GalilACEPhantomB_ClipOut"),
    ("sound/weapons/galilar/galil_clipin.wav", "GalilACEPhantomB_ClipIn"),
    ("sound/weapons/galilar/galil_draw.wav", "GalilACEPhantomB_Select"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg required")
    return exe


def run(cmd, log):
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / f"{log}.out.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG / f"{log}.err.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {(proc.stderr or proc.stdout)[:600]}")
    return proc


def main() -> int:
    for d in (OUT, RAW, PCM, STAGING, LOG):
        d.mkdir(parents=True, exist_ok=True)
    if not BANK.is_file():
        raise RuntimeError(f"missing {BANK}")

    report = {"bank": str(BANK), "wired": []}
    for name, sub in STREAMS.items():
        raw = RAW / f"{name}.wav"
        run([str(VGM), "-i", "-s", str(sub), "-o", str(raw), str(BANK)],
            f"vgm_{name}")
        pcm = PCM / f"{name}.wav"
        run([ffmpeg(), "-y", "-i", str(raw), "-af", "aresample=44100",
             "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(pcm)],
            f"ff_{name}")
        with wave.open(str(pcm), "rb") as w:
            assert w.getframerate() == 44100 and w.getsampwidth() == 2
            secs = w.getnframes() / 44100
        report[name] = {"seconds": round(secs, 3), "sha256": sha256(pcm)}

    for wave_rel, src in WIRE:
        dst = STAGING / wave_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCM / f"{src}.wav", dst)
        report["wired"].append({"wave": wave_rel, "from": src,
                                "sha256": sha256(dst)})
        # deploy straight into the live addon dir too
        addon_dst = ADDON / wave_rel
        addon_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCM / f"{src}.wav", addon_dst)

    (OUT / "sound_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "wired"},
                     indent=2))
    print("[p6] wired", len(report["wired"]), "waves ->", ADDON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
