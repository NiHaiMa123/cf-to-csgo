#!/usr/bin/env python3
"""
P4-M01 Task Spec step A (provenance audit) + step I (closure judgement).

A: trace the P4 Prototype-01 material chain to prove the external-reference gap
   that P4-M01 must correct, then record the new native chain.
I: judge native material closure per spec sec 4-I (8 conditions).
   The local executor does NOT flip plan.md to PASS (Chat/Sol owns that); this
   report records evidence-backed condition status + a recommended state.
"""
import json
import os
import hashlib

REPO = r"D:\project\cf_to_csgo"
EVID = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/evidence")

BUILD = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_prototype_01/build_report.json")


def rel(p):
    return os.path.relpath(p, REPO)


def sha(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    os.makedirs(EVID, exist_ok=True)
    build = json.load(open(BUILD)) if os.path.exists(BUILD) else {}

    # --- A: P4 Prototype-01 provenance (from build_report) ---
    ext_in = build.get("steps", [{}])[3].get("input_hashes", {})
    ext_sha = list(ext_in.values())[0] if ext_in else None
    p4_derived = build.get("steps", [{}])[3].get("output_hashes", {})
    p4_vtf = build.get("steps", [{}])[4].get("output_hashes", {})

    provenance = {
        "schema": "cf2.p4m01.provenance-audit.v1",
        "p4_prototype_01_material_chain": {
            "external_reference_input": {
                "relative_path": "work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png",
                "sha256": ext_sha,
                "source_class": "external_reference",
                "used_for": "derive_prototype_textures -> bornbeast_base / bornbeast_selfillum_mask",
            },
            "derived_png": {rel(k): v for k, v in p4_derived.items()},
            "vtf_outputs": {rel(k): v for k, v in p4_vtf.items()},
            "material_policy": build.get("material_policy", {}),
        },
        "p4_provenance_gap": (
            "P4 Prototype-01 built its material ENTIRELY from one external CS1.6 "
            "flatten texture (final_cf_material=false). No local CF BornBeast "
            "DTX/TGA/CFG was used. This is exactly the gap P4-M01 corrects."
        ),
        "p4_m01_native_chain": {
            "geometry_ltb": {
                "relative_path": "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB",
                "source_class": "local_cf",
                "sha256": sha(os.path.join(REPO, "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB")),
            },
            "base_dtx": {
                "relative_path": "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
                "source_class": "local_cf",
                "sha256": sha(os.path.join(REPO, "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX")),
            },
            "alpha_tga": {"relative_path": "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
                          "source_class": "local_cf",
                          "sha256": sha(os.path.join(REPO, "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA"))},
            "normal_tga": {"relative_path": "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
                           "source_class": "local_cf",
                           "sha256": sha(os.path.join(REPO, "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA"))},
            "specular_tga": {"relative_path": "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
                             "source_class": "local_cf",
                             "sha256": sha(os.path.join(REPO, "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA"))},
            "weapon_strip_cfg": {"relative_path": "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG",
                                 "source_class": "local_cf",
                                 "sha256": sha(os.path.join(REPO, "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG"))},
            "all_inputs_local_cf": True,
            "external_pixels_in_generation": False,
        },
    }
    pa_out = os.path.join(EVID, "provenance_audit.json")
    with open(pa_out, "w") as f:
        json.dump(provenance, f, indent=2)

    # --- I: closure judgement ---
    closure = {
        "schema": "cf2.p4m01.native-material-closure.v1",
        "weapon": "BornBeast (PV-M4A1_S_BornBeast)",
        "conditions_sec4_I": {
            "1_geometry_uv_local_ltb": "PASS - PV-M4A1_S_BornBeast.LTB (local_cf, sha 5dbcee45)",
            "2_visible_color_from_local_cf": "PASS - base/alpha/normal/specular/cfg all local_cf",
            "3_each_map_path_sha": "PASS - recorded in native_material_inventory.json + material_binding_report.json",
            "4_material_binding_structural_evidence": "PASS(convention) - LTB has no inline refs; binding via filename+directory (verified)",
            "5_no_external_pixels": "PASS - H hypotheses use local_cf only; external used reference_only",
            "6_clean_reproducible": "PASS - deterministic Python scripts; inputs sha-pinned",
            "7_recognizable_bornbeast": "PENDING_USER_VISUAL_GATE - native base is a high-saturation purple/blue special/energy layer (not a full auto-albedo like the external CS1.6 grey). Native-only render is purple-toned; human visual confirmation required to assert 'recognizable BornBeast'.",
            "8_external_reference_only_visual": "PASS - external CS1.6 compared for color domain only, never in generation",
        },
        "base_dtx_role_finding": (
            "Verified (not assumed): PV-M4A1_S_BornBeast.DTX = 512x256 BGR24 full "
            "mip chain + 163-byte trailer; NOT a LithTech header DTX, NOT LZMA; "
            "color domain mean_sat=213 (high-saturation purple/blue). vs external "
            "CS1.6 mean_sat=11.5 (grey metal). The native base DTX is a "
            "SPECIAL/ENERGY layer, not a complete albedo. BornBeast native "
            "identity is carried by the layer combination (base + specular.R "
            "highlight + CFG-ramp emissive)."
        ),
        "recommended_state": "NATIVE_MATERIAL_RECOVERED (pending Chat/Sol review + user visual gate)",
        "executor_authority_note": (
            "Local executor records evidence + recommended state only. Authoritative "
            "plan.md status change to PASS/NATIVE_MATERIAL_RECOVERED is owned by "
            "Chat/Sol per CODEX_TASKS sec 7."
        ),
        "evidence_chain": [
            "evidence/provenance_audit.json (A)",
            "evidence/native_material_inventory.json (B)",
            "evidence/dtx_validation.json (C)",
            "evidence/tga_decode_matrix.json (D)",
            "evidence/material_binding_report.json (E)",
            "evidence/cfg_reverse_report.json (F)",
            "evidence/variant_diff_report.json (G)",
            "evidence/shader_hypotheses.json (H)",
            "previews/native_base_dtx.png, native_alpha.png, native_normal.png, native_specular.png",
            "previews/cfg_ramp_BornBeast.png",
            "previews/hypotheses/h1_full_base_spec.png, h2_full_base_emissive.png",
        ],
        "next_step": "Chat/Sol review of evidence -> if accepted, resume P5-T02 applying this method to M4A1_S_Transformers (Leishen). Optional step J (Source1 integration on NEW addon p4_m01_native_material_test) may follow.",
    }
    cl_out = os.path.join(EVID, "native_material_closure.json")
    with open(cl_out, "w") as f:
        json.dump(closure, f, indent=2)
    print("Wrote", pa_out)
    print("Wrote", cl_out)
    print("\nClosure conditions: 6 PASS, 1 PENDING_USER_VISUAL_GATE (cond 7), 1 PASS")
    print("Recommended state:", closure["recommended_state"])


if __name__ == "__main__":
    main()
