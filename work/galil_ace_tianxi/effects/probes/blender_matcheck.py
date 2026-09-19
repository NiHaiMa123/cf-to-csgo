import bpy

m = bpy.data.materials.get('fx_galilace_parts_blue')
print('=== material:', m)
if m and m.use_nodes:
    for n in m.node_tree.nodes:
        print('node:', n.name, n.bl_idname)
        for i in n.inputs:
            try:
                print('   in', i.name, '=', getattr(i, 'default_value', 'link'), 'links:', len(i.links))
            except Exception:
                pass
    for l in m.node_tree.links:
        print('link:', l.from_node.name, l.from_socket.name, '->', l.to_node.name, l.to_socket.name)
