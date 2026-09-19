import json
import os

import bpy
from mathutils import Vector

OUT = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04\blender"
SHOT = os.path.join(OUT, "shots")
os.makedirs(SHOT, exist_ok=True)

scene = bpy.context.scene
gun = bpy.data.objects["CF_GUN_P6"]
glove = bpy.data.objects["CS_GLOVE"]
sleeve = bpy.data.objects["CS_SLEEVE"]
deform = gun.modifiers[0].object
if deform is None:
    raise RuntimeError("gun has no armature modifier target")

# Point glove/sleeve copy-transforms at the deforming armature.
for obj in (bpy.data.objects["CS_GLOVE_Armature"], bpy.data.objects["CS_SLEEVE_Armature"]):
    obj.hide_viewport = True
    obj.hide_render = True
    for pb in obj.pose.bones:
        for con in pb.constraints:
            if con.type == "COPY_TRANSFORMS":
                con.target = deform

# Drop the unused duplicate if it is not the deformer.
for obj in list(bpy.data.objects):
    if obj.type == "ARMATURE" and obj.name.startswith("CS_M4A4_Armature") and obj != deform:
        bpy.data.objects.remove(obj, do_unlink=True)

deform.name = "CS_M4A4_Armature"
deform.data.name = "CS_M4A4_Armature"
deform.hide_viewport = False
deform.hide_render = True
deform.data.pose_position = "POSE"
deform.show_in_front = True
if deform.animation_data is None:
    deform.animation_data_create()

world = scene.world
if world and world.use_nodes:
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Color"].default_value = (0.18, 0.19, 0.21, 1.0)
            node.inputs["Strength"].default_value = 0.7
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.35
scene.view_settings.gamma = 1.0
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.film_transparent = False
if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 8


def set_clip(action_name, frame):
    act = bpy.data.actions[action_name]
    deform.animation_data.action = act
    if getattr(act, "slots", None) and act.slots:
        deform.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(frame))
    bpy.context.view_layer.update()


def w(name):
    return (deform.matrix_world @ deform.pose.bones[name].matrix).to_translation()


def eval_pts(objects):
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for obj in objects:
        ev = obj.evaluated_get(deps)
        for corner in ev.bound_box:
            pts.append(ev.matrix_world @ Vector(corner))
    return pts


def place_cameras():
    pts = eval_pts([gun, glove])
    center = sum(pts, Vector((0, 0, 0))) / max(len(pts), 1)
    minc = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    maxc = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size = max((maxc - minc).length, 8.0)
    review = bpy.data.objects.get("P7S04_Review")
    eye = bpy.data.objects.get("P7S04_Cam")
    review.location = center + Vector((size * 0.15, -size * 0.55, size * 0.12))
    review.rotation_euler = (center - review.location).to_track_quat("-Z", "Y").to_euler()
    review.data.lens = 55
    review.data.clip_start = 0.05
    review.data.clip_end = 400
    eye.location = Vector((0.0, 0.0, 0.6))
    eye.rotation_euler = (center - eye.location).to_track_quat("-Z", "Y").to_euler()
    eye.data.lens = 42
    return review, eye, center, size


def render_shot(cam, path):
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


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

set_clip("1_idle_hold", 0)
review, eye, center, size = place_cameras()
report = {
    "deform": deform.name,
    "gun_mod": gun.modifiers[0].object.name,
    "center": list(center),
    "size": size,
    "shots": [],
}
for action_name, frame, label in SHOTS:
    set_clip(action_name, frame)
    review, eye, center, size = place_cameras()
    side = os.path.join(SHOT, f"side_{label}.png")
    eye_path = os.path.join(SHOT, f"eye_{label}.png")
    render_shot(review, side)
    render_shot(eye, eye_path)
    report["shots"].append({
        "label": label,
        "action": action_name,
        "frame": frame,
        "gun_hand": (w("v_weapon.M4A1_Parent") - w("v_weapon.Bip01_R_Hand")).length,
        "wrist": (w("v_weapon.Bip01_R_Forearm") - w("v_weapon.Bip01_R_Hand")).length,
        "finger": (w("v_weapon.Bip01_R_Finger1") - w("v_weapon.Bip01_R_Finger11")).length,
        "lhand_clip": (w("v_weapon.Bip01_L_Hand") - w("v_weapon.M4A1_Clip")).length,
        "r_hand": list(w("v_weapon.Bip01_R_Hand")),
        "gun": list(w("v_weapon.M4A1_Parent")),
        "side": side.replace("\\", "/"),
        "eye": eye_path.replace("\\", "/"),
    })

set_clip("1_idle_hold", 0)
place_cameras()
scene.camera = review
if hasattr(scene, "p7_clip"):
    scene.p7_clip = "1_idle_hold"
bpy.ops.wm.save_mainfile()
print(json.dumps(report, ensure_ascii=False))
