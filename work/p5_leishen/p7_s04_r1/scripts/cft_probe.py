# -*- coding: utf-8 -*-
import sys, re
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload
CF = audit.CF
idx = CF/"rez"/"RF100.REZ"
entries = audit.read_rez_index_mmap(idx)
out = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\cft")
out.mkdir(exist_ok=True, parents=True)
for e in entries:
    if e["full_path"] in ("Table/Character.CFT","Table/ModelBute.CFT","Table/CharacterSkinRenewal.CFT"):
        data,row = read_verified_payload(idx,e)
        (out/Path(e["full_path"]).name).write_bytes(data)
        print(e["full_path"], len(data), data[:32].hex())
        s = re.findall(rb"[ -~]{4,}", data)
        fox = [x for x in s if b"ox" in x.lower() or b"Arm" in x or b"FVIEW" in x]
        print("  strings:", len(s), "foxish:", [x[:80] for x in fox[:20]])
