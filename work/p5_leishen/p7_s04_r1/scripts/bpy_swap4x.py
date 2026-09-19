import bpy
TEX = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex"
swap = {"MT_FH_BL": TEX+r"\4x_up_hand_00001_.png", "MT_FA_BL": TEX+r"\4x_up_arm_00001_.png"}
for mn, imgp in swap.items():
    m = bpy.data.materials[mn]
    img = bpy.data.images.load(imgp)
    for n in m.node_tree.nodes:
        if n.type=="TEX_IMAGE" and "FVIEW" in (n.image.filepath if n.image else ""):
            n.image = img
            print(mn,"->",imgp)
            break
sc=bpy.context.scene
sc.render.filepath=r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\shots\bl_4x_idle10.png"
sc.frame_set(10); bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
print("SAVED")
