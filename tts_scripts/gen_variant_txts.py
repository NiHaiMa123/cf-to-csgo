# -*- coding: utf-8 -*-
"""汇总 tts_scripts/lines/part*.py 的台词数据，生成每个变体一个 txt。

每个 part 文件定义一个 LINES = { 变体文件名: "台词" }。
本脚本：
  1. 加载所有 part 的 LINES；
  2. 与 variants.json（全部变体清单）比对，报告缺失/多余；
  3. 把台词写入 D:\\project\\rvc\\data\\txt\\{变体文件名}.txt。
"""
import os
import glob
import json

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = r"D:\project\rvc\data\txt"

variants = json.load(open(os.path.join(BASE, "variants.json"), encoding="utf-8"))
all_variants = set()
for names in variants.values():
    all_variants.update(names)

lines = {}
for mod in sorted(glob.glob(os.path.join(BASE, "lines", "part*.py"))):
    ns = {}
    exec(open(mod, encoding="utf-8").read(), ns)
    lines.update(ns["LINES"])

os.makedirs(OUT, exist_ok=True)
written = 0
missing = []
for fname in sorted(all_variants):  # fname 形如 t_smoke01.wav
    key = fname[:-4]  # 去 .wav
    line = lines.get(key)
    if line is None:
        missing.append(fname)
        continue
    with open(os.path.join(OUT, key + ".txt"), "w", encoding="utf-8") as f:
        f.write(line + "\n")
    written += 1

extra = set(lines) - set(f[:-4] for f in all_variants)
print(f"已写 {written}/{len(all_variants)} 个 txt")
print(f"缺失台词: {len(missing)}  {sorted(missing)[:20]}")
print(f"多余条目: {len(extra)}  {sorted(extra)[:20]}")
