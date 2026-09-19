# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload

OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")
OUT.mkdir(parents=True, exist_ok=True)
idx = audit.CF / "rez" / "rf017.rez"
entries = audit.read_rez_index_mmap(idx)
want = ["PLAYERVIEW/FVIEW_HAND_FH_GR.DTX","PLAYERVIEW/FH_HAND_GR.DTX",
        "PLAYERVIEW/FVIEW_ARM_FH_Undercover_GR.DTX","PLAYERVIEW/FVIEW_HAND_FH_Undercover_GR.DTX",
        "PLAYERVIEW/FVIEW_HAND_FH_BL.DTX","PLAYERVIEW/FH_HAND_BL.DTX"]
for e in entries:
    if e["full_path"].upper() in [w.upper() for w in want]:
        data,row = read_verified_payload(idx,e)
        dec = audit.decode_repo_pixels(data)
        if dec.get("ok"):
            name = Path(e["full_path"]).stem
            p = OUT/(name+".png"); dec["image"].save(p)
            print("OK",e["full_path"],"->",p.name,dec["image"].size,"hdr",row.get("header",{}) and audit.repo_dtx_try_read_header(data))
        else:
            print("FAIL",e["full_path"],dec)
