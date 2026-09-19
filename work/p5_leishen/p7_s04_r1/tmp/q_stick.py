import bpy, json
j = bpy.data.objects.get("R1A_ANIM_J_42") or bpy.data.objects.get("R1A_ANIM_J_00")
s = bpy.data.objects.get("R1A_ANIM_S_42") or bpy.data.objects.get("R1A_ANIM_S_00")
out = {}
for label, o in [("J", j), ("S", s)]:
    if o:
        mats = []
        for m in o.data.materials:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        mats.append({"mat": m.name, "base": list(n.inputs["Base Color"].default_value)[:3],
                                     "emit": list(n.inputs["Emission Color"].default_value)[:3] if "Emission Color" in n.inputs else None,
                                     "emit_str": n.inputs["Emission Strength"].default_value if "Emission Strength" in n.inputs else None})
            elif m:
                mats.append({"mat": m.name, "diffuse": list(m.diffuse_color)[:3]})
        out[label] = {"name": o.name, "loc": [round(v,2) for v in o.matrix_world.translation],
                      "scale": [round(v,3) for v in o.scale], "mats": mats,
                      "show_in_front": o.show_in_front, "disp": o.display_type}
# where are joints vs gun: list a few joint positions
dg = bpy.context.evaluated_depsgraph_get()
poss = {}
for i in [0,1,42,43,55,56]:
    o = bpy.data.objects.get("R1A_ANIM_J_%02d" % i)
    if o: poss[o.name] = [round(v,2) for v in o.matrix_world.translation]
out["joint_pos"] = poss
print(json.dumps(out, ensure_ascii=False, indent=1))
