# -*- coding: utf-8 -*-
"""Rasterize idle knife+hands from CS viewmodel camera (origin, look -Y)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parents[1]
SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
IDLE = WORK / "native_vm" / "source1" / "v_knife_anims" / "idle1.smd"
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
OUT = WORK / "csref" / "_diag"
Wtex, Htex = TEX.size
tex = np.array(TEX)


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
            hp = dw @ np.array([pos[0], pos[1], pos[2], 1.0])
            hn = dw[:3, :3] @ nrm
            acc += w * hp[:3]
            nacc += w * hn
        ln = np.linalg.norm(nacc) or 1.0
        out.append((mat, acc, nacc / ln, uv))
    posed.append(out)

# bbox by material
from collections import defaultdict
bags = defaultdict(list)
for tri in posed:
    for mat, p, n, uv in tri:
        bags[mat].append(p)
for mat, pts in bags.items():
    a = np.array(pts)
    print(mat, "n", len(a), "min", a.min(0).round(3), "max", a.max(0).round(3), "mean", a.mean(0).round(3))

knife = [t for t in posed if t[0][0] == "cf_kukri_spring"]
kpts = np.array([v[1] for t in knife for v in t])
c = kpts.mean(0)
_, _, vt = np.linalg.svd(kpts - c)
print("idle knife PCA")
print(vt.round(3))
print("knife mean", c.round(3), "extent PCA0", ((kpts - c) @ vt[0]).min(), ((kpts - c) @ vt[0]).max())

# facing: camera looks -Y, towards camera is +Y
cam_facing = 0
cam_away = 0
pink = blue = black = 0
for t in knife:
    p0, p1, p2 = (t[0][1], t[1][1], t[2][1])
    fn = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(fn) or 1.0
    fn = fn / ln
    # Source samples V=0 at bottom of PNG => y = (1-v)*H
    uvs = [v[3] for v in t]
    cu, cv = np.mean(uvs, 0)
    x = int(np.clip(cu * (Wtex - 1), 0, Wtex - 1))
    y = int(np.clip((1.0 - cv) * (Htex - 1), 0, Htex - 1))
    r, g, b = tex[y, x]
    if fn[1] > 0:
        cam_facing += 1
        if r < 25 and g < 25 and b < 25:
            black += 1
        elif r > g and r > 80:
            pink += 1
        elif b > r and b > 80:
            blue += 1
    else:
        cam_away += 1
print("knife tris facing camera(+Y)", cam_facing, "away", cam_away,
      "facing colors black", black, "pink", pink, "blue", blue)


def render_dots(path, size=640, fov_y=54.0, only_knife=False):
    img = Image.new("RGB", (size, size), (24, 24, 24))
    draw = ImageDraw.Draw(img)
    f = 0.5 * size / math.tan(math.radians(fov_y) / 2)
    cx = cy = size / 2
    order = posed if not only_knife else knife
    order = sorted(order, key=lambda t: -(t[0][1][1] + t[1][1][1] + t[2][1][1]) / 3)
    for tri in order:
        scr = []
        cols = []
        skip = False
        for mat, p, n, uv in tri:
            if p[1] >= -0.2:
                skip = True
                break
            depth = -p[1]
            sx = cx + f * p[0] / depth
            sy = cy - f * p[2] / depth
            scr.append((sx, sy))
            tx = int(np.clip(uv[0] * (Wtex - 1), 0, Wtex - 1))
            ty = int(np.clip((1.0 - uv[1]) * (Htex - 1), 0, Htex - 1))
            col = tuple(int(x) for x in tex[ty, tx])
            if mat != "cf_kukri_spring":
                col = (170, 170, 170)
            cols.append(col)
        if skip or any(s[0] < -50 or s[0] > size + 50 or s[1] < -50 or s[1] > size + 50 for s in scr):
            continue
        fill = tuple(int(sum(c[i] for c in cols) / 3) for i in range(3))
        draw.polygon(scr, fill=fill, outline=fill)
    img.save(path)
    print("wrote", path)


render_dots(OUT / "idle_view.png", only_knife=False)
render_dots(OUT / "idle_knife.png", only_knife=True)

pink_n = []
blue_n = []
for t in knife:
    p0, p1, p2 = t[0][1], t[1][1], t[2][1]
    fn = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(fn) or 1.0
    fn = fn / ln
    cu, cv = np.mean([v[3] for v in t], 0)
    x = int(np.clip(cu * (Wtex - 1), 0, Wtex - 1))
    y = int(np.clip((1.0 - cv) * (Htex - 1), 0, Htex - 1))
    r, g, b = tex[y, x]
    area = ln
    if r > g and r > 80:
        pink_n.append((fn, area))
    elif b > r and b > 80:
        blue_n.append((fn, area))


def mean_n(items):
    if not items:
        return None
    acc = np.zeros(3)
    wsum = 0.0
    for n, w in items:
        acc += w * n
        wsum += w
    v = acc / (wsum or 1.0)
    return v / (np.linalg.norm(v) or 1.0)

pn, bn = mean_n(pink_n), mean_n(blue_n)
print("pink face mean n", None if pn is None else pn.round(3), "n=", len(pink_n))
print("blue face mean n", None if bn is None else bn.round(3), "n=", len(blue_n))
if pn is not None:
    # camera toward model is +Y; want pink n aligned with +Y (towards camera)
    print("pink n·+Y", float(pn[1]), "angle_from_cam_deg", math.degrees(math.acos(max(-1, min(1, pn[1])))))
if bn is not None:
    print("blue n·+Y", float(bn[1]), "angle_from_cam_deg", math.degrees(math.acos(max(-1, min(1, bn[1])))))
print("done")
