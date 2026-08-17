import os
import glob
import re
import shutil
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import data_dir

source_dir = os.path.join(data_dir(), "FMOD_Voices", "Voice_CN")
dest_dir = os.path.join(data_dir(), "FMOD_Voices", "Voice_CN", "Categorized")

os.makedirs(dest_dir, exist_ok=True)

files = glob.glob(os.path.join(source_dir, "*.wav"))
char_pattern = re.compile(r'_(BL|GR|GHOST|SP)_([A-Za-z0-9]+)')

moved = 0
for f in files:
    name = os.path.basename(f)
    match = char_pattern.search(name)
    
    if match:
        # E.g. BL_C
        code = f"{match.group(1)}_{match.group(2)}"
        target_folder = os.path.join(dest_dir, code)
    else:
        # General sounds
        target_folder = os.path.join(dest_dir, "General")
        
    os.makedirs(target_folder, exist_ok=True)
    
    try:
        shutil.move(f, os.path.join(target_folder, name))
        moved += 1
    except Exception as e:
        print(f"Error moving {name}: {e}")

print(f"Successfully categorized {moved} files into {dest_dir}")
