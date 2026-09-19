import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
m = bpy.data.materials.get("MT_PV_Transformers") or bpy.data.materials.new("MT_PV_Transformers")
m.use_nodes=True
nt=m.node_tree; nt.nodes.clear()
out=nt.nodes.new("ShaderNodeOutputMaterial"); out.location=(600,0)
bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(300,0)
nt.links.new(bs.outputs[0],out.inputs[0])
# base = mix(diffuse_dark, specmap_silver, 0.8)  — approximates CF env-reflect look
mix=nt.nodes.new("ShaderNodeMix"); mix.data_type='RGBA'; mix.location=(0,300)
mix.inputs["Factor"].default_value=0.8
td=nt.nodes.new("ShaderNodeTexImage"); td.location=(-400,400)
td.image=bpy.data.images.load(TEX+r"\PV-M4A1_S_Transformers.png")
ts=nt.nodes.new("ShaderNodeTexImage"); ts.location=(-400,80)
ts.image=bpy.data.images.load(TEX+r"\M4A1_S_Transformers_S.png")
nt.links.new(td.outputs["Color"],mix.inputs[6])
nt.links.new(ts.outputs["Color"],mix.inputs[7])
nt.links.new(mix.outputs[2],bs.inputs["Base Color"])
# roughness: shinier where spec bright -> rough = 1 - luminance(spec)*k
rg=nt.nodes.new("ShaderNodeMapRange"); rg.location=(0,-60)
rg.inputs["To Min"].default_value=0.55; rg.inputs["To Max"].default_value=0.15
nt.links.new(ts.outputs["Color"],rg.inputs["Value"]); nt.links.new(rg.outputs["Result"],bs.inputs["Roughness"])
bs.inputs["Metallic"].default_value=0.55
# normal map
tn=nt.nodes.new("ShaderNodeTexImage"); tn.location=(-400,-260)
tn.image=bpy.data.images.load(TEX+r"\M4A1_S_Transformers_N.png"); tn.image.colorspace_settings.name="Non-Color"
nm=nt.nodes.new("ShaderNodeNormalMap"); nm.location=(0,-260)
nt.links.new(tn.outputs["Color"],nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
# brighten world so metallic has something to reflect
w=bpy.context.scene.world
w.use_nodes=True
bg=next(n for n in w.node_tree.nodes if n.type=="BACKGROUND")
bg.inputs[0].default_value=(0.35,0.4,0.5,1.0); bg.inputs[1].default_value=1.2
for ob in bpy.data.objects:
    if ob.name.startswith("CF_M4A1_transformers"):
        ob.data.materials.clear(); ob.data.materials.append(m)
sc=bpy.context.scene
sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\gun_v2_idle10.png"
bpy.ops.render.render(write_still=True)
print("done")
