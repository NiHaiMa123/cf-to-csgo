import os
import shutil
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir

addons_dir = os.path.join(game_dir(), "migi", "csgo", "addons", "p_GuanXiaoyu_Voice", "sound", "player", "vo")
jungle_fem_dir = os.path.join(addons_dir, "jungle_fem")
factions = ["leet", "anarchist", "balkan", "balkan_epic", "pirate", "professional", "separatist", "phoenix"]

mappings = {
    "plantingbomb01.wav": "aff1_i_plant_bomb_01.wav",
    "plantingbomb02.wav": "aff1_i_plant_bomb_02.wav",
    "plantingbomb03.wav": "aff1_i_plant_bomb_03.wav",
    "plantingbomb04.wav": "aff1_i_plant_bomb_04.wav",
    
    "goingtoplantbomb01.wav": "aff1_i_plant_bomb_03.wav",
    "goingtoplantbomb02.wav": "aff1_i_plant_bomb_04.wav",
    "goingtoplantbomb03.wav": "aff1_i_plant_bomb_05.wav",
    
    "goingtoplantbomba01.wav": "aff1_omw_to_plant_b_01.wav",
    "goingtoplantbomba02.wav": "aff1_omw_to_plant_b_02.wav",
    "goingtoplantbomba03.wav": "aff1_omw_to_plant_b_03.wav",
    
    "goingtoplantbombb01.wav": "aff1_omw_to_plant_a_01.wav",
    "goingtoplantbombb02.wav": "aff1_omw_to_plant_a_02.wav",
    "goingtoplantbombb03.wav": "aff1_omw_to_plant_a_03.wav",
}

for target, src in mappings.items():
    src_path = os.path.join(jungle_fem_dir, src)
    if os.path.exists(src_path):
        for faction in factions:
            faction_dir = os.path.join(addons_dir, faction)
            os.makedirs(faction_dir, exist_ok=True)
            shutil.copy2(src_path, os.path.join(faction_dir, target))

# Map global announcer "bomb planted"
radio_dir = os.path.join(game_dir(), "migi", "csgo", "addons", "p_GuanXiaoyu_Voice", "sound", "radio")
os.makedirs(radio_dir, exist_ok=True)
bomb_planted_src = os.path.join(jungle_fem_dir, "aff1_bomb_planted_01.wav")
if os.path.exists(bomb_planted_src):
    shutil.copy2(bomb_planted_src, os.path.join(radio_dir, "bombpl.wav"))

print("Planting bomb voices fixed!")
