import bpy, math, os
from mathutils import Vector

# reuse the scene from blender_eye.py run: find existing objects
eye_main = bpy.data.objects.get('eye_main')
core = bpy.data.objects.get('eye_core')
rbw = bpy.data.objects.get('eye_rbw')
camob = bpy.context.scene.camera

def look_at(obj, pt):
    obj.rotation_euler = (obj.location - Vector(pt)).to_track_quat('Z', 'Y').to_euler()

def face_sprites():
    for ob in (rbw, eye_main, core):
        if ob:
            ob.rotation_euler = (camob.location - ob.location).to_track_quat('Z', 'Y').to_euler()

sc = bpy.context.scene
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
OUT = r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\render_'

# left side profile (camera on -X side where the eye sockets live)
camob.location = (-34, 8, -3)
look_at(camob, (-6, 12, -5))
face_sprites()
sc.render.filepath = OUT + 'eye_left.png'
bpy.ops.render.render(write_still=True)

# eye close-up from -X
camob.location = (-22, -2, -1.5)
look_at(camob, (-15.8, -2.6, -0.8))
face_sprites()
sc.render.filepath = OUT + 'eye_left_close.png'
bpy.ops.render.render(write_still=True)

# fp-ish view matching user's screenshot angle (gun viewed slightly from left)
camob.location = (-4, -8, -4.5)
look_at(camob, (6, 18, -7))
face_sprites()
sc.render.filepath = OUT + 'eye_fp2.png'
bpy.ops.render.render(write_still=True)
print('DONE')
