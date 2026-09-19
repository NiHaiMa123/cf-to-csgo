# -*- coding: utf-8 -*-
"""Find blade flat-side normal in CF space, its UV island, and where it ends up in view space."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parents[1]
import json

skin = json.loads((WORK / "decode" / "cf_skin_kukri_spring.json").read_text(encoding="utf-8"))
payload = json.loads((WORK / "decode" / "reference_payload.json").read_text(encoding="utf-8"))
vt = json.loads((WORK / "csref" / "viewmodel_transform.json").read_text(encoding="utf-8"))

mesh = next(m for m in skin["meshes"] if m["name"] == "objObject03000")
V = np.array(mesh["vertices"], dtype=float).reshape(-1, 3)
UV = np.array(mesh["uvs"], dtype=float).reshape(-1, 2)
T = np.array(mesh["triangles"], dtype=int).reshape(-1, 3)

# CF-space face normals + area
nrm = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
area = np.linalg.norm(nrm, axis=1)
n = nrm / np.maximum(area[:, None], 1e-12)

# biggest-area tris = flat sides
order = np.argsort(-area)
print("top-20 area tris normals & uv centroids:")
for i in order[:20]:
    cu, cv = UV[T[i]].mean(0)
    print(f"  tri{i} area={area[i]:.1f} n={n[i].round(3)} uv=({cu:.3f},{cv:.3f})")

# cluster flat-side normals: pick tris with area>median*4
big = area > np.median(area) * 4
print("big tris:", big.sum(), "of", len(T))
# two flat sides should have opposing normals
ref = n[order[0]]
sideA = big & (n @ ref > 0.5)
sideB = big & (n @ ref < -0.5)
print("sideA tris", sideA.sum(), "mean n", n[sideA].mean(0).round(3))
print("sideB tris", sideB.sum(), "mean n", n[sideB].mean(0).round(3))
for label, mask in (("A", sideA), ("B", sideB)):
    if mask.sum():
        uvs = UV[T[mask]].reshape(-1, 2)
        print(f"side{label} uv u[{uvs[:,0].min():.3f},{uvs[:,0].max():.3f}] "
              f"v[{uvs[:,1].min():.3f},{uvs[:,1].max():.3f}] "
              f"mean({uvs[:,0].mean():.3f},{uvs[:,1].mean():.3f})")

# Transform flat-side normals into view space: anim world = VIEW*MX*H*w*H^-1*MX
def q2m(q):
    x, y, z, w = q
    nn = math.sqrt(x * x + y * y + z * z + w * w) or 1
    x, y, z, w = x / nn, y / nn, z / nn, w / nn
    m = np.eye(4)
    m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                 [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                 [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return m

hs = vt["H"]["scale"]
HR = np.array(vt["H"]["rotation"])
HT = np.array(vt["H"]["translation"])
H = np.eye(4); H[:3, :3] = HR * hs; H[:3, 3] = HT
Hinv = np.linalg.inv(H)
GUN_XC = vt["gun_center_x"]
MX = np.eye(4); MX[0, 0] = -1; MX[0, 3] = 2 * GUN_XC
VIEW = np.eye(4)
VIEW[1, 3] = vt["view_push_y"]; VIEW[2, 3] = vt["view_push_z"]

# knife is rigid-bound to Box01 (node 47); its anim world in idle_0 frame0
s0 = payload["clips"]["idle_0"]["samples"][0]
Wg = q2m(s0["quat_xyzw_world"][47]); Wg[:3, 3] = s0["pos"][47]
Bg = np.array([nn for nn in payload["nodes"] if nn["index"] == 47][0]["bind_world"])
# anim_world(wcf) = VIEW @ MX @ (H @ wcf @ Hinv) @ MX
delta = VIEW @ MX @ (H @ (Wg @ np.linalg.inv(Bg)) @ Hinv) @ MX
nA = n[sideA].mean(0); nB = n[sideB].mean(0)
dA = (delta[:3, :3] @ nA); dB = (delta[:3, :3] @ nB)
dA /= np.linalg.norm(dA); dB /= np.linalg.norm(dB)
print("sideA view-space dir:", dA.round(3), "-> toward camera(+Y)?", dA[1] > 0)
print("sideB view-space dir:", dB.round(3), "-> toward camera(+Y)?", dB[1] > 0)
