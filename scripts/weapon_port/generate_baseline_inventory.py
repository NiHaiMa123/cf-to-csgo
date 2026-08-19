"""
Generate baseline_inventory.json for P4-T01.
Inventories repository P4 inputs, D3/F4 baseline, P4 staging, mods_temp MODs, and active MIGI addon.
Strictly read-only with respect to external MODs (no move, delete, or overwrite).
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(file_path: str) -> str:
    if not os.path.isfile(file_path):
        return None
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def scan_directory(dir_path: str) -> dict:
    result = {}
    if not os.path.exists(dir_path):
        return result
    for root, _, filenames in os.walk(dir_path):
        for fn in sorted(filenames):
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, dir_path).replace(os.sep, "/")
            result[rel] = {
                "path": os.path.abspath(fp),
                "size": os.path.getsize(fp),
                "sha256": compute_sha256(fp),
            }
    return result

def main():
    print(f"Project root: {ROOT}")
    
    # 1. Repository P4 Inputs
    manifest_rel = "assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json"
    manifest_abs = os.path.join(ROOT, manifest_rel)
    with open(manifest_abs, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    p4_input_entries = {
        "prototype_01_manifest": {
            "path": manifest_abs,
            "rel_path": manifest_rel,
            "role": "authoritative_prototype_manifest",
            "size": os.path.getsize(manifest_abs),
            "sha256": compute_sha256(manifest_abs),
        }
    }
    
    for key, item in manifest_data.get("inputs", {}).items():
        rel_p = item["path"]
        abs_p = os.path.join(ROOT, rel_p)
        exists = os.path.isfile(abs_p)
        p4_input_entries[key] = {
            "path": abs_p,
            "rel_path": rel_p,
            "role": "manifest_declared_input",
            "exists": exists,
            "size": os.path.getsize(abs_p) if exists else None,
            "sha256": compute_sha256(abs_p) if exists else None,
            "expected_sha256": item.get("sha256"),
            "hash_matches_manifest": (compute_sha256(abs_p) == item.get("sha256")) if exists else False,
        }
    
    for key, item in manifest_data.get("toolchain", {}).items():
        rel_p = item["path"]
        abs_p = os.path.join(ROOT, rel_p)
        exists = os.path.isfile(abs_p)
        p4_input_entries[f"tool_{key}"] = {
            "path": abs_p,
            "rel_path": rel_p,
            "role": "manifest_declared_tool",
            "exists": exists,
            "size": os.path.getsize(abs_p) if exists else None,
            "sha256": compute_sha256(abs_p) if exists else None,
            "expected_sha256": item.get("sha256"),
            "hash_matches_manifest": (compute_sha256(abs_p) == item.get("sha256")) if exists else False,
        }
    
    # Extra pipeline / helper scripts
    extra_scripts = [
        ("pipeline_script", "scripts/weapon_port/pipeline.py"),
        ("b3_validator", "scripts/cf_ltb/validate_b3_obj_roundtrip.py"),
        ("c1_splitter", "scripts/cf_ltb/split_c1_meshes.py"),
    ]
    for key, rel_p in extra_scripts:
        abs_p = os.path.join(ROOT, rel_p)
        exists = os.path.isfile(abs_p)
        p4_input_entries[key] = {
            "path": abs_p,
            "rel_path": rel_p,
            "role": "pipeline_core_script",
            "exists": exists,
            "size": os.path.getsize(abs_p) if exists else None,
            "sha256": compute_sha256(abs_p) if exists else None,
        }

    # 2. D3/F4 baseline & mods_temp
    f4_mod_dir = r"D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp"
    p4_mod_dir = r"D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp"
    p4_staging_dir = os.path.join(ROOT, "work", "m4a1_s_bornbeast", "p4_prototype_01", "staging")
    active_addon_dir = r"D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_m4a4_bornbeast_final"

    f4_files = scan_directory(f4_mod_dir)
    p4_mod_files = scan_directory(p4_mod_dir)
    p4_staging_files = scan_directory(p4_staging_dir)
    active_addon_files = scan_directory(active_addon_dir)

    # Cross comparisons
    staging_vs_p4_mod = {}
    for rel_k, info in p4_staging_files.items():
        if rel_k == "package_manifest.json":
            continue
        p4_info = p4_mod_files.get(rel_k)
        staging_vs_p4_mod[rel_k] = {
            "staging_sha256": info["sha256"],
            "p4_mod_sha256": p4_info["sha256"] if p4_info else None,
            "match": info["sha256"] == (p4_info["sha256"] if p4_info else None),
        }

    inventory = {
        "$schema": "cf2.p4.baseline-inventory.v1",
        "task_id": "P4-T01",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "status": "P4 REWORK / Gate Not Passed",
            "active_runtime_slot": "m4a4",
            "active_runtime_model": "weapons/v_rif_m4a1.mdl",
            "preservation_policy": "STRICT_READ_ONLY: No moving, deleting, or overwriting of existing MODs or baseline files.",
            "scope_isolation": "P5/P6 final assets and active addons are strictly out_of_scope_unreviewed for P4.",
        },
        "repository_p4_inputs": {
            "description": "Repository input files and scripts for Prototype-01 P4 pipeline",
            "file_count": len(p4_input_entries),
            "files": p4_input_entries,
        },
        "d3_f4_baseline": {
            "classification": "user_confirmed_previous_stage",
            "status_description": "Known runnable visual baseline confirmed in-game by user across previous stages. Must be preserved, not deleted or overwritten.",
            "path": f4_mod_dir,
            "exists": os.path.exists(f4_mod_dir),
            "file_count": len(f4_files),
            "files": f4_files,
        },
        "p4_staging": {
            "classification": "automated_only_not_user_confirmed",
            "status_description": "Automated pipeline output. Verified copy-identical to historical p_cf_bornbeast_m4a4_p4_pipeline_tmp in mods_temp, but not yet user-confirmed in-game or validated with complete gate trace.",
            "path": p4_staging_dir,
            "exists": os.path.exists(p4_staging_dir),
            "file_count": len(p4_staging_files),
            "files": p4_staging_files,
        },
        "mods_temp_inventory": {
            "description": "Historical MOD copies stored in MIGI mods_temp directory",
            "mods": {
                "p_cf_bornbeast_m4a4_f4_recognizable_tmp": {
                    "classification": "user_confirmed_previous_stage",
                    "path": f4_mod_dir,
                    "exists": os.path.exists(f4_mod_dir),
                    "file_count": len(f4_files),
                    "files": f4_files,
                },
                "p_cf_bornbeast_m4a4_p4_pipeline_tmp": {
                    "classification": "automated_only_not_user_confirmed",
                    "path": p4_mod_dir,
                    "exists": os.path.exists(p4_mod_dir),
                    "file_count": len(p4_mod_files),
                    "files": p4_mod_files,
                },
            },
        },
        "active_migi_addon": {
            "classification": "out_of_scope_unreviewed",
            "status_description": "Addon in MIGI addons directory belonging to P6/final track. Strictly out of scope for P4 review. Must not be used as input, golden fixture, or pass evidence. Must not be deleted, moved, or overwritten.",
            "path": active_addon_dir,
            "exists": os.path.exists(active_addon_dir),
            "file_count": len(active_addon_files),
            "files": active_addon_files,
        },
        "consistency_analysis": {
            "staging_vs_mods_temp_p4": {
                "total_runtime_files": len(staging_vs_p4_mod),
                "matching_runtime_files": sum(1 for v in staging_vs_p4_mod.values() if v["match"]),
                "all_match": all(v["match"] for v in staging_vs_p4_mod.values()),
                "detail": staging_vs_p4_mod,
            },
        },
    }

    out_dir = os.path.join(ROOT, "work", "m4a1_s_bornbeast", "p4_prototype_01")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "baseline_inventory.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated baseline inventory: {out_file}")
    print(f"Repository inputs: {len(p4_input_entries)} entries")
    print(f"F4 MOD (user_confirmed_previous_stage): {len(f4_files)} files")
    print(f"P4 MOD (automated_only_not_user_confirmed): {len(p4_mod_files)} files")
    print(f"P4 Staging (automated_only_not_user_confirmed): {len(p4_staging_files)} files")
    print(f"Active Final Addon (out_of_scope_unreviewed): {len(active_addon_files)} files")
    print(f"Staging vs mods_temp P4 match: {all(v['match'] for v in staging_vs_p4_mod.values())}")

if __name__ == "__main__":
    main()
