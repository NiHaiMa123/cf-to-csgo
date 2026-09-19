# -*- coding: utf-8 -*-
"""Diagnose kukri UV (raw vs 1-v) and current idle pose extents."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parents[1]
SKIN = json.loads((WORK / "decode" / "cf_skin_kukri_spring.json").read_text(encoding="utf-8"))
TEX = Image.open(WORK / "decode" / "PV-Kukri_Beast_spring.png").convert("RGB")
SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
VT = json.loads((WORK / "csref" / "viewmodel_transform.json").read_text(encoding="utf-8"))
OUT = WORK / "csref" / "_diag"
OUT.mkdir(exist_ok=True)

W, H = TEX.size
mesh = next(m for m in SKIN["meshes"] if m["name"] == "objObject03000")
uvs = np.array(mesh["uvs"], dtype=float).reshape(-1, 2)
tris = np.array(mesh["triangles"], dtype=int).reshape(-1, 3)
verts = np.array(mesh["vertices"], dtype=float).reshape(-1, 3)
print("knife verts", len(verts), "tris", len(tris))
print("uv raw  u", uvs[:, 0].min(), uvs[:, 0].max(), "v", uvs[:, 1].min(), uvs[:, 1].max())
print("uv 1-v  u", uvs[:, 0].min(), uvs[:, 0].max(), "v", (1 - uvs[:, 1]).min(), (1 - uvs[:, 1]).max())


def overlay(flip: bool, name: str):
    img = TEX.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    black_hits = 0
    pink_hits = 0
    blue_hits = 0
    samples = []
    for a, b, c in tris:
        pts = []
        cols = []
        for i in (a, b, c):
            u, v = uvs[i]
            if flip:
                v = 1.0 - v
            x = u * (W - 1)
            y = v * (H - 1)  # image y=0 is top; decoder V=0 is top if already image-top-left
            pts.append((x, y))
            px = TEX.getpixel((int(max(0, min(W - 1, x))), int(max(0, min(H - 1, y)))))
            cols.append(px)
        cx = sum(p[0] for p in pts) / 3
        cy = sum(p[1] for p in pts) / 3
        r, g, b = TEX.getpixel((int(max(0, min(W - 1, cx))), int(max(0, min(H - 1, cy)))))
        if r < 25 and g < 25 and b < 25:
            black_hits += 1
        elif r > g and r > 80:
            pink_hits += 1
        elif b > r and b > 80:
            blue_hits += 1
        samples.append((r, g, b))
        draw.line(pts + [pts[0]], fill=(0, 255, 0, 90), width=1)
    img.save(OUT / name)
    arr = np.array(samples)
    print(name, "black_tris", black_hits, "pink", pink_hits, "blue", blue_hits,
          "meanRGB", arr.mean(0).round(1).tolist())


overlay(False, "uv_raw_on_tex.png")
overlay(True, "uv_1minusv_on_tex.png")

# Source SMD uses V=0 at BOTTOM typically. PNG y=0 is TOP.
# If we write SMD uv=(u,1-v_raw) and VTFCmd stores PNG without extra semantic flip
# relative to SMD, then sampling PNG at y = (1-smd_v)*H = v_raw*H  -> image-top-left V.
# Overlay above with flip=True draws at y=(1-v_raw)*H.


def parse_smd_tris(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    mode = None
    cur_mat = None
    buf = []
    tris_out = []
    for ln in lines:
        s = ln.strip()
        if s == "triangles":
            mode = "t"
            continue
        if s == "end":
            mode = None
            continue
        if mode != "t":
            continue
        parts = s.split()
        try:
            bone = int(parts[0])
        except (ValueError, IndexError):
            cur_mat = s
            buf = []
            continue
        pos = [float(v) for v in parts[1:4]]
        uv = [float(v) for v in parts[7:9]]
        buf.append((cur_mat, pos, uv))
        if len(buf) == 3:
            tris_out.append(buf)
            buf = []
    return tris_out


smd_tris = parse_smd_tris(SMD)
knife = [t for t in smd_tris if t[0][0] == "cf_kukri_spring"]
hands = [t for t in smd_tris if t[0][0] != "cf_kukri_spring"]
print("smd knife tris", len(knife), "other", len(hands))


def bbox(tris):
    pts = np.array([v[1] for t in tris for v in t])
    return pts.min(0), pts.max(0), pts.mean(0)


kmin, kmax, kmean = bbox(knife)
print("knife bbox min", kmin.round(3), "max", kmax.round(3), "mean", kmean.round(3))
hmin, hmax, hmean = bbox(hands)
print("hands bbox min", hmin.round(3), "max", hmax.round(3), "mean", hmean.round(3))

# split left/right by x
hpts = np.array([v[1] for t in hands for v in t])
left = hpts[hpts[:, 0] < kmean[0]]
right = hpts[hpts[:, 0] >= kmean[0]]
for label, points in (("left hand", left), ("right hand", right)):
    if len(points):
        print(label, "n", len(points), "mean", points.mean(0).round(3),
              "minY", points[:, 1].min(), "maxY", points[:, 1].max())
    else:
        print(label, "n", 0)

# knife long axis from PCA of knife verts
kpts = np.array([v[1] for t in knife for v in t])
c = kpts.mean(0)
_, _, vt = np.linalg.svd(kpts - c)
print("knife PCA axes (rows):")
print(vt.round(3))
print("extent along PCA0", ((kpts - c) @ vt[0]).min(), ((kpts - c) @ vt[0]).max())

# SMD UV overlay: Source V=0 bottom. Draw onto PNG with y = (1-v)*H
img = TEX.copy()
draw = ImageDraw.Draw(img, "RGBA")
black = pink = blue = 0
for t in knife:
    pts = []
    for _mat, _pos, uv in t:
        x = uv[0] * (W - 1)
        y = (1.0 - uv[1]) * (H - 1)
        pts.append((x, y))
    cx = sum(p[0] for p in pts) / 3
    cy = sum(p[1] for p in pts) / 3
    r, g, b = TEX.getpixel((int(max(0, min(W - 1, cx))), int(max(0, min(H - 1, cy)))))
    if r < 25 and g < 25 and b < 25:
        black += 1
    elif r > g and r > 80:
        pink += 1
    elif b > r and b > 80:
        blue += 1
    draw.line(pts + [pts[0]], fill=(255, 255, 0, 90), width=1)
img.save(OUT / "uv_smd_as_source.png")
print("smd-as-source black", black, "pink", pink, "blue", blue)

# SMD UV overlay assuming SMD V already image-top (y=v*H)
img = TEX.copy()
draw = ImageDraw.Draw(img, "RGBA")
black = pink = blue = 0
for t in knife:
    pts = []
    for _mat, _pos, uv in t:
        x = uv[0] * (W - 1)
        y = uv[1] * (H - 1)
        pts.append((x, y))
    cx = sum(p[0] for p in pts) / 3
    cy = sum(p[1] for p in pts) / 3
    r, g, b = TEX.getpixel((int(max(0, min(W - 1, cx))), int(max(0, min(H - 1, cy)))))
    if r < 25 and g < 25 and b < 25:
        black += 1
    elif r > g and r > 80:
        pink += 1
    elif b > r and b > 80:
        blue += 1
    draw.line(pts + [pts[0]], fill=(0, 255, 255, 90), width=1)
img.save(OUT / "uv_smd_as_image_top.png")
print("smd-as-image-top black", black, "pink", pink, "blue", blue)

print("view_push_y", VT.get("view_push_y"), "apply_mirror", VT.get("apply_mirror"))
print("wrote", OUT)
