# Export listen-only WAVs. Not wired into the game.
# FSB layers are 0.2-1.2s; Windows players skip those. Repeat each clip so it is audible.
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

VGM = Path(r"D:\project\cf_to_csgo\tools\vgmstream\vgmstream-cli.exe")
FFMPEG = shutil.which("ffmpeg")
BANK = Path(r"D:\Program Files\CF(2)\rez\FMODStudio\Weapons\M4A1IronBeast.bank")
OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7\listen")

LISTEN = [
    (8, "01_射击_SHOOT_1.wav", "射击（你说过这段是对的）"),
    (12, "02_切枪时那个_GasEjection.wav", "上一版切枪听到的那段，你说是换弹"),
    (17, "03_Beast_Reload.wav", "名字带 Reload"),
    (1, "04_Beast_ClipOut.wav", "名字带 ClipOut"),
    (11, "05_Beast_ClipIn.wav", "名字带 ClipIn"),
    (7, "06_Beast_knifeAttack.wav", "近战"),
    (2, "07_BeastAir_远处尾音.wav", "远处/尾音"),
    (6, "08_同bank层_Reload_03.wav", "同 bank 层 Reload_03"),
    (3, "09_同bank层_ClipOut.wav", "同 bank 层 ClipOut"),
    (10, "10_同bank层_ClipIn_01.wav", "同 bank 层 ClipIn"),
    (14, "11_同bank层_Swish_02.wav", "同 bank 层 Swish"),
    (15, "12_同bank层_Shoot_02.wav", "同 bank 层 Shoot_02"),
    (9, "13_同bank层_Shoot_03.wav", "同 bank 层 Shoot_03"),
]


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or b"").decode("utf-8", "replace")[:800])


def make_repeatable(src: Path, dest: Path, times: int = 4) -> None:
    # stereo 44100, 0.5s lead-in, clip, 0.45s gap, repeat, 1.2s tail
    n = 1 + times * 2  # pre + (clip,gap)*times but last gap replaced by post
    parts = ["[pre]"]
    labels = [
        "anullsrc=r=44100:cl=stereo:d=0.55[pre];",
        "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,asetpts=PTS-STARTPTS[c];",
        "anullsrc=r=44100:cl=stereo:d=0.45[g];",
        "anullsrc=r=44100:cl=stereo:d=1.20[post];",
    ]
    for i in range(times):
        parts.append("[c]")
        parts.append("[g]" if i < times - 1 else "[post]")
    graph = "".join(labels) + "".join(parts) + f"concat=n={len(parts)}:v=0:a=1[out]"
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(src),
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


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    once = OUT / "原长_只播一遍"
    play = OUT / "请听这些_每段重复4遍"
    once.mkdir(parents=True)
    play.mkdir(parents=True)
    tmp = OUT / "_tmp"
    tmp.mkdir()
    catalog = []
    play_files: list[Path] = []
    for subsong, filename, note in LISTEN:
        raw = tmp / f"{subsong:02d}.wav"
        run([str(VGM), "-i", "-s", str(subsong), "-o", str(raw), str(BANK)])
        info = json.loads(
            subprocess.run(
                [str(VGM), "-I", "-s", str(subsong), str(BANK)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        src_once = once / filename
        run(
            [
                FFMPEG,
                "-y",
                "-i",
                str(raw),
                "-ar",
                "44100",
                "-c:a",
                "pcm_s16le",
                str(src_once),
            ]
        )
        dest = play / filename
        make_repeatable(src_once, dest)
        play_files.append(dest)
        catalog.append(
            {
                "file": filename,
                "note": note,
                "bank_name": info["streamInfo"]["name"],
                "original_seconds": round(info["numberOfSamples"] / info["sampleRate"], 3),
                "channels": info["channels"],
            }
        )

    # One concatenated pass, 1.6s gap between numbers.
    concat_list = tmp / "concat.txt"
    gap = tmp / "gap.wav"
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo:d=1.6",
            "-c:a",
            "pcm_s16le",
            str(gap),
        ]
    )
    lines = []
    for path in play_files:
        lines.append(f"file '{path.as_posix()}'")
        lines.append(f"file '{gap.as_posix()}'")
    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    all_path = play / "00_从01到13连播.wav"
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(all_path),
        ]
    )
    shutil.rmtree(tmp)

    text = [
        "雷神 FMOD 试听",
        "",
        "请听文件夹：请听这些_每段重复4遍",
        "00_从01到13连播.wav  从头放到尾，中间有空档。",
        "",
        "原声在 bank 里就是短层（0.2~1.2秒），不是整段换弹动画。",
        "Windows 对超短 wav 经常一闪就关，所以每段前面留空、重复4遍。",
        "原长_只播一遍 里是未经重复的原时长，不用这个听。",
        "",
        "没有 Qingchun / BB / Zeekr / BornBeast。",
        "",
        "听完回编号即可，例如：换弹=02  拉栓=08  切枪=11",
        "",
    ]
    for row in catalog:
        text.append(f"{row['file']}")
        text.append(f"  {row['note']}")
        text.append(f"  bank名 {row['bank_name']}  原长 {row['original_seconds']}s")
        text.append("")
    (OUT / "请先看这个.txt").write_text("\n".join(text), encoding="utf-8")
    (play / "请先看这个.txt").write_text("\n".join(text), encoding="utf-8")
    print(play)
    for row in catalog:
        print(f"{row['file']}  {row['original_seconds']}s  {row['bank_name']}")


if __name__ == "__main__":
    main()
