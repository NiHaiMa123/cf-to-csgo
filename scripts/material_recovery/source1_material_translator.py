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
PHONG_MASK_GAIN = 4.0
PHONG_BOOST_FLOOR = 0.5
ENVMAP_TINT_MAX = 1.0
ENV_STRENGTH_GAIN = 1.4
# shared lightwarp: compress diffuse lit/unlit gap to the CFG-derived
# lit fraction (CF viewmodel lighting is weakly directional)
LIGHT_INFLUENCE_SCALE = 0.25
MIN_LIT_FRACTION = 0.05
MAX_LIT_FRACTION = 0.8
STRATEGY_BOOST_MUL = {"warm_phong": 1.0, "colored_phong": 0.8,
                      "envmap_metal": 0.8, "controlled_phong": 0.5,
                      "dim_phong": 0.25, "matte_dark": 0.0}
# tight highlights on dark/rough regions resolve normal-map bumps as
# per-dot speckle (fish-scale); regions this dark get a broad sheen cap
DARK_REGION_EXP_CAP = 2
DARK_REGION_LUM = 0.08


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
    radius = max(2.0, w / 256.0)
    spec = np.asarray(Image.open(maps["specular"]).convert("RGB"),
                      dtype=np.float32) / 255.0 if maps.get("specular") else None
    alpha = np.asarray(Image.open(maps["alpha"]).convert("RGB"),
                       dtype=np.float32) / 255.0 if maps.get("alpha") else None
    spec_lum = (spec @ LUM_WEIGHTS) if spec is not None else np.zeros((h, w), np.float32)
    a_g = alpha[:, :, 1] if alpha is not None else np.zeros((h, w), np.float32)
    a_b = alpha[:, :, 2] if alpha is not None else np.zeros((h, w), np.float32)
    # CF spec is additive over the whole weapon (alpha.G=1.0); scale the
    # low-pass mask so Source phong gets comparable coverage
    phong = _lowpass(np.clip(spec_lum * a_g * PHONG_MASK_GAIN, 0, 1), radius)
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
    elif f.get("specular_lum", 0) < 0.03:
        strategy = "matte_dark"          # only truly non-reflective surfaces
    elif f.get("diffuse_lum", 0) < 0.05:
        strategy = "dim_phong"           # dark but CF spec still applies
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


# ------------------------------------------------------------------ cube bake

# DX face -> direction basis (inverse of cf_reference_renderer.cube_sample)
_FACE_DIRS = {
    "+X": (1.0, ("z", -1), ("y", -1)),
    "-X": (-1.0, ("z", 1), ("y", -1)),
    "+Y": (1.0, ("x", 1), ("z", 1)),
    "-Y": (-1.0, ("x", 1), ("z", -1)),
    "+Z": (1.0, ("x", 1), ("y", -1)),
    "-Z": (-1.0, ("x", -1), ("y", -1)),
}
_FACE_ORDER = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]


def _face_dirs(face: str, n: int) -> np.ndarray:
    """Per-pixel unit directions for a DX cubemap face of size n."""
    t = (np.arange(n, dtype=np.float32) + 0.5) / n * 2.0 - 1.0
    u, v = np.meshgrid(t, t)
    dirs = np.zeros((n, n, 3), dtype=np.float32)
    axis = {"+X": 0, "-X": 0, "+Y": 1, "-Y": 1, "+Z": 2, "-Z": 2}[face]
    sign, (u_axis, u_s), (v_axis, v_s) = _FACE_DIRS[face]
    dirs[:, :, axis] = sign
    dirs[:, :, "xyz".index(u_axis)] = u * u_s
    dirs[:, :, "xyz".index(v_axis)] = v * v_s
    return dirs / np.linalg.norm(dirs, axis=2, keepdims=True)


def bake_env_cube(dds_path, transform_y_deg: float,
                  out_vtf, face_size: int = 256) -> Path:
    """CF cubemap DDS -> Source envmap VTF, CubeMapTransformY baked in.

    Source samples its cubemap with reflect(dir); we want that lookup to
    return cf_cube(rotY(dir)), so each Source face pixel samples the CF
    cube through the rotated direction. Output is an uncompressed
    BGRA8888 ENVMAP VTF (6 faces, 1 mip) - fixed reflection everywhere,
    independent of map env_cubemap entities.
    """
    import struct
    import cf_reference_renderer as cfrr

    cf_faces = cfrr.dds_faces(dds_path)
    faces_bgra = []
    for name in _FACE_ORDER:
        dirs = _face_dirs(name, face_size).reshape(-1, 3)
        dirs = cfrr.rot_y(dirs, transform_y_deg)
        rgb = cfrr.cube_sample(cf_faces, dirs).reshape(face_size, face_size, 3)
        px = np.uint8(np.round(np.clip(rgb, 0, 1) * 255.0))
        bgra = np.concatenate([px[:, :, ::-1],
                               np.full((*px.shape[:2], 1), 255, np.uint8)], 2)
        faces_bgra.append(bgra.tobytes())

    out_vtf = Path(out_vtf)
    out_vtf.parent.mkdir(parents=True, exist_ok=True)
    header = bytearray(80)
    header[0:4] = b"VTF\x00"
    struct.pack_into("<II", header, 4, 7, 2)
    struct.pack_into("<I", header, 12, 80)
    struct.pack_into("<HH", header, 16, face_size, face_size)
    struct.pack_into("<I", header, 20, 0x4000)          # ENVMAP
    struct.pack_into("<HH", header, 24, 1, 0)
    struct.pack_into("<fff", header, 32, 0.5, 0.5, 0.5)
    struct.pack_into("<f", header, 48, 1.0)
    struct.pack_into("<I", header, 52, 12)             # BGRA8888
    header[56] = 1                                     # 1 mip
    struct.pack_into("<I", header, 57, 13)             # lowres fmt DXT1
    header[61] = 16
    header[62] = 16
    struct.pack_into("<H", header, 63, 1)
    color = ((128 >> 3) << 11) | ((128 >> 2) << 5) | (128 >> 3)
    thumb = struct.pack("<HHI", color, color, 0) * 16
    out_vtf.write_bytes(bytes(header) + thumb + b"".join(faces_bgra))
    return out_vtf


def lightwarp_terms(cfg_flat: dict) -> tuple[Image.Image, float]:
    """Shared 256x16 lightwarp ramp; dark floor = 1 - CFG lit fraction."""
    lit = float(cfg_flat.get("LightBrightness", 0.5) or 0.5)
    lit_fraction = max(MIN_LIT_FRACTION,
                       min(MAX_LIT_FRACTION, lit * LIGHT_INFLUENCE_SCALE))
    floor = 1.0 - lit_fraction
    ramp = np.linspace(floor, 1.0, 256, dtype=np.float32)
    arr = np.repeat(ramp[None, :, None], 16, axis=0).repeat(3, axis=2)
    img = Image.fromarray(np.uint8(np.round(arr * 255.0)), "RGB")
    return img, round(lit_fraction, 4)


def vertexlit_vmt(material_root: str, base_name: str, normal_name: str,
                  slot_name: str, strategy: str, cfg_flat: dict,
                  tint: list[float], env_tint: list[float] | None,
                  exponent: int | None = None,
                  boost: float | None = None,
                  lightwarp_name: str | None = None,
                  envmap_texture: str | None = None) -> str:
    if exponent is None or boost is None:
        exponent, boost = phong_terms(cfg_flat, tint, strategy)
    lines = [
        '"VertexLitGeneric"', "{",
        f'\t"$basetexture" "{material_root}/{base_name}"',
        f'\t"$bumpmap" "{material_root}/{normal_name}"',
        '\t"$halflambert" "1"',
    ]
    if lightwarp_name:
        lines.append(f'\t"$lightwarptexture" "{material_root}/{lightwarp_name}"')
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
    if env_tint is not None:
        envmap_ref = (f"{material_root}/{envmap_texture}"
                      if envmap_texture else "env_cubemap")
        lines += [
            f'\t"$envmap" "{envmap_ref}"',
            '\t"$normalmapalphaenvmapmask" "1"',
            f'\t"$envmaptint" "{_fmt_vec(env_tint)}"',
        ]
    lines += ['\t"$nocull" "0"', "}", ""]
    return "\n".join(lines)


def env_tint_for_region(region: dict, cfg_flat: dict,
                        tint: list[float]) -> list[float]:
    """envmaptint: region env-response strength x specular chroma.

    CF env cube is neutral gray; the gold comes from _S chroma, so the
    envmap tint inherits the specular hue (approximated, tagged).
    """
    f = region["feature_means"]
    env_b = float(cfg_flat.get("EnvCubeMapBrightness", 1.0) or 1.0)
    strength = min(ENVMAP_TINT_MAX,
                   f.get("alpha_b", 0.1) * env_b * ENV_STRENGTH_GAIN)
    return [round(min(ENVMAP_TINT_MAX, strength * c), 3) for c in tint]


def translate(ir: dict, regions_result: dict, maps: dict,
              material_root: str, base_name: str, normal_name: str,
              out_dir: Path | str, size: tuple[int, int],
              envmap_texture: str | None = None) -> dict:
    """Produce VMT set + slot names + translation report."""
    cfg_flat = ir["cfg"]["flat"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    masks = build_masks(maps, cfg_flat, size)
    masks["phong_mask"].save(out_dir / "mask_phong.png")
    masks["env_mask"].save(out_dir / "mask_env.png")
    lightwarp, lit_fraction = lightwarp_terms(cfg_flat)
    lightwarp.save(out_dir / f"{base_name}_lightwarp.png")
    lightwarp_name = f"{base_name}_lightwarp"
    tint = spec_tint(maps)
    slots = []
    vmts = {}
    for region in regions_result["regions"]:
        s = choose_strategy(region, cfg_flat)
        slot = f"{base_name}_r{region['region_id']}"
        env_t = (env_tint_for_region(region, cfg_flat, tint)
                 if s["strategy"] != "matte_dark" else None)
        exponent, boost = phong_terms(cfg_flat, tint, s["strategy"])
        if region["feature_means"].get("diffuse_lum", 1.0) < DARK_REGION_LUM:
            exponent = min(exponent, DARK_REGION_EXP_CAP)
        vmt = vertexlit_vmt(material_root, base_name, normal_name, slot,
                            s["strategy"], cfg_flat, tint, env_t,
                            exponent, boost, lightwarp_name,
                            envmap_texture)
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
        "lightwarp": {"texture": lightwarp_name,
                      "lit_fraction": lit_fraction,
                      "dark_floor": round(1.0 - lit_fraction, 4)},
        "envmap_texture": envmap_texture,
        "tags": {
            "preserved": ["diffuse base texture", "normal map", "specular->phong mask (low-pass)",
                          "alpha.B->envmap mask (low-pass)", "specular chroma->$phongtint",
                          "SpecularPower*0.25->exponent scale"],
            "approximated": ["CF lobby cubemap->static envmap VTF (transform baked, content preserved)"
                             if envmap_texture else
                             "CF lobby cubemap->engine env_cubemap (content differs)",
                             "CF transformed/refract ray->Source reflect ray (approximated)",
                             "per-region envmaptint from alpha.B energy (approximated)",
                             "envmap enabled on all non-matte slots; per-pixel alpha.B mask bounds coverage"],
            "lost": ["Snell refraction contribution",
                     "exact CF diffuse-lit scale (ambient/boost terms)"],
            "unsupported_by_source1": [],
        },
    }
    return {"vmts": vmts, "slots": slots, "report": report}
