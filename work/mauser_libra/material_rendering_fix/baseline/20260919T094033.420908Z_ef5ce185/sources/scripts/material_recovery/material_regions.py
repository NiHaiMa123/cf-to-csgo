"""Generic Phase D material-region analysis (triangle -> material_region_id).

Features per triangle come from real assets only (plan.md v2 §9):
diffuse chroma/luminance, specular response, alpha/mask channels, CF
reference response (channel energies under the recovered formula), mesh
piece and UV-island connectivity.

Clustering: k-means over z-scored features -> region candidates; then a
connectivity pass merges tiny isolated islands into the dominant
neighbour region so slots stay few and regions stay coherent.

No weapon names, fixed category schema, or thresholds tuned to one
weapon: k and feature weights are parameters.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

LUM_WEIGHTS = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)


def _sample(map_arr: np.ndarray, uv: np.ndarray) -> np.ndarray:
    h, w = map_arr.shape[:2]
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)
    return map_arr[y, x]


def triangle_features(meshes: list[dict], maps: dict) -> list[dict]:
    """Per-triangle feature rows; one row per mesh triangle."""
    rows = []
    diff = maps["diffuse"]
    spec = maps.get("specular")
    alpha = maps.get("alpha")
    normal = maps.get("normal")
    for mi, mesh in enumerate(meshes):
        tris, uvs = mesh["tris"], mesh["uvs"]
        cent = (uvs[tris[:, 0]] + uvs[tris[:, 1]] + uvs[tris[:, 2]]) / 3.0
        d = _sample(diff, cent)
        d_lum = d @ LUM_WEIGHTS
        d_chroma = d - d_lum[:, None]
        s = _sample(spec, cent) if spec is not None else np.zeros_like(d)
        s_lum = s @ LUM_WEIGHTS
        a = _sample(alpha, cent) if alpha is not None else np.ones_like(d)
        nm = _sample(normal, cent) if normal is not None else np.full_like(d, 0.5)
        # CF reference response proxies under the recovered formula
        cf_env = (s_lum * a[:, 1] if spec is not None else np.zeros(len(d)))
        cf_cube = a[:, 2]
        feats = np.stack([
            d_lum, d_chroma[:, 0], d_chroma[:, 1],
            s_lum, (s - s_lum[:, None])[:, 0],
            a[:, 1], a[:, 2], cf_env, cf_cube,
            nm[:, 2],
        ], axis=1)
        for t in range(len(tris)):
            rows.append({"mesh": mi, "tri": t, "name": mesh["name"],
                         "features": feats[t], "uv": cent[t]})
    return rows


FEATURE_NAMES = [
    "diffuse_lum", "diffuse_r_minus_lum", "diffuse_g_minus_lum",
    "specular_lum", "specular_r_minus_lum",
    "alpha_g", "alpha_b", "cf_env_response", "cf_cube_response",
    "normalmap_b",
]


def kmeans(feats: np.ndarray, k: int, iters: int = 40,
           seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    z = (feats - feats.mean(0)) / np.maximum(feats.std(0), 1e-9)
    idx = rng.choice(len(z), size=k, replace=False)
    cent = z[idx].copy()
    for _ in range(iters):
        d = ((z[:, None, :] - cent[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        new = cent.copy()
        for c in range(k):
            if (lab == c).any():
                new[c] = z[lab == c].mean(0)
        if np.allclose(new, cent):
            break
        cent = new
    return lab, cent


def describe_region(centroid_z: np.ndarray, feats_mean: np.ndarray,
                    feats_std: np.ndarray) -> str:
    """Name a cluster by its dominant real-unit traits."""
    c = {n: centroid_z[i] * feats_std[i] + feats_mean[i]
         for i, n in enumerate(FEATURE_NAMES)}
    traits = []
    if c["alpha_b"] > 0.25:
        traits.append("env_reflective")
    if c["specular_lum"] > 0.35 and c["specular_r_minus_lum"] > 0.02:
        traits.append("warm_metal")
    elif c["specular_lum"] > 0.35:
        traits.append("bright_metal")
    if c["diffuse_lum"] < 0.08:
        traits.append("dark")
    if c["diffuse_lum"] > 0.25:
        traits.append("light_surface")
    if not traits:
        traits.append("mid_surface")
    return "_".join(traits)


def adjacency(mesh: dict) -> dict[int, set[int]]:
    """Triangle adjacency via shared edges within one mesh."""
    edge_to_tris: dict[tuple[int, int], list[int]] = {}
    tris = mesh["tris"]
    for t, (a, b, c) in enumerate(tris):
        for e in ((a, b), (b, c), (c, a)):
            edge_to_tris.setdefault(tuple(sorted(e)), []).append(t)
    adj: dict[int, set[int]] = {}
    for ts in edge_to_tris.values():
        for t in ts:
            adj.setdefault(t, set()).update(x for x in ts if x != t)
    return adj


def merge_islands(meshes: list[dict], labels: np.ndarray,
                  rows: list[dict], min_island: int) -> np.ndarray:
    """Flood same-region islands; relabel islands smaller than min_island
    to the majority neighbouring region."""
    out = labels.copy()
    offsets = {}
    base = 0
    for mi, mesh in enumerate(meshes):
        offsets[mi] = base
        base += len(mesh["tris"])
    for mi, mesh in enumerate(meshes):
        adj = adjacency(mesh)
        off = offsets[mi]
        seen = np.zeros(len(mesh["tris"]), bool)
        for t0 in range(len(mesh["tris"])):
            if seen[t0]:
                continue
            lab = out[off + t0]
            island = []
            q = deque([t0])
            seen[t0] = True
            while q:
                t = q.popleft()
                island.append(t)
                for nb in adj.get(t, ()):
                    if not seen[nb] and out[off + nb] == lab:
                        seen[nb] = True
                        q.append(nb)
            if len(island) >= min_island:
                continue
            votes: dict[int, int] = {}
            for t in island:
                for nb in adj.get(t, ()):
                    nlab = out[off + nb]
                    if nlab != lab:
                        votes[nlab] = votes.get(nlab, 0) + 1
            if votes:
                winner = max(votes, key=votes.get)
                for t in island:
                    out[off + t] = winner
    return out


def region_preview(rows: list[dict], labels: np.ndarray, names: list[str],
                   diffuse: np.ndarray, out_path: Path | str,
                   palette: list[tuple[int, int, int]] | None = None) -> Path:
    h, w = diffuse.shape[:2]
    img = Image.fromarray(np.uint8(np.round(diffuse * 110.0)), "RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    if palette is None:
        palette = [(255, 80, 80), (80, 200, 80), (90, 140, 255),
                   (255, 210, 60), (220, 80, 220), (60, 220, 220),
                   (255, 150, 60), (160, 160, 255), (200, 255, 120),
                   (255, 120, 180)]
    # draw per-triangle quads is heavy; draw centroid dots + hull-free fill
    for row, lab in zip(rows, labels):
        x, y = row["uv"][0] * w, row["uv"][1] * h
        c = palette[lab % len(palette)]
        r = 2.0
        draw.ellipse((x - r, y - r, x + r, y + r), fill=c + (170,))
    for i, name in enumerate(names):
        draw.text((6, 6 + i * 12), f"{i}: {name}", fill=palette[i % len(palette)])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def analyze(meshes: list[dict], maps: dict, k: int = 6,
            min_island: int = 6) -> dict:
    rows = triangle_features(meshes, maps)
    feats = np.stack([r["features"] for r in rows])
    labels, cent = kmeans(feats, k)
    labels = merge_islands(meshes, labels, rows, min_island)
    fm, fs = feats.mean(0), np.maximum(feats.std(0), 1e-9)
    regions = []
    for c in range(k):
        sel = labels == c
        if not sel.any():
            continue
        mean = feats[sel].mean(0)
        pieces: dict[str, int] = {}
        for r, l in zip(rows, labels):
            if l == c:
                pieces[r["name"]] = pieces.get(r["name"], 0) + 1
        regions.append({
            "region_id": int(c),
            "label": describe_region(cent[c], fm, fs),
            "triangles": int(sel.sum()),
            "feature_means": {n: round(float(mean[i]), 4)
                              for i, n in enumerate(FEATURE_NAMES)},
            "pieces": dict(sorted(pieces.items(), key=lambda kv: -kv[1])),
        })
    assignments = {}
    for r, l in zip(rows, labels):
        assignments.setdefault(r["name"], {})[str(r["tri"])] = int(l)
    return {
        "k_requested": k,
        "regions": regions,
        "triangle_materials": assignments,
        "feature_names": FEATURE_NAMES,
        "rows": rows,
        "labels": labels,
    }
