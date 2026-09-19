# -*- coding: utf-8 -*-
"""Export gun meshes to OBJ with per-triangle slot materials (Phase H review)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import cf_reference_renderer as cfrr  # noqa: E402

WORK = _REPO / "work" / "cop357_snowfox"
MV2 = WORK / "material_v2"
SKIN = WORK / "decode" / "cf_skin_cop357_dominator.json"
OUT = MV2 / "preview_source" / "gun_slots.obj"


def main() -> int:
    meshes = cfrr.load_skin_meshes(SKIN, skip_prefixes=("fview",))
    assigns = json.loads((MV2 / "g_material_assignments.json")
                         .read_text("utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    v_off = t_off = 0
    with OUT.open("w", encoding="utf-8") as f:
        f.write("# mauser libra gun, per-tri material slots\n")
        for mesh in meshes:
            f.write(f"o {mesh['name']}\n")
            # obj vt: raw uvs (renderer flips v internally; blender does too)
            for v in mesh["verts"]:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            # raw uvs: undo the renderer flip -> vt = (u, 1-v_flipped)
            for uv in mesh["uvs"]:
                f.write(f"vt {uv[0]:.6f} {1.0 - uv[1]:.6f}\n")
            names = assigns.get(mesh["name"], {})
            for t in range(len(mesh["tris"])):
                slot = names.get(str(t), "cf_cop357_snowfox")
                f.write(f"usemtl {slot}\n")
                a, b, c = mesh["tris"][t]
                f.write(f"f {a + v_off + 1}/{a + t_off + 1} "
                        f"{b + v_off + 1}/{b + t_off + 1} "
                        f"{c + v_off + 1}/{c + t_off + 1}\n")
            v_off += len(mesh["verts"])
            t_off += len(mesh["uvs"])
    print("wrote", OUT, f"verts={v_off} uvs={t_off}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
