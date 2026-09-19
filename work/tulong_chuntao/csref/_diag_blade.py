# -*- coding: utf-8 -*-
"""High-res render of the NEW SMD knife only, from a viewpoint looking at the
flat face. Source-true sampling: PNG row = (1 - v_smd)."""
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

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

kt = [t for t in tris if t[0][0] == "cf_kukri_spring"]
PV = []
for tri in kt:
    out = []
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([*pos, 1.0]))[:3]
        out.append((acc, uv))
    PV.append(out)
P = np.array([[v[0] for v in t] for t in PV])
allp = P.reshape(-1, 3)
c = allp.mean(0)

# blade axes: PCA0 = long axis; flat-face normal = direction that maximizes
# projected area when viewed along it -> PCA2 (smallest extent = thickness)
_, _, vt3 = np.linalg.svd(allp - c)
axis = vt3[0]
if axis[2] < 0:
    axis = -axis
thick = vt3[2]  # smallest spread = flat-face normal direction
flat = thick / np.linalg.norm(thick)
if flat[1] < 0:
    flat = -flat  # choose side toward camera (+Y)
print("axis", axis.round(3), "flat(PCA2)", flat.round(3))

# view along -flat: screen up = axis, screen right = cross
right = np.cross(axis, flat)
right /= np.linalg.norm(right)
up = np.cross(right, flat)  # ~ -axis? recompute: for view dir -flat, up≈axis
up = axis - (axis @ flat) * flat
up /= np.linalg.norm(up)
right = np.cross(up, -flat)
right /= np.linalg.norm(right)

S = 900
img = Image.new("RGB", (S, S), (25, 25, 28))
dr = np.zeros((S, S, 3))
zb = np.full((S, S), -1e9)
tex = np.asarray(Image.open(TEX).convert("RGB"), float) / 255.0
th, tw = tex.shape[:2]
sc = 55.0


def proj(p):
    d = p - c
    return (S / 2 + (d @ right) * sc, S / 2 - (d @ up) * sc, d @ (-flat))


for t in PV:
    pp = [proj(v[0]) for v in t]
    if all(p[2] < -0.01 for p in pp):
        pass
    sx = [p[0] for p in pp]
    sy = [p[1] for p in pp]
    dz = [p[2] for p in pp]
    x0, x1 = max(0, int(min(sx)) - 1), min(S, int(max(sx)) + 2)
    y0, y1 = max(0, int(min(sy)) - 1), min(S, int(max(sy)) + 2)
    if x1 <= x0 or y1 <= y0:
        continue
    den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
    if abs(den) < 1e-9:
        continue
    uvs = [v[1] for v in t]
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            w0 = ((sy[1] - sy[2]) * (xx - sx[2]) + (sx[2] - sx[1]) * (yy - sy[2])) / den
            w1 = ((sy[2] - sy[0]) * (xx - sx[2]) + (sx[0] - sx[2]) * (yy - sy[2])) / den
            w2 = 1 - w0 - w1
            if w0 < 0 or w1 < 0 or w2 < 0:
                continue
            z = w0 * dz[0] + w1 * dz[1] + w2 * dz[2]
            if z <= zb[yy, xx]:
                continue
            zb[yy, xx] = z
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            tx = min(tw - 1, max(0, int(u * tw)))
            ty = min(th - 1, max(0, int((1 - v) * th)))
            dr[yy, xx] = tex[ty, tx]

Image.fromarray((np.clip(dr, 0, 1) * 255).astype(np.uint8)).save(
    WORK / "csref" / "_diag" / "knife_face_final.png")
print("wrote knife_face_final.png")
