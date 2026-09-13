"""Blender scene of the P7-S04 viewmodel after gun-driven retarget fix.

Live Blender MCP. Does not compile or deploy. In-game stays parked until
the user accepts this scene.

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
SHOT_DIR = os.path.join(OUT_DIR, "shots")
REPORT_PATH = os.path.join(OUT_DIR, "scene_report.json")
SWITCHER_PATH = os.path.join(OUT_DIR, "p7_clip_switcher.py")

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
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = PREVIEW_PATH
scene.render.film_transparent = False
scene.render.fps = 30
scene.frame_start = 0
scene.frame_end = 160
scene.frame_current = 0
if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 8
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


add_light("Key", 1600, (10, -16, 12), (55, 0, 30), 6)
add_light("Fill", 700, (-12, -14, 8), (70, 0, -30), 8)
add_light("Rim", 900, (4, 14, 10), (50, 0, 180), 5)
add_light("Front", 800, (0, -6, 4), (80, 0, 0), 8)
add_light("Eye", 500, (0, 2, 3), (90, 0, 0), 4)


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

# BST VALIDATE can spawn a second armature and reparent the gun onto it.
deform = None
for mod in cf_gun.modifiers:
    if mod.type == "ARMATURE" and mod.object:
        deform = mod.object
        break
if deform is None:
    raise RuntimeError("CF gun has no armature modifier target")
for obj in list(bpy.data.objects):
    if obj.type == "ARMATURE" and obj.name.startswith("CS_M4A4_Armature") and obj != deform:
        bpy.data.objects.remove(obj, do_unlink=True)
deform.name = "CS_M4A4_Armature"
deform.data.name = "CS_M4A4_Armature"
armature = deform
for label in ("CS_GLOVE_Armature", "CS_SLEEVE_Armature"):
    arm_obj = bpy.data.objects.get(label)
    if arm_obj is None:
        continue
    for pose_bone in arm_obj.pose.bones:
        for con in pose_bone.constraints:
            if con.type == "COPY_TRANSFORMS":
                con.target = armature

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
if getattr(bpy.data.actions["1_idle_hold"], "slots", None) and bpy.data.actions["1_idle_hold"].slots:
    armature.animation_data.action_slot = bpy.data.actions["1_idle_hold"].slots[0]
bpy.ops.object.mode_set(mode="OBJECT")
scene.frame_end = 54
scene.frame_set(0)
armature.data.pose_position = "POSE"
armature.hide_render = True

SWITCHER = r'''import bpy

CLIPS = [
    ("1_idle_hold", "1 持枪 idle", 54),
    ("2_shoot", "2 射击", 4),
    ("3_draw", "3 切枪 draw", 30),
    ("4_reload", "4 换弹 reload", 107),
    ("5_lookat", "5 检视 lookat", 159),
]


def _items(self, context):
    return [(name, label, "", i) for i, (name, label, _end) in enumerate(CLIPS)]


def apply_clip(self, context):
    obj = bpy.data.objects.get("CS_M4A4_Armature")
    if obj is None:
        return
    if obj.animation_data is None:
        obj.animation_data_create()
    act = bpy.data.actions.get(self.p7_clip)
    if act is None:
        return
    obj.data.pose_position = "POSE"
    obj.animation_data.action = act
    if getattr(act, "slots", None) and len(act.slots):
        obj.animation_data.action_slot = act.slots[0]
    end = 54
    for name, _label, clip_end in CLIPS:
        if name == self.p7_clip:
            end = clip_end
            break
    context.scene.frame_start = 0
    context.scene.frame_end = end
    context.scene.frame_current = 0
    context.scene.frame_set(0)


class P7_PT_clips(bpy.types.Panel):
    bl_label = "P7 clips"
    bl_idname = "P7_PT_clips"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "P7"

    def draw(self, context):
        self.layout.prop(context.scene, "p7_clip")


def register():
    if not hasattr(bpy.types.Scene, "p7_clip"):
        bpy.types.Scene.p7_clip = bpy.props.EnumProperty(name="clip", items=_items, update=apply_clip)
    try:
        bpy.utils.register_class(P7_PT_clips)
    except ValueError:
        pass


def unregister():
    if hasattr(bpy.types.Scene, "p7_clip"):
        del bpy.types.Scene.p7_clip
    try:
        bpy.utils.unregister_class(P7_PT_clips)
    except Exception:
        pass


register()
'''
with open(SWITCHER_PATH, "w", encoding="utf-8") as handle:
    handle.write(SWITCHER)
text = bpy.data.texts.get("p7_clip_switcher.py") or bpy.data.texts.new("p7_clip_switcher.py")
text.clear()
text.write(SWITCHER)
text.use_module = True
exec(SWITCHER, {"bpy": bpy})
scene.p7_clip = "1_idle_hold"

coords = [cf_gun.matrix_world @ Vector(v.co) for v in cf_gun.data.vertices]
center = sum(coords, Vector((0, 0, 0))) / max(len(coords), 1)
min_c = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
max_c = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
size = (max_c - min_c).length

cam_data = bpy.data.cameras.new("P7S04_Cam")
cam_data.lens = 50
cam_data.clip_start = 0.05
cam_data.clip_end = 200.0
cam = bpy.data.objects.new("P7S04_Cam", cam_data)
# Viewmodel-style: sit at the eye and look at the gun.
cam.location = Vector((0.0, 0.0, 1.2))
direction = center - cam.location
if direction.length < 1e-6:
    direction = Vector((0.0, -1.0, 0.0))
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
col_lights.objects.link(cam)
scene.camera = cam

review_data = bpy.data.cameras.new("P7S04_Review")
review_data.lens = 45
review_data.clip_start = 0.05
review_data.clip_end = 200.0
review = bpy.data.objects.new("P7S04_Review", review_data)
review.location = center + Vector((size * 0.55, -size * 1.15, size * 0.35))
review.rotation_euler = (center - review.location).to_track_quat("-Z", "Y").to_euler()
col_lights.objects.link(review)

for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        space = area.spaces.active
        space.shading.type = "MATERIAL"
        space.overlay.show_bones = False
        space.region_3d.view_perspective = "CAMERA"
        break

os.makedirs(SHOT_DIR, exist_ok=True)


def set_clip(action_name, frame):
    act = bpy.data.actions[action_name]
    armature.animation_data.action = act
    if getattr(act, "slots", None) and act.slots:
        armature.animation_data.action_slot = act.slots[0]
    armature.data.pose_position = "POSE"
    scene.frame_set(int(frame))
    bpy.context.view_layer.update()


def bone_world(name):
    pb = armature.pose.bones[name]
    return (armature.matrix_world @ pb.matrix).to_translation()


def bone_dist(a, b):
    return (bone_world(a) - bone_world(b)).length


def render_shot(camera_obj, path):
    scene.camera = camera_obj
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


SHOTS = [
    ("1_idle_hold", 0, "idle_f0"),
    ("2_shoot", 2, "shoot_f2"),
    ("3_draw", 0, "draw_f0"),
    ("3_draw", 13, "draw_f13"),
    ("4_reload", 0, "reload_f0"),
    ("4_reload", 13, "reload_f13_clipout"),
    ("4_reload", 48, "reload_f48_clipin"),
    ("4_reload", 81, "reload_f81_bolt"),
    ("4_reload", 106, "reload_f106"),
]

blender_metrics = []
shot_paths = {}
for action_name, frame, label in SHOTS:
    set_clip(action_name, frame)
    metrics = {
        "label": label,
        "action": action_name,
        "frame": frame,
        "gun_hand": bone_dist("v_weapon.M4A1_Parent", "v_weapon.Bip01_R_Hand"),
        "lhand_clip": bone_dist("v_weapon.Bip01_L_Hand", "v_weapon.M4A1_Clip"),
        "wrist": bone_dist("v_weapon.Bip01_R_Forearm", "v_weapon.Bip01_R_Hand"),
        "finger": bone_dist("v_weapon.Bip01_R_Finger1", "v_weapon.Bip01_R_Finger11"),
        "r_hand": list(bone_world("v_weapon.Bip01_R_Hand")),
        "gun": list(bone_world("v_weapon.M4A1_Parent")),
    }
    blender_metrics.append(metrics)
    eye_path = os.path.join(SHOT_DIR, f"eye_{label}.png")
    side_path = os.path.join(SHOT_DIR, f"side_{label}.png")
    render_shot(cam, eye_path)
    render_shot(review, side_path)
    shot_paths[label] = {"eye": eye_path.replace("\\", "/"), "side": side_path.replace("\\", "/")}

set_clip("1_idle_hold", 0)
scene.p7_clip = "1_idle_hold"
scene.camera = review
scene.render.filepath = PREVIEW_PATH
bpy.ops.render.render(write_still=True)
set_clip("4_reload", 81)
scene.render.filepath = PREVIEW_FRAME_PATH
bpy.ops.render.render(write_still=True)
set_clip("1_idle_hold", 0)
scene.camera = review
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

report = {
    "schema": "cf2.p7.blender-current.v1",
    "blend": BLEND_PATH.replace("\\", "/"),
    "preview": PREVIEW_PATH.replace("\\", "/"),
    "preview_reload_f81": PREVIEW_FRAME_PATH.replace("\\", "/"),
    "shots": shot_paths,
    "blender_metrics": blender_metrics,
    "armature": armature.name,
    "bones": len(armature.data.bones),
    "action": "1_idle_hold",
    "actions": [
        "1_idle_hold",
        "2_shoot",
        "3_draw",
        "4_reload",
        "5_lookat",
    ],
    "active_slot": "idle",
    "base_pose": "CS idle hold at frame 0; Pose Position not Rest Position",
    "meshes": {
        "cf_gun": {"name": cf_gun.name, "verts": len(cf_gun.data.vertices), "faces": len(cf_gun.data.polygons)},
        **{
            key: {"name": mesh.name, "verts": len(mesh.data.vertices), "faces": len(mesh.data.polygons)}
            for key, mesh in arm_meshes.items()
        },
    },
    "how_to_switch": "3D View N-panel tab P7; sets Action + Slot. Action Editor dropdown alone does not play layered clips.",
    "note": "Gun-driven relative retarget. Not deployed. Verify here before any in-game compile.",
}
with open(REPORT_PATH, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps({
    "blend": report["blend"],
    "shots": report["shots"],
    "blender_metrics": report["blender_metrics"],
    "actions": action_map,
}, ensure_ascii=False))

