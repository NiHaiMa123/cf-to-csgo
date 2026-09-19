# -*- coding: utf-8 -*-
import sys, re
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
from n02_butes_config_triage import _decode_ltc_c_sharp

KEY = bytes.fromhex("5483B2E1103F6E9DCCFB2A5988B7E615")
BUTES = Path(r"D:\Program Files\CF(2)\rez\Butes")
outdir = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\butes")
outdir.mkdir(parents=True, exist_ok=True)
ok=0
for f in sorted(BUTES.glob("bf*.ltc")):
    raw = f.read_bytes()
    un = bytes(b ^ KEY[i % 16] for i, b in enumerate(raw))
    try:
        dec = _decode_ltc_c_sharp(un)
    except Exception as e:
        print(f.name, "fail", e); continue
    ok+=1
    (outdir/(f.stem+".txt")).write_bytes(dec)
    txt = dec.decode("latin-1", errors="replace")
    hits = [k for k in ("FoxHowl","foxhowl","FOXHOWL","ArmModel","FVIEW_HAND","Arm_","Renewal") if k in txt]
    print(f.name, len(dec), hits if hits else "")
print("decoded:",ok)
