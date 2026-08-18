"""Blender-side D1 scene builder for the M4A1-S BornBeast port.

Run through blender_mcp_call.py.  The script consumes the locked C3 geometry,
loads the repository copy of Blender Source Tools without installing it into the
user profile, creates the D1 collection layout, performs conservative geometry
cleanup, and writes a reproducible .blend plus a machine-readable report.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector


PROJECT = os.environ.get("CF2_PROJECT_DIR", r"D:\project\cf_to_csgo")
BST_ROOT = os.path.join(PROJECT, "tools", "bst_extracted", "BlenderSourceTools-master")
BST_PACKAGE = os.path.join(BST_ROOT, "io_scene_valvesource")
ALIGNED_OBJ = os.path.join(
    PROJECT,
    "work",
    "m4a1_s_bornbeast",
    "source_dump",
    "c3_alignment",
    "PV-M4A1_S_BornBeast_Classic_c3_aligned.obj",
)
REFERENCE_SMD = os.path.join(
    PROJECT,
    "work",
    "m4a1_s_bornbeast",
    "reference_m4a1_s",
    "decompiled",
    "v_rif_m4a1_s.smd",
)
C2_MANIFEST = os.path.join(PROJECT, "assets", "weapons", "m4a1_s_bornbeast", "c2_skeleton_manifest.json")
C3_MANIFEST = os.path.join(PROJECT, "assets", "weapons", "m4a1_s_bornbeast", "c3_alignment_manifest.json")
C3_REPORT = os.path.join(
    PROJECT, "work", "m4a1_s_bornbeast", "source_dump", "c3_alignment", "c3_alignment_report.json"
)
OUTPUT_DIR = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "d1")
BLEND_PATH = os.path.join(OUTPUT_DIR, "d1_m4a1_s_bornbeast.blend")
REPORT_PATH = os.path.join(OUTPUT_DIR, "d1_scene_report.json")
PREVIEW_PATH = os.path.join(OUTPUT_DIR, "d1_export_scene.png")

R1_BINDINGS = {
    "M4A1S_BornBeast": ("v_weapon.M4A1_s_Parent", "temporary_static_parent"),
    "M4A1S_BornBeast01": ("v_weapon.M4A1_Clip", "locked_rigid_magazine"),
    "M4A1S_BornBeast02": ("v_weapon.M4A1_Bolt", "provisional_rigid_bolt"),
    "M4A1S_BornBeast03": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
    "M4A1S_BornBeast04": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
    "M4A1S_BornBeast05": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
    "M4A1S_BornBeast06": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
    "M4A1S_BornBeast07": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
    "M4A1S_BornBeast08": ("v_weapon.M4A1_s_Parent", "acknowledged_static_downgrade"),
}

for required in (BST_PACKAGE, ALIGNED_OBJ, REFERENCE_SMD, C2_MANIFEST, C3_MANIFEST, C3_REPORT):
    if not os.path.exists(required):
        raise RuntimeError(f"D1 required input is missing: {required}")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


with open(C2_MANIFEST, "r", encoding="utf-8") as stream:
    c2 = json.load(stream)
with open(C3_MANIFEST, "r", encoding="utf-8") as stream:
    c3 = json.load(stream)
with open(C3_REPORT, "r", encoding="utf-8") as stream:
    c3_report = json.load(stream)

# Load the pinned repository copy for this session only.  Nothing is copied to
# Blender's user add-on directory and no preference is persisted.
if BST_ROOT not in sys.path:
    sys.path.insert(0, BST_ROOT)
import io_scene_valvesource

if not hasattr(bpy.ops.import_scene, "smd"):
    io_scene_valvesource.register()

# Rebuild from an empty scene so running the script twice is idempotent.
bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
# Object deletion does not remove orphan mesh/material/armature datablocks.
# Purging them is required for stable names across repeated D1 builds.
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

scene = bpy.context.scene
scene.unit_settings.system = "NONE"
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"


def make_collection(name):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


collections = {name: make_collection(name) for name in ("REFERENCE", "CF_WEAPON", "CSGO_ARMS", "EXPORT", "GUIDES")}


def move_to_collection(obj, target):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    target.objects.link(obj)


# Import the official SMD through the pinned Source Tools importer.  It provides
# the exact official armature; the stock weapon mesh is retained as hidden
# reference rather than becoming export geometry.
before = set(bpy.data.objects)
result = bpy.ops.import_scene.smd(
    filepath=REFERENCE_SMD,
    append="NEW_ARMATURE",
    upAxis="Z",
    rotMode="XYZ",
    createCollections=False,
    doAnim=False,
)
if "FINISHED" not in result:
    raise RuntimeError(f"Blender Source Tools failed to import official SMD: {result}")
reference_import = [obj for obj in bpy.data.objects if obj not in before]
armatures = [obj for obj in reference_import if obj.type == "ARMATURE"]
reference_meshes = [obj for obj in reference_import if obj.type == "MESH"]
if len(armatures) != 1:
    raise RuntimeError(f"D1 expected one official armature, got {len(armatures)}")
armature = armatures[0]
armature.name = "CSGO_M4A1S_Canonical_Armature"
armature.data.name = "CSGO_M4A1S_Canonical_ArmatureData"
armature.show_in_front = True
armature.display_type = "WIRE"
armature["cf2_role"] = "official_canonical_skeleton"
move_to_collection(armature, collections["CSGO_ARMS"])
for index, obj in enumerate(reference_meshes):
    obj.name = f"REFERENCE_M4A1S_{index:02d}"
    obj.hide_viewport = True
    obj.hide_render = True
    obj["cf2_role"] = "official_reference_mesh"
    move_to_collection(obj, collections["REFERENCE"])

# The official armature must match the C2 manifest exactly before the scene is
# allowed to become the D1 source of truth.
armature_bones = {bone.name: bone.parent.name if bone.parent else None for bone in armature.data.bones}
manifest_bones = {bone["name"]: bone.get("parent") for bone in c2["hierarchy"]}
skeleton_exact_match = armature_bones == manifest_bones and len(armature_bones) == 58


def import_obj(path):
    before_objects = set(bpy.data.objects)
    try:
        bpy.ops.wm.obj_import(
            filepath=path,
            use_split_objects=True,
            use_split_groups=True,
            forward_axis="Y",
            up_axis="Z",
        )
    except Exception:
        bpy.ops.import_scene.obj(
            filepath=path,
            use_split_objects=True,
            use_split_groups=True,
            axis_forward="Y",
            axis_up="Z",
        )
    return [obj for obj in bpy.data.objects if obj not in before_objects and obj.type == "MESH"]


cf_objects = import_obj(ALIGNED_OBJ)
if len(cf_objects) != 9 or any("Fview-" in obj.name for obj in cf_objects):
    raise RuntimeError(f"D1 requires exactly nine weapon meshes and no CF arms; got {[obj.name for obj in cf_objects]}")


def uv_area(face, uv_layer):
    if len(face.loops) != 3:
        return 0.0
    a, b, c = (loop[uv_layer].uv for loop in face.loops)
    return abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) * 0.5


def mesh_statistics(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.active
    zero_geometry = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    zero_uv = sum(1 for face in bm.faces if uv_layer is not None and uv_area(face, uv_layer) <= 1e-12)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    nonmanifold_complex = sum(1 for edge in bm.edges if not edge.is_manifold and not edge.is_boundary)
    wire = sum(1 for edge in bm.edges if edge.is_wire)
    loose_vertices = sum(1 for vertex in bm.verts if not vertex.link_faces and not vertex.link_edges)
    bm.free()
    normal_lengths = [loop.normal.length for loop in mesh.loops]
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "loops": len(mesh.loops),
        "materials": len(mesh.materials),
        "faces_without_material": sum(1 for face in mesh.polygons if face.material_index >= len(mesh.materials)),
        "zero_area_geometry_faces": zero_geometry,
        "zero_area_uv_faces": zero_uv,
        "boundary_edges": boundary,
        "complex_nonmanifold_edges": nonmanifold_complex,
        "wire_edges": wire,
        "loose_vertices": loose_vertices,
        "zero_length_loop_normals": sum(1 for length in normal_lengths if length <= 1e-8),
        "normal_length_min": min(normal_lengths) if normal_lengths else 0.0,
        "normal_length_max": max(normal_lengths) if normal_lengths else 0.0,
    }


cleanup_records = []
for obj in sorted(cf_objects, key=lambda item: item.name):
    obj.name = obj.name.removeprefix("PV-M4A1_S_BornBeast_Classic_")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)
    before_stats = mesh_statistics(obj)

    mesh = obj.data
    source_loop_normals = [loop.normal.copy() for loop in mesh.loops]
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.active
    old_vertices = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-8)
    removed_duplicate_vertices = old_vertices - len(bm.verts)
    # A zero-area UV on a geometrically valid face is a material/unwrap issue,
    # not permission to delete weapon geometry.  Preserve it for targeted D2
    # review and only remove truly degenerate geometry here.
    bad_faces = [face for face in bm.faces if face.calc_area() <= 1e-12]
    removed_faces = len(bad_faces)
    if bad_faces:
        bmesh.ops.delete(bm, geom=bad_faces, context="FACES")
    bm.normal_update()
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = not (len(edge.link_faces) == 2 and edge.calc_face_angle(0.0) >= math.radians(45.0))
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False, clean_customdata=False)
    mesh.update(calc_edges=True)
    # If cleanup did not change topology, retain the decoded LTB loop normals
    # exactly.  Otherwise Blender's rebuilt normals are used and reported.
    normals_restored = False
    if len(source_loop_normals) == len(mesh.loops):
        try:
            mesh.normals_split_custom_set(source_loop_normals)
            normals_restored = True
        except Exception:
            normals_restored = False

    obj["cf2_role"] = "cleaned_cf_weapon_source"
    obj["cf2_c3_manifest"] = os.path.relpath(C3_MANIFEST, PROJECT).replace("\\", "/")
    obj["cf2_normals"] = "decoded_ltb_restored" if normals_restored else "blender_rebuilt"
    move_to_collection(obj, collections["CF_WEAPON"])
    after_stats = mesh_statistics(obj)
    cleanup_records.append(
        {
            "mesh": obj.name,
            "before": before_stats,
            "cleanup": {
                "duplicate_vertices_merged": removed_duplicate_vertices,
                "degenerate_geometry_faces_removed": removed_faces,
                "decoded_loop_normals_restored": normals_restored,
                "hard_edge_angle_degrees": 45.0,
            },
            "after": after_stats,
        }
    )

# Keep cleaned source objects hidden and place linked-data export instances in a
# dedicated collection.  D2/D3 can bind the EXPORT objects without mutating the
# source geometry or duplicating mesh datablocks.
export_objects = []
for source in sorted(cf_objects, key=lambda item: item.name):
    source.hide_viewport = True
    source.hide_render = True
    export = source.copy()
    export.data = source.data
    export.name = "EXPORT_" + source.name
    export.hide_viewport = False
    export.hide_render = False
    export["cf2_role"] = "source1_export_candidate"
    export["cf2_source_mesh"] = source.name
    export["cf2_export_axis"] = "Z_UP_SMD"
    export["cf2_transform_applied"] = True
    bone_name, binding_status = R1_BINDINGS[source.name]
    vertex_group = export.vertex_groups.new(name=bone_name)
    vertex_group.add(list(range(len(export.data.vertices))), 1.0, "REPLACE")
    modifier = export.modifiers.new(name="CF2_Canonical_Armature", type="ARMATURE")
    modifier.object = armature
    export["cf2_rigid_bone"] = bone_name
    export["cf2_binding_status"] = binding_status
    export["cf2_binding_profile"] = "r1_static"
    collections["EXPORT"].objects.link(export)
    export_objects.append(export)

# Attachment guides are evidence only.  They are never exported as geometry.
guide_colors = {
    "flash": (0.0, 1.0, 0.1, 1.0),
    "muzzle_flash2_silenced": (1.0, 0.0, 1.0, 1.0),
    "shelleject": (1.0, 0.8, 0.0, 1.0),
}
for key, color in guide_colors.items():
    guide = bpy.data.objects.new("GUIDE_" + key, None)
    guide.empty_display_type = "SPHERE"
    guide.empty_display_size = 0.4
    guide.color = color
    guide.location = c3_report["attachments"][key]["official_position"]
    guide["cf2_role"] = "non_export_attachment_guide"
    collections["GUIDES"].objects.link(guide)

# Preview the export candidate only.  Reference geometry remains available but
# hidden; the armature is shown as wire for an immediate sanity check.
all_export_points = [obj.matrix_world @ vertex.co for obj in export_objects for vertex in obj.data.vertices]
minimum = Vector(tuple(min(point[axis] for point in all_export_points) for axis in range(3)))
maximum = Vector(tuple(max(point[axis] for point in all_export_points) for axis in range(3)))
center = (minimum + maximum) / 2
bpy.ops.object.camera_add(location=center + Vector((38, 28, 24)))
camera = bpy.context.object
camera.name = "GUIDE_D1_Camera"
camera.rotation_euler = ((center - camera.location).to_track_quat("-Z", "Y")).to_euler()
camera.data.lens = 58
move_to_collection(camera, collections["GUIDES"])
scene.camera = camera
scene.render.filepath = PREVIEW_PATH
bpy.ops.render.render(write_still=True)

for collection in collections.values():
    collection["cf2_stage"] = "D1"
collections["REFERENCE"].hide_viewport = True
collections["REFERENCE"].hide_render = True
collections["CF_WEAPON"].hide_viewport = True
collections["CF_WEAPON"].hide_render = True

totals = {
    "vertices": sum(record["after"]["vertices"] for record in cleanup_records),
    "faces": sum(record["after"]["faces"] for record in cleanup_records),
    "zero_area_geometry_faces": sum(record["after"]["zero_area_geometry_faces"] for record in cleanup_records),
    "zero_area_uv_faces": sum(record["after"]["zero_area_uv_faces"] for record in cleanup_records),
    "zero_length_loop_normals": sum(record["after"]["zero_length_loop_normals"] for record in cleanup_records),
    "boundary_edges": sum(record["after"]["boundary_edges"] for record in cleanup_records),
    "complex_nonmanifold_edges": sum(record["after"]["complex_nonmanifold_edges"] for record in cleanup_records),
    "duplicate_vertices_merged": sum(record["cleanup"]["duplicate_vertices_merged"] for record in cleanup_records),
        "faces_removed": sum(record["cleanup"]["degenerate_geometry_faces_removed"] for record in cleanup_records),
}
identity_transforms = all(
    obj.location.length <= 1e-8
    and obj.rotation_euler.to_matrix().is_identity
    and all(abs(component - 1.0) <= 1e-8 for component in obj.scale)
    for obj in export_objects
)
hard_failures = []
if not skeleton_exact_match:
    hard_failures.append("official SMD armature does not exactly match the 58-bone C2 canonical skeleton")
if len(export_objects) != 9:
    hard_failures.append("EXPORT must contain exactly nine weapon meshes")
if any("Fview-" in obj.name for obj in export_objects):
    hard_failures.append("CF arm/hand mesh leaked into EXPORT")
if not identity_transforms:
    hard_failures.append("one or more EXPORT object transforms are not applied")
if totals["zero_area_geometry_faces"]:
    hard_failures.append("degenerate geometry remains after cleanup")
if totals["zero_length_loop_normals"]:
    hard_failures.append("zero-length loop normals remain after cleanup")
if any(record["after"]["faces_without_material"] for record in cleanup_records):
    hard_failures.append("faces without a material slot remain")

advisories = []
if totals["zero_area_uv_faces"]:
    advisories.append(
        "Geometrically valid faces with zero-area UV remain. They are preserved to avoid deleting real weapon surfaces; R1 may retain them with the explicit placeholder material, while D2 r2_full requires CF material semantics."
    )
if totals["boundary_edges"]:
    advisories.append(
        "Open boundary edges remain. They are retained because the reviewed CF source contains intentional open/mechanical shells; D2 must not silently treat them as watertight."
    )
if totals["complex_nonmanifold_edges"]:
    advisories.append("Complex non-manifold edges remain and require targeted review before D2 can pass.")
if not all(record["cleanup"]["decoded_loop_normals_restored"] for record in cleanup_records):
    advisories.append("At least one mesh required Blender-rebuilt normals because cleanup changed loop topology.")

scene["cf2_stage"] = "D1"
scene["cf2_coordinate_space"] = "Source 1 SMD model space"
scene["cf2_source_units"] = "unitless Source units, scale_length=1.0"
scene["cf2_up_axis"] = "Z"
scene["cf2_export_format"] = "SMD via Blender Source Tools 3.4.3"
scene["cf2_c3_manifest_sha256"] = sha256(C3_MANIFEST)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
report = {
    "schema": "cf2.m4a1_s.d1-scene.v1",
    "status": "PASS_WITH_UV_AND_BOUNDARY_ADVISORY" if not hard_failures else "FAIL",
    "inputs": {
        "aligned_obj": ALIGNED_OBJ,
        "aligned_obj_sha256": sha256(ALIGNED_OBJ),
        "reference_smd": REFERENCE_SMD,
        "reference_smd_sha256": sha256(REFERENCE_SMD),
        "c2_manifest": C2_MANIFEST,
        "c2_manifest_sha256": sha256(C2_MANIFEST),
        "c3_manifest": C3_MANIFEST,
        "c3_manifest_sha256": sha256(C3_MANIFEST),
    },
    "tools": {
        "blender": bpy.app.version_string,
        "blender_source_tools": ".".join(str(value) for value in io_scene_valvesource.bl_info["version"]),
        "blender_source_tools_source": BST_PACKAGE,
        "installation": "session-only import from repository; user add-on directory is not modified",
    },
    "scene_configuration": {
        "unit_system": scene.unit_settings.system,
        "scale_length": scene.unit_settings.scale_length,
        "up_axis": "Z",
        "source_coordinate_input": "C3-aligned Source 1 SMD model space",
        "obj_import_axes": {"forward": "Y", "up": "Z"},
        "smd_import_up_axis": "Z",
        "export_axis_contract": "Z_UP_SMD",
        "object_transforms_applied": identity_transforms,
    },
    "collections": {name: sorted(obj.name for obj in collection.objects) for name, collection in collections.items()},
    "canonical_skeleton": {
        "bone_count": len(armature_bones),
        "exact_name_parent_match": skeleton_exact_match,
        "armature": armature.name,
    },
    "r1_rigid_bindings": {
        obj["cf2_source_mesh"]: {
            "bone": obj["cf2_rigid_bone"],
            "status": obj["cf2_binding_status"],
            "vertex_count": len(obj.data.vertices),
            "weight": 1.0,
            "armature_modifier": armature.name,
        }
        for obj in export_objects
    },
    "geometry": {"meshes": cleanup_records, "totals": totals},
    "normal_policy": {
        "source": "decoded LTB loop normals from C3 OBJ",
        "cleanup": "restore exact loop normals when topology is unchanged; otherwise rebuild in Blender",
        "hard_edges": "45-degree dihedral threshold",
        "weighted_normal_modifier": "not applied; valid decoded LTB normals take precedence",
    },
    "outputs": {
        "blend": BLEND_PATH,
        "blend_sha256": sha256(BLEND_PATH),
        "preview": PREVIEW_PATH,
        "preview_sha256": sha256(PREVIEW_PATH),
    },
    "hard_failures": hard_failures,
    "advisories": advisories,
    "next_gate": "D2 must validate materials, rigid weights, movable-part bindings and Source export compatibility.",
}
with open(REPORT_PATH, "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps({"status": report["status"], "report": REPORT_PATH, "blend": BLEND_PATH, "totals": totals}, ensure_ascii=False))
if hard_failures:
    raise RuntimeError("D1 hard gate failed: " + "; ".join(hard_failures))
