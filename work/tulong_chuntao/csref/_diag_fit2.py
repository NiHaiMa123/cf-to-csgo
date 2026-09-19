# -*- coding: utf-8 -*-
"""Fit view-model correction: R = T_grip @ R_axis(beta) @ R_yview(alpha) @ T_-grip
applied to raw view coords (after existing H/MX), plus push (px,py,pz).

alpha: screen-plane tilt about +Y (view fwd) -> sets blade's on-screen lean.
beta : roll about the (tilted) blade long axis -> brings flat side to +Y.
push : translation solved to place grip & match blade px length.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _diag_idle_view import parse_smd, compose, invert

WORK = Path(__file__).resolve().parents[1]
SMD = WORK / "native_vm" / "source1" / "cf_native_vm.smd"
IDLE = WORK / "native_vm" / "source1" / "v_knife_anims" / "idle1.smd"
W, H, FOV = 960, 540, 54.0
f = 0.5 * H / math.tan(math.radians(FOV / 2))

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}

PV, pm = [], []
for tri in tris:
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        PV.append(acc)
        pm.append(tri[0][0])
PV = np.array(PV)
kmask = np.array([m == "cf_kukri_spring" for m in pm])
KV = PV[kmask]

axis = np.linalg.svd(KV - KV.mean(0))[2][0]
if axis[2] < 0:
    axis = -axis

kt = [t for t in tris if t[0][0] == "cf_kukri_spring"]
P = []
for tri in kt:
    out = []
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        out.append(acc)
    P.append(out)
P = np.array(P)
nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
ar = np.linalg.norm(nrm, axis=1)
n = nrm / np.maximum(ar[:, None], 1e-12)
big = ar > np.median(ar) * 4
ref = n[big][np.argmax(ar[big])]
nA = n[big & (n @ ref > 0.5)].mean(0)
nB = n[big & (n @ ref < -0.5)].mean(0)
n_cam = nA if nA[1] > nB[1] else nB

HPTS = PV[~kmask]
d2 = ((KV[:, None, :] - HPTS[None, ::8, :]) ** 2).sum(-1)
grip = KV[d2.min(1) < 4.0].mean(0)
tip = KV[np.argmax(KV[:, 2])]
print(f"axis {axis.round(3)} grip {grip.round(2)} tip {tip.round(2)}")


def rot(axis_, deg):
    a = np.asarray(axis_, float); a /= np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) * math.cos(t) + (1 - math.cos(t)) * np.outer(a, a) + math.sin(t) * K


def project(p):
    return np.array([f * p[0] / p[1] + W / 2, f * p[2] / p[1] + H / 2])


# ref targets on 960x540
T_TIP = np.array([0.87 * W, 0.07 * H])
T_GRIP = np.array([0.80 * W, 0.87 * H])
T_DIR = T_TIP - T_GRIP
T_LEN = float(np.linalg.norm(T_DIR))
want_ang = math.degrees(math.atan2(T_DIR[0], -T_DIR[1]))  # deg right of vertical
print(f"target dir {T_DIR.round(0)} len {T_LEN:.0f} lean {want_ang:.1f}deg right of vertical")

Y = np.array([0, 1, 0.0])
best = None
for alpha in np.arange(-40, 41, 2.5):
    Ry = rot(Y, alpha)
    L = Ry @ axis
    t2 = Ry @ (tip - grip) + grip
    d2v = t2 - grip
    # projected blade dir angle from vertical (screen up = -y_px)
    sp = np.array([-d2v[0], d2v[2]])  # screen dir (x_px, up) since y const-ish
    ang = math.degrees(math.atan2(sp[0], sp[1]))
    if abs(ang - want_ang) > 6:
        continue
    # beta: roll about L to bring n_cam -> +Y
    nc = Ry @ n_cam
    np_perp = nc - (nc @ L) * L
    yp = Y - (Y @ L) * L
    np_perp /= np.linalg.norm(np_perp)
    yp /= np.linalg.norm(yp)
    beta = math.degrees(math.atan2(float(np.cross(np_perp, yp) @ L), float(np_perp @ yp)))
    R = rot(L, beta) @ Ry
    g2 = grip.copy()  # pivot at grip
    t2 = R @ (tip - grip) + grip
    # depth solve for px len
    def pxlen(dy):
        off = np.array([0.0, dy, 0.0])
        return np.linalg.norm(project(t2 + off) - project(g2 + off))
    lo, hi = -25.0, 25.0  # dy range; yv = g2[1]+dy must stay < -4
    for _ in range(50):
        mid = (lo + hi) / 2
        if pxlen(mid) > T_LEN:
            hi = mid
        else:
            lo = mid
    dy = (lo + hi) / 2
    yv = g2[1] + dy  # signed view y (negative)
    gp = project(g2 + np.array([0, dy, 0]))
    dpx = gp - T_GRIP
    px = -dpx[0] * yv / f  # dsx = f*px/yv ; want dsx = -dpx0
    pz = -dpx[1] * yv / f
    push = np.array([px, dy, pz])
    allp = (R @ (PV.T - grip[:, None])).T + grip + push
    nc2 = R @ n_cam
    kscr = np.array([project(p) for p in allp[kmask][::5]])
    hscr = np.array([project(p) for p in allp[~kmask][::11] if p[1] < -0.5])
    tfin = project(R @ (tip - grip) + grip + push)
    gfin = project(grip + push)
    ok_h = (hscr[:, 0].min() > -300) and (hscr[:, 1].max() < 1200)
    print(f"a={alpha:+.1f} b={beta:+.1f} push={push.round(2)} nY={nc2[1]:+.2f} "
          f"tip{tfin.round(0)} grip{gfin.round(0)} "
          f"kx[{kscr[:,0].min():.0f},{kscr[:,0].max():.0f}] ky[{kscr[:,1].min():.0f},{kscr[:,1].max():.0f}] "
          f"hx[{hscr[:,0].min():.0f},{hscr[:,0].max():.0f}] hy[{hscr[:,1].min():.0f},{hscr[:,1].max():.0f}]")
