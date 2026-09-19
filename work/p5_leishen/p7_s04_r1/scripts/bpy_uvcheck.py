import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
for tag,img in [("spec",r"\M4A1_S_Transformers_S.png"),("diff",r"\PV-M4A1_S_Transformers.png")]:
    m=bpy.data.materials.new("MT_UVCHK_"+tag); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    em=nt.nodes.new("ShaderNodeEmission")
    ti=nt.nodes.new("ShaderNodeTexImage"); ti.image=bpy.data.images.load(TEX+img)
    nt.links.new(ti.outputs["Color"],em.inputs["Color"]); nt.links.new(em.outputs[0],out.inputs[0])
    for ob in bpy.data.objects:
        if ob.name.startswith("CF_M4A1_transformers"):
            ob.data.materials.clear(); ob.data.materials.append(m)
    sc=bpy.context.scene; sc.frame_set(10); bpy.context.view_layer.update()
    sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\uvchk_%s.png"%tag
    bpy.ops.render.render(write_still=True)
    print("done",tag)
