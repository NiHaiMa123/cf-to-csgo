import os
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir

target_base_dir = os.path.join(game_dir(), "migi", "csgo", "addons", "p_GuanXiaoyu_Voice", "sound", "player", "vo")

for root, _, files in os.walk(target_base_dir):
    for f in files:
        if f.endswith('.wav'):
            path = os.path.join(root, f)
            temp_path = path + ".tmp.wav"
            
            # Convert to 44100 Hz, Mono, 16-bit PCM
            cmd = ['ffmpeg', '-y', '-i', path, '-ar', '44100', '-ac', '1', '-c:a', 'pcm_s16le', temp_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Replace original
            os.replace(temp_path, path)
            print(f"Converted {path}")
