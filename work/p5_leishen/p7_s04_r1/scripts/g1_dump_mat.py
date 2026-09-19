import json
import bpy

mat = bpy.data.materials["rif_m4a1_p6"]
nt = mat.node_tree
nodes = []
for n in nt.nodes:
    item = {"name": n.name, "type": n.type}
    if n.type == "TEX_IMAGE" and n.image:
        item["image"] = n.image.filepath
        item["colorspace"] = n.image.colorspace_settings.name
    if n.type == "BSDF_PRINCIPLED":
        base = n.inputs.get("Base Color")
        item["base_links"] = bool(base and base.is_linked)
        if base and not base.is_linked:
            item["base_default"] = list(base.default_value)
    nodes.append(item)
links = []
for l in nt.links:
    links.append("%s.%s -> %s.%s" % (l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name))
gun = bpy.data.objects["R1A_VIEW_GUN"]
out = {
    "nodes": nodes,
    "links": links,
    "uv": [uv.name for uv in gun.data.uv_layers],
    "slot_link": gun.material_slots[0].link if gun.material_slots else None,
    "slot_mat": gun.material_slots[0].material.name if gun.material_slots and gun.material_slots[0].material else None,
}
path = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_mat.json"
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
    handle.write("\n")
