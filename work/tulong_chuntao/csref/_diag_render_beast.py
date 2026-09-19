# -*- coding: utf-8 -*-
"""Textured render of idle viewmodel — per-pixel UV sampling, compare with game."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parents[1]


def parse_smd(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes = {}
    frames = []
    tris = []
    mode = None
    cur = None
    cur_mat = None
    buf = []
    for ln in lines:
        s = ln.strip()
        if s == "nodes":
            mode = "n"; continue
        if s == "skeleton":
            mode = "s"; continue
        if s == "triangles":
            mode = "t"; continue
        if s == "end":
            if cur is not None:
                frames.append(cur); cur = None
            mode = None
            continue
        if mode == "n":
            name = s.split('"')[1]
            idx = int(s.split()[0])
            parent = int(s.rsplit('"', 1)[1])
            nodes[idx] = (name, parent)
        elif mode == "s":
            if s.startswith("time"):
                if cur is not None:
                    frames.append(cur)
                cur = {}
            else:
                p = s.split()
                cur[int(p[0])] = tuple(float(x) for x in p[1:7])
        elif mode == "t":
            p = s.split()
            try:
                bone = int(p[0])
            except (ValueError, IndexError):
                cur_mat = s
                buf = []
                continue
            pos = np.array([float(x) for x in p[1:4]])
            nrm = np.array([float(x) for x in p[4:7]])
            uv = np.array([float(x) for x in p[7:9]])
            nlinks = int(p[9]) if len(p) > 9 else 0
            links = [(int(p[10 + 2 * k]), float(p[11 + 2 * k])) for k in range(nlinks)] or [(bone, 1.0)]
            buf.append((cur_mat, pos, nrm, uv, links))
            if len(buf) == 3:
                tris.append(buf)
                buf = []
    return nodes, frames, tris


def euler_mat(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return np.array([
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx, 0],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx, 0],
        [-sy, cy * sx, cy * cx, 0],
        [0, 0, 0, 1],
    ])


def compose(nodes, frame):
    worlds = {}
    def world(i):
        if i in worlds:
            return worlds[i]
        pos = frame[i][:3]
        m = euler_mat(*frame[i][3:])
        m[:3, 3] = pos
        name, p = nodes[i]
        worlds[i] = m if p < 0 else world(p) @ m
        return worlds[i]
    for i in nodes:
        world(i)
    return worlds


def invert(m):
    r = m[:3, :3]
    t = m[:3, 3]
    out = np.eye(4)
    out[:3, :3] = r.T
    out[:3, 3] = -r.T @ t
    return out

SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
IDLE = WORK / "native_vm" / "source1" / "v_knife_anims" / "idle1.smd"
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast.png").convert("RGB")
HAND_TEX = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_HAND_Nini_GR.PNG"
).convert("RGB")
ARM_TEX = Image.open(
    WORK.parent / "galil_ace_tianxi" / "decode" / "nini_gr" / "FVIEW_ARM_Nini_GR.PNG"
).convert("RGB")
OUT = WORK / "csref" / "_diag"
OUT.mkdir(exist_ok=True)

TEXMAP = {
    "cf_kukri_beast": np.array(TEX),
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
    teximg = TEXMAP.get(mat, TEXMAP["cf_kukri_beast"])
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
