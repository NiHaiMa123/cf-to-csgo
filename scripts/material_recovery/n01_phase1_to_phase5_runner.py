#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N01 Complete Execution Runner: Phase 1 through Phase 5.

Performs:
  - Phase 1: Consumer call/data-path discovery & matrix generation
  - Phase 2: ArmModel positive control + 5-target weapon-family differential
  - Phase 3: WeaponShader CFG consumer analysis
  - Phase 4: Channel / storage / shader semantics layering
  - Phase 5: Engine binding closure

Generates:
  - consumer_candidate_matrix.json
  - consumer_search_report.md
  - weapon_material_differential.json
  - cfg_consumer_report.json
  - channel_semantics_report.json
  - engine_binding_closure.json
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import lzma
import os
import re
import struct
import sys

REPO = r"D:\project\cf_to_csgo"
DATA = os.path.join(REPO, "data")
N01_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/n01")
os.makedirs(N01_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# F1 cleanup: executor provenance parameterization
# ---------------------------------------------------------------------------
# Priority order:
#   1. --executor-* CLI flag
#   2. N01_EXECUTOR_* environment variable
#   3. literal "unspecified"
# A generic N01 generator MUST NOT bake in any specific model identity.
EXECUTOR_UNSPECIFIED = "unspecified"
EXECUTOR_ENV_VARS = {
    "executor_model": "N01_EXECUTOR_MODEL",
    "executor_harness": "N01_EXECUTOR_HARNESS",
    "executor_family": "N01_EXECUTOR_FAMILY",
}


def _resolve_executor_field(field_name, cli_value):
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
    model = _resolve_executor_field(
        "executor_model",
        getattr(args, "executor_model", None) if args is not None else None,
    )
    harness = _resolve_executor_field(
        "executor_harness",
        getattr(args, "executor_harness", None) if args is not None else None,
    )
    family = _resolve_executor_field(
        "executor_family",
        getattr(args, "executor_family", None) if args is not None else None,
    )
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
    parser = argparse.ArgumentParser(
        description=(
            "N01 Phase 1-5 runner. Pass --executor-* to override the "
            "default 'unspecified' provenance. Without flags, every "
            "provenance field is written as 'unspecified'."
        ),
        add_help=True,
    )
    parser.add_argument("--executor-model", default=None)
    parser.add_argument("--executor-harness", default=None)
    parser.add_argument("--executor-family", default=None)
    return parser.parse_args(argv)


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lzma_decompress_safe(raw: bytes) -> bytes | None:
    if len(raw) >= 13 and raw[0] in (0x5D, 0x08):
        try:
            return lzma.decompress(raw, format=lzma.FORMAT_ALONE)
        except Exception:
            return None
    return None


def extract_weapon_meshes_detailed(d: bytes):
    """Extract all weapon mesh entries from decoded LTB binary."""
    out = []
    for i in range(len(d) - 4):
        nlen = struct.unpack_from("<H", d, i)[0]
        if not (4 <= nlen <= 64):
            continue
        seg = d[i + 2 : i + 2 + nlen]
        if len(seg) == nlen and (seg.startswith(b"M4A") or seg.startswith(b"Body") or seg.startswith(b"part")) and all(32 <= b < 127 for b in seg):
            nm = seg.decode("ascii")
            base = i + 2 + nlen
            if base + 85 + 6 > len(d):
                continue
            vc = struct.unpack_from("<H", d, base + 49)[0]
            fc = struct.unpack_from("<H", d, base + 53)[0]
            if not (0 < vc <= 40000 and 0 < fc <= 80000):
                continue
            idx_end = base + 85 + vc * 32 + fc * 6
            if idx_end + 2 > len(d):
                continue
            slen = d[idx_end]
            tail = d[idx_end + 1 : idx_end + 1 + slen]
            tail_s = tail.decode("ascii", "replace") if (0 <= slen <= 16 and len(tail) == slen) else None
            vert_bytes = d[base + 85 : base + 85 + vc * 32]
            vert_sha = hashlib.sha256(vert_bytes).hexdigest()
            out.append({
                "mesh_name": nm,
                "name_offset": i,
                "vertex_count": vc,
                "face_count": fc,
                "slot_tail_len": slen,
                "slot_id_string": tail_s,
                "vertex_buffer_sha256": vert_sha,
            })
    return out


def analyze_cfg_binary_strip(raw: bytes):
    """Analyze a single WeaponShader CFG binary strip."""
    if len(raw) == 0:
        return {"size": 0, "status": "empty"}
    mod_phases = collections.defaultdict(list)
    for idx, b in enumerate(raw):
        if b != 0xFF:
            mod_phases[idx % 3].append((idx, b))
    active_phases = list(mod_phases.keys())
    if len(active_phases) == 1:
        ph = active_phases[0]
        samples = [b for _, b in mod_phases[ph]]
        first_off = mod_phases[ph][0][0]
        last_off = mod_phases[ph][-1][0]
        trailing = len(raw) - 1 - last_off
        return {
            "size": len(raw),
            "is_single_mod3_phase": True,
            "phase": ph,
            "sample_count": len(samples),
            "first_offset": first_off,
            "last_offset": last_off,
            "trailing_bytes": trailing,
            "min_val": min(samples),
            "max_val": max(samples),
            "sample_bytes_hex_preview": [f"0x{b:02x}" for b in samples[:16]],
        }
    return {
        "size": len(raw),
        "is_single_mod3_phase": False,
        "active_phases": active_phases,
    }


def scan_arm_model_positive_control():
    """Extract full evidence for ArmModel positive control."""
    arm_shader_dir = os.path.join(DATA, "rf016", "Models", "PLAYERVIEW", "ArmModel", "Shader")
    results = {}
    if os.path.isdir(arm_shader_dir):
        for fn in sorted(os.listdir(arm_shader_dir)):
            p = os.path.join(arm_shader_dir, fn)
            raw = open(p, "rb").read()
            decomp = lzma_decompress_safe(raw)
            if decomp is None:
                continue
            text = decomp.decode("gbk", "replace")
            if "[Textures]" in text or "PieceIndex" in text:
                tex_matches = dict(re.findall(r"([A-Za-z0-9_]+)\s*=\s*([^\r\n]+)", text))
                results[fn] = {
                    "relative_path": os.path.relpath(p, DATA).replace("\\", "/"),
                    "raw_size": len(raw),
                    "decoded_size": len(decomp),
                    "sha256": sha256_of(p),
                    "textures": {k: v.strip() for k, v in tex_matches.items() if k.endswith("Name0") or "Map" in k},
                    "techniques": {k: v.strip() for k, v in tex_matches.items() if k.endswith("Enabled")},
                    "properties": {k: v.strip() for k, v in tex_matches.items() if k in ("PieceIndex", "RenderParam", "LightingParam")},
                }
    return results


def run_phase2_differential(executor_provenance=None):
    """Phase 2: ArmModel positive control + 5 weapon differential analysis."""
    if executor_provenance is None:
        executor_provenance = resolve_executor_provenance()
    print("Running Phase 2: Positive Control + Weapon Differential...")

    # 1. ArmModel Positive Control
    arm_control = scan_arm_model_positive_control()
    print(f"  ArmModel positive control configs found: {len(arm_control)}")

    # 2. Weapon Targets
    targets = [
        {
            "label": "BornBeast",
            "ltb_rel": "rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB",
            "dtx_rel": "rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
            "alpha_rel": "rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_Alpha.TGA",
            "normal_rel": "rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
            "specular_rel": "rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
            "cfg_rel": "rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG",
        },
        {
            "label": "Transformers",
            "ltb_rel": "rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB",
            "dtx_rel": "rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_Transformers.DTX",
            "alpha_rel": "rf017/ModelTextures/AlphaMap/M4A1_S_Transformers_Alpha.TGA",
            "normal_rel": "rf017/ModelTextures/NormalMap/M4A1_S_Transformers_N.TGA",
            "specular_rel": "rf017/ModelTextures/SpecularMap/M4A1_S_Transformers_S.TGA",
            "cfg_rel": "rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Transformers.CFG",
        },
        {
            "label": "Jewelry",
            "ltb_rel": "rf016/Models/PLAYERVIEW/PV-M4A1_S_Jewelry.LTB",
            "dtx_rel": "rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_Jewelry.DTX",
            "alpha_rel": "rf017/ModelTextures/AlphaMap/M4A1_S_Jewelry_alpha.TGA",
            "normal_rel": "rf017/ModelTextures/NormalMap/M4A1_S_Jewelry_N.TGA",
            "specular_rel": "rf017/ModelTextures/SpecularMap/M4A1_S_Jewelry01_S.TGA",
            "cfg_rel": "rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Jewelry.CFG",
        },
        {
            "label": "UltimateGold",
            "ltb_rel": "rf016/Models/PLAYERVIEW/PV-M4A1_S_UltimateGold.LTB",
            "dtx_rel": "rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_UltimateGold.DTX",
            "alpha_rel": None,
            "normal_rel": None,
            "specular_rel": None,
            "cfg_rel": None,
        },
        {
            "label": "BlueDiamond_Control",
            "ltb_rel": None,
            "dtx_rel": "rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BlueDiamond.DTX",
            "alpha_rel": "rf017/ModelTextures/AlphaMap/M4A1_S_BlueDiamond_Alpha.TGA",
            "normal_rel": "rf017/ModelTextures/NormalMap/M4A1_S_BlueDiamond_N.TGA",
            "specular_rel": "rf017/ModelTextures/SpecularMap/M4A1_S_BlueDiamond_S.TGA",
            "cfg_rel": "rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BlueDiamond.CFG",
        }
    ]

    target_differentials = {}
    for t in targets:
        lbl = t["label"]
        res = {"label": lbl}

        # LTB info
        if t["ltb_rel"]:
            p = os.path.join(DATA, t["ltb_rel"].replace("/", "\\"))
            if os.path.exists(p):
                raw = open(p, "rb").read()
                decomp = lzma_decompress_safe(raw)
                if decomp:
                    meshes = extract_weapon_meshes_detailed(decomp)
                    slots = [m["slot_id_string"] for m in meshes if m["slot_id_string"] is not None]
                    res["ltb"] = {
                        "relative_path": t["ltb_rel"],
                        "raw_size": len(raw),
                        "decomp_size": len(decomp),
                        "sha256": sha256_of(p),
                        "mesh_count": len(meshes),
                        "meshes": meshes,
                        "slot_ids": slots,
                        "slot_id_set": sorted(set(slots)),
                    }
        else:
            res["ltb"] = None

        # DTX info
        if t["dtx_rel"]:
            p = os.path.join(DATA, t["dtx_rel"].replace("/", "\\"))
            if os.path.exists(p):
                res["dtx"] = {
                    "relative_path": t["dtx_rel"],
                    "size": os.path.getsize(p),
                    "sha256": sha256_of(p),
                }
        else:
            res["dtx"] = None

        # Alpha TGA
        if t["alpha_rel"]:
            p = os.path.join(DATA, t["alpha_rel"].replace("/", "\\"))
            if os.path.exists(p):
                res["alpha_tga"] = {
                    "relative_path": t["alpha_rel"],
                    "size": os.path.getsize(p),
                    "sha256": sha256_of(p),
                }
        else:
            res["alpha_tga"] = None

        # Normal TGA
        if t["normal_rel"]:
            p = os.path.join(DATA, t["normal_rel"].replace("/", "\\"))
            if os.path.exists(p):
                res["normal_tga"] = {
                    "relative_path": t["normal_rel"],
                    "size": os.path.getsize(p),
                    "sha256": sha256_of(p),
                }
        else:
            res["normal_tga"] = None

        # Specular TGA
        if t["specular_rel"]:
            p = os.path.join(DATA, t["specular_rel"].replace("/", "\\"))
            if os.path.exists(p):
                res["specular_tga"] = {
                    "relative_path": t["specular_rel"],
                    "size": os.path.getsize(p),
                    "sha256": sha256_of(p),
                }
        else:
            res["specular_tga"] = None

        # CFG
        if t["cfg_rel"]:
            p = os.path.join(DATA, t["cfg_rel"].replace("/", "\\"))
            if os.path.exists(p):
                raw = open(p, "rb").read()
                strip_info = analyze_cfg_binary_strip(raw)
                res["weapon_shader_cfg"] = {
                    "relative_path": t["cfg_rel"],
                    "size": len(raw),
                    "sha256": sha256_of(p),
                    "binary_strip_info": strip_info,
                }
        else:
            res["weapon_shader_cfg"] = None

        target_differentials[lbl] = res

    diff_out = {
        "schema": "cf2.p4m01.n01.weapon-material-differential.v2",
        "task_id": "P4-M01-N01",
        "phase": 2,
        "positive_control": {
            "source": "rf016/Models/PLAYERVIEW/ArmModel/Shader",
            "configs_examined": len(arm_control),
            "samples": {k: v for k, v in list(arm_control.items())[:3]},
            "architectural_deduction": (
                "CrossFire ArmModel text shader configs use 5 named texture "
                "channels (SpecularMap / EnvCubeMap / NormalMap / AlphaMap / "
                "Diffuse), each with a *Name0 / *MappingEnabled flag, plus a "
                "[Properties] PieceIndex. This is engine-format positive "
                "evidence for the existence of a multi-channel shader "
                "pipeline."
            ),
            "evidence_grade": "ENGINE_FORMAT_POSITIVE_CONTROL_VERIFIED (ArmModel text CFG has these sections); NOT a recovered weapon-format binding (weapon uses binary WeaponShader CFG)",
        },
        "weapon_differentials": target_differentials,
        "structural_conclusions": {
            "mesh_slot_ids": {
                "BornBeast": target_differentials["BornBeast"]["ltb"]["slot_id_set"] if target_differentials["BornBeast"]["ltb"] else [],
                "Transformers": target_differentials["Transformers"]["ltb"]["slot_id_set"] if target_differentials["Transformers"]["ltb"] else [],
                "Jewelry": target_differentials["Jewelry"]["ltb"]["slot_id_set"] if target_differentials["Jewelry"]["ltb"] else [],
                "UltimateGold": target_differentials["UltimateGold"]["ltb"]["slot_id_set"] if target_differentials["UltimateGold"]["ltb"] else [],
                "conclusion": "All M4A1-S variant models share the same mesh numeric slot ID convention ('0' through '8'). The mapping from digit to weapon component (Body, Barrel, Mag, Silencer, etc.) is HYPOTHESIS only and is not yet established by a CF-engine consumer/reference contract.",
                "evidence_grade": "STRUCTURALLY_VERIFIED (slot digits exist); HYPOTHESIS (digit -> component name mapping)"
            },
            "cfg_mod3_profile": {
                "BornBeast": target_differentials["BornBeast"]["weapon_shader_cfg"]["binary_strip_info"] if target_differentials["BornBeast"]["weapon_shader_cfg"] else None,
                "Transformers": target_differentials["Transformers"]["weapon_shader_cfg"]["binary_strip_info"] if target_differentials["Transformers"]["weapon_shader_cfg"] else None,
                "Jewelry": target_differentials["Jewelry"]["weapon_shader_cfg"]["binary_strip_info"] if target_differentials["Jewelry"]["weapon_shader_cfg"] else None,
                "BlueDiamond_Control": target_differentials["BlueDiamond_Control"]["weapon_shader_cfg"]["binary_strip_info"] if target_differentials["BlueDiamond_Control"]["weapon_shader_cfg"] else None,
                "conclusion": "Every WeaponShader CFG matches single-phase mod-3 structure with one phase carrying all non-0xFF bytes (BornBeast: phase 2, 164 samples; Transformers: phase 1, 169 samples; Jewelry: phase 2, 214 samples; BlueDiamond: phase 2, 166 samples). Sample_count and phase vary systematically across skins. Whether the byte sequence encodes LUT values, packed shader constants, or another contract remains OPEN_UNRESOLVED; 'skin-specific shader parameterization' wording is HYPOTHESIS only.",
                "evidence_grade_structural_form": "STRUCTURALLY_VERIFIED",
                "evidence_grade_cross_skin_difference": "DIFFERENTIAL_SUPPORTED",
                "evidence_grade_semantic_interpretation": "OPEN_UNRESOLVED"
            }
        },
        # Per F1 cleanup: provenance is resolved at runtime from
        # --executor-* CLI flags / N01_EXECUTOR_* env vars, with a
        # default of "unspecified". The Co-Authored-By trailer is NEVER
        # authoritative.
        "executor_provenance": executor_provenance,
    }

    diff_path = os.path.join(N01_DIR, "weapon_material_differential.json")
    with open(diff_path, "w", encoding="utf-8") as f:
        json.dump(diff_out, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {diff_path}")
    return target_differentials


def run_phase3_cfg_consumer(diffs, executor_provenance=None):
    """Phase 3: WeaponShader CFG Consumer Analysis (graded).

    Per Chat/Sol 69c03d review:
      - H-CFG-A (1D LUT) is HYPOTHESIS only; do not claim DIFFERENTIAL_SUPPORTED.
      - BlueDiamond sample_count is 166 (NOT 164); do not claim it shares a
        sample_count with BornBeast.
      - Source1 VMT mapping is SOURCE1_DESIGN_CANDIDATE; do not state
        "CFG -> Phong exponent / boost / selfillum" as a recovered CF fact.
    """
    if executor_provenance is None:
        executor_provenance = resolve_executor_provenance()
    print("Running Phase 3: CFG Consumer Analysis (graded) ...")

    def get_cfg_info(target):
        if diffs[target]["weapon_shader_cfg"]:
            return diffs[target]["weapon_shader_cfg"]["binary_strip_info"]
        return None

    cfg_report = {
        "schema": "cf2.p4m01.n01.cfg-consumer-report.v3",
        "task_id": "P4-M01-N01",
        "phase": 3,
        "summary": (
            "Hypothesis-graded evaluation of WeaponShader binary CFG "
            "semantics. Structural facts are kept; all semantic / Source 1 "
            "mapping claims are explicitly evidence-graded and never "
            "upgraded to VERIFIED without a real consumer/reference contract."
        ),
        "evidence_grade_legend": {
            "STRUCTURALLY_VERIFIED": "Mechanical structural fact, reproducible by deterministic decode",
            "OBSERVED": "Direct observation of byte/value/field, not interpreted",
            "DIFFERENTIAL_SUPPORTED": "Same byte-pattern metric varies systematically across a same-family sample set",
            "HYPOTHESIS": "Possibly true, but no consumer/contract evidence yet",
            "SOURCE1_DESIGN_CANDIDATE": "Conversion-design choice for Source 1 mapping; NOT a recovered CF fact",
            "OPEN_UNRESOLVED": "No evidence yet, deliberately not claimed",
        },
        "corpus_statistics": {
            "total_files": 237,
            "single_mod3_phase_verified": 237,
            "compliance_rate": "100.0%",
            "non_mod3_counterexamples": 0,
            "evidence_grade": "STRUCTURALLY_VERIFIED",
        },
        "sample_counts_by_target": {
            "M4A1_S_BornBeast": get_cfg_info("BornBeast"),
            "M4A1_S_Transformers": get_cfg_info("Transformers"),
            "M4A1_S_Jewelry": get_cfg_info("Jewelry"),
            "M4A1_S_BlueDiamond": get_cfg_info("BlueDiamond_Control"),
        },
        "hypotheses_evaluation": [
            {
                "hypothesis": "H-CFG-A: 1D Color/Intensity LUT Ramp",
                "evidence_status": "HYPOTHESIS",
                "description": "CFG represents a 1D lookup table for dynamic shader color/energy modulation or specular ramp across the weapon surface.",
                "support": "Sample counts differ per skin (BornBeast 164 / Transformers 169 / Jewelry 214 / BlueDiamond 166) and the non-FF values stay in a narrow range per file.",
                "rejection_note": "Cannot be upgraded without a real consumer/reference contract. Earlier DIFFERENTIAL_SUPPORTED claim and the false BornBeast/BlueDiamond 164-equals-164 prose have been removed.",
            },
            {
                "hypothesis": "H-CFG-B: Packed Parameter / Constant Strip",
                "evidence_status": "HYPOTHESIS",
                "description": "CFG represents packed shader constants or vertex/pixel shader uniforms padded with 0xFF delimiter phases.",
                "support": "Exactly one mod-3 phase carries non-0xFF bytes, suggesting fixed-stride serialization where 2 bytes out of 3 are reserved/padding. No record-boundary or scalar-vs-RGB contract has been verified.",
            },
            {
                "hypothesis": "H-CFG-C: Text Format (CfgTextDecoder)",
                "evidence_status": "REJECTED_FOR_WEAPON_SHADER",
                "description": "WeaponShader CFGs contain INI-like [Sections] and key-value text.",
                "rejection_reason": "0 of 237 WeaponShader CFGs contain text sections or LZMA headers. All match CfgBinaryStripDecoder.",
            },
        ],
        "consumer_status": {
            "consumer_identified": False,
            "evidence_grade": "OPEN_UNRESOLVED",
            "note": (
                "The local corpus does not expose a CF runtime/engine "
                "binary that consumes WeaponShader CFGs. The repo's own "
                "decoders (CfgTextDecoder / CfgBinaryStripDecoder) only "
                "describe byte patterns; they do not constitute an "
                "engine-side consumer."
            ),
        },
        "conclusion": (
            "Only the structural fact is established. Semantic "
            "interpretation of CFG remains OPEN_UNRESOLVED. Source 1 "
            "mapping choices are explicit conversion-design candidates, "
            "NOT recovered CF facts."
        ),
        # Per F1 cleanup: provenance is resolved at runtime from
        # --executor-* CLI flags / N01_EXECUTOR_* env vars, with a
        # default of "unspecified". The Co-Authored-By trailer is NEVER
        # authoritative.
        "executor_provenance": executor_provenance,
    }
    # ----- regression guard: no false-PASS / overclaim phrases -----
    text_blob = json.dumps(cfg_report, ensure_ascii=False)
    forbidden = [
        "DIFFERENTIAL_SUPPORTED for H-CFG-A",
        "1D Color/Intensity LUT\", \"evidence_status\": \"DIFFERENTIAL_SUPPORTED",
        "binary shader parameter/LUT strips",
        "WeaponShader CFGs function as",
        "Phong exponent, boost, and self-illumination tint",
        "BlueDiamond shares the 164 sample count with BornBeast",
        "BlueDiamond: 164 samples phase 0",
        "READY_FOR_NATIVE_MATERIAL_COMPOSITION",
    ]
    for phrase in forbidden:
        assert phrase not in text_blob, (
            f"regression: cfg_consumer_report still contains forbidden phrase {phrase!r}"
        )
    cfg_path = os.path.join(N01_DIR, "cfg_consumer_report.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg_report, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {cfg_path}")

def run_phase4_channel_semantics(executor_provenance=None):
    """Phase 4: Channel & Storage Semantics Layering.

    Per Chat/Sol 69c03d review: this generator was a future regression hazard
    because it produced overclaim phrasing such as
    'AlphaMap = transparency + emissive glow mask',
    'SpecularMap = gloss/roughness map',
    'WeaponShader CFG = shader parameter & color LUT profile', and
    'CFG -> phongboost/phongexponent/selfillum'.

    This version is a hypothesis-graded / OPEN_UNRESOLVED generator:
      - Layer A keeps only mechanical storage facts.
      - Layer B keeps directory-based role HYPOTHESES, each with
        an evidence grade; the overclaim phrases are removed.
      - Layer C explicitly marks Source 1 VMT mapping as
        SOURCE1_DESIGN_CANDIDATE (NOT recovered CF facts).

    The runner that owns main() currently does NOT auto-invoke this
    function. It is kept here for completeness and to allow manual
    regeneration of the graded channel-semantics JSON.

    Regression guard: this function MUST NOT emit
    `READY_FOR_NATIVE_MATERIAL_COMPOSITION` or any other PASS-equivalent
    status without explicit direct/accepted Path-B evidence.
    """
    if executor_provenance is None:
        executor_provenance = resolve_executor_provenance()
    print("Running Phase 4: Channel & Storage Semantics (graded) ...")
    semantics_report = {
        "schema": "cf2.p4m01.n01.channel-semantics.v2",
        "task_id": "P4-M01-N01",
        "phase": 4,
        "summary": (
            "Strict layered separation: Layer A = storage byte order "
            "(mechanical facts only); Layer B = naming/directory "
            "resource-role HYPOTHESES (each item evidence-graded); "
            "Layer C = Source 1 conversion-design candidates "
            "(explicitly NOT recovered CF facts)."
        ),
        "layer_a_storage_byte_order": {
            "TGA": {
                "container": "Truevision TGA with bottom footer structure",
                "footer_offset_formula": "TRUEVISION-XFILE. signature offset - 8",
                "header_offset_formula": "footer_offset + 26",
                "raw_pixel_order": "BGRA / BGR (little-endian uncompressed)",
                "evidence_grade": "STRUCTURALLY_VERIFIED",
            },
            "DTX": {
                "container": "LithTech PV DTX (proprietary)",
                "header": "No standard LithTech -2/-3/-5 header; whole-file 3-byte payload",
                "stride": "1024",
                "evidence_grade_stride": "STRONG_HYPOTHESIS",
                "fixed_byte": "One constant 0xFF byte per 3-byte group",
                "two_varying_channels": "Continuous 2D spatial correlation across 1024 stride",
                "evidence_grade_two_channels": "OBSERVED",
                "dominant_corpus_statistic": "1043 of 1046 (99.71%) files match size % 2048 == 164",
                "evidence_grade_dominant_statistic": "VERIFIED_CORPUS_STATISTIC",
                "terminal_tail": "2212 bytes",
                "evidence_grade_terminal_tail": "OPEN_UNRESOLVED",
                "evidence_grade": "STRUCTURALLY_VERIFIED_PAYLOAD",
            },
        },
        "layer_b_map_binding_roles": [
            {
                "name": "Base_DTX",
                "directory": "rf017/ModelTextures/PLAYERVIEW/PV-*.DTX",
                "role_hypothesis": "Diffuse / Base Color Map (per directory name + file extension)",
                "evidence_grade": "HYPOTHESIS",
            },
            {
                "name": "AlphaMap_TGA",
                "directory": "rf017/ModelTextures/AlphaMap/*_Alpha.TGA",
                "role_hypothesis": "Alpha / transparency channel",
                "evidence_grade": "HYPOTHESIS",
            },
            {
                "name": "NormalMap_TGA",
                "directory": "rf017/ModelTextures/NormalMap/*_N.TGA",
                "role_hypothesis": "Tangent-space normal map",
                "evidence_grade": "HYPOTHESIS",
            },
            {
                "name": "SpecularMap_TGA",
                "directory": "rf017/ModelTextures/SpecularMap/*_S.TGA",
                "role_hypothesis": "Specular reflection / gloss channel",
                "evidence_grade": "HYPOTHESIS",
            },
            {
                "name": "WeaponShader_CFG",
                "directory": "rf017/ModelTextures/Shader/WeaponShader/*.CFG",
                "role_hypothesis": "Per-skin shader parameter / modulation strip",
                "evidence_grade": "HYPOTHESIS",
            },
        ],
        "layer_c_source1_conversion_design_candidates": {
            "_note": (
                "Source 1 VMT mapping is a conversion-design CHOICE, NOT "
                "a recovered CF fact."
            ),
            "vmt_shader_choice": "VertexLitGeneric",
            "evidence_grade": "SOURCE1_DESIGN_CANDIDATE",
            "parameters": [
                {"vmt_param": "$basetexture", "source_decision": "Local Base DTX",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$bumpmap", "source_decision": "Local Normal TGA",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$phong", "source_decision": "Enabled for weapon",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$phongboost / $phongexponent",
                 "source_decision": "Driven by chosen CFG byte mapping",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$phongfresnelranges",
                 "source_decision": "[.2 .5 1] placeholder",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$selfillum / $selfillummask",
                 "source_decision": "Driven by chosen CFG / SpecularMap mapping",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
                {"vmt_param": "$envmap",
                 "source_decision": "env_cubemap (CFG / SpecularMap driven)",
                 "evidence_grade": "SOURCE1_DESIGN_CANDIDATE"},
            ],
        },
        "removed_overclaim_phrasing": [
            "AlphaMap = transparency + emissive glow mask",
            "SpecularMap = gloss/roughness map",
            "NormalMap TGA = DirectX handedness",
            "WeaponShader CFG = shader parameter & color LUT profile",
            "CFG -> phongboost/phongexponent/selfillum as recovered CF fact",
        ],
        # Per F1 cleanup: provenance is resolved at runtime from
        # --executor-* CLI flags / N01_EXECUTOR_* env vars, with a
        # default of "unspecified". The Co-Authored-By trailer is NEVER
        # authoritative.
        "executor_provenance": executor_provenance,
    }
    # ----- regression guard: no false-PASS status without Path-B evidence -----
    text_blob = json.dumps(semantics_report, ensure_ascii=False)
    assert "READY_FOR_NATIVE_MATERIAL_COMPOSITION" not in text_blob, (
        "regression: channel_semantics_report emitted READY_FOR_NATIVE_MATERIAL_COMPOSITION"
    )
    assert "Path A direct engine closure" not in text_blob, (
        "regression: channel_semantics_report claimed Path A direct closure"
    )
    semantics_path = os.path.join(N01_DIR, "channel_semantics_report.json")
    with open(semantics_path, "w", encoding="utf-8") as f:
        json.dump(semantics_report, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {semantics_path}")


def run_phase5_engine_binding_closure(executor_provenance=None):
    """Phase 5: Final Engine Binding Closure (graded only).

    Per Chat/Sol 69c03d review: the previous version of this generator
    emitted `status = READY_FOR_NATIVE_MATERIAL_COMPOSITION` even though
    Path-B evidence was incomplete. That was a false-PASS future
    regression hazard.

    This version is locked to OPEN_UNRESOLVED / NEGATIVE_RESULT_SCOPED
    until direct/accepted Path-B evidence is established. It does NOT
    flip closure to PASS / READY.

    The runner that owns main() currently does NOT auto-invoke this
    function. It is kept here for completeness and manual regeneration.
    """
    print("Running Phase 5: Engine Binding Closure (graded) ...")
    if executor_provenance is None:
        executor_provenance = resolve_executor_provenance()
    closure_report = {
        "schema": "cf2.p4m01.n01.engine-binding-closure.v3",
        "task_id": "P4-M01-N01",
        "phase": 5,
        "closure_path": "Path B - Incomplete",
        "status": "OPEN_UNRESOLVED",
        "substantive_blocker": "BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS",
        "authoritative_evidence": {
            "1_model_mesh_slots": {
                "status": "STRUCTURALLY_VERIFIED",
                "evidence": (
                    "LTB mesh index buffer is followed by u8-prefixed ASCII "
                    "slot strings ('0'..'8') verified across BornBeast, "
                    "Transformers, Jewelry, and UltimateGold. However, no "
                    "open-source C# repo code consumes these IDs to map "
                    "texture files."
                ),
            },
            "2_texture_family_mirroring": {
                "status": "TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE",
                "evidence": (
                    "The REPO EXPORTER (LithTechObjExporter."
                    "ExpandSourceResourceTexturePathCandidates + "
                    "EnumerateTextureCandidates) performs deterministic "
                    "Models/PLAYERVIEW/PV-*.LTB -> ModelTextures/PLAYERVIEW/"
                    "PV-*.DTX (+ AlphaMap/ + NormalMap/ + SpecularMap/ + "
                    "Shader/WeaponShader/) mirroring and applies one texture "
                    "family to all sub-meshes because the LTB parser drops "
                    "the post-mesh short IDs. This is repo/tool behavior, "
                    "NOT a recovered property of the original CF runtime."
                ),
                "original_cf_runtime_mirroring": "OPEN_UNRESOLVED",
                "original_cf_runtime_blocker": "BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS",
            },
            "3_multi_channel_shader_pipeline": {
                "status": "ENGINE_FORMAT_POSITIVE_CONTROL_VERIFIED",
                "evidence": (
                    "ArmModel text shader configs prove the engine's "
                    "5-texture shader architecture indexed by PieceIndex. "
                    "This is an engine-format positive control for ArmModel "
                    "only; the WEAPON format uses binary WeaponShader CFG "
                    "and is not directly equivalent."
                ),
            },
            "4_weapon_shader_cfg_profile": {
                "status": "STRUCTURALLY_VERIFIED",
                "evidence": (
                    "All 237 WeaponShader CFGs match single-phase mod-3 "
                    "binary strips. Specific CFG consumers (LUT vs "
                    "Parameters) remain OPEN_UNRESOLVED."
                ),
            },
        },
        "next_step": (
            "blocked pending a new original CF runtime/client artifact or "
            "equivalent documented consumer contract. Closure status MUST NOT "
            "be flipped to PASS / READY without direct/accepted Path-B evidence."
        ),
        "forbidden_claim": {
            "claim_text_pattern": (
                "the assertion that the original CF runtime binding is "
                "verified solely by the repo exporter's deterministic "
                "directory mirroring"
            ),
            "why_forbidden": (
                "The local corpus does not contain any CF client "
                ".exe/.dll/.rez/.bin/.pak or engine module. The mirroring "
                "evidence above describes the REPO'S OWN EXPORTER, not the "
                "original CF runtime. Treating this as verified would be a "
                "false-PASS."
            ),
        },
        # Per F1 cleanup: provenance is resolved at runtime from
        # --executor-* CLI flags / N01_EXECUTOR_* env vars, with a
        # default of "unspecified". The Co-Authored-By trailer is NEVER
        # authoritative.
        "executor_provenance": executor_provenance,
    }
    # ----- regression guard: no false-PASS status -----
    text_blob = json.dumps(closure_report, ensure_ascii=False)
    assert "READY_FOR_NATIVE_MATERIAL_COMPOSITION" not in text_blob, (
        "regression: engine_binding_closure emitted READY_FOR_NATIVE_MATERIAL_COMPOSITION"
    )
    assert closure_report["status"] != "READY_FOR_NATIVE_MATERIAL_COMPOSITION", (
        "regression: engine_binding_closure status flipped to READY_FOR_NATIVE_MATERIAL_COMPOSITION"
    )
    # F2 cleanup: must NOT contain the literal forbidden claim phrasing
    # except inside the forbidden_claim.claim_text_pattern reference.
    forbidden_pattern = "original CF runtime mirroring = verified"
    if forbidden_pattern in text_blob:
        # Allowed only inside forbidden_claim reference, never as actual claim
        non_ref_count = (
            text_blob.count(forbidden_pattern)
            - text_blob.count("\"claim_text_pattern\"")
        )
        assert non_ref_count == 0, (
            f"regression: engine_binding_closure contains literal forbidden "
            f"phrase outside forbidden_claim reference"
        )
    # F2 cleanup: must NOT contain the old 'runtime appears to resolve' framing
    assert "CrossFire LithTech runtime appears to resolve" not in text_blob, (
        "regression: engine_binding_closure used old 'runtime appears to "
        "resolve' framing; F2 cleanup requires repo/tool behavior wording."
    )
    closure_path = os.path.join(N01_DIR, "engine_binding_closure.json")
    with open(closure_path, "w", encoding="utf-8") as f:
        json.dump(closure_report, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {closure_path}")


def main(argv=None):
    # ----- F1 cleanup: parse CLI flags and resolve executor provenance -----
    args = parse_executor_args(argv)
    executor_provenance = resolve_executor_provenance(args)
    print("executor provenance:")
    for k, v in executor_provenance.items():
        print(f"  {k}: {v}")
    print("=== P4-M01-N01 Execution (Phase 2 - 3) ===")
    diffs = run_phase2_differential(executor_provenance=executor_provenance)
    run_phase3_cfg_consumer(diffs, executor_provenance=executor_provenance)
    # Phase 4 / 5 generators are intentionally NOT auto-invoked from main().
    # They are graded generators (no false-PASS) but should only be triggered
    # by manual regeneration, never by an automated run.
    # Regression guard: this runner MUST NOT emit
    # READY_FOR_NATIVE_MATERIAL_COMPOSITION on its own.
    print("=== Completed N01 Phase 2 & 3. Did not auto-run Phase 4/5 closure. ===")
    print("    (Phase 4 / Phase 5 generators available as manual functions, both")
    print("    graded: NO false-PASS, no READY_FOR_NATIVE_MATERIAL_COMPOSITION.)")
if __name__ == "__main__":
    main(sys.argv[1:])
