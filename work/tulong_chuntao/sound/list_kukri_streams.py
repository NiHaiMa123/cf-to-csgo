# -*- coding: utf-8 -*-
"""List FMOD Weapon.bank streams matching Kukri."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

VGM = Path(_paths.vgmstream())
BANK = Path(_paths.cf_dir()) / "rez" / "FMODStudio" / "Weapon" / "Weapon.bank"
OUT = Path(__file__).resolve().parent / "kukri_streams.txt"


def main() -> int:
    proc = subprocess.run(
        [str(VGM), "-S", "0", str(BANK)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    # vgmstream -S 0 may just play first. Use -I or dump subsong count.
    # Try listing via -m metadata for many subsongs is slow; use a python FSB walk.
    # Fallback: call vgmstream with increasing -s until fail, only print Kukri names.
    hits = []
    # probe count
    info = subprocess.run(
        [str(VGM), "-m", "-s", "1", str(BANK)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    text = (info.stdout or "") + (info.stderr or "")
    print(text[:800])
    n = 0
    for line in text.splitlines():
        if "stream count" in line.lower() or "subsong" in line.lower():
            print("META", line)
            for tok in line.replace(",", " ").split():
                if tok.isdigit():
                    n = max(n, int(tok))
    if n <= 1:
        # brute: many banks report count in "sample count"
        n = 800
    print("probing up to", n)
    for i in range(1, n + 1):
        p = subprocess.run(
            [str(VGM), "-m", "-s", str(i), str(BANK)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        blob = (p.stdout or "") + (p.stderr or "")
        if p.returncode != 0 and "subsong" in blob.lower() and "failed" in blob.lower():
            break
        name = ""
        for line in blob.splitlines():
            if "stream name" in line.lower() or "sample name" in line.lower() or line.strip().startswith("stream name"):
                name = line.split(":", 1)[-1].strip()
        if not name:
            # vgmstream often prints: "stream name: Foo"
            for line in blob.splitlines():
                if "name:" in line.lower() and "bank" not in line.lower():
                    name = line.split(":", 1)[-1].strip()
                    break
        if "KUKRI" in name.upper() or "KUKRI" in blob.upper():
            hits.append((i, name, blob.splitlines()[0] if blob else ""))
            print(f"HIT {i} {name}")
    OUT.write_text("\n".join(f"{i}\t{name}" for i, name, _ in hits), encoding="utf-8")
    print("hits", len(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
