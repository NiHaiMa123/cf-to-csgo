# -*- coding: utf-8 -*-
"""Debug preview: project post-VIEW verts into the eye-space image plane.

Renders (a) CF gun pieces, (b) Nini arm verts, (c) stock glock verts for
reference, from the eye at origin looking down -Y. Lets us SEE the fitted
viewmodel without launching the game.
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

W_IMG, H_IMG, FOCAL = 960, 720, 700.0  # ~50deg vfov


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


def blit(img, pts, color, r=1):
    d = ImageDraw.Draw(img)
    f = pts[pts[:, 1] < -0.5]
    sx = W_IMG / 2 + f[:, 0] / (-f[:, 1]) * FOCAL
    sy = H_IMG / 2 - f[:, 2] / (-f[:, 1]) * FOCAL
    for x, y in zip(sx, sy):
        if 0 <= x < W_IMG and 0 <= y < H_IMG:
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)


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

    body_v, pieces_v = [], []
    for m in skin["meshes"]:
        ni = PIECE_NODE.get(m["name"])
        if ni is None:
            continue
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        pts = xf(D, np.array(m["vertices"]).reshape(-1, 3))
        (body_v if m["name"] == "PV-Mauser_Libra" else pieces_v).append(pts)
    gun_cf = np.concatenate(body_v)
    gun_h = xf(H, gun_cf)
    xc = float((gun_h[:, 0].min() + gun_h[:, 0].max()) / 2)
    MX = np.array([[-1., 0, 0, 2 * xc], [0, 1, 0, 0], [0, 0, 1, 0],
                   [0, 0, 0, 1]])
    E = MX @ H

    VIEW = np.array(vt["view_matrix"]) if vt.get("view_matrix") else np.eye(4)

    # arm verts reposed exactly like the builder (B @ inv(BARM))
    armdump = json.loads((_REPO / "work/galil_ace_tianxi/decode/nini_gr/"
                          "cf_skin_nini_gr.json").read_text())
    name2idx = {n["name"]: n["index"] for n in nodes}
    B = {n["index"]: np.array(n["bind_world"]) for n in nodes}
    BARM = {name2idx[n["name"]]: np.array(n["bind_matrix"]).reshape(4, 4)
            for n in armdump["skeleton"] if n["name"] in name2idx}
    BARM_INV = {i: np.linalg.inv(m) for i, m in BARM.items()}
    arm_names = [n["name"] for n in armdump["skeleton"]]
    armv = []
    for m in armdump["meshes"]:
        bw, bi = m["bone_weights"], m["bone_indices"]
        for vi in range(m["vertex_count"]):
            v = np.array(m["vertices"][3 * vi:3 * vi + 3])
            ws = list(bw[3 * vi:3 * vi + 3])
            ws.append(max(0.0, 1 - sum(ws)))
            acc = np.zeros(3)
            for ni, w in zip(bi[4 * vi:4 * vi + 4], ws):
                if ni == 255 or ni >= len(arm_names) or w <= 1e-6:
                    continue
                an = arm_names[ni]
                if an not in name2idx or name2idx[an] not in BARM_INV:
                    continue
                pi = name2idx[an]
                acc += w * xf(W[pi] @ BARM_INV[pi], v.reshape(1, 3))[0]
            armv.append(acc)
    arm_eye = xf(VIEW @ E, np.array(armv))
    gun_eye = xf(VIEW @ E, gun_cf)
    pieces_eye = xf(VIEW @ E, np.concatenate(pieces_v))

    # stock glock verts posed to idle f0 via dominant-bone delta
    model = parse_smd(CSREF / "glock18_model.smd")
    mw = compose_worlds(model["nodes"], model["frames"][0])
    idle = parse_smd(CSREF / "v_pist_glock18_anims" / "glock_idle.smd")
    iw = compose_worlds(idle["nodes"], idle["frames"][0])
    lines = (CSREF / "glock18_model.smd").read_text().splitlines()
    vs, mode = [], False
    for ln in lines:
        st = ln.strip()
        if st == "triangles":
            mode = True
            continue
        if st == "end":
            if mode:
                break
            continue
        if mode:
            f = st.split()
            try:
                vs.append((int(f[0]), [float(f[1]), float(f[2]), float(f[3])]))
            except (ValueError, IndexError):
                pass
    sv = []
    for b, p in vs:
        if b not in {3, 4, 5, 6, 7, 8, 27, 28}:
            continue
        D = np.array(iw[b]) @ np.linalg.inv(np.array(mw[b]))
        sv.append((D @ np.append(p, 1.0))[:3])
    sv = np.array(sv)

    img = Image.new("RGB", (W_IMG, H_IMG), (18, 18, 24))
    blit(img, sv, (120, 40, 40), 1)          # stock gun: dark red
    blit(img, pieces_eye, (60, 140, 220), 1)  # constellation/reload parts: blue
    blit(img, arm_eye, (200, 200, 200), 1)   # arms: white
    blit(img, gun_eye, (255, 200, 60), 2)    # CF gun: gold
    d = ImageDraw.Draw(img)
    d.line([W_IMG / 2 - 12, H_IMG / 2, W_IMG / 2 + 12, H_IMG / 2], fill=(0, 255, 0))
    d.line([W_IMG / 2, H_IMG / 2 - 12, W_IMG / 2, H_IMG / 2 + 12], fill=(0, 255, 0))
    out = WORK / "csref" / "preview.png"
    img.save(out)
    print("wrote", out)
    print("gun eye bbox", gun_eye.min(0).round(2), gun_eye.max(0).round(2))
    print("arm eye bbox", arm_eye.min(0).round(2), arm_eye.max(0).round(2))


if __name__ == "__main__":
    sys.exit(main())
