# -*- coding: utf-8 -*-
"""Render ALL skin meshes (hands+arm+knife) posed at idle_0 in CF space via CF camera."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parents[1]
payload = json.loads((WORK / "decode" / "reference_payload.json").read_text(encoding="utf-8"))
skin = json.loads((WORK / "decode" / "cf_skin_kukri_spring.json").read_text(encoding="utf-8"))
vt = json.loads((WORK / "csref" / "viewmodel_transform.json").read_text(encoding="utf-8"))
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
tex = np.array(TEX)
Ht, Wt = tex.shape[:2]


def q2m(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1
    x, y, z, w = x / n, y / n, z / n, w / n
    m = np.eye(4)
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return m


hs = vt["H"]["scale"]
H = np.eye(4)
H[:3, :3] = np.array(vt["H"]["rotation"]) * hs
H[:3, 3] = vt["H"]["translation"]
Hinv = np.linalg.inv(H)
cam_pos = (Hinv @ np.array([0, 0, 0, 1.0]))[:3]
fwd_cf = Hinv[:3, :3] @ np.array([0, -1, 0])
up_cf = Hinv[:3, :3] @ np.array([0, 0, 1])
right_cf = np.cross(fwd_cf, up_cf)
fwd_cf /= np.linalg.norm(fwd_cf)
up_cf /= np.linalg.norm(up_cf)
right_cf /= np.linalg.norm(right_cf)

nodes = payload["nodes"]
B = {n["index"]: np.array(n["bind_world"]) for n in nodes}
name2idx = {n["name"]: n["index"] for n in nodes}
Binv = {i: np.linalg.inv(m) for i, m in B.items()}
skel = skin["skeleton"]
sname2idx = {s["name"]: i for i, s in enumerate(skel)}
print("skin bones:", len(skel), "nodes:", len(nodes))

s0 = payload["clips"]["idle_0"]["samples"][0]
W = {}
for n in nodes:
    i = n["index"]
    m = q2m(s0["quat_xyzw_world"][i])
    m[:3, 3] = s0["pos"][i]
    W[i] = m

all_tris = []  # (posed_pos(3), uv(3))
for m in skin["meshes"]:
    V = np.array(m["vertices"], dtype=float).reshape(-1, 3)
    UV = np.array(m["uvs"], dtype=float).reshape(-1, 2)
    T = np.array(m["triangles"], dtype=int).reshape(-1, 3)
    bw = m.get("bone_weights")
    bi = m.get("bone_indices")
    PV = np.zeros_like(V)
    if bw and bi:
        bw = np.array(bw, dtype=float).reshape(-1, 3)
        bi = np.array(bi, dtype=int).reshape(-1, 4)
        for vi in range(len(V)):
            w0, w1, w2 = bw[vi]
            w3 = max(0.0, 1 - w0 - w1 - w2)
            for k, wv in enumerate((w0, w1, w2, w3)):
                ni = bi[vi][k]
                if ni == 255 or wv <= 0:
                    continue
                bname = skel[ni]["name"] if ni < len(skel) else None
                if bname not in name2idx:
                    continue
                pidx = name2idx[bname]
                PV[vi] += wv * ((W[pidx] @ Binv[pidx]) @ np.array([*V[vi], 1.0]))[:3]
    else:
        GUN = 47
        d = W[GUN] @ Binv[GUN]
        PV = (d @ np.hstack([V, np.ones((len(V), 1))]).T).T[:, :3]
    for t in T:
        all_tris.append(([PV[j] for j in t], [UV[j] for j in t], m["name"]))

SIZE = 640
F = 0.5 * SIZE / math.tan(math.radians(54) / 2)
CX = CY = SIZE / 2
arr = np.full((SIZE, SIZE, 3), (30, 30, 34), np.uint8)
zb = np.full((SIZE, SIZE), np.inf)
for ps, uvs, name in all_tris:
    rel = [np.asarray(p) - cam_pos for p in ps]
    xc = [r @ right_cf for r in rel]
    yc = [r @ fwd_cf for r in rel]
    zc = [r @ up_cf for r in rel]
    if any(d <= 0.05 for d in yc):
        continue
    scr = [(CX + F * xc[i] / yc[i], CY - F * zc[i] / yc[i]) for i in range(3)]
    a, b, c = [np.asarray(s) for s in scr]
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9:
        continue
    x0 = int(max(0, min(s[0] for s in scr)))
    x1 = int(min(SIZE - 1, max(s[0] for s in scr)))
    y0 = int(max(0, min(s[1] for s in scr)))
    y1 = int(min(SIZE - 1, max(s[1] for s in scr)))
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            w0 = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
            w1 = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
            w2 = 1 - w0 - w1
            if w0 < -0.02 or w1 < -0.02 or w2 < -0.02:
                continue
            dd = w0 * yc[0] + w1 * yc[1] + w2 * yc[2]
            if dd >= zb[yy, xx]:
                continue
            zb[yy, xx] = dd
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            ty = min(Ht - 1, int(v * (Ht - 1)))
            tx = min(Wt - 1, int(u * (Wt - 1)))
            arr[yy, xx] = tex[ty, tx] if name == "objObject03000" else (160, 160, 165)
Image.fromarray(arr).save(WORK / "csref" / "_diag" / "cf_native_view_full.png")
print("wrote cf_native_view_full.png")
