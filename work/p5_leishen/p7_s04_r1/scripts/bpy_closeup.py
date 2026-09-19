import bpy, mathutils
sc=bpy.context.scene; cam=sc.camera
# aim at the fore-grip hand: gun area is around x -1..0, y -4..-2, z -5..-1 in mirrored space; find hand object bounds
deps=bpy.context.evaluated_depsgraph_get()
ob=bpy.data.objects["CF_fox_bl_HAND"].evaluated_get(deps)
me=ob.to_mesh(); mw=ob.matrix_world
lo=[1e9]*3; hi=[-1e9]*3
for v in me.vertices:
    w=mw@v.co
    for i in range(3):
        lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
ob.to_mesh_clear()
ctr=[(lo[i]+hi[i])/2 for i in range(3)]
print("hand bounds",lo,hi)
cam.location=(ctr[0]+4.5, ctr[1]-7.0, ctr[2]+2.5)
d=(mathutils.Vector(ctr)-cam.location)
cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.lens=55
sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\bl_4x_closeup.png"
bpy.ops.render.render(write_still=True)
print("done")
