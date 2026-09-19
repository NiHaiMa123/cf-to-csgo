"""G1: build CF_SOURCE_REFERENCE in a NEW blend. Does not overwrite working or frozen files."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = r"D:\project\cf_to_csgo"
WORKING = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend")
DEST = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\source_reference.blend")
PAYLOAD = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\reference_payload.json")
PRE_HASHES = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\baseline\pre_hashes.json")
SHOT_DIR = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\shots")
RESULT = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\review\g1_blender_build.json")
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"

FOCUS = ("select", "reload", "idle_0")
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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_preconditions():
    live = os.path.abspath(bpy.data.filepath)
    want = os.path.abspath(WORKING)
    if live != want:
        raise RuntimeError("live filepath %s != working %s" % (live, want))
    if os.path.exists(DEST):
        raise RuntimeError("refusing to overwrite existing %s" % DEST)
    disk_sha = sha256_file(WORKING)
    if disk_sha != WORKING_SHA:
        raise RuntimeError("working disk sha %s != %s" % (disk_sha, WORKING_SHA))
    frozen = json.loads(open(PRE_HASHES, encoding="utf-8").read())["files"]
    frozen_ok = {}
    for rel, meta in frozen.items():
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        got = sha256_file(path)
        if got != meta["sha256"]:
            raise RuntimeError("frozen hash changed: %s" % rel)
        frozen_ok[rel] = got
    return {
        "live_filepath": live,
        "is_dirty_before": bool(bpy.data.is_dirty),
        "working_disk_sha": disk_sha,
        "frozen_ok": frozen_ok,
    }


def look_at(obj, location, target):
    obj.location = Vector(location)
    direction = Vector(target) - Vector(location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def make_armature(name, nodes, rest_mats, collection, palette):
    data = bpy.data.armatures.new(name + "_data")
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = []
    for i, node in enumerate(nodes):
        eb = data.edit_bones.new(node["name"])
        M = rest_mats[i]
        head = Vector((M[0][3], M[1][3], M[2][3]))
        axis = Vector((M[0][1], M[1][1], M[2][1]))
        if axis.length < 1e-8:
            axis = Vector((0.0, 1.0, 0.0))
        else:
            axis = axis.normalized()
        length = 0.18
        if node["children"]:
            cM = rest_mats[node["children"][0]]
            delta = Vector((cM[0][3], cM[1][3], cM[2][3])) - head
            if delta.length > 0.05:
                length = delta.length
                axis = delta.normalized()
        eb.head = head
        eb.tail = head + axis * max(length, 0.12)
        ebs.append(eb)
    for i, node in enumerate(nodes):
        if node["parent"] >= 0:
            ebs[i].parent = ebs[node["parent"]]
            ebs[i].use_connect = False
    bpy.ops.object.mode_set(mode="POSE")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
        if hasattr(pb, "color"):
            pb.color.palette = palette
    data.display_type = "OCTAHEDRAL"
    data.show_axes = True
    obj.show_in_front = True
    obj.select_set(False)
    return obj


def dfs_order(nodes):
    order = []

    def walk(i):
        order.append(i)
        for child in nodes[i]["children"]:
            walk(child)

    for i, node in enumerate(nodes):
        if node["parent"] < 0:
            walk(i)
    return order


def world_matrix(pos, quat_xyzw):
    x, y, z, w = quat_xyzw
    q = Quaternion((w, x, y, z))
    M = q.to_matrix().to_4x4()
    M.translation = Vector(pos)
    return M


def apply_pose(obj, nodes, order, pos_list, quat_list):
    bones = obj.pose.bones
    for i in order:
        pb = bones[nodes[i]["name"]]
        pb.matrix = world_matrix(pos_list[i], quat_list[i])


def bind_action_slot(obj, action):
    if obj.animation_data is None:
        obj.animation_data_create()
    obj.animation_data.action = action
    slots = getattr(action, "slots", None)
    if slots:
        if len(slots) == 0 and hasattr(slots, "new"):
            try:
                slots.new(id_type="OBJECT", name="OB" + obj.name)
            except Exception:
                pass
        if len(slots):
            obj.animation_data.action_slot = slots[0]


def key_clip(obj, nodes, order, clip_name, samples):
    action = bpy.data.actions.new("R1A_CF_" + clip_name)
    bind_action_slot(obj, action)
    obj.data.pose_position = "POSE"
    for sample in samples:
        apply_pose(obj, nodes, order, sample["pos"], sample["quat_xyzw_world"])
        bpy.context.view_layer.update()
        frame = int(sample["frame_100"])
        for node in nodes:
            pb = obj.pose.bones[node["name"]]
            pb.keyframe_insert("location", frame=frame)
            pb.keyframe_insert("rotation_quaternion", frame=frame)
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return action


def set_hud(text_obj, clip, time_ms, key, extra):
    key_s = "none" if key is None else str(key)
    text_obj.data.body = (
        "CF SOURCE  %s\n"
        "%d ms   key %s\n"
        "SKELETON_ONLY_REFERENCE\n"
        "100 fps diagnostic SLERP\n"
        "%s"
    ) % (clip, int(round(time_ms)), key_s, extra)


def nearest_key(clip_payload, time_ms):
    best = None
    best_d = 1e9
    for i, t in enumerate(clip_payload["times_ms"]):
        d = abs(t - time_ms)
        if d < best_d:
            best_d = d
            best = i
    if best is not None and best_d <= 1.0:
        return best
    return None


def render_still(scene, camera, path):
    scene.camera = camera
    scene.render.filepath = path
    bpy.context.view_layer.update()
    result = bpy.ops.render.opengl(write_still=True)
    return list(result), os.path.exists(path) and os.path.getsize(path) > 0


def measure_pose_error(obj, nodes, order, sample):
    apply_pose  # kept as sampler comparison against evaluated pose
    bpy.context.view_layer.update()
    max_pos = 0.0
    worst = None
    for i, node in enumerate(nodes):
        pb = obj.pose.bones[node["name"]]
        got = Vector(pb.matrix.to_translation())
        want = Vector(sample["pos"][i])
        d = (got - want).length
        if d > max_pos:
            max_pos = d
            worst = node["name"]
    return max_pos, worst


def write_switcher(text_body):
    name = "r1a_source_switcher.py"
    if name in bpy.data.texts:
        block = bpy.data.texts[name]
        block.clear()
    else:
        block = bpy.data.texts.new(name)
    block.write(text_body)
    block.use_module = True
    return name


SWITCHER = '''import bpy

CLIPS = [
    ("R1A_CF_select", "select 640ms", 64),
    ("R1A_CF_reload", "reload 1600ms", 160),
    ("R1A_CF_idle_0", "idle_0 3000ms", 300),
    ("R1A_CF_fire", "fire 90ms", 9),
    ("R1A_CF_prefire", "prefire 500ms", 50),
    ("R1A_CF_postfire", "postfire 500ms", 50),
    ("R1A_CF_run", "run 650ms", 65),
    ("R1A_CF_knife-attack", "knife-attack 666ms", 66),
]


def _items(self, context):
    return [(name, label, "", i) for i, (name, label, _end) in enumerate(CLIPS)]


def apply_clip(self, context):
    obj = bpy.data.objects.get("R1A_CF_ANIM")
    if obj is None:
        return
    if obj.animation_data is None:
        obj.animation_data_create()
    act = bpy.data.actions.get(self.r1a_clip)
    if act is None:
        return
    obj.data.pose_position = "POSE"
    obj.animation_data.action = act
    if getattr(act, "slots", None) and len(act.slots):
        obj.animation_data.action_slot = act.slots[0]
    end = 64
    for name, _label, clip_end in CLIPS:
        if name == self.r1a_clip:
            end = clip_end
            break
    sc = context.scene
    sc.render.fps = 100
    sc.render.fps_base = 1.0
    sc.frame_start = 0
    sc.frame_end = end
    sc.frame_current = 0
    sc.frame_set(0)


class R1A_PT_clips(bpy.types.Panel):
    bl_label = "R1A CF source clips"
    bl_idname = "R1A_PT_clips"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "R1A"

    def draw(self, context):
        self.layout.prop(context.scene, "r1a_clip")
        self.layout.label(text="100 fps; frame=ms/10")
        self.layout.label(text="ANIM=tracks  BIND=static")


def register():
    if not hasattr(bpy.types.Scene, "r1a_clip"):
        bpy.types.Scene.r1a_clip = bpy.props.EnumProperty(name="clip", items=_items, update=apply_clip)
    try:
        bpy.utils.register_class(R1A_PT_clips)
    except ValueError:
        pass


def unregister():
    if hasattr(bpy.types.Scene, "r1a_clip"):
        del bpy.types.Scene.r1a_clip
    try:
        bpy.utils.unregister_class(R1A_PT_clips)
    except Exception:
        pass


register()
'''


def main():
    os.makedirs(SHOT_DIR, exist_ok=True)
    pre = assert_preconditions()
    payload = json.loads(open(PAYLOAD, encoding="utf-8").read())
    nodes = payload["nodes"]
    order = dfs_order(nodes)
    bind_mats = [n["bind_world"] for n in nodes]
    bbox = payload["bbox_all_clips"]
    bmin = Vector(bbox["min"])
    bmax = Vector(bbox["max"])
    center = (bmin + bmax) * 0.5
    size = (bmax - bmin).length

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    save_res = bpy.ops.wm.save_as_mainfile(filepath=DEST, copy=False, check_existing=False)
    if "FINISHED" not in save_res:
        raise RuntimeError("save_as to source_reference failed: %s" % (save_res,))
    if bpy.data.filepath != DEST:
        raise RuntimeError("session did not switch to dest: %s" % bpy.data.filepath)
    if not os.path.exists(DEST) or os.path.getsize(DEST) < 1000:
        raise RuntimeError("dest missing/empty after save_as")
    if sha256_file(WORKING) != WORKING_SHA:
        raise RuntimeError("working disk hash changed after save_as")

    if "CF_SOURCE_REFERENCE" in bpy.data.scenes:
        raise RuntimeError("CF_SOURCE_REFERENCE already exists")
    scene = bpy.data.scenes.new("CF_SOURCE_REFERENCE")
    bpy.context.window.scene = scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.fps = 100
    scene.render.fps_base = 1.0
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.frame_start = 0
    scene.frame_end = 160
    scene.frame_current = 0
    scene.unit_settings.system = "NONE"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 8
    world = bpy.data.worlds.new("R1A_World")
    scene.world = world
    world.use_nodes = True
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Color"].default_value = (0.18, 0.19, 0.21, 1.0)
            node.inputs["Strength"].default_value = 0.7
    scene.view_settings.view_transform = "Standard"

    root_col = bpy.data.collections.new("R1A_CF_SOURCE_REFERENCE")
    scene.collection.children.link(root_col)
    col_bind = bpy.data.collections.new("R1A_CF_BIND")
    col_anim = bpy.data.collections.new("R1A_CF_ANIM")
    col_cam = bpy.data.collections.new("R1A_CAMERAS")
    for col in (col_bind, col_anim, col_cam):
        root_col.children.link(col)

    bind_obj = make_armature("R1A_CF_BIND", nodes, bind_mats, col_bind, "THEME03")
    anim_obj = make_armature("R1A_CF_ANIM", nodes, bind_mats, col_anim, "THEME01")
    bind_obj.data.pose_position = "REST"

    actions = {}
    for clip_name, clip in payload["clips"].items():
        actions[clip_name] = key_clip(anim_obj, nodes, order, clip_name, clip["samples"])

    bind_action_slot(anim_obj, actions["select"])
    scene.frame_end = int(payload["clips"]["select"]["duration_ms"] / 10.0)
    scene.frame_set(0)

    # Cameras from global bbox; never follow the gun.
    cam_data_side = bpy.data.cameras.new("R1A_CAM_SIDE")
    cam_data_top = bpy.data.cameras.new("R1A_CAM_TOP")
    cam_data_front = bpy.data.cameras.new("R1A_CAM_FRONT")
    for cam_d in (cam_data_side, cam_data_top, cam_data_front):
        cam_d.lens = 50
        cam_d.clip_start = 0.05
        cam_d.clip_end = 200.0
    cam_side = bpy.data.objects.new("R1A_CAM_SIDE", cam_data_side)
    cam_top = bpy.data.objects.new("R1A_CAM_TOP", cam_data_top)
    cam_front = bpy.data.objects.new("R1A_CAM_FRONT", cam_data_front)
    for cam in (cam_side, cam_top, cam_front):
        col_cam.objects.link(cam)
    look_at(cam_side, (center.x + size * 0.85, center.y, center.z + size * 0.08), center)
    look_at(cam_top, (center.x, center.y, center.z + size * 0.95), center)
    look_at(cam_front, (center.x, center.y - size * 0.95, center.z + size * 0.05), center)
    scene.camera = cam_side

    light_data = bpy.data.lights.new("R1A_Key", "AREA")
    light_data.energy = 400
    light_data.size = 8
    light = bpy.data.objects.new("R1A_Key", light_data)
    light.location = center + Vector((size * 0.4, -size * 0.5, size * 0.6))
    col_cam.objects.link(light)
    fill_data = bpy.data.lights.new("R1A_Fill", "AREA")
    fill_data.energy = 180
    fill_data.size = 10
    fill = bpy.data.objects.new("R1A_Fill", fill_data)
    fill.location = center + Vector((-size * 0.5, -size * 0.2, size * 0.4))
    col_cam.objects.link(fill)

    font = bpy.data.curves.new("R1A_HUD", "FONT")
    font.size = 0.35
    hud = bpy.data.objects.new("R1A_HUD", font)
    col_cam.objects.link(hud)
    hud.location = center + Vector((-size * 0.15, -size * 0.05, size * 0.42))

    switcher_name = write_switcher(SWITCHER)
    exec(SWITCHER, {"bpy": bpy})

    # Bake-vs-sampler at select 0ms and 277ms (on-grid) and 31.5ms (half frame).
    bind_action_slot(anim_obj, actions["select"])
    scene.frame_set(0)
    bpy.context.view_layer.update()
    err0, bone0 = measure_pose_error(anim_obj, nodes, order, payload["clips"]["select"]["samples"][0])
    scene.frame_set(28)  # 280ms grid; event is 277ms
    bpy.context.view_layer.update()
    sample28 = payload["clips"]["select"]["samples"][28]
    err28, bone28 = measure_pose_error(anim_obj, nodes, order, sample28)
    scene.frame_set(3, subframe=0.15)
    bpy.context.view_layer.update()
    # Reconstruct sampler pose is in payload only on 10ms grid; report evaluated vs neighbors.
    s3 = payload["clips"]["select"]["samples"][3]
    s4 = payload["clips"]["select"]["samples"][4]
    mid_pos = []
    for i in range(len(nodes)):
        a = Vector(s3["pos"][i])
        b = Vector(s4["pos"][i])
        mid_pos.append((a * 0.85 + b * 0.15))
    max_half = 0.0
    worst_half = None
    for i, node in enumerate(nodes):
        got = Vector(anim_obj.pose.bones[node["name"]].matrix.to_translation())
        d = (got - mid_pos[i]).length
        if d > max_half:
            max_half = d
            worst_half = node["name"]

    rendered = []
    cameras = [("side", cam_side), ("top", cam_top)]
    for clip_name, time_ms in SHOTS:
        clip = payload["clips"][clip_name]
        frame = int(round(time_ms / 10.0))
        frame = max(0, min(frame, len(clip["samples"]) - 1))
        bind_action_slot(anim_obj, actions[clip_name])
        scene.frame_end = int(clip["duration_ms"] / 10.0)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        key = nearest_key(clip, time_ms)
        extra = "ANIM tracks  BIND hidden"
        bind_obj.hide_viewport = True
        bind_obj.hide_render = True
        anim_obj.hide_viewport = False
        set_hud(hud, clip_name, time_ms, key, extra)
        for cam_name, cam in cameras:
            path = os.path.join(SHOT_DIR, "%s_%s_t%04dms.png" % (cam_name, clip_name, time_ms))
            op, ok = render_still(scene, cam, path)
            rendered.append({"path": path, "ok": ok, "ops": op, "clip": clip_name, "time_ms": time_ms, "frame": frame})

    # Comparison: both skeletons visible at reload 0 and idle 0.
    bind_obj.hide_viewport = False
    bind_obj.hide_render = False
    for clip_name, time_ms in (("reload", 0), ("idle_0", 0), ("select", 0)):
        clip = payload["clips"][clip_name]
        bind_action_slot(anim_obj, actions[clip_name])
        scene.frame_set(0)
        bpy.context.view_layer.update()
        set_hud(hud, clip_name, 0, 0, "ANIM+BIND same world; not compensated")
        path = os.path.join(SHOT_DIR, "side_%s_t0000ms_bind_and_anim.png" % clip_name)
        op, ok = render_still(scene, cam_side, path)
        rendered.append({"path": path, "ok": ok, "ops": op, "clip": clip_name, "compare": True})

    bind_obj.hide_viewport = True
    bind_obj.hide_render = True
    bind_action_slot(anim_obj, actions["select"])
    scene.frame_start = 0
    scene.frame_end = 64
    scene.frame_set(0)
    scene.camera = cam_side
    if hasattr(scene, "r1a_clip"):
        scene.r1a_clip = "R1A_CF_select"

    bpy.ops.wm.save_mainfile()
    dest_sha = sha256_file(DEST)
    working_sha_after = sha256_file(WORKING)

    videos = []
    ffmpeg = "ffmpeg"
    seq_dir = os.path.join(SHOT_DIR, "_seq_select_side")
    os.makedirs(seq_dir, exist_ok=True)
    bind_action_slot(anim_obj, actions["select"])
    scene.frame_start = 0
    scene.frame_end = 64
    scene.camera = cam_side
    set_hud(hud, "select", 0, 0, "sequence")
    scene.render.filepath = os.path.join(seq_dir, "f")
    bpy.ops.render.opengl(animation=True)
    mp4 = os.path.join(SHOT_DIR, "select_side_100fps.mp4")
    cmd = [
        ffmpeg, "-y", "-framerate", "25", "-i", os.path.join(seq_dir, "f%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos.append({
            "mp4": mp4,
            "ok": proc.returncode == 0 and os.path.exists(mp4),
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-400:],
            "note": "encoded at 25 fps display of 100 fps diagnostic frames (4x slow)",
        })
    except Exception as exc:
        videos.append({"mp4": mp4, "ok": False, "error": str(exc)})

    seq_dir2 = os.path.join(SHOT_DIR, "_seq_reload_side")
    os.makedirs(seq_dir2, exist_ok=True)
    bind_action_slot(anim_obj, actions["reload"])
    scene.frame_start = 0
    scene.frame_end = 160
    set_hud(hud, "reload", 0, 0, "sequence")
    scene.render.filepath = os.path.join(seq_dir2, "f")
    bpy.ops.render.opengl(animation=True)
    mp4b = os.path.join(SHOT_DIR, "reload_side_100fps.mp4")
    cmd = [
        ffmpeg, "-y", "-framerate", "25", "-i", os.path.join(seq_dir2, "f%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4b,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        videos.append({
            "mp4": mp4b,
            "ok": proc.returncode == 0 and os.path.exists(mp4b),
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-400:],
            "note": "encoded at 25 fps display of 100 fps diagnostic frames (4x slow)",
        })
    except Exception as exc:
        videos.append({"mp4": mp4b, "ok": False, "error": str(exc)})

    bind_action_slot(anim_obj, actions["select"])
    scene.frame_start = 0
    scene.frame_end = 64
    scene.frame_set(0)
    bpy.ops.wm.save_mainfile()

    out = {
        "status": "SOURCE_REFERENCE_BUILT",
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "pre": pre,
        "dest": DEST,
        "dest_sha256": dest_sha,
        "working_sha_unchanged": working_sha_after == WORKING_SHA,
        "working_sha_after": working_sha_after,
        "live_filepath": bpy.data.filepath,
        "scene": scene.name,
        "objects": ["R1A_CF_ANIM", "R1A_CF_BIND", "R1A_CAM_SIDE", "R1A_CAM_TOP", "R1A_CAM_FRONT", "R1A_HUD"],
        "actions": list(actions.keys()),
        "switcher_text": switcher_name,
        "pose_error_select_f0": {"max_pos": err0, "bone": bone0},
        "pose_error_select_f28": {"max_pos": err28, "bone": bone28},
        "half_frame_vs_linear_neighbors": {"max_pos": max_half, "bone": worst_half, "note": "subframe 3.15 vs linear mix of 30/40ms samples, not SLERP proof"},
        "rendered": rendered,
        "videos": videos,
        "compiled": False,
        "deployed": False,
        "user_accepted": False,
        "cs_scene_preserved": "Scene" in bpy.data.scenes,
        "save_as_ops": list(save_res),
    }
    with open(RESULT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)
        handle.write("\n")
    return out


main()
