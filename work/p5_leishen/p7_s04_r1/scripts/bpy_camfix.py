import bpy, mathutils
sc=bpy.context.scene
deps=bpy.context.evaluated_depsgraph_get()
lo=[1e9]*3; hi=[-1e9]*3
for o in bpy.data.objects:
    if o.type!="MESH" or o.hide_get() or not (o.name.startswith("CF_")): continue
    if o.name=="CF_GUN_P6": continue
    oe=o.evaluated_get(deps); me=oe.to_mesh(); mw=oe.matrix_world
    for v in me.vertices:
        w=mw@v.co
        for i in range(3):
            lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    oe.to_mesh_clear()
ctr=[(lo[i]+hi[i])/2 for i in range(3)]; span=max(hi[i]-lo[i] for i in range(3))
print("bounds",lo,hi,"ctr",ctr,"span",span)
cam=sc.camera
cam.location=(ctr[0]+span*0.35, ctr[1]-span*1.1, ctr[2]+span*0.25)
d=(mathutils.Vector(ctr)-cam.location)
cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.clip_start=0.1; cam.data.clip_end=10000; cam.data.lens=40
sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\mirrored_idle10.png"
bpy.ops.render.render(write_still=True)
print("done")
