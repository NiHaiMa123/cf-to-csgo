import bpy
for ob in bpy.data.objects:
    if ob.type=="MESH" and ob.name.startswith("CF_M4A1_transformers"):
        for uvl in ob.data.uv_layers:
            for d in uvl.data: d.uv.y=1.0-d.uv.y
sc=bpy.context.scene; sc.frame_set(10); bpy.context.view_layer.update()
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\uvchk_spec_rawv.png"
bpy.ops.render.render(write_still=True)
print("done")
