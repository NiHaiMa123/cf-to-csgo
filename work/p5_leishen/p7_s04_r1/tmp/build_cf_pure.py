import bpy, json
from mathutils import Vector

DUMP = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\cf_skin_dump.json"
d = json.load(open(DUMP, "r", encoding="utf-8"))
skel = d["skeleton"]
node_names = [n["name"] for n in skel]

ARM = "R1A_CF_ANIM"
RIGID_NODE = {
    "M4A1_transformers_Body": "Dummy01",
    "M4A1_transformers_MAG": "Bone06",
    "M4A1_transformers_Reload01": "Bone04",
    "M4A1_transformers_Reload02": "Box001",
    "M4A1_transformers_part01": "Box003",
    "M4A1_transformers_part02": "Box004",
    "M4A1_transformers_part03": "Box005",
    "M4A1_transformers_part04": "Box006",
    "M4A1_transformers_part05": "Box002",
}
# materials
def mk_mat(name, color, metallic=0.0, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    return m
M_GUN = mk_mat("CF_GunBody", (0.045, 0.05, 0.06), 0.75, 0.35)
M_PART = mk_mat("CF_GunPart", (0.10, 0.11, 0.13), 0.6, 0.45)
M_ARM = mk_mat("CF_Arm", (0.55, 0.45, 0.38), 0.0, 0.8)
M_HAND = mk_mat("CF_Hand", (0.55, 0.45, 0.38), 0.0, 0.8)

coll = bpy.data.collections.get("CF_PURE") or bpy.data.collections.new("CF_PURE")
if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
    bpy.context.scene.collection.children.link(coll)

created = []
for mesh_def in d["meshes"]:
    name = "CF_" + mesh_def["name"].replace(" ", "_")
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    vs = mesh_def["vertices"]
    verts = [(vs[i], vs[i+1], vs[i+2]) for i in range(0, len(vs), 3)]
    tris = [tuple(mesh_def["triangles"][i:i+3]) for i in range(0, len(mesh_def["triangles"]), 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], tris)
    me.update()
    # uvs
    if mesh_def["uvs"]:
        uvl = me.uv_layers.new(name="UVMap")
        uv = mesh_def["uvs"]
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = (uv[2*vi], uv[2*vi+1])
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    # vertex groups
    bw = mesh_def["bone_weights"]; bi = mesh_def["bone_indices"]
    if bw and bi:
        used = set()
        for vi in range(mesh_def["vertex_count"]):
            w0, w1, w2 = bw[3*vi], bw[3*vi+1], bw[3*vi+2]
            w3 = max(0.0, 1.0 - (w0+w1+w2))
            ids = bi[4*vi:4*vi+4]
            for node_i, w in zip(ids, (w0, w1, w2, w3)):
                if node_i == 255 or w <= 1e-6 or node_i >= len(node_names):
                    continue
                used.add(node_i)
        grp = {ni: ob.vertex_groups.new(name=node_names[ni]) for ni in used}
        for vi in range(mesh_def["vertex_count"]):
            w0, w1, w2 = bw[3*vi], bw[3*vi+1], bw[3*vi+2]
            w3 = max(0.0, 1.0 - (w0+w1+w2))
            ids = bi[4*vi:4*vi+4]
            for node_i, w in zip(ids, (w0, w1, w2, w3)):
                if node_i == 255 or w <= 1e-6 or node_i not in grp:
                    continue
                grp[node_i].add([vi], w, "REPLACE")
        mat = M_HAND if "hand" in mesh_def["name"].lower() else M_ARM
    else:
        node = RIGID_NODE.get(mesh_def["name"], "Dummy01")
        g = ob.vertex_groups.new(name=node)
        g.add(list(range(mesh_def["vertex_count"])), 1.0, "REPLACE")
        mat = M_GUN if "Body" in mesh_def["name"] else M_PART
    me.materials.append(mat)
    mod = ob.modifiers.new("CF_ARM", "ARMATURE")
    mod.object = bpy.data.objects[ARM]
    mod.use_deform_preserve_volume = False
    created.append(name)

print(json.dumps({"created": created}))
