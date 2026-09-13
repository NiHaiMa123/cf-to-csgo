"""Blender scene of the current P7-S04 viewmodel (broken CF retarget).

Live Blender MCP. Does not compile or deploy. In-game stays parked until
this scene is used to fix/verify.

Repro:
  python scripts/cf_ltb/blender_mcp_exec.py execute_code --code-file scripts/cf_ltb/build_p7_s04_blender_current.py --timeout 300
"""
from __future__ import annotations

import json
import os
import sys
from math import radians

import bmesh
import bpy
from mathutils import Vector

PROJECT = r"D:\project\cf_to_csgo"
BST_ROOT = os.path.join(PROJECT, "tools", "bst_extracted", "BlenderSourceTools-master")
MESH_CF = os.path.join(PROJECT, "work", "p5_leishen", "p7_s04", "source1", "cf_leishen_m4a4.smd")
MESH_GLOVE = os.path.join(
    PROJECT, "work", "m4a1_s_bornbeast", "blender_arm_reference", "decompiled",
    "glove_fullfinger", "v_glove_fullfinger.smd",
)
MESH_SLEEVE = os.path.join(
    PROJECT, "work", "m4a1_s_bornbeast", "blender_arm_reference", "decompiled",
    "sas", "v_sleeve_ct.smd",
)
ANIM_DIR = os.path.join(PROJECT, "work", "p5_leishen", "p7_s04", "smd")
LOOKAT = os.path.join(PROJECT, "work", "p5_leishen", "p7_s02", "source1", "v_rif_m4a1_anims", "lookat01.smd")
PNG_DIR = os.path.join(PROJECT, "work", "p5_leishen", "p6", "_png")
OUT_DIR = os.path.join(PROJECT, "work", "p5_leishen", "p7_s04", "blender")
BLEND_PATH = os.path.join(OUT_DIR, "p7_s04_current.blend")
PREVIEW_PATH = os.path.join(OUT_DIR, "viewport.png")
PREVIEW_FRAME_PATH = os.path.join(OUT_DIR, "viewport_reload_f81.png")
REPORT_PATH = os.path.join(OUT_DIR, "scene_report.json")

ANIMS = [
    ("cf_idle", os.path.join(ANIM_DIR, "idle.smd")),
    ("cf_shoot", os.path.join(ANIM_DIR, "shoot1.smd")),
    ("cf_draw", os.path.join(ANIM_DIR, "draw.smd")),
    ("cf_reload", os.path.join(ANIM_DIR, "reload.smd")),
    ("cs_lookat", LOOKAT),
]

for required in [BST_ROOT, MESH_CF, MESH_GLOVE, MESH_SLEEVE, PNG_DIR, *[path for _, path in ANIMS]]:
    if not os.path.exists(required):
        raise RuntimeError(f"missing: {required}")
os.makedirs(OUT_DIR, exist_ok=True)

if BST_ROOT not in sys.path:
    sys.path.insert(0, BST_ROOT)
import io_scene_valvesource

if not hasattr(bpy.ops.import_scene, "smd"):
    try:
        io_scene_valvesource.register()
    except ValueError:
        pass
if not hasattr(bpy.ops.import_scene, "smd"):
    raise RuntimeError("Blender Source Tools import_scene.smd is not available")

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
for act in list(bpy.data.actions):
    bpy.data.actions.remove(act)

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
scene.render.fps = 30
scene.frame_start = 0
scene.frame_end = 160
scene.frame_current = 0
if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 16
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 1.6
scene.view_settings.gamma = 1.0

world = bpy.data.worlds.new("P7S04_Studio")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.16, 0.17, 0.19, 1.0)
bg.inputs["Strength"].default_value = 2.2
wo = wn.new("ShaderNodeOutputWorld")
wl.new(bg.outputs["Background"], wo.inputs["Surface"])

root = bpy.data.collections.new("P7S04_CURRENT")
scene.collection.children.link(root)
col_gun = bpy.data.collections.new("CF_GUN")
col_arms = bpy.data.collections.new("CS_ARMS_BONEMERGE")
col_armature = bpy.data.collections.new("ARMATURE")
col_lights = bpy.data.collections.new("LIGHTS")
for col in (col_gun, col_arms, col_armature, col_lights):
    root.children.link(col)


def move_to(obj, target):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    target.objects.link(obj)


def add_light(name, energy, loc, rot_deg, size=8.0):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = [radians(v) for v in rot_deg]
    col_lights.objects.link(obj)
    return obj


add_light("Key", 900, (18, -22, 14), (60, 0, 40), 8)
add_light("Fill", 350, (-16, -18, 8), (70, 0, -35), 10)
add_light("Rim", 500, (2, 18, 12), (50, 0, 180), 6)
add_light("Front", 280, (0, -8, 6), (80, 0, 0), 12)


def import_smd(path, append, do_anim):
    before = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    result = bpy.ops.import_scene.smd(
        filepath=path,
        append=append,
        upAxis="Z",
        rotMode="XYZ",
        createCollections=False,
        doAnim=do_anim,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"SMD import failed {path}: {result}")
    objects = [obj for obj in bpy.data.objects if obj not in before]
    actions = [act for act in bpy.data.actions if act not in before_actions]
    return objects, actions


# 1) Current P6 CF gun + CS M4A4 armature (same 57 bones as in-game)
cf_objects, _ = import_smd(MESH_CF, "NEW_ARMATURE", False)
armatures = [obj for obj in cf_objects if obj.type == "ARMATURE"]
cf_meshes = [
    obj for obj in cf_objects
    if obj.type == "MESH" and obj.name != "smd_bone_vis" and not obj.name.startswith("smd_bone")
]
if len(armatures) != 1:
    raise RuntimeError(f"expected 1 armature, got {[o.name for o in armatures]}")
armature = armatures[0]
armature.name = "CS_M4A4_Armature"
armature.data.name = "CS_M4A4_Armature"
armature.show_in_front = True
armature.display_type = "WIRE"
move_to(armature, col_armature)
if len(cf_meshes) != 1:
    raise RuntimeError(f"expected 1 CF gun mesh, got {[o.name for o in cf_meshes]}")
cf_gun = cf_meshes[0]
cf_gun.name = "CF_GUN_P6"
cf_gun.data.name = "CF_GUN_P6"
move_to(cf_gun, col_gun)

# 2) In-game hands are bonemerge. Keep glove/sleeve on their own bind
# armature and copy-transform onto the weapon bones. VALIDATE-skinning
# them onto the weapon rest made frame 0 look like a T-pose.
arm_meshes = {}
gray = bpy.data.materials.new("CS_ARMS_GRAY")
gray.use_nodes = True
gnt = gray.node_tree
gnt.nodes.clear()
gout = gnt.nodes.new("ShaderNodeOutputMaterial")
gbsdf = gnt.nodes.new("ShaderNodeBsdfPrincipled")
gbsdf.inputs["Base Color"].default_value = (0.45, 0.42, 0.38, 1.0)
gbsdf.inputs["Roughness"].default_value = 0.65
gnt.links.new(gbsdf.outputs["BSDF"], gout.inputs["Surface"])
for label, path in (("CS_GLOVE", MESH_GLOVE), ("CS_SLEEVE", MESH_SLEEVE)):
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    imported, _ = import_smd(path, "NEW_ARMATURE", False)
    arm_objs = [obj for obj in imported if obj.type == "ARMATURE"]
    meshes = [
        obj for obj in imported
        if obj.type == "MESH" and obj.name != "smd_bone_vis" and not obj.name.startswith("smd_bone")
    ]
    if len(arm_objs) != 1 or not meshes:
        raise RuntimeError(f"{label} import failed: { [o.name for o in imported] }")
    arm_obj = arm_objs[0]
    arm_obj.name = f"{label}_Armature"
    arm_obj.hide_viewport = True
    arm_obj.hide_render = True
    move_to(arm_obj, col_arms)
    mesh_obj = meshes[0]
    mesh_obj.name = label
    mesh_obj.data.name = label
    mesh_obj.data.materials.clear()
    mesh_obj.data.materials.append(gray)
    move_to(mesh_obj, col_arms)
    for pose_bone in arm_obj.pose.bones:
        if pose_bone.name not in armature.pose.bones:
            continue
        con = pose_bone.constraints.new("COPY_TRANSFORMS")
        con.target = armature
        con.subtarget = pose_bone.name
        con.target_space = "WORLD"
        con.owner_space = "WORLD"
    arm_meshes[label] = mesh_obj

# 3) P6 texture
diff = os.path.join(PNG_DIR, "diffuse.png")
norm = os.path.join(PNG_DIR, "normal_src.png")
img_d = bpy.data.images.load(diff)
img_d.colorspace_settings.name = "sRGB"
mat = bpy.data.materials.new("rif_m4a1_p6")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img_d
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
if os.path.isfile(norm):
    img_n = bpy.data.images.load(norm)
    img_n.colorspace_settings.name = "Non-Color"
    ntex = nt.nodes.new("ShaderNodeTexImage")
    ntex.image = img_n
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(ntex.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])
cf_gun.data.materials.clear()
cf_gun.data.materials.append(mat)
vis = bpy.data.objects.get("smd_bone_vis")
if vis:
    vis.hide_viewport = True
    vis.hide_render = True

# 4) Retargeted clips + CS lookat onto the live armature
action_map = {}
for name, path in ANIMS:
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    before_actions = set(bpy.data.actions.keys())
    import_smd(path, "VALIDATE", True)
    created = [act for act in bpy.data.actions if act.name not in before_actions]
    src = None
    stem = os.path.splitext(os.path.basename(path))[0]
    if stem in bpy.data.actions:
        src = bpy.data.actions[stem]
    elif created:
        src = created[0]
    elif armature.animation_data and armature.animation_data.action:
        src = armature.animation_data.action
    if src is None:
        action_map[name] = {"error": "no action created", "source": path.replace("\\", "/")}
        continue
    if src.name != name:
        src.name = name
    n_fcurves = len(src.fcurves)
    if n_fcurves == 0 and hasattr(src, "layers"):
        try:
            n_fcurves = sum(len(bag.fcurves) for layer in src.layers for strip in layer.strips for bag in strip.channelbags)
        except Exception:
            n_fcurves = -1
    action_map[name] = {
        "action": src.name,
        "frames": int(src.frame_range[1] - src.frame_range[0]) + 1,
        "range": [float(src.frame_range[0]), float(src.frame_range[1])],
        "source": path.replace("\\", "/"),
        "fcurves": n_fcurves,
    }

if armature.animation_data is None or armature.animation_data.action is None:
    raise RuntimeError("armature has no action after clip import")
act = armature.animation_data.action
act.name = "P7S04_CURRENT"
slots = {slot.name_display: slot for slot in act.slots}
if "idle" not in slots:
    raise RuntimeError(f"idle slot missing: {list(slots)}")
armature.data.pose_position = "POSE"
armature.animation_data.action_slot = slots["idle"]
scene.frame_start = 0
scene.frame_end = 54
scene.frame_current = 0
scene.frame_set(0)

# Named Actions for the Action Editor dropdown (Blender 5 slots are easy to miss).
bake_ranges = {
    "idle": (0, 54, "1_idle_hold"),
    "shoot1": (0, 4, "2_shoot"),
    "draw": (0, 30, "3_draw"),
    "reload": (0, 107, "4_reload"),
    "lookat01": (0, 159, "5_lookat"),
}
bpy.ops.object.select_all(action="DESELECT")
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
for slot_name, (start, end, action_name) in bake_ranges.items():
    armature.animation_data.action = act
    armature.animation_data.action_slot = slots[slot_name]
    bpy.ops.nla.bake(
        frame_start=start,
        frame_end=end,
        step=1,
        only_selected=True,
        visual_keying=False,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,
        clean_curves=False,
        bake_types={"POSE"},
    )
    baked = armature.animation_data.action
    baked.name = action_name
    baked.use_fake_user = True
armature.animation_data.action = bpy.data.actions["1_idle_hold"]
bpy.ops.object.mode_set(mode="OBJECT")
scene.frame_end = 54
scene.frame_set(0)

# Camera on the CF gun
coords = [cf_gun.matrix_world @ Vector(v.co) for v in cf_gun.data.vertices]
center = sum(coords, Vector((0, 0, 0))) / max(len(coords), 1)
cam_data = bpy.data.cameras.new("P7S04_Cam")
cam_data.lens = 35
cam = bpy.data.objects.new("P7S04_Cam", cam_data)
cam.location = center + Vector((12.0, -28.0, 10.0))
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
col_lights.objects.link(cam)
scene.camera = cam

for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        space = area.spaces.active
        space.shading.type = "MATERIAL"
        space.overlay.show_bones = True
        break

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
scene.render.filepath = PREVIEW_PATH
bpy.ops.render.render(write_still=True)
scene.frame_set(81)
scene.render.filepath = PREVIEW_FRAME_PATH
bpy.ops.render.render(write_still=True)
scene.frame_set(0)
bpy.ops.wm.save_mainfile()

report = {
    "schema": "cf2.p7.blender-current.v1",
    "blend": BLEND_PATH.replace("\\", "/"),
    "preview": PREVIEW_PATH.replace("\\", "/"),
    "preview_reload_f81": PREVIEW_FRAME_PATH.replace("\\", "/"),
    "armature": armature.name,
    "bones": len(armature.data.bones),
    "meshes": {
        "cf_gun": {"name": cf_gun.name, "verts": len(cf_gun.data.vertices), "faces": len(cf_gun.data.polygons)},
        **{
            key: {"name": mesh.name, "verts": len(mesh.data.vertices), "faces": len(mesh.data.polygons)}
            for key, mesh in arm_meshes.items()
        },
    },
    "actions": action_map,
    "note": "Current broken P7-S04 retarget. Not deployed. Fix/verify here before any in-game compile.",
}
with open(REPORT_PATH, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(report, ensure_ascii=False))
