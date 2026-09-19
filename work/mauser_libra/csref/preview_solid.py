# -*- coding: utf-8 -*-
"""Solid preview: painter's-algorithm flat-shaded tris in eye space.

Compare CF gun (idle_0 f0, post-VIEW) vs stock glock (idle f0) side by side.
Eye at origin looking down -Y; screen x = right, screen y = up.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "mauser_libra"
CSREF = WORK / "csref" / "decompiled_stock" / "v_pist_glock18"
sys.path.insert(0, str(WORK / "csref"))
from fit_transform import PIECE_NODE, parse_smd, compose_worlds  # noqa: E402

W_IMG, H_IMG, FOCAL = 960, 720, 700.0
LIGHT = np.array([0.4, 0.6, 0.7])
LIGHT /= np.linalg.norm(LIGHT)


def quat_worlds(nodes, sample):
    W = []
    for i in range(len(nodes)):
        x, y, z, w = sample["quat_xyzw_world"][i]
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ])
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = sample["pos"][i]
        W.append(M)
    return W


def xf(M, P):
    h = np.concatenate([P, np.ones((len(P), 1))], 1)
    return (M @ h.T).T[:, :3]


def render(img, verts, tris, base, side=False):
    d = ImageDraw.Draw(img)
    order = []
    for t in range(0, len(tris), 3):
        a, b, c = tris[t:t + 3]
        key = (verts[a][0] + verts[b][0] + verts[c][0]) if side else \
            (verts[a][1] + verts[b][1] + verts[c][1])
        order.append((key, a, b, c))
    order.sort()
    for _, a, b, c in order:
        pa, pb, pc = (np.asarray(verts[a]), np.asarray(verts[b]),
                      np.asarray(verts[c]))
        if pa[1] > -0.5 or pb[1] > -0.5 or pc[1] > -0.5:
            continue
        n = np.cross(pb - pa, pc - pa)
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n /= ln
        s = 0.35 + 0.65 * abs(float(np.dot(n, LIGHT)))
        col = tuple(min(255, int(v * s)) for v in base)
        pts = []
        for p in (pa, pb, pc):
            if side:
                pts.append((W_IMG / 2 - p[1] * 18.0,  # -y -> right (depth)
                            H_IMG / 2 - p[2] * 18.0))  # z -> up
            else:
                pts.append((W_IMG / 2 + p[0] / (-p[1]) * FOCAL,
                            H_IMG / 2 - p[2] / (-p[1]) * FOCAL))
        d.polygon(pts, fill=col)


def smd_tris_verts(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    verts, tris, mode = [], [], False
    cur = []
    for ln in lines:
        s = ln.strip()
        if s == "triangles":
            mode = True
            continue
        if s == "end":
            if mode:
                break
            continue
        if mode:
            f = s.split()
            try:
                verts.append((int(f[0]),
                              [float(f[1]), float(f[2]), float(f[3])]))
                cur.append(len(verts) - 1)
            except (ValueError, IndexError):
                cur = []
            if len(cur) == 3:
                tris.extend(cur)
                cur = []
    return verts, tris


def main():
    payload = json.loads((WORK / "decode/reference_payload.json").read_text())
    skin = json.loads((WORK / "decode/cf_skin_m1896_libra.json").read_text())
    vt = json.loads((WORK / "csref/viewmodel_transform.json").read_text())
    nodes = payload["nodes"]
    s = float(vt["H"]["scale"])
    R = np.array(vt["H"]["rotation"], float)
    t = np.array(vt["H"]["translation"], float)
    H = np.eye(4); H[:3, :3] = s * R; H[:3, 3] = t
    s0 = payload["clips"]["idle_0"]["samples"][0]
    W = quat_worlds(nodes, s0)

    body_v, body_t, piece_v, piece_t = [], [], [], []
    for m in skin["meshes"]:
        ni = PIECE_NODE.get(m["name"])
        if ni is None:
            continue
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        pts = xf(D, np.array(m["vertices"]).reshape(-1, 3))
        if m["name"] == "PV-Mauser_Libra":
            base = len(body_v)
            body_v.extend(pts.tolist())
            body_t.extend([base + i for i in m["triangles"]])
        else:
            base = len(piece_v)
            piece_v.extend(pts.tolist())
            piece_t.extend([base + i for i in m["triangles"]])
    gun_cf = np.array(body_v)
    gun_h = xf(H, gun_cf)
    xc = float((gun_h[:, 0].min() + gun_h[:, 0].max()) / 2)
    MX = np.array([[-1., 0, 0, 2 * xc], [0, 1, 0, 0], [0, 0, 1, 0],
                   [0, 0, 0, 1]])
    E = MX @ H
    VIEW = np.array(vt["view_matrix"]) if vt.get("view_matrix") else np.eye(4)
    gun_eye = xf(VIEW @ E, gun_cf)
    piece_eye = xf(VIEW @ E, np.array(piece_v))

    # stock glock, posed to idle f0 via dominant-bone delta
    model = parse_smd(CSREF / "glock18_model.smd")
    mw = compose_worlds(model["nodes"], model["frames"][0])
    idle = parse_smd(CSREF / "v_pist_glock18_anims" / "glock_idle.smd")
    iw = compose_worlds(idle["nodes"], idle["frames"][0])
    sverts, stris = smd_tris_verts(CSREF / "glock18_model.smd")
    sp = np.zeros((len(sverts), 3))
    for i, (b, p) in enumerate(sverts):
        if b in {3, 4, 5, 6, 7, 8, 27, 28}:
            D = np.array(iw[b]) @ np.linalg.inv(np.array(mw[b]))
            sp[i] = (D @ np.append(p, 1.0))[:3]
        else:
            sp[i] = [0, 1e6, 0]  # park arm verts far away
    # shift stock to screen-right for comparison
    spx = sp + np.array([-6.0, 0.0, 0.0])

    img = Image.new("RGB", (W_IMG, H_IMG), (18, 18, 24))
    render(img, [tuple(v) for v in spx], stris, (150, 60, 60))
    render(img, [tuple(v) for v in piece_eye], piece_t, (70, 130, 220))
    render(img, [tuple(v) for v in gun_eye], body_t, (240, 190, 70))
    d = ImageDraw.Draw(img)
    d.line([W_IMG / 2 - 14, H_IMG / 2, W_IMG / 2 + 14, H_IMG / 2], fill=(0, 255, 0))
    d.line([W_IMG / 2, H_IMG / 2 - 14, W_IMG / 2, H_IMG / 2 + 14], fill=(0, 255, 0))
    out = WORK / "csref" / "preview_solid.png"
    img.save(out)
    print("wrote", out)

    # side profile: depth -y -> right, z -> up; eye at left edge
    img2 = Image.new("RGB", (W_IMG, H_IMG), (18, 18, 24))
    render(img2, [tuple(v) for v in sp], stris, (150, 60, 60), side=True)
    render(img2, [tuple(v) for v in gun_eye], body_t, (240, 190, 70), side=True)
    d2 = ImageDraw.Draw(img2)
    d2.line([0, H_IMG / 2, W_IMG, H_IMG / 2], fill=(0, 200, 0))
    d2.line([W_IMG / 2, 0, W_IMG / 2, H_IMG], fill=(60, 60, 60))
    out2 = WORK / "csref" / "preview_side.png"
    img2.save(out2)
    print("wrote", out2)


if __name__ == "__main__":
    sys.exit(main())
