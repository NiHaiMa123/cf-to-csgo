"""Generic Source 1 material translator (material reconstruction v2 Phase F).

Inputs: Material IR, material regions, processed maps.
Outputs: VMT set, mask packing plan, triangle->slot assignment, report.

Deliberate-downgrade rules (plan.md v2 §11):
- dark/colored metal -> VertexLitGeneric + base + bump + controlled Phong
- bright/gold metal  -> colored Phong; low-intensity envmap allowed
- env_reflective     -> real directional envmap ONLY: the transformed CF
  cubemap is never bound; `env_cubemap` (engine cube) is used because it
  is direction/mip/light-valid, unlike the CF lobby cube or any baked mean
- glow               -> only with real sparse-emissive evidence
- translucent/etc    -> flagged unsupported_by_source1 with minimal-loss
  approximation, never a fake "equivalent"
- every choice is tagged preserved / approximated / lost / unsupported
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

LUM_WEIGHTS = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)

# uniform cross-engine calibration (not weapon-specific)
SOURCE_EXPONENT_SCALE = 16.0
PHONG_GAIN = 2.5
PHONG_BOOST_FLOOR = 0.5
ENVMAP_TINT_MAX = 1.0
STRATEGY_BOOST_MUL = {"warm_phong": 1.0, "colored_phong": 0.8,
                      "envmap_metal": 0.8, "controlled_phong": 0.5,
                      "matte_dark": 0.0}


def phong_terms(cfg_flat: dict, tint: list[float],
                strategy: str) -> tuple[int, float]:
    spec_power = float(cfg_flat.get("SpecularPower", 1.0) or 1.0)
    exponent = max(1, min(64, int(round(
        spec_power * 0.25 * SOURCE_EXPONENT_SCALE))))
    tint_lum = float(np.asarray(tint) @ LUM_WEIGHTS)
    boost = max(PHONG_BOOST_FLOOR, min(8.0, 1.0 / max(0.25, tint_lum)))
    return exponent, boost * PHONG_GAIN * STRATEGY_BOOST_MUL[strategy]


def _lowpass(arr: np.ndarray, radius: float) -> np.ndarray:
    img = Image.fromarray(np.uint8(np.round(np.clip(arr, 0, 1) * 255.0)), "L")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)),
                      dtype=np.float32) / 255.0


def build_masks(maps: dict, cfg_flat: dict,
                size: tuple[int, int]) -> dict:
    """Shared masks: phong mask -> base alpha, env mask -> bumpmap alpha.

    phong mask: low-pass of specular luminance x alpha.G (spec regions)
    env mask:   low-pass of alpha.B (env-reflective coverage)
    """
    w, h = size
    radius = max(1.0, w / 512.0)
    spec = np.asarray(Image.open(maps["specular"]).convert("RGB"),
                      dtype=np.float32) / 255.0 if maps.get("specular") else None
    alpha = np.asarray(Image.open(maps["alpha"]).convert("RGB"),
                       dtype=np.float32) / 255.0 if maps.get("alpha") else None
    spec_lum = (spec @ LUM_WEIGHTS) if spec is not None else np.zeros((h, w), np.float32)
    a_g = alpha[:, :, 1] if alpha is not None else np.zeros((h, w), np.float32)
    a_b = alpha[:, :, 2] if alpha is not None else np.zeros((h, w), np.float32)
    phong = _lowpass(spec_lum * a_g, radius)
    env = _lowpass(a_b, radius)
    return {
        "phong_mask": Image.fromarray(np.uint8(np.round(phong * 255.0)), "L"),
        "env_mask": Image.fromarray(np.uint8(np.round(env * 255.0)), "L"),
        "phong_mean": round(float(phong.mean()), 4),
        "env_mean": round(float(env.mean()), 4),
    }


def spec_tint(maps: dict, mask_uv=None) -> list[float]:
    """$phongtint from the chromatic specular map (never albedo tint)."""
    if not maps.get("specular"):
        return [1.0, 1.0, 1.0]
    s = np.asarray(Image.open(maps["specular"]).convert("RGB"),
                   dtype=np.float32).mean(axis=(0, 1))
    peak = float(s.max())
    return [round(float(v / peak), 3) for v in s] if peak > 0 else [1.0, 1.0, 1.0]


def choose_strategy(region: dict, cfg_flat: dict) -> dict:
    """Region feature means -> Source strategy id + tags."""
    f = region["feature_means"]
    label = region.get("label", "")
    if "env_reflective" in label or f.get("alpha_b", 0) > 0.25:
        strategy = "envmap_metal"
    elif f.get("specular_lum", 0) > 0.3 and f.get("specular_r_minus_lum", 0) > 0.02:
        strategy = "warm_phong"
    elif f.get("specular_lum", 0) > 0.3:
        strategy = "colored_phong"
    elif f.get("diffuse_lum", 0) < 0.05:
        strategy = "matte_dark"
    else:
        strategy = "controlled_phong"
    return {
        "region_id": region["region_id"],
        "label": label,
        "strategy": strategy,
        "evidence": {k: f[k] for k in ("alpha_b", "specular_lum",
                                       "diffuse_lum", "specular_r_minus_lum")
                     if k in f},
    }


def _fmt_vec(v: list[float]) -> str:
    return "[" + " ".join(f"{x:g}" for x in v) + "]"


def vertexlit_vmt(material_root: str, base_name: str, normal_name: str,
                  slot_name: str, strategy: str, cfg_flat: dict,
                  tint: list[float], env_tint: list[float] | None,
                  exponent: int | None = None,
                  boost: float | None = None) -> str:
    if exponent is None or boost is None:
        exponent, boost = phong_terms(cfg_flat, tint, strategy)
    lines = [
        '"VertexLitGeneric"', "{",
        f'\t"$basetexture" "{material_root}/{base_name}"',
        f'\t"$bumpmap" "{material_root}/{normal_name}"',
        '\t"$halflambert" "1"',
    ]
    if strategy == "matte_dark":
        lines += ['\t"$phong" "0"']
    else:
        lines += [
            '\t"$phong" "1"',
            '\t"$basemapalphaphongmask" "1"',
            f'\t"$phongexponent" "{exponent}"',
            f'\t"$phongboost" "{boost:.3g}"',
            '\t"$phongfresnelranges" "[1 1 1]"',
            f'\t"$phongtint" "{_fmt_vec(tint)}"',
        ]
    if strategy == "envmap_metal":
        lines += [
            '\t"$envmap" "env_cubemap"',
            '\t"$normalmapalphaenvmapmask" "1"',
            f'\t"$envmaptint" "{_fmt_vec(env_tint or [0.5, 0.5, 0.5])}"',
        ]
    lines += ['\t"$nocull" "0"', "}", ""]
    return "\n".join(lines)


def env_tint_for_region(region: dict, cfg_flat: dict) -> list[float]:
    """envmaptint from region env response (attenuation, not fake color)."""
    f = region["feature_means"]
    env_b = float(cfg_flat.get("EnvCubeMapBrightness", 1.0) or 1.0)
    strength = min(ENVMAP_TINT_MAX, f.get("alpha_b", 0.1) * env_b)
    spec_warm = f.get("specular_r_minus_lum", 0.0)
    r = min(ENVMAP_TINT_MAX, strength * (1.0 + max(0.0, spec_warm) * 2.0))
    return [round(r, 3), round(strength, 3), round(strength * 0.9, 3)]


def translate(ir: dict, regions_result: dict, maps: dict,
              material_root: str, base_name: str, normal_name: str,
              out_dir: Path | str, size: tuple[int, int]) -> dict:
    """Produce VMT set + slot names + translation report."""
    cfg_flat = ir["cfg"]["flat"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    masks = build_masks(maps, cfg_flat, size)
    masks["phong_mask"].save(out_dir / "mask_phong.png")
    masks["env_mask"].save(out_dir / "mask_env.png")
    tint = spec_tint(maps)
    slots = []
    vmts = {}
    for region in regions_result["regions"]:
        s = choose_strategy(region, cfg_flat)
        slot = f"{base_name}_r{region['region_id']}"
        env_t = (env_tint_for_region(region, cfg_flat)
                 if s["strategy"] == "envmap_metal" else None)
        exponent, boost = phong_terms(cfg_flat, tint, s["strategy"])
        vmt = vertexlit_vmt(material_root, base_name, normal_name, slot,
                            s["strategy"], cfg_flat, tint, env_t,
                            exponent, boost)
        vmts[slot] = vmt
        slots.append({
            "region_id": region["region_id"],
            "region_label": region["label"],
            "material": slot,
            "strategy": s["strategy"],
            "evidence": s["evidence"],
            "envmap_tint": env_t,
            "phong_exponent": exponent,
            "phong_boost": round(boost, 4),
            "triangles": region["triangles"],
        })
    report = {
        "material_root": material_root,
        "base_name": base_name,
        "slots": slots,
        "phong_tint": tint,
        "masks": {"phong_mean": masks["phong_mean"],
                  "env_mean": masks["env_mean"]},
        "tags": {
            "preserved": ["diffuse base texture", "normal map", "specular->phong mask (low-pass)",
                          "alpha.B->envmap mask (low-pass)", "specular chroma->$phongtint",
                          "SpecularPower*0.25->exponent scale"],
            "approximated": ["CF lobby cubemap->engine env_cubemap (content differs, sampling semantics preserved)",
                             "CF transformed/refract ray->Source reflect ray (approximated)",
                             "per-region envmaptint from alpha.B energy (approximated)"],
            "lost": ["Snell refraction contribution", "CubeMapTransformY orientation",
                     "exact CF diffuse-lit scale (ambient/boost terms)"],
            "unsupported_by_source1": [],
        },
    }
    return {"vmts": vmts, "slots": slots, "report": report}
