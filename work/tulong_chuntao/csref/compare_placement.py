# -*- coding: utf-8 -*-
"""Compare previous working Kukri Beast placement vs our H-transformed CF verts."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fit_transform import (  # noqa: E402
    parse_smd, compose_worlds, cf_posed_gun_verts, PIECE_NODE,
)

WORK = Path(__file__).resolve().parents[1]
PREV = WORK / "csref" / "decompiled_prev_kukri"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_kukri_spring.json"
VT = json.loads((WORK / "csref" / "viewmodel_transform.json").read_text(encoding="utf-8"))


def bbox(pts):
    mn, mx = pts.min(0), pts.max(0)
    return {
        "min": mn.round(3).tolist(),
        "max": mx.round(3).tolist(),
        "center": ((mn + mx) / 2).round(3).tolist(),
        "size": (mx - mn).round(3).tolist(),
        "n": int(len(pts)),
    }


def posed_mesh(model, idle, bone_ok):
    nodes = model["nodes"]
    rest = compose_worlds(nodes, model["frames"][0])
    pose = compose_worlds(nodes, idle["frames"][0])
    name_of = {i: n[0] for i, n in nodes.items()}
    delta = {i: pose[i] @ np.linalg.inv(rest[i]) for i in nodes}
    pts = []
    for tri in model["tris"]:
        for v in tri["verts"]:
            links = v["links"] or [(v["bone"], 1.0)]
            if not any(bone_ok(name_of.get(b, "")) for b, w in links if w > 0):
                continue
            acc = np.zeros(3)
            for b, w in links:
                if w <= 0:
                    continue
                acc += w * (delta[b] @ np.array(v["pos"] + [1.0]))[:3]
            pts.append(acc)
    return np.array(pts)


def apply_H(P, H, gun_xc):
    s = H["scale"]
    R = np.array(H["rotation"])
    t = np.array(H["translation"])
    T = s * (P @ R.T) + t
    # mirror about gun_xc (same as VM builder MX)
    T2 = T.copy()
    T2[:, 0] = 2 * gun_xc - T[:, 0]
    return T, T2


def main():
    prev_model = parse_smd(PREV / "cf_kukri_beast.smd")
    prev_idle = parse_smd(PREV / "v_knife_default_ct_anims" / "idle1.smd")
    Q = posed_mesh(prev_model, prev_idle, lambda n: "kukri" in n.lower() or n.lower() in ("kukri",))
    if len(Q) < 10:
        # all tris not on hands
        Q = posed_mesh(prev_model, prev_idle, lambda n: "valve" not in n.lower() and "bip" not in n.lower() and "dummy" not in n.lower() and "hand" not in n.lower())
    print("prev knife verts", len(Q), bbox(Q))
    print("prev bone names", sorted({prev_model["nodes"][i][0] for i in prev_model["nodes"]}))

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    P, _ = cf_posed_gun_verts(payload, skin)
    print("cf idle knife", bbox(P))

    T, TM = apply_H(P, VT["H"], VT["gun_center_x"])
    print("ours after H", bbox(T))
    print("ours after H+MX", bbox(TM))

    stock = parse_smd(WORK / "csref" / "decompiled_stock" / "v_knife_default_ct" / "knife_ct_model.smd")
    Qs = posed_mesh(stock, stock, lambda n: "knife" in n.lower() or n == "v_weapon")
    print("stock knife", bbox(Qs))


if __name__ == "__main__":
    main()
