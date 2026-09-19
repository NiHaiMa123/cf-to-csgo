import bpy, json
tb = bpy.data.texts["r1a_source_switcher.py"]
src = "\n".join(l.body for l in tb.lines)

old_loop = '''        order = []
        def walk(bone):
            order.append(bone)
            for child in bone.children:
                walk(child)
        for bone in arm.data.bones:
            if bone.parent is None:
                walk(bone)
        for bone in order:
            cf_name = reverse.get(bone.name)
            if cf_name is None:
                continue
            i = idx[cf_name]
            x, y, z, w = quat[i]
            q = Quaternion((w, x, y, z))
            M = q.to_matrix().to_4x4()
            M.translation = Vector(pos[i])
            arm.pose.bones[bone.name].matrix = T @ M'''

new_loop = '''        order = []
        def walk(bone):
            order.append(bone)
            for child in bone.children:
                walk(child)
        for bone in arm.data.bones:
            if bone.parent is None:
                walk(bone)
        desired = {}
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

assert old_loop in src, "posing loop not found"
src = src.replace(old_loop, new_loop)
tb.clear(); tb.write(src)
tb.use_module = True

# re-exec the patched switcher so the live handler is replaced
g = {"bpy": bpy, "__name__": "r1a_source_switcher"}
exec(tb.as_string(), g)
scn = bpy.context.scene
scn.frame_set(scn.frame_current)
bpy.context.view_layer.update()
handlers = [getattr(h, "__name__", str(h)) for h in bpy.app.handlers.frame_change_post]
print(json.dumps({"handlers": handlers, "map_len": len(g["BONE_MAP"]) if "BONE_MAP" in g else None}))
