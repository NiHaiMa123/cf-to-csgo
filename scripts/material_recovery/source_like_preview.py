"""Generic Phase H Source-like preview shading (offline diagnostic only).

NOT a CF renderer and NOT Source 1 ground truth: a behavior approximation
of the translated VertexLitGeneric strategies, run on the SAME rasterized
frame/camera/lights as the CF reference so A/B deltas mean something.

Models per slot strategy:
  diffuse    = albedo * halflambert(N.L)
  phong      = phong_mask * boost * tint * pow(max(reflect(-V,N).L, 0), exp)
               (skipped for matte_dark)
  env proxy  = env_mask * env_tint * cubemap(reflect(-V,N))
               (envmap_metal only; approximates engine env_cubemap —
               content proxied by the CF cube via a PLAIN reflect ray,
               never the transformed/Snell ray)
"""
from __future__ import annotations

import numpy as np

import cf_reference_renderer as cfrr

LUM_WEIGHTS = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)

# flat ambient floor approximating Source radiosity/lightprobe ambient on
# viewmodels; generic engine proxy, not per-weapon tuning
SOURCE_AMBIENT = 0.15


def strategy_params(cfg_flat: dict, tint: list[float],
                    boost: float, exponent: int,
                    env_tint: list[float] | None) -> dict:
    return {"exponent": int(exponent), "boost": float(boost),
            "tint": list(tint), "env_tint": env_tint}


def slot_params_from_report(report: dict, cfg_flat: dict) -> dict:
    """Read per-slot shader constants recorded by the translator."""
    params = {}
    for s in report["slots"]:
        params[s["material"]] = {
            "strategy": s["strategy"],
            "exponent": s["phong_exponent"],
            "boost": s["phong_boost"],
            "tint": report["phong_tint"],
            "env_tint": s.get("envmap_tint"),
        }
    return params


def render_source_like(frame: dict, meshes: list[dict], maps: dict,
                       tri_slot: list[np.ndarray], slot_params: dict,
                       masks: dict, light_dir, eye, size: int,
                       view: np.ndarray) -> tuple[np.ndarray, dict]:
    """Source-like shade on an already-rasterized frame.

    tri_slot[mi][ti] = material slot name for that triangle.
    """
    hit = frame["tri"] >= 0
    idx = np.where(hit)
    n_pix = len(idx[0])
    out = np.zeros((size, size, 3), np.float32)
    comps = {"phong": np.zeros((size, size, 3), np.float32),
             "env": np.zeros((size, size, 3), np.float32),
             "diffuse": np.zeros((size, size, 3), np.float32)}
    if n_pix == 0:
        return out, comps
    P = np.zeros((n_pix, 3), np.float32)
    N = np.zeros((n_pix, 3), np.float32)
    UV = np.zeros((n_pix, 2), np.float32)
    Ttri = np.zeros((n_pix, 3), np.float32)
    Btri = np.zeros((n_pix, 3), np.float32)
    slot_name = np.empty(n_pix, dtype=object)
    hit_mesh = frame["mesh"][idx]
    hit_tri = frame["tri"][idx]
    hit_bary = frame["bary"][idx]
    for mi, mesh in enumerate(meshes):
        sel = hit_mesh == mi
        if not sel.any():
            continue
        t = hit_tri[sel]
        b = hit_bary[sel]
        tri = mesh["tris"][t]
        P[sel] = (mesh["verts"][tri] * b[:, :, None]).sum(1)
        UV[sel] = (mesh["uvs"][tri] * b[:, :, None]).sum(1)
        vn = cfrr.vertex_normals(mesh["verts"], mesh["tris"])
        N[sel] = (vn[tri] * b[:, :, None]).sum(1)
        tang, bitan = cfrr.tangent_frames(mesh["verts"], mesh["uvs"],
                                          mesh["tris"])
        Ttri[sel] = tang[t]
        Btri[sel] = bitan[t]
        slot_name[sel] = tri_slot[mi][t]
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    if maps.get("normal") is not None:
        nm = cfrr.sample_bilinear(maps["normal"], UV) * 2.0 - 1.0
        N = (Ttri * nm[:, 0:1] + Btri * nm[:, 1:2] + N * nm[:, 2:3])
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    V = eye - P
    V = V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
    L = np.asarray(light_dir, np.float32)
    L = L / np.linalg.norm(L)

    albedo = cfrr.sample_bilinear(maps["diffuse"], UV)
    lambert_h = np.clip(((N * L).sum(-1, keepdims=True) + 1.0) * 0.5, 0.0, 1.0)
    diffuse = albedo * (SOURCE_AMBIENT + (1.0 - SOURCE_AMBIENT) * lambert_h)
    phong_mask = cfrr.sample_bilinear(masks["phong"], UV)[:, 0:1]
    env_mask = cfrr.sample_bilinear(masks["env"], UV)[:, 0:1]
    Rv = cfrr.reflect(-V, N)
    spec_angle = np.clip((Rv * L).sum(-1, keepdims=True), 0.0, 1.0)

    phong = np.zeros((n_pix, 3), np.float32)
    env = np.zeros((n_pix, 3), np.float32)
    for name, sp in slot_params.items():
        sel = slot_name == name
        if not sel.any():
            continue
        if sp["boost"] > 0.0:
            phong[sel] = (phong_mask[sel] * sp["boost"]
                          * np.asarray(sp["tint"], np.float32)
                          * spec_angle[sel] ** sp["exponent"])
        if sp.get("env_tint") is not None and maps.get("cubemap") is not None:
            ray = cfrr.reflect(-V[sel], N[sel])
            env[sel] = (env_mask[sel]
                        * np.asarray(sp["env_tint"], np.float32)
                        * cfrr.cube_sample(maps["cubemap"], ray))
    out[idx[0], idx[1]] = diffuse + phong + env
    comps["diffuse"][idx[0], idx[1]] = diffuse
    comps["phong"][idx[0], idx[1]] = phong
    comps["env"][idx[0], idx[1]] = env
    return np.clip(out, 0.0, 1.0), comps


def build_tri_slot(meshes: list[dict], assignments: dict,
                   fallback: str) -> list[np.ndarray]:
    """per-(mesh, tri) -> slot material name from Phase G assignment table."""
    tri_slot = []
    for mesh in meshes:
        names = assignments.get(mesh["name"], {})
        arr = np.array([names.get(str(t), fallback)
                        for t in range(len(mesh["tris"]))], dtype=object)
        tri_slot.append(arr)
    return tri_slot
