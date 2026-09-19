# -*- coding: utf-8 -*-
import sys, re, lzma
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload
CF = audit.CF
idx = CF/"rez"/"rf192.rez"
entries = audit.read_rez_index_mmap(idx)
out = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\cft")
for e in entries:
    if e["full_path"].lower() in ("character/foxhowl_renewal_gr.bin","character/foxhowl_renewal_bl.bin","character/new_foxhowl_gr.bin"):
        data,row = read_verified_payload(idx,e)
        print("##",e["full_path"],len(data),data[:16].hex())
        for dec_name, blob in [("raw",data)]:
            try:
                d2 = lzma.decompress(blob, format=lzma.FORMAT_ALONE); dec_name="lzma"
            except Exception: d2=blob
            t = bytes(b^0x10 for b in d2)
            for cand,nm in [(d2,"plain"),(t,"xor10")]:
                s=cand.decode("latin-1",errors="replace")
                if "Arm" in s or "FVIEW" in s or ".ltb" in s.lower() or ".dtx" in s.lower():
                    print("  format:",nm)
                    strs=re.findall(r"[ -~]{4,}", s)
                    for x in strs[:80]: print("   ",x[:120])
                    break
            else:
                print("  no readable strings; first64:",d2[:64].hex())
