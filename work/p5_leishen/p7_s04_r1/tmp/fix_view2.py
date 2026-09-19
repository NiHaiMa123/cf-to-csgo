import bpy, json
from mathutils import Vector
scn = bpy.context.scene
# full playback range covering all clips (idle_0 is longest: 3000ms -> 300f)
scn.frame_start = 0
scn.frame_end = 300
scn.r1a_source_clip = "idle_0"
scn.frame_set(0)

# point every 3D viewport at the model/skeleton region (around (4,-6,0))
eye = Vector((27.0, -7.65, 7.87))      # reuse studio cam position
target = Vector((4.0, -6.0, 0.5))
view_rot = (target - eye).to_track_quat('-Z', 'Y')
dist = (eye - target).length
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type != "VIEW_3D":
            continue
        space = area.spaces.active
        r3d = space.region_3d
        if scr.name == "Layout":
            continue  # leave Layout as RENDERED + camera
        space.shading.type = "MATERIAL"
        r3d.view_perspective = "PERSP"
        r3d.view_location = target
        r3d.view_rotation = view_rot
        r3d.view_distance = dist
        space.overlay.show_overlays = True

# render select entry (f0) and reload mid to check camera coverage
scn.r1a_source_clip = "select"
scn.frame_set(0)
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\probe_select_f0.png"
bpy.ops.render.render(write_still=True)
scn.r1a_source_clip = "reload"
scn.frame_set(72)   # ~718ms mag insert area
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\probe_reload_72.png"
bpy.ops.render.render(write_still=True)
# back to idle for default view
scn.r1a_source_clip = "idle_0"
scn.frame_set(0)
print(json.dumps({"ok": True, "clip": scn.r1a_source_clip, "range": [scn.frame_start, scn.frame_end]}))
