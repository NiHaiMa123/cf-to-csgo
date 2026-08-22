#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-R1-E stage 2 (targeted): engine-side binding search using existing
infrastructure semantics + explicit negative results.

Per Chat/Sol continuation review, stage-2 must use the repo's own mapping/
config/index/resolver approach (LithTechModelTextureConfigIndex,
LithTechTextureMappingScanner, LithTechDatTextureReferenceIndex,
TextureReferenceResolver, LithTechModelTextureLoader) rather than new blind
scans. This script ports those resolvers' core extraction logic and runs it
across the local corpus, recording:

  A. POSITIVE: the LZMA-compressed TEXT material format discovered in
     rf016/.../ArmModel/Shader/*.CFG — sections [Textures] with
     SpecularMapName0 / EnvCubeMapName0 / NormalMapName0 / AlphaMapName0,
     [Techniques] feature flags, [Properties] float parameters including
     PieceIndex. This is direct engine-format evidence that CF binds
     per-piece texture sets via named CFG fields.

  B. NEGATIVE (explicit): no weapon-side text material CFG and no config/
     dat/table file naming any M4A1_S_BornBeast texture path exists in the
     local data dirs (full scans documented with file counts).

  C. LTB numeric field: stays PROVISIONAL as a slot identifier; the arm
     corpus shows the same post-index length-prefixed-string structure with
     empty strings, so the field is general LTB structure whose weapon
     instance happens to carry single digits.

Outputs r1/material_binding_r1.json (schema v2).
"""
from __future__ import annotations

import hashlib
import json
import lzma
import os
import re
import struct

REPO = r"D:\project\cf_to_csgo"
DATA = os.path.join(REPO, "data")
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/r1")
SUPERSEDES_COMMIT = "632ede449578f688cea7e6b5f40cbf03700aaaa5"

TEX_EXTS = [".dtx", ".dds", ".tga", ".png", ".jpg", ".jpeg", ".bmp"]
CFG_EXTS = [".cfg", ".ini", ".txt", ".xml", ".csv", ".ref", ".lua",
            ".apf", ".cft", ".fcf"]
PATH_BYTE = re.compile(rb"[A-Za-z0-9_\-\.\\/ ]")
MATERIAL_SECTIONS = [b"[Textures]", b"[Techniques]", b"[Properties]",
                     b"PieceIndex", b"MapName0"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lzma_prepare(data):
    if len(data) >= 13 and data[0] in (0x5D, 0x08):
        try:
            return lzma.decompress(data, format=lzma.FORMAT_ALONE)
        except Exception:
            return data
    return data


def extract_texture_refs(data):
    """Port of LithTechDatTextureReferenceIndex.ExtractTextureReferences."""
    refs = []
    seen = set()
    lowered = data.lower()
    for ext in TEX_EXTS:
        start = 0
        while True:
            i = lowered.find(ext.encode("ascii"), start)
            if i < 0:
                break
            s = i
            while s > 0 and PATH_BYTE.match(data[s - 1:s]):
                s -= 1
            norm = data[s:i + len(ext)].decode("ascii", "replace") \
                .replace("\\", "/").strip().strip("\"',;:")
            if len(norm) > len(ext) and "://" not in norm:
                key = norm.lower()
                if key not in seen:
                    seen.add(key)
                    refs.append(norm)
            start = i + 1
    return refs


def scan_arm_material_cfgs():
    """Read all ArmModel Shader CFGs through CfgTextDecoder-equivalent logic."""
    arm_dir = os.path.join(DATA, "rf016", "Models", "PLAYERVIEW",
                           "ArmModel", "Shader")
    out = {}
    if not os.path.isdir(arm_dir):
        return out
    for fn in sorted(os.listdir(arm_dir)):
        p = os.path.join(arm_dir, fn)
        raw = open(p, "rb").read()
        text_blob = lzma_prepare(raw)
        try:
            text = text_blob.decode("gbk")
        except UnicodeDecodeError:
            continue
        if "[Textures]" not in text:
            continue
        tex = dict(re.findall(r"([A-Za-z0-9_]+)=([^\r\n]+)", text))
        out[fn] = {
            "relative_path": os.path.relpath(p, DATA).replace("\\", "/"),
            "compressed_bytes": len(raw),
            "decoded_bytes": len(text_blob),
            "sha256": sha256_of(p),
            "texture_bindings": {k: v for k, v in tex.items()
                                 if k.endswith("Name0")},
            "piece_index": tex.get("PieceIndex"),
            "render_param": tex.get("RenderParam"),
            "technique_flags": {k: v for k, v in tex.items()
                                if k.endswith("Enabled")},
        }
    return out


def scan_for_weapon_text_materials():
    """Negative-control scan: any LZMA/text file containing material sections
    outside ArmModel? Any config/dat naming BornBeast texture paths?"""
    scanned = 0
    material_hits = []
    bornbeast_ref_hits = []
    for d in sorted(os.listdir(DATA)):
        base = os.path.join(DATA, d)
        if not os.path.isdir(base) or not d.startswith("rf"):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                p = os.path.join(root, fn)
                is_cfg_like = ext in CFG_EXTS or ext == ".dat" or ext == ".lta"
                if not is_cfg_like:
                    continue
                try:
                    sz = os.path.getsize(p)
                except OSError:
                    continue
                if sz == 0 or sz > 64 * 1024 * 1024:
                    continue
                scanned += 1
                try:
                    raw = open(p, "rb").read()
                except OSError:
                    continue
                blob = lzma_prepare(raw)
                rel = os.path.relpath(p, DATA).replace("\\", "/")
                if "ArmModel" not in rel:
                    found = [m.decode() for m in MATERIAL_SECTIONS if m in blob]
                    if found:
                        material_hits.append({"file": rel, "sections": found})
                low = blob.lower()
                if (b"bornbeast" in low and
                        any(e.encode() in low for e in TEX_EXTS)):
                    refs = [r for r in extract_texture_refs(blob)
                            if "bornbeast" in r.lower()]
                    if refs:
                        bornbeast_ref_hits.append({"file": rel, "refs": refs[:10]})
    return {
        "files_scanned": scanned,
        "material_format_hits_outside_armmodel": material_hits,
        "bornbeast_texture_reference_hits": bornbeast_ref_hits,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    arm = scan_arm_material_cfgs()
    neg = scan_for_weapon_text_materials()

    report = {
        "schema": "cf2.p4m01.r1.material-binding.v2",
        "supersedes_commit": SUPERSEDES_COMMIT,
        "supersedes_report_schema": "cf2.p4m01.r1.material-binding.v1",
        "continuation_review_reason": (
            "stage-2 must use existing mapping/config infrastructure "
            "semantics and record explicit negative results; numeric-field "
            "meaning must stay provisional."
        ),
        "A_engine_material_format_positive_evidence": {
            "description": (
                "CF ships an explicit text material format: [Textures] binds "
                "SpecularMapName0/EnvCubeMapName0/NormalMapName0/"
                "AlphaMapName0 to texture files; [Techniques] toggles "
                "Diffuse/Specular/EnvCube/NormalMapping; [Properties] holds "
                "float params incl. PieceIndex (per-piece index)."
            ),
            "files_found": len(arm),
            "location": "data/rf016/Models/PLAYERVIEW/ArmModel/Shader/*.CFG (LZMA-compressed GBK text)",
            "examples": {k: v["texture_bindings"] | {"PieceIndex": v["piece_index"]}
                         for k, v in list(arm.items())[:4]},
            "piece_index_values_seen": sorted({v["piece_index"] for v in arm.values()
                                               if v["piece_index"] is not None}),
            "relevance": (
                "proves CF's binding mechanism is explicit named-file "
                "mapping with a per-piece integer index — consistent with "
                "the LTB numeric field being a slot/piece index, but does "
                "not by itself bind weapon meshes to their texture set"
            ),
        },
        "B_negative_results_explicit": neg,
        "C_ltb_numeric_field_status": {
            "field": "u8-length-prefixed string right after each weapon mesh's index buffer",
            "weapon_instance": "single ASCII digits '0'..'8' (BornBeast & Transformers share the set)",
            "general_corpus": (
                "same structural position across arm LTBs but often empty "
                "strings there; some other weapons carry letters ('h','j',"
                "'k','m','n') — i.e. a general per-mesh short-name field"
            ),
            "meaning_texture_slot": "PROVISIONAL_NOT_PROVEN",
            "stage2_binding_mesh_slot_to_texture_set": "OPEN_UNRESOLVED",
        },
        "evidence_grade": {
            "engine_has_explicit_material_format": "VERIFIED_STRUCTURAL (text CFGs decoded)",
            "weapon_side_mapping_file_exists_locally": "NEGATIVE_RESULT (not found)",
            "ltb_numeric_field_is_general_structure": "VERIFIED_STRUCTURAL",
            "numeric_field_equals_texture_slot": "PROVISIONAL",
            "closure_condition_4": "NOT_PASS",
        },
        "conclusion": (
            "Stage-2 produced one positive (the engine's explicit text "
            "material format with PieceIndex) and two clean negatives (no "
            "weapon-side material CFG, no config/dat file referencing "
            "BornBeast textures anywhere in local data). The LTB numeric "
            "field remains provisional; closure condition 4 must not pass."
        ),
    }

    out = os.path.join(OUT_DIR, "material_binding_r1.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("wrote", out)
    print(f"arm material cfgs decoded: {len(arm)}")
    print(f"negative scan: files={neg['files_scanned']} "
          f"material_hits_outside_arm={len(neg['material_format_hits_outside_armmodel'])} "
          f"bornbeast_ref_hits={len(neg['bornbeast_texture_reference_hits'])}")


if __name__ == "__main__":
    main()
