# -*- coding: utf-8 -*-
"""E1 follow-up — structural dump of every FX LTB referenced by the idle
group (the LTBModel geometry layers) via CFRezManager --dump-ltb-skin.

Outputs per-file summaries into discovery/ltb_layers.json plus the raw
skin dumps under discovery/ltb_layers/ for later E3 geometry reuse.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
ASSETS = OUT / "assets" / "FX" / "LTB"
DUMPS = OUT / "ltb_layers"
CFREZ = _REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"


def main() -> int:
    DUMPS.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(ASSETS.glob("*.LTB")):
        dest = DUMPS / (p.stem + ".skin.json")
        r = subprocess.run([str(CFREZ), "--dump-ltb-skin", "--input", str(p), "--output", str(dest)],
                           capture_output=True, text=True, timeout=120)
        row = {"ltb": p.name, "dump": dest.name if dest.exists() else None,
               "rc": r.returncode, "stderr": r.stderr.strip()[:300]}
        if dest.exists():
            d = json.loads(dest.read_text(encoding="utf-8"))
            verts = [v for m in d.get("meshes", []) for v in m.get("vertices", [])]
            xs, ys, zs = verts[0::3], verts[1::3], verts[2::3]
            row.update(
                skeleton=[n["name"] for n in d.get("skeleton", [])],
                meshes=[{"name": m.get("name"), "verts": m.get("vertex_count"),
                         "tris": len(m.get("triangles", [])) // 3 if m.get("triangles") else m.get("triangle_count")}
                        for m in d.get("meshes", [])],
                skinned=len(d.get("skinned_meshes", [])),
                bbox=([min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]) if verts else None,
            )
        rows.append(row)
        print(f"[ltb] {p.name}: rc={r.returncode} meshes={row.get('meshes')} skeleton={row.get('skeleton')}")
    doc = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "files": rows}
    (OUT / "ltb_layers.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
