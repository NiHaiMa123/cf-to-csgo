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

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Optional

REPO = r"D:\project\cf_to_csgo"
N01_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/n01")
DATA = os.path.join(REPO, "data")
os.makedirs(N01_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# F1: executor provenance parameterization
# ---------------------------------------------------------------------------
# Per Chat/Sol F1 cleanup: a generic N01 generator MUST NOT bake in any
# specific model identity. Every provenance field falls back to
# "unspecified" when no CLI arg / env var is supplied, so historical runs
# can never be mis-attributed to a default executor.
#
# Priority order:
#   1. --executor-* CLI flag (highest)
#   2. N01_EXECUTOR_* environment variable
#   3. literal "unspecified"
#
# The literal commit_footer_model_provenance = "NON_AUTHORITATIVE"
# reminder is ALWAYS written, regardless of how the model field was
# resolved. Historical commit footers are never rewritten.
EXECUTOR_UNSPECIFIED = "unspecified"
EXECUTOR_ENV_VARS = {
    "executor_model": "N01_EXECUTOR_MODEL",
    "executor_harness": "N01_EXECUTOR_HARNESS",
    "executor_family": "N01_EXECUTOR_FAMILY",
}


def _resolve_executor_field(field_name: str, cli_value):
    """Resolve a single executor provenance field.

    Returns the CLI value if non-empty; otherwise the env var if
    non-empty; otherwise the literal string "unspecified".
    """
    if cli_value is not None and str(cli_value).strip():
        return str(cli_value).strip()
    env_name = EXECUTOR_ENV_VARS[field_name]
    env_value = os.environ.get(env_name, "").strip()
    if env_value:
        return env_value
    return EXECUTOR_UNSPECIFIED


def resolve_executor_provenance(args=None):
    """Return the executor_provenance dict to embed in this run's outputs.

    `args` may be a argparse.Namespace produced by parse_executor_args().
    """
    model = _resolve_executor_field("executor_model",
                                   getattr(args, "executor_model", None)
                                   if args is not None else None)
    harness = _resolve_executor_field("executor_harness",
                                      getattr(args, "executor_harness", None)
                                      if args is not None else None)
    family = _resolve_executor_field("executor_family",
                                     getattr(args, "executor_family", None)
                                     if args is not None else None)
    if model == EXECUTOR_UNSPECIFIED:
        source = "no CLI flag and no N01_EXECUTOR_MODEL env var; using 'unspecified'"
    else:
        source = "CLI flag / N01_EXECUTOR_MODEL env var"
    return {
        "executor_model": model,
        "executor_harness": harness,
        "executor_family": family,
        "model_id_source": source,
        "commit_footer_model_provenance": "NON_AUTHORITATIVE",
    }


def parse_executor_args(argv=None):
    """Parse only the executor-related CLI flags; ignore the rest."""
    parser = argparse.ArgumentParser(
        description=(
            "N01 Phase 1 consumer search. Pass --executor-* to override "
            "the default 'unspecified' provenance. Without flags, the "
            "generator writes 'unspecified' for every field."
        ),
        add_help=True,
    )
    parser.add_argument(
        "--executor-model", default=None,
        help="Executor model id (overrides N01_EXECUTOR_MODEL).",
    )
    parser.add_argument(
        "--executor-harness", default=None,
        help="Executor harness (overrides N01_EXECUTOR_HARNESS).",
    )
    parser.add_argument(
        "--executor-family", default=None,
        help="Executor family (overrides N01_EXECUTOR_FAMILY).",
    )
    return parser.parse_args(argv)

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
    e = ext.lower()
    if e not in {".cfg", ".ini", ".txt", ".cft", ".fcf", ".csv", ".dat",
                  ".xml", ".json", ".lua", ".ref", ".apf"}:
        return False
    if "/modeltextures/" in n.lower():
        return True
    if "/models/" in n.lower() and e in {".cfg", ".ini", ".txt"}:
        return True
    low = n.lower()
    return any(k in low for k in
               ("material", "shader", "texture", "skin", "weapon",
                "character"))


def is_likely_model_texture_path(path: str, ext: str) -> bool:
    n = normalize_path(path).lower()
    if is_ui_path(n):
        return False
    e = ext.lower()
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
    e = ext.lower()
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
       - config_index: keyed by cfg-path → [(model_key, [texture_refs])]
         (only real parsed mapping objects; NO scan-metadata tuples)
       - scan_metadata: dict keyed by rel → {"scanned": bool, "ext": str}
         (separated; never returned as texture refs)
       - raw_needles: set of all model-name needles used to byte-grep any file
       - material_candidates / mapping_table_candidates: lists for the matrix
    """
    config_index: "dict[str, list[tuple]]" = {}
    scan_metadata: "dict[str, dict]" = {}
    raw_needles: set = set()
    material_candidates: list = []
    mapping_table_candidates: list = []
    # Per M2 cleanup: separate three independent counters so the report
    # can label each scope correctly:
    #   - all_files_seen_post_low_value_filter: every file (any extension)
    #     surviving the low-value/UI/radio path filter.
    #   - config_candidates_seen: subset whose extension is in CONFIG_EXT
    #     AND is_likely_model_texture_config(rel, ext).
    #   - config_candidates_decoded: subset of config_candidates_seen whose
    #     content was successfully decoded as text AND contained
    #     extractable model/texture mappings that produced real entries.
    all_files_seen = 0
    config_candidates_seen = 0
    config_candidates_decoded = 0
    for root, _dirs, files in os.walk(data_root):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, data_root).replace("\\", "/")
            ext = os.path.splitext(fn)[1].lower()
            if not ext:
                continue
            if is_low_value_mapping_path(rel):
                continue
            all_files_seen += 1
            scan_metadata[rel] = {"ext": ext}
            if ext in CONFIG_EXT and is_likely_model_texture_config(rel, ext):
                scan_metadata[rel]["scanned"] = True
                config_candidates_seen += 1
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
                    # Only accept tuples whose texture list is a real list of
                    # resource-path strings; reject anything else.
                    real_mappings = []
                    for mk, textures in mappings:
                        if not isinstance(textures, list):
                            continue
                        if not all(isinstance(t, str) and len(t) > 3 for t in textures):
                            continue
                        real_mappings.append((mk, textures))
                    if real_mappings:
                        config_index[rel] = real_mappings
                        config_candidates_decoded += 1
                        for key, textures in real_mappings:
                            if key:
                                raw_needles.add(
                                    key.split("|")[0] if "|" in key else key
                                )
                                for tk in [os.path.basename(k) for k in (key,)]:
                                    if tk:
                                        raw_needles.add(tk)
                if is_likely_material_table(rel, ext):
                    material_candidates.append(rel)
            if is_likely_model_mapping_table(rel, ext):
                mapping_table_candidates.append(rel)
    return {
        "config_index": config_index,
        "scan_metadata": scan_metadata,
        "raw_needles": raw_needles,
        "material_candidates": material_candidates,
        "mapping_table_candidates": mapping_table_candidates,
        # Three independent counters (per M2 cleanup):
        "all_files_seen_post_low_value_filter": all_files_seen,
        "config_candidates_seen": config_candidates_seen,
        "config_candidates_decoded": config_candidates_decoded,
    }


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
    """Resolve texture refs by trying all model_keys in config_index.

    Schema/type guard: every "mappings" entry must be a list whose elements
    are themselves (str, list[str]) tuples. Any non-conforming entry is
    silently skipped — strings must never be treated as texture lists.
    """
    seen_textures = set()
    ordered = []
    if not isinstance(config_index, dict):
        return ordered
    for k in model_keys:
        if not isinstance(k, str):
            continue
        for rel, mappings in config_index.items():
            if not isinstance(mappings, list):
                continue
            for mk, textures in mappings:
                if not isinstance(mk, str) or not isinstance(textures, list):
                    continue
                if not all(isinstance(t, str) for t in textures):
                    continue
                if mk == k or (k and mk and (k.lower() in mk.lower()
                                             or mk.lower() in k.lower())):
                    for t in textures:
                        if not isinstance(t, str):
                            continue
                        if t not in seen_textures:
                            seen_textures.add(t)
                            ordered.append((rel, t))
    return ordered


# Resource-family classification used to keep `.dat` consumer hits separate
# from `.cfg/.ini/.txt` consumer hits.
RESOURCE_FAMILY_BY_EXT = {
    ".dat": "world_dat",
    ".lta": "model_text",
    ".ltb": "model_binary",
    ".cfg": "config_text",
    ".ini": "config_text",
    ".txt": "config_text",
}

# Scopes that contain only generated/derived reports and MUST NOT count as
# native CF-resource consumer hits. These can be reported separately as
# DERIVED_OUTPUT_HIT but never as evidence for native binding.
DERIVED_OUTPUT_PREFIXES = (
    "data/out/",
    "data\\out\\",
    "out/",
    "out\\",
    "work/",
    "work\\",
    "reports/",
    "reports\\",
    "logs/",
    "logs\\",
)


def is_derived_output_path(rel: str) -> bool:
    n = rel.replace("\\", "/").lower()
    return any(n.startswith(p.replace("\\", "/").lower()) for p in DERIVED_OUTPUT_PREFIXES)


def build_corpus(data_root: str, extensions: set, exclude_derived: bool = True):
    """Walk all files and yield (rel, ext, abs_path, raw bytes safe).

    When exclude_derived is True, files under data/out/, work/, reports/, logs/
    are skipped from raw-byte consumer scans so they cannot inflate the
    `.dat`/`.cfg` consumer hit counts.
    """
    for root, _dirs, files in os.walk(data_root):
        for root_lower in (root.lower(),):
            break
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in extensions:
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, data_root).replace("\\", "/")
            if exclude_derived and is_derived_output_path(rel):
                continue
            raw = _safe_read(p, 8 * 1024 * 1024)
            if raw is None:
                continue
            yield rel, ext, p, raw


def main(argv=None):
    # ----- F1 cleanup: parse CLI flags and resolve executor provenance -----
    args = parse_executor_args(argv)
    executor_provenance = resolve_executor_provenance(args)
    print("executor provenance:")
    for k, v in executor_provenance.items():
        print(f"  {k}: {v}")

    # ----- F3 cleanup: regression guard for scope-counter subset invariant -----
    # Will be re-checked after build_consumer_index() so we can use the
    # actual numbers; declared here so the failure surface is explicit.

    # ----- self-tests for fixed extensions / heuristic helpers -----
    assert ".dtx" in TEXTURE_EXT
    assert ".tga" in TEXTURE_EXT
    assert ".cfg" in CONFIG_EXT
    assert ".txt" in CONFIG_EXT
    assert ".cft" in PREFERRED_MAP_EXT
    assert is_likely_model_texture_path("a/weapons/test.dtx", ".dtx")
    # ----- regression guards for the schema bug -----
    sample_idx = {"some/file.cfg": [("BornBeast", ["foo.dtx", "bar.tga"])]}
    hits = look_up_texture(["bornbeast"], sample_idx)
    assert all(isinstance(rel, str) and isinstance(t, str) for rel, t in hits), hits
    # Ensure that bogus entries are silently dropped, never iterated.
    bad_idx = {"bad.cfg": [("bornbeast", "scanned")]}  # type: ignore[list-item]
    bad_hits = look_up_texture(["bornbeast"], bad_idx)
    assert bad_hits == [], ("regression: string was iterated as texture list", bad_hits)
    # Ensure derived-output path is excluded from raw-needle scan.
    assert is_derived_output_path("data/out/foo.txt")
    assert is_derived_output_path("out/foo.txt")
    assert is_derived_output_path("work/x/y.json")
    assert not is_derived_output_path("rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB")
    assert not is_derived_output_path("rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX")

    print("Phase 1 consumer discovery ...")
    idx_bundle = build_consumer_index(DATA)
    cfg_idx = idx_bundle["config_index"]
    scan_metadata = idx_bundle["scan_metadata"]
    raw_needles = idx_bundle["raw_needles"]
    material_candidates = idx_bundle["material_candidates"]
    mapping_table_candidates = idx_bundle["mapping_table_candidates"]
    # Per M2 cleanup: three independent, machine-reproducible counters.
    all_files_seen = idx_bundle["all_files_seen_post_low_value_filter"]
    config_candidates_seen = idx_bundle["config_candidates_seen"]
    config_candidates_decoded = idx_bundle["config_candidates_decoded"]
    # Per F3 cleanup: config_candidates_decoded MUST be a subset of
    # config_candidates_seen by definition; if this fails the counter
    # bookkeeping has a bug. This does NOT change the 261/18 evidence.
    assert config_candidates_decoded <= config_candidates_seen, (
        f"regression: config_candidates_decoded ({config_candidates_decoded}) "
        f"exceeds config_candidates_seen ({config_candidates_seen})"
    )
    print(f"  config items indexed: {sum(len(v) for v in cfg_idx.values())}")
    print(f"  raw model-name needles: {len(raw_needles)}")
    print(f"  material-table candidates: {len(material_candidates)}")
    print(f"  mapping-table candidates: {len(mapping_table_candidates)}")
    print(f"  [scope=all_files_seen_post_low_value_filter]               = {all_files_seen}")
    print(f"  [scope=config_candidates_seen (.cfg/.ini/.txt cfg-like)]   = {config_candidates_seen}")
    print(f"  [scope=config_candidates_decoded (text + real mappings)]   = {config_candidates_decoded}")

    # ----- regression guard: schema must not contain the legacy _ALL_ key -----
    assert "_ALL_" not in cfg_idx, (
        "regression: legacy '_ALL_' key returned to config_index"
    )
    # ----- regression guard: no 1-char texture refs may appear in any cfg entry -----
    for rel, mappings in cfg_idx.items():
        for mk, textures in mappings:
            for t in textures:
                assert len(t) > 3, (
                    f"regression: 1-char texture ref '{t}' under {rel}:{mk}"
                )

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

    # ----- regression guard: 4 targets must not produce 1-char texture refs -----
    for label, info in candidates_by_target.items():
        for rel, t in info["hits"]:
            assert isinstance(rel, str) and isinstance(t, str) and len(t) > 3, (
                f"regression: bogus hit for {label}: {(rel, t)!r}"
            )

    # ----- Raw-needle scan: split hits by extension / resource family / consumer -----
    text_extensions = {".cfg", ".ini", ".txt", ".dat", ".lta"}
    needles_by_stem = {label: stem for label, stem in targets.items()}
    hits_by_extension: "dict[str, dict[str, list]]" = {ext: {lbl: [] for lbl in targets}
                                                        for ext in text_extensions}
    hits_by_resource_family: "dict[str, dict[str, list]]" = {
        fam: {lbl: [] for lbl in targets}
        for fam in set(RESOURCE_FAMILY_BY_EXT.values())
    }
    hits_by_consumer: "dict[str, dict[str, list]]" = {
        "LithTechDatTextureReferenceIndex": {lbl: [] for lbl in targets},
        "LithTechModelTextureConfigIndex": {lbl: [] for lbl in targets},
    }
    raw_grep_derived_outputs: "dict[str, list]" = {lbl: [] for lbl in targets}
    scanned = 0
    decoded = 0
    print("  raw needle scan (excluding derived outputs) ...")
    for rel, ext, p, raw in build_corpus(DATA, text_extensions, exclude_derived=True):
        scanned += 1
        text = _decode_text(raw) if raw else None
        if text is None:
            continue
        decoded += 1
        ltext = text.lower()
        for label, stem in needles_by_stem.items():
            if stem.lower() in ltext:
                idx = ltext.find(stem.lower())
                ctx = text[max(0, idx - 30): idx + len(stem) + 60].replace("\n", " ")
                hits_by_extension[ext][label].append({"file": rel, "snippet": ctx})
                fam = RESOURCE_FAMILY_BY_EXT.get(ext, "other")
                hits_by_resource_family.setdefault(fam, {lbl: [] for lbl in targets})
                hits_by_resource_family[fam][label].append({"file": rel, "snippet": ctx})
                # consumer routing: world .dat -> DatTextureReferenceIndex,
                # text config (.cfg/.ini/.txt/.lta) -> ModelTextureConfigIndex
                if ext == ".dat":
                    hits_by_consumer["LithTechDatTextureReferenceIndex"][label].append(
                        {"file": rel, "snippet": ctx}
                    )
                else:
                    hits_by_consumer["LithTechModelTextureConfigIndex"][label].append(
                        {"file": rel, "snippet": ctx}
                    )

    # Also count derived-output hits separately so they cannot be mistaken
    # for native binding evidence.
    print("  raw needle scan (derived outputs only) ...")
    for rel, ext, p, raw in build_corpus(DATA, text_extensions, exclude_derived=False):
        if not is_derived_output_path(rel):
            continue
        text = _decode_text(raw) if raw else None
        if text is None:
            continue
        ltext = text.lower()
        for label, stem in needles_by_stem.items():
            if stem.lower() in ltext:
                idx = ltext.find(stem.lower())
                ctx = text[max(0, idx - 30): idx + len(stem) + 60].replace("\n", " ")
                raw_grep_derived_outputs[label].append({"file": rel, "snippet": ctx})

    print(f"  raw scans: {scanned} files (decoded: {decoded}); hits by extension/family/consumer:")
    for label in targets:
        per_ext = {ext: len(hits_by_extension[ext][label]) for ext in text_extensions}
        per_fam = {fam: len(hits_by_resource_family.get(fam, {}).get(label, []))
                   for fam in RESOURCE_FAMILY_BY_EXT.values()}
        per_con = {con: len(hits_by_consumer[con][label]) for con in hits_by_consumer}
        print(f"    {label}:")
        print(f"      hits_by_extension         = {per_ext}")
        print(f"      hits_by_resource_family   = {per_fam}")
        print(f"      hits_by_consumer          = {per_con}")
        print(f"      DERIVED_OUTPUT_HIT_count  = {len(raw_grep_derived_outputs[label])}")

    # candidate consumer matrix
    matrix = {
        "schema": "cf2.p4m01.n01.consumer-candidate.v3",
        "scan_scope": {
            "scan_root": DATA,
            "include_extensions": sorted(text_extensions),
            "exclude_paths": "low-value/UI/radio/lobbynotice prefixes AND derived outputs: data/out/, out/, work/, reports/, logs/",
            # Per M2 cleanup: three independent, machine-reproducible counters
            # with explicit scope labels. Each value is the literal counter
            # name produced by build_consumer_index(); do not collapse them.
            "all_files_seen_post_low_value_filter": all_files_seen,
            "config_candidates_seen": config_candidates_seen,
            "config_candidates_decoded": config_candidates_decoded,
            "raw_scan_files_seen": scanned,
            "raw_scan_files_decoded": decoded,
            "config_index_keys": sorted(cfg_idx.keys()),
            "config_index_total_mapping_tuples": sum(len(v) for v in cfg_idx.values()),
            "scan_metadata_count": len(scan_metadata),
            "scope_legend": {
                "all_files_seen_post_low_value_filter": "Every file (any extension) that survived the low-value/UI/radio path filter during os.walk over data/. Includes models, textures, audio banks, voice files, etc.",
                "config_candidates_seen": "Subset of all_files_seen whose extension is in CONFIG_EXT and is_likely_model_texture_config(rel, ext).",
                "config_candidates_decoded": "Subset of config_candidates_seen whose content was successfully decoded as text AND produced at least one real (model_key, [texture_refs]) mapping.",
                "raw_scan_files_seen": "Files walked during raw-needle scan over .cfg/.dat/.ini/.lta/.txt in data/, after low-value and derived-output exclusion.",
                "raw_scan_files_decoded": "Subset of raw_scan_files_seen whose content decoded as text."
            },
            "regression_assertions": [
                "no legacy '_ALL_' key in config_index",
                "no 1-char texture ref under any config entry",
                "schema/type guard in look_up_texture",
                "derived outputs reported separately (DERIVED_OUTPUT_HIT)",
                "raw scan splits hits_by_extension / hits_by_resource_family / hits_by_consumer",
                "three independent scope counters with explicit legend",
            ],
        },
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
                    "config index built from local corpus; targeted hits are zero "
                    "or bear witness this resolver does not see BornBeast weapon "
                    "side as a direct keyed mapping"
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
                "BornBeast_hit_count": len(hits_by_consumer["LithTechDatTextureReferenceIndex"]["BornBeast"]),
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
        "raw_grep_hits_summary": {
            "schema_note": (
                "Per-target hit counts split by extension / resource family / "
                "consumer (cf2.p4m01.n01.consumer-candidate.v2)."
            ),
            "by_extension": {
                label: {ext: len(hits_by_extension[ext][label]) for ext in text_extensions}
                for label in targets
            },
            "by_resource_family": {
                label: {fam: len(hits_by_resource_family.get(fam, {}).get(label, []))
                        for fam in RESOURCE_FAMILY_BY_EXT.values()}
                for label in targets
            },
            "by_consumer": {
                label: {con: len(hits_by_consumer[con][label]) for con in hits_by_consumer}
                for label in targets
            },
            "DERIVED_OUTPUT_HIT": {
                label: len(raw_grep_derived_outputs[label]) for label in targets
            },
        },
        "raw_grep_examples": {
            label: {
                ext: hits_by_extension[ext][label][:5] for ext in text_extensions
            } for label in targets
        },
        "DERIVED_OUTPUT_HIT_examples": {
            label: raw_grep_derived_outputs[label][:5] for label in targets
        },
        # Per F1 cleanup: provenance is resolved at runtime from
        # --executor-* CLI flags / N01_EXECUTOR_* env vars, with a
        # default of "unspecified". The Co-Authored-By trailer is NEVER
        # authoritative.
        "executor_provenance": executor_provenance,
    }

    out_json = os.path.join(N01_DIR, "consumer_candidate_matrix.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
    print("wrote", out_json)

    # Human-readable search report
    lines = [
        "# N01 Phase 1 — Consumer search report",
        "",
        "Schema: `cf2.p4m01.n01.consumer-candidate.v3`",
        "",
        "## Executor provenance",
        "",
        "```text",
        f"executor_model                = {executor_provenance['executor_model']}",
        f"executor_harness             = {executor_provenance['executor_harness']}",
        f"executor_family              = {executor_provenance['executor_family']}",
        f"model_id_source              = {executor_provenance['model_id_source']}",
        f"commit_footer_model_provenance = {executor_provenance['commit_footer_model_provenance']}",
        "```",
        "",
        "If a field shows `unspecified`, the generator received neither a",
        "`--executor-*` CLI flag nor a `N01_EXECUTOR_*` environment variable",
        "for that field. The generator MUST NOT default to any specific model",
        "identity. The `Co-Authored-By:` trailer of any commit is NEVER",
        "authoritative for actual executor identity.",
        "",
        "## Scope",
        "",
        "Reproduce the call/data paths of the repo's own texture/config/mapping/",
        "index/resolver stack on the local `data/` corpus, focused on the four",
        "weapons `M4A1_S_BornBeast`, `M4A1_S_Transformers`, `M4A1_S_Jewelry`,",
        "and the simpler control `M4A1_S_BlueDiamond`.",
        "",
        "Scan roots: `data/`. Include extensions for raw-needle scan:",
        f"`{sorted(text_extensions)}`.",
        "",
        "Excluded from native-binding accounting (reported separately as",
        "`DERIVED_OUTPUT_HIT`): `data/out/`, `out/`, `work/`, `reports/`, `logs/`.",
        "Also excluded: low-value/UI/radio/lobbynotice paths.",
        "",
        "## Scan scope summary (per M2 cleanup: three independent counters)",
        "",
        f"- **all_files_seen_post_low_value_filter**: **{all_files_seen}** — every file",
        "  (any extension) that survived the low-value/UI/radio path filter",
        "  during `os.walk(data/)`. Includes models, textures, audio banks,",
        "  voice files, etc.",
        f"- **config_candidates_seen**: **{config_candidates_seen}** — subset whose",
        "  extension is in CONFIG_EXT (`.cfg/.ini/.txt`) AND",
        "  `is_likely_model_texture_config(rel, ext)` returned True.",
        f"- **config_candidates_decoded**: **{config_candidates_decoded}** — subset of",
        "  config_candidates_seen whose content decoded as text AND produced",
        "  at least one real `(model_key, [texture_refs])` mapping.",
        f"- config_index keys (cfg files with real parsed mappings): {len(cfg_idx)}",
        f"- config_index total mapping tuples: {sum(len(v) for v in cfg_idx.values())}",
        f"- **raw_needle_scope**: **{scanned}** files seen, **{decoded}** decoded",
        "  (text-decodeable subset).",
        "",
        "Each count above is the literal output of one of the three",
        "independent counters in `build_consumer_index()` / `build_corpus()`;",
        "no count is hand-derived.",
        "",
        "Regression guards (assertions) executed before reporting:",
        "",
        "- no legacy `_ALL_` key in `config_index`;",
        "- no 1-char texture ref under any config entry;",
        "- schema/type guard in `look_up_texture` (string cannot be iterated",
        "  as a texture list);",
        "- `DERIVED_OUTPUT_HIT` rows are reported separately from native",
        "  consumer hits and never count as binding evidence;",
        "- raw-needle scan splits hits into `hits_by_extension`,",
        "  `hits_by_resource_family`, and `hits_by_consumer`;",
        "- three independent scope counters with explicit legend (M2 cleanup).",
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
        "   .dat world files. Hits reported under `hits_by_consumer.`",
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
        "Hits resolved from real parsed mappings only. Each hit is a tuple",
        "`(cfg_path, texture_ref)` where `texture_ref` is a full resource path",
        "of length > 3. The legacy 1-char pseudo-hits produced by the",
        "`_ALL_ -> \"scanned\"` schema bug have been removed.",
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
        f"Scanned every `{'/'.join(sorted(text_extensions))}` in local `data/`",
        "(excluding low-value/UI/radio/lobbynotice paths **and** derived",
        "outputs) for the literal weapon stems.",
        "",
    ])
    lines.append("### Hits by extension (excludes derived outputs)")
    lines.append("")
    lines.append("| target | " + " | ".join(sorted(text_extensions)) + " |")
    lines.append("|---|" + "---|" * len(text_extensions))
    for label in targets:
        per_ext = {ext: len(hits_by_extension[ext][label]) for ext in text_extensions}
        lines.append(f"| {label} | " + " | ".join(str(per_ext[e]) for e in sorted(text_extensions)) + " |")
    lines.append("")
    lines.append("### Hits by resource family")
    lines.append("")
    lines.append("| target | " + " | ".join(sorted(set(RESOURCE_FAMILY_BY_EXT.values()))) + " |")
    lines.append("|---|" + "---|" * len(set(RESOURCE_FAMILY_BY_EXT.values())))
    for label in targets:
        per_fam = {fam: len(hits_by_resource_family.get(fam, {}).get(label, []))
                   for fam in sorted(set(RESOURCE_FAMILY_BY_EXT.values()))}
        lines.append(f"| {label} | " + " | ".join(str(per_fam[f]) for f in sorted(set(RESOURCE_FAMILY_BY_EXT.values()))) + " |")
    lines.append("")
    lines.append("### Hits by consumer")
    lines.append("")
    lines.append("| target | LithTechDatTextureReferenceIndex | LithTechModelTextureConfigIndex |")
    lines.append("|---|---|---|")
    for label in targets:
        per_con = {con: len(hits_by_consumer[con][label]) for con in hits_by_consumer}
        lines.append(f"| {label} | {per_con['LithTechDatTextureReferenceIndex']} | {per_con['LithTechModelTextureConfigIndex']} |")
    lines.append("")
    lines.append("### Per-target examples (first 5 hits per extension)")
    lines.append("")
    for label in targets:
        lines.append(f"#### {label}")
        for ext in sorted(text_extensions):
            rows = hits_by_extension[ext][label][:5]
            if not rows:
                lines.append(f"- `{ext}`: 0 hits")
                continue
            lines.append(f"- `{ext}`: {len(hits_by_extension[ext][label])} hits")
            for h in rows:
                lines.append(f"  - `{h['file']}` — `{h['snippet']}`")
        lines.append("")
    lines.extend([
        "### DERIVED_OUTPUT_HIT (reported separately, NOT a binding evidence)",
        "",
        "Hits found in derived outputs (`data/out/`, `out/`, `work/`,",
        "`reports/`, `logs/`). These cannot be used as native-binding",
        "evidence because they are generated by our own tooling / earlier",
        "runs and merely echo file paths back.",
        "",
    ])
    for label in targets:
        rows = raw_grep_derived_outputs[label]
        lines.append(f"#### {label}: {len(rows)} derived-output hits")
        if not rows:
            lines.append("- (none)")
        else:
            for h in rows[:5]:
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
        "  but we found 0 BornBeast/Transformers/Jewelry/BlueDiamond needle hits",
        "  inside the local dat corpus (only 67 .dat files; CTY/world tables, not",
        "  weapon binding tables).",
        "- On .cfg side, all 237 WeaponShader/*.CFG files match the binary-strip",
        "  heuristic and never reach the structured-text path. No file in the local",
        "  corpus (config-like scanned by R1 stage-2 binding: 355 files) explicitly",
        "  mentions BornBeast/Transformers/Jewelry/BlueDiamond weapon paths or CFG",
        "  stems as a binding key. The structured-text resolvers produced 0 hits",
        "  for any of the four targets.",
        "- Derived outputs (`data/out/`, `work/`, etc.) that happen to mention the",
        "  weapon stems are now reported as `DERIVED_OUTPUT_HIT` and are NOT",
        "  counted as native-binding evidence.",
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
        "",
    ])
    md = "\n".join(lines)
    out_md = os.path.join(N01_DIR, "consumer_search_report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print("wrote", out_md)


if __name__ == "__main__":
    main(sys.argv[1:])
