import bpy
sc = bpy.context.scene
darms = bpy.data.objects["R1A_CF_DEFORM_ARMS"]
deform = bpy.data.objects["R1A_CF_DEFORM"]
def setclip(clip):
    for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
        a = bpy.data.actions[pr+clip]
        ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
for clip,f in [("idle_0",10),("reload",80),("select",30)]:
    setclip(clip)
    sc.frame_set(f); bpy.context.view_layer.update()
    sc.render.filepath = "D:/project/cf_to_csgo/work/p5_leishen/p7_s04_r1/source/shots/fox_%s_%d.png"%(clip,f)
    bpy.ops.render.render(write_still=True)
    print("done",clip,f)
