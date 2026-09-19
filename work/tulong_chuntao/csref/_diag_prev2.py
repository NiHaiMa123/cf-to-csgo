# -*- coding: utf-8 -*-
"""Textured preview of fitted viewmodel transform.
R = T_grip @ R_axis(beta) @ R_y(alpha) @ T_-grip applied to posed view verts, + push.
Samples decoded PNG at (u, 1-v_raw) = post-fix appearance.
Usage: _diag_prev2.py alpha beta px py pz [out]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _diag_idle_view import parse_smd, compose, invert

WORK = Path(__file__).resolve().parents[1]
SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
IDLE = WORK / "native_vm" / "source1" / "v_knife_anims" / "idle1.smd"
TEX = WORK / "decode" / "PV-Kukri_Beast_spring.png"
W, H, FOV = 960, 540, 54.0
f = 0.5 * H / math.tan(math.radians(FOV / 2))

alpha = float(sys.argv[1])
beta = float(sys.argv[2])
push = np.array([float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])])
out = Path(sys.argv[6]) if len(sys.argv) > 6 else WORK / "csref" / "_diag" / "prev2.png"

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

PV, PM, UV = [], [], []
for tri in tris:
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        PV.append(acc)
        PM.append(tri[0][0])
        UV.append(uv)
PV = np.array(PV)
kmask = np.array([m == "cf_kukri_spring" for m in PM])
KV = PV[kmask]
axis = np.linalg.svd(KV - KV.mean(0))[2][0]
if axis[2] < 0:
    axis = -axis
HPTS = PV[~kmask]
d2 = ((KV[:, None, :] - HPTS[None, ::8, :]) ** 2).sum(-1)
km = d2.min(1) < 4.0
grip = KV[km].mean(0) if km.sum() else KV.mean(0)


def rot(axis_, deg):
    a = np.asarray(axis_, float)
    a /= np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) * math.cos(t) + (1 - math.cos(t)) * np.outer(a, a) + math.sin(t) * K


Ry = rot([0, 1, 0], alpha)
L = Ry @ axis
R = rot(L, beta) @ Ry

tex = np.asarray(Image.open(TEX).convert("RGB"), float) / 255.0
th, tw = tex.shape[:2]
img = np.zeros((H, W, 3))
zb = np.full((H, W), -1e9)

ti = 0
for tri in tris:
    pts, uvs = [], []
    ok = True
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        p = (R @ (acc - grip)) + grip + push
        if p[1] > -1.0:
            ok = False
            break
        pts.append(p)
        uvs.append(uv)
    if not ok:
        continue
    sx = [f * p[0] / p[1] + W / 2 for p in pts]
    sy = [f * p[2] / p[1] + H / 2 for p in pts]
    x0, x1 = max(0, int(min(sx)) - 1), min(W, int(max(sx)) + 2)
    y0, y1 = max(0, int(min(sy)) - 1), min(H, int(max(sy)) + 2)
    if x1 <= x0 or y1 <= y0:
        continue
    den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
    if abs(den) < 1e-9:
        continue
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            w0 = ((sy[1] - sy[2]) * (xx - sx[2]) + (sx[2] - sx[1]) * (yy - sy[2])) / den
            w1 = ((sy[2] - sy[0]) * (xx - sx[2]) + (sx[0] - sx[2]) * (yy - sy[2])) / den
            w2 = 1 - w0 - w1
            if w0 < 0 or w1 < 0 or w2 < 0:
                continue
            y3 = w0 * pts[0][1] + w1 * pts[1][1] + w2 * pts[2][1]
            if y3 <= zb[yy, xx]:
                continue
            zb[yy, xx] = y3
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            if not (math.isfinite(u) and math.isfinite(v)):
                continue
            tx = min(tw - 1, max(0, int(u * tw)))
            ty = min(th - 1, max(0, int((1 - v) * th)))
            img[yy, xx] = tex[ty, tx]

Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
print("wrote", out)
