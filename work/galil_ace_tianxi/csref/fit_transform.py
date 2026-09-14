# -*- coding: utf-8 -*-
"""P3b — fit CF-space -> viewmodel-space similarity transform for GalilACE.

Same recipe as p7_s05 R3: ICP-fit the CF idle-posed gun vertices onto the
*stock* v_rif_galilar idle-posed vertices (official reference). Output
viewmodel_transform.json {H:{scale,rotation,translation}, attach_worlds_p6}.

H: v' = s*R*v + t applied to verts; bones rest R' = H B H^-1; anim W' = H W H^-1.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "galil_ace_tianxi"
CSREF = WORK / "csref" / "decompiled_stock"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_galilace.json"
OUT = WORK / "csref" / "viewmodel_transform.json"

PIECE_NODE = {
    "Body": 46, "Mag": 49, "Core01": 55, "Core02": 53, "Core03": 54,
    "Object489": 50, "Object490": 51, "Object491": 52,
    "Stock": 47, "Object492": 48,
}

# stock gun bones: verts skinned to these count as "gun" for the fit
GUN_BONES = {
    "v_weapon", "v_weapon.galilar_parent", "v_weapon.latch",
    "v_weapon.magazine", "v_weapon.plate", "v_weapon.trigger",
    "v_weapon.bolt", "v_weapon.flash", "v_weapon.shelleject",
    "v_weapon.stattrack", "v_weapon.uid",
}
ATTACH = ("v_weapon.flash", "v_weapon.shelleject", "v_weapon.stattrack", "v_weapon.uid")


def euler_to_mat(e):
    rx, ry, rz = e
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return np.array([
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx, 0],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx, 0],
        [-sy, cy * sx, cy * cx, 0],
        [0, 0, 0, 1],
    ])


def parse_smd(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes = {}
    frames = []
    tris = []
    mode = None
    cur = None
    cur_mat = None
    tri_verts = []
    for ln in lines:
        s = ln.strip()
        if s == "nodes":
            mode = "n"; continue
        if s == "skeleton":
            mode = "s"; continue
        if s == "triangles":
            mode = "t"; continue
        if s == "end":
            mode = None
            if cur is not None:
                frames.append(cur); cur = None
            continue
        if mode == "n":
            m = s.split('"')
            idx = int(s.split()[0])
            nodes[idx] = (m[1], int(s.rsplit('"', 1)[1]))
        elif mode == "s":
            if s.startswith("time"):
                if cur is not None:
                    frames.append(cur)
                cur = {}
            else:
                parts = s.split()
                cur[int(parts[0])] = tuple(float(v) for v in parts[1:7])
        elif mode == "t":
            parts = s.split()
            try:
                bone = int(parts[0])
            except (ValueError, IndexError):
                cur_mat = s
                tri_verts = []
                continue
            pos = [float(v) for v in parts[1:4]]
            nrm = [float(v) for v in parts[4:7]]
            uv = [float(v) for v in parts[7:9]]
            nlinks = int(parts[9])
            links = []
            for k in range(nlinks):
                links.append((int(parts[10 + 2 * k]), float(parts[11 + 2 * k])))
            tri_verts.append({"bone": bone, "pos": pos, "nrm": nrm, "uv": uv, "links": links})
            if len(tri_verts) == 3:
                tris.append({"material": cur_mat, "verts": tri_verts})
                cur_mat = None
    if cur is not None:
        frames.append(cur)
    return {"nodes": nodes, "frames": frames, "tris": tris}


def compose_worlds(nodes, frame):
    worlds = {}
    def world(i):
        if i in worlds:
            return worlds[i]
        pos, e = frame[i][:3], frame[i][3:]
        m = euler_to_mat(e)
        m[:3, 3] = pos
        name, p = nodes[i]
        worlds[i] = m if p < 0 else world(p) @ m
        return worlds[i]
    for i in nodes:
        world(i)
    return worlds


def stock_posed_gun_verts(model, idle):
    nodes = model["nodes"]
    rest_w = compose_worlds(nodes, model["frames"][0])
    idle_w = compose_worlds(nodes, idle["frames"][0])
    name_of = {i: n[0] for i, n in nodes.items()}
    delta = {i: idle_w[i] @ np.linalg.inv(rest_w[i]) for i in nodes}
    pts = []
    by_bone = {}
    for tri in model["tris"]:
        for v in tri["verts"]:
            links = v["links"] or [(v["bone"], 1.0)]
            if not any(name_of.get(b) in GUN_BONES for b, w in links if w > 0):
                continue
            acc = np.zeros(3)
            for b, w in links:
                if w <= 0:
                    continue
                acc += w * (delta[b] @ np.array(v["pos"] + [1.0]))[:3]
            pts.append(acc)
            by_bone.setdefault(name_of.get(v["bone"]), []).append(acc)
    return np.array(pts), rest_w, idle_w, name_of, {k: np.array(v) for k, v in by_bone.items()}


def cf_posed_gun_verts(payload, skin):
    nodes = payload["nodes"]
    s0 = payload["clips"]["idle_0"]["samples"][0]
    W = []
    for i in range(len(nodes)):
        x, y, z, wq = s0["quat_xyzw_world"][i]
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * wq), 2 * (x * z + y * wq)],
            [2 * (x * y + z * wq), 1 - 2 * (x * x + z * z), 2 * (y * z - x * wq)],
            [2 * (x * z - y * wq), 2 * (y * z + x * wq), 1 - 2 * (x * x + y * y)],
        ])
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = s0["pos"][i]
        W.append(M)
    pts = []
    by_piece = {}
    for m in skin["meshes"]:
        ni = PIECE_NODE.get(m["name"])
        if ni is None:
            continue
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        vs = np.array(m["vertices"]).reshape(-1, 3)
        hom = np.concatenate([vs, np.ones((len(vs), 1))], axis=1)
        posed = (D @ hom.T).T[:, :3]
        pts.append(posed)
        by_piece[m["name"]] = posed
    return np.concatenate(pts), by_piece


def unique_points(points):
    return np.unique(np.round(points, 6), axis=0)


def sample_points(points, limit):
    points = unique_points(points)
    if len(points) <= limit:
        return points
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    return points[order[np.linspace(0, len(points) - 1, limit, dtype=int)]]


def nearest(source, target, chunk=256):
    indices, distances = [], []
    for start in range(0, len(source), chunk):
        part = source[start:start + chunk]
        squared = np.sum((part[:, None, :] - target[None, :, :]) ** 2, axis=2)
        idx = np.argmin(squared, axis=1)
        indices.append(idx)
        distances.append(np.sqrt(squared[np.arange(len(part)), idx]))
    return np.concatenate(indices), np.concatenate(distances)


def signed_axis_rotations():
    import itertools
    rotations = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix = np.zeros((3, 3))
            for output_axis, input_axis in enumerate(permutation):
                matrix[output_axis, input_axis] = signs[output_axis]
            if np.linalg.det(matrix) > 0.5:
                rotations.append(matrix)
    return rotations


def fit_scale_translation(source, target, rotation):
    rotated = source @ rotation.T
    sc, tc = rotated.mean(0), target.mean(0)
    cs, ct = rotated - sc, target - tc
    denom = float(np.sum(cs * cs))
    scale = float(np.sum(cs * ct) / denom) if denom else 1.0
    if scale < 0:
        scale = -scale
    return scale, tc - scale * sc


def robust_icp(source, target, rotation, scale, translation, iterations=16):
    for _ in range(iterations):
        transformed = scale * (source @ rotation.T) + translation
        indices, distances = nearest(transformed, target)
        keep = distances <= float(np.quantile(distances, 0.72))
        src, dst = source[keep], target[indices[keep]]
        sc, dc = src.mean(0), dst.mean(0)
        sz, dz = src - sc, dst - dc
        u, singular, vt = np.linalg.svd(sz.T @ dz)
        correction = np.eye(3)
        correction[-1, -1] = np.sign(np.linalg.det(vt.T @ u.T))
        rotation = vt.T @ correction @ u.T
        denom = float(np.sum(sz * sz))
        scale = float(np.sum(singular * np.diag(correction)) / denom)
        translation = dc - scale * (sc @ rotation.T)
    transformed = scale * (source @ rotation.T) + translation
    _, forward = nearest(transformed, target)
    _, reverse = nearest(target, transformed)
    metrics = {
        "forward_median": float(np.median(forward)),
        "forward_p90": float(np.quantile(forward, 0.9)),
        "reverse_median": float(np.median(reverse)),
        "reverse_p90": float(np.quantile(reverse, 0.9)),
        "symmetric_trimmed_mean": float(
            (np.mean(forward[forward <= np.quantile(forward, 0.8)])
             + np.mean(reverse[reverse <= np.quantile(reverse, 0.8)])) / 2
        ),
    }
    return rotation, scale, translation, metrics


def anchor_fit(cf_piece, stock_bone):
    """Semantic anchors: Body/Mag/Stock centroids vs galilar_parent/magazine/bolt."""
    cf_anchors = np.array([
        cf_piece["Body"].mean(0), cf_piece["Mag"].mean(0), cf_piece["Stock"].mean(0),
    ])
    stock_anchors = np.array([
        stock_bone["v_weapon.galilar_parent"].mean(0),
        stock_bone["v_weapon.magazine"].mean(0),
        stock_bone["v_weapon.bolt"].mean(0),
    ])
    return cf_anchors, stock_anchors


def main() -> int:
    model = parse_smd(CSREF / "v_galilar_model.smd")
    idle = parse_smd(CSREF / "v_rif_galilar_anims" / "idle.smd")
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))

    Q, rest_w, idle_w, name_of, stock_by_bone = stock_posed_gun_verts(model, idle)
    P, cf_by_piece = cf_posed_gun_verts(payload, skin)
    print(f"stock gun verts={len(Q)} cf gun verts={len(P)}")

    cf_anchors, stock_anchors = anchor_fit(cf_by_piece, stock_by_bone)
    cf_sample = sample_points(P, 1800)
    stock_sample = sample_points(Q, 2600)

    # PCA-based init: align principal axes of both posed gun clouds.
    cf_mu, st_mu = P.mean(0), Q.mean(0)
    _, _, cf_vt = np.linalg.svd(P - cf_mu)
    _, _, st_vt = np.linalg.svd(Q - st_mu)
    cf_rms = float(np.sqrt(((P - cf_mu) ** 2).sum(1).mean()))
    st_rms = float(np.sqrt(((Q - st_mu) ** 2).sum(1).mean()))
    s0 = st_rms / cf_rms

    import itertools
    candidates = []
    for signs in itertools.product((-1.0, 1.0), repeat=3):
        D = np.diag(signs)
        R0 = st_vt.T @ D @ cf_vt
        if np.linalg.det(R0) < 0.5:
            continue
        t0 = st_mu - s0 * (cf_mu @ R0.T)
        candidates.append((R0, s0, t0))
    # also keep axis-permutation inits from semantic anchors as fallbacks
    for axis_rotation in signed_axis_rotations():
        sc, tr = fit_scale_translation(cf_anchors, stock_anchors, axis_rotation)
        if 1.0 <= sc <= 4.0:
            candidates.append((axis_rotation, sc, tr))

    evaluated = []
    for R0, sc, tr in candidates:
        R, s, t, metrics = robust_icp(cf_sample, stock_sample, R0, sc, tr)
        ta = s * (cf_anchors @ R.T) + t
        anchor_rms = float(np.sqrt(np.mean(np.sum((ta - stock_anchors) ** 2, axis=1))))
        score = metrics["symmetric_trimmed_mean"] + 0.35 * anchor_rms
        evaluated.append((score, R, s, t, metrics, anchor_rms))
    evaluated.sort(key=lambda c: c[0])
    for score, R, s, t, metrics, arms in evaluated[:5]:
        print("cand score=%.4f s=%.4f anchor_rms=%.4f sym=%.4f" % (score, s, arms, metrics["symmetric_trimmed_mean"]))
    score, R, s, t, metrics, anchor_rms = evaluated[0]
    med = metrics["forward_median"]
    print(f"H: s={s:.6f} det(R)={np.linalg.det(R):.4f} t={np.round(t,3)}")
    print(f"metrics={json.dumps(metrics, indent=None)} anchor_rms={anchor_rms:.4f}")

    # attachment worlds at stock idle frame 0
    idx_of = {n[0]: i for i, n in model["nodes"].items()}
    attach = {}
    for name in ATTACH:
        i = idx_of[name]
        attach[name] = idle_w[i].tolist()
        print(f"attach {name}: pos={np.round(idle_w[i][:3,3],3)}")

    doc = {
        "H": {"scale": s, "rotation": R.tolist(), "translation": t.tolist()},
        "icp": {"method": "semantic-anchor init + trimmed bidirectional ICP",
                "metrics": metrics, "anchor_rms": anchor_rms,
                "src": "CF idle_0 posed PhantomBeast rigid gun verts",
                "dst": "stock v_rif_galilar idle f0 posed gun verts"},
        "attach_worlds_p6": attach,
        "note": "proper rotation only (det+1); mirror applied separately about gun centre",
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
