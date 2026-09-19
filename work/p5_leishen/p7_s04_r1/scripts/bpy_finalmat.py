import bpy
m=bpy.data.materials["MT_PV_Transformers"]
for ob in bpy.data.objects:
    if ob.name.startswith("CF_M4A1_transformers"):
        ob.data.materials.clear(); ob.data.materials.append(m)
sc=bpy.context.scene
darms=bpy.data.objects["R1A_CF_DEFORM_ARMS"]; deform=bpy.data.objects["R1A_CF_DEFORM"]
def setclip(c):
    for ob,pr in ((deform,"R1A_CFD_"),(darms,"R1A_CFDA_")):
        a=bpy.data.actions[pr+c]; ob.animation_data.action=a; ob.animation_data.action_slot=a.slots[0]
for c,f in [("idle_0",10),("reload",80)]:
    setclip(c); sc.frame_set(f); bpy.context.view_layer.update()
    sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\final_%s_%d.png"%(c,f)
    bpy.ops.render.render(write_still=True)
    print("done",c,f)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
print("SAVED")
