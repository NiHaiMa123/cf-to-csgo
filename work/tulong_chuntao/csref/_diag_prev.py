# -*- coding: utf-8 -*-
"""Render third-party kukri (known-good) in its idle pose, textured with spring skin."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _diag_idle_view import parse_smd, compose, invert

WORK = Path(__file__).resolve().parents[1]
SMD = WORK / "csref" / "decompiled_prev_kukri" / "cf_kukri_beast.smd"
IDLE = WORK / "csref" / "decompiled_prev_kukri" / "v_knife_default_ct_anims" / "idle1.smd"
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
tex = np.array(TEX)
Ht, Wt = tex.shape[:2]

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
print("prev nodes", len(nodes), "rest frames", len(rest), "idle frames", len(idle), "tris", len(tris))
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

posed = []
for tri in tris:
    out = []
    for mat, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            if b not in iw or b not in rinv:
                continue
            dw = iw[b] @ rinv[b]
            acc += w * (dw @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        out.append((mat, acc, uv))
    posed.append(out)

pts = np.array([v[1] for t in posed for v in t])
print("prev idle bbox min", pts.min(0).round(2), "max", pts.max(0).round(2), "mean", pts.mean(0).round(2))

SIZE = 640
F = 0.5 * SIZE / math.tan(math.radians(54) / 2)
CX = CY = SIZE / 2
arr = np.full((SIZE, SIZE, 3), (30, 30, 34), np.uint8)
zb = np.full((SIZE, SIZE), np.inf)
for t in posed:
    scr, dep, uvs, ok = [], [], [], True
    for mat, p, uv in t:
        if p[1] >= -0.2:
            ok = False
            break
        d = -p[1]
        scr.append((CX - F * p[0] / d, CY - F * p[2] / d))
        dep.append(d)
        uvs.append(uv)
    if not ok:
        continue
    a, b, c = [np.asarray(s) for s in scr]
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9:
        continue
    x0 = int(max(0, min(s[0] for s in scr))); x1 = int(min(SIZE - 1, max(s[0] for s in scr)))
    y0 = int(max(0, min(s[1] for s in scr))); y1 = int(min(SIZE - 1, max(s[1] for s in scr)))
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            w0 = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
            w1 = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
            w2 = 1 - w0 - w1
            if w0 < -0.02 or w1 < -0.02 or w2 < -0.02:
                continue
            dd = w0 * dep[0] + w1 * dep[1] + w2 * dep[2]
            if dd >= zb[yy, xx]:
                continue
            zb[yy, xx] = dd
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            arr[yy, xx] = tex[min(Ht - 1, int((1 - v) * (Ht - 1))), min(Wt - 1, int(u * (Wt - 1)))]
Image.fromarray(arr).save(WORK / "csref" / "_diag" / "prev_idle_textured.png")
print("wrote prev_idle_textured.png")
