# -*- coding: utf-8 -*-
"""Phase D driver: material region analysis for the reference weapon."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import cf_reference_renderer as cfrr  # noqa: E402
import material_regions  # noqa: E402

WORK = _REPO / "work" / "cop357_snowfox"
MV2 = WORK / "material_v2"
DECODE = WORK / "decode"
MAPS = DECODE / "maps"
SEG = MV2 / "segmentation"

K = 6
MIN_ISLAND = 6
MAX_SLOTS = 8


def main() -> int:
    SEG.mkdir(parents=True, exist_ok=True)
    meshes = cfrr.load_skin_meshes(DECODE / "cf_skin_cop357_winter.json",
                                   skip_prefixes=("fview",))
    maps = {
        "diffuse": cfrr.load_rgb(DECODE / "PV-Cop357_IronBeast2_Winter.png"),
        "normal": cfrr.load_rgb(MAPS / "Cop357_IronBeast2_Winter_N.PNG"),
        "specular": cfrr.load_rgb(MAPS / "Cop357_IronBeast2_Winter_S.PNG"),
        "alpha": cfrr.load_rgb(MAPS / "Cop357_IronBeast2_Winter_A.PNG"),
    }
    result = material_regions.analyze(meshes, maps, k=K, min_island=MIN_ISLAND)
    names = [r["label"] for r in result["regions"]]
    material_regions.region_preview(
        result["rows"], result["labels"], names, maps["diffuse"],
        SEG / "region_preview.png")
    out = {
        "k": K,
        "min_island": MIN_ISLAND,
        "regions": result["regions"],
        "triangle_materials": result["triangle_materials"],
        "feature_names": result["feature_names"],
    }
    (SEG / "triangle_materials.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    # D gate
    problems = []
    n_regions = len(result["regions"])
    if n_regions > MAX_SLOTS:
        problems.append(f"{n_regions} regions exceeds slot cap {MAX_SLOTS}")
    for r in result["regions"]:
        if r["triangles"] < MIN_ISLAND:
            problems.append(f"region {r['region_id']} has {r['triangles']} tris")
        if not r["feature_means"]:
            problems.append(f"region {r['region_id']} has no feature evidence")
    total = sum(r["triangles"] for r in result["regions"])
    gate = {"passed": not problems, "problems": problems,
            "regions": n_regions, "triangles_classified": total}
    (SEG / "d_gate.json").write_text(
        json.dumps(gate, indent=1, ensure_ascii=False), encoding="utf-8")
    print("D gate:", "PASS" if gate["passed"] else "FAIL", problems)
    for r in result["regions"]:
        print(f"  region {r['region_id']} {r['label']}: {r['triangles']} tris "
              f"pieces={list(r['pieces'])[:3]}")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
