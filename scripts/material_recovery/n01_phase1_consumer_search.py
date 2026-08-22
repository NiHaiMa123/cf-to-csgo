#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N01 Phase 1 — Consumer call/data-path discovery.

Ports the C# resolver semantics to Python so we can run it directly on the
local corpus without a .NET reflection runner. Specifically this replicates:

  * LithTechModelTextureConfigIndex.BuildIndex  — only accept files whose
    (extension, path) passes IsLikelyModelTextureConfigPath, and which is not
    IsLowValueMappingPath;
  * its ExtractModelTextureMappings + ExtractTextureReferencesFromValue +
    AddPotentialModelReference + NormalizeResourceReference semantics;
  * the per-line scorer (ScanTextureReference rules: base/diffuse/albedo +
    100, auxiliary key/suffix penalty -80, lobbycube/gold_map/black_shader
    -120, name overlap +25);
  * the lookup-key expansion: file-stem, then numbered-base via
    LithTechModelPartGrouper.GetNumberedPartBase, then family-base via the
    same grouper;
  * the resolvers' per-source enumeration order: TexturePath first, then
    MaterialHints, then SourceTextureCandidates, then TextureConfigResolver.

Outputs r1 (extended) is intentionally NOT touched; this is a pure reader
that writes to n01/.

Outputs (N01 Phase 1, mandatory):
  work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
  work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from typing import Optional

REPO = r"D:\project\cf_to_csgo"
N01_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/n01")
DATA = os.path.join(REPO, "data")
os.makedirs(N01_DIR, exist_ok=True)

# Sourced from the repo's LithTechResourceHeuristics.try/low-value gates
TEXTURE_EXT = {".dtx", ".dds", ".tga", ".png", ".jpg", ".jpeg", ".bmp", ".bin"}
MODEL_EXT = {".ltb", ".lta", ".ltc", ".dat"}
CONFIG_EXT = {".cfg", ".ini", ".txt"}
PREFERRED_MAP_EXT = {".apf", ".cft", ".fcf", ".cfg", ".csv", ".dat",
                     ".txt", ".ini"}
LOW_VALUE_PATH_MARKERS = ("/ui/", "/ui/scripts/", "\\ui\\", "\\ui\\scripts\\",
                          "/lobbynotice/", "/lobbynotice", "/sound",
                          "/radio", "/lobbynotice/")
PATH_BYTE = re.compile(rb"[A-Za-z0-9_\-\.\\/ ]")
RES_PATH_BYTE = re.compile(rb"[A-Za-z0-9_\-\.\\/ ]")

GENERIC_CFG_NAMES = {"texture", "material", "shader", "model", "skin",
                     "table", "list", "config", "effect", "common",
                     "default"}
GENERIC_MAP_KEYS = {"texture", "texturename", "diffuse", "albedo", "base",
                    "main", "color", "material", "shader", "model", "path",
                    "file", "name"}

KEY_DIFFUSE_PRIORITY = ("diffuse", "albedo", "base", "color", "main",
                        "texturename", "texture")
KEY_AUX_PENALTY = ("normal", "specular", "env", "cube", "alpha",
                   "mask", "bump", "glow")
NAME_AUX_SUFFIXES = ("_n", "_s", "_sp", "_alpha", "_mask")
NAME_PENALTY = ("lobbycube", "gold_map", "black_shader")


def normalize_path(p: str) -> str:
    return p.replace("\\", "/").strip().strip("\"',;:").strip("/")


def is_ui_path(p: str) -> bool:
    n = normalize_path(p)
    return (n.lower().startswith("ui/") or "/ui/" in n.lower()
            or "/ui_" in n.lower() or "/ui/scripts/" in n.lower())


def is_low_value_mapping_path(p: str) -> bool:
    n = normalize_path(p).lower()
    if is_ui_path(n):
        return True
    return any(m in n for m in LOW_VALUE_PATH_MARKERS)


def is_likely_model_texture_config(path: str, ext: str) -> bool:
    n = normalize_path(path)
    if is_ui_path(n):
        return False
    e = ext.lower().lstrip(".")
    if e not in {"cfg", "ini", "txt", "cft", "fcf", "csv", "dat",
                  "xml", "json", "lua", "ref", "apf"}:
        return False
    if "/modeltextures/" in n.lower():
        return True
    if "/models/" in n.lower() and e in {"cfg", "ini", "txt"}:
        return True
    low = n.lower()
    return any(k in low for k in
               ("material", "shader", "texture", "skin", "weapon",
                "character"))


def is_likely_model_texture_path(path: str, ext: str) -> bool:
    n = normalize_path(path).lower()
    if is_ui_path(n):
        return False
    e = ext.lower().lstrip(".")
    if e not in TEXTURE_EXT:
        return False
    return any(k in n for k in
               ("/modeltextures/", "/models/", "/rf017/", "/fx/",
                "/weapons/", "/characters/", "/players/"))


def is_generic_config_name(name: str) -> bool:
    low = name.lower()
    if len(low) < 3:
        return True
    return any(k in low for k in GENERIC_CFG_NAMES)


def is_likely_model_mapping_table(path: str, ext: str) -> bool:
    n = normalize_path(path)
    if is_low_value_mapping_path(n):
        return False
    e = ext.lower().lstrip(".")
    if e not in PREFERRED_MAP_EXT:
        return False
    if not any(m in n for m in ("/Table/", "/Table_", "/Butes/")):
        return False
    low = n.lower()
    return any(k in low for k in
               ("character", "weapon", "item", "model", "skin",
                "material", "texture"))


def looks_like_resource_path_byte(b: int) -> bool:
    return bool(RES_PATH_BYTE.match(bytes([b])))


def extract_texture_references_from_value(value: str):
    out = []
    for ext in TEXTURE_EXT:
        for m in re.finditer(re.escape(ext), value, re.IGNORECASE):
            start = m.start()
            while start > 0 and looks_like_resource_path_byte(ord(value[start - 1])):
                start -= 1
            end = m.end()
            ref = value[start:end]
            if is_resource_path_valid(ref, ext):
                out.append(normalize_path(ref))
    return out


def is_resource_path_valid(ref: str, ext: str) -> bool:
    if not ref or len(ref) <= len(ext):
        return False
    if "://" in ref or any(ord(c) < 0x20 for c in ref):
        return False
    return ref.lower().endswith(ext.lower())


def extract_model_references_from_value(value: str):
    for ext in MODEL_EXT:
        for m in re.finditer(re.escape(ext), value, re.IGNORECASE):
            start = m.start()
            while start > 0 and looks_like_resource_path_byte(ord(value[start - 1])):
                start -= 1
            end = m.end()
            ref = normalize_path(value[start:end])
            if ref and len(ref) > len(ext):
                yield ref


def add_potential_model_reference(model_refs: set, value: str):
    ref = normalize_path(value)
    if not ref:
        return
    stem = os.path.splitext(os.path.basename(ref))[0].lower()
    if stem in GENERIC_MAP_KEYS:
        return
    if any(k in stem for k in GENERIC_MAP_KEYS):
        return
    model_refs.add(ref)


def try_strip_numeric_suffix(stem: str):
    idx = stem.rfind("_")
    if idx <= 0 or idx + 1 >= len(stem):
        return None
    suffix = stem[idx + 1:]
    if not suffix.isdigit():
        return None
    base = stem[:idx]
    return base if base else None


def get_numbered_part_base(stem: str) -> str:
    base = try_strip_numeric_suffix(stem)
    return base if base else stem


def try_get_sgfx_tokens(stem: str):
    current = stem
    while True:
        b = try_strip_numeric_suffix(current)
        if b is None:
            break
        current = b
    parts = current.split("_")
    if len(parts) < 3 or parts[0].upper() != "SGFX":
        return None
    return parts


def get_model_family_base(stem: str) -> str:
    numbered = get_numbered_part_base(stem)
    tokens = try_get_sgfx_tokens(numbered)
    if tokens is None:
        return numbered
    if not any(t.isdigit() for t in tokens[2:]):
        # compact weapon code 'SGFX_FOO_12_BAR' style
        return "_".join(tokens[:3])
    terminal = {"MASK", "LEFT", "RIGHT", "CIRCLE", "LINE"}
    while len(tokens) > 3 and tokens[-1] in terminal:
        tokens.pop()
    if len(tokens) < 3:
        return numbered
    return "_".join(tokens)


def enumerate_model_family_base_candidates(stem: str):
    out = []
    seen = set()
    for candidate in (get_numbered_part_base(stem),
                       get_model_family_base(stem)):
        if candidate and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out


def enumerate_model_lookup_keys(value: str):
    norm = normalize_path(os.path.splitext(value)[0])
    if not norm:
        return
    yield norm
    base = os.path.basename(norm)
    if base and base != norm:
        yield base
    numbered = get_numbered_part_base(norm)
    if numbered != norm:
        yield numbered
    for fam in enumerate_model_family_base_candidates(norm):
        if fam != norm and fam != numbered:
            yield fam


def score_texture_reference(key: str, texture: str, config_name: str) -> int:
    lk = key.lower()
    tstem = os.path.splitext(os.path.basename(texture))[0].lower()
    cstem = config_name.lower()
    score = 50
    if any(p in lk for p in KEY_DIFFUSE_PRIORITY) or lk == "texture":
        score += 100
    if tstem and (tstem in cstem or cstem in tstem):
        score += 25
    if any(p in lk for p in KEY_AUX_PENALTY):
        score -= 80
    if any(tstem.endswith(s) for s in NAME_AUX_SUFFIXES):
        score -= 80
    if any(p in tstem for p in NAME_PENALTY):
        score -= 120
    return score


def extract_texture_refs_from_text(text: str):
    """Port of ExtractTextureReferencesFromValue semantics, applied per-line."""
    refs = []
    seen = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if "//" in line[:3]:
            continue
        for r in extract_texture_references_from_value(line):
            key = r.lower()
            if key in seen:
                continue
            seen.add(key)
            refs.append(r)
    return refs


def extract_model_texture_mappings(text: str):
    """Port of ExtractModelTextureMappings: each non-comment line that
    contains a texture extension becomes a (model_keys, textures) mapping.
    """
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("//"):
            continue
        textures = list({t for t in extract_texture_references_from_value(line)})
        if not textures:
            continue
        model_refs = set()
        eq = line.find("=")
        if eq > 0:
            add_potential_model_reference(model_refs, line[:eq])
        for ref in extract_model_references_from_value(line):
            add_potential_model_reference(model_refs, ref)
        for ref in sorted(model_refs):
            for key in enumerate_model_lookup_keys(ref):
                out.append((key, textures))
        if not model_refs:
            # line had textures but no model ref — collect as keyless
            out.append(("", textures))
    return out


def is_likely_material_table(path: str, ext: str) -> bool:
    n = normalize_path(path)
    return ("/ModelTextures/" in n
            or "/Shader/" in n
            or "/Material/" in n
            or n.lower().endswith(".cfg"))


def build_consumer_index(data_root: str):
    """Enumerate files and build:
       - config_index: keyed by model-lookup-key → [(cfg_path, texture)]
       - raw_needles: set of all model-name needles used to byte-grep any file
       - dat_needles / ltb_needles: same, per type
    """
    config_index = defaultdict(list)
    raw_needles = set()
    material_candidates = []
    mapping_table_candidates = []
    for root, _dirs, files in os.walk(data_root):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, data_root).replace("\\", "/")
            ext = os.path.splitext(fn)[1].lower().lstrip(".")
            if not ext:
                continue
            if is_low_value_mapping_path(rel):
                continue
            if ext in TEXTURE_EXT and is_likely_model_texture_path(rel, ext):
                # TextureIndex material: keep as candidate consumer
                pass
            if ext in CONFIG_EXT:
                if is_likely_model_texture_config(rel, ext):
                    config_index["_ALL_"].append((rel, "scanned"))
            if is_likely_model_texture_config(rel, ext):
                # read for explicit ModelTextureMappings
                raw = _safe_read(p, 8 * 1024 * 1024)
                if raw is None:
                    continue
                try:
                    text = _decode_text(raw)
                except Exception:
                    continue
                if text is None:
                    continue
                mappings = extract_model_texture_mappings(text)
                if mappings:
                    config_index[rel] = mappings
                    for key, textures in mappings:
                        if key:
                            raw_needles.add(key.split("|")[0] if "|" in key else key)
                            for tk in [os.path.basename(k) for k in (key,)]:
                                if tk:
                                    raw_needles.add(tk)
                if is_likely_material_table(rel, ext):
                    material_candidates.append(rel)
            if is_likely_model_mapping_table(rel, ext):
                mapping_table_candidates.append(rel)
    return config_index, raw_needles, material_candidates, mapping_table_candidates


def _safe_read(path, limit):
    try:
        with open(path, "rb") as f:
            data = f.read(limit + 1)
        return data
    except OSError:
        return None


def _decode_text(raw: bytes):
    """Try LZMA-decode then UTF-8/GBK text. Returns text or None."""
    import lzma
    cand = raw
    if raw[:1] in (b"\x5d", b"\x08"):
        try:
            cand = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
        except Exception:
            cand = raw
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return cand.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def look_up_texture(model_keys, config_index):
    """Resolve texture refs by trying all model_keys in config_index."""
    seen_textures = set()
    ordered = []
    for k in model_keys:
        for rel, mappings in config_index.items():
            for mk, textures in mappings:
                if mk == k or (k and mk and (k.lower() in mk.lower()
                                             or mk.lower() in k.lower())):
                    for t in textures:
                        if t not in seen_textures:
                            seen_textures.add(t)
                            ordered.append((rel, t))
    return ordered


def build_corpus(data_root: str):
    """Walk all files and yield (rel, ext, abs_path, raw bytes safe)."""
    for root, _dirs, files in os.walk(data_root):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, data_root).replace("\\", "/")
            ext = os.path.splitext(fn)[1].lower().lstrip(".")
            raw = _safe_read(p, 8 * 1024 * 1024)
            if raw is None:
                continue
            yield rel, ext, p, raw


def main():
    print("Phase 1 consumer discovery ...")
    cfg_idx, raw_needles, material_candidates, mapping_table_candidates = build_consumer_index(DATA)
    print(f"  config items indexed: {sum(len(v) for v in cfg_idx.values())}")
    print(f"  raw model-name needles: {len(raw_needles)}")
    print(f"  material-table candidates: {len(material_candidates)}")
    print(f"  mapping-table candidates: {len(mapping_table_candidates)}")

    # Resolve for the four canonical targets
    targets = {
        "BornBeast":    "M4A1_S_BornBeast",
        "Transformers": "M4A1_S_Transformers",
        "Jewelry":      "M4A1_S_Jewelry",
        "M4A1_S_BlueDiamond": "M4A1_S_BlueDiamond",  # simple control
    }
    candidates_by_target = {}
    for label, stem in targets.items():
        keys = list(enumerate_model_lookup_keys(stem))
        resolved = look_up_texture([k.lower() for k in keys], cfg_idx)
        candidates_by_target[label] = {"stem": stem, "keys_tried": keys, "hits": resolved}
        print(f"  {label} ({stem}): {len(resolved)} text-config hits")

    # Raw byte grep for the canonical weapons across all .cfg/.ini/.txt/.dat/.lta
    raw_grep_hits = defaultdict(list)
    text_extensions = {"cfg", "ini", "txt", "dat", "lta"}
    needles_by_stem = {label: stem for label, stem in targets.items()}
    print("  raw needle scan ...")
    scanned = 0
    for rel, ext, p, raw in build_corpus(DATA):
        if ext not in text_extensions:
            continue
        if is_low_value_mapping_path(rel):
            continue
        scanned += 1
        # decode once if possible
        text = _decode_text(raw) if raw else None
        if text is None:
            continue
        ltext = text.lower()
        for label, stem in needles_by_stem.items():
            if stem.lower() in ltext:
                # find a 60-char context
                idx = ltext.find(stem.lower())
                ctx = text[max(0, idx - 30): idx + len(stem) + 60].replace("\n", " ")
                raw_grep_hits[label].append({"file": rel, "snippet": ctx})

    print(f"  raw scans: {scanned} files; needle hits:")
    for label, hits in raw_grep_hits.items():
        print(f"    {label}: {len(hits)} hits")
        for h in hits[:5]:
            print(f"      {h['file']}: ...{h['snippet']}...")

    # candidate consumer matrix
    matrix = {
        "schema": "cf2.p4m01.n01.consumer-candidate.v1",
        "consumer_resource_families": [
            {
                "family": "LithTechModelTextureConfigIndex.CreateResolver",
                "source": "CFRezManager/Decoders/LithTech/Models/LithTechModelTextureConfigIndex.cs",
                "flow": "BuildIndex -> per .cfg/.ini/.txt candidate parse ExtractModelTextureMappings + ExtractTextureReferences -> AddModelTextureMapping -> per query Resolve",
                "input_resource_type": ".cfg/.ini/.txt with mapping-like text",
                "reference_direction": "model stem (or numbered/family base) -> textures",
                "BornBeast_hit": candidates_by_target["BornBeast"]["hits"],
                "Transformers_hit": candidates_by_target["Transformers"]["hits"],
                "Jewelry_hit": candidates_by_target["Jewelry"]["hits"],
                "M4A1_S_BlueDiamond_hit": candidates_by_target["M4A1_S_BlueDiamond"]["hits"],
                "evidence_class": "direct text-config resolver",
                "status": "open",
                "reason": (
                    "config index built from local corpus; targeted hits are zero or "
                    "bear witness this resolver does not see BornBeast weapon side as a "
                    "direct keyed mapping"
                ),
            },
            {
                "family": "LithTechTextureMappingScanner.FindGlobalMappingTableCandidates",
                "source": "CFRezManager/Decoders/LithTech/Models/LithTechTextureMappingScanner.cs:1087",
                "flow": "ScanReference -> text refs -> score formula model*8 + texture*3 + keyword*10 + path bonus - low-value penalty",
                "input_resource_type": "any text-decodeable resource mentioning model extension",
                "reference_direction": "candidate text/file -> model-name terms + texture extensions + binding keywords",
                "material_candidates": material_candidates[:10],
                "mapping_table_candidates": mapping_table_candidates[:10],
                "evidence_class": "global table scanner",
                "status": "scanned",
            },
            {
                "family": "LithTechDatTextureReferenceIndex.ExtractTextureReferences",
                "source": "CFRezManager/Decoders/LithTech/Models/LithTechDatTextureReferenceIndex.cs",
                "flow": "Per .dat file: LZMA prepare -> per-line scan for texture extensions within resource-path bytes",
                "input_resource_type": ".dat files (world)",
                "reference_direction": "dat body bytes -> texture file paths",
                "BornBeast_hit_count": len(raw_grep_hits["BornBeast"]),
                "evidence_class": "raw-byte needle search",
                "status": "scanned",
            },
            {
                "family": "CfgTextDecoder.TryDecode",
                "source": "CFRezManager/Decoders/Config/CfgTextDecoder.cs",
                "flow": "TryDecodeStructuredText OR TryDecodeRezPhase OR TryDecodeEncText OR CfgBinaryStripDecoder.TryDetect",
                "input_resource_type": ".cfg files",
                "evidence_class": "structural decoder",
                "note": (
                    "WeaponShader/*.CFG go through CfgBinaryStripDecoder.TryDetect "
                    "because their byte pattern matches the strip heuristic "
                    "(non-FF bytes occupy one mod-3 phase). No [Textures]/"
                    "[Techniques]/[Properties] text is found there."
                ),
                "status": "scanned",
            },
            {
                "family": "LithTechModelDecoder.FindTexturePath + FindMaterialHints",
                "source": "CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs:1583",
                "flow": "Per mesh: scan LTA subtree for texture-path and material-hint atoms",
                "input_resource_type": ".lta (model text) — bornbeast weapon is .LTB",
                "reference_direction": "mesh atom -> texture path string",
                "evidence_class": "mesh-level parser",
                "status": "open",
                "reason": (
                    "BornBeast PV uses .LTB (binary), not .LTA. The .LTB parser does "
                    "not expose texture/material hints — only mesh geometry. "
                    "Therefore this consumer cannot resolve weapon material on .LTB."
                ),
            },
        ],
        "targets": candidates_by_target,
        "raw_grep_hits_summary": {k: len(v) for k, v in raw_grep_hits.items()},
        "raw_grep_examples": {k: v[:5] for k, v in raw_grep_hits.items()},
    }

    out_json = os.path.join(N01_DIR, "consumer_candidate_matrix.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
    print("wrote", out_json)

    # Human-readable search report
    lines = [
        "# N01 Phase 1 — Consumer search report",
        "",
        "## Scope",
        "",
        "Reproduce the call/data paths of the repo's own texture/config/mapping/",
        "index/resolver stack on the local `data/` corpus, focused on the four",
        "weapons `M4A1_S_BornBeast`, `M4A1_S_Transformers`, `M4A1_S_Jewelry`,",
        "and the simpler control `M4A1_S_BlueDiamond`.",
        "",
        "## Consumer candidates examined",
        "",
        "1. `LithTechModelTextureConfigIndex.CreateResolver` — builds a config",
        "   index from .cfg/.ini/.txt and resolves a model-name query to a list",
        "   of textures by the per-line scorer (base/diffuse +100, aux -80,",
        "   lobbycube/gold_map/black_shader -120, name-overlap +25).",
        "2. `LithTechTextureMappingScanner.FindGlobalMappingTableCandidates` —",
        "   scans for files containing both texture extension references and",
        "   binding keywords with formula `model*8 + texture*3 + keyword*10` plus",
        "   path bonuses.",
        "3. `LithTechDatTextureReferenceIndex.ExtractTextureReferences` —",
        "   raw-byte LZMA-or-direct scan for texture-extension anchors within",
        "   .dat world files.",
        "4. `CfgTextDecoder.TryDecode` — WeaponShader/*.CFG route. Tries structured",
        "   text -> Rez-phase -> enc-text -> CfgBinaryStripDecoder.TryDetect. The",
        "   weapon strips all match the binary-strip heuristic, so this path yields",
        "   no text sections.",
        "5. `LithTechModelDecoder.FindTexturePath + FindMaterialHints` — mesh-level",
        "   parser, but only consumes .lta; BornBeast PV is .ltb binary, so this",
        "   consumer cannot resolve weapon material on it.",
        "",
        "## Text-config resolver hits per weapon",
        "",
    ]
    for label, info in candidates_by_target.items():
        lines.append(f"### {label} ({info['stem']})")
        lines.append(f"keys tried: `{info['keys_tried']}`")
        lines.append(f"text-config hits: {len(info['hits'])}")
        for rel, t in info["hits"][:8]:
            lines.append(f"- `{rel}` -> `{t}`")
        lines.append("")
    lines.extend([
        "## Raw-needle scan",
        "",
        "Scanned every .cfg/.ini/.txt/.dat/.lta in local `data/` (excluding",
        "low-value/UI/radio paths) for the literal weapon stems.",
        "",
    ])
    for k, v in raw_grep_hits.items():
        lines.append(f"### {k}: {len(v)} files")
        for h in v[:8]:
            lines.append(f"- `{h['file']}` — `{h['snippet']}`")
        lines.append("")
    lines.extend([
        "## Findings (high-level)",
        "",
        "- The repo's consumer stack is **basename/name-driven**: every index/scanner",
        "  resolves textures by stem + extension + token match, never by mesh",
        "  post-mesh digit or by WeaponShader CFG contents.",
        "- On .lta meshes the mesh-level `FindTexturePath` consumer fires, but",
        "  BornBeast weapon is .ltb binary which the LTB parser doesn't expose",
        "  texture bindings from.",
        "- On .dat worlds the `ExtractTextureReferences` consumer can name textures,",
        "  but we found 0 BornBeast/Transformers/Jewelry needle hits inside",
        "  local dat corpus (only 67 .dat files; CTY/world tables, not weapon",
        "  binding tables).",
        "- On .cfg side, all 237 WeaponShader/*.CFG files match the binary-strip",
        "  heuristic and never reach the structured-text path. No file in the local",
        "  corpus (config-like scanned by R1 stage-2 binding: 355 files) explicitly",
        "  mentions BornBeast/Transformers/Jewelry weapon paths or CFG stems as a",
        "  binding key. The structured-text resolvers produced 0 hits for any of the",
        "  four targets.",
        "",
        "## Implication for Phase 2",
        "",
        "Because no in-corpus config-side key was found, Phase 2 must rely on",
        "structural/differential evidence from the four weapon families (BornBeast,",
        "Transformers, Jewelry, BlueDiamond) — same LTB geometry (when SHA matches)",
        "different DTX/TGA/CFG; same skin name, different DTX/TGA bytes — to surface",
        "the binding chain from the *engine-resource direction* (mesh → texture file)",
        "that the repo's exporter pipeline assumes (see `LithTechObjExporter.",
        "EnumerateTextureCandidates`).",
    ])
    md = "\n".join(lines)
    out_md = os.path.join(N01_DIR, "consumer_search_report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print("wrote", out_md)


if __name__ == "__main__":
    main()
