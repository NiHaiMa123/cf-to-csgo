# -*- coding: utf-8 -*-
"""Render the CF-space idle viewmodel from CF's own camera (H^-1 of CS cam)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parents[1]
payload = __import__("json").loads((WORK / "decode" / "reference_payload.json").read_text(encoding="utf-8"))
skin = __import__("json").loads((WORK / "decode" / "cf_skin_kukri_spring.json").read_text(encoding="utf-8"))
vt = __import__("json").loads((WORK / "csref" / "viewmodel_transform.json").read_text(encoding="utf-8"))
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
HR = np.array(vt["H"]["rotation"])
HT = np.array(vt["H"]["translation"])
H = np.eye(4)
H[:3, :3] = HR * hs
H[:3, 3] = HT
Hinv = np.linalg.inv(H)

# CS camera: origin, forward -Y, up +Z, right -X. Map back to CF space.
cam_pos = (Hinv @ np.array([0, 0, 0, 1.0]))[:3]
fwd_cf = (Hinv[:3, :3] @ np.array([0, -1, 0]))
up_cf = (Hinv[:3, :3] @ np.array([0, 0, 1]))
right_cf = np.cross(fwd_cf, up_cf)
fwd_cf /= np.linalg.norm(fwd_cf)
up_cf /= np.linalg.norm(up_cf)
right_cf /= np.linalg.norm(right_cf)
print("CF cam pos", cam_pos.round(2), "fwd", fwd_cf.round(3), "up", up_cf.round(3), "right", right_cf.round(3))

# pose model at idle_0 frame0 in CF space
nodes = payload["nodes"]
B = {n["index"]: np.array(n["bind_world"]) for n in nodes}
par = {n["index"]: n["parent"] for n in nodes}
s0 = payload["clips"]["idle_0"]["samples"][0]
# world transform per node at frame0
W = {}
for n in nodes:
    i = n["index"]
    q = s0["quat_xyzw_world"][i]
    m = q2m(q)
    m[:3, 3] = s0["pos"][i]
    W[i] = m  # already world (sample stores world)

mesh = next(m for m in skin["meshes"] if m["name"] == "objObject03000")
V = np.array(mesh["vertices"], dtype=float).reshape(-1, 3)
UV = np.array(mesh["uvs"], dtype=float).reshape(-1, 2)
T = np.array(mesh["triangles"], dtype=int).reshape(-1, 3)
# knife rigid-bound to Box01 (47): posed = W47 @ inv(B47) @ v
GUN = 47
delta = W[GUN] @ np.linalg.inv(B[GUN])
PV = (delta @ np.hstack([V, np.ones((len(V), 1))]).T).T[:, :3]

# also arms? skip; knife only.
# project to CF camera
rel = PV - cam_pos
xc = rel @ right_cf   # right
yc = rel @ fwd_cf     # depth (positive = in front)
zc = rel @ up_cf      # up
SIZE = 640
F = 0.5 * SIZE / math.tan(math.radians(54) / 2)
CX = CY = SIZE / 2
arr = np.full((SIZE, SIZE, 3), (30, 30, 34), np.uint8)
zb = np.full((SIZE, SIZE), np.inf)
for t in T:
    scr, dep, uvs, ok = [], [], [], True
    for j in t:
        if yc[j] <= 0.05:
            ok = False
            break
        scr.append((CX + F * xc[j] / yc[j], CY - F * zc[j] / yc[j]))
        dep.append(yc[j])
        uvs.append(UV[j])
    if not ok:
        continue
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
            dd = w0 * dep[0] + w1 * dep[1] + w2 * dep[2]
            if dd >= zb[yy, xx]:
                continue
            zb[yy, xx] = dd
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            # CF texture sampling: raw v as image-top? try both visually later; use v direct
            ty = min(Ht - 1, int(v * (Ht - 1)))
            tx = min(Wt - 1, int(u * (Wt - 1)))
            arr[yy, xx] = tex[ty, tx]
Image.fromarray(arr).save(WORK / "csref" / "_diag" / "cf_native_view.png")
print("wrote cf_native_view.png")
print("knife CF-cam bbox x", xc.min().round(1), xc.max().round(1),
      "depth", yc.min().round(1), yc.max().round(1),
      "z", zc.min().round(1), zc.max().round(1))
