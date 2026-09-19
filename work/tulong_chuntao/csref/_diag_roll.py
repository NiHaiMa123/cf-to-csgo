# -*- coding: utf-8 -*-
"""Compute blade long axis, flat normal, grip pivot in SMD bind space & idle space."""
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

nodes, rest, tris = parse_smd(SMD)
_, idle, _ = parse_smd(IDLE)
rw = compose(nodes, rest[0])
iw = compose(nodes, idle[0])
rinv = {i: invert(rw[i]) for i in nodes}
knife = [t for t in tris if t[0][0] == "cf_kukri_spring"]

# knife rigid to one bone (check)
bone_ids = set()
for t in knife:
    for _m, p, n, uv, links in t:
        for b, w in links:
            bone_ids.add(b)
print("knife link bones:", bone_ids)

posed = []
bindv = []
for tri in knife:
    out = []
    for _m, pos, nrm, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            dw = iw[b] @ rinv[b]
            acc += w * (dw @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        out.append((acc, uv, np.asarray(pos)))
        bindv.append(np.asarray(pos))
    posed.append(out)

bindv = np.array(bindv)
PV = np.array([v[0] for t in posed for v in t])

# blade long axis via PCA on posed verts
c = PV.mean(0)
_, sv, vt3 = np.linalg.svd(PV - c)
axis = vt3[0]
print("idle knife PCA axis", axis.round(3), "sv", sv.round(1))

# flat-side normals: biggest-area tris
P = np.array([[v[0] for v in t] for t in posed])
nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
area = np.linalg.norm(nrm, axis=1)
n = nrm / np.maximum(area[:, None], 1e-12)
big = area > np.median(area) * 4
ref = n[big][np.argmax(area[big])]
for sign in (+1, -1):
    sel = big & ((n @ ref) * sign > 0.5)
    if sel.sum():
        print(f"side{'A' if sign>0 else 'B'} mean n {n[sel].mean(0).round(3)} ntris {sel.sum()}")

# grip point = knife verts closest to hand cluster (hands mean pos)
hand_pts = np.array([v[1] for t in tris if t[0][0] != "cf_kukri_spring" for v in
                     [(0, np.zeros(3), 0, 0, [(b, w) for b, w in v[4]]) for v in []]])
# simpler: take posed hand verts
hposed = []
for tri in tris:
    if tri[0][0] == "cf_kukri_spring":
        continue
    for _m, pos, nrm2, uv, links in tri:
        acc = np.zeros(3)
        for b, w in links:
            dw = iw[b] @ rinv[b]
            acc += w * (dw @ np.array([pos[0], pos[1], pos[2], 1.0]))[:3]
        hposed.append(acc)
hposed = np.array(hposed)
# grip = knife verts nearest to right-side hand cluster
# knife verts distances to nearest hand vert
from scipy.spatial import cKDTree
tree = cKDTree(hposed)
d, idx = tree.query(PV)
grip_mask = d < 2.0
print("knife verts near hands:", grip_mask.sum(), "of", len(PV))
grip = PV[grip_mask].mean(0) if grip_mask.sum() else PV.min(0)
print("grip point (posed):", grip.round(3))
print("knife posed bbox min", PV.min(0).round(2), "max", PV.max(0).round(2))

# bind-space axis/pivot: transform back via gun bone delta
gb = list(bone_ids)[0]
D = iw[gb] @ rinv[gb]
Dinv = np.linalg.inv(D)
axis_bind = Dinv[:3, :3] @ axis
axis_bind /= np.linalg.norm(axis_bind)
grip_bind = (Dinv @ np.array([*grip, 1.0]))[:3]
print("bind axis", axis_bind.round(3), "grip_bind", grip_bind.round(3))

# flat normals in bind space for the big tris
PB = bindv.reshape(-1, 3, 3)
nrb = np.cross(PB[:, 1] - PB[:, 0], PB[:, 2] - PB[:, 0])
areab = np.linalg.norm(nrb, axis=1)
nb = nrb / np.maximum(areab[:, None], 1e-12)
bigb = areab > np.median(areab) * 4
refb = nb[bigb][np.argmax(areab[bigb])]
for sign in (+1, -1):
    sel = bigb & ((nb @ refb) * sign > 0.5)
    if sel.sum():
        nvb = nb[sel].mean(0)
        # map to idle space
        nvi = D[:3, :3] @ nvb
        nvi /= np.linalg.norm(nvi)
        print(f"bind side{'A' if sign>0 else 'B'} n_bind {nvb.round(3)} -> idle n {nvi.round(3)}")
