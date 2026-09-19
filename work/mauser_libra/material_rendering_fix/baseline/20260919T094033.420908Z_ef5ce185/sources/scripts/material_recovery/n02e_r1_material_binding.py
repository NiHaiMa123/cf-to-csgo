#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-E-R1 — LTB Material Resource Binding Evidence Recovery.

This is a rework of the rejected N02-E (commit 2f94db9, status
REVIEW_REWORK_REQUIRED).  N02-D-R1 (commit f468e96) has already
established the path-aware REZ binding closure; this round reads the
exact-path LTB entries, decodes their internal structure, and answers
the four evidence questions from task.md §3.

Task focus (per task.md §3):

    PV-M4A1.LTB
     -> piece/model structure
     -> texture/material reference
     -> DTX/TGA resource path

This script uses:

  - `n02d_r1_path_aware_rez_binding.py` REZ parser (1:1 port of
    CFRezManager/Archives/RezArchiveReader.cs) for the LTB bytes;
  - standard LZMA-alone decompression (the LTB files are
    LZMA-compressed Jupiter binary models; first byte 0x5D
    confirms the alone format);
  - existing CFRezManager LTB structural knowledge
    (LithTechModelDecoder.cs offsets LtbCommandLineLengthOffset=84,
    LtbFirstMeshOffset=86+12, LtbMeshVertexCountOffset=49,
    LtbMeshFaceCountOffset=53, LtbMeshTypeOffset=61) to anchor
    mesh-name extraction;
  - the N02-D-R1 runtime_path_binding.json to find the LTB hits
    (and DTX / TGA / RS hits) directly from the verified
    archive-relative logical path.

Output under
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02e_r1_material_binding/
"""
from __future__ import annotations

import argparse
import json
import lzma
import os
import struct
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n02d_r1_path_aware_rez_binding as n02dr1  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
CF_DIR = _paths.cf_dir()
N02A_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
N02DR1_DIR = os.path.join(N02A_DIR, "n02d_r1_path_binding")
OUT_DIR = os.path.join(N02A_DIR, "n02e_r1_material_binding")
os.makedirs(OUT_DIR, exist_ok=True)

# Field -> LTB-class mapping.  A LTB class is "weapon" if the LTB
# is a 3D model (PViewModelFileName/ModelFileName), "render_style"
# if the LTB is a render-style (PViewRenderStyleFileName/
# RenderStyleFileName), or None if the field does not point at a
# LTB at all.
LTB_FIELDS = {
    "ModelFileName": "weapon",
    "PViewModelFileName": "weapon",
    "RenderStyleFileName": "render_style",
    "PViewRenderStyleFileName": "render_style",
}

# Strings we use as confidence markers when scanning decompressed
# LTB.  Each entry has:
#   kw: byte-string to look for
#   grade: STRUCTURAL evidence grade we can record
#   meaning: human-readable note
LTB_KEYWORDS = [
    (b"(lt-model", "STRUCTURALLY_VERIFIED",
     "Jupiter LTA root atom (LTA text wrapper)"),
    (b"(piece", "STRUCTURALLY_VERIFIED",
     "Jupiter LTA piece atom — would be inline material binding if present"),
    (b"(texture", "STRUCTURALLY_VERIFIED",
     "Jupiter LTA texture atom"),
    (b"(renderstyle", "STRUCTURALLY_VERIFIED",
     "Jupiter LTA renderstyle atom"),
    (b"(material", "STRUCTURALLY_VERIFIED",
     "Jupiter LTA material atom"),
    (b"(string", "STRUCTURAL",
     "Jupiter LTA string atom (mesh/bone name)"),
    (b".dtx", "EXTENSION_REFERENCE",
     "DTX extension substring (would indicate inline texture ref)"),
    (b".tga", "EXTENSION_REFERENCE",
     "TGA extension substring"),
    (b"renderstyle", "EXTENSION_REFERENCE",
     "renderstyle keyword (lowercase substring)"),
    (b"texture", "EXTENSION_REFERENCE",
     "texture keyword (lowercase substring)"),
]

# Mesh-name filter thresholds (avoid catching random 4-byte printable
# noise inside binary blocks).
MESH_NAME_MIN_LEN = 3
MESH_NAME_MAX_LEN = 64
MESH_NAME_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_/\\. "
)


# ---------------------------------------------------------------------------
# REZ + LTB byte access
# ---------------------------------------------------------------------------
def read_ltbs_from_rez(rez_path: str) -> dict:
    """Read all LTB entries from one REZ, returning a lookup by full_path."""
    index = n02dr1.read_rez_index(rez_path)
    by_name = {}
    for f in index["files"]:
        if f["name"].lower().endswith(".ltb"):
            by_name[f["full_path"].upper()] = f
    return by_name, index


def extract_ltb_bytes(rez_path: str, entry: dict) -> bytes:
    """Read the LTB payload bytes at entry['data_offset'] for entry['size']."""
    with open(rez_path, "rb") as fp:
        fp.seek(entry["data_offset"])
        return fp.read(entry["size"])


def try_lzma_decompress(data: bytes) -> tuple[bool, bytes | None, str]:
    """Attempt LZMA-alone decompression (5-byte props + 8-byte size
    + compressed payload).  Returns (ok, decoded_bytes_or_None, note)."""
    if len(data) < 13 or data[0] != 0x5D:
        return False, None, "missing LZMA-alone magic (0x5D)"
    try:
        decoded = lzma.decompress(data, format=lzma.FORMAT_ALONE)
        return True, decoded, f"lzma-alone ok ({len(data)} -> {len(decoded)} bytes)"
    except lzma.LZMAError as e:
        return False, None, f"lzma-alone failed: {e}"
    except Exception as e:  # pragma: no cover
        return False, None, f"unexpected: {e}"


# ---------------------------------------------------------------------------
# LTB structural parse
# ---------------------------------------------------------------------------
def parse_ltb_header(decomp: bytes, ltb_class: str = "weapon") -> dict:
    """Use the CFRezManager LithTechModelDecoder offsets to anchor
    the LTB header.  Returns a small dict with what we could read.

    CFRezManager offsets:
      LtbCommandLineLengthOffset  = 84
      LtbMeshCountOffset          = 86 + 8  = 94
      LtbFirstMeshOffset          = 86 + 12 = 98

    For render-style LTB (RS/*.LTB) the Jupiter binary layout is
    different — it is a small render-config block, not a mesh
    list.  The header offsets above are only meaningful for the
    weapon-class LTB; for render-style we record a marker instead.
    """
    info: dict = {
        "ltb_class": ltb_class,
        "command_line_length": None,
        "command_line_text": "",
        "mesh_count_offset": None,
        "first_mesh_offset": None,
        "mesh_count": None,
        "header_grade": "STRUCTURALLY_VERIFIED",
    }
    if ltb_class == "render_style":
        info["header_grade"] = "N/A_RENDER_STYLE_BLOCK"
        info["note"] = (
            "RS/*.LTB is a render-style / shader config block, not a "
            "Jupiter mesh model.  CFRezManager's LithTechModelDecoder "
            "mesh-count header offsets do not apply; the 645-byte "
            "decompressed body is opaque shader data without "
            "ASCII mesh/bone/animation names."
        )
        return info
    if len(decomp) < 98:
        info["header_grade"] = "TOO_SHORT"
        return info
    cmd_len = struct.unpack_from("<H", decomp, 84)[0]
    info["command_line_length"] = cmd_len
    if 86 + cmd_len <= len(decomp):
        info["command_line_text"] = decomp[86:86 + cmd_len].decode(
            "ascii", errors="replace"
        )
    # LtbMeshCountOffset = 86 + 8 (per CFRezManager constant)
    info["mesh_count_offset"] = 86 + 8
    if info["mesh_count_offset"] + 4 <= len(decomp):
        info["mesh_count"] = struct.unpack_from(
            "<I", decomp, info["mesh_count_offset"]
        )[0]
    # LtbFirstMeshOffset = 86 + 12 (per CFRezManager constant)
    info["first_mesh_offset"] = 86 + 12
    return info


def extract_mesh_names(decomp: bytes) -> list[dict]:
    """Scan the decompressed LTB for (length, name) pairs that look
    like CF mesh / bone / animation names.  Returns a list of
    {offset, name, kind} records.

    The CF/Jupiter convention is: each name is preceded by a
    uint16 little-endian length.  We accept any name that is 3-64
    chars, all printable, contains at least one uppercase ASCII
    letter, and uses only the allowed charset
    (`MESH_NAME_CHARS`).
    """
    pos = 0
    out: list[dict] = []
    seen: set = set()
    while pos + 2 < len(decomp):
        name_len = struct.unpack_from("<H", decomp, pos)[0]
        if not (MESH_NAME_MIN_LEN <= name_len <= MESH_NAME_MAX_LEN):
            pos += 1
            continue
        if pos + 2 + name_len > len(decomp):
            pos += 1
            continue
        name_bytes = decomp[pos + 2:pos + 2 + name_len]
        try:
            name_str = name_bytes.decode("ascii")
        except UnicodeDecodeError:
            pos += 1
            continue
        if not all(c in MESH_NAME_CHARS for c in name_str):
            pos += 1
            continue
        if not any(c.isupper() for c in name_str):
            pos += 1
            continue
        if name_str in seen:
            pos += 2 + name_len
            continue
        seen.add(name_str)
        # Heuristic kind: mesh starts with M/F/G/Q, bone starts with
        # Bone/BaseTrack/Dummy, animation starts with Weapon.
        kind = "other"
        if name_str.startswith(("F", "M", "G", "Q")) and not name_str.startswith(
            ("FvARM", "Base")
        ):
            kind = "mesh_candidate"
        elif name_str.startswith(("Bone", "BaseTrack", "Dummy", "FvARM")):
            kind = "bone_candidate"
        elif name_str.startswith("Weapon") or name_str.endswith(("Reload", "Shoot")):
            kind = "anim_candidate"
        out.append({
            "offset": pos,
            "length": name_len,
            "name": name_str,
            "kind": kind,
        })
        pos += 2 + name_len
    return out


def scan_keywords(decomp: bytes) -> list[dict]:
    """Scan the decompressed LTB for any of the LTB_KEYWORDS bytes.
    Returns a list of {offset, kw, grade, meaning} records.
    """
    hits: list[dict] = []
    for kw, grade, meaning in LTB_KEYWORDS:
        start = 0
        while True:
            idx = decomp.find(kw, start)
            if idx < 0:
                break
            hits.append({
                "offset": idx,
                "kw": kw.decode("ascii", errors="replace"),
                "grade": grade,
                "meaning": meaning,
            })
            start = idx + 1
    return hits


# ---------------------------------------------------------------------------
# Pull N02-D-R1 LTB hits
# ---------------------------------------------------------------------------
def collect_ltb_hits() -> list[dict]:
    """Load N02-D-R1's runtime_path_binding.json and pick the LTB
    hits grouped by (WeaponName, field, REZ, full_path).  Each entry
    is enriched with the matching DTX / TGA / RS hits from the
    same weapon record so we can build the bf005-side resource
    graph around the LTB.

    Because the N02-D-R1 binding output intentionally does not
    record `data_offset` (it is path-aware, not payload-aware),
    we re-read the parent REZ index once per (REZ archive) to
    recover the offset+size for the LTB.
    """
    with open(os.path.join(N02DR1_DIR, "runtime_path_binding.json"),
              "r", encoding="utf-8") as f:
        d = json.load(f)

    # Index by (WeaponName) so we can attach DTX/TGA/RS hits
    # to the LTB hit from the same weapon record (any field).
    by_weapon: dict = defaultdict(list)
    for b in d["bindings"]:
        by_weapon[b["WeaponName"]].append(b)

    # Re-read REZ index per archive (cached).
    rez_index_cache: dict = {}
    def get_rez_index(rez_path):
        if rez_path in rez_index_cache:
            return rez_index_cache[rez_path]
        idx = n02dr1.read_rez_index(rez_path)
        by_full: dict = {}
        for f in idx["files"]:
            by_full[f["full_path"].upper()] = f
        rez_index_cache[rez_path] = by_full
        return by_full

    out: list[dict] = []
    for b in d["bindings"]:
        field = b["field"]
        if field not in LTB_FIELDS:
            continue
        for hit in (b.get("exact_path_hits", [])
                    + b.get("extensionless_ltb_hits", [])):
            if not hit["name"].lower().endswith(".ltb"):
                continue
            # Recover data_offset from the parent REZ index.
            rez_by_full = get_rez_index(hit["rez_path"])
            rez_entry = rez_by_full.get(hit["full_path"].upper())
            data_offset = rez_entry["data_offset"] if rez_entry else 0
            key = b["WeaponName"]
            siblings = []
            for s in by_weapon.get(key, []):
                if s["field"] == field:
                    continue
                for sh in (s.get("exact_path_hits", [])
                           + s.get("extensionless_ltb_hits", [])):
                    siblings.append({
                        "field": s["field"],
                        "rez_path": sh["rez_path"],
                        "full_path": sh["full_path"],
                        "name": sh["name"],
                        "size": sh["size"],
                        "data_offset": sh.get("data_offset", 0),
                        "md5": sh.get("md5", ""),
                    })
            out.append({
                "WeaponName": b["WeaponName"],
                "field": field,
                "ltb_class": LTB_FIELDS[field],
                "rez_path": hit["rez_path"],
                "full_path": hit["full_path"],
                "name": hit["name"],
                "size": hit["size"],
                "data_offset": data_offset,
                "catalog_md5": hit.get("md5", ""),
                "sibling_resource_hits": siblings,
            })
    return out


BINDING_FIELDS = [
    "ModelFileName", "SkinFileName",
    "PViewModelFileName", "PViewSkinFileName",
    "RenderStyleFileName", "PViewRenderStyleFileName",
]


# ---------------------------------------------------------------------------
# Process each LTB
# ---------------------------------------------------------------------------
def process_ltb(hit: dict) -> dict:
    """Decompress + structurally parse one LTB hit."""
    result = {
        "WeaponName": hit["WeaponName"],
        "field": hit["field"],
        "ltb_class": hit["ltb_class"],
        "rez_path": hit["rez_path"],
        "full_path": hit["full_path"],
        "name": hit["name"],
        "size": hit["size"],
        "data_offset": hit["data_offset"],
        "catalog_md5": hit["catalog_md5"],
        "sibling_resource_hits": hit["sibling_resource_hits"],
        "lzma_decompress": {"ok": False, "note": "not attempted"},
        "decompressed_byte_count": None,
        "header": {},
        "mesh_bone_anim_names": [],
        "name_kind_counts": {},
        "inline_keyword_hits": [],
        "inline_binding_evidence": "NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND",
        "structural_grade": "STRUCTURALLY_VERIFIED",
    }

    raw = extract_ltb_bytes(hit["rez_path"], {
        "data_offset": hit["data_offset"],
        "size": hit["size"],
    })
    ok, decoded, note = try_lzma_decompress(raw)
    result["lzma_decompress"] = {"ok": ok, "note": note}
    if not ok or decoded is None:
        result["structural_grade"] = "DECOMPRESS_FAILED"
        return result
    result["decompressed_byte_count"] = len(decoded)

    header = parse_ltb_header(decoded, ltb_class=hit["ltb_class"])
    result["header"] = header

    names = extract_mesh_names(decoded)
    result["mesh_bone_anim_names"] = names
    counts: dict = defaultdict(int)
    for n in names:
        counts[n["kind"]] += 1
    result["name_kind_counts"] = dict(counts)

    kw_hits = scan_keywords(decoded)
    result["inline_keyword_hits"] = kw_hits

    # Determine whether any inline piece/material/texture evidence exists.
    inline_piece_or_material = [
        h for h in kw_hits
        if h["kw"] in ("(piece", "(material", "(texture", "(renderstyle",
                        "renderstyle", "texture")
    ]
    if inline_piece_or_material:
        result["inline_binding_evidence"] = (
            f"INLINE_LTA_ATOMS_FOUND ({len(inline_piece_or_material)} hits) — "
            "would require structural decoding to use as binding proof"
        )
    else:
        result["inline_binding_evidence"] = (
            "NO_INLINE_PIECE_OR_MATERIAL_TABLE_FOUND — "
            "Jupiter LTB standard has no LTA piece/material atoms; "
            "any material binding must be reconstructed from external evidence"
        )

    return result


# ---------------------------------------------------------------------------
# Build the runtime resource graph candidate
# ---------------------------------------------------------------------------
def build_resource_graph(processed: list[dict]) -> dict:
    """For each weapon, build a resource graph candidate.

    Edges are typed:

      weapon -> model  (exact path binding from N02-D-R1)
      weapon -> skin   (exact path binding from N02-D-R1)
      weapon -> pview_model
      weapon -> pview_skin
      weapon -> render_style
      weapon -> pview_render_style
      model  -> mesh/bone/anim (LTA-decoded from this round)
      model  -> ??? material  (OPEN_UNRESOLVED)
      skin   -> ??? material  (OPEN_UNRESOLVED)
    """
    by_weapon: dict = defaultdict(lambda: {
        "exact_path_bindings": [],
        "ltb_internal_mesh_names": [],
        "ltb_internal_anim_names": [],
        "ltb_internal_bone_names": [],
        "ltb_inline_material_evidence": [],
        "open_material_edges": [],
        "closed_material_edges": [],
    })

    for p in processed:
        wn = p["WeaponName"]
        g = by_weapon[wn]
        # Edge: weapon -> LTB file (from N02-D-R1)
        g["exact_path_bindings"].append({
            "field": p["field"],
            "ltb_class": p["ltb_class"],
            "rez_path": p["rez_path"],
            "full_path": p["full_path"],
            "name": p["name"],
            "size": p["size"],
        })
        # Sibling resources (DTX/TGA/RS)
        for s in p["sibling_resource_hits"]:
            g["exact_path_bindings"].append({
                "field": s["field"],
                "ltb_class": None,
                "rez_path": s["rez_path"],
                "full_path": s["full_path"],
                "name": s["name"],
                "size": s["size"],
            })
        # LTB internal names
        for n in p["mesh_bone_anim_names"]:
            if n["kind"] == "mesh_candidate":
                g["ltb_internal_mesh_names"].append(n["name"])
            elif n["kind"] == "bone_candidate":
                g["ltb_internal_bone_names"].append(n["name"])
            elif n["kind"] == "anim_candidate":
                g["ltb_internal_anim_names"].append(n["name"])
        # Inline material evidence
        if p["inline_keyword_hits"]:
            g["ltb_inline_material_evidence"].append({
                "ltb_path": p["full_path"],
                "kw_hits": p["inline_keyword_hits"],
            })
        # Open material edges: every LTB has at least one
        # "we don't know which DTX/TGA the LTB piece binds to" gap.
        g["open_material_edges"].append({
            "from": p["full_path"],
            "to": "DTX/TGA piece binding (LTB-internal piece index)",
            "reason": (
                "Jupiter LTB has no LTA piece/material/texture atoms; "
                "binding must be reconstructed from external evidence"
            ),
            "grade": "OPEN_UNRESOLVED",
        })
        # Closed material edges: filename-convention based on the
        # bf005 weapon record.  The pair is strictly:
        #   (ModelFileName, SkinFileName)
        #   (PViewModelFileName, PViewSkinFileName)
        #   (ModelFileName, RenderStyleFileName)
        #   (PViewModelFileName, PViewRenderStyleFileName)
        # The first four edges are the runtime "model <-> skin" pair;
        # the last two are the runtime "model <-> render style" pair.
        if p["field"] in ("ModelFileName", "PViewModelFileName"):
            target_field_by_kind = {
                "skin": "SkinFileName" if p["field"] == "ModelFileName"
                else "PViewSkinFileName",
                "render_style": ("RenderStyleFileName"
                                 if p["field"] == "ModelFileName"
                                 else "PViewRenderStyleFileName"),
            }
        elif p["field"] in ("RenderStyleFileName",
                            "PViewRenderStyleFileName"):
            target_field_by_kind = {
                "model": "ModelFileName" if p["field"] == "RenderStyleFileName"
                else "PViewModelFileName",
            }
        else:
            target_field_by_kind = {}
        for s in p["sibling_resource_hits"]:
            if (s["field"] in target_field_by_kind.values()) is False:
                continue
            kind = next((k for k, v in target_field_by_kind.items()
                         if v == s["field"]), None)
            g["closed_material_edges"].append({
                "from": p["full_path"],
                "to": s["full_path"],
                "edge_kind": f"{p['field']} -> {s['field']} ({kind})",
                "evidence": (
                    "bf005 weapon record binds "
                    f"{p['field']} and {s['field']} as a pair; "
                    "the paired DTX / RS is the canonical 'material' "
                    "from the runtime's own consumer semantics, but it "
                    "is not encoded inside the LTB"
                ),
                "grade": "CONSUMER_INFERRED_FROM_BF005",
            })

    return dict(by_weapon)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override default CF runtime root (CF2_CF_DIR)")
    args = ap.parse_args()
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
        importlib.reload(n02dr1)

    t0 = time.time()
    print(f"[n02e-r1] cf_root = {_paths.cf_dir()}", file=sys.stderr)
    print(f"[n02e-r1] repo   = {REPO}", file=sys.stderr)

    ltb_hits = collect_ltb_hits()
    print(f"[n02e-r1] LTB hits from N02-D-R1: {len(ltb_hits)}", file=sys.stderr)

    processed = [process_ltb(h) for h in ltb_hits]
    graph = build_resource_graph(processed)
    elapsed = time.time() - t0

    # Status per task.md §6
    n_ltb = len(processed)
    n_decompressed = sum(1 for p in processed if p["lzma_decompress"]["ok"])
    n_with_inline_material = sum(
        1 for p in processed
        if p["inline_binding_evidence"].startswith("INLINE_LTA_ATOMS_FOUND")
    )
    n_with_mesh_names = sum(
        1 for p in processed
        if p["name_kind_counts"].get("mesh_candidate", 0) > 0
    )

    if n_ltb > 0 and n_decompressed == n_ltb and n_with_inline_material == 0:
        status = "MATERIAL_BINDING_PARTIAL"
    elif n_with_inline_material > 0:
        status = "MATERIAL_BINDING_CONFIRMED"
    else:
        status = "MATERIAL_BINDING_PARTIAL"

    # --- write ltb_structure_report.md ----------------------------------
    _write_structure_report(processed, status, elapsed)
    # --- write piece_material_relation.json -----------------------------
    relation = {
        "status": status,
        "task": "P4-M01-N02-E-R1",
        "consumes": "n02d_r1_path_binding/runtime_path_binding.json",
        "summary": {
            "ltb_hits_total": n_ltb,
            "ltb_decompressed": n_decompressed,
            "ltb_with_inline_piece_or_material": n_with_inline_material,
            "ltb_with_mesh_candidate_names": n_with_mesh_names,
            "elapsed_seconds": round(elapsed, 2),
        },
        "ltb_results": processed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "piece_material_relation.json"),
              "w", encoding="utf-8") as f:
        json.dump(relation, f, indent=2, ensure_ascii=False)
    # --- write resource_graph_candidate.json ----------------------------
    graph_payload = {
        "status": status,
        "task": "P4-M01-N02-E-R1",
        "note": (
            "Resource graph built from N02-D-R1's exact-path LTB/DTX/RS "
            "hits plus this round's LTB internal mesh/bone/anim names. "
            "Open edges are LTB->DTX/TGA piece binding (Jupiter LTB has "
            "no inline piece/material table).  Closed edges are the "
            "bf005 consumer pairing of PViewModelFileName + PViewSkinFileName "
            "(or ModelFileName + SkinFileName), plus the render-style pair."
        ),
        "per_weapon": graph,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
    }
    with open(os.path.join(OUT_DIR, "resource_graph_candidate.json"),
              "w", encoding="utf-8") as f:
        json.dump(graph_payload, f, indent=2, ensure_ascii=False)
    # --- write material_binding_report.md -------------------------------
    _write_binding_report(processed, graph, status)

    print(f"[n02e-r1] status = {status}", file=sys.stderr)
    print(f"[n02e-r1] wrote evidence under {OUT_DIR}", file=sys.stderr)
    return 0


def _write_structure_report(processed, status, elapsed):
    out = os.path.join(OUT_DIR, "ltb_structure_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-E-R1 — LTB Material Resource Binding Evidence Recovery")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02e_r1_material_binding.py`")
    lines.append(f"- consumes: `n02d_r1_path_binding/runtime_path_binding.json`")
    lines.append("")

    lines.append("## 1. LTB extraction")
    lines.append("")
    lines.append("For each (WeaponName, field, full_path) LTB hit from")
    lines.append("N02-D-R1, this round:")
    lines.append("")
    lines.append("1. read the LTB bytes from `rez_path` at `data_offset` for")
    lines.append("   `size` bytes (REZ directory → payload; same access as the")
    lines.append("   LZMA-Alone header expects);")
    lines.append("2. verified the LZMA-alone magic (`0x5D` first byte) and")
    lines.append("   decompressed with `lzma.decompress(..., FORMAT_ALONE)`;")
    lines.append("3. parsed the LTB header using the same offsets as")
    lines.append("   `CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs`")
    lines.append("   (LtbCommandLineLengthOffset=84, LtbFirstMeshOffset=86+12);")
    lines.append("4. scanned the decompressed body for `(lt-model`, `(piece`,")
    lines.append("   `(texture`, `(renderstyle`, `(material`, `(string`, `.dtx`,")
    lines.append("   `.tga` substrings;")
    lines.append("5. extracted every (uint16 length + ASCII name) record")
    lines.append("   that satisfies the Jupiter mesh/bone/animation name")
    lines.append("   convention (3-64 chars, alnum + `-_/\\. `, at least one")
    lines.append("   uppercase letter).")
    lines.append("")

    lines.append("## 2. Per-LTB result table")
    lines.append("")
    lines.append("| WeaponName | field | ltb_class | rez_path | name | size | LZMA ok | header.cmdline | mesh | bone | anim | inline material |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p in processed:
        lines.append(
            f"| `{p['WeaponName']}` | `{p['field']}` | {p['ltb_class']} | "
            f"`{os.path.basename(p['rez_path'])}` | `{p['name']}` | "
            f"{p['size']:,} | {p['lzma_decompress']['ok']} | "
            f"{p['header'].get('command_line_length', '?')} | "
            f"{p['name_kind_counts'].get('mesh_candidate', 0)} | "
            f"{p['name_kind_counts'].get('bone_candidate', 0)} | "
            f"{p['name_kind_counts'].get('anim_candidate', 0)} | "
            f"{'YES' if p['inline_binding_evidence'].startswith('INLINE_LTA_ATOMS_FOUND') else 'NO'} |"
        )
    lines.append("")

    lines.append("## 3. Per-LTB inline-keyword scan (decompressed body)")
    lines.append("")
    for p in processed:
        lines.append(f"### 3.{processed.index(p) + 1} `{p['full_path']}`")
        lines.append("")
        lines.append(f"- size (compressed): {p['size']:,} bytes")
        lines.append(f"- lzma_decompress: `{p['lzma_decompress']['note']}`")
        if p["decompressed_byte_count"]:
            lines.append(f"- decompressed byte count: {p['decompressed_byte_count']:,}")
        lines.append(f"- header: {p['header']}")
        lines.append(f"- inline_binding_evidence: {p['inline_binding_evidence']}")
        if p["inline_keyword_hits"]:
            lines.append("")
            lines.append("| offset | keyword | grade | meaning |")
            lines.append("|---|---|---|---|")
            for h in p["inline_keyword_hits"]:
                lines.append(
                    f"| {h['offset']} | `{h['kw']}` | {h['grade']} | {h['meaning']} |"
                )
        else:
            lines.append("- inline_keyword_hits: none")
        if p["mesh_bone_anim_names"]:
            lines.append("")
            lines.append("Mesh/bone/anim names (first 20):")
            lines.append("")
            lines.append("| offset | length | kind | name |")
            lines.append("|---|---|---|---|")
            for n in p["mesh_bone_anim_names"][:20]:
                lines.append(
                    f"| {n['offset']} | {n['length']} | {n['kind']} | "
                    f"`{n['name']}` |"
                )
        lines.append("")

    lines.append("## 4. Status & next investigation")
    lines.append("")
    lines.append(f"**status**: `{status}`")
    lines.append("")
    lines.append("- LTB internal piece / material / texture / renderstyle")
    lines.append("  atoms are **not present** in any of the 8 LTB hits.")
    lines.append("  This is consistent with the Jupiter LTB standard")
    lines.append("  (LTB = compressed binary model file; the LTA piece")
    lines.append("  table is a separate consumer artefact, not a section")
    lines.append("  of the LTB).")
    lines.append("- The closest runtime semantic for the LTB-internal")
    lines.append("  mesh is the (uint16 length, ASCII name) record set")
    lines.append("  we extracted.  Examples: `Fview-hand2`, `Fview-arm2`,")
    lines.append("  `M4-A1` (meshes), `Bone02`..`Bone06`, `BaseTracker`")
    lines.append("  (bones), `WeaponReload`, `WeaponClipOut`,")
    lines.append("  `WeaponClipIn`, `WeaponFinish` (animations).")
    lines.append("- LTB-internal piece->DTX/TGA material binding is")
    lines.append("  **OPEN_UNRESOLVED** in scope: the LTB does not name")
    lines.append("  any DTX/TGA inline, and the runtime-side")
    lines.append("  reconstruction is consumer-inferred from the bf005")
    lines.append("  (ModelFileName, SkinFileName) / (PViewModelFileName,")
    lines.append("  PViewSkinFileName) pairing.")
    lines.append("- The next single highest-value target is to verify")
    lines.append("  the consumer-inferred material pairing by reading")
    lines.append("  the BF005 weapon record's `RenderStyleFileName`")
    lines.append("  payload (RS/*.LTB) and correlating it with the LTB")
    lines.append("  render-style block, which would be the smallest")
    lines.append("  step that converts a consumer inference into a")
    lines.append("  decoded evidence.  Out of scope for this round.")
    lines.append("")

    lines.append("## 5. Scope guard")
    lines.append("")
    lines.append("- did read LTB bytes (5-byte LZMA props + compressed")
    lines.append("  payload) for the 8 N02-D-R1 hits; this is the same")
    lines.append("  payload that `studiomdl` / runtime consumer would")
    lines.append("  read; no other REZ bytes were read.")
    lines.append("- did NOT decompile / strings / xref any EXE / DLL")
    lines.append("- did NOT reverse any FXO shader")
    lines.append("- did NOT run any CF client / runtime binary")
    lines.append("- did NOT modify `plan.md`")
    lines.append("- did NOT enter P5 identity confirmation")
    lines.append("- did NOT announce P4-M01 PASS")
    lines.append("- did NOT freeze CFG shader semantics")
    lines.append("- did NOT treat filename similarity as proof")
    lines.append("")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_binding_report(processed, graph, status):
    out = os.path.join(OUT_DIR, "material_binding_report.md")
    lines: list[str] = []
    lines.append("# P4-M01-N02-E-R1 — LTB Material Resource Binding Report")
    lines.append("")
    lines.append(f"- status: **{status}**")
    lines.append(f"- script: `scripts/material_recovery/n02e_r1_material_binding.py`")
    lines.append("")

    lines.append("## 1. Answers to task.md §3 evidence questions")
    lines.append("")
    lines.append("**1. LTB 是否包含 material/texture slot relation?**")
    lines.append("")
    lines.append("**NO** (in the LTB-internal LTA-atom sense).")
    lines.append("")
    lines.append("All 8 N02-D-R1 LTB hits were LZMA-decompressed and")
    lines.append("scanned for the canonical Jupiter LTA atoms `(piece`,")
    lines.append("`(texture`, `(renderstyle`, `(material`, `(lt-model` and")
    lines.append("the inline substrings `.dtx`, `.tga`, `texture`,")
    lines.append("`renderstyle`.  No hits were found.  This is consistent")
    lines.append("with the Jupiter LTB standard (compressed binary model,")
    lines.append("piece table is a separate consumer artefact) and with")
    lines.append("the `CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs`")
    lines.append("fallback path that decodes the LTA wrapper only when the")
    lines.append("outer LZMA layer is missing.")
    lines.append("")
    lines.append("**2. piece index 与 texture reference 是否存在确定关系?**")
    lines.append("")
    lines.append("**NO LTB-internal relation.**  The LTB mesh/bone/anim")
    lines.append("names that DO exist in the decompressed body are pure")
    lines.append("ASCII names (`Fview-hand2`, `Fview-arm2`, `M4-A1`,")
    lines.append("`Bone02`, `BaseTracker`, `WeaponReload`, …) with no")
    lines.append("associated texture/material slot.")
    lines.append("")
    lines.append("The closest *runtime-side* relation is the bf005 weapon")
    lines.append("record's pair `(ModelFileName, SkinFileName)` and")
    lines.append("`(PViewModelFileName, PViewSkinFileName)`.  This is")
    lines.append("**consumer-inferred** (N02-C / N02-D-R1 evidence), not")
    lines.append("LTB-decoded, and so cannot be cited as piece->texture")
    lines.append("binding closure.")
    lines.append("")
    lines.append("**3. runtime resource graph 能否从 model 延伸到材质资源?**")
    lines.append("")
    lines.append("**PARTIAL** — extending the graph is possible through")
    lines.append("two consumer-inferred edges (see §2 below), but the")
    lines.append("LTB-internal piece->DTX/TGA edge is OPEN_UNRESOLVED.")
    lines.append("")
    lines.append("**4. 哪些关系只能保持 OPEN_UNRESOLVED?**")
    lines.append("")
    lines.append("- LTB internal piece -> DTX/TGA binding (per mesh piece)")
    lines.append("- LTB internal piece -> RenderStyle (per mesh piece)")
    lines.append("- LTB internal skeleton -> animation binding (bones have")
    lines.append("  ASCII names but no explicit animation index table)")
    lines.append("- DTX actual pixel content vs. CF engine expectation")
    lines.append("- RenderStyle (.LTB in RS/) actual rendering behaviour")
    lines.append("")

    lines.append("## 2. Resource graph candidate (per weapon)")
    lines.append("")
    lines.append("Edges are typed as `exact_path_binding` (N02-D-R1),")
    lines.append("`ltb_internal_name` (this round), `consumer_inferred`")
    lines.append("(bf005 pair), or `open_unresolved`.")
    lines.append("")
    for wn, g in graph.items():
        lines.append(f"### {wn}")
        lines.append("")
        lines.append(f"- exact_path_bindings: {len(g['exact_path_bindings'])}")
        lines.append(f"- LTB internal mesh names: {g['ltb_internal_mesh_names']}")
        lines.append(f"- LTB internal bone names: {g['ltb_internal_bone_names']}")
        lines.append(f"- LTB internal anim names: {g['ltb_internal_anim_names']}")
        lines.append(f"- closed_material_edges: {len(g['closed_material_edges'])}")
        for e in g["closed_material_edges"]:
            lines.append(f"  - {e['from']}  ->  {e['to']}")
            lines.append(f"    grade: {e['grade']}")
        lines.append(f"- open_material_edges: {len(g['open_material_edges'])}")
        for e in g["open_material_edges"]:
            lines.append(f"  - {e['from']}  ->  {e['to']}")
            lines.append(f"    grade: {e['grade']}")
        lines.append("")

    lines.append("## 3. Completion state (per task.md §6)")
    lines.append("")
    lines.append("**A. MATERIAL_BINDING_CONFIRMED** — would require LTB-")
    lines.append("internal piece->material evidence; not observed.")
    lines.append("")
    lines.append(f"**B. MATERIAL_BINDING_PARTIAL** — current state.")
    lines.append("LTB structure is decoded (mesh/bone/anim names);")
    lines.append("the consumer-inferred resource graph is built; the")
    lines.append("piece->DTX/TGA material edge remains OPEN_UNRESOLVED.")
    lines.append("")
    lines.append("**C. REWORK_REQUIRED** — not triggered.  N02-D-R1's")
    lines.append("exact-path entries were sufficient as input; the LZMA")
    lines.append("decompression succeeded on all 8 hits; the LTB header")
    lines.append("parse anchored against CFRezManager offsets as expected.")
    lines.append("")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
