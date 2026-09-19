# -*- coding: utf-8 -*-
"""Probe: are SND/WEAPON/Mauser/*.WAV plain RIFF or encrypted containers?"""
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/cf_extract")
sys.path.insert(0, "scripts/material_recovery")

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
TARGETS = {
    "SND/WEAPON/MAUSER/MAUSER_SHOOT_1.WAV",
    "SND/WEAPON/MAUSER/MAUSER_SELECT.WAV",
    "SND/WEAPON/MAUSER/MAUSER_CLIPOUT.WAV",
    "SND/WEAPON/MAUSER/MAUSER_CLIPIN.WAV",
    "SND/WEAPON/MAUSER/MAUSER_RELOAD.WAV",
}


def main():
    for idx in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(idx)
        except Exception:
            continue
        for e in entries:
            fp = e["full_path"].replace("\\", "/")
            if fp.upper() not in TARGETS or not is_complete_directory_md5(e.get("md5")):
                continue
            data, _prov = read_verified_payload(idx, e)
            out = Path("work/mauser_libra/sound/raw") / Path(fp).name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(fp, len(data), data[:16].hex(), repr(data[:12]))


if __name__ == "__main__":
    main()
