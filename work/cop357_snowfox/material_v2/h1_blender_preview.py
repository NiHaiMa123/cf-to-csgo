# Blender MCP script: Source-like preview scene for material v2 review.
# Run via: python scripts/cf_ltb/blender_mcp_exec.py execute_code --code-file <this>
import bpy
import math
import os
from mathutils import Vector

MV2 = r"D:\project\cf_to_csgo\work\cop357_snowfox\material_v2"
SV2 = os.path.join(MV2, "source_v2")
UP = os.path.join(MV2, "upscale")
PREV = os.path.join(MV2, "preview_source")
OBJ = os.path.join(PREV, "gun_slots.obj")
os.makedirs(PREV, exist_ok=True)

import json

# slot strategy -> principled params (Source approximation).
# metallic driven by env mask * envmaptint luminance from translation_report.
REPORT = json.load(open(os.path.join(SV2, "translation_report.json")))
LUM = (0.2126, 0.7152, 0.0722)
SLOT_ENV = {}
SLOT_COAT = {}
COAT_BY_STRATEGY = {"envmap_metal": 0.60, "warm_phong": 0.50,
                    "colored_phong": 0.40, "controlled_phong": 0.30,
                    "dim_phong": 0.15, "matte_dark": 0.0}
ROUGH_BY_STRATEGY = {"envmap_metal": 0.28, "warm_phong": 0.32,
                     "colored_phong": 0.35, "controlled_phong": 0.55,
                     "dim_phong": 0.68, "matte_dark": 0.7}
for s in REPORT["slots"]:
    et = s.get("envmap_tint")
    SLOT_ENV[s["material"]] = (sum(et[i] * LUM[i] for i in range(3))
                               if et else 0.0)
    SLOT_COAT[s["material"]] = COAT_BY_STRATEGY[s["strategy"]]
STRATEGY = {s["material"]: {
                "coat": SLOT_COAT[s["material"]],
                "rough": ROUGH_BY_STRATEGY[s["strategy"]],
                "metal_scale": SLOT_ENV[s["material"]]}
            for s in REPORT["slots"]}
STRATEGY["cf_cop357_winter"] = {"coat": 0.30, "rough": 0.45,
                               "metal_scale": 0.3}
PHONG_TINT = tuple(REPORT["phong_tint"]) + (1.0,)

# ---- clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- import mesh
bpy.ops.wm.obj_import(filepath=OBJ)
gun = [o for o in bpy.context.scene.objects if o.type == "MESH"]

# ---- shared images
def img(name, path, noncolor=False):
    i = bpy.data.images.get(name)
    if not i:
        i = bpy.data.images.load(path)
    if noncolor:
        i.colorspace_settings.name = "Non-Color"
    return i

DIFFUSE = os.environ.get("MV2_DIFFUSE", "diffuse_2048.png")
TAG = os.environ.get("MV2_TAG", "")
base_img = img("diffuse_" + TAG or "diffuse_x", os.path.join(UP, DIFFUSE))
nrm_img = img("normal_2048", os.path.join(UP, "normal_2048.png"), True)
phong_img = img("mask_phong", os.path.join(SV2, "mask_phong.png"), True)
env_img = img("mask_env", os.path.join(SV2, "mask_env.png"), True)

def build_mat(slot):
    p = STRATEGY.get(slot, STRATEGY["cf_cop357_winter"])
    m = bpy.data.materials.new(slot)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = p["rough"]
    if "Coat Weight" in bs.inputs:
        bs.inputs["Coat Weight"].default_value = p["coat"]
        bs.inputs["Coat Tint"].default_value = PHONG_TINT
        bs.inputs["Coat Roughness"].default_value = 0.2
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = base_img
    nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = nrm_img
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    env = nt.nodes.new("ShaderNodeTexImage")
    env.image = env_img
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = p["metal_scale"]
    nt.links.new(env.outputs["Color"], mul.inputs[0])
    nt.links.new(mul.outputs[0], bs.inputs["Metallic"])
    nt.links.new(bs.outputs[0], out.inputs[0])
    return m

mats = {s: build_mat(s) for s in STRATEGY}
for o in gun:
    for i, sl in enumerate(o.material_slots):
        name = sl.material.name if sl.material else "cf_cop357_winter"
        if name in mats:
            sl.material = mats[name]
        else:
            sl.material = mats["cf_cop357_winter"]

# ---- world: soft studio env (Source ambient+envmap proxy)
world = bpy.data.worlds.new("preview_world")
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in list(wn):
    wn.remove(n)
wout = wn.new("ShaderNodeOutputWorld")
bg = wn.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
tex = wn.new("ShaderNodeTexSky")
tex.sky_type = "HOSEK_WILKIE"
tex.sun_elevation = math.radians(35)
tex.sun_rotation = math.radians(120)
wl.new(tex.outputs["Color"], bg.inputs["Color"])
wl.new(bg.outputs[0], wout.inputs[0])
bpy.context.scene.world = world

# ---- lights: warm key + cool fill (viewmodel-like)
def add_light(name, kind, loc, energy, size=1.0, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    if kind == "AREA":
        d.shape = "DISK"
        d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return o

def track(o, pt):
    o.rotation_euler = (Vector(pt) - o.location).to_track_quat("-Z", "Y").to_euler()

# gun bounds — center on the main body piece only (remote bullet pieces
# sit far away and would drag the camera off)
import numpy as np
main_o = None
for o in gun:
    if "mauser" in o.name.lower() or "libra" in o.name.lower():
        main_o = o
        break
main_o = main_o or gun[0]
allv = [main_o.matrix_world @ Vector(v) for v in main_o.bound_box]
lo = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
hi = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
center = (lo + hi) / 2
ext = max((hi - lo).length, 1e-3)

key = add_light("key", "AREA", center + Vector((-0.5, -0.7, 0.9)) * ext, 1200, ext * 0.8, (1.0, 0.92, 0.8))
track(key, center)
fill = add_light("fill", "AREA", center + Vector((0.8, -0.2, 0.4)) * ext, 700, ext * 0.7, (0.85, 0.9, 1.0))
track(fill, center)
rim = add_light("rim", "AREA", center + Vector((0.2, 0.8, 0.5)) * ext, 1000, ext * 0.6, (1.0, 0.85, 0.7))
track(rim, center)

# ---- camera angles matching review shots
cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam_d.lens = 55

views = {
    "hero":  Vector((-0.55, -0.75, 0.42)),
    "side":  Vector((-0.95, -0.25, 0.15)),
    "back":  Vector((0.55, 0.75, 0.35)),
}
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "EEVEE_NEXT") else "BLENDER_EEVEE"
try:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 768
sc.render.resolution_y = 768
sc.render.film_transparent = False
sc.view_settings.look = "AgX - Medium High Contrast"

for name, off in views.items():
    cam.location = center + off * ext * 1.1
    track(cam, center)
    sc.render.filepath = os.path.join(PREV, f"blender{TAG}_{name}.png")
    bpy.ops.render.render(write_still=True)

print("rendered", list(views))
