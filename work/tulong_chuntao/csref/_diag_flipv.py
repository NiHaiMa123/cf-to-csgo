# -*- coding: utf-8 -*-
"""Render full idle viewmodel with knife UV flipped (v_smd = 1-v_raw) vs current."""
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
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
HAND = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_HAND_Nini_GR.png").convert("RGB")
ARM = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_ARM_Nini_GR.png").convert("RGB")
TEXMAP = {
    "cf_kukri_spring": np.array(TEX),
    "cf_nini_hand_gr": np.array(HAND),
    "cf_nini_arm_gr": np.array(ARM),
}

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

posed = []
for tri in tris:
    out = []
    for mat, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            dw = iw[b] @ rinv[b]
            acc += w * (dw @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        out.append((mat, acc, uv))
    posed.append(out)

SIZE = 640
F = 0.5 * SIZE / math.tan(math.radians(54) / 2)
CX = CY = SIZE / 2


def raster(name, flip_knife):
    arr = np.full((SIZE, SIZE, 3), (30, 30, 34), np.uint8)
    zb = np.full((SIZE, SIZE), np.inf)
    for t in posed:
        mat = t[0][0]
        tex = TEXMAP[mat]
        Ht, Wt = tex.shape[:2]
        scr, dep, uvs, ok = [], [], [], True
        for _m, p, uv in t:
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
                if flip_knife and mat == "cf_kukri_spring":
                    v = 1.0 - v
                ty = min(Ht - 1, int((1 - v) * (Ht - 1)))
                tx = min(Wt - 1, int(u * (Wt - 1)))
                arr[yy, xx] = tex[ty, tx]
    Image.fromarray(arr).save(WORK / "csref" / "_diag" / name)


raster("vm_current.png", False)
raster("vm_flipv.png", True)
print("done")
