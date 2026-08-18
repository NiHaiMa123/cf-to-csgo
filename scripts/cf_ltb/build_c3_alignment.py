#!/usr/bin/env python3
"""Build and validate the shared CF-LTB -> Source 1 C3 alignment.

The script deliberately works from the B3 raw OBJ.  Every exported weapon group
receives one similarity transform; no group is normalized or hand-adjusted.
The official M4A1-S reference SMDs provide the target coordinate frame.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np


WEAPON_GROUP_TOKEN = "M4A1S_BornBeast"
M4A1S_WEAPON_BONES = {3: "Parent", 4: "Clip", 9: "Silencer", 28: "Trigger", 29: "Bolt"}
M4A4_WEAPON_BONES = {3: "Parent", 4: "Clip", 28: "Trigger", 29: "Bolt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_obj(path: Path) -> tuple[list[str], np.ndarray, np.ndarray, dict[str, list[int]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    vertices: list[list[float]] = []
    normals: list[list[float]] = []
    groups: dict[str, list[int]] = {}
    group = ""
    for line in lines:
        if line.startswith("g "):
            group = line[2:].strip()
            groups.setdefault(group, [])
        elif line.startswith("v "):
            vertices.append([float(value) for value in line.split()[1:4]])
            if group:
                groups[group].append(len(vertices) - 1)
        elif line.startswith("vn "):
            normals.append([float(value) for value in line.split()[1:4]])
    return lines, np.asarray(vertices), np.asarray(normals), groups


def parse_smd_vertices(path: Path) -> dict[int, np.ndarray]:
    by_bone: dict[int, list[list[float]]] = {}
    in_triangles = False
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line == "triangles":
            in_triangles = True
            continue
        if not in_triangles:
            continue
        if line == "end":
            break
        fields = line.split()
        if len(fields) < 9 or not fields[0].lstrip("-").isdigit():
            continue
        bone = int(fields[0])
        by_bone.setdefault(bone, []).append([float(fields[1]), float(fields[2]), float(fields[3])])
    return {bone: np.asarray(points) for bone, points in by_bone.items()}


def parse_smd_skeleton(path: Path) -> tuple[dict[int, tuple[str, int]], dict[int, np.ndarray]]:
    nodes: dict[int, tuple[str, int]] = {}
    local: dict[int, np.ndarray] = {}
    section = ""
    time_zero = False
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line in {"nodes", "skeleton", "triangles"}:
            section = line
            continue
        if line == "end":
            section = ""
            continue
        if section == "nodes" and line:
            node_id_text, remainder = line.split(maxsplit=1)
            name, parent_text = remainder.rsplit(maxsplit=1)
            nodes[int(node_id_text)] = (name.strip('"'), int(parent_text))
        elif section == "skeleton":
            if line.startswith("time "):
                time_zero = line == "time 0"
                continue
            fields = line.split()
            if time_zero and len(fields) >= 7 and fields[0].lstrip("-").isdigit():
                node_id = int(fields[0])
                position = np.asarray([float(value) for value in fields[1:4]])
                x, y, z = (float(value) for value in fields[4:7])
                cx, sx = math.cos(x), math.sin(x)
                cy, sy = math.cos(y), math.sin(y)
                cz, sz = math.cos(z), math.sin(z)
                rx = np.asarray([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
                ry = np.asarray([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
                rz = np.asarray([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
                matrix = np.eye(4)
                matrix[:3, :3] = rz @ ry @ rx
                matrix[:3, 3] = position
                local[node_id] = matrix
    global_matrices: dict[int, np.ndarray] = {}

    def resolve(node_id: int) -> np.ndarray:
        if node_id in global_matrices:
            return global_matrices[node_id]
        parent = nodes[node_id][1]
        global_matrices[node_id] = local[node_id] if parent < 0 else resolve(parent) @ local[node_id]
        return global_matrices[node_id]

    for node_id in local:
        resolve(node_id)
    return nodes, global_matrices


def unique_points(points: np.ndarray, decimals: int = 5) -> np.ndarray:
    rounded = np.round(points, decimals=decimals)
    return np.unique(rounded, axis=0)


def sample_points(points: np.ndarray, limit: int) -> np.ndarray:
    points = unique_points(points)
    if len(points) <= limit:
        return points
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    return points[order[np.linspace(0, len(points) - 1, limit, dtype=int)]]


def nearest(source: np.ndarray, target: np.ndarray, chunk: int = 256) -> tuple[np.ndarray, np.ndarray]:
    indices: list[np.ndarray] = []
    distances: list[np.ndarray] = []
    for start in range(0, len(source), chunk):
        part = source[start : start + chunk]
        squared = np.sum((part[:, None, :] - target[None, :, :]) ** 2, axis=2)
        idx = np.argmin(squared, axis=1)
        indices.append(idx)
        distances.append(np.sqrt(squared[np.arange(len(part)), idx]))
    return np.concatenate(indices), np.concatenate(distances)


def signed_axis_rotations() -> list[np.ndarray]:
    rotations: list[np.ndarray] = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix = np.zeros((3, 3))
            for output_axis, input_axis in enumerate(permutation):
                matrix[output_axis, input_axis] = signs[output_axis]
            if np.linalg.det(matrix) > 0.5:
                rotations.append(matrix)
    return rotations


def fit_scale_translation(source: np.ndarray, target: np.ndarray, rotation: np.ndarray) -> tuple[float, np.ndarray]:
    rotated = source @ rotation.T
    source_center = rotated.mean(axis=0)
    target_center = target.mean(axis=0)
    centered_source = rotated - source_center
    centered_target = target - target_center
    denominator = float(np.sum(centered_source * centered_source))
    scale = float(np.sum(centered_source * centered_target) / denominator) if denominator else 1.0
    if scale < 0:
        scale = -scale
    translation = target_center - scale * source_center
    return scale, translation


def robust_icp(
    source: np.ndarray,
    target: np.ndarray,
    initial_rotation: np.ndarray,
    initial_scale: float,
    initial_translation: np.ndarray,
    iterations: int = 16,
) -> tuple[np.ndarray, float, np.ndarray, dict[str, float]]:
    rotation = initial_rotation.copy()
    scale = initial_scale
    translation = initial_translation.copy()
    for _ in range(iterations):
        transformed = scale * (source @ rotation.T) + translation
        indices, distances = nearest(transformed, target)
        cutoff = float(np.quantile(distances, 0.72))
        keep = distances <= cutoff
        src = source[keep]
        dst = target[indices[keep]]
        src_center = src.mean(axis=0)
        dst_center = dst.mean(axis=0)
        src_zero = src - src_center
        dst_zero = dst - dst_center
        covariance = src_zero.T @ dst_zero
        u, singular, vt = np.linalg.svd(covariance)
        correction = np.eye(3)
        correction[-1, -1] = np.sign(np.linalg.det(vt.T @ u.T))
        rotation = vt.T @ correction @ u.T
        denominator = float(np.sum(src_zero * src_zero))
        scale = float(np.sum(singular * np.diag(correction)) / denominator)
        translation = dst_center - scale * (src_center @ rotation.T)
    transformed = scale * (source @ rotation.T) + translation
    _, forward = nearest(transformed, target)
    _, reverse = nearest(target, transformed)
    metrics = {
        "forward_median": float(np.median(forward)),
        "forward_p90": float(np.quantile(forward, 0.9)),
        "reverse_median": float(np.median(reverse)),
        "reverse_p90": float(np.quantile(reverse, 0.9)),
        "symmetric_trimmed_mean": float(
            (np.mean(forward[forward <= np.quantile(forward, 0.8)]) + np.mean(reverse[reverse <= np.quantile(reverse, 0.8)])) / 2
        ),
    }
    return rotation, scale, translation, metrics


def bounds(points: np.ndarray) -> dict[str, list[float]]:
    return {
        "min": np.min(points, axis=0).round(6).tolist(),
        "max": np.max(points, axis=0).round(6).tolist(),
        "size": np.ptp(points, axis=0).round(6).tolist(),
        "center": ((np.min(points, axis=0) + np.max(points, axis=0)) / 2).round(6).tolist(),
    }


def closest_landmark(source_points: np.ndarray, target_points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    indices, distances = nearest(source_points, target_points)
    best = int(np.argmin(distances))
    return source_points[best], target_points[indices[best]], float(distances[best])


def transform_obj(lines: list[str], rotation: np.ndarray, scale: float, translation: np.ndarray) -> list[str]:
    output: list[str] = []
    normal_index = 0
    vertex_index = 0
    for line in lines:
        if line.startswith("v "):
            point = np.asarray([float(value) for value in line.split()[1:4]])
            value = scale * (point @ rotation.T) + translation
            output.append("v " + " ".join(f"{component:.9f}" for component in value))
            vertex_index += 1
        elif line.startswith("vn "):
            normal = np.asarray([float(value) for value in line.split()[1:4]]) @ rotation.T
            length = np.linalg.norm(normal)
            if length:
                normal /= length
            output.append("vn " + " ".join(f"{component:.9f}" for component in normal))
            normal_index += 1
        else:
            output.append(line)
    return output


def write_reference_obj(path: Path, source_by_bone: dict[int, np.ndarray], source_weapon_bones: dict[int, str], target_name: str) -> None:
    lines = [f"# Official {target_name} weapon-only reference extracted from Crowbar SMD"]
    offset = 1
    for bone in source_weapon_bones:
        points = source_by_bone.get(bone)
        if points is None:
            continue
        lines.append(f"g SOURCE_{source_weapon_bones[bone]}")
        for point in points:
            lines.append("v " + " ".join(f"{component:.9f}" for component in point))
        for index in range(offset, offset + len(points), 3):
            if index + 2 < offset + len(points):
                lines.append(f"f {index} {index + 1} {index + 2}")
        offset += len(points)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-obj", type=Path, required=True)
    parser.add_argument("--weapon-only-obj", type=Path, required=True)
    parser.add_argument("--reference-smd", type=Path, required=True)
    parser.add_argument("--silencer-smd", type=Path)
    parser.add_argument("--target-profile", choices=("m4a1_s", "m4a4"), default="m4a1_s")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()

    required_paths = [args.raw_obj, args.weapon_only_obj, args.reference_smd]
    if args.target_profile == "m4a1_s":
        if args.silencer_smd is None:
            parser.error("--silencer-smd is required for m4a1_s")
        required_paths.append(args.silencer_smd)
    for path in required_paths:
        if not path.is_file():
            parser.error(f"missing input: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # raw_obj is retained as the B3 provenance root.  The C1 weapon-only file is
    # a lossless index rewrite of those same raw coordinates and prevents the
    # two excluded CF arm meshes from leaking into the aligned D-stage output.
    obj_lines, obj_vertices, _, obj_groups = parse_obj(args.weapon_only_obj)
    weapon_indices = sorted(
        index
        for name, indices in obj_groups.items()
        if WEAPON_GROUP_TOKEN in name and "Fview-" not in name
        for index in indices
    )
    cf_weapon = obj_vertices[weapon_indices]
    if len(weapon_indices) != 3646 or len([name for name in obj_groups if WEAPON_GROUP_TOKEN in name and "Fview-" not in name]) != 9:
        raise RuntimeError("C3 requires the reviewed nine-mesh/3646-vertex B3 weapon set")

    source_by_bone = parse_smd_vertices(args.reference_smd)
    source_nodes, source_global = parse_smd_skeleton(args.reference_smd)
    source_weapon_bones = M4A1S_WEAPON_BONES if args.target_profile == "m4a1_s" else M4A4_WEAPON_BONES
    target_name = "M4A1-S" if args.target_profile == "m4a1_s" else "M4A4"
    if args.target_profile == "m4a1_s":
        silencer = parse_smd_vertices(args.silencer_smd)
        source_by_bone[9] = silencer[9]
    source_weapon = np.concatenate([source_by_bone[bone] for bone in source_weapon_bones])

    cf_sample = sample_points(cf_weapon, 1800)
    source_sample = sample_points(source_weapon, 2600)

    # The magazine and bolt centroids provide semantic anchors.  They prevent an
    # apparently good surface ICP result from aligning the wrong end of the gun.
    cf_main_name = next(name for name in obj_groups if name.endswith("_M4A1S_BornBeast"))
    cf_clip_name = next(name for name in obj_groups if name.endswith("_M4A1S_BornBeast01"))
    cf_bolt_name = next(name for name in obj_groups if name.endswith("_M4A1S_BornBeast02"))
    cf_anchors = np.asarray([
        obj_vertices[obj_groups[cf_main_name]].mean(axis=0),
        obj_vertices[obj_groups[cf_clip_name]].mean(axis=0),
        obj_vertices[obj_groups[cf_bolt_name]].mean(axis=0),
    ])
    source_anchors = np.asarray([
        source_by_bone[3].mean(axis=0),
        source_by_bone[4].mean(axis=0),
        source_by_bone[29].mean(axis=0),
    ])

    candidates = []
    for axis_rotation in signed_axis_rotations():
        scale, translation = fit_scale_translation(cf_anchors, source_anchors, axis_rotation)
        transformed_anchors = scale * (cf_anchors @ axis_rotation.T) + translation
        anchor_rms = float(np.sqrt(np.mean(np.sum((transformed_anchors - source_anchors) ** 2, axis=1))))
        if 1.0 <= scale <= 4.0:
            candidates.append((anchor_rms, axis_rotation, scale, translation))
    candidates.sort(key=lambda item: item[0])

    evaluated = []
    for anchor_rms, axis_rotation, scale, translation in candidates[:6]:
        rotation, fitted_scale, fitted_translation, metrics = robust_icp(
            cf_sample, source_sample, axis_rotation, scale, translation
        )
        transformed_anchors = fitted_scale * (cf_anchors @ rotation.T) + fitted_translation
        fitted_anchor_rms = float(np.sqrt(np.mean(np.sum((transformed_anchors - source_anchors) ** 2, axis=1))))
        score = metrics["symmetric_trimmed_mean"] + 0.35 * fitted_anchor_rms
        evaluated.append((score, rotation, fitted_scale, fitted_translation, metrics, fitted_anchor_rms, axis_rotation))
    evaluated.sort(key=lambda item: item[0])
    score, rotation, scale, translation, metrics, anchor_rms, axis_rotation = evaluated[0]

    transformed_weapon = scale * (cf_weapon @ rotation.T) + translation
    determinant = float(np.linalg.det(rotation))
    orthogonality_error = float(np.max(np.abs(rotation @ rotation.T - np.eye(3))))
    transformed_anchors = scale * (cf_anchors @ rotation.T) + translation
    anchor_errors = np.linalg.norm(transformed_anchors - source_anchors, axis=1)

    source_parent = unique_points(source_by_bone[3])
    transformed_cf_sample = sample_points(transformed_weapon, 3200)
    def hand_contact(hand_bone_name: str) -> dict[str, object]:
        hand_bone = source_global[name_to_id[hand_bone_name]][:3, 3]
        _, source_contact, bone_distance = closest_landmark(hand_bone[None, :], source_parent)
        _, cf_contact, distance = closest_landmark(source_contact[None, :], transformed_cf_sample)
        return {
            "official_hand_bone": hand_bone.round(6).tolist(),
            "official_contact": source_contact.round(6).tolist(),
            "nearest_cf_surface": cf_contact.round(6).tolist(),
            "surface_error": round(distance, 6),
            "hand_bone_to_official_surface": round(bone_distance, 6),
        }

    cf_main_transformed = scale * (obj_vertices[obj_groups[cf_main_name]] @ rotation.T) + translation
    cf_clip_transformed = scale * (obj_vertices[obj_groups[cf_clip_name]] @ rotation.T) + translation
    source_clip = unique_points(source_by_bone[4])
    # In Source coordinates the receiver-facing/top edge of both magazines is
    # the largest-Y end.  Averaging its cap is more stable than choosing one
    # coincident triangle vertex from two unlike magazine designs.
    source_interface_clip = source_clip[source_clip[:, 1] >= np.quantile(source_clip[:, 1], 0.95)].mean(axis=0)
    cf_interface_clip = cf_clip_transformed[
        cf_clip_transformed[:, 1] >= np.quantile(cf_clip_transformed[:, 1], 0.90)
    ].mean(axis=0)
    _, source_interface_parent, _ = closest_landmark(source_interface_clip[None, :], source_parent)
    _, cf_interface_main, _ = closest_landmark(cf_interface_clip[None, :], cf_main_transformed)
    magazine_interface_error = float(np.linalg.norm(cf_interface_clip - source_interface_clip))

    name_to_id = {name: node_id for node_id, (name, _) in source_nodes.items()}
    flash_matrix = source_global[name_to_id["v_weapon.flash"]]
    shell_matrix = source_global[name_to_id["v_weapon.shelleject"]]
    flash = flash_matrix[:3, 3]
    muzzle_flash2 = (flash_matrix @ np.asarray([9.5, 0.0, 0.0, 1.0]))[:3] if args.target_profile == "m4a1_s" else None
    shell = shell_matrix[:3, 3]

    def attachment_evidence(point: np.ndarray) -> dict[str, object]:
        _, nearest_cf, distance = closest_landmark(point[None, :], transformed_cf_sample)
        return {
            "official_position": point.round(6).tolist(),
            "nearest_cf_surface": nearest_cf.round(6).tolist(),
            "distance_to_cf_surface": round(distance, 6),
        }

    flash_evidence = attachment_evidence(flash)
    silenced_flash_evidence = attachment_evidence(muzzle_flash2) if muzzle_flash2 is not None else None
    shell_evidence = attachment_evidence(shell)
    expected_axis = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
    axis_delta = rotation @ expected_axis.T
    trace_value = max(-1.0, min(1.0, (float(np.trace(axis_delta)) - 1.0) / 2.0))
    expected_axis_delta_degrees = math.degrees(math.acos(trace_value))
    right_hand_evidence = hand_contact("v_weapon.Bip01_R_Hand")
    left_hand_evidence = hand_contact("v_weapon.Bip01_L_Hand")
    landmarks_pass = bool(
        right_hand_evidence["surface_error"] <= 1.75
        and left_hand_evidence["surface_error"] <= 1.0
        and magazine_interface_error <= 1.0
        and flash_evidence["distance_to_cf_surface"] <= 2.0
    )
    attachments_pass = bool(
        flash_evidence["distance_to_cf_surface"] <= 2.0
        and shell_evidence["distance_to_cf_surface"] <= 1.0
    )
    fov_envelope_safe = bool(
        np.all(np.min(transformed_weapon, axis=0) >= np.min(source_weapon, axis=0))
        and np.all(np.max(transformed_weapon, axis=0) <= np.max(source_weapon, axis=0))
    )
    geometry_fit_pass = bool(
        anchor_rms <= 1.25
        and magazine_interface_error <= 1.25
        and metrics["forward_p90"] <= 1.25
        and metrics["reverse_p90"] <= 1.25
    )
    core_gate_pass = bool(
        expected_axis_delta_degrees < 12.0
        and scale > 0
        and determinant > 0.999
        and (geometry_fit_pass if args.target_profile == "m4a4" else landmarks_pass and attachments_pass and fov_envelope_safe)
    )
    flash_axis = flash_matrix[:3, 0]
    recommended_muzzle_offset = float(
        np.dot(np.asarray(flash_evidence["nearest_cf_surface"]) - flash, flash_axis)
    )

    matrix = np.eye(4)
    matrix[:3, :3] = scale * rotation
    matrix[:3, 3] = translation
    inverse = np.linalg.inv(matrix)

    aligned_obj = args.output_dir / "PV-M4A1_S_BornBeast_Classic_c3_aligned.obj"
    aligned_obj.write_text("\n".join(transform_obj(obj_lines, rotation, scale, translation)) + "\n", encoding="utf-8")
    reference_obj = args.output_dir / f"official_{args.target_profile}_weapon_reference.obj"
    write_reference_obj(reference_obj, source_by_bone, source_weapon_bones, target_name)

    report = {
        "schema": f"cf2.{args.target_profile}.c3-alignment.v1",
        "status": "provisional_visual_gate",
        "policy": {
            "shared_transform": True,
            "weapon_mesh_count": 9,
            "weapon_vertex_count": len(weapon_indices),
            "per_mesh_normalization": False,
            "fit_target": f"official {target_name} weapon-only SMD geometry in bind pose",
            "fit_method": "semantic-anchor initialized, deterministic trimmed bidirectional ICP",
        },
        "inputs": {
            "raw_obj": str(args.raw_obj.resolve()),
            "raw_obj_sha256": sha256(args.raw_obj),
            "weapon_only_obj": str(args.weapon_only_obj.resolve()),
            "weapon_only_obj_sha256": sha256(args.weapon_only_obj),
            "reference_smd": str(args.reference_smd.resolve()),
            "reference_smd_sha256": sha256(args.reference_smd),
            "silencer_smd": str(args.silencer_smd.resolve()) if args.silencer_smd else None,
            "silencer_smd_sha256": sha256(args.silencer_smd) if args.silencer_smd else None,
        },
        "coordinate_assumptions": {
            "source": "raw LTB model coordinates from B3; no center/scale/rotation",
            "target": f"Source 1 SMD model coordinates in official {target_name} bind pose",
            "vector_convention": "report matrix uses homogeneous column vectors: p_source = M @ [p_cf, 1]",
            "normal_transform": "rotation only followed by normalization; uniform positive scale",
            "winding": "preserved because rotation determinant is positive",
            "expected_discrete_axis_map": "Source X=CF X, Source Y=-CF Z, Source Z=CF Y",
        },
        "transform": {
            "matrix_cf_to_source": matrix.round(9).tolist(),
            "matrix_source_to_cf": inverse.round(9).tolist(),
            "rotation": rotation.round(9).tolist(),
            "uniform_scale": round(scale, 9),
            "translation": translation.round(9).tolist(),
            "rotation_determinant": round(determinant, 9),
            "orthogonality_max_error": orthogonality_error,
            "expected_axis_delta_degrees": expected_axis_delta_degrees,
            "initial_axis_rotation": axis_rotation.tolist(),
        },
        "semantic_anchors": {
            name: {
                "cf_raw": cf_anchors[index].round(6).tolist(),
                "source_reference": source_anchors[index].round(6).tolist(),
                "cf_transformed": transformed_anchors[index].round(6).tolist(),
                "error": round(float(anchor_errors[index]), 6),
            }
            for index, name in enumerate(("main_centroid", "magazine_centroid", "bolt_centroid"))
        },
        "four_landmarks": {
            "right_hand_grip": right_hand_evidence,
            "left_hand_foregrip": left_hand_evidence,
            "magazine_interface": {
                "official_clip_point": source_interface_clip.round(6).tolist(),
                "official_parent_point": source_interface_parent.round(6).tolist(),
                "cf_clip_point": cf_interface_clip.round(6).tolist(),
                "cf_main_point": cf_interface_main.round(6).tolist(),
                "clip_point_error": round(magazine_interface_error, 6),
            },
            "muzzle": flash_evidence,
        },
        "attachments": {
            "flash": flash_evidence,
            "muzzle_flash2_silenced": silenced_flash_evidence,
            "shelleject": shell_evidence,
            "recommended_muzzle_local_x_offset": round(recommended_muzzle_offset, 6),
            "official_muzzle_flash2_local_x_offset": 9.5 if args.target_profile == "m4a1_s" else None,
            "policy": "M4A4 uses its flash bone and has no detachable-silencer attachment path." if args.target_profile == "m4a4" else "D-stage QC must override muzzle_flash2 offset for the baked CF muzzle; do not retain the official 9.5 offset.",
        },
        "fit_metrics_source_units": {**metrics, "semantic_anchor_rms": anchor_rms, "selection_score": score},
        "bounds": {
            "cf_raw_weapon": bounds(cf_weapon),
            "cf_transformed_weapon": bounds(transformed_weapon),
            "official_weapon": bounds(source_weapon),
        },
        "outputs": {"aligned_obj": str(aligned_obj.resolve()), "reference_obj": str(reference_obj.resolve())},
        "gate": {
            "offline_transform_reproducible": True,
            "axis_mapping_plausible": expected_axis_delta_degrees < 12.0,
            "positive_uniform_scale": scale > 0 and determinant > 0.999,
            "four_landmarks_numeric_pass": landmarks_pass,
            "attachment_review": True,
            "bare_flash_and_shelleject_pass": attachments_pass,
            "official_silenced_flash_offset_compatible": (
                bool(silenced_flash_evidence["distance_to_cf_surface"] <= 2.0)
                if silenced_flash_evidence is not None else None
            ),
            "default_fov_envelope_safe": fov_envelope_safe,
            "geometry_fit_pass": geometry_fit_pass,
            "m4a4_attachment_and_fov_manual_gate": args.target_profile == "m4a4",
            "result": ("PASS_WITH_PROVISIONAL_ATTACHMENTS" if args.target_profile == "m4a4" else "PASS_WITH_REQUIRED_QC_ATTACHMENT_OVERRIDE") if core_gate_pass else "FAIL",
        },
        "provisional": [
            f"ICP is evidence for one shared transform, not proof that every decorative surface should match the stock {target_name}.",
            "Right-hand grip, left-hand foregrip, magazine interface and muzzle require Blender overlay confirmation.",
            "Flash and shell-eject attachment positions and viewmodel clipping remain unaccepted until visual review.",
        ],
    }
    report_path = args.output_dir / "c3_alignment_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": f"cf2.{args.target_profile}.c3-transform-manifest.v1",
        "status": ("locked_for_D_with_manual_attachment_gate" if args.target_profile == "m4a4" else "locked_for_D_with_attachment_override") if core_gate_pass else "failed_C3_gate",
        "source_report": str(report_path.resolve()),
        "source_report_sha256": sha256(report_path),
        "shared_transform_for_all_nine_weapon_meshes": True,
        "matrix_convention": "homogeneous column vector; p_source = matrix_cf_to_source @ [p_cf, 1]",
        "matrix_cf_to_source": matrix.round(9).tolist(),
        "uniform_scale": round(scale, 9),
        "rotation_determinant": round(determinant, 9),
        "axis_map": f"Source X=CF X, Source Y=-CF Z, Source Z=CF Y, followed by {expected_axis_delta_degrees:.4f}-degree fitted correction",
        "normal_policy": "rotation only then normalize",
        "winding_policy": "preserve; determinant is positive",
        "binding_frame": f"official {target_name} bind pose",
        "attachment_policy": {
            "flash": "official flash bone is within C3 tolerance",
            "shelleject": "official shelleject bone is within C3 tolerance",
            "muzzle": "use official M4A4 flash bone; no detachable-silencer path" if args.target_profile == "m4a4" else "override QC local-X offset; official 9.5 does not match the baked CF muzzle",
            "recommended_local_x_offset": round(recommended_muzzle_offset, 6),
        },
        "provisional": [
            "The D-stage first compile must visually confirm the idle pose at real game FOV.",
            "No detachable-silencer semantics are authored for the M4A4 target." if args.target_profile == "m4a4" else "Silencer detach semantics still require a mesh split or an explicit static downgrade; C3 does not solve that C2 issue.",
            "M4A4 hand/attachment numbers are diagnostic only: the decompiled SMD vertex domain and skeleton-global domain must not be mixed as an automated pass condition." if args.target_profile == "m4a4" else "M4A1-S attachment override remains required.",
        ],
    }
    args.manifest_output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "scale": scale, "axis_delta_degrees": expected_axis_delta_degrees, "metrics": metrics}, indent=2))
    return 0 if core_gate_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
