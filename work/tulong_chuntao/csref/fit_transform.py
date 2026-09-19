# -*- coding: utf-8 -*-
"""P3b — CF PV → CS viewmodel H for 屠龙-春桃.

Hands and knife share one CF PLAYERVIEW skeleton. Do not ICP onto stock CS
knife (wrong shape) and do not copy the third-party p_Kukri_Beast placement.
Reuse the Tianxi (Galil ACE) H: same CF playerview space, same camera.
MX is about this knife's own H-transformed bbox centre, same as A.11.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "tulong_chuntao"
CSREF = WORK / "csref" / "decompiled_stock" / "v_knife_default_ct"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_kukri_spring.json"
OUT = WORK / "csref" / "viewmodel_transform.json"

PIECE_NODE = {"objObject03000": 47}
GUN_BONES = {"v_weapon", "v_weapon.knife"}
ATTACH = ("v_weapon.uid",)


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
            nlinks = int(parts[9]) if len(parts) > 9 else 0
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


def stock_posed_gun_verts(model):
    nodes = model["nodes"]
    rest_w = compose_worlds(nodes, model["frames"][0])
    name_of = {i: n[0] for i, n in nodes.items()}
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
                hom = np.array(v["pos"] + [1.0])
                acc += w * (rest_w[b] @ hom)[:3]
            pts.append(acc)
            by_bone.setdefault(name_of.get(v["bone"]), []).append(acc)
    return np.array(pts), rest_w, name_of, {k: np.array(v) for k, v in by_bone.items()}


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


TIANXI_H = _REPO / "work" / "galil_ace_tianxi" / "csref" / "viewmodel_transform.json"
TIANXI_PAYLOAD = _REPO / "work" / "galil_ace_tianxi" / "decode" / "reference_payload.json"
TIANXI_XC = -5.223


def vm_pos(payload, bone, s, R, t, xc):
    s0 = payload["clips"]["idle_0"]["samples"][0]
    idx = next(n["index"] for n in payload["nodes"] if n["name"] == bone)
    q = s * (R @ np.array(s0["pos"][idx])) + t
    q[0] = 2 * xc - q[0]
    return q


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    tianxi = json.loads(TIANXI_H.read_text(encoding="utf-8"))
    tianxi_payload = json.loads(TIANXI_PAYLOAD.read_text(encoding="utf-8"))
    source, _cf_by_piece = cf_posed_gun_verts(payload, skin)

    s = float(tianxi["H"]["scale"])
    R = np.array(tianxi["H"]["rotation"], dtype=float)
    t = np.array(tianxi["H"]["translation"], dtype=float)
    transformed = s * (source @ R.T) + t
    gun_xc = float((transformed[:, 0].min() + transformed[:, 0].max()) / 2)
    print(f"cf knife verts={len(source)}")
    print("cf idle bbox", source.min(0).round(3).tolist(), source.max(0).round(3).tolist())
    print(f"reuse Tianxi H s={s:.6f} det(R)={np.linalg.det(R):.4f} t={np.round(t, 3)}")
    print("H bbox", transformed.min(0).round(3).tolist(), transformed.max(0).round(3).tolist(),
          "center", transformed.mean(0).round(3).tolist())

    # Keep the shared CF playerview transform and native two-hand pose.
    # Match the accepted rifle hand depth, then apply the user's farther-away adjustment.
    # Source +Z is screen-up, so a negative Z offset lowers the full viewmodel.
    # Remove the extra 15-degree screen rotation and the knife normal inversion.
    knife_l = vm_pos(payload, "FvARM-bone L Hand", s, R, t, gun_xc)
    knife_r = vm_pos(payload, "FvARM-bone R Hand", s, R, t, gun_xc)
    rifle_l = vm_pos(tianxi_payload, "FvARM-bone L Hand", s, R, t, TIANXI_XC)
    rifle_r = vm_pos(tianxi_payload, "FvARM-bone R Hand", s, R, t, TIANXI_XC)
    depth_match = float(((rifle_l[1] + rifle_r[1]) - (knife_l[1] + knife_r[1])) / 2)
    view_push_y = depth_match - 15.0
    view_push_z = -3.5
    view_roll_deg = 0.0
    print(f"gun_center_x={gun_xc:.4f} view_push_y={view_push_y:.3f} "
          f"view_push_z={view_push_z:.3f} view_roll_deg={view_roll_deg}")

    c = transformed.mean(0)
    attach = {
        "v_weapon.uid": [
            [1.0, 0.0, 0.0, float(c[0])],
            [0.0, 1.0, 0.0, float(c[1])],
            [0.0, 0.0, 1.0, float(c[2])],
            [0.0, 0.0, 0.0, 1.0],
        ]
    }
    doc = {
        "H": {"scale": s, "rotation": R.tolist(), "translation": t.tolist()},
        "gun_center_x": gun_xc,
        "apply_mirror": True,
        "view_push_y": view_push_y,
        "view_push_z": view_push_z,
        "view_roll_deg": view_roll_deg,
        "flip_knife_v": False,
        "flip_knife_normals": False,
        "icp": {
            "method": "reuse verified CF-playerview H; preserve native pose; user-calibrated depth/Z offsets",
            "src": "CF idle_0 posed Kukri_Beast spring rigid knife verts",
            "dst": "shared CF playerview camera space with farther/lower review adjustment",
            "depth_match": depth_match,
            "view_push_y": view_push_y,
            "view_push_z": view_push_z,
            "view_roll_deg": view_roll_deg,
        },
        "attach_worlds_p6": attach,
        "note": "Native CF pose retained; middle depth/lower offset; extra roll removed; knife V kept raw; normal inversion disabled.",
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
