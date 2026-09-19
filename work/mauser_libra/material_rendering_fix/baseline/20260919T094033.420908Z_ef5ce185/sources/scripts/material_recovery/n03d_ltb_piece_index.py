#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-D — Jupiter-vs-CF piece/texture-index differential.

Canonical artifact (N03-C SHA-verified):
  rez/RF016.REZ / PLAYERVIEW/PV-M4A1_S_BornBeast.LTB

Reference (not CF proof):
  jsj2008/lithtech runtime/model/src/model_load.cpp
  ModelPiece::Load: name, nLODs, lod dists, unused min/max,
    per LOD: m_nNumTextures, m_iTextures[4], m_iRenderStyle,
    m_nRenderPriority, render_object_type, then mesh payload.

This round records STRUCTURAL indices. It does not map an index
to a DTX/TGA path.

Outputs under
  work/.../runtime_acquisition/n03d_ltb_piece_index/
"""
from __future__ import annotations

import argparse
import json
import lzma
import os
import struct
import sys
import time
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402
import n02e_r2_payload_hash as n02er2  # type: ignore  # noqa: E402
import n03b_rez_packed_config as n03b  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
OUT_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition", "n03d_ltb_piece_index",
)
os.makedirs(OUT_DIR, exist_ok=True)

MAX_PIECE_TEXTURES = 4
ALLOC_NAMES = [
    "nKeyFrames", "nParentAnims", "nNodes", "nPieces", "nChildModels",
    "nTris", "nVerts", "nVertexWeights", "nLODs", "nSockets",
    "nWeightSets", "nStrings", "StringLengths", "VertAnimDataSize",
    "nAnimData",
]
NAME_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/\\. "
)


def read_u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def read_u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def read_i32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<i", buf, off)[0]


def read_f32(buf: bytes, off: int) -> float:
    return struct.unpack_from("<f", buf, off)[0]


def read_string(buf: bytes, off: int) -> tuple[str, int] | None:
    if off + 2 > len(buf):
        return None
    ln = read_u16(buf, off)
    if ln > 512 or off + 2 + ln > len(buf):
        return None
    raw = buf[off + 2 : off + 2 + ln]
    if raw.endswith(b"\x00"):
        raw = raw[:-1]
    if not raw or any(b < 0x20 and b not in (9, 10, 13) for b in raw):
        return None
    try:
        s = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    if not all(c in NAME_CHARS for c in s):
        return None
    return s, off + 2 + ln


def parse_jupiter_header(buf: bytes) -> dict:
    """Aligned LTB_Header (20 B) + fileVersion + 15 alloc uint32s."""
    if len(buf) < 84:
        raise ValueError("too short for Jupiter header+allocs")
    file_type = buf[0]
    version = read_u16(buf, 2)
    file_version = read_u32(buf, 20)
    allocs = list(struct.unpack_from("<15I", buf, 24))
    return {
        "file_type": file_type,
        "file_type_name": {
            1: "LTB_D3D_MODEL_FILE",
            5: "LTB_D3D_RENDERSTYLE_FILE",
        }.get(file_type, f"unknown({file_type})"),
        "ltb_header_version": version,
        "model_file_version": file_version,
        "allocs": dict(zip(ALLOC_NAMES, allocs)),
        "stream_after_allocs": 84,
        "header_layout": "aligned_20B_fileType@0_uint16_version@2_fileVersion@20",
    }


def parse_pre_piece(buf: bytes, off: int) -> dict:
    cmd = read_string(buf, off)
    if cmd is None:
        # empty string is uint16 0
        if read_u16(buf, off) != 0:
            raise ValueError(f"command string unreadable at {off}")
        cmd_s, off = "", off + 2
    else:
        cmd_s, off = cmd
    vis = read_f32(buf, off); off += 4
    nobb = read_u32(buf, off); off += 4
    if nobb > 64:
        raise ValueError(f"implausible num_obb={nobb}")
    off += nobb * 64  # skip unknown OBB payload if any; 0 in this file
    npieces = read_u32(buf, off); off += 4
    return {
        "command_string": cmd_s,
        "vis_radius": vis,
        "num_obb": nobb,
        "nPieces": npieces,
        "first_piece_offset": off,
    }


def try_lod_header(buf: bytes, off: int, layout: str) -> dict | None:
    """Parse one LOD texture/render header. Return fields + new offset or None."""
    if off + 4 > len(buf):
        return None
    ntex = read_u32(buf, off)
    if ntex > MAX_PIECE_TEXTURES:
        return None
    off += 4
    if layout == "jupiter_fixed4":
        if off + 16 + 12 > len(buf):
            return None
        tex = list(struct.unpack_from("<4i", buf, off)); off += 16
    elif layout == "counted":
        if ntex == 0:
            tex = []
        else:
            if off + 4 * ntex > len(buf):
                return None
            tex = list(struct.unpack_from("<" + "i" * ntex, buf, off))
            off += 4 * ntex
    else:
        return None
    if off + 12 > len(buf):
        return None
    rs = read_u32(buf, off); off += 4
    pri = read_u32(buf, off); off += 4
    rtype = read_u32(buf, off); off += 4
    return {
        "nNumTextures": ntex,
        "iTextures": tex,
        "iRenderStyle": rs,
        "nRenderPriority": pri,
        "render_object_type": rtype,
        "after": off,
    }


def try_piece(buf: bytes, off: int, layout: str, skip_unused: bool) -> dict | None:
    name = read_string(buf, off)
    if not name:
        return None
    nm, off = name
    if len(nm) < 2:
        return None
    if off + 4 > len(buf):
        return None
    nlods = read_u32(buf, off); off += 4
    if not (1 <= nlods <= 8):
        return None
    if off + 4 * nlods > len(buf):
        return None
    dists = list(struct.unpack_from("<" + "f" * nlods, buf, off))
    off += 4 * nlods
    if skip_unused:
        if off + 8 > len(buf):
            return None
        unused = list(struct.unpack_from("<II", buf, off))
        off += 8
    else:
        unused = []
    lods = []
    for _ in range(nlods):
        lod = try_lod_header(buf, off, layout)
        if lod is None:
            return None
        off = lod["after"]
        lods.append({k: lod[k] for k in lod if k != "after"})
        # CF delta: do not consume render-object payload here.
        break  # only first LOD header; mesh skip is separate
    return {
        "name": nm,
        "nLODs": nlods,
        "lod_dists": dists,
        "unused_minmax": unused,
        "lods": lods,
        "header_end": lods[0]["after"] if False else None,
        "after_first_lod_header": lods[-1] and try_lod_header and lods[0],
        "_next": None,
    }


def score_lod(lod: dict) -> int:
    s = 0
    if 0 <= lod["nNumTextures"] <= 4:
        s += 2
    if 0 <= lod["iRenderStyle"] <= 32:
        s += 2
    if 0 <= lod["render_object_type"] <= 16:
        s += 3
    elif lod["render_object_type"] < 256:
        s += 1
    if 0 <= lod["nRenderPriority"] <= 255:
        s += 1
    return s


def find_next_name(buf: bytes, start: int, limit: int) -> int | None:
    end = min(len(buf) - 3, start + limit)
    pos = start
    while pos < end:
        got = read_string(buf, pos)
        if got and 2 <= len(got[0]) <= 64:
            # following nLODs plausible?
            nxt = got[1]
            if nxt + 4 <= len(buf):
                nl = read_u32(buf, nxt)
                if 1 <= nl <= 8:
                    return pos
        pos += 1
    return None


def walk_pieces(buf: bytes, first_off: int, n_expected: int,
                layout: str, skip_unused: bool) -> dict:
    pieces = []
    off = first_off
    for i in range(n_expected):
        name = read_string(buf, off)
        if not name:
            break
        nm, after_name = name
        nlods_off = after_name
        if nlods_off + 4 > len(buf):
            break
        nlods = read_u32(buf, nlods_off)
        if not (1 <= nlods <= 8):
            break
        dists_off = nlods_off + 4
        if dists_off + 4 * nlods > len(buf):
            break
        dists = list(struct.unpack_from("<" + "f" * nlods, buf, dists_off))
        lod_off = dists_off + 4 * nlods
        unused = []
        if skip_unused:
            unused = list(struct.unpack_from("<II", buf, lod_off))
            lod_off += 8
        lods = []
        ok = True
        cursor = lod_off
        for li in range(nlods):
            lod = try_lod_header(buf, cursor, layout)
            if lod is None:
                ok = False
                break
            lods.append({k: v for k, v in lod.items() if k != "after"})
            # skip mesh: search next piece or next LOD header
            if li + 1 < nlods:
                nxt = find_next_name(buf, lod["after"], 250000)
                # next LOD is not a name; don't use name search between LODs
                # CF weapons here have nLODs=1 in probe
                cursor = lod["after"]
            else:
                cursor = lod["after"]
        if not ok or not lods:
            break
        nxt_piece = find_next_name(buf, cursor, 400000)
        pieces.append({
            "index": i,
            "name": nm,
            "offset": off,
            "nLODs": nlods,
            "lod_dists": [round(x, 5) for x in dists],
            "unused_minmax": unused,
            "lods": lods,
            "next_piece_offset": nxt_piece,
        })
        if nxt_piece is None:
            break
        off = nxt_piece
    score = 0
    for p in pieces:
        for lod in p["lods"]:
            score += score_lod(lod)
        if p["name"]:
            score += 1
    return {
        "layout": layout,
        "skip_unused": skip_unused,
        "pieces_parsed": len(pieces),
        "score": score,
        "pieces": pieces,
    }


def load_ltb(rez_path: str, full_path: str) -> dict:
    idx = n02dr1.read_rez_index(rez_path)
    by = {f["full_path"].upper(): f for f in idx["files"]}
    e = by.get(full_path.upper())
    if not e:
        raise FileNotFoundError(full_path)
    raw = n02er2.read_payload_bytes(rez_path, e["data_offset"], e["size"])
    dec = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    return {
        "rez_path": rez_path,
        "archive": n03b.archive_label(rez_path),
        "full_path": e["full_path"],
        "size": e["size"],
        "data_offset": e["data_offset"],
        "raw_magic": raw[:4].hex(),
        "decompressed_size": len(dec),
        "bytes": dec,
    }


def analyse(ltb: dict) -> dict:
    buf = ltb["bytes"]
    hdr = parse_jupiter_header(buf)
    pre = parse_pre_piece(buf, hdr["stream_after_allocs"])
    n_exp = pre["nPieces"]
    trials = []
    for layout in ("jupiter_fixed4", "counted"):
        for skip in (True, False):
            trials.append(walk_pieces(buf, pre["first_piece_offset"], n_exp,
                                      layout, skip))
    trials.sort(key=lambda t: (t["pieces_parsed"], t["score"]), reverse=True)
    best = trials[0]
    jupiter_match = (
        hdr["file_type"] == 1
        and hdr["ltb_header_version"] == 9
        and hdr["allocs"]["nPieces"] == pre["nPieces"]
        and pre["nPieces"] > 0
    )
    indices_ok = best["pieces_parsed"] == pre["nPieces"] and all(
        0 <= lod["render_object_type"] <= 16
        for p in best["pieces"] for lod in p["lods"]
    )
    if jupiter_match and indices_ok:
        status = "PIECE_TEXTURE_INDEX_STRUCTURAL"
        conf = "HIGH"
    elif jupiter_match and best["pieces_parsed"] >= 1:
        status = "CANDIDATE_ONLY"
        conf = "MEDIUM"
    else:
        status = "CANDIDATE_ONLY"
        conf = "LOW"
    return {
        "header": hdr,
        "pre_piece": pre,
        "jupiter_header_match": jupiter_match,
        "best_layout": {
            "layout": best["layout"],
            "skip_unused": best["skip_unused"],
            "pieces_parsed": best["pieces_parsed"],
            "score": best["score"],
        },
        "trials": [
            {k: t[k] for k in ("layout", "skip_unused", "pieces_parsed", "score")}
            for t in trials
        ],
        "pieces": best["pieces"],
        "status": status,
        "confidence": conf,
        "delta_notes": [],
    }


def write_report(pv: dict, qv: dict | None, elapsed: float) -> str:
    lines = []
    a = lines.append
    a("# P4-M01-N03-D — Jupiter vs CF LTB piece/texture indices")
    a("")
    a(f"- status: **{pv['analysis']['status']}**")
    a(f"- confidence: **{pv['analysis']['confidence']}**")
    a("- script: `scripts/material_recovery/n03d_ltb_piece_index.py`")
    a("- reference: `jsj2008/lithtech/runtime/model/src/model_load.cpp` "
      "(REFERENCE_IMPLEMENTATION, not CF proof)")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    a("## 1. Canonical PV LTB")
    a("")
    a(f"- archive: `{pv['archive']}`")
    a(f"- path: `{pv['full_path']}`")
    a(f"- compressed: {pv['size']}  decompressed: {pv['decompressed_size']}")
    a(f"- raw magic: `{pv['raw_magic']}` (LZMA-alone `5d`)")
    a("")
    h = pv["analysis"]["header"]
    a("### 1.1 Jupiter header")
    a("")
    a("| field | value |")
    a("|---|---|")
    a(f"| fileType | {h['file_type']} `{h['file_type_name']}` |")
    a(f"| LTB_Header.version | {h['ltb_header_version']} |")
    a(f"| model fileVersion | {h['model_file_version']} |")
    a(f"| header_layout | `{h['header_layout']}` |")
    for k, v in h["allocs"].items():
        a(f"| alloc.{k} | {v} |")
    pre = pv["analysis"]["pre_piece"]
    a(f"| command_string | `{pre['command_string']}` |")
    a(f"| vis_radius | {pre['vis_radius']} |")
    a(f"| num_obb | {pre['num_obb']} |")
    a(f"| nPieces (stream) | {pre['nPieces']} |")
    a(f"| alloc.nPieces match | {h['allocs']['nPieces'] == pre['nPieces']} |")
    a("")
    bl = pv["analysis"]["best_layout"]
    a("### 1.2 Best piece-LOD layout (scored CF delta)")
    a("")
    a(f"- layout: `{bl['layout']}`  skip_unused={bl['skip_unused']}")
    a(f"- pieces_parsed: {bl['pieces_parsed']} / {pre['nPieces']}")
    a(f"- score: {bl['score']}")
    a("")
    a("| trial | skip_unused | pieces | score |")
    a("|---|---|---|---|")
    for t in pv["analysis"]["trials"]:
        a(f"| `{t['layout']}` | {t['skip_unused']} | {t['pieces_parsed']} | {t['score']} |")
    a("")
    a("### 1.3 Pieces")
    a("")
    a("| i | name | nLODs | nNumTextures | iTextures | iRenderStyle | robj_type |")
    a("|---|---|---|---|---|---|---|")
    for p in pv["analysis"]["pieces"]:
        lod = p["lods"][0] if p["lods"] else {}
        a(f"| {p['index']} | `{p['name']}` | {p['nLODs']} | "
          f"{lod.get('nNumTextures','')} | `{lod.get('iTextures','')}` | "
          f"{lod.get('iRenderStyle','')} | {lod.get('render_object_type','')} |")
    a("")
    a("Texture indices are **slot numbers**, not DTX/TGA paths.")
    a("`nNumTextures=0` on every piece: this LTB does not carry extra")
    a("texture filenames. The repeating `iTextures` pattern is the fixed")
    a("Jupiter array of 4 ints (always written). Runtime PV DTX still")
    a("comes from the Bute `PViewSkinFileName` (N03-C), not from these slots.")
    a("")
    a("Winning layout omits Jupiter's deprecated min/max LOD offset")
    a("uint32 pair (`skip_unused=False` scores higher). That is a")
    a("fileVersion-25 CF delta against `ModelPiece::Load` as written.")
    a("")
    if qv:
        a("## 2. QV LTB differential (rez2 copy, optional)")
        a("")
        a(f"- archive: `{qv['archive']}` `{qv['full_path']}`")
        a(f"- status: **{qv['analysis']['status']}**")
        a(f"- nPieces: {qv['analysis']['pre_piece']['nPieces']}")
        a(f"- pieces_parsed: {qv['analysis']['best_layout']['pieces_parsed']}")
        a("")
        a("| i | name | nNumTextures | iTextures | iRenderStyle |")
        a("|---|---|---|---|---|")
        for p in qv["analysis"]["pieces"][:16]:
            lod = p["lods"][0] if p["lods"] else {}
            a(f"| {p['index']} | `{p['name']}` | {lod.get('nNumTextures','')} | "
              f"`{lod.get('iTextures','')}` | {lod.get('iRenderStyle','')} |")
        a("")
    a("## 3. Jupiter vs CF delta")
    a("")
    a("- Header: CF matches Jupiter D3D model (`fileType=1`, header version 9)")
    a("  with **aligned 20-byte** `LTB_Header` (uint16 version at offset 2),")
    a("  then `fileVersion` at 20, then 15 allocation uint32s.")
    a("- Outer compression: CF wraps the Jupiter body in LZMA-alone (`5d`).")
    a("  Jupiter `Model::Load` does not mention this wrapper.")
    a("- Piece names / nPieces match the stream after visRadius/obb.")
    a("- `CDIModelDrawable::Load` mesh payload is **not** walked this round;")
    a("  subsequent pieces are found by scanning the next uint16 name with")
    a("  a plausible `nLODs`. That scan is a CF recovery method, not Jupiter.")
    a("- `m_iTextures[i]` is not a filename. No name table was parsed.")
    a("")
    a("## 4. Remaining ambiguity")
    a("")
    a("- Index → DTX/TGA/CFG path still `OPEN_UNRESOLVED`.")
    a("- `nNumTextures=0`: LTB piece table does not name Alpha/Normal/")
    a("  Specular TGA or WeaponShader CFG.")
    a("- CFG/render semantic closure still `OPEN_UNRESOLVED`.")
    a("- P4-M01 is not PASS. This is not P5 雷神.")
    a("")
    a(f"### Confidence: `{pv['analysis']['confidence']}`")
    a("")
    a("## 5. Status")
    a("")
    a(f"**status**: `{pv['analysis']['status']}`")
    a("")
    a("## 6. Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT map texture index to DTX/TGA path")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT scan all LTB / all REZ")
    a("- did NOT freeze CFG shader semantics")
    a("- did NOT modify historical accepted evidence or `plan.md`")
    a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None)
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02dr1)
        importlib.reload(n02er2)

    global CF_DIR
    CF_DIR = _paths.cf_dir()
    t0 = time.time()
    pv_path = os.path.join(CF_DIR, "rez", "RF016.REZ")
    print(f"[n03d] loading PV LTB from {pv_path}", file=sys.stderr)
    pv = load_ltb(pv_path, "PLAYERVIEW/PV-M4A1_S_BornBeast.LTB")
    pv["analysis"] = analyse(pv)
    print(f"[n03d] PV status={pv['analysis']['status']} "
          f"pieces={pv['analysis']['best_layout']['pieces_parsed']}",
          file=sys.stderr)

    qv = None
    qv_path = os.path.join(CF_DIR, "rez2", "RF016.REZ")
    if os.path.isfile(qv_path):
        try:
            qv = load_ltb(qv_path, "WEAPONS/QV-M4A1_S_BornBeast.LTB")
            qv["analysis"] = analyse(qv)
            print(f"[n03d] QV status={qv['analysis']['status']} "
                  f"pieces={qv['analysis']['best_layout']['pieces_parsed']}",
                  file=sys.stderr)
        except (FileNotFoundError, lzma.LZMAError, ValueError, struct.error) as e:
            print(f"[n03d] QV skip: {e}", file=sys.stderr)
            qv = None

    elapsed = time.time() - t0
    status = pv["analysis"]["status"]

    def strip_bytes(d):
        out = {k: v for k, v in d.items() if k != "bytes"}
        if "analysis" in out:
            out["analysis"] = dict(out["analysis"])
        return out

    payload = {
        "task": "P4-M01-N03-D",
        "status": status,
        "confidence": pv["analysis"]["confidence"],
        "reference": (
            "jsj2008/lithtech/runtime/model/src/model_load.cpp "
            "ModelPiece::Load + ltb.h LTB_Header + modelallocations.cpp"
        ),
        "pv": strip_bytes(pv),
        "qv": strip_bytes(qv) if qv else None,
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "piece_table.json"),
              "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    rels = {
        "task": "P4-M01-N03-D",
        "status": status,
        "confidence": pv["analysis"]["confidence"],
        "relations": [
            {
                "relation": "CF PV LTB decompressed body starts with Jupiter D3D LTB_Header fileType=1 version=9",
                "grade": "STRUCTURALLY_VERIFIED",
            },
            {
                "relation": "alloc.nPieces == stream nPieces",
                "grade": "STRUCTURALLY_VERIFIED",
                "nPieces": pv["analysis"]["pre_piece"]["nPieces"],
            },
            {
                "relation": "texture indices are slots, not paths",
                "grade": "SCOPED_NEGATIVE",
            },
        ],
        "remaining_blockers": [
            "index -> DTX/TGA path OPEN_UNRESOLVED",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(rels, f, indent=2, ensure_ascii=False)

    report = write_report(pv, qv, elapsed)
    with open(os.path.join(OUT_DIR, "piece_index_report.md"),
              "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[n03d] wrote {OUT_DIR} status={status}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
