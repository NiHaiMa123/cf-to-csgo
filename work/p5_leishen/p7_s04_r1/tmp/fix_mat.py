import bpy, json
def mk_mat(name, color, metallic=0.0, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Metallic" in bsdf.inputs: bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs: bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*color, 1.0)
    return m
mk_mat("CF_GunBody", (0.045, 0.05, 0.06), 0.75, 0.35)
mk_mat("CF_GunPart", (0.10, 0.11, 0.13), 0.6, 0.45)
mk_mat("CF_Arm", (0.55, 0.45, 0.38), 0.0, 0.8)
mk_mat("CF_Hand", (0.55, 0.45, 0.38), 0.0, 0.8)
print(json.dumps({"ok": True}))
