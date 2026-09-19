"""Show textured P6 gun + gloves in the source-reference scene for viewing."""
from __future__ import annotations

import json
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

DEST = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\source_reference.blend"
PAYLOAD_PATH = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"
WORKING = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend"
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
SHOT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\view_model.png"
RESULT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_show_model.json"

C3 = [
    [1.784059185, 0.034856661, 0.01256238, -2.536612614],
    [0.011249821, 0.066854712, -1.783155592, -14.701850345],
    [-0.035302149, 1.782850369, 0.066620549, 19.652856554],
    [0.0, 0.0, 0.0, 1.0],
]
BONE_MAP = {
    "FvARM-bone L ForeArm": "v_weapon.Bip01_L_Forearm",
    "FvARM-bone L Hand": "v_weapon.Bip01_L_Hand",
    "FvARM-bone L Finger0": "v_weapon.Bip01_L_Finger0",
    "FvARM-bone L Finger01": "v_weapon.Bip01_L_Finger01",
    "FvARM-bone L Finger02": "v_weapon.Bip01_L_Finger02",
    "FvARM-bone L Finger1": "v_weapon.Bip01_L_Finger1",
    "FvARM-bone L Finger11": "v_weapon.Bip01_L_Finger11",
    "FvARM-bone L Finger12": "v_weapon.Bip01_L_Finger12",
    "FvARM-bone L Finger2": "v_weapon.Bip01_L_Finger2",
    "FvARM-bone L Finger21": "v_weapon.Bip01_L_Finger21",
    "FvARM-bone L Finger22": "v_weapon.Bip01_L_Finger22",
    "FvARM-bone L Finger3": "v_weapon.Bip01_L_Finger3",
    "FvARM-bone L Finger31": "v_weapon.Bip01_L_Finger31",
    "FvARM-bone L Finger32": "v_weapon.Bip01_L_Finger32",
    "FvARM-bone L Finger4": "v_weapon.Bip01_L_Finger4",
    "FvARM-bone L Finger41": "v_weapon.Bip01_L_Finger41",
    "FvARM-bone L Finger42": "v_weapon.Bip01_L_Finger42",
    "FvARM-bone L ForeTwist": "v_weapon.Bip01_L_ForeTwist",
    "FvARM-bone R ForeArm": "v_weapon.Bip01_R_Forearm",
    "FvARM-bone R Hand": "v_weapon.Bip01_R_Hand",
    "FvARM-bone R Finger0": "v_weapon.Bip01_R_Finger0",
    "FvARM-bone R Finger01": "v_weapon.Bip01_R_Finger01",
    "FvARM-bone R Finger02": "v_weapon.Bip01_R_Finger02",
    "FvARM-bone R Finger1": "v_weapon.Bip01_R_Finger1",
    "FvARM-bone R Finger11": "v_weapon.Bip01_R_Finger11",
    "FvARM-bone R Finger12": "v_weapon.Bip01_R_Finger12",
    "FvARM-bone R Finger2": "v_weapon.Bip01_R_Finger2",
    "FvARM-bone R Finger21": "v_weapon.Bip01_R_Finger21",
    "FvARM-bone R Finger22": "v_weapon.Bip01_R_Finger22",
    "FvARM-bone R Finger3": "v_weapon.Bip01_R_Finger3",
    "FvARM-bone R Finger31": "v_weapon.Bip01_R_Finger31",
    "FvARM-bone R Finger32": "v_weapon.Bip01_R_Finger32",
    "FvARM-bone R Finger4": "v_weapon.Bip01_R_Finger4",
    "FvARM-bone R Finger41": "v_weapon.Bip01_R_Finger41",
    "FvARM-bone R Finger42": "v_weapon.Bip01_R_Finger42",
    "FvARM-bone R ForeTwist": "v_weapon.Bip01_R_ForeTwist",
    "FvARM-bone Prop1": "v_weapon.M4A1_Parent",
    "Bone06": "v_weapon.M4A1_Clip",
    "Bone04": "v_weapon.M4A1_Bolt",
}


def sha256_file(path):
    import hashlib
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def look_at(obj, location, target):
    obj.location = Vector(location)
    obj.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


def mat_mul(a, b):
    out = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] + a[i][3] * b[3][j]
    return out


def mat_inv(m):
    return [list(row) for row in Matrix(m).inverted()]


def cf_world(pos, quat_xyzw):
    x, y, z, w = quat_xyzw
    q = Quaternion((w, x, y, z))
    M = q.to_matrix().to_4x4()
    M.translation = Vector(pos)
    return M


def hide_collection(name, hide):
    col = bpy.data.collections.get(name)
    if col is None:
        return
    col.hide_viewport = hide
    col.hide_render = hide
    for obj in col.objects:
        obj.hide_viewport = hide
        obj.hide_render = hide


def remove_if(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def dup_armature(src, name, collection):
    new = src.copy()
    new.data = src.data.copy()
    new.name = name
    new.data.name = name + "_data"
    if new.animation_data:
        new.animation_data_clear()
    collection.objects.link(new)
    new.hide_viewport = True
    new.hide_render = True
    return new


def dup_mesh(src, name, collection, arm):
    new = src.copy()
    new.name = name
    collection.objects.link(new)
    new.parent = arm
    new.matrix_parent_inverse = Matrix.Identity(4)
    new.matrix_basis = Matrix.Identity(4)
    for mod in new.modifiers:
        if mod.type == "ARMATURE":
            mod.object = arm
    new.hide_viewport = False
    new.hide_render = False
    return new


def retarget_copy_constraints(arm, target_arm):
    for pb in arm.pose.bones:
        for con in pb.constraints:
            if con.type == "COPY_TRANSFORMS" and con.target:
                con.target = target_arm


def pose_from_sample(arm, Tmat, nodes, index_by_name, sample):
    T = Matrix(Tmat)
    order = []

    def walk(bone):
        order.append(bone)
        for child in bone.children:
            walk(child)

    for bone in arm.data.bones:
        if bone.parent is None:
            walk(bone)
    reverse = {cs: cf for cf, cs in BONE_MAP.items()}
    for bone in order:
        cf_name = reverse.get(bone.name)
        if cf_name is None:
            continue
        i = index_by_name[cf_name]
        cf_m = cf_world(sample["pos"][i], sample["quat_xyzw_world"][i])
        arm.pose.bones[bone.name].matrix = T @ cf_m
    bpy.context.view_layer.update()


HANDLER = r'''
import json
import bpy
from mathutils import Matrix, Quaternion, Vector

PAYLOAD_PATH = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"
_CACHE = {}
BONE_MAP = {
    "FvARM-bone L ForeArm": "v_weapon.Bip01_L_Forearm",
    "FvARM-bone L Hand": "v_weapon.Bip01_L_Hand",
    "FvARM-bone L Finger0": "v_weapon.Bip01_L_Finger0",
    "FvARM-bone L Finger01": "v_weapon.Bip01_L_Finger01",
    "FvARM-bone L Finger02": "v_weapon.Bip01_L_Finger02",
    "FvARM-bone L Finger1": "v_weapon.Bip01_L_Finger1",
    "FvARM-bone L Finger11": "v_weapon.Bip01_L_Finger11",
    "FvARM-bone L Finger12": "v_weapon.Bip01_L_Finger12",
    "FvARM-bone L Finger2": "v_weapon.Bip01_L_Finger2",
    "FvARM-bone L Finger21": "v_weapon.Bip01_L_Finger21",
    "FvARM-bone L Finger22": "v_weapon.Bip01_L_Finger22",
    "FvARM-bone L Finger3": "v_weapon.Bip01_L_Finger3",
    "FvARM-bone L Finger31": "v_weapon.Bip01_L_Finger31",
    "FvARM-bone L Finger32": "v_weapon.Bip01_L_Finger32",
    "FvARM-bone L Finger4": "v_weapon.Bip01_L_Finger4",
    "FvARM-bone L Finger41": "v_weapon.Bip01_L_Finger41",
    "FvARM-bone L Finger42": "v_weapon.Bip01_L_Finger42",
    "FvARM-bone L ForeTwist": "v_weapon.Bip01_L_ForeTwist",
    "FvARM-bone R ForeArm": "v_weapon.Bip01_R_Forearm",
    "FvARM-bone R Hand": "v_weapon.Bip01_R_Hand",
    "FvARM-bone R Finger0": "v_weapon.Bip01_R_Finger0",
    "FvARM-bone R Finger01": "v_weapon.Bip01_R_Finger01",
    "FvARM-bone R Finger02": "v_weapon.Bip01_R_Finger02",
    "FvARM-bone R Finger1": "v_weapon.Bip01_R_Finger1",
    "FvARM-bone R Finger11": "v_weapon.Bip01_R_Finger11",
    "FvARM-bone R Finger12": "v_weapon.Bip01_R_Finger12",
    "FvARM-bone R Finger2": "v_weapon.Bip01_R_Finger2",
    "FvARM-bone R Finger21": "v_weapon.Bip01_R_Finger21",
    "FvARM-bone R Finger22": "v_weapon.Bip01_R_Finger22",
    "FvARM-bone R Finger3": "v_weapon.Bip01_R_Finger3",
    "FvARM-bone R Finger31": "v_weapon.Bip01_R_Finger31",
    "FvARM-bone R Finger32": "v_weapon.Bip01_R_Finger32",
    "FvARM-bone R Finger4": "v_weapon.Bip01_R_Finger4",
    "FvARM-bone R Finger41": "v_weapon.Bip01_R_Finger41",
    "FvARM-bone R Finger42": "v_weapon.Bip01_R_Finger42",
    "FvARM-bone R ForeTwist": "v_weapon.Bip01_R_ForeTwist",
    "FvARM-bone Prop1": "v_weapon.M4A1_Parent",
    "Bone06": "v_weapon.M4A1_Clip",
    "Bone04": "v_weapon.M4A1_Bolt",
}


def _payload():
    if "p" not in _CACHE:
        with open(PAYLOAD_PATH, "r", encoding="utf-8") as handle:
            _CACHE["p"] = json.load(handle)
        _CACHE["index"] = {n["name"]: n["index"] for n in _CACHE["p"]["nodes"]}
        _CACHE["reverse"] = {cs: cf for cf, cs in BONE_MAP.items()}
        arm = bpy.data.objects.get("R1A_VIEW_ARM")
        T = Matrix(arm["r1a_T"]) if arm and "r1a_T" in arm else Matrix.Identity(4)
        _CACHE["T"] = T
    return _CACHE["p"]


def _stick(obj, a, b):
    a = Vector(a); b = Vector(b)
    d = b - a
    length = d.length
    obj.location = a
    obj.scale = (0.025, 0.025, max(length, 0.001))
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler() if length > 1e-8 else (0.0, 0.0, 0.0)


def r1a_apply(scene):
    p = _payload()
    clip_name = getattr(scene, "r1a_source_clip", "select")
    clip = p["clips"].get(clip_name) or p["clips"]["select"]
    samples = clip["samples"]
    frame = max(0, min(int(scene.frame_current), len(samples) - 1))
    sample = samples[frame]
    nodes = p["nodes"]
    pos = sample["pos"]
    quat = sample["quat_xyzw_world"]
    for i, node in enumerate(nodes):
        obj = bpy.data.objects.get("R1A_ANIM_J_%02d" % i)
        if obj:
            obj.location = Vector(pos[i])
        if node["parent"] >= 0:
            st = bpy.data.objects.get("R1A_ANIM_S_%02d" % i)
            if st:
                _stick(st, pos[node["parent"]], pos[i])
    arm = bpy.data.objects.get("R1A_VIEW_ARM")
    if arm is not None:
        T = _CACHE["T"]
        reverse = _CACHE["reverse"]
        idx = _CACHE["index"]
        order = []
        def walk(bone):
            order.append(bone)
            for child in bone.children:
                walk(child)
        for bone in arm.data.bones:
            if bone.parent is None:
                walk(bone)
        for bone in order:
            cf_name = reverse.get(bone.name)
            if cf_name is None:
                continue
            i = idx[cf_name]
            x, y, z, w = quat[i]
            q = Quaternion((w, x, y, z))
            M = q.to_matrix().to_4x4()
            M.translation = Vector(pos[i])
            arm.pose.bones[bone.name].matrix = T @ M
    hud = bpy.data.objects.get("R1A_HUD")
    if hud and hasattr(hud.data, "body"):
        hud.data.body = "CF SOURCE  %s\n%d ms\nmodel preview  100fps" % (
            clip_name, int(round(sample["time_ms"]))
        )


def register():
    bpy.app.handlers.frame_change_post[:] = [
        h for h in bpy.app.handlers.frame_change_post if getattr(h, "__name__", "") != "r1a_apply"
    ]
    bpy.app.handlers.frame_change_post.append(r1a_apply)
    items = [(n, n, "") for n in (
        "select", "reload", "idle_0", "fire", "prefire", "postfire", "run", "knife-attack"
    )]
    bpy.types.Scene.r1a_source_clip = bpy.props.EnumProperty(
        name="CF clip", items=items, default="select", update=lambda s, c: r1a_apply(s)
    )
    try:
        bpy.utils.register_class(R1A_PT_src)
    except ValueError:
        pass


class R1A_PT_src(bpy.types.Panel):
    bl_label = "R1A CF source"
    bl_idname = "R1A_PT_src"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "R1A"

    def draw(self, context):
        self.layout.prop(context.scene, "r1a_source_clip")
        self.layout.label(text="100 fps; frame = ms/10")
        self.layout.label(text="gun/gloves follow CF source")


register()
'''


if os.path.abspath(bpy.data.filepath) != os.path.abspath(DEST):
    raise RuntimeError("live is %s" % bpy.data.filepath)
if sha256_file(WORKING) != WORKING_SHA:
    raise RuntimeError("working hash changed")
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

scene = bpy.data.scenes["CF_SOURCE_REFERENCE"]
bpy.context.window.scene = scene
payload = json.loads(open(PAYLOAD_PATH, encoding="utf-8").read())
nodes = payload["nodes"]
index_by_name = {n["name"]: n["index"] for n in nodes}

mirror = [[-1.0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
T = mat_mul(mirror, C3)
Tinv = mat_inv(T)

root = bpy.data.collections.get("R1A_CF_SOURCE_REFERENCE")
col = bpy.data.collections.get("R1A_VIEW_MESH")
if col is None:
    col = bpy.data.collections.new("R1A_VIEW_MESH")
    root.children.link(col)
for obj in list(col.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for name in ("R1A_VIEW_ROOT", "R1A_VIEW_ARM", "R1A_VIEW_GUN", "R1A_VIEW_GLOVE",
             "R1A_VIEW_GLOVE_ARM", "R1A_VIEW_SLEEVE", "R1A_VIEW_SLEEVE_ARM", "R1A_CAM_STUDIO"):
    remove_if(name)

empty = bpy.data.objects.new("R1A_VIEW_ROOT", None)
empty.empty_display_type = "PLAIN_AXES"
empty.matrix_world = Matrix(Tinv)
col.objects.link(empty)

src_arm = bpy.data.objects["CS_M4A4_Armature"]
view_arm = dup_armature(src_arm, "R1A_VIEW_ARM", col)
view_arm.parent = empty
view_arm.matrix_parent_inverse = Matrix.Identity(4)
view_arm.matrix_basis = Matrix.Identity(4)
view_arm["r1a_T"] = [list(row) for row in Matrix(T)]

gun = dup_mesh(bpy.data.objects["CF_GUN_P6"], "R1A_VIEW_GUN", col, view_arm)
glove_arm = dup_armature(bpy.data.objects["CS_GLOVE_Armature"], "R1A_VIEW_GLOVE_ARM", col)
glove_arm.parent = empty
glove_arm.matrix_parent_inverse = Matrix.Identity(4)
glove_arm.matrix_basis = Matrix.Identity(4)
retarget_copy_constraints(glove_arm, view_arm)
glove = dup_mesh(bpy.data.objects["CS_GLOVE"], "R1A_VIEW_GLOVE", col, glove_arm)
sleeve_arm = dup_armature(bpy.data.objects["CS_SLEEVE_Armature"], "R1A_VIEW_SLEEVE_ARM", col)
sleeve_arm.parent = empty
sleeve_arm.matrix_parent_inverse = Matrix.Identity(4)
sleeve_arm.matrix_basis = Matrix.Identity(4)
retarget_copy_constraints(sleeve_arm, view_arm)
sleeve = dup_mesh(bpy.data.objects["CS_SLEEVE"], "R1A_VIEW_SLEEVE", col, sleeve_arm)

hide_collection("R1A_MESH_BIND", True)
hide_collection("R1A_MESH_ANIM", True)
hide_collection("R1A_CF_BIND", True)
hide_collection("R1A_CF_ANIM", True)
for arm_name in ("R1A_CF_ANIM", "R1A_CF_BIND"):
    obj = bpy.data.objects.get(arm_name)
    if obj:
        obj.hide_viewport = True
        obj.hide_render = True

idle = payload["clips"]["idle_0"]["samples"][0]
scene.r1a_source_clip = "idle_0"
scene.frame_set(0)
pose_from_sample(view_arm, T, nodes, index_by_name, idle)
bpy.context.view_layer.update()

gun_eval = gun.evaluated_get(bpy.context.evaluated_depsgraph_get())
center = gun_eval.matrix_world.translation.copy()
bb = [gun_eval.matrix_world @ Vector(c) for c in gun_eval.bound_box]
center = sum(bb, Vector((0, 0, 0))) / 8.0
size = (max(p.x for p in bb) - min(p.x for p in bb) +
        max(p.y for p in bb) - min(p.y for p in bb) +
        max(p.z for p in bb) - min(p.z for p in bb)) / 3.0
size = max(size, 4.0)

cam_data = bpy.data.cameras.new("R1A_CAM_STUDIO")
cam_data.lens = 45
cam_data.clip_start = 0.05
cam_data.clip_end = 200.0
cam = bpy.data.objects.new("R1A_CAM_STUDIO", cam_data)
col.objects.link(cam)
look_at(cam, center + Vector((size * 0.55, -size * 1.15, size * 0.35)), center)
scene.camera = cam

hud = bpy.data.objects.get("R1A_HUD")
if hud:
    hud.parent = cam
    hud.location = (-1.2, -0.72, -3.0)
    hud.rotation_euler = (0, 0, 0)
    hud.scale = (0.07, 0.07, 0.07)
    hud.hide_viewport = False

for light_name, energy, offset in (
    ("R1A_Key", 900.0, Vector((size * 0.6, -size * 0.8, size * 0.9))),
    ("R1A_Fill", 350.0, Vector((-size * 0.7, -size * 0.3, size * 0.5))),
):
    light = bpy.data.objects.get(light_name)
    if light:
        light.location = center + offset
        light.data.energy = energy

text = bpy.data.texts.get("r1a_source_switcher.py")
if text is None:
    text = bpy.data.texts.new("r1a_source_switcher.py")
text.clear()
text.write(HANDLER)
text.use_module = True
exec(HANDLER, {"bpy": bpy, "json": json})

scene.render.engine = "BLENDER_EEVEE"
scene.render.film_transparent = False
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
if scene.world and scene.world.use_nodes:
    for node in scene.world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Color"].default_value = (0.08, 0.085, 0.09, 1.0)
            node.inputs["Strength"].default_value = 0.25

scene.r1a_source_clip = "select"
scene.frame_start = 0
scene.frame_end = 64
scene.frame_set(0)
pose_from_sample(view_arm, T, nodes, index_by_name, payload["clips"]["select"]["samples"][0])
bpy.context.view_layer.update()

for area in bpy.context.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "MATERIAL"
    space.overlay.show_bones = False
    space.overlay.show_relationship_lines = False
    space.overlay.show_motion_paths = False
    space.region_3d.view_perspective = "CAMERA"

scene.render.filepath = SHOT
bpy.ops.render.opengl(write_still=True, view_context=False)
bpy.ops.wm.save_mainfile()

parent_pos = list(view_arm.pose.bones["v_weapon.M4A1_Parent"].head)
out = {
    "status": "MODEL_VIEW_READY",
    "working_sha_unchanged": sha256_file(WORKING) == WORKING_SHA,
    "center": list(center),
    "size": size,
    "parent_head": parent_pos,
    "shot": SHOT,
    "shot_ok": os.path.exists(SHOT),
    "objects": ["R1A_VIEW_GUN", "R1A_VIEW_GLOVE", "R1A_VIEW_SLEEVE", "R1A_CAM_STUDIO"],
    "note": "Viewing preview only. Not a retarget accept. Sticks hidden.",
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
