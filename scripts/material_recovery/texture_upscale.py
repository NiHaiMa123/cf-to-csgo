"""Generic Phase E texture processing (material reconstruction v2).

Rules (plan.md v2 §11):
- diffuse: AI upscale allowed, original preserved, 4x is intermediate,
  final usually 2048, atlas/UV must not change;
- normal: NO generative AI — decode vectors, resize/interpolate,
  renormalize, encode;
- specular/alpha/masks: NO generative AI — bicubic/Lanczos resize,
  controlled blur or semantically justified remap only; histogram and
  area coverage must be compared before/after.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image


def resize_rgb(src: Path | str, dst: Path | str, size: tuple[int, int],
               resample=Image.Resampling.LANCZOS) -> dict:
    """Plain RGB resize (for non-generative paths)."""
    im = Image.open(src).convert("RGB")
    im = im.resize(size, resample)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return {"dst": str(dst), "size": list(size), "resample": str(resample)}


def resize_normal(src: Path | str, dst: Path | str, size: tuple[int, int],
                  resample=Image.Resampling.BICUBIC) -> dict:
    """Resize a tangent-space normal map as vectors, then renormalize."""
    arr = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
    vec = arr * 2.0 - 1.0
    h, w = size[1], size[0]
    out = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        out[:, :, c] = np.asarray(
            Image.fromarray(vec[:, :, c]).resize(size, resample),
            dtype=np.float32)
    n = np.linalg.norm(out, axis=2, keepdims=True)
    out = out / np.maximum(n, 1e-6)
    enc = np.uint8(np.round((out * 0.5 + 0.5) * 255.0))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(enc, "RGB").save(dst)
    return {"dst": str(dst), "size": list(size),
            "process": "decode->resize->renormalize->encode"}


def resize_mask(src: Path | str, dst: Path | str, size: tuple[int, int],
                resample=Image.Resampling.LANCZOS,
                blur: float = 0.0) -> dict:
    """Resize a mask/spec map; optional controlled blur (semantic-free)."""
    from PIL import ImageFilter
    im = Image.open(src).convert("RGB").resize(size, resample)
    if blur > 0:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return {"dst": str(dst), "size": list(size),
            "resample": str(resample), "blur": blur}


def coverage_report(before: Path | str, after: Path | str,
                    lum_thresholds=(0.05, 0.5)) -> dict:
    """Histogram + bright-area coverage comparison before/after resize."""
    def stats(p):
        a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0
        lum = a @ np.array((0.2126, 0.7152, 0.0722), np.float32)
        hist, _ = np.histogram(lum, bins=16, range=(0, 1))
        return {
            "size": list(a.shape[1::-1]),
            "lum_mean": round(float(lum.mean()), 4),
            "histogram": [int(x) for x in hist],
            "coverage": {str(t): round(float((lum > t).mean()), 4)
                         for t in lum_thresholds},
        }
    return {"before": stats(before), "after": stats(after)}
