# -*- coding: utf-8 -*-
"""生成符玄 TTS 台词 txt：一个解包音频文件对应一个 txt。

覆盖范围（基础干员 = 7 个基础 T 阵营，不含 balkan_epic 等特殊套）：
  1. data/csgo_voices_unpacked/sound/player/vo/<7阵营> 的并集文件名；
  2. 已部署 migi 目录中残留的额外变体名（affirmative04 之类）；
  3. data/csgo_voices_unpacked/sound/player/*.wav 受伤/死亡音。

分配规则：
  - 非 tmap 族：文件名归一化(去点/数字后缀) → pools_*.py 的 POOLS[族][族内序号]；
  - tmap_* 族：{方位模板 × 地点} 组合，全局序号取词，保证每条唯一；
  - player 音效：PLAYER_LINES 精确表 → 疼痛池兜底。

输出：D:\\project\\dotstts\\inputs\\fuxuan_text\\<文件名>.txt
"""
import os
import re
import sys
import json
import importlib

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))  # tts_scripts/ 目录，供 import fuxuan.pools_*

OUT = r"D:\project\dotstts\inputs\fuxuan_text"
UNPACK_VO = r"D:\project\cf_to_csgo\data\csgo_voices_unpacked\sound\player\vo"
UNPACK_PLAYER = r"D:\project\cf_to_csgo\data\csgo_voices_unpacked\sound\player"
MIGI_VO = r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_GuanXiaoyu_Voice\sound\player\vo"
FACTIONS = ["anarchist", "balkan", "leet", "phoenix", "pirate", "professional", "separatist"]

# 不生成台词的族：疼痛/死亡等每次必触发、世界可闻的音效——部署时跳过即回退原版。
SKIP_FAMILIES = {"t_death", "damage", "pl_burnpain", "pl_fallpain", "pl_pain", "pl_drown",
                 "death", "death_fem", "headshot", "bhit_helmet-1"}

# ---------- 加载台词池 ----------
POOLS = {}
for mod_name in ["pools_radio", "pools_combat", "pools_bot"]:
    mod = importlib.import_module(f"fuxuan.{mod_name}")
    overlap = set(POOLS) & set(mod.POOLS)
    assert not overlap, f"pool key 冲突: {overlap}"
    POOLS.update(mod.POOLS)

# ---------- tmap 组合模板 ----------
TMAP_LOCS = ["A点", "B点", "C点", "中路", "长道", "短道", "小道", "天桥", "连接处", "双门",
             "洞口", "平台", "斜坡", "楼梯", "后院", "侧巷", "下水道", "包点", "人质房", "敌营",
             "香蕉道", "阁楼", "车库", "大厅", "走廊", "窗口", "暗道", "阳台", "广场", "书房"]
TMAP_TPLS = [
    "{loc}有敌，小心。",
    "卦象示警，{loc}异动。",
    "{loc}，敌人现身。",
    "注意{loc}。",
    "{loc}不可有失。",
    "敌军逼近{loc}。",
    "{loc}方向，留神。",
    "本座卜见{loc}有变。",
    "{loc}，速去查看。",
    "{loc}已入卦中。",
    "{loc}的动静，逃不过本座的卦。",
    "往{loc}去，依卦行事。",
]
TMAP_COMBOS = [t.format(loc=loc) for loc in TMAP_LOCS for t in TMAP_TPLS]

# ---------- 击杀数播报：按文件名数字取词 ----------
KILL_FLAVORS = ["再接再厉", "继续", "卦象大吉", "敌胆已寒", "命数在我", "痛快", "势不可挡",
                "还有谁", "合乎天机", "收下了"]
CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九",
          10: "十", 11: "十一", 12: "十二", 13: "十三", 14: "十四", 15: "十五",
          16: "十六", 17: "十七", 18: "十八", 19: "十九", 20: "二十", 21: "二十一",
          22: "二十二", 23: "二十三", 24: "二十四", 25: "二十五", 26: "二十六",
          27: "二十七", 28: "二十八", 29: "二十九", 30: "三十"}


def killcount_line(name):
    m = re.search(r"(\d+)$", name)
    if not m:
        return None
    n = int(m.group(1))
    if n in CN_NUM:
        return f"{CN_NUM[n]}杀，{KILL_FLAVORS[n % len(KILL_FLAVORS)]}。"
    return None


# ---------- player 音效精确表 ----------
PLAYER_LINES = {
    "1": "呃！",
    "bhit_helmet-1": "呃，头盔挡下了……",
    "damage1": "呃，挨了一下。",
    "damage2": "嘶，好痛。",
    "damage3": "唔，竟敢伤本座。",
    "death1": "呃啊……命数已尽……",
    "death2": "不……本座不服……",
    "death3": "啊……这一劫……",
    "death4": "呃……卦数……到头了……",
    "death5": "本座……竟倒在这里……",
    "death6": "啊——天机……难违……",
    "death_fem_01": "呃啊……",
    "death_fem_02": "本座……不甘心……",
    "death_fem_03": "啊……卦象……断了……",
    "death_fem_04": "呃……失策了……",
    "death_fem_05": "不……可能……",
    "death_fem_06": "啊……好痛……",
    "death_fem_07": "本座……先走一步……",
    "death_fem_08": "呃……命数尽了……",
    "headshot1": "啊——",
    "headshot2": "呃啊！",
    "pl_burnpain1": "烫！好烫！",
    "pl_burnpain2": "火……烧到本座了！",
    "pl_burnpain3": "烫死了，救命！",
    "pl_drown1": "咕……救……命……",
    "pl_drown2": "水……呛到了……",
    "pl_drown3": "唔……喘不上气……",
    "pl_fallpain1": "呃，摔疼了……",
    "pl_fallpain3": "哎哟……这一跤。",
    "pl_pain5": "嘶……好痛。",
    "pl_pain6": "疼……",
    "pl_pain7": "呃，挨了一下。",
}


def norm(name):
    n = name.lower().replace(".", "_")
    n = re.sub(r"_?\d+wav$", "", n)
    n = re.sub(r"_?\d+$", "", n)
    return n


def main():
    os.makedirs(OUT, exist_ok=True)

    # 1) vo 目标清单 = 解包并集 ∪ 部署残留名
    vo_names = set()
    for fac in FACTIONS:
        d = os.path.join(UNPACK_VO, fac)
        if os.path.isdir(d):
            vo_names.update(x[:-4] for x in os.listdir(d) if x.endswith(".wav"))
        d2 = os.path.join(MIGI_VO, fac)
        if os.path.isdir(d2):
            vo_names.update(x[:-4] for x in os.listdir(d2) if x.endswith(".wav"))

    # 2) player 音效清单
    player_names = set()
    if os.path.isdir(UNPACK_PLAYER):
        player_names.update(
            x[:-4] for x in os.listdir(UNPACK_PLAYER)
            if x.endswith(".wav") and os.path.isfile(os.path.join(UNPACK_PLAYER, x))
        )

    # 3) 族分组
    fam_members = {}
    for name in vo_names:
        fam_members.setdefault(norm(name), []).append(name)
    for v in fam_members.values():
        v.sort()

    # 4) tmap 全局序号
    tmap_names = sorted(n for n in vo_names if norm(n).startswith("tmap"))
    tmap_idx = {n: i for i, n in enumerate(tmap_names)}
    assert len(tmap_names) <= len(TMAP_COMBOS), "tmap 组合不够，扩 LOCS/TPLS"

    # 5) 生成
    written, missing_fam, overflow, skipped = 0, set(), [], 0
    manifest = {}
    for fam, members in sorted(fam_members.items()):
        if fam in SKIP_FAMILIES:
            skipped += len(members)
            continue
        pool = POOLS.get(fam, [])
        if not fam.startswith("tmap") and not pool:
            missing_fam.add(fam)
        if pool and len(members) > len(pool):
            overflow.append((fam, len(members), len(pool)))
        for i, name in enumerate(members):
            if fam.startswith("tmap"):
                line = TMAP_COMBOS[tmap_idx[name]]
            elif fam == "radiobotkillcount":
                line = killcount_line(name) or pool[i % len(pool)]
            else:
                if not pool:
                    continue
                line = pool[i % len(pool)]
            with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
                f.write(line + "\n")
            manifest[name] = line
            written += 1

    # 6) player 音效：SKIP_FAMILIES 覆盖的不写（部署同样跳过 → 恢复原版）
    pain_fallback = POOLS.get("pl_pain", ["呃……"])
    for name in sorted(player_names):
        if norm(name) in SKIP_FAMILIES or name in SKIP_FAMILIES:
            skipped += 1
            continue
        line = PLAYER_LINES.get(name)
        if line is None:
            pool = POOLS.get(norm(name), pain_fallback)
            line = pool[0]
        with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(line + "\n")
        manifest[name] = line
        written += 1

    with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"写入 {written} 个 txt → {OUT}")
    print(f"vo 文件 {len(vo_names)}，player 文件 {len(player_names)}，跳过 {skipped}")
    if missing_fam:
        print(f"缺池的族({len(missing_fam)}): {sorted(missing_fam)}")
    if overflow:
        print(f"池小于变体数(会循环): {overflow}")
    if not missing_fam and not overflow:
        print("全部覆盖，无缺失、无循环。")


if __name__ == "__main__":
    main()
