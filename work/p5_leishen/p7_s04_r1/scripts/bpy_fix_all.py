import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"

# 1. drop stale GR arm meshes, rename BL ones
for nm in ("CF_fox_gr_hand","CF_Arm_W"):
    o=bpy.data.objects.get(nm)
    if o: bpy.data.objects.remove(o,do_unlink=True); print("removed",nm)
o=bpy.data.objects.get("CF_Arm_W.001")
if o: o.name="CF_fox_bl_ARM"; print("renamed ->",o.name)

# 2. flip V on ALL CF_* mesh UVs (decoder raw v -> 1-v per t02 verified convention)
for ob in bpy.data.objects:
    if ob.type!="MESH" or not ob.name.startswith("CF_"): continue
    for uvl in ob.data.uv_layers:
        for d in uvl.data: d.uv.y = 1.0-d.uv.y
    print("vflip",ob.name)

# 3. materials
def mat(name, imgpath):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    bs=nt.nodes.new("ShaderNodeBsdfPrincipled")
    ti=nt.nodes.new("ShaderNodeTexImage")
    ti.image=bpy.data.images.load(imgpath)
    nt.links.new(ti.outputs["Color"],bs.inputs["Base Color"])
    nt.links.new(bs.outputs[0],out.inputs[0])
    bs.inputs["Roughness"].default_value=0.6
    m["bsdf_node"]=bs.name
    return m
assign = {
 "CF_fox_bl_HAND": ("MT_FH_BL", TEX+r"\FVIEW_HAND_Foxhowl_Renewal_BL.png"),
 "CF_fox_bl_ARM":  ("MT_FA_BL", TEX+r"\FVIEW_ARM_Foxhowl_Renewal_BL.png"),
}
for obn,(mn,img) in assign.items():
    ob=bpy.data.objects[obn]
    ob.data.materials.clear(); ob.data.materials.append(mat(mn,img))
    print("mat",obn,"->",img)
mgun = mat("MT_PV_Transformers", TEX+r"\PV-M4A1_S_Transformers.png")
mg_bs=mgun.node_tree.nodes[mgun["bsdf_node"]]
mg_bs.inputs["Metallic"].default_value=0.35
mg_bs.inputs["Roughness"].default_value=0.5
for ob in bpy.data.objects:
    if ob.name.startswith("CF_M4A1_transformers"):
        ob.data.materials.clear(); ob.data.materials.append(mgun)

# 4. render idle + reload
sc=bpy.context.scene
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
def setclip(c):
    for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
        a=bpy.data.actions[pr+c]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
for c,f in [("idle_0",10),("reload",80)]:
    setclip(c); sc.frame_set(f); bpy.context.view_layer.update()
    sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\bl_%s_%d.png"%(c,f)
    bpy.ops.render.render(write_still=True)
    print("rendered",c,f)
