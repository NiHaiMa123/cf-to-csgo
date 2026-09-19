# -*- coding: utf-8 -*-
"""把 fuxuan_text 精简为「相对已生成 wav 有改动」的 txt。

旧行 = pools_v1_diff.OLD（收录的族）按"旧成员表"取词；
未收录族 / tmap 模板 / killcount 数字逻辑 两版一致 → 视为未改动。
旧成员表 = 当前 union ∪ 当时部署残留的额外变体名（保证旧序号正确）。

输出：
  - 删除未改动/无用的 txt（manifest 同步重写为仅存留项）
  - 打印改动清单
"""
import os
import re
import sys
import json
import importlib

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))

from gen_fuxuan_txts import (OUT, UNPACK_VO, FACTIONS, SKIP_FAMILIES, norm,
                             POOLS)
from pools_v1_diff import OLD

# 生成 E:\data 时存在于部署目录、但不在解包 union 的额外变体名
LEGACY_EXTRAS = {
    "affirmative04", "affirmative05", "affirmative06",
    "enemydown13", "goingtoplantbombb03", "help07",
    "negativeno01", "negativeno02", "requestreport05",
    "thanks06", "thanks07", "thanks08", "waitinghere06",
    "t_death08", "t_death09", "t_death10",
}


def main():
    # 当前 union（7 阵营解包）
    vo_names = set()
    for fac in FACTIONS:
        d = os.path.join(UNPACK_VO, fac)
        if os.path.isdir(d):
            vo_names.update(x[:-4] for x in os.listdir(d) if x.endswith(".wav"))

    # 族成员表：new = union；old = union ∪ 旧残留名
    new_members, old_members = {}, {}
    for n in vo_names:
        new_members.setdefault(norm(n), []).append(n)
    for n in vo_names | LEGACY_EXTRAS:
        old_members.setdefault(norm(n), []).append(n)
    for v in new_members.values():
        v.sort()
    for v in old_members.values():
        v.sort()

    manifest = json.load(open(os.path.join(OUT, "_manifest.json"), encoding="utf-8"))

    changed, unchanged = [], []
    for fam, members in sorted(new_members.items()):
        if fam in SKIP_FAMILIES or fam.startswith("tmap") or fam == "radiobotkillcount":
            continue
        new_pool = POOLS.get(fam, [])
        old_pool = OLD.get(fam)
        for name in members:
            new_line = manifest.get(name)
            if new_line is None:
                continue
            if old_pool is None:
                unchanged.append(name)
                continue
            oi = old_members[fam].index(name)
            old_line = old_pool[oi % len(old_pool)]
            (changed if old_line != new_line else unchanged).append(name)

    # 删除：未改动 + 不在 manifest 的过期 txt
    keep = set(changed)
    removed = 0
    for f in os.listdir(OUT):
        if not f.endswith(".txt"):
            continue
        name = f[:-4]
        if name not in keep:
            os.remove(os.path.join(OUT, f))
            removed += 1
    with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({k: manifest[k] for k in sorted(keep)}, f, ensure_ascii=False, indent=1)

    print(f"改动 {len(changed)} 个，未改动剔除 {len(unchanged)} 个，删除过期/未改 txt {removed} 个")
    print("改动文件示例:")
    for n in changed[:40]:
        print(" ", n)
    if len(changed) > 40:
        print(f"  ... 共 {len(changed)} 个")


if __name__ == "__main__":
    main()
