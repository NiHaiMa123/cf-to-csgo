"""Blender-side N05-G preview: verified PV LTB + recovered native maps.

Invoked through blender_mcp_exec.py execute_code. Diagnostic only:
final_cf_material=false, not a P4-M01 PASS, not a Source formula proof.

Repro:
  python scripts/cf_ltb/blender_mcp_exec.py execute_code --code-file scripts/cf_ltb/build_n05g_blender_native_preview.py
"""
from __future__ import annotations

import json
import os
from math import radians

import bpy
from mathutils import Vector


PROJECT = r"D:\project\cf_to_csgo"
OBJ = os.path.join(PROJECT, "data", "n05d_binding", "obj_export", "PV-M4A1_S_BornBeast.obj")
PNG_DIR = os.path.join(
    PROJECT,
    "work",
    "m4a1_s_bornbeast",
    "p4_m01_native_material",
    "runtime_acquisition",
    "n05f_source1_native_map",
    "_png",
)
OUT_DIR = os.path.join(
    PROJECT,
    "work",
    "m4a1_s_bornbeast",
    "p4_m01_native_material",
    "runtime_acquisition",
    "n05g_blender_native_preview",
)
BLEND_PATH = os.path.join(OUT_DIR, "n05g_bornbeast_native_preview.blend")
PREVIEW_PATH = os.path.join(OUT_DIR, "n05g_viewport.png")
PREVIEW_GUN_PATH = os.path.join(OUT_DIR, "n05g_viewport_gun.png")
REPORT_PATH = os.path.join(OUT_DIR, "n05g_blender_report.json")
MAPS = {
    "diffuse": os.path.join(PNG_DIR, "diffuse.png"),
    "normal": os.path.join(PNG_DIR, "normal.png"),
    "specular": os.path.join(PNG_DIR, "specular.png"),
    "alpha": os.path.join(PNG_DIR, "alpha.png"),
}

os.makedirs(OUT_DIR, exist_ok=True)
for required in [OBJ, *MAPS.values()]:
    if not os.path.exists(required):
        raise RuntimeError(f"missing input: {required}")

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

scene = bpy.context.scene
scene.unit_settings.system = "NONE"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = PREVIEW_PATH
scene.render.film_transparent = False
if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 32
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 1.35
scene.view_settings.gamma = 1.0

world = bpy.data.worlds.new("N05G_Studio")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.18, 0.19, 0.21, 1.0)
bg.inputs["Strength"].default_value = 2.4
wo = wn.new("ShaderNodeOutputWorld")
wl.new(bg.outputs["Background"], wo.inputs["Surface"])

root_col = bpy.data.collections.new("N05G_BORNBEAST_NATIVE")
scene.collection.children.link(root_col)
lights = bpy.data.collections.new("N05G_LIGHTS")
root_col.children.link(lights)


def add_light(name, energy, loc, rot_deg, size=8.0):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = [radians(v) for v in rot_deg]
    lights.objects.link(obj)
    return obj


add_light("Key", 900, (18, -22, 14), (60, 0, 40), 8)
add_light("Fill", 350, (-16, -18, 8), (70, 0, -35), 10)
add_light("Rim", 500, (2, 18, 12), (50, 0, 180), 6)
add_light("Front", 280, (0, -24, 6), (80, 0, 0), 12)


def load_image(path, colorspace):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colorspace
    image.alpha_mode = "CHANNEL_PACKED"
    return image


diffuse = load_image(MAPS["diffuse"], "sRGB")
normal = load_image(MAPS["normal"], "Non-Color")
specular = load_image(MAPS["specular"], "Non-Color")
alpha = load_image(MAPS["alpha"], "Non-Color")

mat = bpy.data.materials.new("CF_BornBeast_NativeDiag")
mat.use_nodes = True
if hasattr(mat, "blend_method"):
    try:
        mat.blend_method = "OPAQUE"
    except TypeError:
        pass
if hasattr(mat, "surface_render_method"):
    mat.surface_render_method = "DITHERED"
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial")
out.location = (900, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.location = (520, 0)
tex_d = nodes.new("ShaderNodeTexImage")
tex_d.image = diffuse
tex_d.location = (-420, 220)
tex_n = nodes.new("ShaderNodeTexImage")
tex_n.image = normal
tex_n.location = (-420, -40)
tex_s = nodes.new("ShaderNodeTexImage")
tex_s.image = specular
tex_s.location = (-420, -280)
tex_a = nodes.new("ShaderNodeTexImage")
tex_a.image = alpha
tex_a.location = (-420, -520)
nmap = nodes.new("ShaderNodeNormalMap")
nmap.location = (40, -40)
nmap.space = "TANGENT"
sep = nodes.new("ShaderNodeSeparateColor")
sep.location = (-120, -40)
comb = nodes.new("ShaderNodeCombineColor")
comb.location = (80, -80)
invert_g = nodes.new("ShaderNodeMath")
invert_g.operation = "SUBTRACT"
invert_g.inputs[0].default_value = 1.0
invert_g.location = (-20, -180)
inv_spec = nodes.new("ShaderNodeInvert")
inv_spec.location = (-40, -280)
links.new(tex_n.outputs["Color"], sep.inputs["Color"])
links.new(sep.outputs["Red"], comb.inputs["Red"])
links.new(sep.outputs["Green"], invert_g.inputs[1])
links.new(invert_g.outputs["Value"], comb.inputs["Green"])
links.new(sep.outputs["Blue"], comb.inputs["Blue"])
links.new(comb.outputs["Color"], nmap.inputs["Color"])
links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])
links.new(tex_s.outputs["Color"], bsdf.inputs["Specular IOR Level"])
links.new(tex_s.outputs["Color"], inv_spec.inputs["Color"])
links.new(inv_spec.outputs["Color"], bsdf.inputs["Roughness"])
links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
# Alpha map is loaded but not connected: first look must not punch the mesh
# if the TGA convention is still open. Socket stays at 1.0.
bsdf.inputs["Alpha"].default_value = 1.0
bsdf.inputs["Metallic"].default_value = 0.15
if "IOR" in bsdf.inputs:
    bsdf.inputs["IOR"].default_value = 1.45

before = set(bpy.data.objects)
try:
    bpy.ops.wm.obj_import(
        filepath=OBJ,
        use_split_objects=True,
        use_split_groups=True,
        forward_axis="Y",
        up_axis="Z",
    )
except Exception:
    bpy.ops.import_scene.obj(
        filepath=OBJ,
        use_split_objects=True,
        use_split_groups=True,
        axis_forward="Y",
        axis_up="Z",
    )
imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
if not imported:
    raise RuntimeError("OBJ import produced no mesh objects")

for obj in imported:
    if obj.name not in root_col.objects:
        root_col.objects.link(obj)
        if obj.name in scene.collection.objects:
            scene.collection.objects.unlink(obj)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.display_type = "TEXTURED"
    if obj.data.uv_layers:
        obj.data.uv_layers[0].name = "UVMap"

gun = [obj for obj in imported if "Fview" not in obj.name]
hands = [obj for obj in imported if "Fview" in obj.name]


def mesh_bbox(objects):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
    return mins, maxs, (mins + maxs) * 0.5, maxs - mins


_, _, gun_center, _ = mesh_bbox(gun or imported)
root = bpy.data.objects.new("N05G_Root", None)
root.empty_display_type = "PLAIN_AXES"
root.location = gun_center
root_col.objects.link(root)
for obj in imported:
    matrix = obj.matrix_world.copy()
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()
    obj.matrix_world = matrix
# Raw PV rest pose is barrel-up. Lay it on its side for inspect.
root.rotation_euler = (radians(90), 0.0, radians(-20))
bpy.context.view_layer.update()

cam_data = bpy.data.cameras.new("N05G_Camera")
cam_data.lens = 50
cam_data.clip_start = 0.01
cam_data.clip_end = 1000
cam = bpy.data.objects.new("N05G_Camera", cam_data)
root_col.objects.link(cam)
scene.camera = cam


def frame_and_render(objects, path, hide_others):
    for obj in imported:
        hidden = hide_others and obj not in objects
        obj.hide_set(hidden)
        obj.hide_render = hidden
        obj.select_set(obj in objects)
    _, _, mid, size = mesh_bbox(objects)
    span = max(size.x, size.y, size.z, 1.0)
    cam.location = mid + Vector((span * 0.85, -span * 1.35, span * 0.42))
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.objects.active = objects[0]
    for area in bpy.context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        space = area.spaces.active
        space.shading.type = "RENDERED"
        space.shading.use_scene_lights = True
        space.shading.use_scene_world = True
        space.overlay.show_overlays = False
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        if region is None:
            continue
        with bpy.context.temp_override(
            window=bpy.context.window,
            screen=bpy.context.screen,
            area=area,
            region=region,
            scene=scene,
        ):
            bpy.ops.view3d.view_camera()
            try:
                bpy.ops.view3d.camera_to_view_selected()
            except Exception as exc:
                print("camera_to_view_selected failed:", exc)
    for obj in bpy.data.objects:
        obj.select_set(False)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return os.path.exists(path)


all_ok = frame_and_render(imported, PREVIEW_PATH, hide_others=False)
gun_ok = frame_and_render(gun, PREVIEW_GUN_PATH, hide_others=True)

for obj in imported:
    obj.hide_set(obj in hands)
    obj.hide_render = obj in hands
    obj.select_set(False)
for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "RENDERED"
    space.overlay.show_overlays = False
    region = next((item for item in area.regions if item.type == "WINDOW"), None)
    if region is None:
        continue
    with bpy.context.temp_override(
        window=bpy.context.window,
        screen=bpy.context.screen,
        area=area,
        region=region,
        scene=scene,
    ):
        bpy.ops.view3d.view_camera()

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
mins, maxs, center, _ = mesh_bbox(imported)
report = {
    "schema": "cf2.p4-m01.n05g-blender-native-preview.v1",
    "task": "P4-M01-N05-G",
    "result": "BLENDER_NATIVE_PREVIEW_SHOWN",
    "p4_m01": "INCOMPLETE",
    "final_cf_material": False,
    "blender": bpy.app.version_string,
    "obj": OBJ,
    "maps": MAPS,
    "blend": BLEND_PATH,
    "preview": PREVIEW_PATH if all_ok else None,
    "preview_gun": PREVIEW_GUN_PATH if gun_ok else None,
    "viewport_shading": "RENDERED",
    "orientation": "inspect_3q_from_raw_rest_pose",
    "exposure": scene.view_settings.exposure,
    "mesh_objects": [
        {
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "kind": "hands" if obj in hands else "weapon",
        }
        for obj in imported
    ],
    "bounds": {"min": list(mins), "max": list(maxs), "center": list(center)},
    "notes": [
        "Uses N05-D verified PV LTB OBJ (raw transform) and N05-F verified PNG maps.",
        "DirectX green-channel invert on normal is a Blender display convention, not a CF runtime proof.",
        "Specular plugged into Specular IOR Level and inverted Roughness is a diagnostic look, not CFG->Source formula.",
        "Alpha map is loaded but not connected; first look stays opaque.",
        "Hands and weapon share the verified 1024 PV atlas. Hands start hidden in the live view; they are rest-pose, not animated.",
        "Not deployed, frozen addon untouched.",
    ],
}
with open(REPORT_PATH, "w", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")

print("N05G_OK")
print("meshes", len(imported))
print("blend", BLEND_PATH)
print("preview", PREVIEW_PATH if all_ok else "MISSING")
print("preview_gun", PREVIEW_GUN_PATH if gun_ok else "MISSING")
print("report", REPORT_PATH)
