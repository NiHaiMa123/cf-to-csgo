#!/usr/bin/env python3
"""
P4-M01 Task Spec steps B (inventory) + E (binding).

B: full inventory of the BornBeast native material family across local data.
E: recover material binding. PROVEN FACT (from LTB decompress + string scan):
   the LTB geometry file contains ONLY mesh names + animation names; it has NO
   embedded DTX/TGA/CFG/texture references. Therefore material binding is NOT
   stored inline in the LTB. It is recovered via the CF naming convention +
   directory structure: every BornBeast asset shares the base name
   "M4A1_S_BornBeast" and lives in the role-specific directory
   (PLAYERVIEW=DTX base, AlphaMap/NormalMap/SpecularMap=TGAs, Shader/WeaponShader=CFG).
   This convention-based binding is evidence-backed by filename + directory,
   not by guessing.
"""
import json
import os
import hashlib

REPO = r"D:\project\cf_to_csgo"
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/evidence")

# Local CF BornBeast native material family (verified present on disk).
BORNBEAST_FAMILY = {
    "geometry":  "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB",
    "base_dtx":  "data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
    "alpha":     "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
    "normal":    "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
    "specular":  "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
    "shader_cfg":"data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG",
}

# External reference (NOT final provenance) - kept for differential control only.
EXTERNAL_REFERENCE = {
    "cs16_flatten": "work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png",
}

ROLE = {
    "geometry":  "source_mesh_uv",
    "base_dtx":  "base_color_or_special_layer_512x256 (role TBD: see dtx_validation)",
    "alpha":     "alpha_or_visibility_atlas_1024 (variable channel G)",
    "normal":    "normal_map_1024 (variable channel B; NOT direct tangent normal)",
    "specular":  "specular_map_1024 (variable channel R)",
    "shader_cfg":"weapon_shader_cfg_rgb_ramp_164px (gradient lookup; semantic slot TBD)",
}


def sha256_of(path):
    p = os.path.join(REPO, path)
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    inv_items = []
    for role, rel in BORNBEAST_FAMILY.items():
        p = os.path.join(REPO, rel)
        exists = os.path.exists(p)
        sha = sha256_of(rel) if exists else None
        sz = os.path.getsize(p) if exists else None
        inv_items.append({
            "asset_role": role,
            "relative_path": rel,
            "present": exists,
            "sha256": sha,
            "size_bytes": sz,
            "source_class": "local_cf",
            "interpreted_role": ROLE[role],
        })

    inventory = {
        "schema": "cf2.p4m01.native-material-inventory.v1",
        "weapon": "BornBeast (PV-M4A1_S_BornBeast)",
        "base_name": "M4A1_S_BornBeast",
        "scope": "local_cf only; external CS1.6 textures are reference_only",
        "family_member_count": len(inv_items),
        "items": inv_items,
        "note": "Inventory covers the complete native material family found on "
                "local data. No separate lookup/detail/emissive/overlay/mask "
                "files exist for BornBeast (only PrismBeast has MaskMap entries). "
                "Emissive/energy character derives from the base DTX special "
                "layer + the CFG color ramp.",
    }
    inv_out = os.path.join(OUT_DIR, "native_material_inventory.json")
    with open(inv_out, "w") as f:
        json.dump(inventory, f, indent=2)

    # E: binding report. LTB has no inline refs -> binding via naming convention.
    binding = {
        "schema": "cf2.p4m01.material-binding.v1",
        "method": "CF naming convention + directory structure (LTB contains no "
                  "embedded material references; verified by LZMA decompress + "
                  "ASCII string scan returning only mesh/animation names).",
        "ltb_inline_references": "NONE (mesh names + animation names only)",
        "binding_group": {
            "base_name": "M4A1_S_BornBeast",
            "geometry_ltb": BORNBEAST_FAMILY["geometry"],
            "base_color_or_special": BORNBEAST_FAMILY["base_dtx"],
            "alpha": BORNBEAST_FAMILY["alpha"],
            "normal": BORNBEAST_FAMILY["normal"],
            "specular": BORNBEAST_FAMILY["specular"],
            "weapon_shader_cfg": BORNBEAST_FAMILY["shader_cfg"],
        },
        "binding_evidence": [
            "All six assets share the literal base name 'M4A1_S_BornBeast'.",
            "Directory encodes role: ModelTextures/PLAYERVIEW -> base DTX; "
            "AlphaMap/NormalMap/SpecularMap -> TGAs; Shader/WeaponShader -> CFG.",
            "Geometry LTB 'PV-M4A1_S_BornBeast.LTB' matches the same weapon "
            "and provides the UV space the maps sample.",
        ],
        "unresolved_semantic_slots": [
            "Exact CF engine mapping of base DTX (albedo vs detail/energy layer).",
            "Exact shader parameter the CFG 164px RGB ramp drives "
            "(tint/emissive/energy gradient).",
            "Whether alpha.specmap uses additive/multiply/lerp vs base.",
            "These require engine/render-style semantics not present in local "
            "data and are flagged PROVISIONAL, per spec E (no guessing).",
        ],
        "binding_confidence": "STRUCTURAL (filename+directory) — not decode-proven "
                              "per-pixel by an inline LTB material table.",
    }
    bind_out = os.path.join(OUT_DIR, "material_binding_report.json")
    with open(bind_out, "w") as f:
        json.dump(binding, f, indent=2)

    print(f"inventory: {len(inv_items)} local items, external excluded")
    for it in inv_items:
        print(f"  {it['asset_role']:10s} present={it['present']} sha={(it['sha256'] or '')[:12]}")
    print(f"binding: LTB inline refs = NONE; convention-based group of {len(BORNBEAST_FAMILY)} assets")
    print(f"\nWrote {inv_out}\nWrote {bind_out}")


if __name__ == "__main__":
    main()
