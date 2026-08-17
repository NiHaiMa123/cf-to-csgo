import os, wave, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import cf_dir, data_dir

src_dir = os.path.join(cf_dir(), "rez", "Snd2")
dst_dir = os.path.join(data_dir(), "Snd2_Cleaned")

def clean_wav(src_path, dst_path):
    try:
        with wave.open(src_path, 'rb') as w_in:
            params = w_in.getparams()
            data = w_in.readframes(params.nframes)
        with wave.open(dst_path, 'wb') as w_out:
            w_out.setparams(params)
            w_out.writeframes(data)
        return True
    except Exception as e:
        print(f"Failed to process {src_path}: {e}")
        return False

count = 0
for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.lower().endswith('.wav'):
            src_path = os.path.join(root, f)
            rel_path = os.path.relpath(src_path, src_dir)
            dst_path = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            if clean_wav(src_path, dst_path):
                count += 1
                if count % 100 == 0:
                    print(f"Cleaned {count} files...")
print(f"Done! Total cleaned: {count} files.")
