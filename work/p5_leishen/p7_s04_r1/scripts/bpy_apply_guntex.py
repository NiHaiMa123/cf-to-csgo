import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
m = bpy.data.materials.new("MT_PV_Transformers")
m.use_nodes=True
nt=m.node_tree
bs=next(n for n in nt.nodes if n.type=="BSDF_PRINCIPLED")
ti=nt.nodes.new("ShaderNodeTexImage")
ti.image=bpy.data.images.load(TEX+r"\PV-M4A1_S_Transformers.png")
nt.links.new(ti.outputs["Color"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value=0.45
bs.inputs["Metallic"].default_value=0.4
for ob in bpy.data.objects:
    if ob.name.startswith("CF_M4A1_transformers"):
        ob.data.materials.clear(); ob.data.materials.append(m)
        print("tex",ob.name)
sc=bpy.context.scene
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
for ob,pr,clip,f in [(deform,"R1A_CFD_","idle_0",10),(darms,"R1A_CFDA_","idle_0",10)]:
    a=bpy.data.actions[pr+clip]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=TEX+r"\..\shots\full_tex_idle10.png"
bpy.ops.render.render(write_still=True)
for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
    a=bpy.data.actions[pr+"reload"]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
sc.frame_set(80); bpy.context.view_layer.update()
sc.render.filepath=TEX+r"\..\shots\full_tex_reload80.png"
bpy.ops.render.render(write_still=True)
print("done")
