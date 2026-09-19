"""Blender-side A2: unlit emission render of weapon meshes with raw diffuse.

Invoked through blender_mcp_exec.py execute_code:

  python scripts/cf_ltb/blender_mcp_exec.py execute_code \
      --code-file work/cop357_snowfox/material_v2/a2_blender_emission.py \
      --timeout 300

Workbench TEXTURE color mode renders the diffuse atlas unlit — the offline
equivalent of Emission(diffuse) for the mesh/UV compatibility gate.
"""
from __future__ import annotations

import json
import os

import bpy
from mathutils import Vector

PROJECT = r"D:\project\cf_to_csgo"
WORK = os.path.join(PROJECT, "work", "cop357_snowfox")
SKIN = os.path.join(WORK, "decode", "cf_skin_cop357_dominator.json")
DIFFUSE = os.path.join(WORK, "decode", "PV-Cop357_Dominator_Classic.png")
OUT_DIR = os.path.join(WORK, "material_v2", "audit")
BLEND_PATH = os.path.join(OUT_DIR, "a2_emission_scene.blend")
REPORT_PATH = os.path.join(OUT_DIR, "a2_blender_report.json")

os.makedirs(OUT_DIR, exist_ok=True)
skin = json.loads(open(SKIN, encoding="utf-8").read())
meshes = [m for m in skin["meshes"]
          if not m["name"].lower().startswith(("fview", "fview-"))]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

scene = bpy.context.scene
scene.unit_settings.system = "NONE"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0

img = bpy.data.images.load(DIFFUSE)
mat = bpy.data.materials.new("cf_diffuse_emission_check")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()
out_node = nodes.new("ShaderNodeOutputMaterial")
em = nodes.new("ShaderNodeEmission")
tex = nodes.new("ShaderNodeTexImage")
tex.image = img
mat.node_tree.links.new(tex.outputs["Color"], em.inputs["Color"])
mat.node_tree.links.new(em.outputs["Emission"], out_node.inputs["Surface"])

lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
built = []
for m in meshes:
    verts = [tuple(m["vertices"][i:i + 3]) for i in range(0, len(m["vertices"]), 3)]
    tris = [tuple(m["triangles"][i:i + 3]) for i in range(0, len(m["triangles"]), 3)]
    uvs = m["uvs"]
    me = bpy.data.meshes.new(m["name"])
    me.from_pydata(verts, [], tris)
    me.update()
    uv_layer = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv_layer.data[li].uv = (uvs[2 * vi], 1.0 - uvs[2 * vi + 1])
    me.materials.append(mat)
    obj = bpy.data.objects.new(m["name"], me)
    scene.collection.objects.link(obj)
    built.append({"name": m["name"], "verts": len(verts), "tris": len(tris)})
    for v in verts:
        lo = Vector(map(min, lo, v))
        hi = Vector(map(max, hi, v))

center = (lo + hi) / 2.0
diag = max((hi - lo).length, 1.0)
dist = diag * 1.4

cam_data = bpy.data.cameras.new("A2Cam")
cam = bpy.data.objects.new("A2Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.clip_start = 0.01
cam_data.clip_end = dist * 10


def point(cam_obj, direction):
    cam_obj.location = center + Vector(direction) * dist
    look = center - cam_obj.location
    cam_obj.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()


views = {
    "emission_front.png": (0, -1, 0.35),
    "emission_back.png": (0, 1, 0.35),
    "emission_left.png": (-1, -0.35, 0.3),
    "emission_right.png": (1, -0.35, 0.3),
}
for name, direction in views.items():
    point(cam, direction)
    scene.render.filepath = os.path.join(OUT_DIR, name)
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
json.dump({
    "engine": scene.render.engine,
    "color_mode": scene.display.shading.color_type,
    "diffuse": DIFFUSE,
    "meshes": built,
    "bbox_min": list(lo), "bbox_max": list(hi),
    "views": list(views),
    "note": "unlit texture render = offline Emission(diffuse) equivalent",
}, open(REPORT_PATH, "w", encoding="utf-8"), indent=1)
print("A2 blender done:", len(built), "meshes ->", OUT_DIR)
