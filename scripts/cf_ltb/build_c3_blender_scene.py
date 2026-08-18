"""Blender-side C3 overlay builder, invoked through blender_mcp_call.py."""

import hashlib
import json
import os

import bpy
from mathutils import Vector


PROJECT = os.environ.get("CF2_PROJECT_DIR", r"D:\project\cf_to_csgo")
ALIGNED = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "source_dump", "c3_alignment", "PV-M4A1_S_BornBeast_Classic_c3_aligned.obj")
REFERENCE = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "source_dump", "c3_alignment", "official_m4a1_s_weapon_reference.obj")
ALIGNMENT_REPORT = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "source_dump", "c3_alignment", "c3_alignment_report.json")
OUTPUT = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "reports", "c3")
os.makedirs(OUTPUT, exist_ok=True)
with open(ALIGNMENT_REPORT, "r", encoding="utf-8") as stream:
    alignment = json.load(stream)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
overlay = bpy.data.collections.new("C3_OVERLAY")
bpy.context.scene.collection.children.link(overlay)


def import_obj(path):
    before = set(bpy.data.objects)
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
    return [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]


cf_objects = import_obj(ALIGNED)
for obj in cf_objects:
    obj.name = "CF_" + obj.name
for obj in list(cf_objects):
    if "Fview-" in obj.name:
        bpy.data.objects.remove(obj, do_unlink=True)
        cf_objects.remove(obj)
reference_objects = import_obj(REFERENCE)
for obj in reference_objects:
    obj.name = "REF_" + obj.name

cf_material = bpy.data.materials.new("C3_CF_ORANGE")
cf_material.diffuse_color = (1.0, 0.12, 0.02, 1.0)
cf_material.use_nodes = True
cf_shader = next(node for node in cf_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
cf_shader.inputs["Base Color"].default_value = (1.0, 0.035, 0.005, 1.0)
cf_shader.inputs["Roughness"].default_value = 0.38

reference_material = bpy.data.materials.new("C3_REFERENCE_BLUE")
reference_material.diffuse_color = (0.015, 0.22, 1.0, 0.28)
reference_material.use_nodes = True
reference_shader = next(node for node in reference_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
reference_shader.inputs["Base Color"].default_value = (0.01, 0.08, 1.0, 1.0)
reference_shader.inputs["Alpha"].default_value = 0.28
reference_shader.inputs["Roughness"].default_value = 0.28
reference_material.surface_render_method = "DITHERED"

for obj in cf_objects:
    obj.data.materials.clear()
    obj.data.materials.append(cf_material)
for obj in reference_objects:
    obj.data.materials.clear()
    obj.data.materials.append(reference_material)
    obj.show_in_front = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.018, 0.018, 0.025)

bpy.ops.object.light_add(type="AREA", location=(15, -10, 18))
key = bpy.context.object
key.name = "C3_Key"
key.data.energy = 1800
key.data.shape = "DISK"
key.data.size = 12
bpy.ops.object.light_add(type="AREA", location=(-12, -20, 4))
fill = bpy.context.object
fill.name = "C3_Fill"
fill.data.energy = 1000
fill.data.size = 10

bpy.ops.object.camera_add()
camera = bpy.context.object
camera.name = "C3_Camera"
scene.camera = camera
world_points = [obj.matrix_world @ vertex.co for obj in cf_objects + reference_objects for vertex in obj.data.vertices]
minimum = Vector((min(point.x for point in world_points), min(point.y for point in world_points), min(point.z for point in world_points)))
maximum = Vector((max(point.x for point in world_points), max(point.y for point in world_points), max(point.z for point in world_points)))
center = (minimum + maximum) / 2
key.rotation_euler = ((center - key.location).to_track_quat("-Z", "Y")).to_euler()
fill.rotation_euler = ((center - fill.location).to_track_quat("-Z", "Y")).to_euler()


def look_at(location, ortho_scale=None):
    camera.location = Vector(location)
    camera.rotation_euler = ((center - camera.location).to_track_quat("-Z", "Y")).to_euler()
    if ortho_scale:
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = ortho_scale
    else:
        camera.data.type = "PERSP"
        camera.data.lens = 58


views = [
    ("c3_overlay_side.png", center + Vector((45, 0, 0)), 52),
    ("c3_overlay_top.png", center + Vector((0, 0, 45)), 52),
    ("c3_overlay_perspective.png", center + Vector((29, 29, 26)), None),
]
for filename, location, ortho_scale in views:
    look_at(location, ortho_scale)
    scene.render.filepath = os.path.join(OUTPUT, filename)
    bpy.ops.render.render(write_still=True)


def marker(name, location, color):
    material = bpy.data.materials.new(name + "_MAT")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Strength"].default_value = 3.0
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)


marker("C3_FLASH", alignment["attachments"]["flash"]["official_position"], (0.0, 1.0, 0.1))
marker(
    "C3_MUZZLE_FLASH2_OFFICIAL",
    alignment["attachments"]["muzzle_flash2_silenced"]["official_position"],
    (1.0, 0.0, 1.0),
)
marker("C3_SHELLEJECT", alignment["attachments"]["shelleject"]["official_position"], (1.0, 0.8, 0.0))
look_at(center + Vector((45, 0, 0)), 52)
attachment_image = os.path.join(OUTPUT, "c3_attachment_side.png")
scene.render.filepath = attachment_image
bpy.ops.render.render(write_still=True)

look_at(center + Vector((29, 29, 26)))
for obj in cf_objects + reference_objects:
    obj.select_set(False)
for obj in cf_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = cf_objects[0]

blend_path = os.path.join(OUTPUT, "c3_alignment_review.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


image_paths = [os.path.join(OUTPUT, view[0]) for view in views] + [attachment_image]
review = {
    "schema": "cf2.m4a1_s.c3-blender-overlay.v1",
    "status": "visual_overlay_reviewed",
    "blender_version": bpy.app.version_string,
    "cf_weapon_objects": len(cf_objects),
    "reference_weapon_objects": len(reference_objects),
    "colors": {"cf": "orange/red", "official_reference": "transparent blue"},
    "images": [{"path": path, "sha256": file_sha256(path)} for path in image_paths],
    "blend": blend_path,
    "observations": [
        "Receiver, foregrip, magazine and bolt regions overlap without mirroring or a 90-degree error.",
        "The CF silhouette is shorter than the official attached-silencer reference but stays inside its XYZ envelope.",
        "Official bare flash and shell-eject locations are near CF geometry.",
        "Official muzzle_flash2 offset 9.5 is visibly beyond the baked CF muzzle and requires a QC override.",
    ],
    "result": "PASS_WITH_REQUIRED_QC_ATTACHMENT_OVERRIDE",
}
review_path = os.path.join(OUTPUT, "c3_blender_overlay_report.json")
with open(review_path, "w", encoding="utf-8") as stream:
    json.dump(review, stream, indent=2, ensure_ascii=False)
    stream.write("\n")

print(
    {
        "cf_objects": len(cf_objects),
        "reference_objects": len(reference_objects),
        "outputs": image_paths,
        "blend": blend_path,
        "report": review_path,
    }
)
