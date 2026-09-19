# -*- coding: utf-8 -*-
"""P6 v2 — CF Kukri/Beast SND wavs onto CS:GO Weapon_Knife wave paths.

v1 used FMOD bank streams (KUKRI_*_R = reverb variants). v2 uses the dry
SND/WEAPON wavs plus the Beast-specific hit sound found in REZ:
  SND/WEAPON/KUKRI/Kucri_{Attack_1..3,Select}.WAV
  SND/WEAPON/Kukri-Beast/KukriBeast_Hit.WAV
Extracted payloads are LZMA-alone compressed -> *.raw.wav under sound/cf_raw.
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

REPO = Path(_paths.project_dir())
WORK = REPO / "work" / "tulong_chuntao"
OUT = WORK / "sound"
RAW = OUT / "cf_raw"          # LZMA-decompressed RIFF wavs from REZ
PCM = OUT / "pcm"
STAGING = WORK / "addon"

SRC = {
    "Kucri_Attack_1": RAW / "Kucri_Attack_1.raw.wav",
    "Kucri_Attack_2": RAW / "Kucri_Attack_2.raw.wav",
    "Kucri_Attack_3": RAW / "Kucri_Attack_3.raw.wav",
    "Kucri_Select": RAW / "Kucri_Select.raw.wav",
    "KukriBeast_Hit": RAW / "KukriBeast_Hit.raw.wav",
}

# Engine auto-plays Weapon_Knife.Slash (rndwave slash1/2) and .Stab — random
# and detached from the actual CF anim. Those waves are silenced; the per-clip
# whoosh is fired by QC events bound to hijacked Ursus soundscript entries.
WIRE = [
    ("sound/weapons/knife/knife_slash1.wav", "silence"),
    ("sound/weapons/knife/knife_slash2.wav", "silence"),
    ("sound/weapons/knife/knife_stab.wav", "silence"),
    ("sound/weapons/knife/knife_deploy1.wav", "Kucri_Select"),
    ("sound/weapons/knife/knife_hit1.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit2.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit3.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit4.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit_01.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit_02.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit_03.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit_04.wav", "KukriBeast_Hit"),
    ("sound/weapons/knife/knife_hit_05.wav", "KukriBeast_Hit"),
    # QC-event carriers: combo_1 -> Flip.01, combo_2 -> Flip.02, bigshot -> Flip.03
    ("sound/weapons/knife_ursus/ursus_flip_01.wav", "Kucri_Attack_1"),
    ("sound/weapons/knife_ursus/ursus_flip_02.wav", "Kucri_Attack_2"),
    ("sound/weapons/knife_ursus/ursus_flip_03.wav", "Kucri_Attack_3"),
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
        raise RuntimeError("ffmpeg not on PATH")
    return exe


def main() -> int:
    PCM.mkdir(parents=True, exist_ok=True)
    pcm = {}
    for name, src in SRC.items():
        if not src.is_file():
            raise RuntimeError(f"missing extracted wav {src}")
        dst = PCM / f"{name}.wav"
        ff = subprocess.run(
            [ffmpeg(), "-y", "-i", str(src), "-ar", "44100", "-ac", "1",
             "-acodec", "pcm_s16le", str(dst)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if ff.returncode != 0 or not dst.is_file():
            raise RuntimeError(f"ffmpeg {name}: {ff.stderr[-400:]}")
        pcm[name] = dst
        print("pcm", name, dst.stat().st_size)
    # tiny silence for muted auto-play waves
    sil = PCM / "silence.wav"
    ff = subprocess.run(
        [ffmpeg(), "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", "0.05", "-acodec", "pcm_s16le", str(sil)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if ff.returncode != 0 or not sil.is_file():
        raise RuntimeError(f"ffmpeg silence: {ff.stderr[-400:]}")
    pcm["silence"] = sil
    files = []
    for rel, sname in WIRE:
        dest = STAGING / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pcm[sname], dest)
        files.append({"path": rel, "src": sname,
                      "sha256": sha256(dest), "bytes": dest.stat().st_size})
        print("wire", rel, "<-", sname)
    (OUT / "sound_report.json").write_text(json.dumps({
        "sources": {k: str(v) for k, v in SRC.items()}, "files": files,
        "note": "dry SND wavs; Hit/HitWall use KukriBeast_Hit",
    }, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
