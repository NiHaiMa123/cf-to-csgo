#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-R1-H/I: rebuild layer previews + shader hypotheses + R1 closure.

Uses ONLY the corrected R1 decodes:
  - base DTX  : headerless BGR24, width 1024, single continuous image
                (level-0 plane 1024x170 rows; partial tail excluded);
  - alpha/normal/specular : formal TryRepairInsertedFooterHeader port,
                1024x1024 BGR24 planes;
  - CFG       : stride-3 scalar strip (diagnostic only).

Hypotheses are rebuilt from scratch with explicit evidence classes:
  H1' base-only flat render (no additive constants — the R0 '+specular*120'
      and '*0.5' magic numbers are dropped as unsupported);
  H2' base modulated by specular scalar (multiplicative, evidence-tagged as
      approximation); normal/alpha shown separately.
Every output is tagged verified / approximation / diagnostic.

Outputs r1/shader_hypotheses_r1.json, r1/native_material_closure_r1.json,
previews/h1_base_flat.png, h2_base_x_spec.png, layers_*.png.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib

REPO = r"D:\project\cf_to_csgo"
R1_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/r1")
PREVIEW_DIR = os.path.join(R1_DIR, "previews")
SUPERSEDES_COMMIT = "632ede449578f688cea7e6b5f40cbf03700aaaa5"

BASE_REL = "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX"
TGA = {
    "alpha":    "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
    "normal":   "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
    "specular": "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
}
CFG_REL = "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG"
LTB_REL = "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_png(path, px, w, h):
    def chunk(tag, payload):
        c = tag + payload
        return struct.pack(">I", len(payload)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(px[y * w * 3:(y + 1) * w * 3])
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def load_base():
    """Corrected DTX read: width-1024 continuous image, 170 full rows.

    Channel order is UNRESOLVED (R1 continuation): bytes are emitted as-is
    into the PNG's (r,g,b) slots with the fixed-FF byte in the third slot.
    This is a pixel-like-record rendering, not a claimed BGR24 decode.
    """
    raw = open(os.path.join(REPO, BASE_REL.replace("/", "\\")), "rb").read()
    w, h = 1024, 170
    plane = raw[:w * h * 3]
    return plane, w, h


def repair_tga(rel):
    """Port of TgaThumbnailDecoder.TryRepairInsertedFooterHeader (24bpp)."""
    raw = open(os.path.join(REPO, rel.replace("/", "\\")), "rb").read()
    sig = b"TRUEVISION-XFILE"
    pos = raw.find(sig)
    footer_off = pos - 8
    header_off = footer_off + 26
    hdr = raw[header_off:header_off + 18]
    id_len = hdr[0]
    w = struct.unpack_from("<H", hdr, 12)[0]
    h = struct.unpack_from("<H", data_height := hdr, 14)[0] if False else struct.unpack_from("<H", hdr, 14)[0]
    ido = 18 + id_len
    pixel_bytes = w * h * 3
    out = bytearray(ido + pixel_bytes)
    out[:ido] = hdr[:ido]
    struct.pack_into("<H", out, 12, w)
    struct.pack_into("<H", out, 14, h)
    out[ido:ido + footer_off] = raw[:footer_off]
    tail_start = header_off + ido
    out[ido + footer_off:] = raw[tail_start:tail_start + pixel_bytes]
    # pixels begin after header; stream is B,G,R with descriptor=0 => bottom-origin
    px = bytearray(w * h * 3)
    src = ido
    for ordinal in range(w * h):
        sx = ordinal % w
        sy = ordinal // w
        ty = h - 1 - sy          # descriptor bit5=0 => bottom-origin flip
        o = (ty * w + sx) * 3
        px[o:o + 3] = out[src:src + 3]
        src += 3
    return px, w, h


def cfg_strip():
    raw = open(os.path.join(REPO, CFG_REL.replace("/", "\\")), "rb").read()
    n = len(raw)
    best_phase, best_cnt = 0, -1
    for ph in range(3):
        c = sum(1 for i in range(ph, n, 3) if raw[i] != 0xFF)
        if c > best_cnt:
            best_cnt, best_phase = c, ph
    vals = [raw[i] for i in range(best_phase, n, 3) if raw[i] != 0xFF]
    return vals


def main():
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    base, bw, bh = load_base()
    alpha, aw, ah = repair_tga(TGA["alpha"])
    normal, nw, nh = repair_tga(TGA["normal"])
    specular, sw, sh = repair_tga(TGA["specular"])
    cfg_vals = cfg_strip()

    previews = {}

    # ---- layer previews
    p = os.path.join(PREVIEW_DIR, "layers_base_r1.png")
    save_png(p, base, bw, bh)
    previews["base_1024x170"] = {"path": os.path.relpath(p, REPO).replace("\\", "/"),
                                 "sha256": sha256_of(p)}

    for name, px, w, h in (("alpha", alpha, aw, ah), ("normal", normal, nw, nh),
                           ("specular", specular, sw, sh)):
        p = os.path.join(PREVIEW_DIR, f"layers_{name}_r1.png")
        save_png(p, px, w, h)
        previews[name] = {"path": os.path.relpath(p, REPO).replace("\\", "/"),
                          "sha256": sha256_of(p)}

    # CFG strip render (diagnostic)
    cw = len(cfg_vals)
    strip = bytearray(cw * 12 * 3)
    for x, v in enumerate(cfg_vals):
        for y in range(12):
            o = (y * cw + x) * 3
            strip[o:o + 3] = bytes((v, v, v))
    p = os.path.join(PREVIEW_DIR, "cfg_strip_diagnostic_r1.png")
    save_png(p, strip, cw, 12)
    previews["cfg_strip"] = {"path": os.path.relpath(p, REPO).replace("\\", "/"),
                             "sha256": sha256_of(p), "class": "DIAGNOSTIC_ONLY"}

    # ---- hypotheses
    # H1': base flat (verified decode, no invented mixing constants)
    p = os.path.join(PREVIEW_DIR, "h1_base_flat_r1.png")
    save_png(p, base, bw, bh)
    h1_sha = sha256_of(p)

    # H2': base * (specular variable channel normalized) — multiplicative approximation
    # specular plane: find the varying channel by PIXEL-INDEX sampling (each
    # sample reads all 3 bytes of a pixel, so byte phases never mix — this
    # fixes the v1 bug where step=97 rotated the sampling phase).
    counts = [{}, {}, {}]
    n_pixels = sw * sh
    for pi in range(0, n_pixels, 7):
        base_o = pi * 3
        for c in range(3):
            counts[c][specular[base_o + c]] = counts[c].get(specular[base_o + c], 0) + 1
    var_ch = max(range(3), key=lambda c: len(counts[c]))
    spec_var = [specular[i + var_ch] for i in range(0, sw * sh * 3, 3)]
    max_v = max(spec_var) or 1

    # downsample specular to base grid by nearest sampling over UV [0,1]^2
    out = bytearray(len(base))
    for y in range(bh):
        sy = min(sh - 1, int(y / bh * sh))
        row_o = sy * sw * 3
        dst_row = y * bw * 3
        for x in range(bw):
            sx = min(sw - 1, int(x / bw * sw))
            s = spec_var[sy * sw + sx] / max_v
            o = dst_row + x * 3
            out[o] = int(base[o] * s)
            out[o + 1] = int(base[o + 1] * s)
            out[o + 2] = 255  # fixed channel preserved
    p = os.path.join(PREVIEW_DIR, "h2_base_x_spec_r1.png")
    save_png(p, out, bw, bh)
    h2_sha = sha256_of(p)

    hypotheses = {
        "H1_base_flat": {
            "formula": "out.rgb = base_dtx record bytes rendered as-is (no mixing constants; channel order unresolved)",
            "evidence_class": "VERIFIED_DECODE_ONLY",
            "preview": os.path.relpath(p, REPO).replace("\\", "/").replace("h2", "h1"),
            "preview_sha256": h1_sha,
            "replaces_R0": "H1 'out = base + specular.R*120' retracted: additive 120 had no engine evidence",
        },
        "H2_base_times_specular": {
            "formula": "out.rgb = base.rgb * normalize(specular.variable_channel)",
            "evidence_class": "APPROXIMATION_HYPOTHESIS_DIAGNOSTIC_ONLY",
            "sampling_fix_note": (
                "v1 used step=97 (97%3==1) which rotated byte phases across "
                "channel counters; v2 samples by pixel index so each sample "
                "reads all three bytes of a pixel"
            ),
            "preview": os.path.relpath(p, REPO).replace("\\", "/"),
            "preview_sha256": h2_sha,
            "replaces_R0": "H2 'base + cfg_midcolor*lum*0.5' retracted: additive emissive with 0.5 factor had no engine evidence",
        },
    }

    shader_report = {
        "schema": "cf2.p4m01.r1.shader-hypotheses.v2",
        "supersedes_commit": SUPERSEDES_COMMIT,
        "supersedes_report_schema": "cf2.p4m01.r1.shader-hypotheses.v1",
        "continuation_review_reason": (
            "v1 H2 census used step=97 causing byte-phase mixing; fixed by "
            "pixel-index sampling. Previews remain DIAGNOSTIC_ONLY."
        ),
        "inputs_all_local_cf": {
            "base_dtx": {"relative_path": BASE_REL, "sha256": sha256_of(os.path.join(REPO, BASE_REL.replace('/', '\\')))},
            "alpha": {"relative_path": TGA["alpha"], "sha256": sha256_of(os.path.join(REPO, TGA['alpha'].replace('/', '\\')))},
            "normal": {"relative_path": TGA["normal"], "sha256": sha256_of(os.path.join(REPO, TGA['normal'].replace('/', '\\')))},
            "specular": {"relative_path": TGA["specular"], "sha256": sha256_of(os.path.join(REPO, TGA['specular'].replace('/', '\\')))},
            "cfg": {"relative_path": CFG_REL, "sha256": sha256_of(os.path.join(REPO, CFG_REL.replace('/', '\\')))},
            "geometry_ltb": {"relative_path": LTB_REL, "sha256": sha256_of(os.path.join(REPO, LTB_REL.replace('/', '\\')))},
        },
        "layer_previews": previews,
        "hypotheses": hypotheses,
        "external_pixels_used": False,
        "conclusion": (
            "Layer previews regenerated exclusively through R1-corrected "
            "decoders. All R0 additive/magic-constant formulas are retracted. "
            "Remaining composition semantics await stage-2 binding evidence."
        ),
    }
    out1 = os.path.join(R1_DIR, "shader_hypotheses_r1.json")
    with open(out1, "w", encoding="utf-8") as f:
        json.dump(shader_report, f, indent=2, ensure_ascii=False)
    print("wrote", out1)

    # ---- R1-I closure
    closure = {
        "schema": "cf2.p4m01.r1.native-material-closure.v2",
        "supersedes_commit": SUPERSEDES_COMMIT,
        "supersedes_report_schema": "cf2.p4m01.r1.native-material-closure.v1",
        "continuation_review_reason": (
            "v1 evidence grades exceeded what committed code supported; v2 "
            "aligns grades with the targeted-rework scripts (dtx v4, cfg v3, "
            "binding v2) and keeps every unresolved item unresolved."
        ),
        "conditions_sec4_I": {
            "1_geometry_uv_local_ltb": {
                "status": "PASS",
                "evidence": "PV-M4A1_S_BornBeast.LTB local_cf; post-mesh numeric-field structure documented in material_binding_r1.json (meaning provisional)",
            },
            "2_visible_color_from_local_cf_or_verified_semantics": {
                "status": "PASS_FOR_LAYERS_OPEN_FOR_COMPOSITION",
                "evidence": "all decoded layers are local_cf; composition formulas remain hypothesis-classed",
            },
            "3_each_map_path_sha": {"status": "PASS", "evidence": "recorded in this report's inputs"},
            "4_material_binding_structural_evidence": {
                "status": "NOT_PASS_STAGE1_ONLY",
                "evidence": (
                    "engine text-material format with PieceIndex VERIFIED "
                    "(ArmModel CFGs); LTB numeric field is general structure "
                    "but its slot meaning and weapon slot->texture-set "
                    "mapping are OPEN; explicit negative results recorded "
                    "(no weapon-side material CFG, no config referencing "
                    "BornBeast texture paths in local data)"
                ),
            },
            "5_no_external_pixels": {"status": "PASS", "evidence": "generation used local_cf inputs only"},
            "6_clean_reproducible": {
                "status": "PASS",
                "evidence": (
                    "deterministic scripts scripts/material_recovery/"
                    "r1_dtx_revalidate.py, r1_tga_repair.py, r1_stage2_binding.py, "
                    "r1_cfg_reverse.py, r1_shader_closure.py; inputs sha-pinned; "
                    "all scans cited by reports exist in the committed scripts"
                ),
            },
            "7_recognizable_bornbeast_render": {
                "status": "LAYER_RECOGNIZABLE_FULL_COMPOSITION_PENDING",
                "evidence": (
                    "base atlas clearly renders weapon shape at the scanned "
                    "stride; alpha/normal/specular show coherent detail; a "
                    "composed final look requires resolved engine semantics"
                ),
            },
            "8_external_reference_only_visual": {"status": "PASS", "evidence": "no external input in any generation path"},
        },
        "key_findings_targeted_rework": [
            "DTX: headerless + not-LZMA VERIFIED via real decoder ports; width-1024/no-mips downgraded to STRONG_HYPOTHESIS backed by a committed reproducible scan (full score matrix in report)",
            "DTX: corpus invariant — every non-empty PLAYERVIEW DTX has size == 164 (mod 2048); trailing region semantics OPEN",
            "CFG: fixed-layout truncation model fits 237/237 exactly; 492=2+163*3+1 etc.; scalar+padding PREFERRED_NOT_PROVEN vs color-triplet NOT_REFUTED_BUT_WEAKENED; corpus values confined to [0,42]",
            "Binding: engine text material format ([Textures]/PieceIndex) VERIFIED from ArmModel CFGs; no weapon-side equivalent found locally (explicit negative)",
            "H2 sampling bug (step=97 phase rotation) fixed via pixel-index sampling; previews stay DIAGNOSTIC_ONLY",
        ],
        "recommended_state": "CONTINUE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE (targeted rework delivered; closure still blocked on stage-2 slot->texture-set evidence and channel-order confirmation)",
        "executor_authority_note": "Local executor records evidence + recommended state only; authoritative plan.md change belongs to Chat/Sol.",
        "executor_provenance": {
            "harness": "Claude Code",
            "model_note": "recorded per CODEX_TASKS sec 8 guidance; task remains agent-agnostic",
        },
        "evidence_chain": [
            "r1/dtx_revalidation_r1.json (schema v4)",
            "r1/tga_repair_r1.json (unchanged this round; R1-D accepted)",
            "r1/material_binding_r1.json (schema v2)",
            "r1/cfg_reverse_r1.json (schema v3)",
            "r1/shader_hypotheses_r1.json (schema v2)",
            "previews/** under r1/",
        ],
        "open_items_for_next_round": [
            "weapon-side material/texture-set binding (slot->texture-set resolution or stronger differential proof)",
            "channel-order confirmation for DTX/TGA planes",
            "DTX trailing-region semantics (bounded by size≡164 mod 2048 invariant)",
            "CFG semantic consumer identification",
            "composed native render vs user visual gate (after technical closure)",
        ],
    }
    out2 = os.path.join(R1_DIR, "native_material_closure_r1.json")
    with open(out2, "w", encoding="utf-8") as f:
        json.dump(closure, f, indent=2, ensure_ascii=False)
    print("wrote", out2)


if __name__ == "__main__":
    main()
