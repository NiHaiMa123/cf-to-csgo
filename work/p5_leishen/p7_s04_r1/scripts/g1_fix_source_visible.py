"""Replace overlay-only bones with renderable joint/stick meshes and camera stills."""
from __future__ import annotations

import json
import os
import subprocess

import bmesh
import bpy
from mathutils import Vector

ROOT = r"D:\project\cf_to_csgo"
DEST = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\source_reference.blend")
PAYLOAD_PATH = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\reference_payload.json")
SHOT_DIR = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\shots")
RESULT = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\review\g1_visible_fix.json")
WORKING = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend")
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"

SHOTS = [
    ("select", 0),
    ("select", 277),
    ("select", 640),
    ("reload", 0),
    ("reload", 194),
    ("reload", 718),
    ("reload", 1211),
    ("reload", 1585),
    ("reload", 1600),
    ("idle_0", 0),
]
AXIS_BONES = ("FvARM-bone Prop1", "Bone06", "Bone04")


def sha256_file(path):
    import hashlib
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def emission_mat(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (color[0], color[1], color[2], 1.0)
    nt = mat.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    em.inputs["Strength"].default_value = 4.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def ico_mesh(name, radius):
    mesh = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def unit_cylinder(name):
    mesh = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=8,
        radius1=1.0, radius2=1.0, depth=1.0,
    )
    bmesh.ops.translate(bm, verts=list(bm.verts), vec=(0.0, 0.0, 0.5))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def axis_mesh(name):
    """Three unit axes as a mesh: X red-length 1 along X, etc. Built as 3 edges; color via 3 objects instead."""
    mesh = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0)], [(0, 1)], [])
    mesh.update()
    return mesh


def unlink_if_exists(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    bpy.data.objects.remove(obj, do_unlink=True)


def look_at(obj, location, target):
    obj.location = Vector(location)
    direction = Vector(target) - Vector(location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_stick(obj, a, b):
    a = Vector(a)
    b = Vector(b)
    d = b - a
    length = d.length
    obj.location = a
    obj.scale = (0.025, 0.025, max(length, 0.001))
    if length > 1e-8:
        obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    else:
        obj.rotation_euler = (0.0, 0.0, 0.0)


def set_axis(obj, origin, axis, length=0.55):
    origin = Vector(origin)
    axis = Vector(axis)
    if axis.length < 1e-8:
        axis = Vector((1.0, 0.0, 0.0))
    axis = axis.normalized()
    obj.location = origin
    obj.scale = (0.02, 0.02, length)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()


def quat_xyzw_axes(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    R = [
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
    ]
    return (
        Vector((R[0][0], R[1][0], R[2][0])),
        Vector((R[0][1], R[1][1], R[2][1])),
        Vector((R[0][2], R[1][2], R[2][2])),
    )


def ensure_collection(scene, name, parent):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    if col.name not in parent.children:
        parent.children.link(col)
    return col


def apply_pose(nodes, index_by_name, joints, sticks, axes_objs, pos, quat, axis_indices):
    for i, node in enumerate(nodes):
        joints[i].location = Vector(pos[i])
    for i, node in enumerate(nodes):
        if node["parent"] < 0:
            continue
        set_stick(sticks[i], pos[node["parent"]], pos[i])
    for bone_name, triple in axes_objs.items():
        i = index_by_name[bone_name]
        ax, ay, az = quat_xyzw_axes(quat[i])
        origin = pos[i]
        set_axis(triple[0], origin, ax)
        set_axis(triple[1], origin, ay)
        set_axis(triple[2], origin, az)


HANDLER = r'''
import json
import bpy
from mathutils import Vector

PAYLOAD_PATH = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json"
_CACHE = {}


def _payload():
    if "p" not in _CACHE:
        with open(PAYLOAD_PATH, "r", encoding="utf-8") as handle:
            _CACHE["p"] = json.load(handle)
        _CACHE["index"] = {n["name"]: n["index"] for n in _CACHE["p"]["nodes"]}
    return _CACHE["p"]


def _vec(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        Vector((1.0 - 2.0 * (yy + zz), 2.0 * (xy + wz), 2.0 * (xz - wy))),
        Vector((2.0 * (xy - wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz + wx))),
        Vector((2.0 * (xz + wy), 2.0 * (yz - wx), 1.0 - 2.0 * (xx + yy))),
    )


def _stick(obj, a, b):
    a = Vector(a); b = Vector(b)
    d = b - a
    length = d.length
    obj.location = a
    obj.scale = (0.025, 0.025, max(length, 0.001))
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler() if length > 1e-8 else (0.0, 0.0, 0.0)


def _axis(obj, origin, axis, length=0.55):
    origin = Vector(origin)
    axis = Vector(axis)
    if axis.length < 1e-8:
        axis = Vector((1.0, 0.0, 0.0))
    obj.location = origin
    obj.scale = (0.02, 0.02, length)
    obj.rotation_euler = axis.normalized().to_track_quat("Z", "Y").to_euler()


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
    idx = _CACHE["index"]
    for bone_name in ("FvARM-bone Prop1", "Bone06", "Bone04"):
        i = idx[bone_name]
        ax, ay, az = _vec(quat[i])
        # _vec above returned columns of R from rows incorrectly; use same as builder
        x, y, z, w = quat[i]
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z
        ax = Vector((1.0 - 2.0 * (yy + zz), 2.0 * (xy + wz), 2.0 * (xz - wy)))
        ay = Vector((2.0 * (xy - wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz + wx)))
        az = Vector((2.0 * (xz + wy), 2.0 * (yz - wx), 1.0 - 2.0 * (xx + yy)))
        origin = pos[i]
        ox = bpy.data.objects.get("R1A_ANIM_AX_%s_X" % bone_name.replace(" ", "_"))
        oy = bpy.data.objects.get("R1A_ANIM_AX_%s_Y" % bone_name.replace(" ", "_"))
        oz = bpy.data.objects.get("R1A_ANIM_AX_%s_Z" % bone_name.replace(" ", "_"))
        if ox: _axis(ox, origin, ax)
        if oy: _axis(oy, origin, ay)
        if oz: _axis(oz, origin, az)
    hud = bpy.data.objects.get("R1A_HUD")
    if hud and hasattr(hud.data, "body"):
        times = clip["times_ms"]
        t = sample["time_ms"]
        key = sample.get("source_key")
        hud.data.body = "CF SOURCE  %s\n%d ms   key %s\nSKELETON_ONLY  100fps SLERP" % (
            clip_name, int(round(t)), "none" if key is None else str(key)
        )


def register():
    if r1a_apply not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(r1a_apply)
    if not hasattr(bpy.types.Scene, "r1a_source_clip"):
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
        self.layout.label(text="orange=anim  cyan=bind")


register()
'''


def main():
    if os.path.abspath(bpy.data.filepath) != os.path.abspath(DEST):
        raise RuntimeError("live is %s, expected source_reference" % bpy.data.filepath)
    if sha256_file(WORKING) != WORKING_SHA:
        raise RuntimeError("working hash changed; abort")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    payload = json.loads(open(PAYLOAD_PATH, encoding="utf-8").read())
    nodes = payload["nodes"]
    index_by_name = {n["name"]: n["index"] for n in nodes}
    scene = bpy.data.scenes.get("CF_SOURCE_REFERENCE")
    if scene is None:
        raise RuntimeError("missing CF_SOURCE_REFERENCE")
    bpy.context.window.scene = scene

    root = bpy.data.collections.get("R1A_CF_SOURCE_REFERENCE")
    if root is None:
        root = bpy.data.collections.new("R1A_CF_SOURCE_REFERENCE")
        scene.collection.children.link(root)
    col_anim = ensure_collection(scene, "R1A_MESH_ANIM", root)
    col_bind = ensure_collection(scene, "R1A_MESH_BIND", root)
    col_cam = bpy.data.collections.get("R1A_CAMERAS") or ensure_collection(scene, "R1A_CAMERAS", root)

    for obj in list(col_anim.objects) + list(col_bind.objects):
        if obj.name.startswith("R1A_ANIM_") or obj.name.startswith("R1A_BIND_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    mat_anim = emission_mat("R1A_MAT_ANIM", (1.0, 0.42, 0.08))
    mat_bind = emission_mat("R1A_MAT_BIND", (0.15, 0.72, 0.95))
    mat_x = emission_mat("R1A_MAT_X", (0.95, 0.15, 0.1))
    mat_y = emission_mat("R1A_MAT_Y", (0.2, 0.9, 0.2))
    mat_z = emission_mat("R1A_MAT_Z", (0.2, 0.4, 1.0))
    ico_anim = ico_mesh("R1A_ICO_ANIM", 0.09)
    ico_bind = ico_mesh("R1A_ICO_BIND", 0.09)
    cyl_anim = unit_cylinder("R1A_CYL_ANIM")
    cyl_bind = unit_cylinder("R1A_CYL_BIND")
    ico_anim.materials.append(mat_anim)
    ico_bind.materials.append(mat_bind)
    cyl_anim.materials.append(mat_anim)
    cyl_bind.materials.append(mat_bind)

    bind_pos = [n["bind_pos"] for n in nodes]
    bind_quat = [n["bind_quat_xyzw_polar"] for n in nodes]
    idle0 = payload["clips"]["idle_0"]["samples"][0]
    select0 = payload["clips"]["select"]["samples"][0]

    anim_joints = []
    bind_joints = []
    anim_sticks = {}
    bind_sticks = {}
    for i, node in enumerate(nodes):
        aj = bpy.data.objects.new("R1A_ANIM_J_%02d" % i, ico_anim)
        bj = bpy.data.objects.new("R1A_BIND_J_%02d" % i, ico_bind)
        aj.location = Vector(select0["pos"][i])
        bj.location = Vector(bind_pos[i])
        aj.show_in_front = True
        bj.show_in_front = True
        col_anim.objects.link(aj)
        col_bind.objects.link(bj)
        anim_joints.append(aj)
        bind_joints.append(bj)
        if node["parent"] >= 0:
            ast = bpy.data.objects.new("R1A_ANIM_S_%02d" % i, cyl_anim)
            bst = bpy.data.objects.new("R1A_BIND_S_%02d" % i, cyl_bind)
            ast.show_in_front = True
            bst.show_in_front = True
            col_anim.objects.link(ast)
            col_bind.objects.link(bst)
            set_stick(ast, select0["pos"][node["parent"]], select0["pos"][i])
            set_stick(bst, bind_pos[node["parent"]], bind_pos[i])
            anim_sticks[i] = ast
            bind_sticks[i] = bst

    def make_axes(prefix, collection, pos, quat, mats):
        out = {}
        for bone_name in AXIS_BONES:
            i = index_by_name[bone_name]
            safe = bone_name.replace(" ", "_")
            triple = []
            ax, ay, az = quat_xyzw_axes(quat[i])
            for tag, axis, mat in (("X", ax, mats[0]), ("Y", ay, mats[1]), ("Z", az, mats[2])):
                obj = bpy.data.objects.new("%s_AX_%s_%s" % (prefix, safe, tag), axm if False else cyl)
                obj.data = cyl
                obj.data.materials.clear()
                # materials are on mesh shared; use object color via override
                obj.material_slots.data  # noqa: keep mesh shared, assign via overlay
                obj.show_in_front = True
                collection.objects.link(obj)
                # unique material copy per axis object: link slot
                set_axis(obj, pos[i], axis)
                triple.append(obj)
                obj["r1a_mat"] = tag
            out[bone_name] = triple
            # assign materials by replacing mesh copies
            for obj, mat in zip(triple, mats):
                obj.data = cyl
        return out

    # unique meshes so materials stick (shared cyl would share one material)
    def cyl_copy(name, mat):
        mesh = cyl_anim.copy()
        mesh.name = name
        mesh.materials.clear()
        mesh.materials.append(mat)
        return mesh

    anim_axes = {}
    bind_axes = {}
    for bone_name in AXIS_BONES:
        i = index_by_name[bone_name]
        safe = bone_name.replace(" ", "_")
        anim_triple = []
        bind_triple = []
        ax, ay, az = quat_xyzw_axes(select0["quat_xyzw_world"][i])
        bx, by, bz = quat_xyzw_axes(bind_quat[i])
        for tag, aaxis, baxis, mat in (
            ("X", ax, bx, mat_x),
            ("Y", ay, by, mat_y),
            ("Z", az, bz, mat_z),
        ):
            am = bpy.data.objects.new("R1A_ANIM_AX_%s_%s" % (safe, tag), cyl_copy("R1A_CYL_A_%s_%s" % (safe, tag), mat))
            bm = bpy.data.objects.new("R1A_BIND_AX_%s_%s" % (safe, tag), cyl_copy("R1A_CYL_B_%s_%s" % (safe, tag), mat))
            col_anim.objects.link(am)
            col_bind.objects.link(bm)
            am.show_in_front = True
            bm.show_in_front = True
            set_axis(am, select0["pos"][i], aaxis)
            set_axis(bm, bind_pos[i], baxis)
            anim_triple.append(am)
            bind_triple.append(bm)
        anim_axes[bone_name] = anim_triple
        bind_axes[bone_name] = bind_triple

    for arm_name in ("R1A_CF_ANIM", "R1A_CF_BIND"):
        arm = bpy.data.objects.get(arm_name)
        if arm:
            arm.hide_viewport = True
            arm.hide_render = True

    # Cameras: focus bbox of select+reload+idle, not bind T-pose hands.
    pts = []
    for clip_name in ("select", "reload", "idle_0"):
        for sample in payload["clips"][clip_name]["samples"]:
            for p in sample["pos"]:
                pts.append(Vector(p))
    bmin = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    bmax = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (bmin + bmax) * 0.5
    size = max((bmax - bmin).length, 1.0)
    cam_side = bpy.data.objects["R1A_CAM_SIDE"]
    cam_top = bpy.data.objects["R1A_CAM_TOP"]
    cam_front = bpy.data.objects["R1A_CAM_FRONT"]
    for cam in (cam_side, cam_top, cam_front):
        cam.data.lens = 35
        cam.data.clip_start = 0.05
        cam.data.clip_end = 250.0
    look_at(cam_side, (center.x + size * 0.62, center.y - size * 0.08, center.z + size * 0.12), center)
    look_at(cam_top, (center.x, center.y, center.z + size * 0.72), center)
    look_at(cam_front, (center.x, center.y - size * 0.72, center.z + size * 0.06), center)
    scene.camera = cam_side

    hud = bpy.data.objects.get("R1A_HUD")
    if hud:
        hud.parent = cam_side
        hud.location = (-1.35, -0.78, -3.2)
        hud.rotation_euler = (0.0, 0.0, 0.0)
        hud.scale = (0.08, 0.08, 0.08)
        hud.data.size = 0.35
        hud.data.align_x = "LEFT"
        hud.data.align_y = "TOP"
        hud.show_in_front = True
        mat_hud = emission_mat("R1A_MAT_HUD", (1.0, 1.0, 1.0))
        if hud.data.materials:
            hud.data.materials[0] = mat_hud
        else:
            hud.data.materials.append(mat_hud)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.fps = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    if scene.world and scene.world.use_nodes:
        for node in scene.world.node_tree.nodes:
            if node.type == "BACKGROUND":
                node.inputs["Color"].default_value = (0.12, 0.13, 0.15, 1.0)
                node.inputs["Strength"].default_value = 0.35

    text = bpy.data.texts.get("r1a_source_switcher.py")
    if text is None:
        text = bpy.data.texts.new("r1a_source_switcher.py")
    text.clear()
    text.write(HANDLER)
    text.use_module = True
    exec(HANDLER, {"bpy": bpy, "json": json, "Vector": Vector})

    scene.r1a_source_clip = "select"
    scene.frame_start = 0
    scene.frame_end = 64
    scene.frame_set(0)
    bpy.context.view_layer.update()

    def render_cam(cam, path):
        scene.camera = cam
        if hud:
            hud.parent = cam
            hud.location = (-1.35, -0.78, -3.2)
        scene.render.filepath = path
        bpy.context.view_layer.update()
        result = bpy.ops.render.opengl(write_still=True, view_context=False)
        return list(result), os.path.exists(path) and os.path.getsize(path) > 2000

    rendered = []
    for clip_name, time_ms in SHOTS:
        clip = payload["clips"][clip_name]
        frame = int(round(time_ms / 10.0))
        frame = max(0, min(frame, len(clip["samples"]) - 1))
        scene.r1a_source_clip = clip_name
        scene.frame_end = int(clip["duration_ms"] / 10.0)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        # hide bind for motion stills
        for obj in col_bind.objects:
            obj.hide_viewport = True
            obj.hide_render = True
        for obj in col_anim.objects:
            obj.hide_viewport = False
            obj.hide_render = False
        for cam_name, cam in (("side", cam_side), ("top", cam_top)):
            path = os.path.join(SHOT_DIR, "%s_%s_t%04dms.png" % (cam_name, clip_name, time_ms))
            op, ok = render_cam(cam, path)
            rendered.append({"path": path, "ok": ok, "ops": op, "size": os.path.getsize(path) if ok else 0})

    for obj in col_bind.objects:
        obj.hide_viewport = False
        obj.hide_render = False
    for clip_name in ("select", "reload", "idle_0"):
        scene.r1a_source_clip = clip_name
        scene.frame_set(0)
        bpy.context.view_layer.update()
        path = os.path.join(SHOT_DIR, "side_%s_t0000ms_bind_and_anim.png" % clip_name)
        op, ok = render_cam(cam_side, path)
        rendered.append({"path": path, "ok": ok, "ops": op, "compare": True, "size": os.path.getsize(path) if ok else 0})

    for obj in col_bind.objects:
        obj.hide_viewport = True
        obj.hide_render = True
    scene.r1a_source_clip = "select"
    scene.frame_start = 0
    scene.frame_end = 64
    scene.frame_set(0)
    scene.camera = cam_side
    if hud:
        hud.parent = cam_side
        hud.location = (-1.35, -0.78, -3.2)

    bpy.ops.wm.save_mainfile()

    videos = []
    for clip_name, end, seq_name, mp4_name in (
        ("select", 64, "_seq_select_side", "select_side_100fps.mp4"),
        ("reload", 160, "_seq_reload_side", "reload_side_100fps.mp4"),
    ):
        seq_dir = os.path.join(SHOT_DIR, seq_name)
        os.makedirs(seq_dir, exist_ok=True)
        scene.r1a_source_clip = clip_name
        scene.frame_start = 0
        scene.frame_end = end
        scene.camera = cam_side
        if hud:
            hud.parent = cam_side
        scene.render.filepath = os.path.join(seq_dir, "f")
        bpy.ops.render.opengl(animation=True, view_context=False)
        mp4 = os.path.join(SHOT_DIR, mp4_name)
        cmd = [
            "ffmpeg", "-y", "-framerate", "25",
            "-i", os.path.join(seq_dir, "f%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        videos.append({
            "mp4": mp4,
            "ok": proc.returncode == 0 and os.path.exists(mp4),
            "returncode": proc.returncode,
            "sizes_unique": len({os.path.getsize(os.path.join(seq_dir, f)) for f in os.listdir(seq_dir) if f.endswith(".png")}),
        })

    scene.r1a_source_clip = "select"
    scene.frame_end = 64
    scene.frame_set(0)
    bpy.ops.wm.save_mainfile()

    gun_i = index_by_name["FvARM-bone Prop1"]
    scene.r1a_source_clip = "select"
    scene.frame_set(0)
    bpy.context.view_layer.update()
    g0 = list(anim_joints[gun_i].location)
    scene.frame_set(64)
    bpy.context.view_layer.update()
    g64 = list(anim_joints[gun_i].location)
    want0 = select0["pos"][gun_i]
    want64 = payload["clips"]["select"]["samples"][-1]["pos"][gun_i]

    out = {
        "status": "SOURCE_REFERENCE_VISIBLE_FIXED",
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "working_sha_unchanged": sha256_file(WORKING) == WORKING_SHA,
        "live": bpy.data.filepath,
        "camera_center": list(center),
        "camera_size": size,
        "select_gun_f0": {"got": g0, "want": want0, "err": (Vector(g0) - Vector(want0)).length},
        "select_gun_f64": {"got": g64, "want": want64, "err": (Vector(g64) - Vector(want64)).length},
        "rendered": rendered,
        "videos": videos,
        "compiled": False,
        "deployed": False,
        "user_accepted": False,
    }
    with open(RESULT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)
        handle.write("\n")


main()
