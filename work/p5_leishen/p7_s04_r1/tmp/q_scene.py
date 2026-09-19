import bpy, json
objs = []
for o in bpy.data.objects:
    objs.append({
        "name": o.name,
        "type": o.type,
        "hide_viewport": o.hide_viewport,
        "hide_render": o.hide_render,
        "hide_get": o.hide_get(),
        "display_type": o.display_type,
        "parent": o.parent.name if o.parent else None,
        "collection": [c.name for c in o.users_collection],
        "visible_get": o.visible_get(),
    })
info = {
    "filepath": bpy.data.filepath,
    "is_dirty": bpy.data.is_dirty,
    "frame": bpy.context.scene.frame_current,
    "fps": bpy.context.scene.render.fps,
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "objects": objs,
    "collections": [c.name for c in bpy.data.collections],
    "actions": [a.name for a in bpy.data.actions],
}
print(json.dumps(info, ensure_ascii=False, indent=1))
