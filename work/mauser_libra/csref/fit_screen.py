# -*- coding: utf-8 -*-
"""P3d — screen-space VIEW solve for 毛瑟-天秤座.

The user-requested method: corresponding points determine the transform.
CF's camera matrix is NOT in the LTB (playerview space is not camera space),
so instead of recovering CF's camera we solve the CS eye-space transform
directly: pick identifiable semantic vertices on OUR 3D mesh and their
desired 2D screen positions taken from the CF reference screenshot, then
least-squares solve the rigid VIEW (rot+trans) that projects them onto
those pixels.

Projection model matches the engine's view draw (mirrored x: -x = screen
right, -y = forward, +z = up):
    px = W/2 - x/(-y)*f ; py = H/2 - z/(-y)*f ; f = H/2 / tan(fov/2)

For reuse on other weapons: edit SEMI_PTS (3D pickers) + TARGETS (pixels).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "mauser_libra"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_m1896_libra.json"
VT = WORK / "csref" / "viewmodel_transform.json"

sys.path.insert(0, str(WORK / "csref"))
from fit_transform import PIECE_NODE  # noqa: E402

IMG_W, IMG_H = 1024.0, 576.0
FOV_DEG = 54.0                      # CS:GO viewmodel fov guess
F = (IMG_H / 2) / math.tan(math.radians(FOV_DEG / 2))


def proj(p):
    d = -p[1]
    return np.array([IMG_W / 2 - p[0] / d * F, IMG_H / 2 - p[2] / d * F])


def pick_muzzle(V):
    """barrel tip: top-region (high CF +y) vert with max +z."""
    top = V[V[:, 1] >= np.percentile(V[:, 1], 70)]
    return top[np.argmax(top[:, 2])]


def pick_grip(V):
    """grip bottom: global lowest vert."""
    return V[np.argmin(V[:, 1])]


def pick_hammer(V):
    """rear receiver top: max +y among rear-half (low z) verts."""
    zm = np.median(V[:, 2])
    rear = V[V[:, 2] < zm]
    return rear[np.argmax(rear[:, 1])]


def mesh_centroid(skin, name):
    m = [m for m in skin["meshes"] if m["name"] == name][0]
    return np.array(m["vertices"], float).reshape(-1, 3).mean(0)


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


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    vt = json.loads(VT.read_text(encoding="utf-8"))
    nodes = payload["nodes"]

    s = float(vt["H"]["scale"])
    H = np.eye(4)
    H[:3, :3] = s * np.array(vt["H"]["rotation"], float)
    H[:3, 3] = np.array(vt["H"]["translation"], float)

    s0 = payload["clips"]["idle_0"]["samples"][0]
    W = quat_worlds(nodes, s0)

    body = None
    for m in skin["meshes"]:
        if m["name"] != "PV-Mauser_Libra":
            continue
        ni = PIECE_NODE[m["name"]]
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        body = (D[:3, :3] @ np.array(m["vertices"]).reshape(-1, 3).T).T + D[:3, 3]
    assert body is not None
    body_h = (H[:3, :3] @ body.T).T + H[:3, 3]
    xc = float((body_h[:, 0].min() + body_h[:, 0].max()) / 2)
    MX = np.array([[-1.0, 0, 0, 2 * xc], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
                   [0, 0, 0, 1.0]])
    E = MX @ H

    def eye(cf_pt):
        return (E[:3, :3] @ cf_pt + E[:3, 3])

    # ---- semantic 3D points (CF space) ----
    pts_cf = {
        "muzzle": pick_muzzle(body),
        "grip": pick_grip(body),
        "hammer": pick_hammer(body),
        "coin": mesh_centroid(skin, "coin"),
    }
    pts_e = {k: eye(v) for k, v in pts_cf.items()}

    # ---- desired screen positions from the CF reference screenshot ----
    TARGETS = {
        "muzzle": np.array([575.0, 316.0]),
        "grip": np.array([700.0, 468.0]),
        "hammer": np.array([648.0, 350.0]),
        "coin": np.array([620.0, 390.0]),
    }

    keys = [k for k in TARGETS if k in pts_e]
    P = np.stack([pts_e[k] for k in keys])
    T2 = np.stack([TARGETS[k] for k in keys])

    # ---- Gauss-Newton solve: params = rodrigues(3) + translation(3) ----
    # seed: current view_matrix if present else identity
    V0 = np.array(vt["view_matrix"]) if vt.get("view_matrix") else np.eye(4)

    def exp_rot(w):
        th = np.linalg.norm(w)
        if th < 1e-12:
            return np.eye(3)
        ax = w / th
        K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]],
                      [-ax[1], ax[0], 0]])
        return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K

    R0, t0 = V0[:3, :3].copy(), V0[:3, 3].copy()
    w = np.zeros(3)
    t = np.zeros(3)
    for it in range(200):
        R = exp_rot(w) @ R0
        tv = t + t0
        Q = (R @ P.T).T + tv
        res = np.stack([proj(q) for q in Q]) - T2
        err = res.reshape(-1)
        cost = float(err @ err)
        if it % 40 == 0:
            print(f"  iter {it}: cost {cost:.3f}")
        if cost < 1e-6:
            break
        # numeric jacobian
        J = np.zeros((2 * len(keys), 6))
        par = np.concatenate([w, t])
        for j in range(6):
            dp = par.copy()
            dp[j] += 1e-5
            Rw = exp_rot(dp[:3]) @ R0
            tw = dp[3:] + t0
            Qp = (Rw @ P.T).T + tw
            rp = np.stack([proj(q) for q in Qp]) - T2
            J[:, j] = (rp.reshape(-1) - err) / 1e-5
        step = np.linalg.solve(J.T @ J + 1e-9 * np.eye(6), -J.T @ err)
        w = w + step[:3]
        t = t + step[3:]
        if np.linalg.norm(step) < 1e-10:
            break
    R = exp_rot(w) @ R0
    tv = t + t0
    VIEW = np.eye(4)
    VIEW[:3, :3] = R
    VIEW[:3, 3] = tv
    Q = (R @ P.T).T + tv
    print("\nsolved VIEW:")
    print(np.round(VIEW, 4))
    print("\nprojected vs target:")
    for i, k in enumerate(keys):
        print(f"  {k:7s} cf{np.round(pts_cf[k],2)} -> 3d {np.round(Q[i],2)} "
              f"px {np.round(proj(Q[i]),1)} vs {np.round(T2[i],1)}")

    vt["view_matrix"] = VIEW.tolist()
    for k in ("view_push_x", "view_push_y", "view_push_z", "view_roll_deg"):
        vt[k] = 0.0
    vt["gun_center_x"] = xc
    vt["view_fit"] = {
        "method": "screen-space solve: semantic mesh verts projected to "
                  "desired pixels (CF reference look), Gauss-Newton rigid fit",
        "fov_deg": FOV_DEG,
        "points": {k: {"cf": np.round(pts_cf[k], 2).tolist(),
                       "target_px": T2[i].tolist()}
                   for i, k in enumerate(keys)},
    }
    VT.write_text(json.dumps(vt, indent=2) + "\n", encoding="utf-8")
    print("\nwrote", VT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
