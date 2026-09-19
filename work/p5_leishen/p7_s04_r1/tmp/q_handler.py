import bpy, json
out = {}
out["frame_handlers"] = [getattr(h, "__name__", str(h)) for h in bpy.app.handlers.frame_change_post]
out["depsgraph_handlers"] = [getattr(h, "__name__", str(h)) for h in bpy.app.handlers.depsgraph_update_post]
out["has_clip_prop"] = hasattr(bpy.context.scene, "r1a_source_clip")
out["clip_prop"] = getattr(bpy.context.scene, "r1a_source_clip", None)
out["hud"] = bpy.data.objects.get("R1A_HUD") is not None
if bpy.data.objects.get("R1A_HUD"):
    hud = bpy.data.objects["R1A_HUD"]
    out["hud_hide_vp"] = hud.hide_viewport
    out["hud_body"] = getattr(hud.data, "body", None)
# test: record view gun parent world, change frame, re-record
dg = bpy.context.evaluated_depsgraph_get()
arm = bpy.data.objects["R1A_VIEW_ARM"]
ev = arm.evaluated_get(dg)
p0 = (arm.matrix_world @ ev.pose.bones["v_weapon.M4A1_Parent"].matrix).translation[:]
scn = bpy.context.scene
scn.frame_set(0)
dg = bpy.context.evaluated_depsgraph_get()
ev = arm.evaluated_get(dg)
p1 = (arm.matrix_world @ ev.pose.bones["v_weapon.M4A1_Parent"].matrix).translation[:]
scn.frame_set(30)
dg = bpy.context.evaluated_depsgraph_get()
ev = arm.evaluated_get(dg)
p2 = (arm.matrix_world @ ev.pose.bones["v_weapon.M4A1_Parent"].matrix).translation[:]
out["gun_world_f10"] = [round(v,3) for v in p0]
out["gun_world_f0"] = [round(v,3) for v in p1]
out["gun_world_f30"] = [round(v,3) for v in p2]
# count J_/S_ objects and their hide state
j = [o for o in bpy.data.objects if o.name.startswith("R1A_ANIM_J_")]
s = [o for o in bpy.data.objects if o.name.startswith("R1A_ANIM_S_")]
out["J_count"] = len(j); out["S_count"] = len(s)
out["J_hidden"] = sum(1 for o in j if o.hide_viewport)
out["S_hidden"] = sum(1 for o in s if o.hide_viewport)
scn.frame_set(10)
print(json.dumps(out, ensure_ascii=False, indent=1))
