# -*- coding: utf-8 -*-
"""P1 — decode GalilACE_PhantomBeast verified assets.

- PV LTB (LZMA-alone) -> skeleton nodes + clips -> reference_payload.json
  (same 100fps diagnostic sampler as p7_s04_r1 g1_source_audit_v3:
  linear position in source ms + unit-quat shortest-arc SLERP)
- PV LTB -> CFRezManager --dump-ltb-skin -> cf_skin JSON
  (verts/tris/uv/bone_weights/bone_indices)
- PV DTX -> PNG via decode_repo_pixels
- CFG + _S/_N/_A maps copied to decode/maps/

Outputs to work/galil_ace_tianxi/decode/.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import math
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "p5"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
sys.path.insert(0, str(_REPO / "work" / "p5_leishen" / "p7_s04_r1" / "scripts"))

import _paths  # noqa: E402
import p5_p7_s04_cf_animation as a  # noqa: E402
import g1_source_audit_v3 as v3  # noqa: E402
import n05a_decoder_provenance_audit as n05a  # noqa: E402

ACQ = _REPO / "work" / "galil_ace_tianxi" / "acquire" / "verified_root"
OUT = _REPO / "work" / "galil_ace_tianxi" / "decode"
CFREZ = _REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"

PV_LTB = ACQ / "Models" / "PLAYERVIEW" / "PV-GalilACE_PhantomBeast.LTB"
PV_DTX = ACQ / "ModelTextures" / "PLAYERVIEW" / "PV-GalilACE_PhantomBeast.DTX"
MAPS = [
    ACQ / "ModelTextures" / "SpecularMap" / "GalilACE_PhantomBeast_S.PNG",
    ACQ / "ModelTextures" / "NormalMap" / "GalilACE_PhantomBeast_N.PNG",
    ACQ / "ModelTextures" / "AlphaMap" / "GalilACE_PhantomBeast_A.PNG",
]
CFG = ACQ / "ModelTextures" / "Shader" / "WeaponShader" / "GalilACE_PhantomBeast.CFG"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "maps").mkdir(exist_ok=True)

    # --- LTB body ---
    raw = PV_LTB.read_bytes()
    body = raw
    if raw[:1] == b"\x5d":
        body = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    print(f"[p1] ltb packed={len(raw)} body={len(body)} sha256={hashlib.sha256(body).hexdigest()[:16]}")
    (OUT / "PV-GalilACE_PhantomBeast.body.bin").write_bytes(body)

    # --- skeleton + clips -> reference payload (100fps diagnostic sampler) ---
    header = a.parse_header(body)
    alloc = header["allocs"]
    nodes, offset = a.parse_skeleton(body, alloc["nNodes"])
    weight_sets, offset = a.parse_weight_sets(body, offset, len(nodes), alloc["nWeightSets"])
    child_models, offset = a.parse_child_models(body, offset, alloc["nChildModels"])
    clips, end_off = a.parse_anims(body, offset, nodes, alloc["nParentAnims"])
    print(f"[p1] nodes={len(nodes)} clips={[c['name'] for c in clips]} weights={len(weight_sets)} child={len(child_models)}")
    for n in nodes:
        n["matrix"] = n["matrix"]  # keep

    binds = [v3.reshape16(n["matrix"]) for n in nodes]
    samplers = {c["name"]: v3.ClipSampler(nodes, c) for c in clips}

    import numpy as np
    payload_clips = {}
    bbox_all = None
    for clip in clips:
        samples, bbox = v3.sample_clip_payload(nodes, samplers[clip["name"]])
        payload_clips[clip["name"]] = {
            "duration_ms": clip["duration_ms"],
            "times_ms": list(clip["times_ms"]),
            "events": clip.get("events") or [],
            "n_samples": len(samples),
            "samples": samples,
            "bbox": bbox,
            "n_keyframes": clip["n_keyframes"],
            "fps": clip.get("fps"),
            "compression_name": clip.get("compression_name"),
        }
        mins = np.array(bbox["min"]); maxs = np.array(bbox["max"])
        bbox_all = {"min": mins, "max": maxs} if bbox_all is None else {
            "min": np.minimum(bbox_all["min"], mins), "max": np.maximum(bbox_all["max"], maxs)}

    payload = {
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "sampler_label": "DIAGNOSTIC: linear pos in source ms; unit-quat SLERP (same as g1 v3).",
        "convention": v3.CONVENTION,
        "source_ltb_sha256_packed": hashlib.sha256(raw).hexdigest(),
        "source_ltb_sha256_body": hashlib.sha256(body).hexdigest(),
        "bbox_all_clips": {"min": bbox_all["min"].tolist(), "max": bbox_all["max"].tolist()},
        "nodes": [
            {
                "index": n["index"], "name": n["name"], "parent": n["parent"],
                "children": n["children"],
                "bind_world": binds[n["index"]].tolist(),
            }
            for n in nodes
        ],
        "clips": payload_clips,
    }
    (OUT / "reference_payload.json").write_text(
        json.dumps(v3.jsonable(payload), indent=2) + "\n", encoding="utf-8")

    audit = {
        "header": header,
        "n_nodes": len(nodes),
        "n_clips": len(clips),
        "clip_summary": [
            {
                "name": c["name"], "n_keyframes": c["n_keyframes"],
                "duration_ms": c["duration_ms"], "fps": c.get("fps"),
                "compression": c.get("compression_name"),
                "events": c.get("events") or [],
            }
            for c in clips
        ],
        "node_names": [n["name"] for n in nodes],
        "weight_sets": [{"name": w["name"], "count": w["count"], "nonzero": w["nonzero"]} for w in weight_sets],
        "child_models": child_models,
        "stream_end_offset": end_off,
        "body_bytes": len(body),
    }
    (OUT / "ltb_audit.json").write_text(json.dumps(v3.jsonable(audit), indent=2) + "\n", encoding="utf-8")

    # --- skin dump via CFRezManager ---
    skin_out = OUT / "cf_skin_galilace.json"
    proc = subprocess.run(
        [str(CFREZ), "--dump-ltb-skin", "--input", str(PV_LTB), "--output", str(skin_out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    print("[p1] dump-ltb-skin:", (proc.stdout or proc.stderr).strip()[:400])
    if proc.returncode != 0 or not skin_out.is_file():
        raise RuntimeError(f"dump-ltb-skin failed: {proc.stderr}")
    skin = json.loads(skin_out.read_text(encoding="utf-8"))
    print(f"[p1] skin meshes={len(skin['meshes'])} nodes={len(skin['skeleton'])}")
    for m in skin["meshes"]:
        print(f"      {m['name']}: v={m['vertex_count']} tri={len(m['triangles'])//3} w={'Y' if m['bone_weights'] else 'rigid'}")

    # --- DTX -> PNG ---
    dtx = PV_DTX.read_bytes()
    res = n05a.decode_repo_pixels(dtx)
    if not res.get("ok"):
        raise RuntimeError(f"DTX decode failed: {res.get('reason')} {res.get('header')}")
    png = OUT / "PV-GalilACE_PhantomBeast.png"
    res["image"].save(png)
    print(f"[p1] dtx -> {png.name} {res['image'].size} fmt={res.get('format')}")

    # --- maps + cfg ---
    import shutil
    for p in MAPS + [CFG]:
        shutil.copy2(p, OUT / "maps" / p.name)
    print("[p1] maps+cfg copied")
    print("[p1] DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
