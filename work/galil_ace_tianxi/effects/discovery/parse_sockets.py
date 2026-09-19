# -*- coding: utf-8 -*-
"""E1c — recover fix_effect_* sockets (plan.md §7 task 2).

Finding: PV-GalilACE_PhantomBeast.LTB has nSockets=0 and no fix_effect
strings. The hand-variant PV-GalilACE_PhantomBeast_BL.LTB (and identical
_GR.LTB body) carries the socket table: nSockets=39.

Layout (lithtech runtime/model/src/model_load.cpp):
  header -> skeleton -> weight sets -> child models -> anims (u32 count)
  -> u32 nSockets -> per socket: u32 node_idx, u16 name_len+name,
     quat rot (4*f32), pos (3*f32), scale (3*f32)
  -> anim bindings (u16 len + name + dims(3*f32) + translation(3*f32))

Outputs effects/discovery/sockets.json and stores the verified _BL LTB
under assets/Models/PLAYERVIEW/.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
sys.path.insert(0, str(_REPO / "scripts" / "p5"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
import p5_p7_s04_cf_animation as anim  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent
ASSETS = OUT / "assets"
GROUP_JSON = OUT / "clientfx_group_pv_galilace_phantombeast_idle.json"

TARGETS = [
    "Models/PLAYERVIEW/PV-GalilACE_PhantomBeast_BL.LTB",
    "Models/PLAYERVIEW/PV-GalilACE_PhantomBeast_GR.LTB",
]
BASE_LTB = Path(_REPO / "work" / "galil_ace_tianxi" / "decode" / "PV-GalilACE_PhantomBeast.body.bin")


def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]


def read_str(b, o):
    ln = u16(b, o)
    raw = b[o + 2:o + 2 + ln]
    if raw.endswith(b"\0"):
        raw = raw[:-1]
    return raw.decode("ascii", errors="replace"), o + 2 + ln


def parse_sockets(body: bytes, nodes, off: int):
    n = u32(body, off)
    off += 4
    socks = []
    for _ in range(n):
        node_idx = u32(body, off)
        off += 4
        name, off = read_str(body, off)
        rot = list(struct.unpack_from("<4f", body, off)); off += 16
        pos = list(struct.unpack_from("<3f", body, off)); off += 12
        scale = list(struct.unpack_from("<3f", body, off)); off += 12
        parent = nodes[node_idx]["name"] if 0 <= node_idx < len(nodes) else None
        socks.append({"node_index": node_idx, "node_name": parent,
                      "name": name, "rot_quat": rot, "pos": pos, "scale": scale})
    return socks, off


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    group = json.loads(GROUP_JSON.read_text(encoding="utf-8"))
    used = group["fxf"]["attach_names"]

    # fetch verified _BL/_GR payloads
    found = {}
    for ip in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(ip)
        except Exception:
            continue
        for e in entries:
            for t in TARGETS:
                if e["full_path"].replace("\\", "/").upper() == t.upper() and is_complete_directory_md5(e.get("md5")):
                    found[t] = (ip, e)

    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "attach_names_used_by_group": used, "sources": [], "sockets": [],
           "evidence": {}}

    bodies = {}
    for t, (ip, e) in found.items():
        data, prov = read_verified_payload(ip, e)
        body = lzma.decompress(data, format=lzma.FORMAT_ALONE) if data[:1] == b"\x5d" else data
        dest = ASSETS / t
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        rec = {"rez_path": t, "archive": prov["index_archive"], "size": prov["size"],
               "md5": prov["directory_md5"], "sha256": prov["sha256"],
               "body_sha256": hashlib.sha256(body).hexdigest(), "body_bytes": len(body)}
        out["sources"].append(rec)
        bodies[t] = body

    # _BL and _GR bodies are identical; parse once
    base = bodies.get(TARGETS[0]) or next(iter(bodies.values()))
    hdr = anim.parse_header(base)
    nodes, off = anim.parse_skeleton(base, hdr["allocs"]["nNodes"])
    wsets, off = anim.parse_weight_sets(base, off, len(nodes), hdr["allocs"]["nWeightSets"])
    children, off = anim.parse_child_models(base, off, hdr["allocs"]["nChildModels"])
    n_anims = u32(base, off)
    off += 4
    socks, off = parse_sockets(base, nodes, off)

    # anim bindings sanity: u32 count then per-anim u16 len+name+6 f32
    n_bind = u32(base, off)
    off += 4
    bind_names = []
    for _ in range(n_bind):
        nm, off = read_str(base, off)
        off += 24  # dims(3f) + translation(3f)
        bind_names.append(nm)

    out["bl_header_allocs"] = hdr["allocs"]
    out["n_nodes"] = len(nodes)
    out["child_models"] = children
    out["n_anims"] = n_anims
    out["n_anim_bindings"] = n_bind
    out["anim_binding_names"] = bind_names
    out["stream_end"] = off
    out["body_bytes"] = len(base)
    out["sockets"] = socks

    # verify base PV LTB has nSockets=0 at its own socket position
    if BASE_LTB.is_file():
        bbody = BASE_LTB.read_bytes()
        bh = anim.parse_header(bbody)
        bn, boff = anim.parse_skeleton(bbody, bh["allocs"]["nNodes"])
        bw, boff = anim.parse_weight_sets(bbody, boff, len(bn), bh["allocs"]["nWeightSets"])
        bc, boff = anim.parse_child_models(bbody, boff, bh["allocs"]["nChildModels"])
        # anims exist here; the known-good audit put stream_end at 1581194 with tail = nSockets(0)+bindings
        tail = bbody[1581194:1581194 + 8]
        out["evidence"]["base_pv_ltb"] = {
            "allocs": bh["allocs"], "n_nodes": len(bn),
            "tail_first_u32": struct.unpack_from("<I", tail, 0)[0],
            "tail_u32_1": struct.unpack_from("<I", tail, 4)[0],
            "note": "tail = u32 nSockets(0) then u32 nAnimBindings(10); base PV LTB has no socket table",
        }

    used_set = set(used)
    have = {s["name"] for s in socks}
    out["coverage"] = {
        "used": sorted(used_set), "available": sorted(have),
        "used_missing": sorted(used_set - have),
        "available_unused": sorted(have - used_set),
    }
    (OUT / "sockets.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e1c] sockets={len(socks)} bindings={n_bind} used_missing={out['coverage']['used_missing']}")
    for s in socks:
        print(f"  {s['name']:>16s} -> node#{s['node_index']:3d} {s['node_name']!r} pos={[round(x,3) for x in s['pos']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
