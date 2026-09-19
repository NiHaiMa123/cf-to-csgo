import bpy
sc=bpy.context.scene
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
for c,f in [("reload",80),("select",30)]:
    for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
        a=bpy.data.actions[pr+c]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
    sc.frame_set(f); bpy.context.view_layer.update()
    sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\mir_%s_%d.png"%(c,f)
    bpy.ops.render.render(write_still=True)
    print("done",c,f)
# back to idle default
for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_"),(bpy.data.objects["R1A_CF_ANIM"],"R1A_CF_")):
    a=bpy.data.actions[pr+"idle_0"]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
sc.cfd_clip="idle_0"; sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
print("SAVED")
