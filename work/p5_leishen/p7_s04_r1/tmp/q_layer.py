import bpy, json
vl = bpy.context.view_layer
def walk(lc, depth=0):
    out = [{"name": lc.collection.name, "exclude": lc.exclude, "hide_viewport": lc.hide_viewport, "children": []}]
    for ch in lc.children:
        out[0]["children"].append(walk(ch, depth+1))
    return out[0]
tree = walk(vl.layer_collection)
vis = [o.name for o in bpy.data.objects if o.visible_get()]
arm = [o.name for o in bpy.data.objects if o.type=="ARMATURE"]
meshes = {}
for o in bpy.data.objects:
    if o.type=="MESH":
        meshes.setdefault(o.users_collection[0].name if o.users_collection else "NONE", []).append(o.name)
print(json.dumps({
  "layer_tree": tree,
  "visible_objects": vis,
  "armatures": arm,
  "mesh_count": len([o for o in bpy.data.objects if o.type=='MESH']),
  "mesh_by_collection": {k: len(v) for k,v in meshes.items()},
}, ensure_ascii=False, indent=1))
