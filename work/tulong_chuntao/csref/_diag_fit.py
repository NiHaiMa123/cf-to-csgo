# -*- coding: utf-8 -*-
"""Fit axis-roll + push so the posed viewmodel matches CF reference framing.

Targets measured on cf_ref2/cf_ref3 (640x480, we use 960x540 same FOV 54):
  - blade tip ~ (0.86W, 0.08H), grip ~ (0.80W, 0.85H)  -> blade at right edge,
    flat side frontal, tip up.
  - left hand low at bottom-left.
Solves: for each candidate roll, depth y chosen so blade length matches ref
(~0.75H px), then push_x/push_z to place grip. Reports resulting screen box.
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


def pose_all():
    pv, pm = [], []
    for tri in tris:
        for _m, pos, nrm, uv, links in tri:
            acc = np.zeros(3)
            for b, w in links:
                acc += w * (iw[b] @ rinv[b] @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
            pv.append(acc)
            pm.append(tri[0][0])
    return np.array(pv), np.array([m == "cf_kukri_spring" for m in pm])


PV, kmask = pose_all()
KV = PV[kmask]
axis = np.linalg.svd(KV - KV.mean(0))[2][0]
if axis[2] < 0:
    axis = -axis

# flat-side normal
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

np_perp = n_cam - (n_cam @ axis) * axis
yp = np.array([0, 1, 0.0]) - (np.array([0, 1, 0.0]) @ axis) * axis
np_perp /= np.linalg.norm(np_perp)
yp /= np.linalg.norm(yp)
theta_full = math.degrees(math.atan2(float(np.cross(np_perp, yp) @ axis),
                                     float(np_perp @ yp)))

HPTS = PV[~kmask]
d2 = ((KV[:, None, :] - HPTS[None, ::8, :]) ** 2).sum(-1)
grip = KV[d2.min(1) < 4.0].mean(0)
tip = KV[np.argmax(KV[:, 2])]  # highest point
blen = float(np.linalg.norm(tip - grip))
print(f"axis {axis.round(3)} theta_full {theta_full:.1f} grip {grip.round(2)} tip {tip.round(2)} blen {blen:.2f}")

def rot(axis, deg):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) * math.cos(t) + (1 - math.cos(t)) * np.outer(a, a) + math.sin(t) * K


def project(p):
    return np.array([-f * p[0] / p[1] + W / 2, f * p[2] / p[1] + H / 2])


# ref targets (960x540)
T_TIP = np.array([0.86 * W, 0.10 * H])
T_GRIP = np.array([0.80 * W, 0.86 * H])
T_LEN = float(np.linalg.norm(T_TIP - T_GRIP))

print(f"\nref blade px len {T_LEN:.0f}")
for deg in range(30, 75, 5):
    R = rot(axis, deg)
    g2 = R @ (grip - grip) + grip  # pivot at grip -> grip fixed
    t2 = R @ (tip - grip) + grip
    # depth so projected length matches
    y_g = -g2[1]  # grip depth positive
    # solve depth scale: len_px = f*|d_perp|/y roughly; use exact 2pt solve
    # try candidate dy added to current y
    def pxlen(dy):
        return np.linalg.norm(project(t2 + np.array([0, -dy, 0])) - project(g2 + np.array([0, -dy, 0])))
    lo, hi = -30.0, 30.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if pxlen(mid) > T_LEN:
            lo = mid
        else:
            hi = mid
    dy = (lo + hi) / 2
    off = np.array([0.0, -dy, 0.0])
    gp = project(g2 + off)
    tp = project(t2 + off)
    # remaining push_x/z to move grip to target: screen delta -> view delta
    dpx = gp - T_GRIP  # how much we need to move (screen px)
    # dx_view = -dpx_x * y / f ; dz_view = +dpx_y * y / f
    ydep = -(g2[1] + off[1])
    push = np.array([dpx[0] * ydep / f, -dy, dpx[1] * ydep / f])
    allp = (R @ (PV.T - grip[:, None])).T + grip + push
    km = allp[kmask]
    hm = allp[~kmask]
    kscr = np.array([project(p) for p in km[::7]])
    hscr = np.array([project(p) for p in hm[::17]])
    print(f"deg {deg}: push {push.round(2)} tip {tp.round(0)} grip {gp.round(0)} "
          f"knife x[{kscr[:,0].min():.0f},{kscr[:,0].max():.0f}] y[{kscr[:,1].min():.0f},{kscr[:,1].max():.0f}] "
          f"hands x[{hscr[:,0].min():.0f},{hscr[:,0].max():.0f}] y[{hscr[:,1].min():.0f},{hscr[:,1].max():.0f}]")
