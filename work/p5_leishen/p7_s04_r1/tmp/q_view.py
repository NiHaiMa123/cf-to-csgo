import bpy, json
out = {"screens": []}
for scr in bpy.data.screens:
    s = {"name": scr.name, "areas": []}
    for area in scr.areas:
        a = {"type": area.type}
        if area.type == "VIEW_3D":
            space = area.spaces.active
            r3d = space.region_3d
            a["shading"] = space.shading.type
            a["view_persp"] = r3d.view_perspective if r3d else None
            a["view_dist"] = r3d.view_distance if r3d else None
            a["view_loc"] = list(r3d.view_location) if r3d else None
            a["view_rot"] = [round(x,3) for x in r3d.view_rotation] if r3d else None
            a["localview"] = space.local_view is not None
            a["overlay"] = space.overlay.show_overlays
            a["clip_start"], a["clip_end"] = space.clip_start, space.clip_end
            a["use_scene_lights"] = getattr(space.shading, "use_scene_lights", None)
            a["use_scene_world"] = getattr(space.shading, "use_scene_world", None)
        s["areas"].append(a)
    out["screens"].append(s)
out["active_screen"] = bpy.context.window.screen.name if bpy.context.window else None
out["active_obj"] = bpy.context.object.name if bpy.context.object else None
out["mode"] = bpy.context.mode
out["frame"] = bpy.context.scene.frame_current
for n in ["R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE","R1A_VIEW_GUN"]:
    o = bpy.data.objects.get(n)
    if o:
        out[n] = {"hide_vp": o.hide_viewport, "hide_get": o.hide_get(), "hide_render": o.hide_render,
                  "type": o.type, "verts": len(o.data.vertices) if o.type=="MESH" else None}
out["fps"] = bpy.context.scene.render.fps
out["engine"] = bpy.context.scene.render.engine
out["is_dirty"] = bpy.data.is_dirty
print(json.dumps(out, ensure_ascii=False, indent=1))
