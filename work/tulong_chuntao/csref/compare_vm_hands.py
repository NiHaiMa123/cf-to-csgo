# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def xf(p, s, R, t, xc):
    q = s * (R @ np.array(p)) + t
    q[0] = 2 * xc - q[0]
    return q


def dump(label, payload, s, R, t, xc):
    s0 = payload["clips"]["idle_0"]["samples"][0]
    print(f"=== {label} idle ===")
    for n in payload["nodes"]:
        name = n["name"]
        if "Finger" in name or "Twist" in name or "Clavicle" in name:
            continue
        if "Upper" in name or "ForeArm" in name or "Spine" in name:
            continue
        if "Neck" in name or "Pelvis" in name:
            continue
        keep = any(k in name for k in ("Box", "Hand", "Prop", "FvARM-bone"))
        if not keep or name.count(" ") > 3:
            if name not in ("FvARM-bone",):
                if "Hand" not in name and "Box" not in name and "Prop" not in name:
                    continue
        pos = np.array(s0["pos"][n["index"]])
        print(f"{name:32s} cf={pos.round(2).tolist()}  vm={xf(pos, s, R, t, xc).round(2).tolist()}")


gvt = load(REPO / "work/galil_ace_tianxi/csref/viewmodel_transform.json")
gpl = load(REPO / "work/galil_ace_tianxi/decode/reference_payload.json")
dump(
    "TIANXI",
    gpl,
    gvt["H"]["scale"],
    np.array(gvt["H"]["rotation"]),
    np.array(gvt["H"]["translation"]),
    -5.223,
)

kvt = load(REPO / "work/tulong_chuntao/csref/viewmodel_transform.json")
kpl = load(REPO / "work/tulong_chuntao/decode/reference_payload.json")
dump(
    "KNIFE",
    kpl,
    kvt["H"]["scale"],
    np.array(kvt["H"]["rotation"]),
    np.array(kvt["H"]["translation"]),
    kvt["gun_center_x"],
)
