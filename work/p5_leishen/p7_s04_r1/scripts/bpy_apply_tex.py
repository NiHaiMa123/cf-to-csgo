import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
def mat_with_tex(imgpath):
    m = bpy.data.materials.new("MT_"+imgpath.split("\\")[-1][:-4])
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type=="BSDF_PRINCIPLED")
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(imgpath)
    nt.links.new(ti.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.7
    return m
assign = {"CF_fox_gr_hand": TEX+r"\FVIEW_HAND_Foxhowl_Renewal_GR.png",
          "CF_Arm_W": TEX+r"\FVIEW_ARM_Foxhowl_Renewal_GR.png"}
for obn, img in assign.items():
    ob = bpy.data.objects[obn]
    m = mat_with_tex(img)
    ob.data.materials.clear(); ob.data.materials.append(m)
    print("assigned", obn, "->", img)
sc = bpy.context.scene
sc.frame_set(10)
sc.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\fox_tex_idle10.png"
bpy.ops.render.render(write_still=True)
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
    a=bpy.data.actions[pr+"reload"]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
sc.frame_set(80); bpy.context.view_layer.update()
sc.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\fox_tex_reload80.png"
bpy.ops.render.render(write_still=True)
print("done")
