# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload
import io
from PIL import Image

OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")
idx = audit.CF/"rez"/"rf017.rez"
entries = audit.read_rez_index_mmap(idx)
want = {p.upper() for p in [
 "PLAYERVIEW/PV-M4A1_S_Transformers.DTX","SpecularMap/M4A1_S_Transformers_S.TGA",
 "AlphaMap/M4A1_S_Transformers_Alpha.TGA","NormalMap/M4A1_S_Transformers_N.TGA",
 "WeaponShader/M4A1_S_Transformers.CFG"]}
for e in entries:
    if e["full_path"].upper() in want:
        data,row = read_verified_payload(idx,e)
        name = Path(e["full_path"]).name; ext = Path(name).suffix.upper()
        if ext==".DTX":
            dec = audit.decode_repo_pixels(data)
            dest = OUT/(Path(name).stem+".png"); dec["image"].save(dest)
            print("DTX",name,dec["image"].size)
        elif ext==".TGA":
            im = Image.open(io.BytesIO(data)); dest=OUT/(Path(name).stem+".png"); im.save(dest)
            print("TGA",name,im.size)
        else:
            (OUT/name).write_bytes(data); print("CFG",name,len(data))
