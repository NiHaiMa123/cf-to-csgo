"""Generic Phase B2 texture-channel audit for CF material reconstruction.

For every texture channel: extrema, mean/std, percentiles, histogram,
sparsity, pairwise channel correlation, correlation against the diffuse
luminance, and per-mesh-piece sampled means (UV-island correlation).

No weapon names or channel semantics live here; callers supply the map
paths and optional skin dump for per-piece aggregation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LUM_WEIGHTS = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
_PERCENTILES = (5, 25, 50, 75, 95)
_HIST_BINS = 16


def _band_stats(band: np.ndarray) -> dict:
    flat = band.ravel().astype(np.float32)
    hist, edges = np.histogram(flat, bins=_HIST_BINS, range=(0.0, 1.0))
    values, counts = np.unique(flat, return_counts=True)
    modal = int(counts.argmax())
    return {
        "min": round(float(flat.min()), 4),
        "max": round(float(flat.max()), 4),
        "mean": round(float(flat.mean()), 4),
        "std": round(float(flat.std()), 4),
        "percentiles": {str(p): round(float(np.percentile(flat, p)), 4)
                        for p in _PERCENTILES},
        "histogram": {"bins": _HIST_BINS, "counts": [int(c) for c in hist],
                      "edges": [round(float(e), 4) for e in edges]},
        "unique_values": int(len(values)),
        "modal_value": round(float(values[modal]), 4),
        "modal_fraction": round(float(counts[modal]) / flat.size, 4),
        "zero_fraction": round(float((flat == 0.0).mean()), 4),
        "saturated_fraction": round(float((flat >= 254 / 255).mean()), 4),
    }


def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    a = a.ravel().astype(np.float32)
    b = b.ravel().astype(np.float32)
    if a.std() < 1e-9 or b.std() < 1e-9:
        return None
    return round(float(np.corrcoef(a, b)[0, 1]), 4)


def audit_image(path: Path | str) -> dict:
    with Image.open(path) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
        bands = im.getbands()
        extra = {}
        if "A" in bands:
            extra["A"] = np.asarray(im.getchannel("A"), dtype=np.float32) / 255.0
    channels = {"R": rgb[:, :, 0], "G": rgb[:, :, 1], "B": rgb[:, :, 2],
                "lum": rgb @ LUM_WEIGHTS, **extra}
    names = list(channels)
    return {
        "path": str(path),
        "width": rgb.shape[1],
        "height": rgb.shape[0],
        "channels": {name: _band_stats(arr) for name, arr in channels.items()},
        "channel_correlation": {
            f"{a}x{b}": _corr(channels[a], channels[b])
            for i, a in enumerate(names) for b in names[i + 1:]
        },
        "_arrays": channels,
    }


def diffuse_correlation(audit: dict, diffuse_lum: np.ndarray) -> dict:
    """Correlate each channel against diffuse luminance (same canvas)."""
    return {
        name: _corr(arr, diffuse_lum)
        for name, arr in audit["_arrays"].items()
        if arr.shape == diffuse_lum.shape
    }


def piece_sampled_means(audit: dict, skin: dict, mesh_names: list[str],
                        sample: str = "lum") -> dict:
    """Mean of each channel sampled at triangle UV centroids, per piece."""
    arrays = audit["_arrays"]
    h, w = arrays["lum"].shape
    out = {}
    wanted = set(mesh_names)
    for mesh in skin.get("meshes", []):
        if mesh["name"] not in wanted:
            continue
        tris, uvs = mesh["triangles"], mesh["uvs"]
        sums = {k: 0.0 for k in arrays}
        n = 0
        for t in range(len(tris) // 3):
            cu = cv = 0.0
            for k in range(3):
                vi = tris[3 * t + k]
                cu += uvs[2 * vi] / 3.0
                cv += (1.0 - uvs[2 * vi + 1]) / 3.0
            if not (0.0 <= cu <= 1.0 and 0.0 <= cv <= 1.0):
                continue
            x = min(w - 1, max(0, int(cu * w)))
            y = min(h - 1, max(0, int(cv * h)))
            for k, arr in arrays.items():
                sums[k] += float(arr[y, x])
            n += 1
        if n:
            out[mesh["name"]] = {
                "triangles_sampled": n,
                "channel_means": {k: round(v / n, 4) for k, v in sums.items()},
            }
    return out


def channel_sheet(audits: dict[str, dict], out_path: Path | str,
                  thumb: int = 256) -> Path:
    """Contact sheet: rows = textures, cols = R/G/B/A/lum previews."""
    cols = ["R", "G", "B", "A", "lum"]
    label_h = 24
    rows = [a for a in audits.values() if "_arrays" in a]
    names = [k for k, a in audits.items() if "_arrays" in a]
    label_w = 160
    sheet = Image.new("RGB", (label_w + len(cols) * thumb,
                              label_h + len(rows) * thumb), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    for ci, col in enumerate(cols):
        draw.text((label_w + ci * thumb + 4, 4), col, fill=(255, 255, 0))
    for ri, (name, audit) in enumerate(zip(names, rows)):
        y0 = label_h + ri * thumb
        draw.text((4, y0 + 4), name, fill=(255, 255, 255))
        for ci, col in enumerate(cols):
            arr = audit["_arrays"].get(col)
            if arr is None:
                continue
            img = Image.fromarray(np.uint8(np.round(arr * 255.0)), "L")
            img = img.convert("RGB").resize((thumb, thumb))
            sheet.paste(img, (label_w + ci * thumb, y0))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def strip_arrays(audit: dict) -> dict:
    return {k: v for k, v in audit.items() if k != "_arrays"}


def audit_material_maps(maps: dict[str, Path | str], out_json: Path | str,
                        sheet_png: Path | str | None = None,
                        diffuse_role: str = "diffuse",
                        skin: dict | None = None,
                        mesh_names: list[str] | None = None) -> dict:
    audits = {name: audit_image(p) for name, p in maps.items()}
    report = {"maps": {name: strip_arrays(a) for name, a in audits.items()}}
    if diffuse_role in audits:
        dlum = audits[diffuse_role]["_arrays"]["lum"]
        report["diffuse_luminance_correlation"] = {
            name: diffuse_correlation(a, dlum)
            for name, a in audits.items() if name != diffuse_role
        }
    if skin and mesh_names:
        report["piece_sampled_means"] = {
            name: piece_sampled_means(a, skin, mesh_names)
            for name, a in audits.items()
        }
    if sheet_png:
        report["channel_sheet"] = str(channel_sheet(audits, sheet_png))
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=1, ensure_ascii=False),
                        encoding="utf-8")
    return report
