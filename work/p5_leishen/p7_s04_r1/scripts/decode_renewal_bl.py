# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload
OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")
idx = audit.CF/"rez2"/"RF017.REZ"
entries = audit.read_rez_index_mmap(idx)
want = {p.upper() for p in [
 "PLAYERVIEW/FVIEW_HAND_Foxhowl_Renewal_BL.DTX","PLAYERVIEW/FVIEW_ARM_Foxhowl_Renewal_BL.DTX",
 "SpecularMap/FVIEW_HAND_Foxhowl_Renewal_BL_S.PNG","SpecularMap/FVIEW_ARM_Foxhowl_Renewal_BL_S.PNG",
 "NormalMap/FVIEW_HAND_Foxhowl_Renewal_BL_N.PNG","NormalMap/FVIEW_ARM_Foxhowl_Renewal_BL_N.PNG",
 "AlphaMap/FVIEW_HAND_Foxhowl_Renewal_BL_Alpha.PNG","AlphaMap/FVIEW_ARM_Foxhowl_Renewal_BL_Alpha.PNG",
 "AdvancedShader/Arm_Foxhowl_Renewal_BL_Piece0.CFG","AdvancedShader/Arm_Foxhowl_Renewal_BL_Piece1.CFG"]}
for e in entries:
    if e["full_path"].upper() in want:
        data,row = read_verified_payload(idx,e)
        name = Path(e["full_path"]).name; ext = Path(name).suffix.upper()
        if ext==".DTX":
            dec = audit.decode_repo_pixels(data)
            (OUT/(Path(name).stem+".png")).parent.mkdir(exist_ok=True,parents=True)
            dec["image"].save(OUT/(Path(name).stem+".png")); print("DTX",name,dec["image"].size)
        else:
            (OUT/name).write_bytes(data); print(ext,name,len(data),"B")
