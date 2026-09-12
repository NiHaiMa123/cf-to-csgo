"""P7-S01 — CF original sound for M4A1-雷神 on the CS:GO M4A4 slot.

Bute ShotSoundName is the FMOD event ShootM4A1-S-Beast, not a REZ WAV.
Identity-core samples live in rez/FMODStudio/Weapons/M4A1IronBeast.bank
as FSB streams named M4A1-S-Beast_*. Qingchun / BB / Zeekr / BornBeast
streams are refused.

Wires those samples onto vanilla M4A4 soundscript wave paths
(Weapon_M4A1.Single uses weapons/m4a1/m4a1_01.wav + m4a1_02.wav).
Does not overwrite P6 mesh/materials or the parked frozen addon.

Repro:
  python scripts/p5/p5_p7_original_sound.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())
VGM = Path(_paths.vgmstream())
OUT = REPO / "work" / "p5_leishen" / "p7"
STAGING = OUT / "addon"
RAW_DIR = OUT / "fmod_raw"
PCM_DIR = OUT / "pcm"
LOG_DIR = OUT / "logs"
BUTE = REPO / "work" / "p5_leishen" / "t03" / "bute_canonical.json"

ADDON_NAME = "p_cf_leishen_m4a4_p7_sound"
P6_ADDON = "p_cf_leishen_m4a4_p6"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
MIGI_ADDONS = GAME / "migi" / "csgo" / "addons"
PARK = GAME / "migi" / "csgo" / "_parked_addons"

BANK_REL = Path("rez/FMODStudio/Weapons/M4A1IronBeast.bank")
FORBIDDEN_NAME_NEEDLES = (
    "BORNBEEST",
    "BORNBEAST",
    "QINGCHUN",
    "ZEEKR",
    "BB_M4A1",
    "BBM4A1",
    "TRANSFORMERS_",
)
IDENTITY_PREFIX = "M4A1-S-BEAST"
# Draw sequence is 35 frames @ 30 fps. Bolt motion starts at frame 10.
DRAW_BOLT_DELAY_S = 10 / 30
# Weapon_M4A1.Draw is CHAN_STATIC volume 0.3; boost so Reload/拉栓 is audible.
DRAW_VOLUME_COMPENSATE = 3.3

# CS:GO M4A4 (Weapon_M4A1.Single) reads these waves. Pitch 120 is compensated
# in the close-fire WAV so playback matches the CF sample pitch.
WIRE_MAP: list[dict[str, Any]] = [
    {
        "bute_event": "ShootM4A1-S-Beast",
        "stream": "M4A1-S-Beast_SHOOT_1",
        "csgo_event": "Weapon_M4A1.Single",
        "waves": ["sound/weapons/m4a1/m4a1_01.wav", "sound/weapons/m4a1/m4a1_02.wav"],
        "pitch_compensate": 120,
        "grade": "OBSERVED",
        "note": "Listen 01. User: 01-06 match filenames; fire was already correct.",
    },
    {
        "bute_event": "ShootM4A1-S-Beast (distant uses same shoot sample)",
        "stream": "M4A1-S-Beast_SHOOT_1",
        "csgo_event": "Weapon_M4A4.SingleDistant",
        "waves": ["sound/weapons/m4a1/m4a1_distant_01.wav"],
        "pitch_compensate": 100,
        "grade": "OBSERVED",
        "note": "Listen 07 BeastAir was rejected. Distant reuses listen 01, not 07-13.",
    },
]

EXTRACT_ONLY = ("M4A1-S-Beast_knifeAttack",)
# Match CS M4A4 events for now. CF animation still later P7.
# Reload: Clipout@11 喷气+退弹 together, Clipin@35 上弹, ClipHit@57 拉栓.
# Draw bolt: BoltBack@17 拉栓.
CF_RELOAD_GAS = "M4A1-S-Beast_GasEjection"
CF_RELOAD_CLIPOUT = "M4A1-S-Beast_ClipOut"
CF_RELOAD_CLIPIN = "M4A1-S-Beast_ClipIn"
CF_RELOAD_ORDER = (
    CF_RELOAD_GAS,
    CF_RELOAD_CLIPOUT,
    CF_RELOAD_CLIPIN,
    "M4A1-S-Beast_Reload",
)
BOLT_CLIP = "M4A1-S-Beast_Reload"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def tree_hashes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows[path.relative_to(root).as_posix()] = sha256_file(path)
    return rows


def which_ffmpeg() -> Path:
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError("ffmpeg is required to resample FMOD dumps to Source 1 PCM")
    return Path(found)


def run_checked(cmd: list[str], log_name: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{log_name}.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / f"{log_name}.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed ({log_name}): {(proc.stderr or proc.stdout or '')[:800]}")
    return proc


def list_streams(bank: Path) -> list[dict[str, Any]]:
    info = json.loads(run_checked([str(VGM), "-I", str(bank)], "vgm_bank_info").stdout)
    total = int(info["streamInfo"]["total"])
    rows: list[dict[str, Any]] = []
    for index in range(1, total + 1):
        payload = json.loads(
            run_checked([str(VGM), "-I", "-s", str(index), str(bank)], f"vgm_info_{index:02d}").stdout
        )
        name = str(payload["streamInfo"]["name"] or "")
        samples = int(payload["numberOfSamples"])
        rate = int(payload["sampleRate"])
        rows.append(
            {
                "index": int(payload["streamInfo"]["index"]),
                "subsong": index,
                "name": name,
                "samples": samples,
                "rate": rate,
                "channels": int(payload["channels"]),
                "seconds": round(samples / rate, 3) if rate else 0.0,
                "encoding": payload.get("encoding"),
            }
        )
    return rows


def assert_identity_name(name: str) -> None:
    upper = name.upper()
    for needle in FORBIDDEN_NAME_NEEDLES:
        if needle in upper:
            raise RuntimeError(f"refusing non-identity stream {name}")
    if not upper.startswith(IDENTITY_PREFIX):
        raise RuntimeError(f"stream {name} is not M4A1-S-Beast identity-core")


def extract_stream(bank: Path, subsong: int, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_checked(
        [str(VGM), "-i", "-s", str(subsong), "-o", str(dest), str(bank)],
        f"vgm_extract_{dest.stem}",
    )
    if not dest.is_file() or dest.stat().st_size < 44:
        raise RuntimeError(f"vgmstream produced no WAV for subsong {subsong}")
    return {"path": rel(dest), "sha256": sha256_file(dest), "bytes": dest.stat().st_size}


def pcm_info(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as handle:
        if handle.getnchannels() not in (1, 2) or handle.getsampwidth() != 2 or handle.getframerate() != 44100:
            raise RuntimeError(f"PCM check failed for {path.name}")
        frames = handle.getnframes()
        channels = handle.getnchannels()
    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "channels": channels,
        "rate": 44100,
        "seconds": round(frames / 44100, 3),
    }


def concat_pcm(inputs: list[Path], dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = which_ffmpeg()
    labels = "".join(
        f"[{index}]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        f"asetpts=PTS-STARTPTS[s{index}];"
        for index in range(len(inputs))
    )
    joined = "".join(f"[s{index}]" for index in range(len(inputs)))
    graph = f"{labels}{joined}concat=n={len(inputs)}:v=0:a=1[out]"
    cmd = [str(ffmpeg), "-y"]
    for path in inputs:
        cmd.extend(["-i", str(path)])
    cmd.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            "[out]",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    run_checked(cmd, f"ffmpeg_concat_{dest.stem}")
    return pcm_info(dest)


def mix_pcm(inputs: list[Path], dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = which_ffmpeg()
    labels = "".join(f"[{index}]aformat=sample_fmts=fltp:channel_layouts=stereo[s{index}];" for index in range(len(inputs)))
    joined = "".join(f"[s{index}]" for index in range(len(inputs)))
    graph = (
        f"{labels}{joined}amix=inputs={len(inputs)}:duration=longest:normalize=0,"
        f"alimiter=limit=0.95[out]"
    )
    cmd = [str(ffmpeg), "-y"]
    for path in inputs:
        cmd.extend(["-i", str(path)])
    cmd.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            "[out]",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    run_checked(cmd, f"ffmpeg_mix_{dest.stem}")
    return pcm_info(dest)


def delay_amplify_pcm(src: Path, dest: Path, delay_s: float, amplify: float) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = which_ffmpeg()
    delay_ms = int(round(delay_s * 1000))
    filters = [f"adelay={delay_ms}|{delay_ms}"]
    if amplify != 1.0:
        filters.append(f"volume={amplify}")
        filters.append("alimiter=limit=0.95")
    run_checked(
        [
            str(ffmpeg),
            "-y",
            "-i",
            str(src),
            "-af",
            ",".join(filters),
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ],
        f"ffmpeg_delay_{dest.stem}",
    )
    info = pcm_info(dest)
    info["delay_s"] = delay_s
    info["amplify"] = amplify
    return info


def silence_pcm(dest: Path, seconds: float = 0.05) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = which_ffmpeg()
    run_checked(
        [
            str(ffmpeg),
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=mono:d={seconds}",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ],
        f"ffmpeg_silence_{dest.stem}",
    )
    return pcm_info(dest)


def stage_waves(src: Path, waves: list[str]) -> list[dict[str, str]]:
    rows = []
    for relative in waves:
        dest = STAGING / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        rows.append({"wave": relative.replace("\\", "/"), "sha256": sha256_file(dest)})
    return rows


def convert_pcm(src: Path, dest: Path, pitch: int, channels: int) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = which_ffmpeg()
    with wave.open(str(src), "rb") as handle:
        src_rate = handle.getframerate()
    filters = []
    if pitch != 100:
        # Source pitch 120 plays 20% fast. Slow the file so the engine restores CF pitch.
        filters.append(f"asetrate={src_rate}*{100}/{int(pitch)}")
    filters.append("aresample=44100")
    cmd = [
        str(ffmpeg),
        "-y",
        "-i",
        str(src),
        "-af",
        ",".join(filters),
        "-ar",
        "44100",
        "-ac",
        str(1 if channels == 1 else 2),
        "-c:a",
        "pcm_s16le",
        str(dest),
    ]
    run_checked(cmd, f"ffmpeg_{dest.stem}")
    with wave.open(str(dest), "rb") as handle:
        if handle.getnchannels() not in (1, 2) or handle.getsampwidth() != 2 or handle.getframerate() != 44100:
            raise RuntimeError(f"PCM check failed for {dest.name}")
        frames = handle.getnframes()
        ch = handle.getnchannels()
    return {
        "path": rel(dest),
        "sha256": sha256_file(dest),
        "bytes": dest.stat().st_size,
        "channels": ch,
        "rate": 44100,
        "seconds": round(frames / 44100, 3),
        "pitch_compensate": pitch,
    }


def frozen_status() -> dict[str, Any]:
    return {
        "frozen_in_addons": (MIGI_ADDONS / FROZEN_NAME).exists(),
        "frozen_parked": (PARK / FROZEN_NAME).exists(),
        "p6_live": (MIGI_ADDONS / P6_ADDON).exists(),
        "p6_has_sound": (MIGI_ADDONS / P6_ADDON / "sound").exists(),
    }


def deploy_addon(staging_hashes: dict[str, str]) -> dict[str, Any]:
    if ADDON_NAME in {P6_ADDON, FROZEN_NAME}:
        raise RuntimeError("refusing to deploy over P6 or frozen")
    target = MIGI_ADDONS / ADDON_NAME
    if target.exists():
        existing = tree_hashes(target)
        if existing == staging_hashes:
            return {"target": str(target), "action": "verified_existing", "hashes": existing}
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for relative in staging_hashes:
        src = STAGING / relative
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    deployed = tree_hashes(target)
    if deployed != staging_hashes:
        raise RuntimeError("post-deploy hash mismatch")
    p6 = MIGI_ADDONS / P6_ADDON
    frozen = PARK / FROZEN_NAME
    return {
        "target": str(target),
        "action": "created",
        "hashes": deployed,
        "p6_untouched": p6.exists(),
        "frozen_untouched": frozen.exists(),
    }


def write_report(report: dict[str, Any]) -> None:
    wired = report["wired"]
    lines = [
        "# P7-S01 — CF original sound (M4A1-雷神)",
        "",
        f"Result: **{report['result']}**. P6 mesh addon `{P6_ADDON}` is unchanged. Frozen addon not modified. P4-M01 remains **INCOMPLETE**.",
        "",
        f"Addon: `{ADDON_NAME}`",
        f"Deploy: `{report['deploy']['target']}` ({report['deploy']['action']})",
        "",
        "P6 only replaced the M4A4 viewmodel and textures. Vanilla `Weapon_M4A1.Single` still pointed at `weapons/m4a1/m4a1_01.wav`. Identity-core has no REZ WAV; Bute `ShotSoundName` is the FMOD event `ShootM4A1-S-Beast`.",
        "",
        f"Source bank: `{BANK_REL.as_posix()}` SHA256 `{report['bank']['sha256'][:16]}…`. Extractor: vgmstream. Qingchun / BB / Zeekr / BornBeast streams were not used.",
        "",
        "Wired:",
        "",
        "| Bute / CF | FSB stream | CS:GO event | wave | grade |",
        "|---|---|---|---|---|",
    ]
    for row in wired:
        waves = ", ".join(f"`{Path(item).name}`" for item in row["waves"])
        lines.append(
            f"| `{row['bute_event']}` | `{row['stream']}` | `{row['csgo_event']}` | {waves} | {row['grade']} |"
        )
    lines.extend(
        [
            "",
            "User listen: 01-06 match filenames. 07 BeastAir is wrong. 08-13 unknown, unused.",
            "",
            "Match CS actions: Clipout = 喷气+退弹 together, Clipin = 上弹, ClipHit = 拉栓 (later, not packed into clipout). Draw BoltBack = 拉栓. Fire=01. CF animation still later P7.",
            "",
            "`BoltForward` / `BoltBack` stay silent. Qingchun / BB / Zeekr / BornBeast unused.",
            "",
            "Not done: Inspect, CF animation, world model, knife foley, lighting.",
            "",
            "This is not P4-M01 PASS and not release-quality audio mastering.",
            "",
        ]
    )
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not VGM.is_file():
        raise RuntimeError(f"vgmstream missing: {VGM}")
    which_ffmpeg()
    bank = CF / BANK_REL
    if not bank.is_file():
        raise RuntimeError(f"FMOD bank missing: {bank}")

    for path in (OUT, STAGING, RAW_DIR, PCM_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)

    bute = json.loads(BUTE.read_text(encoding="utf-8"))
    expected_events = {
        "ShotSoundName": "ShootM4A1-S-Beast",
        "MagazineClipOutSoundName": "ClipOutM4A1-S-Beast",
        "MagazineClipInSoundName": "ClipInM4A1-S-Beast",
        "ReloadSoundName": "ReloadM4A1-S-Beast",
    }
    for field, value in expected_events.items():
        if bute.get(field) != value:
            raise RuntimeError(f"canonical Bute {field}={bute.get(field)!r}, expected {value}")

    streams = list_streams(bank)
    by_name = {row["name"]: row for row in streams}
    wanted = list(dict.fromkeys(
        [row["stream"] for row in WIRE_MAP] + list(EXTRACT_ONLY) + list(CF_RELOAD_ORDER)
    ))
    for name in wanted:
        assert_identity_name(name)
        if name not in by_name:
            raise RuntimeError(f"stream {name} not in {BANK_REL}")

    extracted: dict[str, Any] = {}
    converted: dict[str, Any] = {}
    for name in wanted:
        meta = by_name[name]
        raw_path = RAW_DIR / f"{name}.wav"
        extracted[name] = {
            **meta,
            "extract": extract_stream(bank, meta["subsong"], raw_path),
        }

    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True, exist_ok=True)

    wired_out: list[dict[str, Any]] = []
    for item in WIRE_MAP:
        name = item["stream"]
        src = RAW_DIR / f"{name}.wav"
        pcm_path = PCM_DIR / f"{name}.wav"
        pcm = convert_pcm(src, pcm_path, item["pitch_compensate"], by_name[name]["channels"])
        converted[name] = pcm
        wired_out.append({**item, "pcm": pcm, "deployed": stage_waves(pcm_path, item["waves"])})

    for name in CF_RELOAD_ORDER:
        src = RAW_DIR / f"{name}.wav"
        pcm_path = PCM_DIR / f"{name}.wav"
        if name not in converted:
            converted[name] = convert_pcm(src, pcm_path, 100, by_name[name]["channels"])

    gas_clip_pcm = PCM_DIR / "gas_and_clipout.wav"
    converted["gas_and_clipout"] = mix_pcm(
        [PCM_DIR / f"{CF_RELOAD_GAS}.wav", PCM_DIR / f"{CF_RELOAD_CLIPOUT}.wav"],
        gas_clip_pcm,
    )
    silence_path = PCM_DIR / "silence.wav"
    converted["silence"] = silence_pcm(silence_path)
    bolt_pcm = PCM_DIR / f"{BOLT_CLIP}.wav"

    composites = [
        {
            "bute_event": "喷气+退弹 together at CS Clipout",
            "stream": f"{CF_RELOAD_GAS}|{CF_RELOAD_CLIPOUT}",
            "csgo_event": "Weapon_M4A1.Clipout",
            "waves": ["sound/weapons/m4a1/m4a1_clipout.wav"],
            "grade": "OBSERVED",
            "note": "User: 退弹的时候一起播放喷气. CS reload frame 11.",
            "pcm": converted["gas_and_clipout"],
            "deployed": stage_waves(gas_clip_pcm, ["sound/weapons/m4a1/m4a1_clipout.wav"]),
        },
        {
            "bute_event": "上弹 at CS Clipin",
            "stream": CF_RELOAD_CLIPIN,
            "csgo_event": "Weapon_M4A1.Clipin",
            "waves": ["sound/weapons/m4a1/m4a1_clipin.wav"],
            "grade": "OBSERVED",
            "note": "CS reload frame 35.",
            "pcm": converted[CF_RELOAD_CLIPIN],
            "deployed": stage_waves(PCM_DIR / f"{CF_RELOAD_CLIPIN}.wav", ["sound/weapons/m4a1/m4a1_clipin.wav"]),
        },
        {
            "bute_event": "拉栓 at CS ClipHit",
            "stream": BOLT_CLIP,
            "csgo_event": "Weapon_M4A1.ClipHit",
            "waves": ["sound/weapons/m4a1/m4a1_cliphit.wav"],
            "grade": "OBSERVED",
            "note": "User: 拉栓 was too early in the packed clip. CS reload frame 57.",
            "pcm": converted[BOLT_CLIP],
            "deployed": stage_waves(bolt_pcm, ["sound/weapons/m4a1/m4a1_cliphit.wav"]),
        },
        {
            "bute_event": "silence draw rustle",
            "stream": "silence",
            "csgo_event": "Weapon_M4A1.Draw",
            "waves": ["sound/weapons/m4a1/m4a1_draw.wav"],
            "grade": "SOURCE1_DESIGN_CANDIDATE",
            "note": "拉栓 waits for CS BoltBack, not the draw raise.",
            "pcm": converted["silence"],
            "deployed": stage_waves(silence_path, ["sound/weapons/m4a1/m4a1_draw.wav"]),
        },
        {
            "bute_event": "silence CS BoltForward",
            "stream": "silence",
            "csgo_event": "Weapon_M4A1.BoltForward",
            "waves": ["sound/weapons/m4a1/m4a1_boltforward.wav"],
            "grade": "SOURCE1_DESIGN_CANDIDATE",
            "note": "Same CHAN_ITEM as BoltBack; leaving vanilla CS bolt would cut CF 拉栓.",
            "pcm": converted["silence"],
            "deployed": stage_waves(silence_path, ["sound/weapons/m4a1/m4a1_boltforward.wav"]),
        },
        {
            "bute_event": "拉栓 at CS BoltBack (切枪)",
            "stream": BOLT_CLIP,
            "csgo_event": "Weapon_M4A1.BoltBack",
            "waves": ["sound/weapons/m4a1/m4a1_boltback.wav"],
            "grade": "OBSERVED",
            "note": "User: CS also has a 拉栓 action. Draw frame 17.",
            "pcm": converted[BOLT_CLIP],
            "deployed": stage_waves(bolt_pcm, ["sound/weapons/m4a1/m4a1_boltback.wav"]),
        },
    ]
    wired_out.extend(composites)

    staging_hashes = tree_hashes(STAGING)
    if not staging_hashes:
        raise RuntimeError("P7 staging produced no sound files")
    frozen = frozen_status()
    if frozen["frozen_in_addons"]:
        raise RuntimeError("frozen addon is still in MIGI addons; stop before adding a second overlay")
    if not frozen["p6_live"]:
        raise RuntimeError("P6 live addon is missing; sound overlay has nothing to sit on")
    deploy = deploy_addon(staging_hashes)

    report = {
        "schema": "cf2.p7.original-sound.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P7-S01",
        "result": "P7_ORIGINAL_SOUND_DEPLOYED",
        "final_target_identity": True,
        "final_cf_material": False,
        "p4_m01": "INCOMPLETE",
        "addon_name": ADDON_NAME,
        "p6_addon": P6_ADDON,
        "bute_events": {field: bute.get(field) for field in list(expected_events) + ["KnifeAttackSoundName", "Extra01SoundName"]},
        "bank": {
            "rel_cf": BANK_REL.as_posix(),
            "path": str(bank),
            "sha256": sha256_file(bank),
            "size": bank.stat().st_size,
            "stream_count": len(streams),
        },
        "streams": streams,
        "extracted": extracted,
        "converted": converted,
        "wired": wired_out,
        "refused": {
            "needles": list(FORBIDDEN_NAME_NEEDLES),
            "note": "Qingchun/BB/Zeekr REZ WAVs and BornBeast FSB streams are not identity-core.",
        },
        "staging": rel(STAGING),
        "staging_hashes": staging_hashes,
        "park_frozen": frozen,
        "deploy": {k: v for k, v in deploy.items() if k != "hashes"} | {"file_count": len(deploy["hashes"])},
        "notes": [
            "User listen: 01-06 match filenames; 07 wrong; 08-13 unknown unused.",
            "CS-timed reload: clipout=喷气+退弹, clipin=上弹, cliphit=拉栓. Draw BoltBack=拉栓. Fire=01.",
            "Knife 06 extracted, not wired to M4A4.",
            "Weapon_M4A1.Single pitch 120 is compensated in the close-fire WAV.",
            "Inspect / CF animation / world model are still open.",
            "Not a P4-M01 PASS.",
        ],
    }
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "mapping.json").write_text(
        json.dumps(
            {
                "addon_name": ADDON_NAME,
                "result": report["result"],
                "bank_sha256": report["bank"]["sha256"],
                "wired": [
                    {
                        "bute_event": row["bute_event"],
                        "stream": row["stream"],
                        "csgo_event": row["csgo_event"],
                        "waves": row["waves"],
                        "grade": row["grade"],
                    }
                    for row in wired_out
                ],
                "staging_hashes": staging_hashes,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_report(report)
    print(
        json.dumps(
            {
                "result": report["result"],
                "addon": ADDON_NAME,
                "deploy": deploy["action"],
                "files": list(staging_hashes),
                "out": rel(OUT),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
