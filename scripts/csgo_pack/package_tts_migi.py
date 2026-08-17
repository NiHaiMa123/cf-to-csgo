import os
import shutil
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import data_dir, game_dir

tts_dir = os.path.join(data_dir(), "rvc", "tts")
base_migi = os.path.join(game_dir(), "migi", "csgo", "addons", "p_GuanXiaoyu_Voice", "sound", "player", "vo")
factions = ["anarchist", "balkan", "balkan_epic", "leet", "phoenix", "pirate", "professional", "separatist"]

# 1. Process all TTS files with volume boost and standard formatting
processed_dir = os.path.join(data_dir(), "rvc", "tts_processed")
os.makedirs(processed_dir, exist_ok=True)

tts_files = [f for f in os.listdir(tts_dir) if f.endswith('.wav')]
print(f"Found {len(tts_files)} TTS files. Boosting volume and normalizing format...")

for f in tts_files:
    src_path = os.path.join(tts_dir, f)
    dst_path = os.path.join(processed_dir, f)
    
    # +10dB volume boost, 44100Hz, Mono, 16-bit PCM
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-filter:a", "volume=10dB",
        "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le",
        dst_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Identify a generic fallback file from the processed files (e.g. radio_letsgo01.wav)
fallback_file = os.path.join(processed_dir, "radio_letsgo01.wav")
if not os.path.exists(fallback_file):
    # Just pick any processed file if letsgo doesn't exist
    fallback_file = os.path.join(processed_dir, tts_files[0])

# 2. Distribute to the 8 MIGI T-factions
print("Distributing files to MIGI factions and applying fallback for missing maps...")
for faction in factions:
    faction_dir = os.path.join(base_migi, faction)
    if not os.path.exists(faction_dir):
        continue
        
    # Overwrite the 392 explicitly generated TTS files
    for f in tts_files:
        processed_path = os.path.join(processed_dir, f)
        target_path = os.path.join(faction_dir, f)
        shutil.copy2(processed_path, target_path)
        
    # Scan the directory to see if there are any other existing .wav files 
    # (these would be the original jungle_fem padded files like tmap_de_inferno)
    # Overwrite them with the fallback so they don't play original audio or old CF audio!
    all_faction_files = os.listdir(faction_dir)
    for f in all_faction_files:
        if f.endswith('.wav') and f not in tts_files:
            target_path = os.path.join(faction_dir, f)
            shutil.copy2(fallback_file, target_path)

print("Packaging complete! MIGI folders are now fully populated with boosted AI TTS lines.")
