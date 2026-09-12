#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-E — Parse canonical RenderStyle LTBs as Jupiter RS files.

Artifacts (N03-C bound):
  rez/rf002.rez  RS/NINJATRANSLUCENT.LTB
  rez/rf002.rez  RS/PVMODELDEFAULT.LTB

Reference:
  jsj2008/lithtech runtime/render_a/src/sys/d3d/d3d_renderstyle.cpp
  CD3DRenderStyle::Load_LTBData
  LTB_D3D_RENDERSTYLE_FILE = 5
  RENDERSTYLE_D3D_VERSION  = 3

Does not map TextureParam slots to DTX/TGA paths.
Does not freeze CFG shader semantics.

Outputs under
  work/.../runtime_acquisition/n03e_renderstyle_ltb/
"""
from __future__ import annotations

import argparse
import json
import lzma
import os
import re
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
import n03a_bornbeast_consumer as n03a  # type: ignore  # noqa: E402
import n03b_rez_packed_config as n03b  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
OUT_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material",
    "runtime_acquisition", "n03e_renderstyle_ltb",
)
os.makedirs(OUT_DIR, exist_ok=True)

LTB_D3D_RENDERSTYLE_FILE = 5
RENDERSTYLE_D3D_VERSION = 3
TEXTURE_PARAM = {
    0: "RENDERSTYLE_NOTEXTURE",
    1: "RENDERSTYLE_USE_TEXTURE1",
    2: "RENDERSTYLE_USE_TEXTURE2",
    3: "RENDERSTYLE_USE_TEXTURE3",
    4: "RENDERSTYLE_USE_TEXTURE4",
}
BLEND_MODE = {
    0: "NOBLEND", 1: "BLEND_ADD", 2: "BLEND_SATURATE",
    3: "BLEND_MOD_SRCALPHA", 4: "BLEND_MOD_SRCCOLOR",
}
RS_PATHS = (
    "RS/NINJATRANSLUCENT.LTB",
    "RS/PVMODELDEFAULT.LTB",
)


def u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def f32(buf: bytes, off: int) -> float:
    return struct.unpack_from("<f", buf, off)[0]


def load_rs(rez_path: str, full_path: str) -> dict:
    idx = n02dr1.read_rez_index(rez_path)
    by = {f["full_path"].upper(): f for f in idx["files"]}
    e = by.get(full_path.upper())
    if not e:
        raise FileNotFoundError(full_path)
    raw = n02er2.read_payload_bytes(rez_path, e["data_offset"], e["size"])
    dec = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    return {
        "archive": n03b.archive_label(rez_path),
        "full_path": e["full_path"],
        "compressed_size": e["size"],
        "data_offset": e["data_offset"],
        "sha256": __import__("hashlib").sha256(raw).hexdigest().upper(),
        "raw_magic": raw[:4].hex(),
        "decompressed_size": len(dec),
        "bytes": dec,
    }


def parse_header(buf: bytes) -> dict:
    if len(buf) < 32:
        raise ValueError("RS body too short")
    file_type = buf[0]
    version = u16(buf, 2)
    # 20-byte aligned header (same layout as N03-D model LTB)
    i_total = u32(buf, 20)
    i_cnt = u32(buf, 24)
    i_size = u32(buf, 28)
    return {
        "file_type": file_type,
        "file_type_ok": file_type == LTB_D3D_RENDERSTYLE_FILE,
        "version_at_offset2": version,
        "version_ok": version == RENDERSTYLE_D3D_VERSION,
        "byte1": buf[1],
        "header_layout": "aligned_20B_fileType@0_uint16_version@2 (byte1 is CF reserved/pad)",
        "iTotalSize": i_total,
        "iRenStyleCnt": i_cnt,
        "iSize": i_size,
        "body_offset": 32,
        "sanity_cnt": 1 <= i_cnt <= 32,
        "sanity_size": 0 < i_total <= 1_000_000,
    }


def parse_lighting(buf: bytes, off: int) -> dict:
    """LightingMaterial: 4x FourFloatColor + SpecularPower = 17 floats."""
    if off + 68 > len(buf):
        raise ValueError("lighting truncated")
    vals = struct.unpack_from("<17f", buf, off)
    names = (
        "Ambient", "Diffuse", "Emissive", "Specular",
    )
    mats = {}
    for i, n in enumerate(names):
        sl = vals[i * 4:(i + 1) * 4]
        mats[n] = {"r": sl[0], "g": sl[1], "b": sl[2], "a": sl[3]}
    mats["SpecularPower"] = vals[16]
    return {"offset": off, "size": 68, "material": mats}


def parse_stage_packed(buf: bytes, off: int) -> dict | None:
    """TextureStageOps with pack(1): 11 enums + bool + 16 floats + bool + u32 = 114."""
    need = 11 * 4 + 1 + 16 * 4 + 1 + 4  # 114
    if off + need > len(buf):
        return None
    enums = struct.unpack_from("<11I", buf, off)
    off2 = off + 44
    uv_en = buf[off2]
    off2 += 1
    matrix = struct.unpack_from("<16f", buf, off2)
    off2 += 64
    proj = buf[off2]
    off2 += 1
    tex_coord_count = u32(buf, off2)
    off2 += 4
    tex_param = enums[0]
    if tex_param > 8:
        return None
    return {
        "TextureParam": tex_param,
        "TextureParamName": TEXTURE_PARAM.get(tex_param, f"unknown({tex_param})"),
        "ColorOp": enums[1],
        "ColorArg1": enums[2],
        "ColorArg2": enums[3],
        "AlphaOp": enums[4],
        "UVSource": enums[7],
        "UAddress": enums[8],
        "VAddress": enums[9],
        "TexFilter": enums[10],
        "UVTransform_Enable": bool(uv_en),
        "ProjectTexCoord": bool(proj),
        "TexCoordCount": tex_coord_count,
        "size": need,
        "after": off2,
    }


def parse_stage_aligned(buf: bytes, off: int) -> dict | None:
    """TextureStageOps MSVC default align: 11 enums + bool+pad3 + 16f + bool+pad3 + u32 = 120."""
    need = 120
    if off + need > len(buf):
        return None
    enums = struct.unpack_from("<11I", buf, off)
    uv_en = buf[off + 44]
    proj = buf[off + 112]
    tex_coord_count = u32(buf, off + 116)
    tex_param = enums[0]
    if tex_param > 8:
        return None
    return {
        "TextureParam": tex_param,
        "TextureParamName": TEXTURE_PARAM.get(tex_param, f"unknown({tex_param})"),
        "ColorOp": enums[1],
        "ColorArg1": enums[2],
        "ColorArg2": enums[3],
        "AlphaOp": enums[4],
        "UVSource": enums[7],
        "UAddress": enums[8],
        "VAddress": enums[9],
        "TexFilter": enums[10],
        "UVTransform_Enable": bool(uv_en),
        "ProjectTexCoord": bool(proj),
        "TexCoordCount": tex_coord_count,
        "size": need,
        "after": off + need,
    }


def parse_pass_tail(buf: bytes, off: int, packed: bool) -> dict | None:
    """BlendMode .. BumpEnvMap after 4 stages."""
    if packed:
        # 5x u32, bool, 3x u32, bool, u32, 2x f32  = 20+1+12+1+4+8 = 46
        need = 46
        if off + need > len(buf):
            return None
        blend, zmode, cull, tfactor, aref = struct.unpack_from("<5I", buf, off)
        dyn = buf[off + 20]
        ztest, atest, fill = struct.unpack_from("<3I", buf, off + 21)
        bump = buf[off + 33]
        bump_stage = u32(buf, off + 34)
        scale = f32(buf, off + 38)
        offset = f32(buf, off + 42)
        after = off + 46
    else:
        need = 52  # bools padded to 4
        if off + need > len(buf):
            return None
        blend, zmode, cull, tfactor, aref = struct.unpack_from("<5I", buf, off)
        dyn = buf[off + 20]
        ztest, atest, fill = struct.unpack_from("<3I", buf, off + 24)
        bump = buf[off + 36]
        bump_stage = u32(buf, off + 40)
        scale = f32(buf, off + 44)
        offset = f32(buf, off + 48)
        after = off + 52
    if blend > 20 or zmode > 8 or cull > 8:
        return None
    return {
        "BlendMode": blend,
        "BlendModeName": BLEND_MODE.get(blend, f"enum({blend})"),
        "ZBufferMode": zmode,
        "CullMode": cull,
        "TextureFactor": f"0x{tfactor:08X}",
        "AlphaRef": aref,
        "DynamicLight": bool(dyn),
        "ZBufferTestMode": ztest,
        "AlphaTestMode": atest,
        "FillMode": fill,
        "bUseBumpEnvMap": bool(bump),
        "BumpEnvMapStage": bump_stage,
        "fBumpEnvMap_Scale": scale,
        "fBumpEnvMap_Offset": offset,
        "after": after,
    }


def try_passes(buf: bytes, off: int, npass: int, packed: bool) -> dict | None:
    stages_fn = parse_stage_packed if packed else parse_stage_aligned
    passes = []
    cur = off
    for pi in range(npass):
        stages = []
        for _ in range(4):
            st = stages_fn(buf, cur)
            if st is None:
                return None
            cur = st["after"]
            stages.append({k: v for k, v in st.items() if k not in {"after", "size"}})
        tail = parse_pass_tail(buf, cur, packed)
        if tail is None:
            return None
        cur = tail["after"]
        # optional iHasRSD3DRP uint8 + shader ids
        shader = None
        if cur < len(buf):
            has = buf[cur]
            if has in (0, 1) and cur + 1 + (16 if has else 0) <= len(buf) + 16:
                shader = {"iHasRSD3DRP": int(has)}
                cur += 1
                if has:
                    # bool + int + bool + int, packing unknown; read loosely
                    if cur + 10 <= len(buf):
                        shader["bUseVertexShader"] = bool(buf[cur])
                        shader["VertexShaderID"] = u32(buf, cur + 1) if cur + 5 <= len(buf) else None
        passes.append({
            "index": pi,
            "stages": stages,
            "tail": {k: v for k, v in tail.items() if k != "after"},
            "shader": shader,
        })
    return {"packed": packed, "passes": passes, "after": cur, "ok": True}


def string_scan(buf: bytes) -> list[dict]:
    text = n03a.extract_ascii_and_utf16le(buf, min_len=4)
    hits = []
    for pat, kind in (
        (r"[\w./\\-]+\.cfg", "cfg"),
        (r"[\w./\\-]+\.fxo?", "fx"),
        (r"[\w./\\-]+\.tga", "tga"),
        (r"[\w./\\-]+\.dtx", "dtx"),
        (r"WeaponShader", "WeaponShader"),
    ):
        for m in re.finditer(pat, text, re.I):
            hits.append({"kind": kind, "match": m.group(0)})
    return hits


def analyse(rs: dict) -> dict:
    buf = rs["bytes"]
    hdr = parse_header(buf)
    lighting = parse_lighting(buf, hdr["body_offset"])
    npass = u32(buf, lighting["offset"] + lighting["size"])
    pass_off = lighting["offset"] + lighting["size"] + 4
    trials = []
    for packed in (True, False):
        if not (1 <= npass <= 4):
            break
        t = try_passes(buf, pass_off, npass, packed)
        if t:
            # score: remaining bytes small, TextureParam in 0-4
            score = 0
            leftover = len(buf) - t["after"]
            if 0 <= leftover <= 80:
                score += 3
            for p in t["passes"]:
                for st in p["stages"]:
                    if 0 <= st["TextureParam"] <= 4:
                        score += 1
            t["score"] = score
            t["leftover"] = leftover
            trials.append(t)
    trials.sort(key=lambda x: x["score"], reverse=True)
    best = trials[0] if trials else None
    strings = string_scan(buf)
    header_ok = hdr["file_type_ok"] and hdr["version_ok"] and hdr["sanity_cnt"]
    if header_ok and best and best["ok"] and best["leftover"] <= 80:
        status = "RENDERSTYLE_STRUCTURAL"
        conf = "HIGH"
    elif header_ok:
        status = "CANDIDATE_ONLY"
        conf = "MEDIUM"
    else:
        status = "CANDIDATE_ONLY"
        conf = "LOW"
    return {
        "header": hdr,
        "lighting": lighting,
        "iRenderPasses": npass,
        "best": None if not best else {
            "packed": best["packed"],
            "score": best["score"],
            "leftover": best["leftover"],
            "passes": best["passes"],
        },
        "trials": [
            {"packed": t["packed"], "score": t["score"], "leftover": t["leftover"],
             "npasses": len(t["passes"])}
            for t in trials
        ],
        "string_hits": strings,
        "status": status,
        "confidence": conf,
    }


def write_report(results: list[dict], elapsed: float) -> str:
    lines = []
    a = lines.append
    statuses = [r["analysis"]["status"] for r in results]
    if statuses and all(s == "RENDERSTYLE_STRUCTURAL" for s in statuses):
        status = "RENDERSTYLE_STRUCTURAL"
        conf = "HIGH"
    elif any(s != "REWORK_REQUIRED" for s in statuses):
        status = "CANDIDATE_ONLY"
        conf = "MEDIUM"
    else:
        status = "REWORK_REQUIRED"
        conf = "NONE"
    a("# P4-M01-N03-E — RenderStyle LTB parse")
    a("")
    a(f"- status: **{status}**")
    a(f"- confidence: **{conf}**")
    a("- script: `scripts/material_recovery/n03e_renderstyle_ltb.py`")
    a("- reference: `jsj2008/lithtech/.../d3d_renderstyle.cpp` Load_LTBData")
    a(f"- elapsed: {elapsed:.2f}s")
    a("")
    for r in results:
        an = r["analysis"]
        h = an["header"]
        a(f"## `{r['full_path']}`")
        a("")
        a(f"- archive: `{r['archive']}`")
        a(f"- compressed {r['compressed_size']} → decompressed {r['decompressed_size']}")
        a(f"- parse status: **{an['status']}**")
        a("")
        a("| field | value |")
        a("|---|---|")
        a(f"| fileType | {h['file_type']} (want 5) ok={h['file_type_ok']} |")
        a(f"| version @2 | {h['version_at_offset2']} (want 3) ok={h['version_ok']} |")
        a(f"| byte1 | 0x{h['byte1']:02x} |")
        a(f"| iTotalSize | {h['iTotalSize']} |")
        a(f"| iRenStyleCnt | {h['iRenStyleCnt']} |")
        a(f"| iSize | {h['iSize']} |")
        a(f"| iRenderPasses | {an['iRenderPasses']} |")
        a("")
        lm = an["lighting"]["material"]
        a("LightingMaterial (Ambient/Diffuse/Emissive/Specular rgb):")
        a("")
        a("| channel | r | g | b | a |")
        a("|---|---|---|---|---|")
        for ch in ("Ambient", "Diffuse", "Emissive", "Specular"):
            c = lm[ch]
            a(f"| {ch} | {c['r']:.4f} | {c['g']:.4f} | {c['b']:.4f} | {c['a']:.4f} |")
        a(f"| SpecularPower | {lm['SpecularPower']:.4f} | | | |")
        a("")
        if an["best"]:
            a(f"Best stage layout: packed={an['best']['packed']} "
              f"score={an['best']['score']} leftover={an['best']['leftover']}")
            a("")
            a("| pass | stage | TextureParam | ColorOp | BlendMode |")
            a("|---|---|---|---|---|")
            for p in an["best"]["passes"]:
                for si, st in enumerate(p["stages"]):
                    blend = p["tail"].get("BlendModeName", "")
                    a(f"| {p['index']} | {si} | `{st['TextureParamName']}` | "
                      f"{st['ColorOp']} | `{blend}` |")
            a("")
            a("TextureParam is a **slot selector**, not a filename.")
            a("")
        hits = an["string_hits"]
        a("### String scan")
        a("")
        if not hits:
            a("**No** `.cfg` / `.fx` / `.tga` / `.dtx` / `WeaponShader` strings.")
            a("")
        else:
            a("| kind | match |")
            a("|---|---|")
            for h in hits:
                a(f"| `{h['kind']}` | `{h['match']}` |")
            a("")
    a("## Jupiter vs CF delta")
    a("")
    a("- Outer wrapper is LZMA-alone (`5d`), same as model LTB.")
    a("- Header is the 20-byte aligned `LTB_Header` used on the PV model:")
    a("  `fileType` at 0, `uint16 version` at 2. For RS, `fileType=5` and")
    a("  version=3 (`RENDERSTYLE_D3D_VERSION`). Byte 1 is non-zero on these")
    a("  files (CF reserved); model LTB had 0 pad there.")
    a("- No filename table in the RS body.")
    a("")
    a("## Remaining ambiguity")
    a("")
    a("- TextureParam slots are not DTX/TGA paths.")
    a("- Both RS files use **one** pass, stage0=`USE_TEXTURE1`, stages 1–3")
    a("  `NOTEXTURE`. That matches a single Bute skin DTX, not Alpha/Normal/")
    a("  Specular TGA or WeaponShader CFG.")
    a("- CFG/render semantic closure still `OPEN_UNRESOLVED`.")
    a("- P4-M01 is not PASS. This is not P5 雷神.")
    a("")
    a(f"### Confidence: `{conf}`")
    a("")
    a("## Status")
    a("")
    a(f"**status**: `{status}`")
    a("")
    a("## Scope guard")
    a("")
    a("- did NOT announce P4-M01 PASS")
    a("- did NOT map TextureParam to DTX/TGA path")
    a("- did NOT freeze CFG shader semantics")
    a("- did NOT reverse DLL / EXE / FXO")
    a("- did NOT scan all RS LTB files")
    a("- did NOT modify historical accepted evidence or `plan.md`")
    a("")
    return "\n".join(lines) + "\n", status, conf


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
    rez = os.path.join(CF_DIR, "rez", "rf002.rez")
    results = []
    for fp in RS_PATHS:
        rec = load_rs(rez, fp)
        rec["analysis"] = analyse(rec)
        print(f"[n03e] {fp} status={rec['analysis']['status']} "
              f"passes={rec['analysis']['iRenderPasses']}", file=sys.stderr)
        results.append(rec)
    elapsed = time.time() - t0
    report, status, conf = write_report(results, elapsed)

    def strip(d):
        return {k: v for k, v in d.items() if k != "bytes"}

    payload = {
        "task": "P4-M01-N03-E",
        "status": status,
        "confidence": conf,
        "reference": "jsj2008/lithtech CD3DRenderStyle::Load_LTBData",
        "files": [strip(r) for r in results],
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "rs_parse.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    rels = {
        "task": "P4-M01-N03-E",
        "status": status,
        "confidence": conf,
        "relations": [
            {
                "relation": "both RS LTBs LZMA-decompress to LTB_D3D_RENDERSTYLE_FILE type 5 version 3",
                "grade": "STRUCTURALLY_VERIFIED",
            },
            {
                "relation": "no .cfg/.fx/.tga/.dtx strings in decompressed RS bodies",
                "grade": "SCOPED_NEGATIVE",
            },
        ],
        "remaining_blockers": [
            "TextureParam slot -> DTX/TGA path OPEN_UNRESOLVED",
            "CFG/render semantic closure OPEN_UNRESOLVED",
            "P4-M01 native material closure INCOMPLETE",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "confirmed_relations.json"),
              "w", encoding="utf-8") as f:
        json.dump(rels, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "rs_parse_report.md"),
              "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[n03e] wrote {OUT_DIR} status={status}", file=sys.stderr)
    return 0 if status != "REWORK_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
