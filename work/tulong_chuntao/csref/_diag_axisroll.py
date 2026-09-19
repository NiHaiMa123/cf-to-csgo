# -*- coding: utf-8 -*-
"""Compute the roll about the blade long axis that brings the flat side toward
the camera (+Y in view space), then render a preview with tunable roll/push."""
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
OUT = WORK / "csref" / "_diag" / "axisroll_preview.png"

# ---- tunables ----
ROLL_DEG = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
PUSH = np.array([float(sys.argv[2]) if len(sys.argv) > 2 else 0.0,
                 float(sys.argv[3]) if len(sys.argv) > 3 else 0.0,
                 float(sys.argv[4]) if len(sys.argv) > 4 else 0.0])
W, H, FOV = 960, 540, 54.0


def rodrigues(axis, deg):
    a = np.asarray(axis, float)
    a /= np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) * math.cos(t) + (1 - math.cos(t)) * np.outer(a, a) + math.sin(t) * K
    M = np.eye(4)
    M[:3, :3] = R
    return M


nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

def posed_verts(links_filter=None):
    pv, pm = [], []
    for tri in tris:
        mat = tri[0][0]
        for _m, pos, nrm, uv, links in tri:
            if links_filter and not all(b == links_filter for b, _ in links):
                continue
            acc = np.zeros(3)
            for b, w in links:
                acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
            pv.append(acc)
            pm.append(mat)
    return np.array(pv), pm

pv, pm = posed_verts()
kmask = np.array([m == "cf_kukri_spring" for m in pm])
KV = pv[kmask]

axis = np.linalg.svd(KV - KV.mean(0))[2][0]
# orient axis toward blade tip (+Z up)
if axis[2] < 0:
    axis = -axis

# flat-side normal (biggest tris)
kt = [t for t in tris if t[0][0] == "cf_kukri_spring"]
P = []
for tri in kt:
    out = []
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        out.append(acc)
    P.append(out)
P = np.array(P)
nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
ar = np.linalg.norm(nrm, axis=1)
n = nrm / np.maximum(ar[:, None], 1e-12)
big = ar > np.median(ar) * 4
ref = n[big][np.argmax(ar[big])]
nA = n[big & (n @ ref > 0.5)].mean(0)
nB = n[big & (n @ ref < -0.5)].mean(0)
n_cam = nA if nA[1] > nB[1] else nB
print("flat normal toward cam:", n_cam.round(3), "axis:", axis.round(3))

# optimal roll about axis to make n_cam -> +Y
np_perp = n_cam - (n_cam @ axis) * axis
yp = np.array([0, 1, 0.0]) - (np.array([0, 1, 0.0]) @ axis) * axis
np_perp /= np.linalg.norm(np_perp)
yp /= np.linalg.norm(yp)
cos_t = float(np.clip(np_perp @ yp, -1, 1))
sin_t = float((np.cross(np_perp, yp) @ axis))
theta_full = math.degrees(math.atan2(sin_t, cos_t))
print("roll-to-frontal deg:", round(theta_full, 1))

# pivot: knife verts nearest hands (grip)
HPTS = pv[~kmask]
d2 = ((KV[:, None, :] - HPTS[None, ::8, :]) ** 2).sum(-1)
grip = KV[d2.min(1) < 4.0].mean(0)
print("grip:", grip.round(2), "knife bbox", KV.min(0).round(1), KV.max(0).round(1))

R = rodrigues(axis, ROLL_DEG)
R[:3, 3] = grip - R[:3, :3] @ grip

tex = np.asarray(Image.open(TEX).convert("RGB"), float) / 255.0
th, tw = tex.shape[:2]
f = 0.5 * H / math.tan(math.radians(FOV / 2))
img = np.zeros((H, W, 3))
zb = np.full((H, W), -1e9)

for tri in tris:
    pts, uvs = [], []
    for _m, pos, n, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        p = (R @ np.array([*acc, 1.0]))[:3] + PUSH
        if p[1] > -0.5:
            break
        pts.append(p)
        uvs.append(uv)
    else:
        sx = [-f * p[0] / p[1] + W / 2 for p in pts]
        sy = [f * p[2] / p[1] + H / 2 for p in pts]
        xs, ys = np.array(sx), np.array(sy)
        x0, x1 = max(0, int(xs.min()) - 1), min(W, int(xs.max()) + 2)
        y0, y1 = max(0, int(ys.min()) - 1), min(H, int(ys.max()) + 2)
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
                tx = min(tw - 1, max(0, int(u * tw)))
                ty = min(th - 1, max(0, int((1 - v) * th)))
                img[yy, xx] = tex[ty, tx]

Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(OUT)
print("wrote", OUT, "roll", ROLL_DEG, "push", PUSH)
