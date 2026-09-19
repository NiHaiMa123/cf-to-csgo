# -*- coding: utf-8 -*-
"""Phase E driver: texture processing v2 for the reference weapon."""
from __future__ import annotations

import json
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import texture_upscale  # noqa: E402

WORK = _REPO / "work" / "mauser_libra"
MV2 = WORK / "material_v2"
DECODE = WORK / "decode"
MAPS = DECODE / "maps"
UP = MV2 / "upscale"
UP4 = WORK / "texture" / "up" / "4x_PV-M1896_Libra.png"  # existing AI 4x cache

SIZE = (2048, 2048)
COMFY = "http://127.0.0.1:8188"


def e1_diffuse() -> dict:
    """Diffuse resize. AI upscale REJECTED for this asset: the cached 4x
    ComfyUI output over-amplified the low-contrast engraved pattern into
    a loud scale-like texture (local-contrast drift vs original). Use
    non-generative LANCZOS instead — semantics must be preserved."""
    original = DECODE / "PV-M1896_Libra.png"
    keep = UP / "diffuse_original.png"
    keep.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(original, keep)
    out = UP / "diffuse_2048.png"
    meta = texture_upscale.resize_rgb(original, out, SIZE)
    rep = {"original_preserved": str(keep), "final": str(out),
           "ai_upscale_used": False,
           "ai_rejected_reason": ("cached AI 4x over-enhanced engraved "
                                  "pattern contrast (fish-scale artifact); "
                                  "non-generative resize preserves semantics"),
           "ai_cache_checked": str(UP4),
           "coverage": texture_upscale.coverage_report(original, out)}
    rep.update(meta)
    if UP4.is_file():
        rep["ai_cache_coverage"] = texture_upscale.coverage_report(
            original, UP4)
    return rep


def e2_normal() -> dict:
    src = MAPS / "M1896_Libra_N.TGA"
    out = UP / "normal_2048.png"
    meta = texture_upscale.resize_normal(src, out, SIZE)
    meta["coverage"] = texture_upscale.coverage_report(src, out)
    return meta


def e3_maps() -> dict:
    res = {}
    for name, src in (("specular", MAPS / "M1896_Libra_S.TGA"),
                      ("alpha", MAPS / "M1896_Libra_alpha.TGA")):
        out = UP / f"{name}_2048.png"
        meta = texture_upscale.resize_mask(src, out, SIZE)
        meta["coverage"] = texture_upscale.coverage_report(src, out)
        res[name] = meta
    return res


def main() -> int:
    report = {"size": list(SIZE), "e1_diffuse": e1_diffuse(),
              "e2_normal": e2_normal(), "e3": e3_maps(),
              "rules": {
                  "diffuse": "AI upscale ok; original preserved; atlas/UV unchanged",
                  "normal": "decode->resize->renormalize->encode; no generative AI",
                  "spec/alpha/masks": "resize only; histogram+coverage compared"}}
    (UP / "upscale_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in report["e3"].items():
        b, a = v["coverage"]["before"], v["coverage"]["after"]
        drift = abs(a["lum_mean"] - b["lum_mean"])
        print(f"E3 {k}: lum {b['lum_mean']} -> {a['lum_mean']} drift={drift:.4f}")
    d = report["e1_diffuse"]["coverage"]
    print("E1 diffuse lum:", d["before"]["lum_mean"], "->", d["after"]["lum_mean"])
    print("Phase E outputs ->", UP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
