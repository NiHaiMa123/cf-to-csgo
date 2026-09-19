import bpy
m = bpy.data.materials["MT_PV_Transformers"]
nt=m.node_tree
mix=[n for n in nt.nodes if n.bl_idname=="ShaderNodeMix"][0]
mix.inputs["Factor"].default_value=0.93
bs=[n for n in nt.nodes if n.type=="BSDF_PRINCIPLED"][0]
bs.inputs["Metallic"].default_value=0.75
w=bpy.context.scene.world
bg=next(n for n in w.node_tree.nodes if n.type=="BACKGROUND")
bg.inputs[0].default_value=(0.6,0.68,0.8,1.0); bg.inputs[1].default_value=1.6
sc=bpy.context.scene; sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\gun_v3_idle10.png"
bpy.ops.render.render(write_still=True)
print("done")
