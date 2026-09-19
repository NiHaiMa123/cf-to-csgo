import bpy, json
out = {}
for n in ["R1A_VIEW_ARM","R1A_VIEW_GLOVE_ARM","R1A_VIEW_SLEEVE_ARM","R1A_VIEW_GUN","R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE","R1A_VIEW_ROOT"]:
    o = bpy.data.objects.get(n)
    if not o: continue
    d = {"constraints": [{"type": c.type, "target": c.target.name if c.target else None,
                          "subtarget": getattr(c, "subtarget", "")} for c in o.constraints],
         "drivers": len(o.animation_data.drivers) if o.animation_data else 0}
    if o.type == "ARMATURE":
        pb_con = {}
        for pb in o.pose.bones:
            if pb.constraints:
                pb_con[pb.name] = [{"type": c.type, "target": c.target.name if c.target else None,
                                    "subtarget": getattr(c, "subtarget", "")} for c in pb.constraints]
        d["bone_constraints_count"] = len(pb_con)
        d["bone_constraints_sample"] = dict(list(pb_con.items())[:4])
    if o.animation_data and o.animation_data.action:
        d["action"] = o.animation_data.action.name
    out[n] = d
# actions list + frame ranges
out["actions"] = {a.name: list(a.frame_range) for a in bpy.data.actions}
# NLA / scene props
scn = bpy.context.scene
out["scene_props"] = {k: scn[k] for k in scn.keys() if "r1a" in k.lower() or "clip" in k.lower()}
# frame markers
out["markers"] = {m.name: m.frame for m in scn.timeline_markers}
print(json.dumps(out, ensure_ascii=False, indent=1))
