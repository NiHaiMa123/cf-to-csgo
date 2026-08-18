# -*- coding: utf-8 -*-
"""Build the D3 R1 main-body-only M4A4 replacement in an isolated game root."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _paths import game_dir  # noqa: E402

REFERENCE = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a4"
ALIGNED_OBJ = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "source_dump" / "c3_alignment_m4a4" / "PV-M4A1_S_BornBeast_Classic_c3_aligned.obj"
C3_MANIFEST = PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "c3_alignment_m4a4_manifest.json"
REPORT_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "d3_m4a4"
TARGET_MANIFEST = PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "m4a4_target_manifest.json"
MAIN_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast"
CLIP_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast01"
BOLT_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast02"
PART03_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast03"
PART04_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast04"
PART05_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast05"
PART06_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast06"
PART07_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast07"
PART08_GROUP = "PV-M4A1_S_BornBeast_Classic_M4A1S_BornBeast08"
GROUP_BINDINGS = {
    MAIN_GROUP: (3, "v_weapon.M4A1_Parent"),
    CLIP_GROUP: (4, "v_weapon.M4A1_Clip"),
    BOLT_GROUP: (29, "v_weapon.M4A1_Bolt"),
    PART03_GROUP: (3, "v_weapon.M4A1_Parent"),
    PART04_GROUP: (3, "v_weapon.M4A1_Parent"),
    PART05_GROUP: (3, "v_weapon.M4A1_Parent"),
    PART06_GROUP: (3, "v_weapon.M4A1_Parent"),
    PART07_GROUP: (3, "v_weapon.M4A1_Parent"),
    PART08_GROUP: (3, "v_weapon.M4A1_Parent"),
}
LAYER_GROUPS = {
    "main": (MAIN_GROUP,),
    "clip": (MAIN_GROUP, CLIP_GROUP),
    "bolt": (MAIN_GROUP, CLIP_GROUP, BOLT_GROUP),
    "part03": (MAIN_GROUP, CLIP_GROUP, BOLT_GROUP, PART03_GROUP),
    "part04": (MAIN_GROUP, CLIP_GROUP, BOLT_GROUP, PART03_GROUP, PART04_GROUP),
    "part05": (MAIN_GROUP, CLIP_GROUP, BOLT_GROUP, PART03_GROUP, PART04_GROUP, PART05_GROUP),
    "full": (
        MAIN_GROUP, CLIP_GROUP, BOLT_GROUP, PART03_GROUP, PART04_GROUP, PART05_GROUP,
        PART06_GROUP, PART07_GROUP, PART08_GROUP,
    ),
}
STATIC_R1_GROUPS = {PART03_GROUP, PART04_GROUP, PART05_GROUP, PART06_GROUP, PART07_GROUP, PART08_GROUP}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smd_prefix(reference_smd: Path) -> list[str]:
    lines = reference_smd.read_text(encoding="utf-8", errors="replace").splitlines()
    triangle_at = next(i for i, line in enumerate(lines) if line.strip().lower() == "triangles")
    return lines[:triangle_at]


def parse_obj(path: Path, selected_groups: tuple[str, ...]) -> tuple[list[tuple[float, float, float]], list[tuple[float, float]], list[tuple[float, float, float]], list[tuple[str, str, list[tuple[int, int, int]]]]]:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces: list[tuple[str, str, list[tuple[int, int, int]]]] = []
    group = ""
    material = "rif_m4a1"
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "vt":
            uvs.append(tuple(map(float, parts[1:3])))
        elif parts[0] == "vn":
            normals.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "g":
            group = parts[1] if len(parts) > 1 else ""
        elif parts[0] == "usemtl":
            material = parts[1] if len(parts) > 1 else "rif_m4a1"
        elif parts[0] == "f" and group in selected_groups:
            refs: list[tuple[int, int, int]] = []
            for token in parts[1:]:
                fields = token.split("/")
                if len(fields) != 3 or not all(fields):
                    raise ValueError(f"D3 requires v/vt/vn faces, got: {raw}")
                refs.append(tuple(int(value) - 1 for value in fields))
            if len(refs) != 3:
                raise ValueError(f"D3 requires triangulated OBJ, got {len(refs)} corners")
            faces.append((group, material, refs))
    if not faces:
        raise ValueError(f"selected groups not found: {selected_groups}")
    return vertices, uvs, normals, faces


def write_layer_smd(reference_smd: Path, obj: Path, output: Path, selected_groups: tuple[str, ...]) -> dict[str, Any]:
    vertices, uvs, normals, faces = parse_obj(obj, selected_groups)
    lines = smd_prefix(reference_smd)
    lines.append("triangles")
    used_vertices: dict[str, set[int]] = {group: set() for group in selected_groups}
    triangle_counts: dict[str, int] = {group: 0 for group in selected_groups}
    materials: set[str] = set()
    for group, _source_material, refs in faces:
        bone_index, _bone_name = GROUP_BINDINGS[group]
        lines.append("rif_m4a1")
        materials.add("rif_m4a1")
        for vi, ti, ni in refs:
            position = vertices[vi]
            normal = normals[ni]
            uv = uvs[ti]
            used_vertices[group].add(vi)
            lines.append(
                f"  {bone_index} "
                + " ".join(f"{value:.9f}" for value in (*position, *normal, uv[0], uv[1]))
                + f" 1 {bone_index} 1.000000"
            )
        triangle_counts[group] += 1
    lines.append("end")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "groups": [
            {
                "source_group": group,
                "rigid_bone_index": GROUP_BINDINGS[group][0],
                "rigid_bone_name": GROUP_BINDINGS[group][1],
                "unique_position_indices": len(used_vertices[group]),
                "triangle_count": triangle_counts[group],
            }
            for group in selected_groups
        ],
        "unique_position_indices": sum(len(indices) for indices in used_vertices.values()),
        "triangle_count": len(faces),
        "corner_count": len(faces) * 3,
        "material": sorted(materials),
    }


def mdl_header(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    i32 = lambda offset: int.from_bytes(data[offset:offset + 4], "little", signed=True)
    return {
        "magic": data[:4].decode("ascii", errors="replace"),
        "version": i32(4),
        "internal_name": data[12:76].split(b"\0", 1)[0].decode("ascii", errors="replace"),
        "bone_count": i32(156),
        "local_animation_count": i32(180),
        "local_sequence_count": i32(188),
        "size_bytes": len(data),
        "sha256": sha256(path),
    }


def smd_primary_bone_counts(path: Path) -> dict[int, int]:
    counts: Counter[int] = Counter()
    in_triangles = False
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line == "triangles":
            in_triangles = True
            continue
        if in_triangles and line == "end":
            break
        fields = line.split()
        if in_triangles and len(fields) >= 9 and fields[0].lstrip("-").isdigit():
            counts[int(fields[0])] += 1
    return dict(sorted(counts.items()))


def smd_bone_motion(path: Path, bone_index: int) -> dict[str, Any]:
    samples: list[list[float]] = []
    in_skeleton = False
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line == "skeleton":
            in_skeleton = True
            continue
        if in_skeleton and line == "end":
            break
        fields = line.split()
        if in_skeleton and len(fields) >= 7 and fields[0].lstrip("-").isdigit() and int(fields[0]) == bone_index:
            samples.append([float(value) for value in fields[1:7]])
    if not samples:
        raise ValueError(f"bone {bone_index} has no samples in {path}")
    first = samples[0]
    max_delta = max(abs(value - first[index]) for sample in samples for index, value in enumerate(sample))
    return {"path": str(path), "bone_index": bone_index, "sample_count": len(samples), "max_component_delta": max_delta}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studiomdl", type=Path, default=Path(game_dir()) / "bin" / "studiomdl.exe")
    parser.add_argument(
        "--decompiler",
        type=Path,
        default=PROJECT_ROOT / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe",
    )
    parser.add_argument("--deploy-migi", action="store_true")
    parser.add_argument("--migi-addon", type=Path)
    parser.add_argument("--layer", choices=tuple(LAYER_GROUPS), default="main")
    args = parser.parse_args()
    selected_groups = LAYER_GROUPS[args.layer]
    build = PROJECT_ROOT / "build" / "m4a1_s_bornbeast_m4a4" / f"d3_r1_{args.layer}"
    manual_check_path = REPORT_DIR / ("d3_manual_game_check.json" if args.layer == "main" else f"d3_{args.layer}_manual_game_check.json")
    qc_source = REFERENCE / "decompiled" / "v_rif_m4a1.qc"
    reference_smd = REFERENCE / "decompiled" / "v_m4a1_model.smd"
    required = (qc_source, reference_smd, ALIGNED_OBJ, C3_MANIFEST, args.studiomdl, args.decompiler)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("D3 inputs missing: " + ", ".join(missing))

    m4a4_reference = json.loads((REFERENCE / "reference_report.json").read_text(encoding="utf-8"))
    m4a1s_reference_path = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a1_s" / "reference_report.json"
    m4a1s_reference = json.loads(m4a1s_reference_path.read_text(encoding="utf-8"))
    common_bind_bones = {
        "v_weapon.M4A1_Parent": "v_weapon.M4A1_s_Parent",
        "v_weapon.M4A1_Clip": "v_weapon.M4A1_Clip",
        "v_weapon.M4A1_Bolt": "v_weapon.M4A1_Bolt",
        "v_weapon.M4A1_Trigger": "v_weapon.M4A1_Trigger",
        "v_weapon.flash": "v_weapon.flash",
        "v_weapon.shelleject": "v_weapon.shelleject",
    }
    m4a4_bones = {item["name"]: item for item in m4a4_reference["bones"]["hierarchy"]}
    m4a1s_bones = {item["name"]: item for item in m4a1s_reference["bones"]["hierarchy"]}
    bind_comparison = {
        m4a4_name: {
            "m4a1_s_bone": m4a1s_name,
            "m4a4": m4a4_bones[m4a4_name]["transform"],
            "m4a1_s": m4a1s_bones[m4a1s_name]["transform"],
            "exact_match": m4a4_bones[m4a4_name]["transform"] == m4a1s_bones[m4a1s_name]["transform"],
        }
        for m4a4_name, m4a1s_name in common_bind_bones.items()
    }
    c3_manifest = json.loads(C3_MANIFEST.read_text(encoding="utf-8"))
    if c3_manifest.get("schema") != "cf2.m4a4.c3-transform-manifest.v1" or c3_manifest.get("status") != "locked_for_D_with_manual_attachment_gate":
        raise SystemExit("D3 requires a locked independent M4A4 C3 transform")

    target_manifest = {
        "schema": "cf2.m4a4.target-manifest.v1",
        "source_weapon": "CF M4A1-S BornBeast Classic",
        "runtime_target": {"slot": "m4a4", "modelname": "weapons/v_rif_m4a1.mdl"},
        "silencer_policy": "cancelled; no detachable silencer bone, bodygroup, attachment or sequence",
        "official_reference": str(REFERENCE / "reference_report.json"),
        "canonical_skeleton": {"bone_count": 57, "hierarchy": m4a4_reference["bones"]["hierarchy"]},
        "sequences": [item["name"] for item in m4a4_reference["sequences"]],
        "attachments": m4a4_reference["attachments"],
        "material_placeholder": "rif_m4a1",
        "c3_frame_compatibility": {
            "basis": "M4A1-S and M4A4 bind transforms differ, so M4A4 was independently refitted against v_m4a1_model.smd.",
            "old_vs_new_bind_transforms": bind_comparison,
            "independent_m4a4_c3_manifest": str(C3_MANIFEST),
            "m4a1_s_only_bones_removed": sorted(set(m4a1s_bones) - set(m4a4_bones)),
        },
        "d3_r1_mesh_mapping": {
            "M4A1S_BornBeast": "v_weapon.M4A1_Parent",
            "M4A1S_BornBeast01": "v_weapon.M4A1_Clip",
            "M4A1S_BornBeast02": "v_weapon.M4A1_Bolt",
            "M4A1S_BornBeast03": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
            "M4A1S_BornBeast04": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
            "M4A1S_BornBeast05": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
            "M4A1S_BornBeast06": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
            "M4A1S_BornBeast07": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
            "M4A1S_BornBeast08": "v_weapon.M4A1_Parent (R1 explicit static downgrade)",
        },
        "deferred_mesh_mapping": {},
    }
    TARGET_MANIFEST.write_text(json.dumps(target_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if build.exists():
        shutil.rmtree(build)
    source1 = build / "source1"
    isolated_csgo = build / "game_root" / "csgo"
    addon = build / "addon"
    source1.mkdir(parents=True)
    isolated_csgo.mkdir(parents=True)
    shutil.copytree(REFERENCE / "decompiled", source1, dirs_exist_ok=True)
    shutil.copy2(Path(game_dir()) / "csgo" / "gameinfo.txt", isolated_csgo / "gameinfo.txt")
    shutil.copytree(REFERENCE / "source_vpk" / "materials", isolated_csgo / "materials", dirs_exist_ok=True)

    layer_smd_name = f"cf_bornbeast_{args.layer}_m4a4.smd"
    mesh_stats = write_layer_smd(reference_smd, ALIGNED_OBJ, source1 / layer_smd_name, selected_groups)
    expected_primary_bones: Counter[int] = Counter()
    for item in mesh_stats["groups"]:
        expected_primary_bones[item["rigid_bone_index"]] += item["triangle_count"] * 3
    qc_path = source1 / "v_rif_m4a1.qc"
    qc_text = qc_path.read_text(encoding="utf-8", errors="replace")
    qc_text, replacements = re.subn(
        r'studio\s+"v_m4a1_model\.smd"', f'studio "{layer_smd_name}"', qc_text, count=1, flags=re.I
    )
    if replacements != 1:
        raise SystemExit("official M4A4 QC bodygroup could not be replaced exactly once")
    qc_path.write_text(qc_text, encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [str(args.studiomdl.resolve()), "-game", str(isolated_csgo), str(qc_path)],
        cwd=source1,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (REPORT_DIR / f"d3_{args.layer}_studiomdl.stdout.log").write_text(process.stdout or "", encoding="utf-8")
    (REPORT_DIR / f"d3_{args.layer}_studiomdl.stderr.log").write_text(process.stderr or "", encoding="utf-8")
    if process.returncode != 0:
        raise SystemExit("D3 studiomdl failed; inspect work/m4a1_s_bornbeast/d3_m4a4 logs")

    compiled = isolated_csgo / "models" / "weapons" / "v_rif_m4a1.mdl"
    if not compiled.is_file():
        raise SystemExit("studiomdl exited 0 but v_rif_m4a1.mdl is missing")
    copied: list[str] = []
    for path in isolated_csgo.rglob("*"):
        if path.is_file() and path.relative_to(isolated_csgo).parts[0].lower() in {"models", "materials"}:
            relative = path.relative_to(isolated_csgo)
            destination = addon / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied.append(relative.as_posix())

    header = mdl_header(compiled)
    deployment: dict[str, Any] = {"migi_deployed": False, "game_files_modified": False}
    if args.deploy_migi:
        target = args.migi_addon or (
            Path(game_dir()) / "migi" / "csgo" / "addons" / f"p_cf_bornbeast_m4a4_d3_{args.layer}_tmp"
        )
        target = target.resolve()
        existed_before = target.exists()
        if existed_before:
            source_files = {path.relative_to(addon).as_posix(): sha256(path) for path in addon.rglob("*") if path.is_file()}
            target_files = {path.relative_to(target).as_posix(): sha256(path) for path in target.rglob("*") if path.is_file()}
            if source_files != target_files:
                raise SystemExit(f"refusing to overwrite non-identical MIGI addon: {target}")
        else:
            shutil.copytree(addon, target)
        deployment = {
            "migi_deployed": True,
            "migi_addon": str(target),
            "game_files_modified": False,
            "existing_identical_addon_accepted": existed_before,
        }
    roundtrip_dir = build / "compiled_decompiled"
    roundtrip_dir.mkdir(parents=True)
    decompile = subprocess.run(
        [str(args.decompiler.resolve()), str(compiled), str(roundtrip_dir)],
        cwd=build,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (REPORT_DIR / f"d3_{args.layer}_roundtrip_decompiler.stdout.log").write_text(decompile.stdout or "", encoding="utf-8")
    (REPORT_DIR / f"d3_{args.layer}_roundtrip_decompiler.stderr.log").write_text(decompile.stderr or "", encoding="utf-8")
    if decompile.returncode != 0:
        raise SystemExit("D3 round-trip decompile failed")
    report_script = Path(__file__).with_name("report_m4a1_s_reference.py")
    report_process = subprocess.run(
        [
            sys.executable,
            str(report_script),
            "--reference-dir", str(roundtrip_dir),
            "--weapon", "M4A4",
            "--expected-modelname", r"weapons\v_rif_m4a1.mdl",
            "--schema", "cf2.m4a4.d3-roundtrip-reference.v1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if report_process.returncode != 0:
        (REPORT_DIR / f"d3_{args.layer}_roundtrip_report.stderr.log").write_text(report_process.stderr or "", encoding="utf-8")
        raise SystemExit("D3 round-trip report failed")
    roundtrip = json.loads((roundtrip_dir / "reference_report.json").read_text(encoding="utf-8"))
    roundtrip_meshes = [item for item in roundtrip["smd_files"] if item["kind"] == "mesh"]
    roundtrip_mesh_path = next(roundtrip_dir.rglob("cf_bornbeast_*_m4a4.smd"))
    roundtrip_primary_bones = smd_primary_bone_counts(roundtrip_mesh_path)
    clip_animation_evidence = {
        "idle": smd_bone_motion(REFERENCE / "decompiled" / "v_rif_m4a1_anims" / "idle.smd", 4),
        "reload": smd_bone_motion(REFERENCE / "decompiled" / "v_rif_m4a1_anims" / "reload.smd", 4),
    }
    bolt_animation_evidence = {
        name: smd_bone_motion(REFERENCE / "decompiled" / "v_rif_m4a1_anims" / f"{name}.smd", 29)
        for name in ("idle", "shoot1", "shoot2", "shoot3", "reload", "draw")
    }
    roundtrip_summary = {
        "internal_modelname": roundtrip["target"]["internal_modelname"],
        "bone_count": roundtrip["bones"]["count"],
        "sequence_count": len(roundtrip["sequences"]),
        "sequence_names": [item["name"] for item in roundtrip["sequences"]],
        "attachment_count": len(roundtrip["attachments"]),
        "triangle_count": sum(item["triangle_count"] for item in roundtrip_meshes),
        "materials": roundtrip["materials"]["smd_materials"],
    }
    manual_game_check = (
        json.loads(manual_check_path.read_text(encoding="utf-8"))
        if manual_check_path.is_file()
        else {"status": "not_run", "reason": "Awaiting explicit user confirmation in CS:GO Legacy."}
    )
    report = {
        "schema": f"cf2.m4a4.d3-r1-{args.layer}.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": {
            "slot": "m4a4",
            "internal_modelname": "weapons/v_rif_m4a1.mdl",
            "silencer_feature": "cancelled_not_present_in_m4a4_baseline",
        },
        "scope": {
            "main": "main_body_only", "clip": "main_plus_clip", "bolt": "main_plus_clip_plus_bolt",
            "part03": "main_plus_clip_plus_bolt_plus_static_part03",
            "part04": "main_plus_clip_plus_bolt_plus_static_parts03_04",
            "part05": "main_plus_clip_plus_bolt_plus_static_parts03_05",
            "full": "all_nine_weapon_meshes_with_parts03_08_static",
        }[args.layer],
        "inputs": {
            "official_reference_report": str(REFERENCE / "reference_report.json"),
            "target_manifest": str(TARGET_MANIFEST),
            "aligned_obj": str(ALIGNED_OBJ),
            "alignment_note": "Uses an independent official-M4A4 C3 fit; the old M4A1-S transform is explicitly rejected.",
        },
        "mesh": mesh_stats,
        "compile": {
            "exit_code": process.returncode,
            "command": [str(args.studiomdl.resolve()), "-game", str(isolated_csgo), str(qc_path)],
            "compiled_header": header,
            "addon_files": sorted(copied),
        },
        "roundtrip": roundtrip_summary,
        "binding_and_animation_evidence": {
            "roundtrip_primary_bone_corner_counts": {str(key): value for key, value in roundtrip_primary_bones.items()},
            "clip_bone_motion": clip_animation_evidence,
            "bolt_bone_motion": bolt_animation_evidence,
        },
        "explicit_downgrades": ([{
            "mesh": group.split("Classic_", 1)[-1],
            "binding": "v_weapon.M4A1_Parent",
            "status": "r1_static_visibility_only",
            "reason": "CF animation keyframes are not decoded and no semantically equivalent official M4A4 bone is proven.",
        } for group in selected_groups if group in STATIC_R1_GROUPS]),
        "deployment": deployment,
        "manual_game_check": manual_game_check,
        "validation": {
            "compile_pass": process.returncode == 0,
            "internal_name_is_m4a4_slot": header["internal_name"].replace("\\", "/").lower() == "weapons/v_rif_m4a1.mdl",
            "bone_count_is_official_m4a4": header["bone_count"] == 57,
            "sequence_count_is_official_m4a4": header["local_sequence_count"] == 9,
            "mesh_bindings_match_layer": all(
                item["rigid_bone_index"] == GROUP_BINDINGS[item["source_group"]][0]
                for item in mesh_stats["groups"]
            ) and len(mesh_stats["groups"]) == len(selected_groups),
            "roundtrip_primary_bones_match_layer": roundtrip_primary_bones == dict(sorted(expected_primary_bones.items())),
            "clip_motion_semantics_match_layer": (
                True if args.layer == "main" else
                clip_animation_evidence["idle"]["max_component_delta"] <= 1e-6
                and clip_animation_evidence["reload"]["max_component_delta"] > 0.1
            ),
            "bolt_motion_semantics_match_layer": (
                True if args.layer not in {"bolt", "part03", "part04", "part05", "full"} else
                bolt_animation_evidence["idle"]["max_component_delta"] <= 1e-6
                and all(bolt_animation_evidence[name]["max_component_delta"] <= 1e-6 for name in ("shoot1", "shoot2", "shoot3", "reload"))
                and bolt_animation_evidence["draw"]["max_component_delta"] > 0.1
            ),
            "static_downgrades_acknowledged": all(
                any(item["source_group"] == group and item["rigid_bone_index"] == 3 for item in mesh_stats["groups"])
                for group in selected_groups if group in STATIC_R1_GROUPS
            ),
            "material_is_explicit_placeholder": mesh_stats["material"] == ["rif_m4a1"],
            "independent_m4a4_c3_transform_locked": c3_manifest.get("status") == "locked_for_D_with_manual_attachment_gate",
            "roundtrip_structure_matches": (
                roundtrip_summary["internal_modelname"].replace("\\", "/").lower() == "weapons/v_rif_m4a1.mdl"
                and roundtrip_summary["bone_count"] == 57
                and roundtrip_summary["sequence_count"] == 9
                and roundtrip_summary["attachment_count"] == 2
                and roundtrip_summary["triangle_count"] == mesh_stats["triangle_count"]
                and roundtrip_summary["materials"] == ["rif_m4a1"]
            ),
            "original_game_files_unmodified": deployment["game_files_modified"] is False,
        },
        "provisional": [
            "Official rif_m4a1 is a visibility placeholder, not the final CF material.",
            "Only main is included; magazine, bolt and decorative groups 01-08 are deferred." if args.layer == "main" else ("Main and 01 magazine are included; bolt and decorative groups 02-08 are deferred." if args.layer == "clip" else ("Main, 01 magazine and 02 bolt/charging-handle group are included; decorative groups 03-08 are deferred." if args.layer == "bolt" else ("03 is included as an explicit Parent-bound R1 static downgrade; decorative groups 04-08 are deferred." if args.layer == "part03" else ("03 and 04 are included as explicit Parent-bound R1 static downgrades; decorative groups 05-08 are deferred." if args.layer == "part04" else ("03 through 05 are included as explicit Parent-bound R1 static downgrades; decorative groups 06-08 are deferred." if args.layer == "part05" else "All nine weapon meshes are included; 03-08 remain explicit Parent-bound R1 static downgrades."))))),
            "The CF main mesh contains its modeled muzzle/barrel silhouette; no detachable silencer feature is authored.",
            "Game visibility and animation behavior require a manual check of the staged MIGI addon." if manual_game_check["status"] != "passed_user_confirmed" else "D3 R1 game behavior passed by explicit user confirmation; later mesh layers require their own checks.",
        ],
    }
    report["validation"]["all_automated_checks_pass"] = all(report["validation"].values())
    output = REPORT_DIR / f"d3_r1_{args.layer}_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "header": header, "mesh": mesh_stats, "pass": report["validation"]["all_automated_checks_pass"]}, ensure_ascii=False, indent=2))
    return 0 if report["validation"]["all_automated_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
