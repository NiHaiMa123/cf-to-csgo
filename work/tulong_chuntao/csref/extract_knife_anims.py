# -*- coding: utf-8 -*-
"""Extract + Crowbar-decompile shared knife anim mdls for sequence names."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import vpk
except ImportError as exc:
    raise SystemExit("vpk required") from exc

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
from _paths import game_dir, project_dir  # noqa: E402

GAME = Path(game_dir())
OUT = Path(__file__).resolve().parent
CROWBAR = Path(project_dir()) / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe"
STEMS = (
    "models/weapons/v_ct_knife_anim",
    "models/weapons/v_t_knife_anim",
    "models/weapons/v_knife_anim",
)
EXTS = (".mdl", ".vvd", ".dx90.vtx", ".ani", ".dx80.vtx", ".sw.vtx")


def main() -> int:
    pak = vpk.open(str(GAME / "csgo" / "pak01_dir.vpk"))
    src = OUT / "source_vpk"
    for stem in STEMS:
        got = False
        for ext in EXTS:
            rel = stem + ext
            try:
                payload = pak.get_file(rel).read()
            except Exception:
                continue
            dest = src / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
            print(f"[anim] {rel} {len(payload)}B")
            got = True
        if not got:
            print(f"[anim] missing {stem}")
            continue
        mdl = src / (stem + ".mdl")
        dest = OUT / "decompiled_stock" / Path(stem).name
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [str(CROWBAR), str(mdl), str(dest)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        (OUT / f"crowbar_{Path(stem).name}.log").write_text(
            (proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")
        if proc.returncode != 0:
            print("FAIL", stem, (proc.stderr or proc.stdout or "")[:400])
            continue
        for qc in dest.rglob("*.qc"):
            text = qc.read_text(encoding="utf-8", errors="replace")
            print("====", qc)
            for m in re.finditer(r'\$sequence\s+"([^"]+)"[\s\S]*?(?=\$sequence|\Z)', text):
                block = m.group(0)
                name = m.group(1)
                acts = re.findall(r'activity\s+"([^"]+)"', block, re.I)
                evs = re.findall(r'event\s+(\S+)\s+(\S+)\s+"([^"]*)"', block)
                print(f"  seq {name} act={acts} ev={evs[:6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
