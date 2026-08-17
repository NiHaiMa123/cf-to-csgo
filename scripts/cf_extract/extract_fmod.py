import os
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import cf_dir, data_dir, vgmstream as vgmstream_path

vgmstream = vgmstream_path()
banks = [
    os.path.join(cf_dir(), "rez", "FMODStudio", "Voice", "Voice_CN.bank"),
    os.path.join(cf_dir(), "rez", "FMODStudio", "Voice", "AnnouncerPack_CN.bank")
]
out_dir_base = os.path.join(data_dir(), "FMOD_Voices")

for bank in banks:
    bank_name = os.path.splitext(os.path.basename(bank))[0]
    out_dir = os.path.join(out_dir_base, bank_name)
    os.makedirs(out_dir, exist_ok=True)
    out_pattern = os.path.join(out_dir, "?s_?n.wav")
    print(f"Extracting {bank_name} to {out_dir}...")
    # Run vgmstream to extract all streams (-S 0)
    # This might take a while since Voice_CN has 50k streams.
    subprocess.run([vgmstream, "-S", "0", "-o", out_pattern, bank])

print("Finished extracting FMOD banks!")
