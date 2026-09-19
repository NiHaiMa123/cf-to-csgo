"""Pull cameras back so the full CF source skeleton fits. Re-render stills and videos."""
import json
import os
import subprocess

import bpy
from mathutils import Vector

ROOT = r"D:\project\cf_to_csgo"
DEST = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\source_reference.blend")
PAYLOAD_PATH = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\reference_payload.json")
SHOT_DIR = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\source\shots")
WORKING = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\baseline\working_20260913_113051.blend")
WORKING_SHA = "3982f71ec64e6d54b577a58250f4b4a974fb92253545b7b326d25ebe977b6ed1"
RESULT = os.path.join(ROOT, r"work\p5_leishen\p7_s04_r1\review\g1_reframe.json")

SHOTS = [
    ("select", 0), ("select", 277), ("select", 640),
    ("reload", 0), ("reload", 194), ("reload", 718),
    ("reload", 1211), ("reload", 1585), ("reload", 1600),
    ("idle_0", 0),
]


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


if os.path.abspath(bpy.data.filepath) != os.path.abspath(DEST):
    raise RuntimeError("live %s" % bpy.data.filepath)
if sha256_file(WORKING) != WORKING_SHA:
    raise RuntimeError("working hash changed")

payload = json.loads(open(PAYLOAD_PATH, encoding="utf-8").read())
scene = bpy.data.scenes["CF_SOURCE_REFERENCE"]
bpy.context.window.scene = scene
pts = [Vector((0.0, 0.0, 0.0))]
for clip_name in ("select", "reload", "idle_0"):
    for sample in payload["clips"][clip_name]["samples"]:
        for p in sample["pos"]:
            pts.append(Vector(p))
bmin = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
bmax = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (bmin + bmax) * 0.5
extent = bmax - bmin
dist = max(extent.x, extent.y, extent.z) * 1.35

cam_side = bpy.data.objects["R1A_CAM_SIDE"]
cam_top = bpy.data.objects["R1A_CAM_TOP"]
cam_front = bpy.data.objects["R1A_CAM_FRONT"]
for cam in (cam_side, cam_top, cam_front):
    cam.data.lens = 24
    cam.data.clip_start = 0.05
    cam.data.clip_end = 400.0
look_at(cam_side, (center.x + dist, center.y, center.z + extent.z * 0.15), center)
look_at(cam_top, (center.x, center.y, center.z + dist), center)
look_at(cam_front, (center.x, center.y - dist, center.z + extent.z * 0.1), center)

hud = bpy.data.objects.get("R1A_HUD")
col_bind = bpy.data.collections.get("R1A_MESH_BIND")
col_anim = bpy.data.collections.get("R1A_MESH_ANIM")


def render_cam(cam, path):
    scene.camera = cam
    if hud:
        hud.parent = cam
        hud.location = (-1.55, -0.88, -3.4)
        hud.scale = (0.09, 0.09, 0.09)
    scene.render.filepath = path
    bpy.context.view_layer.update()
    result = bpy.ops.render.opengl(write_still=True, view_context=False)
    return list(result), os.path.exists(path)


rendered = []
for clip_name, time_ms in SHOTS:
    clip = payload["clips"][clip_name]
    frame = max(0, min(int(round(time_ms / 10.0)), len(clip["samples"]) - 1))
    scene.r1a_source_clip = clip_name
    scene.frame_end = int(clip["duration_ms"] / 10.0)
    scene.frame_set(frame)
    if col_bind:
        for obj in col_bind.objects:
            obj.hide_viewport = True
            obj.hide_render = True
    if col_anim:
        for obj in col_anim.objects:
            obj.hide_viewport = False
            obj.hide_render = False
    for cam_name, cam in (("side", cam_side), ("top", cam_top), ("front", cam_front)):
        path = os.path.join(SHOT_DIR, "%s_%s_t%04dms.png" % (cam_name, clip_name, time_ms))
        op, ok = render_cam(cam, path)
        rendered.append({"path": path, "ok": ok, "ops": op})

if col_bind:
    for obj in col_bind.objects:
        obj.hide_viewport = False
        obj.hide_render = False
for clip_name in ("select", "reload", "idle_0"):
    scene.r1a_source_clip = clip_name
    scene.frame_set(0)
    path = os.path.join(SHOT_DIR, "side_%s_t0000ms_bind_and_anim.png" % clip_name)
    op, ok = render_cam(cam_side, path)
    rendered.append({"path": path, "ok": ok, "compare": True})

if col_bind:
    for obj in col_bind.objects:
        obj.hide_viewport = True
        obj.hide_render = True

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
    proc = subprocess.run(
        ["ffmpeg", "-y", "-framerate", "25", "-i", os.path.join(seq_dir, "f%04d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4],
        capture_output=True, text=True, timeout=180,
    )
    videos.append({"mp4": mp4, "ok": proc.returncode == 0, "returncode": proc.returncode})

scene.r1a_source_clip = "select"
scene.frame_end = 64
scene.frame_set(0)
scene.camera = cam_side
bpy.ops.wm.save_mainfile()

out = {
    "center": list(center),
    "dist": dist,
    "working_sha_unchanged": sha256_file(WORKING) == WORKING_SHA,
    "rendered_ok": all(r.get("ok") for r in rendered),
    "n_stills": len(rendered),
    "videos": videos,
}
with open(RESULT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
