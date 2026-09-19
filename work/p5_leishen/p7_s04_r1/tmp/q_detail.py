import bpy, json
names = ["R1A_CF_ANIM","R1A_CF_BIND","R1A_VIEW_ARM","R1A_VIEW_GLOVE_ARM","R1A_VIEW_SLEEVE_ARM",
         "R1A_VIEW_GUN","R1A_VIEW_ROOT","CS_M4A4_Armature","CF_GUN_P6","CS_GLOVE","CS_SLEEVE",
         "R1A_CAM_FRONT","R1A_CAM_SIDE","R1A_CAM_TOP","R1A_CAM_STUDIO"]
out = {}
for n in names:
    o = bpy.data.objects.get(n)
    if not o:
        out[n] = None; continue
    d = {"type": o.type, "hide_vp": o.hide_viewport, "hide_render": o.hide_render,
         "hide_get": o.hide_get(), "disp": o.display_type, "show_in_front": o.show_in_front,
         "coll": [c.name for c in o.users_collection],
         "parent": o.parent.name if o.parent else None,
         "loc": list(o.location), "scale": list(o.scale)}
    if o.type == "ARMATURE":
        d["bones"] = len(o.data.bones)
        d["bones_hidden"] = sum(1 for b in o.data.bones if b.hide)
        d["pose_bones_hidden"] = sum(1 for b in o.pose.bones if b.hide)
        d["display_type_bones"] = o.data.display_type
        d["show_names"] = o.data.show_names
        d["show_axes"] = o.data.show_axes
    if o.type == "MESH":
        d["verts"] = len(o.data.vertices)
        d["materials"] = [m.name if m else None for m in o.data.materials]
        d["armature_mod"] = [m.object.name if m.object else None for m in o.modifiers if m.type=="ARMATURE"]
    if o.type == "CAMERA":
        d["lens"] = o.data.lens
        d["rot"] = list(o.rotation_euler)
    out[n] = d
# all meshes in R1A_VIEW_MESH
vm = bpy.data.collections.get("R1A_VIEW_MESH")
out["__VIEW_MESH__"] = [o.name for o in vm.objects] if vm else None
# scene camera + animation on armatures
out["__scene_cam__"] = bpy.context.scene.camera.name if bpy.context.scene.camera else None
anim = {}
for n in ["R1A_CF_ANIM","R1A_CF_BIND","R1A_VIEW_ARM","R1A_VIEW_GLOVE_ARM","R1A_VIEW_SLEEVE_ARM","R1A_VIEW_GUN"]:
    o = bpy.data.objects.get(n)
    if o:
        anim[n] = o.animation_data.action.name if o.animation_data and o.animation_data.action else None
out["__actions__"] = anim
print(json.dumps(out, ensure_ascii=False, indent=1))
