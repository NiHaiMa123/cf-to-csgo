import bpy
for nm in ("CF_fox_bl_ARM","CF_fox_bl_HAND"):
    ob=bpy.data.objects[nm]
    for uvl in ob.data.uv_layers:
        for d in uvl.data: d.uv.y = 1.0-d.uv.y
    print("reflip",nm)
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
