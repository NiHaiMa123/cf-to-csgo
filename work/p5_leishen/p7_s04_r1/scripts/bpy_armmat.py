import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
def build(name, diff, spec, norm):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial"); out.location=(600,0)
    bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(300,0)
    nt.links.new(bs.outputs[0],out.inputs[0])
    td=nt.nodes.new("ShaderNodeTexImage"); td.location=(-400,300)
    td.image=bpy.data.images.load(diff)
    nt.links.new(td.outputs["Color"],bs.inputs["Base Color"])
    ts=nt.nodes.new("ShaderNodeTexImage"); ts.location=(-400,0)
    ts.image=bpy.data.images.load(spec); ts.image.colorspace_settings.name="Non-Color"
    rg=nt.nodes.new("ShaderNodeMapRange"); rg.location=(0,-40)
    rg.inputs["To Min"].default_value=0.75; rg.inputs["To Max"].default_value=0.3
    nt.links.new(ts.outputs["Color"],rg.inputs["Value"]); nt.links.new(rg.outputs["Result"],bs.inputs["Roughness"])
    tn=nt.nodes.new("ShaderNodeTexImage"); tn.location=(-400,-350)
    tn.image=bpy.data.images.load(norm); tn.image.colorspace_settings.name="Non-Color"
    nm=nt.nodes.new("ShaderNodeNormalMap"); nm.location=(0,-350)
    nt.links.new(tn.outputs["Color"],nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m
mh = build("MT_FH_BL", TEX+r"\FVIEW_HAND_Foxhowl_Renewal_BL.png", TEX+r"\FVIEW_HAND_Foxhowl_Renewal_BL_S.PNG", TEX+r"\FVIEW_HAND_Foxhowl_Renewal_BL_N.PNG")
ma = build("MT_FA_BL", TEX+r"\FVIEW_ARM_Foxhowl_Renewal_BL.png", TEX+r"\FVIEW_ARM_Foxhowl_Renewal_BL_S.PNG", TEX+r"\FVIEW_ARM_Foxhowl_Renewal_BL_N.PNG")
bpy.data.objects["CF_fox_bl_HAND"].data.materials.clear(); bpy.data.objects["CF_fox_bl_HAND"].data.materials.append(mh)
bpy.data.objects["CF_fox_bl_ARM"].data.materials.clear(); bpy.data.objects["CF_fox_bl_ARM"].data.materials.append(ma)
sc=bpy.context.scene
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
def setclip(c):
    for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
        a=bpy.data.actions[pr+c]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
setclip("reload"); sc.frame_set(80); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\bl_nm_reload80.png"
bpy.ops.render.render(write_still=True)
setclip("idle_0"); sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\bl_nm_idle10.png"
bpy.ops.render.render(write_still=True)
print("done")
