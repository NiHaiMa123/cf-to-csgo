# -*- coding: utf-8 -*-
"""P3b — CF PV → CS viewmodel H for COP357-雪域霜狐.

Hands and pistol share one CF PLAYERVIEW skeleton (same FvARM space as
Tianxi/Kukri). Reuse the verified Tianxi H; MX is about this pistol's own
H-transformed bbox centre. Stock glock used only for attachment worlds
and sequence/sound reference.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "cop357_snowfox"
CSREF = _REPO / "work" / "mauser_libra" / "csref" / "decompiled_stock" / "v_pist_glock18"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_cop357_winter.json"
OUT = WORK / "csref" / "viewmodel_transform.json"

# mesh -> LTB node index (Hungarian assignment on bind-local mean radius;
# see work/mauser_libra/scan notes / pipeline M.3)
PIECE_NODE = {
    "Cop357Derringer_RoyalDragon": 46,  # Box001 gun root
    "RoyalDragon6-reload": 47,          # Box003 cylinder/mag
    "bullet003": 48,                    # Box007
    "bullet004": 49,                    # Box006
    "bullet002": 50,                    # Box005
    "bullet01": 51,                     # Box004
}

ATTACH = ("v_weapon.flash", "v_weapon.shelleject", "v_weapon.stattrack", "v_weapon.uid")


def euler_to_mat(e):
    rx, ry, rz = e
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return np.array([
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx, 0],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx, 0],
        [-sy, cy * sx, cy * cx, 0],
        [0, 0, 0, 1],
    ])


def parse_smd(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes = {}
    frames = []
    mode = None
    cur = None
    for ln in lines:
        s = ln.strip()
        if s == "nodes":
            mode = "n"; continue
        if s == "skeleton":
            mode = "s"; continue
        if s == "end":
            mode = None
            if cur is not None:
                frames.append(cur); cur = None
            continue
        if mode == "n":
            m = s.split('"')
            idx = int(s.split()[0])
            nodes[idx] = (m[1], int(s.rsplit('"', 1)[1]))
        elif mode == "s":
            if s.startswith("time"):
                if cur is not None:
                    frames.append(cur)
                cur = {}
            else:
                parts = s.split()
                cur[int(parts[0])] = tuple(float(v) for v in parts[1:7])
    if cur is not None:
        frames.append(cur)
    return {"nodes": nodes, "frames": frames}


def compose_worlds(nodes, frame):
    worlds = {}
    def world(i):
        if i in worlds:
            return worlds[i]
        pos, e = frame[i][:3], frame[i][3:]
        m = euler_to_mat(e)
        m[:3, 3] = pos
        name, p = nodes[i]
        worlds[i] = m if p < 0 else world(p) @ m
        return worlds[i]
    for i in nodes:
        world(i)
    return worlds


def cf_posed_gun_verts(payload, skin):
    nodes = payload["nodes"]
    s0 = payload["clips"]["idle_0"]["samples"][0]
    W = []
    for i in range(len(nodes)):
        x, y, z, wq = s0["quat_xyzw_world"][i]
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * wq), 2 * (x * z + y * wq)],
            [2 * (x * y + z * wq), 1 - 2 * (x * x + z * z), 2 * (y * z - x * wq)],
            [2 * (x * z - y * wq), 2 * (y * z + x * wq), 1 - 2 * (x * x + y * y)],
        ])
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = s0["pos"][i]
        W.append(M)
    pts = []
    by_piece = {}
    for m in skin["meshes"]:
        ni = PIECE_NODE.get(m["name"])
        if ni is None:
            continue
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        vs = np.array(m["vertices"]).reshape(-1, 3)
        hom = np.concatenate([vs, np.ones((len(vs), 1))], axis=1)
        posed = (D @ hom.T).T[:, :3]
        pts.append(posed)
        by_piece[m["name"]] = posed
    return np.concatenate(pts), by_piece


TIANXI_H = _REPO / "work" / "galil_ace_tianxi" / "csref" / "viewmodel_transform.json"


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    tianxi = json.loads(TIANXI_H.read_text(encoding="utf-8"))
    source, by_piece = cf_posed_gun_verts(payload, skin)

    s = float(tianxi["H"]["scale"])
    R = np.array(tianxi["H"]["rotation"], dtype=float)
    t = np.array(tianxi["H"]["translation"], dtype=float)
    transformed = s * (source @ R.T) + t
    # mirror centre from the *gun body only* (PV-Mauser_Libra) so remote
    # bull/coin pieces don't skew the axis
    body = s * (by_piece["Cop357Derringer_RoyalDragon"] @ R.T) + t
    gun_xc = float((body[:, 0].min() + body[:, 0].max()) / 2)
    print(f"cf gun verts={len(source)}")
    print("cf idle bbox", source.min(0).round(3).tolist(), source.max(0).round(3).tolist())
    print(f"reuse Tianxi H s={s:.6f} det(R)={np.linalg.det(R):.4f} t={np.round(t, 3)}")
    print("H bbox(all)", transformed.min(0).round(3).tolist(), transformed.max(0).round(3).tolist())
    print("H bbox(body)", body.min(0).round(3).tolist(), body.max(0).round(3).tolist(),
          "gun_center_x", round(gun_xc, 4))

    # attachment worlds from stock glock idle frame 0
    idle = parse_smd(CSREF / "v_pist_glock18_anims" / "glock_idle.smd")
    idle_w = compose_worlds(idle["nodes"], idle["frames"][0])
    idx_of = {n[0]: i for i, n in idle["nodes"].items()}
    attach = {}
    for name in ATTACH:
        i = idx_of[name]
        attach[name] = idle_w[i].tolist()
        print(f"attach {name}: pos={np.round(idle_w[i][:3,3],3)}")

    doc = {
        "H": {"scale": s, "rotation": R.tolist(), "translation": t.tolist()},
        "gun_center_x": gun_xc,
        "apply_mirror": True,
        "view_push_x": 2.0,
        "view_push_y": -5.0,
        "view_push_z": 0.0,
        "view_roll_deg": 0.0,
        "flip_knife_v": False,
        "flip_knife_normals": False,
        "icp": {
            "method": "reuse verified CF-playerview H (same FvARM space as Tianxi); MX about gun-body x centre",
            "src": "CF idle_0 posed M1896_Libra rigid gun verts",
            "dst": "shared CF playerview camera space",
        },
        "attach_worlds_p6": attach,
        "piece_node": PIECE_NODE,
        "note": "proper rotation only (det+1); mirror applied separately about gun body centre; no view correction yet",
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
