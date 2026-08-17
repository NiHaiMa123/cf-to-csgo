# -*- coding: utf-8 -*-
"""把一套 TTS 语音（按目标文件名命名）分发到 7 个基础 T 阵营并部署到 MIGI。

用法：
    python scripts/csgo_pack/deploy_tts_voices.py                 # 默认读 rvc/output/tts_standard
    python scripts/csgo_pack/deploy_tts_voices.py --src <目录>     # 指定 wav 目录

命名约定：wav 文件名必须等于目标文件名（如 t_smoke01.wav、radio.enemyspotted01.wav）。
对每个 wav，脚本在 7 个 T 阵营的解包目录里查找同名文件，若某阵营存在该文件名则复制到
migi/csgo/addons/p_GuanXiaoyu_Voice/sound/player/vo/<阵营>/ 下（同名覆盖）。

流程：校验 wav 格式(16-bit/mono/44.1kHz) → 按文件名分发到对应阵营。
"""
import os
import sys
import glob
import wave
import shutil
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir, project_dir

T_FACTIONS = ["anarchist", "balkan", "leet", "phoenix", "pirate",
              "professional", "separatist"]
UNPACK_VO = os.path.join(project_dir(), "data", "csgo_voices_unpacked",
                         "sound", "player", "vo")
MIGI_VO = os.path.join(game_dir(), "migi", "csgo", "addons",
                       "p_GuanXiaoyu_Voice", "sound", "player", "vo")


def faction_file_sets():
    """每个阵营在解包数据里拥有的文件名集合（用于判断该文件名属于哪些阵营）。"""
    sets = {}
    for fac in T_FACTIONS:
        d = os.path.join(UNPACK_VO, fac)
        sets[fac] = set(os.listdir(d)) if os.path.isdir(d) else set()
    return sets


def main():
    ap = argparse.ArgumentParser(description="TTS 语音按文件名分发到 T 阵营并部署到 MIGI")
    ap.add_argument("--src", default=r"D:\project\rvc\output\tts_standard",
                    help="TTS 生成的 wav 目录（文件名 = 目标文件名）")
    args = ap.parse_args()

    fac_sets = faction_file_sets()
    deployed, no_match, bad_format = [], [], []
    wavs = sorted(glob.glob(os.path.join(args.src, "*.wav")))
    for wav in wavs:
        fname = os.path.basename(wav)
        try:
            w = wave.open(wav, "rb")
            ok = (w.getnchannels() == 1 and w.getsampwidth() == 2
                  and w.getframerate() == 44100)
            w.close()
        except Exception:
            ok = False
        if not ok:
            bad_format.append(fname)
            continue
        matched = [fac for fac in T_FACTIONS if fname in fac_sets[fac]]
        if not matched:
            no_match.append(fname)
            continue
        for fac in matched:
            dest = os.path.join(MIGI_VO, fac, fname)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(wav, dest)
            deployed.append((fname, fac))

    print(f"wav 总数: {len(wavs)}")
    print(f"部署条目: {len(deployed)}")
    print(f"无匹配阵营(文件名不在任何 T 阵营): {len(no_match)}  {no_match[:10]}")
    print(f"格式不合规: {len(bad_format)}  {bad_format[:10]}")


if __name__ == "__main__":
    main()
