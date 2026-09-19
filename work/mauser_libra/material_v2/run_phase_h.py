# -*- coding: utf-8 -*-
"""Phase H driver: Source-like A/B preview for the reference weapon.

Same rasterized frame, camera, lights for both sides:
  left  = CF reference formula (cfrr.render_full)
  right = Source-like approximation of the emitted VMT slots
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import cf_reference_renderer as cfrr  # noqa: E402
import material_ir  # noqa: E402
import source_like_preview as slp  # noqa: E402

WORK = _REPO / "work" / "mauser_libra"
MV2 = WORK / "material_v2"
DECODE = WORK / "decode"
MAPS = DECODE / "maps"
SKIN = DECODE / "cf_skin_m1896_libra.json"
IR_PATH = MV2 / "ir" / "cf_mauser_libra.material_ir.json"
SV2 = MV2 / "source_v2"
PREV = MV2 / "preview_source"

SIZE = 512
FOV = 45.0
LUM = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)


def load_inputs():
    ir = material_ir.load_ir(IR_PATH)
    params = cfrr.params_from_cfg_flat(ir["cfg"]["flat"])
    meshes = cfrr.load_skin_meshes(SKIN, skip_prefixes=("fview",))
    maps = {
        "diffuse": cfrr.load_rgb(DECODE / "PV-M1896_Libra.png"),
        "normal": cfrr.load_rgb(MAPS / "M1896_Libra_N.TGA"),
        "specular": cfrr.load_rgb(MAPS / "M1896_Libra_S.TGA"),
        "alpha": cfrr.load_rgb(MAPS / "M1896_Libra_alpha.TGA"),
        "cubemap": cfrr.dds_faces(MAPS / "LobbyCube.DDS"),
    }
    return ir, params, meshes, maps


def gun_center(meshes):
    for m in meshes:
        if "mauser" in m["name"].lower() or "libra" in m["name"].lower():
            v = m["verts"]
            lo, hi = v.min(0), v.max(0)
            return (lo + hi) / 2, float((hi - lo).max())
    v = np.concatenate([m["verts"] for m in meshes])
    lo, hi = v.min(0), v.max(0)
    return (lo + hi) / 2, float((hi - lo).max())


def main() -> int:
    PREV.mkdir(parents=True, exist_ok=True)
    ir, params, meshes, maps = load_inputs()
    report = json.loads((SV2 / "translation_report.json").read_text("utf-8"))
    assigns = json.loads((MV2 / "g_material_assignments.json")
                         .read_text("utf-8"))
    tri_slot = slp.build_tri_slot(meshes, assigns, "cf_mauser_libra")
    slot_params = slp.slot_params_from_report(report, ir["cfg"]["flat"])
    masks = {
        "phong": np.stack([np.asarray(Image.open(SV2 / "mask_phong.png"),
                                      dtype=np.float32) / 255.0] * 3, -1),
        "env": np.stack([np.asarray(Image.open(SV2 / "mask_env.png"),
                                    dtype=np.float32) / 255.0] * 3, -1),
    }
    center, extent = gun_center(meshes)
    dist = extent * 1.6
    scenes = {
        "neutral":      {"eye_off": (-0.6, -1.0, 0.45), "light": (-0.3, -0.5, 0.8)},
        "front_lit":    {"eye_off": (-0.6, -1.0, 0.45), "light": (-0.2, -0.9, 0.4)},
        "side_lit":     {"eye_off": (-0.6, -1.0, 0.45), "light": (0.95, -0.2, 0.25)},
        "back_dark":    {"eye_off": (-0.6, -1.0, 0.45), "light": (0.2, 0.9, 0.4)},
        "rotated_view": {"eye_off": (0.9, -0.7, 0.5), "light": (-0.3, -0.5, 0.8)},
    }
    sheet_rows = []
    metrics = {}
    for name, sc in scenes.items():
        eye = center + np.asarray(sc["eye_off"], np.float32) * dist
        light = np.asarray(sc["light"], np.float32)
        view = cfrr.look_at(eye, center)
        frame = cfrr.rasterize(meshes, view, FOV, SIZE)
        cf_img, _ = cfrr.shade(frame, meshes, maps, params, view,
                               light, SIZE, eye)
        cf_img = np.clip(cf_img, 0.0, 1.0)
        sl_img, comps = slp.render_source_like(
            frame, meshes, maps, tri_slot, slot_params, masks,
            light, eye, SIZE, view)
        hit = frame["tri"] >= 0
        cf_hit = cf_img[hit]
        sl_hit = sl_img[hit]
        cf_lum = cf_hit @ LUM
        sl_lum = sl_hit @ LUM
        m = {
            "mean_abs_delta": round(float(np.abs(cf_hit - sl_hit).mean()), 5),
            "cf_lum_mean": round(float(cf_lum.mean()), 5),
            "sl_lum_mean": round(float(sl_lum.mean()), 5),
            "dark_retention": round(
                float((sl_lum[cf_lum < np.percentile(cf_lum, 25)]).mean()
                      / max(cf_lum[cf_lum < np.percentile(cf_lum, 25)].mean(), 1e-6)),
                4) if hit.any() else 0.0,
            "phong_hit_mean": round(float(comps["phong"][hit].mean()), 5),
            "env_hit_mean": round(float(comps["env"][hit].mean()), 5),
        }
        metrics[name] = m
        row = np.concatenate([cf_img, np.ones((SIZE, 8, 3), np.float32),
                              sl_img], axis=1)
        sheet_rows.append(row)
        cfrr.save_png(cf_img, PREV / f"{name}_cf.png")
        cfrr.save_png(sl_img, PREV / f"{name}_source.png")
    sheet = np.concatenate(sheet_rows, axis=0)
    cfrr.save_png(sheet, PREV / "reference_vs_source_sheet.png")

    # view dependence: how much does the render change between views
    vd = {}
    for side in ("cf", "source"):
        a = np.asarray(Image.open(PREV / f"neutral_{side}.png"),
                       dtype=np.float32) / 255.0
        b = np.asarray(Image.open(PREV / f"rotated_view_{side}.png"),
                       dtype=np.float32) / 255.0
        vd[side] = round(float(np.abs(a - b).mean()), 5)
    metrics["view_dependence_neutral_vs_rotated"] = vd

    out = {
        "limitation": ("Blender preview is diagnostic only. It is not "
                       "Source 1 / CS:GO runtime ground truth."),
        "renderer": "software Source-like approximation "
                    "(source_like_preview.py), same frame/camera/lights "
                    "as CF reference",
        "scenes": {k: {"eye_off": v["eye_off"], "light": v["light"]}
                   for k, v in scenes.items()},
        "metrics": metrics,
        "tags": report["tags"],
        "slot_params": slot_params,
    }
    (MV2 / "reports" / "source_translation_report.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False, default=str),
        encoding="utf-8")
    print("Phase H sheet ->", PREV / "reference_vs_source_sheet.png")
    for k, m in metrics.items():
        if isinstance(m, dict) and "mean_abs_delta" in m:
            print(f"  {k}: delta={m['mean_abs_delta']} "
                  f"lum cf={m['cf_lum_mean']} sl={m['sl_lum_mean']} "
                  f"dark_ret={m['dark_retention']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
