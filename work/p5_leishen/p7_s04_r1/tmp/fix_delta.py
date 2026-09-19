import bpy, json
tb = bpy.data.texts["r1a_source_switcher.py"]
src = "\n".join(l.body for l in tb.lines)

old = '''        desired = {}
        for bone in order:
            cf_name = reverse.get(bone.name)
            if cf_name is not None:
                i = idx[cf_name]
                x, y, z, w = quat[i]
                q = Quaternion((w, x, y, z))
                M = q.to_matrix().to_4x4()
                M.translation = Vector(pos[i])
                pose = T @ M
            elif bone.parent is None:
                pose = bone.matrix_local.copy()
            else:
                pose = desired[bone.parent.name] @ bone.parent.matrix_local.inverted() @ bone.matrix_local
            desired[bone.name] = pose
            if bone.parent is None:
                basis = bone.matrix_local.inverted() @ pose
            else:
                basis = (bone.matrix_local.inverted() @ bone.parent.matrix_local
                         @ desired[bone.parent.name].inverted() @ pose)
            arm.pose.bones[bone.name].matrix_basis = basis'''

new = '''        desired = {}
        T_inv = T.inverted()
        bind_inv = _CACHE.setdefault("bind_inv", {})
        for bone in order:
            cf_name = reverse.get(bone.name)
            rest = bone.matrix_local
            if cf_name is not None:
                i = idx[cf_name]
                x, y, z, w = quat[i]
                q = Quaternion((w, x, y, z))
                M = q.to_matrix().to_4x4()
                M.translation = Vector(pos[i])
                bi = bind_inv.get(cf_name)
                if bi is None:
                    bi = Matrix(nodes[i]["bind_world"]).inverted()
                    bind_inv[cf_name] = bi
                Dt = T @ (M @ bi) @ T_inv
                pose = (Matrix.Translation((T @ M).translation)
                        @ Dt.to_3x3().to_4x4()
                        @ rest.to_3x3().to_4x4())
            elif bone.parent is None:
                pose = rest.copy()
            else:
                pose = desired[bone.parent.name] @ bone.parent.matrix_local.inverted() @ rest
            desired[bone.name] = pose
            if bone.parent is None:
                basis = rest.inverted() @ pose
            else:
                basis = (rest.inverted() @ bone.parent.matrix_local
                         @ desired[bone.parent.name].inverted() @ pose)
            arm.pose.bones[bone.name].matrix_basis = basis'''

assert old in src, "loop not found"
src = src.replace(old, new)
tb.clear(); tb.write(src)
tb.use_module = True
g = {"bpy": bpy, "__name__": "r1a_source_switcher"}
exec(tb.as_string(), g)
scn = bpy.context.scene
scn.frame_set(scn.frame_current)
bpy.context.view_layer.update()
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\delta_v1.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"ok": True, "clip": scn.r1a_source_clip, "frame": scn.frame_current}))
