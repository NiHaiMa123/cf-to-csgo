"""Blender-side D2 export preflight; reads the current D1 scene without mutating it."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re

import bmesh
import bpy
from mathutils import Vector


PROJECT = os.environ.get("CF2_PROJECT_DIR", r"D:\project\cf_to_csgo")
ASSET_DIR = os.path.join(PROJECT, "assets", "weapons", "m4a1_s_bornbeast")
MESH_MAP = os.path.join(ASSET_DIR, "mesh_map.yaml")
MATERIAL_MAP = os.path.join(ASSET_DIR, "material_map.json")
C2_MANIFEST = os.path.join(ASSET_DIR, "c2_skeleton_manifest.json")
C3_MANIFEST = os.path.join(ASSET_DIR, "c3_alignment_manifest.json")
D1_REPORT = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "d1", "d1_scene_report.json")
REFERENCE_REPORT = os.path.join(
    PROJECT, "work", "m4a1_s_bornbeast", "reference_m4a1_s", "reference_report.json"
)
OUTPUT_DIR = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "d2")
OUTPUT_REPORT = os.path.join(OUTPUT_DIR, "d2_preflight_report.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def parse_mesh_map(path):
    entries = {}
    current = None
    for raw in open(path, "r", encoding="utf-8"):
        if match := re.match(r"^\s{2}- mesh:\s*(.+?)\s*$", raw):
            current = {"mesh": match.group(1).strip().strip('"')}
            entries[current["mesh"]] = current
            continue
        if current is not None and (match := re.match(r"^\s{4}([A-Za-z_]+):\s*(.*?)\s*$", raw)):
            value = match.group(2).strip().strip('"')
            if value == "true":
                value = True
            elif value == "false":
                value = False
            elif value == "null":
                value = None
            current[match.group(1)] = value
    return entries


for required in (MESH_MAP, MATERIAL_MAP, C2_MANIFEST, C3_MANIFEST, D1_REPORT, REFERENCE_REPORT):
    if not os.path.isfile(required):
        raise RuntimeError(f"D2 required input missing: {required}")

mesh_map = parse_mesh_map(MESH_MAP)
material_map = load_json(MATERIAL_MAP)
c2 = load_json(C2_MANIFEST)
c3 = load_json(C3_MANIFEST)
d1 = load_json(D1_REPORT)
reference = load_json(REFERENCE_REPORT)

expected_weapon_meshes = {name for name, entry in mesh_map.items() if entry.get("export") is True}
canonical_bones = {bone["name"]: bone.get("parent") for bone in c2["hierarchy"]}
official_materials = set(reference.get("materials", {}).get("smd_materials", []))
export_collection = bpy.data.collections.get("EXPORT")
arms_collection = bpy.data.collections.get("CSGO_ARMS")
if export_collection is None or arms_collection is None:
    raise RuntimeError("D2 requires the D1 EXPORT and CSGO_ARMS collections")
export_objects = [obj for obj in export_collection.objects if obj.type == "MESH"]
armatures = [obj for obj in arms_collection.objects if obj.type == "ARMATURE"]
armature = armatures[0] if len(armatures) == 1 else None
actual_bones = (
    {bone.name: bone.parent.name if bone.parent else None for bone in armature.data.bones} if armature else {}
)

expected_r1_bones = {
    "M4A1S_BornBeast": "v_weapon.M4A1_s_Parent",
    "M4A1S_BornBeast01": "v_weapon.M4A1_Clip",
    "M4A1S_BornBeast02": "v_weapon.M4A1_Bolt",
    **{f"M4A1S_BornBeast0{index}": "v_weapon.M4A1_s_Parent" for index in range(3, 9)},
}


def uv_triangle_area(mesh, polygon):
    if not mesh.uv_layers.active or len(polygon.loop_indices) != 3:
        return 0.0
    data = mesh.uv_layers.active.data
    a, b, c = (data[index].uv for index in polygon.loop_indices)
    return abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) * 0.5


mesh_records = []
all_material_slots = set()
for obj in sorted(export_objects, key=lambda item: item.get("cf2_source_mesh", item.name)):
    source_mesh = obj.get("cf2_source_mesh")
    mesh = obj.data
    material_slots = [material.name if material else None for material in mesh.materials]
    all_material_slots.update(name for name in material_slots if name)
    zero_uv_faces = []
    flipped_faces = []
    normal_keys = {}
    zero_normals = 0
    nonfinite_normals = 0
    for loop in mesh.loops:
        normal = loop.normal
        length = normal.length
        if length <= 1e-8:
            zero_normals += 1
            continue
        if not all(math.isfinite(value) for value in normal):
            nonfinite_normals += 1
            continue
        key = tuple(round(value / length, 3) for value in normal)
        normal_keys[key] = normal_keys.get(key, 0) + 1
    for polygon in mesh.polygons:
        uv_area = uv_triangle_area(mesh, polygon)
        if uv_area <= 1e-12:
            center = obj.matrix_world @ polygon.center
            zero_uv_faces.append(
                {
                    "polygon": polygon.index,
                    "center": [round(value, 6) for value in center],
                    "geometry_area": round(polygon.area, 10),
                }
            )
        if polygon.loop_indices:
            average = Vector((0.0, 0.0, 0.0))
            for loop_index in polygon.loop_indices:
                average += mesh.loops[loop_index].normal
            if average.length and polygon.normal.dot(average.normalized()) < -1e-5:
                flipped_faces.append(polygon.index)

    group_names = {group.index: group.name for group in obj.vertex_groups}
    invalid_bone_vertices = []
    invalid_weight_vertices = []
    influence_overflow_vertices = []
    actual_bone_usage = {}
    for vertex in mesh.vertices:
        influences = [
            (group_names.get(assignment.group), assignment.weight)
            for assignment in vertex.groups
            if assignment.weight > 1e-8
        ]
        if len(influences) > 3:
            influence_overflow_vertices.append(vertex.index)
        if abs(sum(weight for _, weight in influences) - 1.0) > 1e-5:
            invalid_weight_vertices.append(vertex.index)
        for bone_name, weight in influences:
            actual_bone_usage[bone_name] = actual_bone_usage.get(bone_name, 0) + 1
            if bone_name not in canonical_bones or not math.isfinite(weight) or weight < 0.0:
                invalid_bone_vertices.append(vertex.index)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    degenerate_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    boundary_edges = sum(1 for edge in bm.edges if edge.is_boundary)
    complex_nonmanifold = sum(1 for edge in bm.edges if not edge.is_manifold and not edge.is_boundary)
    bm.free()

    armature_modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
    mapped_targets = {
        material_map.get("slots", {}).get(name) for name in material_slots if name is not None
    }
    mapped_targets.discard(None)
    mesh_records.append(
        {
            "object": obj.name,
            "source_mesh": source_mesh,
            "controlled_by_mesh_map": source_mesh in expected_weapon_meshes,
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.polygons),
            "material_slots": material_slots,
            "faces_without_material": sum(
                1 for polygon in mesh.polygons if polygon.material_index >= len(mesh.materials) or not mesh.materials[polygon.material_index]
            ),
            "mapped_source_materials": sorted(mapped_targets),
            "all_material_slots_mapped": all(
                name is not None and name in material_map.get("slots", {}) for name in material_slots
            ),
            "mapped_targets_exist_in_official_reference": all(target in official_materials for target in mapped_targets),
            "normal": {
                "zero_length": zero_normals,
                "nonfinite": nonfinite_normals,
                "distinct_rounded_directions": len(normal_keys),
                "largest_direction_fraction": max(normal_keys.values(), default=0) / max(len(mesh.loops), 1),
                "flipped_against_face_normal": len(flipped_faces),
            },
            "uv": {"zero_area_faces": zero_uv_faces},
            "topology": {
                "degenerate_faces": degenerate_faces,
                "boundary_edges": boundary_edges,
                "complex_nonmanifold_edges": complex_nonmanifold,
            },
            "weights": {
                "vertex_groups": sorted(group_names.values()),
                "bone_usage": actual_bone_usage,
                "invalid_weight_sum_vertices": invalid_weight_vertices,
                "invalid_bone_vertices": sorted(set(invalid_bone_vertices)),
                "influence_overflow_vertices": influence_overflow_vertices,
                "expected_r1_bone": expected_r1_bones.get(source_mesh),
                "rigid_r1_match": set(actual_bone_usage) == {expected_r1_bones.get(source_mesh)}
                and actual_bone_usage.get(expected_r1_bones.get(source_mesh)) == len(mesh.vertices),
            },
            "armature": {
                "modifier_count": len(armature_modifiers),
                "targets_canonical_armature": len(armature_modifiers) == 1
                and armature is not None
                and armature_modifiers[0].object == armature,
            },
            "object_transform_identity": obj.location.length <= 1e-8
            and obj.rotation_euler.to_matrix().is_identity
            and all(abs(value - 1.0) <= 1e-8 for value in obj.scale),
            "binding_status": obj.get("cf2_binding_status"),
        }
    )

global_checks = {
    "mesh_set_exact": {record["source_mesh"] for record in mesh_records} == expected_weapon_meshes,
    "no_cf_arms_in_export": all("Fview-" not in (record["source_mesh"] or "") for record in mesh_records),
    "all_groups_controlled": all(record["controlled_by_mesh_map"] for record in mesh_records),
    "all_faces_material_assigned": all(record["faces_without_material"] == 0 for record in mesh_records),
    "all_material_slots_mapped": all(record["all_material_slots_mapped"] for record in mesh_records),
    "all_mapped_targets_exist": all(record["mapped_targets_exist_in_official_reference"] for record in mesh_records),
    "normals_valid_and_nondefault": all(
        record["normal"]["zero_length"] == 0
        and record["normal"]["nonfinite"] == 0
        and record["normal"]["distinct_rounded_directions"] > 4
        and record["normal"]["largest_direction_fraction"] < 0.75
        and record["normal"]["flipped_against_face_normal"] == 0
        for record in mesh_records
    ),
    "weights_normalized_valid_and_within_limit": all(
        not record["weights"]["invalid_weight_sum_vertices"]
        and not record["weights"]["invalid_bone_vertices"]
        and not record["weights"]["influence_overflow_vertices"]
        for record in mesh_records
    ),
    "r1_rigid_bindings_match": all(record["weights"]["rigid_r1_match"] for record in mesh_records),
    "armature_modifiers_valid": all(record["armature"]["targets_canonical_armature"] for record in mesh_records),
    "canonical_skeleton_exact": armature is not None and actual_bones == canonical_bones and len(actual_bones) == 58,
    "object_transforms_identity": all(record["object_transform_identity"] for record in mesh_records),
    "no_degenerate_or_complex_nonmanifold": all(
        record["topology"]["degenerate_faces"] == 0
        and record["topology"]["complex_nonmanifold_edges"] == 0
        for record in mesh_records
    ),
    "zero_area_uv_count": sum(len(record["uv"]["zero_area_faces"]) for record in mesh_records),
    "boundary_edge_count": sum(record["topology"]["boundary_edges"] for record in mesh_records),
    "c3_locked": c3.get("status") == "locked_for_D_with_attachment_override",
    "muzzle_override_recorded": abs(c3.get("attachment_policy", {}).get("recommended_local_x_offset", 0.0) - 1.613005) <= 1e-6,
}
zero_uv_faces = [
    {"mesh": record["source_mesh"], **face}
    for record in mesh_records
    for face in record["uv"]["zero_area_faces"]
]
zero_uv_clusters = {}
for face in zero_uv_faces:
    key = f"{face['mesh']}@Y={round(face['center'][1], 0):.0f}"
    zero_uv_clusters[key] = zero_uv_clusters.get(key, 0) + 1
zero_uv_assessment = {
    "face_count": len(zero_uv_faces),
    "clusters_by_long_axis": zero_uv_clusters,
    "classification": "two_eight_triangle_collapsed_uv_caps" if sorted(zero_uv_clusters.values()) == [8, 8] else "unclassified",
    "geometry_degenerate": False,
    "r1_policy": "allowed only with the explicit official reference placeholder material",
    "r2_policy": "material-dependent; verify the intended CF texel before preserving or re-unwrapping",
}

base_boolean_checks = [
    "mesh_set_exact",
    "no_cf_arms_in_export",
    "all_groups_controlled",
    "all_faces_material_assigned",
    "all_material_slots_mapped",
    "all_mapped_targets_exist",
    "normals_valid_and_nondefault",
    "weights_normalized_valid_and_within_limit",
    "r1_rigid_bindings_match",
    "armature_modifiers_valid",
    "canonical_skeleton_exact",
    "object_transforms_identity",
    "no_degenerate_or_complex_nonmanifold",
    "c3_locked",
    "muzzle_override_recorded",
]
r1_failures = [name for name in base_boolean_checks if global_checks.get(name) is not True]
r1_advisories = []
if global_checks["zero_area_uv_count"]:
    r1_advisories.append(
        f"{global_checks['zero_area_uv_count']} zero-area UV faces are allowed only for the official-material visibility compile; no CF material claim is permitted."
    )
if global_checks["boundary_edge_count"]:
    r1_advisories.append(
        f"{global_checks['boundary_edge_count']} open boundary edges are preserved; complex non-manifold edges are zero."
    )
r1_advisories.extend(
    [
        "Main -> Parent keeps the baked muzzle/silencer static and is not R2-correct.",
        "M4A1S_BornBeast03-08 -> Parent is an acknowledged static downgrade.",
        "rif_m4a1_s is an official reference placeholder, not the translated CF material.",
    ]
)

r2_failures = list(r1_failures)
if global_checks["zero_area_uv_count"]:
    r2_failures.append("collapsed_uv_caps_require_cf_material_semantics")
if material_map.get("status") != "final_cf_source1_materials":
    r2_failures.append("final_cf_material_map_missing")
r2_failures.extend(
    [
        "main_baked_silencer_not_split_from_parent",
        "bolt_binding_still_provisional",
        "components_03_08_use_parent_fallback",
    ]
)

report = {
    "schema": "cf2.m4a1_s.d2-preflight.v1",
    "scene": bpy.data.filepath,
    "scene_sha256": sha256(bpy.data.filepath),
    "inputs": {
        "mesh_map": {"path": MESH_MAP, "sha256": sha256(MESH_MAP)},
        "material_map": {"path": MATERIAL_MAP, "sha256": sha256(MATERIAL_MAP)},
        "c2_manifest": {"path": C2_MANIFEST, "sha256": sha256(C2_MANIFEST)},
        "c3_manifest": {"path": C3_MANIFEST, "sha256": sha256(C3_MANIFEST)},
        "d1_report": {"path": D1_REPORT, "sha256": sha256(D1_REPORT)},
        "reference_report": {"path": REFERENCE_REPORT, "sha256": sha256(REFERENCE_REPORT)},
    },
    "global_checks": global_checks,
    "zero_uv_assessment": zero_uv_assessment,
    "meshes": mesh_records,
    "profiles": {
        "r1_static": {
            "passed": not r1_failures,
            "result": "PASS_WITH_EXPLICIT_DOWNGRADES" if not r1_failures else "FAIL",
            "failures": r1_failures,
            "advisories": r1_advisories,
        },
        "r2_full": {
            "passed": not r2_failures,
            "result": "PASS" if not r2_failures else "NO_GO",
            "failures": sorted(set(r2_failures)),
            "advisories": [
                "CF animation decoding is not an R2 blocker because R2 uses official M4A1-S animations."
            ],
        },
    },
}
with open(OUTPUT_REPORT, "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(
    json.dumps(
        {
            "report": OUTPUT_REPORT,
            "r1": report["profiles"]["r1_static"]["result"],
            "r2": report["profiles"]["r2_full"]["result"],
            "zero_area_uv_faces": global_checks["zero_area_uv_count"],
            "boundary_edges": global_checks["boundary_edge_count"],
        },
        ensure_ascii=False,
    )
)
