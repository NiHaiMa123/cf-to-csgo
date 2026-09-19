# -*- coding: utf-8 -*-
"""部署符玄 TTS 语音，替换现有 p_GuanXiaoyu_Voice 内容。

流程：
  1. 音源合并转码 → data/fuxuan_processed/
     - E:\\data\\符玄t阵营  旧批（未改动台词的 wav，mtime 跳过已转码的）
     - E:\\data\\符玄更改版 新批（改动台词，强制覆盖同名旧成品）
  2. 清空 addon vo/<阵营>/ 与 player/ 下全部旧 wav（含 GuanXiaoyu 残留与 fallback）
  3. 按各阵营解包 manifest 逐名写入（无此名的阵营不写，多余名不复制）
  4. sound/player/*.wav（爆头/受伤等音效）一律不写 → 回退原版；
     vo/t_death* 同样跳过（避免听到敌人死亡语音）。
balkan_epic 与新集零重合 → 清空后回退原版英文（特殊干员不做）。
"""
import os
import re
import sys
import glob
import shutil
import subprocess

SRC_OLD = r"E:\data\符玄t阵营"   # 旧批：未改动台词
SRC_NEW = r"E:\data\符玄更改版"  # 新批：改动台词，覆盖同名旧成品
PROCESSED = r"D:\project\cf_to_csgo\data\fuxuan_processed"
UNPACK = r"D:\project\cf_to_csgo\data\csgo_voices_unpacked\sound\player"
ADDON = r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_GuanXiaoyu_Voice\sound"
FACTIONS = ["anarchist", "balkan", "balkan_epic", "leet", "phoenix", "pirate",
            "professional", "separatist"]

# 不回部署的族：疼痛/死亡等每次必触发、世界可闻的音效——删掉即回退原版，
# 避免挨打就说话、死后尸体发声、听到别人死亡语音的问题。
SKIP_FAMILIES = {"t_death", "damage", "pl_burnpain", "pl_fallpain", "pl_pain", "pl_drown",
                 "death", "death_fem", "headshot", "bhit_helmet-1"}
SKIP_PLAYER_DIR = True  # sound/player/*.wav 全部跳过（原版呻吟音恢复）


def _norm(name):
    n = name.lower().replace(".", "_")
    n = re.sub(r"_?\d+wav$", "", n)
    n = re.sub(r"_?\d+$", "", n)
    return n

# ---------- 1. 转码（旧批增量 + 新批强制覆盖同名成品） ----------
os.makedirs(PROCESSED, exist_ok=True)
for src_dir, force in [(SRC_OLD, False), (SRC_NEW, True)]:
    src_wavs = sorted(glob.glob(os.path.join(src_dir, "*.wav")))
    print(f"转码 {len(src_wavs)} 个 wav ← {src_dir}（{'覆盖' if force else '增量'}）")
    for p in src_wavs:
        dst = os.path.join(PROCESSED, os.path.basename(p))
        if not force and os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(p):
            continue
        subprocess.run(
            ["ffmpeg", "-y", "-i", p,
             "-af", "volume=5dB,alimiter=limit=0.95",
             "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", dst],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
have = {os.path.splitext(f)[0] for f in os.listdir(PROCESSED) if f.endswith(".wav")}
print(f"已就绪 {len(have)} 个成品")

# ---------- 2. 清空旧 wav ----------
cleared = 0
for fac in FACTIONS:
    fd = os.path.join(ADDON, "player", "vo", fac)
    if os.path.isdir(fd):
        for f in os.listdir(fd):
            if f.endswith(".wav"):
                os.remove(os.path.join(fd, f))
                cleared += 1
pd = os.path.join(ADDON, "player")
for f in os.listdir(pd):
    fp = os.path.join(pd, f)
    if os.path.isfile(fp) and f.endswith(".wav"):
        os.remove(fp)
        cleared += 1
print(f"清除旧 wav {cleared} 个")

# ---------- 3. 按阵营 manifest 写入 ----------
total = 0
for fac in FACTIONS:
    unpack_dir = os.path.join(UNPACK, "vo", fac)
    if not os.path.isdir(unpack_dir):
        continue
    dest_dir = os.path.join(ADDON, "player", "vo", fac)
    os.makedirs(dest_dir, exist_ok=True)
    n = 0
    for f in os.listdir(unpack_dir):
        if not f.endswith(".wav"):
            continue
        name = f[:-4]
        if _norm(name) in SKIP_FAMILIES:
            continue
        if name in have:
            shutil.copy2(os.path.join(PROCESSED, f), os.path.join(dest_dir, f))
            n += 1
    total += n
    print(f"  {fac}: {n}")

# ---------- 4. player 音效（SKIP_PLAYER_DIR 时跳过，恢复原版） ----------
pn = 0
if not SKIP_PLAYER_DIR:
    for f in os.listdir(UNPACK):
        fp = os.path.join(UNPACK, f)
        if os.path.isfile(fp) and f.endswith(".wav") and f[:-4] in have:
            shutil.copy2(os.path.join(PROCESSED, f), os.path.join(ADDON, "player", f))
            pn += 1
print(f"  player/: {pn}（跳过=恢复原版）")
print(f"部署完成：vo {total} + player {pn}")
