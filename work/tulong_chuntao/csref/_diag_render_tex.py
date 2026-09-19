# -*- coding: utf-8 -*-
"""Textured render of idle viewmodel — per-pixel UV sampling, compare with game."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK / "csref"))
from _diag_idle_view import parse_smd, compose, invert  # reuse parser

SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
IDLE = WORK / "native_vm" / "source1" / "v_knife_anims" / "idle1.smd"
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
HAND_TEX = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_HAND_Nini_GR.PNG"
).convert("RGB")
ARM_TEX = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_ARM_Nini_GR.PNG"
).convert("RGB")
OUT = WORK / "csref" / "_diag"
OUT.mkdir(exist_ok=True)

TEXMAP = {
    "cf_kukri_spring": np.array(TEX),
    "cf_nini_hand_gr": np.array(HAND_TEX),
    "cf_nini_arm_gr": np.array(ARM_TEX),
}

nodes, rest_frames, tris = parse_smd(SMD)
_, idle_frames, _ = parse_smd(IDLE)
rest_w = compose(nodes, rest_frames[0])
idle_w = compose(nodes, idle_frames[0])
rest_inv = {i: invert(rest_w[i]) for i in nodes}

posed = []
for tri in tris:
    out = []
    for mat, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        nacc = np.zeros(3)
        for b, w in links:
            if w <= 0:
                continue
            dw = idle_w[b] @ rest_inv[b]
            acc += w * (dw @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
            nacc += w * (dw[:3, :3] @ nrm)
        ln = np.linalg.norm(nacc) or 1.0
        out.append((mat, acc, nacc / ln, uv))
    posed.append(out)

SIZE = 1024
arr = np.full((SIZE, SIZE, 3), (30, 30, 34), dtype=np.uint8)
zbuf = np.full((SIZE, SIZE), np.inf)
FOV = 54.0
f = 0.5 * SIZE / math.tan(math.radians(FOV) / 2)
cx = cy = SIZE / 2


def sample_tex(teximg, u, v):
    h, w = teximg.shape[:2]
    x = int(np.clip(u * (w - 1), 0, w - 1))
    y = int(np.clip((1.0 - v) * (h - 1), 0, h - 1))
    return teximg[y, x]


for tri in posed:
    mat = tri[0][0]
    teximg = TEXMAP.get(mat, TEXMAP["cf_kukri_spring"])
    scr = []
    depths = []
    uvs = []
    behind = False
    for _m, p, n, uv in tri:
        if p[1] >= -0.2:
            behind = True
            break
        depth = -p[1]
        scr.append((cx - f * p[0] / depth, cy - f * p[2] / depth))
        depths.append(depth)
        uvs.append(uv)
    if behind:
        continue
    if any(s[0] < -SIZE or s[0] > 2 * SIZE or s[1] < -SIZE or s[1] > 2 * SIZE for s in scr):
        continue
    p0, p1, p2 = [np.asarray(s, dtype=float) for s in scr]
    minx = int(max(0, math.floor(min(p[0] for p in scr))))
    maxx = int(min(SIZE - 1, math.ceil(max(p[0] for p in scr))))
    miny = int(max(0, math.floor(min(p[1] for p in scr))))
    maxy = int(min(SIZE - 1, math.ceil(max(p[1] for p in scr))))
    if maxx <= minx or maxy <= miny:
        continue
    d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
    if abs(d) < 1e-9:
        continue
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            w0 = ((p1[1] - p2[1]) * (xx - p2[0]) + (p2[0] - p1[0]) * (yy - p2[1])) / d
            w1 = ((p2[1] - p0[1]) * (xx - p2[0]) + (p0[0] - p2[0]) * (yy - p2[1])) / d
            w2 = 1.0 - w0 - w1
            if w0 < -0.02 or w1 < -0.02 or w2 < -0.02:
                continue
            dep = w0 * depths[0] + w1 * depths[1] + w2 * depths[2]
            if dep >= zbuf[yy, xx]:
                continue
            u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
            v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
            zbuf[yy, xx] = dep
            arr[yy, xx] = sample_tex(teximg, u, v)

Image.fromarray(arr).save(OUT / "idle_textured.png")
print("wrote", OUT / "idle_textured.png")
