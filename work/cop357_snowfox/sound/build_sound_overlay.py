# -*- coding: utf-8 -*-
"""COP357-雪域霜狐 — CF Cop357Derringer/Dominator sounds on the CS:GO Glock slot.

Same recipe as mauser_libra/sound/build_sound_overlay.py: REZ SND WAVs are
LZMA-alone compressed RIFF (first byte 0x5D), 44.1 kHz mono PCM16 -> written
verbatim onto the vanilla glock18 wave paths inside addon p_cf_cop357_snowfox_p1.
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

WORK = REPO / "work" / "cop357_snowfox"
OUT = WORK / "sound"
RAW = OUT / "raw"
PCM = OUT / "pcm"
STAGING = WORK / "addon_v2"
LOG = OUT / "logs"
ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_cop357_snowfox_p1"

# REZ SND paths (LZMA-compressed RIFF) -> logical name
SOURCES = {
    "Shoot": "SND/WEAPON/Cop357Derringer/Cop357Derringer_SHOOT_1.WAV",
    "Reload": "SND/WEAPON/Cop357Derringer/Cop357Derringer_Reload.WAV",
    "ClipOut": "SND/WEAPON/Cop357Derringer/Cop357Derringer_ClipOut.WAV",
    "ClipIn": "SND/WEAPON/Cop357Derringer/Cop357Derringer_ClipIn.WAV",
    "Select": "SND/WEAPON/Cop357_Dominator/Cop357_Dominator_Select.WAV",
}

# CS:GO wave path <- pcm source name (target: glock18)
WIRE = [
    ("sound/weapons/glock18/glock_01.wav", "Shoot"),
    ("sound/weapons/glock18/glock_02.wav", "Shoot"),
    ("sound/weapons/glock18/glock18-1-distant.wav", "Shoot"),
    ("sound/weapons/glock18/glock_clipout.wav", "ClipOut"),
    ("sound/weapons/glock18/glock_clipin.wav", "ClipIn"),
    ("sound/weapons/glock18/glock_draw.wav", "Select"),
    ("sound/weapons/glock18/glock_slideback.wav", "ClipOut"),
    ("sound/weapons/glock18/glock_sliderelease.wav", "Reload"),
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
        # normalize to 44.1 kHz mono PCM16 (CS:GO weapon wav convention)
        import io
        import numpy as np
        with wave.open(io.BytesIO(dec), "rb") as w0:
            fr, ch, sw, nf = w0.getframerate(), w0.getnchannels(), w0.getsampwidth(), w0.getnframes()
            frames = w0.readframes(nf)
        arr = np.frombuffer(frames, dtype=np.int16).astype(np.float64)
        if ch == 2:
            arr = arr.reshape(-1, 2).mean(axis=1)
        if fr != 44100:
            n_out = int(round(len(arr) * 44100.0 / fr))
            xp = np.linspace(0.0, len(arr) - 1, num=n_out)
            arr = np.interp(xp, np.arange(len(arr)), arr)
        frames = np.clip(arr, -32768, 32767).astype(np.int16).tobytes()
        pcm = PCM / f"{name}.wav"
        with wave.open(str(pcm), "wb") as w1:
            w1.setnchannels(1); w1.setsampwidth(sw); w1.setframerate(44100)
            w1.writeframes(frames)
        dec = pcm.read_bytes()
        with wave.open(str(pcm), "rb") as w:
            secs = w.getnframes() / w.getframerate()
            ok = w.getframerate() == 44100 and w.getsampwidth() == 2 and w.getnchannels() == 1
            if not ok:
                raise RuntimeError(f"{name}: unexpected fmt {w.getframerate()}Hz ch={w.getnchannels()} sw={w.getsampwidth()}")
        report["sources"][name] = {
            "rez": upath, "bytes_packed": len(data), "seconds": round(secs, 3),
            "sha256": sha256(pcm),
        }
        print(f"[snd] {name}: {len(data)}B -> {len(dec)}B RIFF {secs:.2f}s")
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
    print("[snd] wired", len(report["wired"]), "waves ->", ADDON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
