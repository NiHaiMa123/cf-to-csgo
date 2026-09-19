import json
import os

import bpy
from mathutils import Vector

OUT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04\blender"
SHOT = os.path.join(OUT, "shots")
os.makedirs(SHOT, exist_ok=True)

scene = bpy.context.scene
arm = bpy.data.objects["CS_M4A4_Armature"]
gun = bpy.data.objects["CF_GUN_P6"]
glove = bpy.data.objects.get("CS_GLOVE")
sleeve = bpy.data.objects.get("CS_SLEEVE")
arm.data.pose_position = "POSE"
arm.hide_render = True
arm.hide_viewport = True

world = scene.world
if world and world.use_nodes:
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Color"].default_value = (0.22, 0.23, 0.25, 1.0)
            node.inputs["Strength"].default_value = 0.8
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.4
scene.view_settings.gamma = 1.0
scene.render.film_transparent = False
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 8


def set_clip(action_name, frame):
    act = bpy.data.actions[action_name]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    if getattr(act, "slots", None) and act.slots:
        arm.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(frame))
    bpy.context.view_layer.update()


def eval_center_size(objects):
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for obj in objects:
        if obj is None:
            continue
        ev = obj.evaluated_get(deps)
        for corner in ev.bound_box:
            pts.append(ev.matrix_world @ Vector(corner))
    center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)
    minc = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    maxc = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size = max((maxc - minc).length, 1.0)
    return center, size, minc, maxc


def place_cameras(center, size):
    review = bpy.data.objects.get("P7S04_Review")
    eye = bpy.data.objects.get("P7S04_Cam")
    # Three-quarter from front-right-above, close enough to fill the frame.
    review.location = center + Vector((size * 0.35, -size * 0.85, size * 0.22))
    review.rotation_euler = (center - review.location).to_track_quat("-Z", "Y").to_euler()
    review.data.lens = 50
    review.data.clip_start = 0.05
    review.data.clip_end = 400.0
    eye.location = Vector((0.0, 0.0, 0.8))
    aim = Vector((center.x * 0.35, center.y, center.z * 0.6))
    eye.rotation_euler = (aim - eye.location).to_track_quat("-Z", "Y").to_euler()
    eye.data.lens = 40
    eye.data.clip_start = 0.05
    return review, eye


def render_shot(cam, path):
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


set_clip("1_idle_hold", 0)
center, size, minc, maxc = eval_center_size([gun, glove, sleeve])
review, eye = place_cameras(center, size)

SHOTS = [
    ("1_idle_hold", 0, "idle_f0"),
    ("2_shoot", 2, "shoot_f2"),
    ("3_draw", 13, "draw_f13"),
    ("4_reload", 0, "reload_f0"),
    ("4_reload", 13, "reload_f13_clipout"),
    ("4_reload", 40, "reload_f40"),
    ("4_reload", 48, "reload_f48_clipin"),
    ("4_reload", 81, "reload_f81_bolt"),
    ("4_reload", 106, "reload_f106"),
]

info = {
    "center": list(center),
    "size": size,
    "min": list(minc),
    "max": list(maxc),
    "review_loc": list(review.location),
    "shots": [],
}
for action_name, frame, label in SHOTS:
    set_clip(action_name, frame)
    c, s, _, _ = eval_center_size([gun, glove, sleeve])
    place_cameras(c, s)
    side = os.path.join(SHOT, f"side_{label}.png")
    eye_path = os.path.join(SHOT, f"eye_{label}.png")
    render_shot(review, side)
    render_shot(eye, eye_path)
    pb = arm.pose.bones
    def w(name):
        return (arm.matrix_world @ pb[name].matrix).to_translation()
    info["shots"].append({
        "label": label,
        "gun_hand": (w("v_weapon.M4A1_Parent") - w("v_weapon.Bip01_R_Hand")).length,
        "wrist": (w("v_weapon.Bip01_R_Forearm") - w("v_weapon.Bip01_R_Hand")).length,
        "finger": (w("v_weapon.Bip01_R_Finger1") - w("v_weapon.Bip01_R_Finger11")).length,
        "lhand_clip": (w("v_weapon.Bip01_L_Hand") - w("v_weapon.M4A1_Clip")).length,
        "side": side.replace("\\", "/"),
        "eye": eye_path.replace("\\", "/"),
    })

set_clip("1_idle_hold", 0)
place_cameras(*eval_center_size([gun, glove, sleeve])[:2])
scene.camera = review
if hasattr(scene, "p7_clip"):
    scene.p7_clip = "1_idle_hold"
bpy.ops.wm.save_mainfile()
print(json.dumps(info, ensure_ascii=False))
