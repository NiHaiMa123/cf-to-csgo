# -*- coding: utf-8 -*-
"""E1 final — join the verified discovery artifacts into the unified
effect description required by plan.md §"建议的后续代码组织":

  assets/weapons/galil_ace_tianxi/effects.json

Per FX node: type, times, repeat, scale range, attach socket (resolved to
parent node + socket-local rot/pos/scale from the _BL socket table), node
Offset, resource refs (model/skin/sprite/renderstyle resolved to verified
local files + sha256), Ck/Sk curves in original order, and a suggested
Source-side implementation class:

  LTBModel       -> "C_mesh"      (附加网格 + 加法/RenderStyle 材质)
  Sprite         -> "C_sprite"    (光片/相机面片; Flare 语义另测)
  FlareSpriteFX  -> "C_sprite"    (同上; 视角/遮挡语义待实测)
  ParticleSystem -> "D_pcf"       (Source 1 PCF 重建)

Evidence levels: "verified" for values read from original definitions,
"inferred" for Source mapping suggestions.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
GROUP = json.loads((OUT / "clientfx_group_pv_galilace_phantombeast_idle.json").read_text(encoding="utf-8"))
SOCK = json.loads((OUT / "sockets.json").read_text(encoding="utf-8"))
GRAPH = json.loads((OUT / "asset_graph.json").read_text(encoding="utf-8"))
LAYERS = json.loads((OUT / "ltb_layers.json").read_text(encoding="utf-8"))
DEST = _REPO / "assets" / "weapons" / "galil_ace_tianxi" / "effects.json"

IMPL = {"LTBModel": "C_mesh", "Sprite": "C_sprite", "FlareSpriteFX": "C_sprite", "ParticleSystem": "D_pcf"}
SORT_KEY = lambda n: n["track_id"]


def prop_map(node):
    """first-value map + ordered full list kept separately"""
    m = {}
    for p in node["properties"]:
        m.setdefault(p["name"], p["value"])
    return m


def main() -> int:
    sock_by_name = {s["name"]: s for s in SOCK["sockets"]}
    files_by_rez = {f["rez_path"].replace("\\", "/").upper(): f for f in GRAPH["files"]}
    layer_by_ltb = {r["ltb"].upper(): r for r in LAYERS["files"]}

    nodes = []
    for n in sorted(GROUP["fxf"]["group_record"]["nodes"], key=SORT_KEY):
        pm = prop_map(n)
        base = n["fx_name"].split(";")[0].strip()
        label = n["fx_name"].split(";")[1].strip() if ";" in n["fx_name"] else ""
        attach = pm.get("AttachName")
        sock = sock_by_name.get(str(attach))
        refs = {}
        for p in n["properties"]:
            if p["type_id"] != 7 or not isinstance(p["value"], str) or "|" not in p["value"]:
                continue
            ext, _, path = p["value"].partition("|")
            path = path.strip()
            if not path or path == "...":
                continue
            rec = files_by_rez.get(path.replace("\\", "/").upper())
            entry = {"path": path, "sha256": rec["sha256"] if rec else None,
                     "local": rec["local_path"] if rec else None}
            if p["name"].startswith("Skin") or p["name"].startswith("SpriteSkin") or p["name"].startswith("RenderStyle"):
                refs.setdefault(p["name"], entry)
            else:
                refs[p["name"]] = entry
            if ext == "ltb" and "Model" in p["name"]:
                li = layer_by_ltb.get(Path(path).name.upper())
                if li:
                    entry["geometry"] = {"meshes": li.get("meshes"), "skeleton": li.get("skeleton"),
                                         "skinned": li.get("skinned"), "bbox": li.get("bbox")}
        curves = {"Ck": [p["value"] for p in n["properties"] if p["name"] == "Ck"],
                  "Sk": [p["value"] for p in n["properties"] if p["name"] == "Sk"]}
        nodes.append({
            "track_id": n["track_id"], "fx_id": n["fx_id"], "type": base, "label": label,
            "linked": bool(n["linked"]), "link_id": n["link_id"], "link_node": n["link_node"],
            "start_time": n["start_time"], "end_time": n["end_time"], "repeat": n["repeat"],
            "min_scale": n["min_scale"], "max_scale": n["max_scale"],
            "update_pos": {"raw": pm.get("UpdatePos"), "selected": (str(pm.get("UpdatePos") or "").split(",")[0])},
            "attach_name": attach,
            "socket": sock and {"node_index": sock["node_index"], "node_name": sock["node_name"],
                               "rot_quat": sock["rot_quat"], "pos": sock["pos"], "scale": sock["scale"],
                               "source": "PV-GalilACE_PhantomBeast_BL.LTB socket table (nSockets=39)"},
            "offset": pm.get("Offset"), "rotate_add": pm.get("RotateAdd"),
            "facing": pm.get("Facing"), "blend_mode": pm.get("BlendMode"),
            "detail_level": pm.get("DetailLevel"),
            "resources": refs,
            "curves": curves,
            "all_properties": [{"name": p["name"], "kind": p["kind"], "value": p["value"]}
                               for p in n["properties"]],
            "source_impl_suggestion": {"class": IMPL.get(base, "unknown"), "evidence": "inferred",
                                       "note": "Source mapping suggestion only; verify per-path probes (E2)"},
        })

    doc = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "weapon": "galil_ace_tianxi",
        "group": GROUP["fxf"]["group"],
        "phase_raw": GROUP["fxf"]["group_record"]["phase_raw"],
        "coordinate_note": "socket pos/rot are CF LTB node-local (parent=node_name); port through existing H-transform + mirror pipeline; not yet applied",
        "sockets_source": "PV-GalilACE_PhantomBeast_BL.LTB socket table; base PV LTB has nSockets=0",
        "nodes": nodes,
        "provenance": {
            "group_json": "discovery/clientfx_group_pv_galilace_phantombeast_idle.json",
            "sockets_json": "discovery/sockets.json",
            "asset_graph": "discovery/asset_graph.json",
            "ltb_layers": "discovery/ltb_layers.json",
        },
        "evidence_legend": {"verified": "read from original CF definition",
                            "inferred": "aligned/mapped by pipeline convention",
                            "approximation": "hand-rebuilt"},
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    n_sock = sum(1 for n in nodes if n["socket"])
    print(f"[effects.json] nodes={len(nodes)} sockets_resolved={n_sock} -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
