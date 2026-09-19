import bpy, json
t = bpy.data.texts.get("p7_clip_switcher.py")
if t:
    src = "\n".join(l.body for l in t.lines)
    print("===== p7_clip_switcher.py (%d chars) =====" % len(src))
    print(src[:5000])
out = {
 "frame_handlers": [getattr(h, "__name__", str(h)) for h in bpy.app.handlers.frame_change_post],
 "clip_prop": getattr(bpy.context.scene, "r1a_source_clip", "MISSING"),
 "p7_prop": getattr(bpy.context.scene, "p7_clip", "MISSING"),
 "frame": bpy.context.scene.frame_current,
 "anim_action": bpy.data.objects["R1A_CF_ANIM"].animation_data.action.name if bpy.data.objects["R1A_CF_ANIM"].animation_data else None,
}
print("===== STATE =====")
print(json.dumps(out, ensure_ascii=False, indent=1))
