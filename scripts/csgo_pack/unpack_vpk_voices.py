import vpk
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir, data_dir

# 需要解包的语音路径前缀：
#   sound/player/vo/  —— 探员/阵营角色语音
#   sound/radio/      —— 全局回合播报
#   sound/coop_radio/ —— 合作/战役模式无线电
#   sound/commander/  —— 指挥官/战术语音
#   sound/campaign/   —— 战役模式剧情语音
#   sound/survival/   —— 危险地带/生存模式语音
#   sound/hostage/    —— 人质语音
VOICE_PREFIXES = (
    "sound/player/vo/",
    "sound/radio/",
    "sound/coop_radio/",
    "sound/commander/",
    "sound/campaign/",
    "sound/survival/",
    "sound/hostage/",
)
AUDIO_EXTS = (".wav", ".mp3")


def _is_damage_death_sound(filepath):
    """sound/player/ 根目录下的受击/死亡相关角色音效（damage/death/pl_pain 等）。"""
    if not filepath.startswith("sound/player/"):
        return False
    rel = filepath[len("sound/player/"):]
    if "/" in rel:
        return False  # 子目录（vo/footsteps/...）不在此列
    name = rel.lower()
    return name.startswith(("damage", "death", "pl_pain", "pl_burnpain",
                            "pl_fallpain", "pl_drown", "headshot", "bhit"))

vpk_path = os.path.join(game_dir(), "csgo", "pak01_dir.vpk")
out_dir = os.path.join(data_dir(), "csgo_voices_unpacked")

print("Opening VPK...")
pak = vpk.open(vpk_path)

print(f"Extracting voices to {out_dir}...")
os.makedirs(out_dir, exist_ok=True)

count = 0
skipped = 0
start_time = time.time()

for filepath in pak:
    if not (filepath.startswith(VOICE_PREFIXES) or _is_damage_death_sound(filepath)):
        continue
    if not filepath.endswith(AUDIO_EXTS):
        continue

    # Build output path
    target_path = os.path.join(out_dir, filepath.replace('/', os.sep))
    if os.path.exists(target_path):
        skipped += 1
        continue

    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)

    # Read and save file
    file_obj = pak.get_file(filepath)
    if file_obj:
        with open(target_path, 'wb') as f:
            f.write(file_obj.read())
        count += 1

        if count % 500 == 0:
            print(f"Extracted {count} files...")

elapsed = time.time() - start_time
print(f"Extraction complete! Newly unpacked {count}, skipped {skipped} existing "
      f"files in {elapsed:.1f} seconds.")
